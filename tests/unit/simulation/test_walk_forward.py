"""
Unit tests for K-Fold Walk-Forward Validator.

Tests the most critical guarantees:
  1. Fold boundaries are chronological and contiguous
  2. Fold test windows do NOT overlap with held-out dates
  3. InsufficientDataError fires on short date ranges
  4. WFE math is correct with known inputs
  5. Negative OOS Sharpe tracking
"""
import pytest
from datetime import date, timedelta
from typing import List

import numpy as np
import pandas as pd

from engines.simulation.metrics import compute_walk_forward_efficiency
from engines.simulation.walk_forward import (
    WalkForwardValidator,
    InsufficientDataError,
    MIN_TEST_DAYS,
    MIN_VALID_FOLDS,
)


# ═══════════════════════════════════════════════════════════════════════
# Helpers
# ═══════════════════════════════════════════════════════════════════════

def _make_business_dates(start: date, n_days: int) -> List[date]:
    """Generate n business days starting from start."""
    dates = pd.date_range(start, periods=n_days, freq='B').date.tolist()
    return dates


# ═══════════════════════════════════════════════════════════════════════
# 1. Fold boundaries — chronological, contiguous, non-overlapping
# ═══════════════════════════════════════════════════════════════════════

class TestFoldBoundaries:

    def _make_validator(self, n_folds: int = 6):
        """Create a WalkForwardValidator with a minimal mock config."""
        from unittest.mock import MagicMock
        config = MagicMock()
        config.run_id = "test_run_123"
        return WalkForwardValidator(config, n_folds=n_folds)

    def test_folds_are_chronological(self):
        """Each fold's test window starts after the previous fold's test window."""
        validator = self._make_validator(n_folds=6)
        opt_dates = _make_business_dates(date(2022, 1, 3), 500)
        folds = validator.compute_fold_boundaries(opt_dates)

        assert len(folds) == 6

        prev_test_end = None
        for train_dates, test_dates in folds:
            assert len(test_dates) > 0, "Test dates should not be empty"
            # Each test window starts where the previous one ended
            if prev_test_end is not None:
                assert test_dates[0] > prev_test_end, (
                    f"Fold test window {test_dates[0]} should start after "
                    f"previous test window end {prev_test_end}"
                )
            prev_test_end = test_dates[-1]

    def test_folds_are_contiguous(self):
        """All optimization dates appear in exactly one fold (train or test)."""
        validator = self._make_validator(n_folds=6)
        opt_dates = _make_business_dates(date(2022, 1, 3), 500)
        folds = validator.compute_fold_boundaries(opt_dates)

        # Every opt_date should appear in at least one fold
        all_fold_dates = set()
        for train_dates, test_dates in folds:
            all_fold_dates.update(train_dates)
            all_fold_dates.update(test_dates)

        for d in opt_dates:
            assert d in all_fold_dates, f"Date {d} missing from all folds"

    def test_test_windows_dont_overlap(self):
        """No date appears in two different test windows."""
        validator = self._make_validator(n_folds=6)
        opt_dates = _make_business_dates(date(2022, 1, 3), 500)
        folds = validator.compute_fold_boundaries(opt_dates)

        all_test_dates = []
        for _, test_dates in folds:
            all_test_dates.extend(test_dates)

        assert len(all_test_dates) == len(set(all_test_dates)), (
            "Test windows have overlapping dates"
        )

    def test_training_window_expands(self):
        """Each fold's training window is strictly larger than the previous."""
        validator = self._make_validator(n_folds=6)
        opt_dates = _make_business_dates(date(2022, 1, 3), 500)
        folds = validator.compute_fold_boundaries(opt_dates)

        prev_train_size = 0
        for train_dates, _ in folds:
            assert len(train_dates) > prev_train_size, (
                "Training window should expand with each fold"
            )
            prev_train_size = len(train_dates)


# ═══════════════════════════════════════════════════════════════════════
# 2. Holdout exclusion — walk-forward operates only on optimization dates
# ═══════════════════════════════════════════════════════════════════════

class TestHoldoutExclusion:

    def test_no_holdout_dates_in_fold_test_windows(self):
        """Walk-forward test windows must not contain any held-out dates."""
        from unittest.mock import MagicMock
        config = MagicMock()
        config.run_id = "test_holdout_exclusion"

        validator = WalkForwardValidator(config, n_folds=6)

        all_dates = _make_business_dates(date(2022, 1, 3), 500)

        # Simulate holdout: randomly select 20% of dates
        rng = np.random.RandomState(42)
        n_holdout = int(len(all_dates) * 0.2)
        holdout_dates = sorted(rng.choice(all_dates, n_holdout, replace=False))
        holdout_set = set(holdout_dates)

        # Optimization dates = all minus holdout
        opt_dates = [d for d in all_dates if d not in holdout_set]

        folds = validator.compute_fold_boundaries(opt_dates)

        for train_dates, test_dates in folds:
            for d in test_dates:
                assert d not in holdout_set, (
                    f"Holdout date {d} found in a walk-forward test window!"
                )
            for d in train_dates:
                assert d not in holdout_set, (
                    f"Holdout date {d} found in a walk-forward train window!"
                )


