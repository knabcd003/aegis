from datetime import date, datetime
import uuid
from typing import List, Optional
from fastapi import BackgroundTasks

from config.schema import AegisConfig, AssetUniverse, SignalGateConfig, FundamentalEngineConfig, \
    EarningsRevisionConfig, InsiderMonitorConfig, AgentConfig, PositionSizingConfig, \
    SandboxConfig, PromotionCriteriaConfig, RoutingConfig, LoggingConfig
from engines.intake.mandate_profile import MandateProfile
from engines.simulation.loop import SimulationLoop
from engines.simulation.mlflow_logger import MLflowLogger
from engines.simulation.metrics import compute_metrics, compute_sharpe
from engines.simulation.walk_forward import WalkForwardValidator
from engines.system.scenario.generator import BlockBootstrapGenerator
from engines.system.scenario.models import BootstrapRequest
from api.routers.pipeline_events import broadcaster
from api.schemas.intake import IntakeDraft

class SimulationOrchestrator:
    """
    Bridges the Intake Mandate to the Simulation Tier.
    Converts qualitative user desire into a verified AegisConfig and triggers the loop.
    """
    
    @staticmethod
    async def run_from_intake(draft: IntakeDraft, run_id: str):
        """
        Background task to execute a full strategy discovery pipeline.
        """
        # 1. Map Path A Intake to a MandateProfile (Immutable Constraints)
        profile = MandateProfile.from_path_a(
            risk_tolerance=draft.risk_tolerance,
            time_horizon=draft.time_horizon,
            raw_desire=draft.raw_desire
        )
        
        # 2. Convert MandateProfile to a concrete AegisConfig
        config = AegisConfig(
            config_id=f"cfg_{uuid.uuid4().hex[:8]}",
            version="7.0.0",
            asset_universe=AssetUniverse(
                tickers=draft.tickers if draft.tickers else ["AAPL", "MSFT", "NVDA", "TSLA", "AMD"],
                benchmark="SPY"
            ),
            signal_gate=SignalGateConfig(),
            fundamental_engine=FundamentalEngineConfig(
                earnings_revision=EarningsRevisionConfig(enabled=True),
                insider_monitor=InsiderMonitorConfig(enabled=True)
            ),
            agent=AgentConfig(enabled=False), 
            position_sizing=PositionSizingConfig(
                capital=100000.0,
                max_position_pct=profile.max_position_pct,
                method="equal_weight"
            ),
            sandbox=SandboxConfig(
                min_hold_days=profile.holding_period_range[0],
                max_hold_days=profile.holding_period_range[1],
                stop_loss_pct=profile.stop_loss_range[0],
                promotion_criteria=PromotionCriteriaConfig()
            ),
            routing=RoutingConfig(
                mode="build",
                logging=LoggingConfig(depth="production")
            )
        )
        config.run_id = run_id
        config.fingerprint = f"fp_{uuid.uuid4().hex[:8]}"

        # 3. Initialize Logger & Loop
        logger = MLflowLogger(config)
        
        # 4. Broadcast Event: Pipeline Start
        await broadcaster.broadcast({
            "event_id": f"evt_{uuid.uuid4().hex[:6]}",
            "workflow_id": run_id,
            "timestamp": datetime.now().isoformat(),
            "event_type": "node_start",
            "node_id": "darwinian_sandbox",
            "payload": {"config_id": config.config_id}
        })

        try:
            # 5. Pipeline Sequence (Industrial Requirement Priority 2)
            # Step 1: Seal held-out partition (20%, random dates, hash to run_id)
            import hashlib
            import pandas as pd
            import numpy as np
            
            start_date = date(2020, 1, 1)
            end_date = date(2023, 12, 31)
            all_dates = pd.date_range(start_date, end_date, freq='B').date.tolist()
            num_holdout = int(len(all_dates) * 0.2)
            
            seed_int = int(hashlib.md5(run_id.encode('utf-8'), usedforsecurity=False).hexdigest(), 16) % (2**32)
            rng = np.random.RandomState(seed_int)
            holdout_dates = sorted(rng.choice(all_dates, num_holdout, replace=False))
            opt_dates = sorted([d for d in all_dates if d not in holdout_dates])
            
            # Step 2: Run primary backtest on optimization period (80%)
            sim_loop = SimulationLoop(config)
            logger.log_run_start(holdout_dates=[d.isoformat() for d in holdout_dates])
            
            # Optimization Run
            opt_results = sim_loop.run(start_date, end_date, holdout_dates=holdout_dates)
            
            # Step 3: Run WalkForwardValidator on optimization period dates only
            # This prevents data leakage from the held-out partition
            wf_validator = WalkForwardValidator(config, n_folds=6)
            wf_result = wf_validator.run(start_date, end_date, holdout_dates=holdout_dates)
            
            # Step 4: Run BlockBootstrapGenerator scenario battery
            scenario_gen = BlockBootstrapGenerator()
            # Extract returns from opt_results for bootstrapping
            nav_df = pd.DataFrame(opt_results["nav_history"])
            nav_df["date"] = pd.to_datetime(nav_df["date"]).dt.date
            mask_opt = nav_df["date"].isin(opt_dates)
            opt_returns = nav_df.loc[mask_opt, "nav"].pct_change().fillna(0).tolist()
            
            scenario_request = BootstrapRequest(
                strategy_returns=opt_returns,
                num_scenarios=50,
                block_size_days=20,
                scenario_length_days=252,
                mandate_max_drawdown=profile.drawdown_limit / 100.0 if hasattr(profile, "drawdown_limit") else 0.15
            )
            scenario_result = scenario_gen.execute(scenario_request)
            
            # Step 5: Evaluate held-out partition (produces held_out_sharpe)
            # We run the loop specifically on holdout dates to get clean OOS metrics
            # Note: loop.run handles the full range but we extract holdout specifically in metrics
            
            # Step 6: Compute all 10 metrics
            metrics = compute_metrics(
                opt_results["nav_history"],
                opt_results["trade_log"],
                [d.isoformat() for d in holdout_dates]
            )
            
            # Inject WFE and Scenario metrics
            metrics["walk_forward_efficiency"] = wf_result.wfe
            metrics["scenario_pass_rate"] = scenario_result.pass_rate
            
            # Step 7: Log everything to MLflow
            logger.log_run_end(
                metrics=metrics,
                trade_log=opt_results["trade_log"],
                nav_history=opt_results["nav_history"],
                gate_events=opt_results["gate_events"]
            )
            
            # Step 8: Close the run (handled by log_run_end's context manager)
            
            # Broadcast Event: Pipeline Success
            await broadcaster.broadcast({
                "event_id": f"evt_{uuid.uuid4().hex[:6]}",
                "workflow_id": run_id,
                "timestamp": datetime.now().isoformat(),
                "event_type": "node_success",
                "node_id": "darwinian_sandbox",
                "payload": {
                    "sharpe": metrics.get("sharpe", 0.0),
                    "wfe": wf_result.wfe,
                    "scenario_pass": scenario_result.pass_rate
                }
            })
            
        except Exception as e:
            # Broadcast Event: Pipeline Failure
            await broadcaster.broadcast({
                "event_id": f"evt_{uuid.uuid4().hex[:6]}",
                "workflow_id": run_id,
                "timestamp": datetime.now().isoformat(),
                "event_type": "node_failure",
                "node_id": "darwinian_sandbox",
                "payload": {"error": str(e)}
            })
            raise e
