import os
import sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from typing import Dict, Any, List
from langchain_core.prompts import PromptTemplate
from langchain_anthropic import ChatAnthropic
from tools.market_api import AlpacaClient, FMPClient
from tools.calculators import TradingCalculators
from memory.db_helpers import MemoryManager

class SentinelAgent:
    """
    Monitoring Loop (The Sentinel).
    Reviews open positions against their original thesis and technical limits.
    Executes SELL orders if conditions are breached.
    """
    def __init__(self):
        self.alpaca = AlpacaClient()
        self.fmp = FMPClient()
        self.db = MemoryManager()
        
        self.llm = ChatAnthropic(
            model="claude-3-5-sonnet-20240620",
            temperature=0.1
        )
        
        self.verification_prompt = PromptTemplate.from_template(
            "You are an algorithmic risk manager. Review the original investment thesis for {ticker} "
            "against the most recent metric update. Determine if the fundamental basis of the trade is BROKEN or INTACT.\n\n"
            "Original Thesis:\n{thesis}\n\n"
            "Recent Data Update:\n{recent_data}\n\n"
            "Output exactly one word: BROKEN or INTACT."
        )

    def review_portfolio(self):
        """
        Main entry point for the Sentinel. Usually run asynchronously on a cron.
        """
        open_positions = self.alpaca.get_open_positions()
        print(f"[Sentinel] Initiating portfolio review for {len(open_positions)} open positions.")
        
        for pos in open_positions:
            self._evaluate_position(pos)
            
    def _evaluate_position(self, pos: Dict[str, Any]):
        ticker = pos["symbol"]
        qty = pos["qty"]
        entry_price = pos["avg_entry_price"]
        current_price = pos["current_price"]
        
        print(f"\n[Sentinel] Evaluating {ticker} | Entry: ${entry_price:.2f} | Current: ${current_price:.2f}")
        
        exit_reason = None
        
        try:
            # 1. Check Hard Take-Profit & Stop-Loss (assuming default 5% ATR proxy for prototype)
            atr_proxy = entry_price * 0.05
            stop_loss = TradingCalculators.calculate_stop_loss_price(entry_price, atr_proxy, 2.0)
            take_profit = TradingCalculators.calculate_take_profit_price(entry_price, atr_proxy, 3.0)
            
            if current_price <= stop_loss:
                exit_reason = f"STOP_LOSS_HIT (Price < ${stop_loss:.2f})"
            elif current_price >= take_profit:
                exit_reason = f"TAKE_PROFIT_HIT (Price > ${take_profit:.2f})"
                
            # 2. Check Fundamental Thesis (if technicals are intact)
            if not exit_reason:
                # Retrieve closest/latest thesis
                theses = self.db.get_all_theses_for_symbol(ticker)
                if theses:
                    # Sort desc by timestamp or assume latest
                    latest_thesis = theses[-1]
                    
                    # Fetch recent data
                    metrics = self.fmp.get_company_metrics(ticker)
                    
                    prompt_val = self.verification_prompt.format(
                        ticker=ticker,
                        thesis=latest_thesis.get("document", ""),
                        recent_data=str(metrics)
                    )
                    
                    response = self.llm.invoke(prompt_val)
                    judgment = response.content.strip().upper()
                    
                    if "BROKEN" in judgment:
                        exit_reason = "FUNDAMENTAL_THESIS_BROKEN"
            
            # 3. Execute Exit if needed
            if exit_reason:
                print(f"[Sentinel] Exit triggered for {ticker}: {exit_reason}. Executing SELL.")
                order = self.alpaca.execute_trade(symbol=ticker, qty=qty, side="sell")
                if order:
                    self.db.log_trade(trade_data=order, exit_reason=exit_reason)
                    print(f"[Sentinel] Successfully closed {ticker} and logged post-mortem.")
                else:
                    print(f"[Sentinel] Failed to execute SELL for {ticker}.")
            else:
                print(f"[Sentinel] Position {ticker} is INTACT. Holding.")
                
        except Exception as e:
            print(f"[Sentinel] Error evaluating position {ticker}: {e}")
