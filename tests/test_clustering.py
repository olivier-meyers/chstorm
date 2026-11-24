import datetime as dt

import numpy as np

from chstorm.clustering import dispersion, winter_counts
from chstorm.impact import sample_counts, sample_ylt


def test_winter_counts_split_at_july_and_fill_gaps():
    days = ["1999-12-26", "2000-02-10", "2001-11-01"]
    c = winter_counts(np.array([dt.date.fromisoformat(d).toordinal() for d in days]))
    assert c.to_dict() == {1999: 2, 2000: 0, 2001: 1}


def test_dispersion_zero_for_poisson():
    rng = np.random.default_rng(0)
    phi, se = dispersion(rng.poisson(2.0, 50_000))
    assert abs(phi) < 0.03 and se < 0.01


def test_negative_binomial_keeps_mean_adds_variance():
    rng = np.random.default_rng(1)
    c = sample_counts(2.0, 200_000, rng, dispersion=1.0)
    assert abs(c.mean() - 2.0) < 0.02
    assert abs(c.var() / c.mean() - 2.0) < 0.05  # var/mean = 1 + phi


def test_clustering_keeps_aal():
    loss, freq = np.array([1.0, 100.0]), np.array([1.5, 0.05])
    _, y0 = sample_ylt(loss, freq, 200_000, seed=3)
    _, y1 = sample_ylt(loss, freq, 200_000, seed=3, dispersion=1.0)
    assert abs(y1["agg_loss"].mean() / y0["agg_loss"].mean() - 1) < 0.03
