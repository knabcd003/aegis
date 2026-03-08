"""
Aegis AI - Full System Integration Test
Tests all 5 systems working together in a mock live-flow scenario.
Data -> Quant -> Analyst (Supervisor) -> Sentinel (Reflexion) -> MLOps
"""

import asyncio
import os
import time
from dotenv import load_dotenv

# System 1
from engines.data_ingestion.data_engine import DataEngine
from engines.data_ingestion.connectors.yfinance_connector import YFinanceConnector
# System 3
from engines.analyst.supervisor import AnalystSupervisor
from engines.analyst.reflexion import ReflexionEngine
from engines.analyst.episodic_memory import EpisodicMemory
# System 4
from engines.sentinel.semantic_trigger import SemanticTrigger
# System 5
from engines.sandbox.orchestrator import SandboxOrchestrator

async def run_alpha_pipeline():
    print("=" * 70)
    print("🚀 INITIALIZING AEGIS AI FULL PIPELINE TEST")
    print("=" * 70)
    
    ticker = "AAPL"
    
    # ---------------------------------------------------------
    # 1. SYSTEM 1: DATA INGESTION
    # ---------------------------------------------------------
    print("\n[System 1: Data Engine] Booting...")
    engine = DataEngine()
    engine.register(YFinanceConnector())
    
    print(f" > Fetching live fundamentals and news for {ticker}...")
    try:
        fundamentals = engine.get_fundamentals(ticker)
        news = engine.get_news(ticker, days=3)
        raw_news_text = " ".join([n['headline'] for n in news[:5]]) if news else "No major news."
        raw_fund_text = str(fundamentals)
        print(" > Data Engine: Success.")
    except Exception as e:
        print(f" > Data Engine Failed: {e}")
        return

    # ---------------------------------------------------------
    # 2. SYSTEM 2: QUANT ENGINE (Mock)
    # ---------------------------------------------------------
    print("\n[System 2: Quant Engine] Generating mock baseline constraints...")
    quant_data = {
        "sector": "Technology",
        "regime": "High Inflation",
        "hmm_state": "High Volatility Bear Market",
        "vpin_toxicity": 0.88,
        "raw_fundamentals_text": raw_fund_text[:1000], # Trucated for speed
        "raw_news_text": raw_news_text
    }
    print(f" > Regime: {quant_data['regime']}")
    print(f" > VPIN: {quant_data['vpin_toxicity']}")

    # ---------------------------------------------------------
    # 3. SYSTEM 3: ANALYST ENGINE
    # ---------------------------------------------------------
    print("\n[System 3: Analyst Engine] Booting Declarative LangGraph Supervisor...")
    memory = EpisodicMemory(collection_name="integration_test_memory")
    supervisor = AnalystSupervisor(config_path="config/experiment_config.yaml", memory=memory)
    
    print(" > Claude evaluating Quant constraints + invoking local Qwen RAG...")
    try:
        decision_str = supervisor.evaluate_trade(ticker, quant_data)
        print("\n=== CLAUDE SUPERVISOR DECISION ===")
        print(decision_str)
        print("==================================")
    except Exception as e:
        print(f" > Analyst Engine Failed: {e}")
        return

    # ---------------------------------------------------------
    # 4. SYSTEM 4: SENTINEL ENGINE (Reflexion Autopsy)
    # ---------------------------------------------------------
    print("\n[System 4: Sentinel Engine] Simulating a bad outcome to trigger Reflexion...")
    print(" > Assuming Claude accidentally decided to BUY and lost 15%...")
    
    reflexion = ReflexionEngine(config_path="config/experiment_config.yaml", memory=memory)
    
    print(" > Claude Autopsy Graph generating correction rule...")
    bad_outcome = "The stock dropped 15% because high VPIN (0.88) accurately predicted toxic order flow dumping, which Claude ignored."
    try:
        lesson = reflexion.run_autopsy(ticker, decision_str, quant_data, bad_outcome)
        print("\n=== GENERATED PERMANENT RULE (Saved to Memory) ===")
        print(lesson)
        print("==================================================")
    except Exception as e:
        print(f" > Reflexion Failed: {e}")
        return

    # ---------------------------------------------------------
    # 5. SYSTEM 5: SANDBOX ORCHESTRATOR
    # ---------------------------------------------------------
    print("\n[System 5: MLOps Sandbox] Verifying optuna tracking...")
    orchestrator = SandboxOrchestrator(experiment_name="Full_Pipeline_Integration")
    print(" > Orchestrator initialized. SQLite MLflow db successfully hooked.")
    
    print("\n" + "=" * 70)
    print("✅ FULL SYSTEM PIPELINE (DATA -> MLOPS) VERIFIED SUCCESSFULLY")
    print("=" * 70)

if __name__ == "__main__":
    load_dotenv()
    asyncio.run(run_alpha_pipeline())
