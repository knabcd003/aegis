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
from api.schemas.intake import V9IntakeSchema

class SimulationOrchestrator:
    """
    Bridges the Intake Mandate to the Simulation Tier.
    Converts qualitative user desire into a verified AegisConfig and triggers the loop.
    """
    
    @staticmethod
    async def run_from_intake(draft: V9IntakeSchema, run_id: str):
        """
        Background task to execute a full strategy discovery pipeline.
        """
        # 1. Map Path A Intake to a MandateProfile (Immutable Constraints)
        
        # Derive risk tolerance from max drawdown (simplistic mapping for now)
        risk_tol = "moderate"
        drawdown = 0.15
        if draft.mandate_hard_constraints and draft.mandate_hard_constraints.max_portfolio_drawdown_pct is not None:
            drawdown = draft.mandate_hard_constraints.max_portfolio_drawdown_pct
            if drawdown <= 0.10: risk_tol = "conservative"
            elif drawdown >= 0.20: risk_tol = "aggressive"
            
        # Derive horizon from weights
        horizon = "swing"
        if draft.mandate_hard_constraints and draft.mandate_hard_constraints.horizon_allocation:
            for h in draft.mandate_hard_constraints.horizon_allocation:
                if h.capital_weight and h.capital_weight > 0.5 and h.label:
                    horizon = h.label
                    
        desire = ""
        if draft.universe_mandate and draft.universe_mandate.raw_desire:
            desire = draft.universe_mandate.raw_desire

        profile = MandateProfile.from_path_a(
            risk_tolerance=risk_tol,
            time_horizon=horizon,
            raw_desire=desire
        )
        
        tickers = ["AAPL", "MSFT", "NVDA", "TSLA", "AMD"]
        if draft.mandate_hard_constraints and draft.mandate_hard_constraints.universe_hard_filters and draft.mandate_hard_constraints.universe_hard_filters.specific_tickers_focus:
            tickers = draft.mandate_hard_constraints.universe_hard_filters.specific_tickers_focus
        
        # 2. Convert MandateProfile to a concrete AegisConfig
        config = AegisConfig(
            config_id=f"cfg_{uuid.uuid4().hex[:8]}",
            version="7.0.0",
            asset_universe=AssetUniverse(
                tickers=tickers,
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
            
            start_date = date(2019, 1, 1)
            end_date = date(2023, 12, 31)
            all_dates = pd.date_range(start_date, end_date, freq='B').date.tolist()
            num_holdout = int(len(all_dates) * 0.2)
            
            # Contiguous trailing block: Optimization period is first 80%, Holdout period is final 20%
            opt_dates = sorted(all_dates[:-num_holdout])
            holdout_dates = sorted(all_dates[-num_holdout:])
            
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
