import argparse
import sys
import os
from dotenv import load_dotenv

# Load all environment variables before initializing any modules
load_dotenv()

from graph.workflow import build_trading_graph
from agents.sentinel import SentinelAgent

def run_trading_pipeline(ticker: str):
    print(f"=== Starting Autonomous Trading Pipeline for {ticker} ===")
    
    app = build_trading_graph()
    
    initial_state = {
        "ticker": ticker.upper(),
        "prices": [],
        "research_data": {},
        "quant_data": {},
        "analyst_decision": None,
        "thesis": None,
        "order": None,
        "error": None
    }
    
    try:
        # Run the compiled graph
        result = app.invoke(initial_state)
        
        print("\n=== Pipeline Execution Summary ===")
        print(f"Target: {result.get('ticker')}")
        
        if result.get("error"):
            print(f"Status: ERROR - {result['error']}")
        else:
            quant = result.get("quant_data", {})
            print(f"Quant Decision: {quant.get('decision')}")
            print(f"Recommended Size: {quant.get('recommended_shares')} shares (${quant.get('recommended_allocation_usd', 0):.2f})")
            
            analyst_dec = result.get("analyst_decision")
            print(f"Analyst Output: {analyst_dec}")
            
            if analyst_dec == "BUY_EXECUTED":
                print("\nInvestment Thesis Stored:")
                print(result.get("thesis", ""))
                print(f"\nOrder Details: {result.get('order')}")
                
    except Exception as e:
        print(f"Critical error executing pipeline: {e}")

def run_sentinel():
    print("=== Starting Sentinel Portfolio Monitor ===")
    try:
        sentinel = SentinelAgent()
        sentinel.review_portfolio()
    except Exception as e:
        print(f"Critical error running Sentinel: {e}")

def main():
    parser = argparse.ArgumentParser(description="Aegis Autonomous Trading Prototype")
    
    subparsers = parser.add_subparsers(dest="command", help="Available commands")
    
    # Trade Command
    trade_parser = subparsers.add_parser("trade", help="Run the research and execution pipeline for a specific ticker")
    trade_parser.add_argument("--ticker", "-t", required=True, type=str, help="Ticker symbol to analyze (e.g. AAPL)")
    
    # Monitor Command
    monitor_parser = subparsers.add_parser("monitor", help="Run the Sentinel agent to monitor open positions")
    
    args = parser.parse_args()
    
    if args.command == "trade":
        run_trading_pipeline(args.ticker)
    elif args.command == "monitor":
        run_sentinel()
    else:
        parser.print_help()

if __name__ == "__main__":
    main()