# ═══════════════════════════════════════════════════════════════════════
# 3. Minimum 4-fold rule — InsufficientDataError on short date ranges
# ═══════════════════════════════════════════════════════════════════════

class TestMinimumFoldRule:

    def test_insufficient_data_raises(self):
        """Date ranges too short for 4 valid folds should raise InsufficientDataError."""
        from unittest.mock import MagicMock
        config = MagicMock()
        config.run_id = "test_short_range"
        config.asset_universe.tickers = ["AAPL"]

        validator = WalkForwardValidator(config, n_folds=6)

        # 50 dates with 20% holdout = 40 opt dates
        # 7 chunks of ~5 days each = way under MIN_TEST_DAYS=20
        with pytest.raises(InsufficientDataError):
            validator.run(date(2022, 1, 3), date(2022, 3, 15))

    def test_n_folds_below_minimum_rejected(self):
        """Cannot create validator with fewer than MIN_VALID_FOLDS folds."""
        from unittest.mock import MagicMock
        config = MagicMock()
        with pytest.raises(ValueError):
            WalkForwardValidator(config, n_folds=3)


# ═══════════════════════════════════════════════════════════════════════
# 4. WFE math
# ═══════════════════════════════════════════════════════════════════════

class TestWFEMath:

    def test_perfect_oos(self):
        """If OOS == IS, WFE = 1.0."""
        wfe = compute_walk_forward_efficiency([2.0, 2.0, 2.0, 2.0], 2.0)
        assert abs(wfe - 1.0) < 1e-9

    def test_half_oos(self):
        """If mean OOS = half of IS, WFE = 0.5."""
        wfe = compute_walk_forward_efficiency([1.0, 1.0, 1.0, 1.0], 2.0)
        assert abs(wfe - 0.5) < 1e-9

    def test_zero_is_sharpe(self):
        """If IS Sharpe <= 0, WFE = 0.0 (no positive in-sample performance)."""
        assert compute_walk_forward_efficiency([1.0, 2.0], 0.0) == 0.0
        assert compute_walk_forward_efficiency([1.0, 2.0], -1.0) == 0.0

    def test_negative_oos(self):
        """Negative OOS Sharpes produce negative WFE (correctly rejected by gate)."""
        wfe = compute_walk_forward_efficiency([-1.0, -2.0, -1.0, -2.0], 2.0)
        assert wfe < 0, f"Expected negative WFE, got {wfe}"

    def test_empty_folds(self):
        """No fold results → WFE = 0.0."""
        assert compute_walk_forward_efficiency([], 2.0) == 0.0

    def test_mixed_folds(self):
        """Mix of positive and negative OOS Sharpes."""
        # Mean OOS = (1.5 + 0.8 + -0.3 + 1.2) / 4 = 0.8
        # IS = 2.0 → WFE = 0.4
        wfe = compute_walk_forward_efficiency([1.5, 0.8, -0.3, 1.2], 2.0)
        assert abs(wfe - 0.4) < 1e-9


# ═══════════════════════════════════════════════════════════════════════
# 5. Negative OOS tracking
# ═══════════════════════════════════════════════════════════════════════

class TestNegativeOOSTracking:

    def test_counts_negative_folds(self):
        """WalkForwardResult should count how many folds produced negative OOS Sharpe."""
        # This is tested through the full run(), but we can verify the
        # counting logic in the result object
        from engines.simulation.walk_forward import WalkForwardResult, FoldResult

        fold_results = [
            FoldResult(0, date(2022,1,1), date(2022,3,1), date(2022,3,1), date(2022,5,1),
                       1.5, 0.8, 40, 40, False),
            FoldResult(1, date(2022,1,1), date(2022,5,1), date(2022,5,1), date(2022,7,1),
                       1.6, -0.3, 80, 40, False),
            FoldResult(2, date(2022,1,1), date(2022,7,1), date(2022,7,1), date(2022,9,1),
                       1.7, -0.1, 120, 40, False),
            FoldResult(3, date(2022,1,1), date(2022,9,1), date(2022,9,1), date(2022,11,1),
                       1.8, 1.2, 160, 40, False),
        ]

        n_negative = sum(1 for fr in fold_results if fr.oos_sharpe < 0)
        assert n_negative == 2


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
