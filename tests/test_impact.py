import numpy as np

from chstorm.impact import calibration_scale, make_impf_set, sample_ylt


def test_calibration_scale():
    assert calibration_scale(2.0, 10.0) == 5.0


def test_scaled_curve_capped_at_one():
    impf = make_impf_set("welker2021", scale=1e6).get_func()["WS"][1]
    assert impf.mdd.max() == 1.0


def test_power_curve_shape():
    impf = make_impf_set("power3").get_func()["WS"][1]
    assert impf.calc_mdr(np.array([25.0]))[0] == 0.0
    assert np.isclose(impf.calc_mdr(np.array([60.0]))[0], 1.0)
    assert np.isclose(impf.calc_mdr(np.array([46.0]))[0], 0.6**3)  # 21/35 of the way -> 0.216


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
