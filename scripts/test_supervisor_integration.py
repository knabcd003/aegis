import os
from dotenv import load_dotenv
from engines.analyst.supervisor import AnalystSupervisor

def run_supervisor_test():
    print("=" * 60)
    print("🚀 INITIALIZING LANGGRAPH SUPERVISOR TEST")
    print("=" * 60)
    
    if not os.environ.get("ANTHROPIC_API_KEY"):
        print("ERROR: ANTHROPIC_API_KEY is not set in the environment.")
        return

    print("\n[System] Booting Analyst Supervisor (Claude 3.5 + Qwen 2.5)...")
    try:
        supervisor = AnalystSupervisor(config_path="config/experiment_config.yaml")
    except Exception as e:
        print(f"Failed to initialize Supervisor: {e}")
        return
        
    ticker = "AAPL"
    print(f"\n[Test] Evaluating mock quant baseline for {ticker}...")
    
    mock_quant_data = {
        "sector": "Technology",
        "regime": "High Inflation",
        "hmm_state": "High Volatility Bear Market",
        "vpin_toxicity": 0.88,
        "raw_fundamentals_text": (
            "Item 1A. Risk Factors. "
            "Our primary risk is the concentration of our manufacturing deeply tied to global supply chains "
            "that are susceptible to disruption. We anticipate a 10% YoY reduction in hardware margin due to macro impacts."
        ),
        "raw_news_text": (
            "Tech stocks fall as supply chain woes continue. Apple sees delays in new manufacturing sites. "
            "However, services revenue remains a strong bright spot for the company."
        )
    }
    
    print("\n[Execution] Passing data to LangGraph. Watch the node routing...")
    try:
        final_decision = supervisor.evaluate_trade(ticker, mock_quant_data)
        print("\n" + "=" * 50)
        print("🎯 FINAL CLAUDE SUPERVISOR DECISION:")
        print("=" * 50)
        print(final_decision)
    except Exception as e:
        print(f"Graph execution failed: {e}")

if __name__ == "__main__":
    load_dotenv()
    run_supervisor_test()
