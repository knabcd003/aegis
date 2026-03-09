from datetime import date
from typing import Dict, Any

from engines.data_ingestion.connectors.fred_connector import FREDConnector


class MacroOverlay:
    """
    Provides macroeconomic context based on FRED indicators like Fed Funds Rate and Treasury Yields.
    """
    def __init__(self):
        self.fred = FREDConnector()

    def compute(self, as_of_date: date) -> Dict[str, Any]:
        """
        Input: FRED series, `as_of_date`
        Output: {macro_regime: "tightening"|"easing"|"stable", yield_curve: "inverted"|"flat"|"normal"}
        """
        macro_data = self.fred.get_macro(as_of_date=as_of_date)
        
        regime = "stable"
        if "fed_funds_rate" in macro_data and macro_data["fed_funds_rate"]:
            # Compare current to some hypothetical past or just base on levels if absolute.
            # Here we just set stable for simplicity as per blueprint.
            # In Phase 4, plugins logic handles actual derivative computation.
            rate = macro_data["fed_funds_rate"].get("value", 0)
            if rate > 4.5:
                regime = "tightening"
            elif rate < 2.0:
                regime = "easing"
                
        yield_curve = "normal"
        if "treasury_spread" in macro_data and macro_data["treasury_spread"]:
            spread = macro_data["treasury_spread"].get("value", 0)
            if spread < -0.1:
                yield_curve = "inverted"
            elif spread < 0.1:
                yield_curve = "flat"
                
        return {
            "macro_regime": regime,
            "yield_curve": yield_curve
        }
