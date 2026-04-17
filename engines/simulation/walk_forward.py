"""
K-Fold Anchored Walk-Forward Validator (Phase 5).

Implements expanding-window walk-forward to compute Walk-Forward Efficiency (WFE).

Design constraints:
  - Fold boundaries are CHRONOLOGICAL and CONTIGUOUS — not random.
  - Operates ONLY on the 80% optimization dates. The held-out 20% partition
    must be sealed before this validator runs. Walk-forward folds and held-out
    dates are guaranteed mutually exclusive because the caller passes only
    opt_dates (already excluding holdout).
  - Explicit price_cache dict passed to every fold — no implicit caching.
  - If fewer than 4 valid folds remain (< 20 test days each), raises
    InsufficientDataError rather than returning a misleading WFE.

WFE = mean(OOS Sharpe across k valid folds) / full IS Sharpe
"""
from dataclasses import dataclass, field
from datetime import date
from typing import List, Dict, Optional, Tuple, Any

import numpy as np
import pandas as pd

from config.schema import AegisConfig


class InsufficientDataError(Exception):
    """Raised when fewer than 4 valid folds remain after filtering short folds."""
    pass


MIN_TEST_DAYS = 20
MIN_VALID_FOLDS = 4


@dataclass
class FoldResult:
    fold_index:     int
    train_start:    date
    train_end:      date
    test_start:     date
    test_end:       date
    is_sharpe:      float   # Sharpe computed on the training period's returns
    oos_sharpe:     float   # Sharpe computed on the test period's returns
    n_train_days:   int
    n_test_days:    int
    skipped:        bool    # True if fold had < MIN_TEST_DAYS test days


@dataclass
class WalkForwardResult:
    wfe:                    float
    fold_results:           List[FoldResult]
    n_folds_valid:          int
    n_folds_negative_oos:   int     # how many folds lost money OOS
    is_sharpe:              float   # full optimization-period IS Sharpe
    mean_oos_sharpe:        float
    failure_context:        str     # human-readable for Builder prompt injection


