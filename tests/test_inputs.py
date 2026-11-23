"""Exposure rescaling keeps the spatial pattern and hits the target total."""

import numpy as np
import pytest

from chstorm.inputs import scale_to_total


def test_scale_to_total_keeps_shares():
    v = np.array([1.0, 3.0, 6.0])
    out = scale_to_total(v, 2.5e12)
    assert out.sum() == pytest.approx(2.5e12)
    np.testing.assert_allclose(out / out.sum(), v / v.sum())


def test_scale_to_total_rejects_empty():
    with pytest.raises(ValueError):
        scale_to_total(np.zeros(3), 1.0)
