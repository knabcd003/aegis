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
from engines.simulation.metrics import compute_metrics
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
            # 5. Run Backtest
            sim_loop = SimulationLoop(config)
            start_date = date(2023, 1, 1)
            end_date = date(2023, 12, 31)
            
            logger.log_run_start(holdout_dates=[]) 
            results = sim_loop.run(start_date, end_date)
            
            # 6. Calculate & Log Metrics
            metrics = compute_metrics(
                results["nav_history"],
                results["trade_log"],
                results["holdout_dates"]
            )
            
            logger.log_run_end(
                metrics=metrics,
                trade_log=results["trade_log"],
                nav_history=results["nav_history"],
                gate_events=results["gate_events"]
            )
            
            # 7. Broadcast Event: Pipeline Success
            await broadcaster.broadcast({
                "event_id": f"evt_{uuid.uuid4().hex[:6]}",
                "workflow_id": run_id,
                "timestamp": datetime.now().isoformat(),
                "event_type": "node_success",
                "node_id": "darwinian_sandbox",
                "payload": {"sharpe": metrics.get("sharpe", 0.0)}
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
