import os
import sys
from dotenv import load_dotenv

# Add the project root to the python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from tools.market_api import AlpacaClient

def run_test():
    load_dotenv()
    
    # Check if keys are present (even if dummy) to proceed
    if not os.getenv("ALPACA_API_KEY"):
        print("Please set ALPACA_API_KEY in .env file to run this test.")
        return

    print("--- Testing Alpaca Client Connection ---")
    try:
        client = AlpacaClient()
        
        balance = client.get_account_balance()
        print(f"Account Balance: ${balance:,.2f}")
        
        symbol = "AAPL"
        print(f"\nRetrieving historical prices for {symbol} (Last 5 days):")
        prices = client.get_historical_prices(symbol, days=5)
        for p in prices:
            print(f"  {p['date']}: Close=${p['close']:.2f}, Vol={p['volume']}")
            
        print("\nRetrieving open positions...")
        positions = client.get_open_positions()
        if not positions:
            print("  No open positions.")
        else:
            for pos in positions:
                print(f"  {pos['symbol']}: {pos['qty']} shares @ ${pos['current_price']:.2f} (P&L: ${pos['unrealized_pl']:.2f})")
                
        print("\nAlpaca API connection test completed successfully!")
        
    except Exception as e:
        print(f"\nTest failed with error: {e}")
        print("This is expected if using dummy API keys.")

if __name__ == "__main__":
    run_test()
