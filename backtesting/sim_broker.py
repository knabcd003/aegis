"""
Simulated Broker — In-memory paper portfolio tracker for backtesting.
Mirrors the AlpacaClient interface so agents can run unchanged.
"""
from typing import Dict, Any, List, Optional
from datetime import datetime


class SimulatedBroker:
    """
    Simulates trade execution against historical prices.
    Tracks positions, cash, trade history, and daily equity snapshots.
    """

    def __init__(self, starting_cash: float = 50000.0):
        self.starting_cash = starting_cash
        self.cash = starting_cash
        self.positions: Dict[str, Dict[str, Any]] = {}  # symbol → {qty, avg_entry_price}
        self.trade_log: List[Dict[str, Any]] = []
        self.equity_history: List[Dict[str, Any]] = []  # [{date, equity, cash}]
        self._trade_counter = 0

    # ── AlpacaClient-compatible interface ────────────────────────────────

    def get_account_balance(self) -> float:
        return self.cash

    def get_portfolio_metrics(self) -> Dict[str, Any]:
        """Returns portfolio value (requires mark-to-market call first)."""
        total = self.cash + sum(
            pos["qty"] * pos.get("current_price", pos["avg_entry_price"])
            for pos in self.positions.values()
        )
        return {
            "total_value": total,
            "daily_pnl": 0.0,
            "pnl_percentage": 0.0,
            "available_cash": self.cash,
        }

    def get_open_positions(self) -> List[Dict[str, Any]]:
        return [
            {
                "symbol": sym,
                "qty": pos["qty"],
                "market_value": pos["qty"] * pos.get("current_price", pos["avg_entry_price"]),
                "avg_entry_price": pos["avg_entry_price"],
                "current_price": pos.get("current_price", pos["avg_entry_price"]),
                "unrealized_pl": pos["qty"] * (pos.get("current_price", pos["avg_entry_price"]) - pos["avg_entry_price"]),
            }
            for sym, pos in self.positions.items()
            if pos["qty"] > 0
        ]

    def execute_trade(
        self, symbol: str, qty: float, side: str, fill_price: Optional[float] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Simulates a market order fill at the given fill_price.
        If fill_price is None, uses the position's current_price (for sells).
        """
        self._trade_counter += 1
        order_id = f"SIM-{self._trade_counter:06d}"

        if fill_price is None and side == "sell":
            pos = self.positions.get(symbol, {})
            fill_price = pos.get("current_price", pos.get("avg_entry_price", 0))

        if fill_price is None or fill_price <= 0:
            return None

        cost = qty * fill_price

        if side == "buy":
            if cost > self.cash:
                # Not enough cash — buy what we can
                qty = int(self.cash // fill_price)
                if qty <= 0:
                    return None
                cost = qty * fill_price

            self.cash -= cost

            if symbol in self.positions:
                existing = self.positions[symbol]
                total_qty = existing["qty"] + qty
                avg_price = (
                    (existing["avg_entry_price"] * existing["qty"]) + (fill_price * qty)
                ) / total_qty
                existing["qty"] = total_qty
                existing["avg_entry_price"] = avg_price
            else:
                self.positions[symbol] = {
                    "qty": qty,
                    "avg_entry_price": fill_price,
                    "current_price": fill_price,
                }

        elif side == "sell":
            if symbol not in self.positions or self.positions[symbol]["qty"] < qty:
                return None  # Can't sell what we don't own

            self.cash += cost
            self.positions[symbol]["qty"] -= qty

            if self.positions[symbol]["qty"] <= 0:
                del self.positions[symbol]

        order = {
            "id": order_id,
            "symbol": symbol,
            "qty": float(qty),
            "filled_avg_price": fill_price,
            "status": "filled",
            "side": side,
            "timestamp": datetime.now().isoformat(),
        }
        self.trade_log.append(order)
        return order

    # ── Backtesting utilities ───────────────────────────────────────────

    def mark_to_market(self, current_prices: Dict[str, float], date: str):
        """
        Updates all position current_prices and records an equity snapshot.
        Called once per simulated trading day.
        """
        for symbol, pos in self.positions.items():
            if symbol in current_prices:
                pos["current_price"] = current_prices[symbol]

        total_equity = self.cash + sum(
            pos["qty"] * pos.get("current_price", pos["avg_entry_price"])
            for pos in self.positions.values()
        )

        self.equity_history.append({
            "date": date,
            "equity": total_equity,
            "cash": self.cash,
            "num_positions": len(self.positions),
        })

    def get_equity_curve(self) -> List[Dict[str, Any]]:
        return self.equity_history

    def get_trade_log(self) -> List[Dict[str, Any]]:
        return self.trade_log

    def get_total_return(self) -> float:
        if not self.equity_history:
            return 0.0
        final = self.equity_history[-1]["equity"]
        return ((final - self.starting_cash) / self.starting_cash) * 100

    def reset(self):
        """Clears all state for a fresh backtest run."""
        self.cash = self.starting_cash
        self.positions.clear()
        self.trade_log.clear()
        self.equity_history.clear()
        self._trade_counter = 0