class WalkForwardValidator:
    """
    Anchored walk-forward with expanding training window.

    Splits the optimization period into (n_folds + 1) equal chronological
    chunks. Chunk 0 is the mandatory initial training period. For fold k
    (k = 1..n_folds):
        Train: chunks 0 through k-1 (expanding)
        Test:  chunk k

    This guarantees every fold has a training window at least as large as
    one chunk, and the training window grows with each fold.
    """

    def __init__(self, config: AegisConfig, n_folds: int = 6):
        if n_folds < MIN_VALID_FOLDS:
            raise ValueError(f"n_folds must be >= {MIN_VALID_FOLDS}, got {n_folds}")
        self.config = config
        self.n_folds = n_folds

    def compute_fold_boundaries(
        self, opt_dates: List[date]
    ) -> List[Tuple[List[date], List[date]]]:
        """
        Compute (train_dates, test_dates) for each fold.

        Splits opt_dates into (n_folds + 1) equal chronological chunks.
        Chunk 0 = mandatory initial training. Fold k uses chunks 0..k-1
        for training and chunk k for testing.

        Returns list of n_folds (train_dates, test_dates) tuples.
        """
        n = len(opt_dates)
        n_chunks = self.n_folds + 1
        chunk_size = n // n_chunks

        # Build chunk boundaries
        chunks: List[List[date]] = []
        for i in range(n_chunks):
            start_idx = i * chunk_size
            # Last chunk absorbs remainder
            end_idx = (i + 1) * chunk_size if i < n_chunks - 1 else n
            chunks.append(opt_dates[start_idx:end_idx])

        # Build folds with expanding training window
        folds = []
        for k in range(1, n_chunks):  # k = 1..n_folds
            # Train: concatenate chunks 0 through k-1
            train_dates = []
            for c in range(k):
                train_dates.extend(chunks[c])
            test_dates = chunks[k]
            folds.append((train_dates, test_dates))

        return folds

    def _bulk_fetch_prices(
        self, tickers: List[str], start_date: date, end_date: date
    ) -> Dict[str, pd.DataFrame]:
        """
        Single bulk fetch of all price data for all tickers.
        Returns dict[ticker] -> DataFrame with columns [date, open, close, volume, ...].
        This is called ONCE before any folds run.
        """
        from engines.data_ingestion.connectors.yfinance_connector import YFinanceConnector
        yf = YFinanceConnector()

        cache: Dict[str, pd.DataFrame] = {}
        total_days = (end_date - start_date).days + 30  # buffer for lookback

        for ticker in tickers:
            df = yf.get_prices(ticker, days=total_days, as_of_date=end_date)
            if df is not None and not df.empty:
                df["_date_obj"] = pd.to_datetime(df["date"]).dt.date
                cache[ticker] = df
            else:
                print(f"[WalkForward] Warning: no price data for {ticker}")

        return cache

    def _run_fold_simulation(
        self,
        fold_train_dates: List[date],
        fold_test_dates: List[date],
        price_cache: Dict[str, pd.DataFrame],
    ) -> Tuple[float, float]:
        """
        Run a single fold: simulate over (train + test) dates, compute
        IS Sharpe from training returns and OOS Sharpe from test returns.

        Returns (is_sharpe, oos_sharpe).
        """
        from engines.simulation.loop import SimulationLoop
        from engines.simulation.metrics import compute_sharpe

        # Fresh simulation instance — no state leakage from other folds
        loop = SimulationLoop(self.config)

        # Run over all dates (train + test) so the strategy warms up during training
        all_dates = fold_train_dates + fold_test_dates
        fold_result = loop.run_fold(trading_dates=all_dates, price_cache=price_cache)

        # Build NAV DataFrame and split by train/test
        nav_df = pd.DataFrame(fold_result["nav_history"])
        if nav_df.empty:
            return 0.0, 0.0

        nav_df["date"] = pd.to_datetime(nav_df["date"])
        nav_df.set_index("date", inplace=True)
        nav_df["returns"] = nav_df["nav"].pct_change().fillna(0)

        train_set = set(fold_train_dates)
        test_set = set(fold_test_dates)

        train_mask = nav_df.index.map(lambda x: x.date() in train_set)
        test_mask = nav_df.index.map(lambda x: x.date() in test_set)

        is_sharpe = compute_sharpe(nav_df.loc[train_mask, "returns"])
        oos_sharpe = compute_sharpe(nav_df.loc[test_mask, "returns"])

        return is_sharpe, oos_sharpe

    def run(
        self,
        start_date: date,
        end_date: date,
        holdout_dates: Optional[List[date]] = None,
    ) -> WalkForwardResult:
        """
        Execute k-fold anchored walk-forward validation.

        Args:
            start_date: Backtest start date.
            end_date: Backtest end date.
            holdout_dates: Pre-sealed held-out dates (already excluded from opt).
                           If provided, walk-forward operates ONLY on the remaining
                           optimization dates. This guarantees mutual exclusivity.

        Returns:
            WalkForwardResult with WFE, per-fold data, and Builder failure context.

        Raises:
            InsufficientDataError: If fewer than 4 valid folds remain.
        """
        import hashlib

        # 1. Generate full trading calendar
        all_dates = pd.date_range(start_date, end_date, freq='B').date.tolist()

        # 2. Compute holdout dates (same deterministic logic as SimulationLoop)
        if holdout_dates is None:
            num_holdout = int(len(all_dates) * 0.2)
            seed_int = int(
                hashlib.md5(
                    self.config.run_id.encode('utf-8'), usedforsecurity=False
                ).hexdigest(), 16
            ) % (2 ** 32)
            rng = np.random.RandomState(seed_int)
            holdout_dates = sorted(
                rng.choice(all_dates, num_holdout, replace=False)
            )

        # 3. Optimization dates = full calendar MINUS held-out dates
        holdout_set = set(holdout_dates)
        opt_dates = sorted([d for d in all_dates if d not in holdout_set])

        if len(opt_dates) < (self.n_folds + 1) * MIN_TEST_DAYS:
            raise InsufficientDataError(
                f"Only {len(opt_dates)} optimization days — need at least "
                f"{(self.n_folds + 1) * MIN_TEST_DAYS} for {self.n_folds} folds "
                f"with {MIN_TEST_DAYS}-day minimum per chunk."
            )

        # 4. Compute chronological contiguous fold boundaries
        folds = self.compute_fold_boundaries(opt_dates)

        # 5. Bulk-fetch all price data ONCE
        tickers = self.config.asset_universe.tickers
        price_cache = self._bulk_fetch_prices(tickers, start_date, end_date)

        # 6. Run each fold
        fold_results: List[FoldResult] = []
        valid_oos_sharpes: List[float] = []

        for k, (train_dates, test_dates) in enumerate(folds):
            # Skip folds with insufficient test data
            if len(test_dates) < MIN_TEST_DAYS:
                fold_results.append(FoldResult(
                    fold_index=k,
                    train_start=train_dates[0] if train_dates else start_date,
                    train_end=train_dates[-1] if train_dates else start_date,
                    test_start=test_dates[0] if test_dates else start_date,
                    test_end=test_dates[-1] if test_dates else start_date,
                    is_sharpe=0.0, oos_sharpe=0.0,
                    n_train_days=len(train_dates), n_test_days=len(test_dates),
                    skipped=True,
                ))
                continue

            is_sharpe, oos_sharpe = self._run_fold_simulation(
                train_dates, test_dates, price_cache
            )

            fold_results.append(FoldResult(
                fold_index=k,
                train_start=train_dates[0],
                train_end=train_dates[-1],
                test_start=test_dates[0],
                test_end=test_dates[-1],
                is_sharpe=is_sharpe,
                oos_sharpe=oos_sharpe,
                n_train_days=len(train_dates),
                n_test_days=len(test_dates),
                skipped=False,
            ))
            valid_oos_sharpes.append(oos_sharpe)

        # 7. Enforce minimum valid folds
        n_valid = len(valid_oos_sharpes)
        if n_valid < MIN_VALID_FOLDS:
            raise InsufficientDataError(
                f"Only {n_valid} valid folds (need >= {MIN_VALID_FOLDS}). "
                f"{len(folds) - n_valid} folds skipped due to < {MIN_TEST_DAYS} test days."
            )

        # 8. Compute full IS Sharpe (across entire optimization period)
        #    We use the first fold's simulation with ALL opt dates for this
        from engines.simulation.loop import SimulationLoop
        from engines.simulation.metrics import compute_sharpe

        full_loop = SimulationLoop(self.config)
        full_result = full_loop.run_fold(trading_dates=opt_dates, price_cache=price_cache)

        full_nav = pd.DataFrame(full_result["nav_history"])
        if not full_nav.empty:
            full_nav["date"] = pd.to_datetime(full_nav["date"])
            full_nav.set_index("date", inplace=True)
            full_nav["returns"] = full_nav["nav"].pct_change().fillna(0)
            full_is_sharpe = compute_sharpe(full_nav["returns"])
        else:
            full_is_sharpe = 0.0

        # 9. Compute WFE
        from engines.simulation.metrics import compute_walk_forward_efficiency
        mean_oos = float(np.mean(valid_oos_sharpes))
        wfe = compute_walk_forward_efficiency(valid_oos_sharpes, full_is_sharpe)

        # 10. Diagnostics
        n_negative = sum(1 for s in valid_oos_sharpes if s < 0)

        # 11. Build failure context for Builder prompt injection
        context_lines = [
            f"WALK-FORWARD {'PASS' if wfe >= 0.50 else 'FAILURE'}: WFE={wfe:.3f} (threshold: 0.50)",
            f"  IS Sharpe: {full_is_sharpe:.2f} | Mean OOS Sharpe: {mean_oos:.2f}",
        ]
        for fr in fold_results:
            if fr.skipped:
                context_lines.append(
                    f"  Fold {fr.fold_index} ({fr.test_start} to {fr.test_end}): SKIPPED "
                    f"({fr.n_test_days} days < {MIN_TEST_DAYS} min)"
                )
            else:
                marker = " ← NEGATIVE" if fr.oos_sharpe < 0 else ""
                context_lines.append(
                    f"  Fold {fr.fold_index} ({fr.test_start} to {fr.test_end}): "
                    f"OOS Sharpe {fr.oos_sharpe:.2f}{marker}"
                )
        context_lines.append(
            f"  Negative OOS folds: {n_negative}/{n_valid}"
        )
        failure_context = "\n".join(context_lines)

        return WalkForwardResult(
            wfe=wfe,
            fold_results=fold_results,
            n_folds_valid=n_valid,
            n_folds_negative_oos=n_negative,
            is_sharpe=full_is_sharpe,
            mean_oos_sharpe=mean_oos,
            failure_context=failure_context,
        )
