"""Metrics: hand-computed return-period losses, OEP <= AEP, AAL = YLT mean."""

import numpy as np
import pandas as pd
import pytest

from chstorm.losses import build_elt, build_ylt
from chstorm.metrics import (
    aal,
    bootstrap_ci,
    convergence,
    ep_table,
    expected_shortfall_99,
    return_period_loss,
    tvar,
)


def _synthetic_elt(n_years: int, rate: float, seed: int) -> pd.DataFrame:
    """Compound Poisson catalogue: Poisson(rate) events per year, lognormal losses."""
    rng = np.random.default_rng(seed)
    counts = rng.poisson(rate, n_years)
    year = np.repeat(np.arange(n_years), counts)
    loss = rng.lognormal(mean=10, sigma=2, size=len(year))
    return build_elt(np.arange(len(year)), year, loss)


def test_return_period_loss_and_tvar_hand_case() -> None:
    # 100 years: 90 without loss, then losses 1..10. 50-yr loss = 2nd largest = 9.
    annual = np.r_[np.zeros(90), np.arange(1, 11)]
    assert return_period_loss(annual, 50) == 9
    assert return_period_loss(annual, 100) == 10
    assert return_period_loss(annual, 10) == 1
    assert tvar(annual, 50) == pytest.approx(9.5)  # mean of {10, 9}
    assert tvar(annual, 20) == pytest.approx(8.0)  # mean of {10, 9, 8, 7, 6}


def test_return_period_needs_enough_years() -> None:
    with pytest.raises(ValueError):
        return_period_loss(np.ones(100), 1000)  # 100 years cannot give a 1000-yr loss
    with pytest.raises(ValueError):
        return_period_loss(np.ones(100), 30)  # 100/30 is not a whole rank


def test_ylt_keeps_zero_years_and_splits_aggregate_and_max() -> None:
    elt = build_elt(np.arange(3), np.array([1, 1, 3]), np.array([5.0, 2.0, 4.0]))
    ylt = build_ylt(elt, n_years=5)
    assert len(ylt) == 5
    np.testing.assert_array_equal(ylt["agg_loss"], [0, 7, 0, 4, 0])
    np.testing.assert_array_equal(ylt["max_loss"], [0, 5, 0, 4, 0])
    np.testing.assert_array_equal(ylt["n_events"], [0, 2, 0, 1, 0])


def test_aal_equals_ylt_mean_and_elt_total_over_years() -> None:
    n = 10_000
    elt = _synthetic_elt(n, rate=0.8, seed=3)
    ylt = build_ylt(elt, n)
    assert aal(ylt) == pytest.approx(ylt["agg_loss"].mean())
    assert aal(ylt) == pytest.approx(elt["loss"].sum() / n)


def test_oep_never_exceeds_aep() -> None:
    n = 10_000
    ylt = build_ylt(_synthetic_elt(n, rate=2.0, seed=7), n)
    table = ep_table(ylt)
    assert (table["OEP"] <= table["AEP"]).all()
    assert (table["TVaR_OEP"] <= table["TVaR_AEP"]).all()
    assert (table["TVaR_AEP"] >= table["AEP"]).all()  # tail mean >= tail threshold
    assert table["AEP"].is_monotonic_increasing  # longer return period, larger loss
    assert expected_shortfall_99(ylt) == table.loc[100, "TVaR_AEP"]


def test_convergence_ends_at_full_catalogue() -> None:
    n = 10_000
    ylt = build_ylt(_synthetic_elt(n, rate=0.8, seed=11), n)
    conv = convergence(ylt["agg_loss"].to_numpy(), rp=200)
    assert conv["n_years"].iloc[-1] == n
    assert conv["aal"].iloc[-1] == pytest.approx(aal(ylt))


def test_bootstrap_interval_contains_point_estimate() -> None:
    n = 10_000
    annual = build_ylt(_synthetic_elt(n, rate=0.8, seed=5), n)["agg_loss"].to_numpy()
    ci = bootstrap_ci(annual, 200, np.random.default_rng(0), n_boot=300)
    lo, hi = ci["aal"]
    assert lo < annual.mean() < hi
    lo, hi = ci["loss_200"]
    assert lo <= return_period_loss(annual, 200) <= hi
