"""Cat XL against hand-computed cases."""

import numpy as np
import pytest

from chstorm.financial import cat_xl, layer_recoveries


def test_layer_recoveries() -> None:
    # 100 xs 50: below, inside, above the layer.
    np.testing.assert_allclose(layer_recoveries(np.array([30, 80, 500]), 100, 50), [0, 30, 100])


def test_cat_xl_hand_case() -> None:
    # 100 xs 50, 1 reinstatement at 100 %, three years:
    #   year 0: events 80, 200 -> recoveries 30 + 100 = 130 (<= 200 aggregate) ; reinstated 1.0
    #   year 1: three events of 300 -> 3 x 100 = 300, capped at 200          ; reinstated 1.0
    #   year 2: no events                                                   ; 0
    # E[recovery] = 330 / 3 = 110; E[reinstated] = 2/3; P = 110 / (1 + 2/3) = 66.
    # Check: P + E[reinstatement premium] = 66 + 66 * 2/3 = 110 = E[recovery].
    loss = np.array([80.0, 200.0, 300.0, 300.0, 300.0])
    year = np.array([0, 0, 1, 1, 1])
    ylt, s = cat_xl(
        loss, year, 3, limit=100, attachment=50, reinstatements=1, reinstatement_rate=1.0
    )
    np.testing.assert_allclose(ylt["recovery"], [130, 200, 0])
    np.testing.assert_allclose(ylt["reinstated"], [1.0, 1.0, 0.0])
    assert s["expected_recovery"] == pytest.approx(110)
    assert s["pure_premium"] == pytest.approx(66)
    assert s["rate_on_line"] == pytest.approx(0.66)
    assert s["p_attach"] == pytest.approx(2 / 3)
    assert s["p_exhaust"] == pytest.approx(1 / 3)


def test_cat_xl_without_reinstatement_is_one_limit_per_year() -> None:
    ylt, s = cat_xl(np.array([300.0, 300.0]), np.array([0, 0]), 1, 100, 50, 0, 1.0)
    assert ylt["recovery"].iloc[0] == 100
    assert s["pure_premium"] == pytest.approx(100)  # no reinstatement premium to offset
