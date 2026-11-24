import numpy as np

from chstorm.impact import sample_ylt


def test_ylt_aal_matches_analytic():
    loss = np.array([0.0, 10.0, 100.0])
    freq = np.array([1.0, 0.5, 0.1])
    _, ylt = sample_ylt(loss, freq, 200_000, seed=1)
    expected = (loss * freq).sum()  # 10*0.5 + 100*0.1 = 15
    assert abs(ylt["agg_loss"].mean() - expected) / expected < 0.02


def test_ylt_oep_le_aep():
    loss = np.array([5.0, 50.0])
    _, ylt = sample_ylt(loss, np.array([1.0, 0.2]), 5_000, seed=2)
    assert (ylt["max_loss"] <= ylt["agg_loss"]).all()
