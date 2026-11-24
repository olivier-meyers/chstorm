"""M2: vulnerability, per-event loss (ELT) and Poisson-sampled year loss table (YLT).

Vulnerability: ImpfStormEurope.from_schwierz is CLIMADA's storm damage curve. It maps peak gust
to a mean damage ratio (share of value lost) with a steep cubic rise above a gust threshold, so
only the strongest storms cause material loss. Source: Schwierz et al. 2010, Clim. Change 101.

Occurrence: the event set gives one annual frequency per event, not a timeline. We draw the
number of storms per simulated year from Poisson(sum of frequencies) and pick each storm in
proportion to its frequency. Poisson is the standard cat-model assumption for event counts.
"""

import numpy as np
import pandas as pd
from climada.engine import ImpactCalc
from climada.entity import ImpactFunc, ImpactFuncSet
from climada.entity.impact_funcs.storm_europe import ImpfStormEurope

from chstorm.losses import build_elt, build_ylt

POWER_THRESHOLD_MS = 25.0  # gust below which no damage; = where the Schwierz curve starts


def power_impf(n: float, threshold: float = POWER_THRESHOLD_MS) -> ImpactFunc:
    """Damage ratio = ((gust - threshold) / (60 - threshold))^n, 0 below threshold.

    A one-parameter family to test curve SHAPE: n = 3 is the cubic law of Klawa & Ulbrich
    (2003); n = 2 spreads loss over moderate storms, n = 5 concentrates it in the extremes.
    The level (value at 60 m/s) is arbitrary because it is calibrated away afterwards.
    """
    v = np.arange(0.0, 101.0)
    return ImpactFunc(
        haz_type="WS",
        id=1,
        intensity=v,
        mdd=np.clip((v - threshold) / (60.0 - threshold), 0.0, None) ** n,
        paa=np.ones_like(v),
        intensity_unit="m/s",
        name=f"power{n:g}",
    )


def make_impf_set(name: str = "schwierz2010", scale: float = 1.0) -> ImpactFuncSet:
    """Impact function set (haz_type WS, id 1) for the named curve.

    Names: schwierz2010, welker2021, or power<n> (e.g. power3). `scale` multiplies the mean
    damage degree (capped at 100%). This is how the curve is calibrated to a known historical
    loss: shape from the literature, level from claims.
    """
    builders = {
        "schwierz2010": ImpfStormEurope.from_schwierz,
        "welker2021": ImpfStormEurope.from_welker,
    }
    if name.startswith("power"):
        impf = power_impf(float(name[5:]))
    elif name in builders:
        impf = builders[name]()
    else:
        raise ValueError(f"unknown vulnerability curve: {name}")
    impf.mdd = np.minimum(impf.mdd * scale, 1.0)
    return ImpactFuncSet([impf])


def calibration_scale(modelled: float, target: float) -> float:
    """Damage scale factor so a historical event's modelled loss matches its observed loss.

    Exact while no point hits the 100% damage cap (true here: damage ratios stay at a few %).
    """
    if modelled <= 0:
        raise ValueError("event has zero modelled loss; cannot calibrate")
    return target / modelled


def event_losses(haz, exp, impf_set) -> np.ndarray:
    """Ground-up loss (CHF) per event in the hazard set."""
    return ImpactCalc(exp, impf_set, haz).impact(save_mat=False).at_event


def sample_counts(lam: float, n_years: int, rng, dispersion: float = 0.0) -> np.ndarray:
    """Storms per year: Poisson if dispersion == 0, else negative binomial with the same mean.

    dispersion phi = var / mean - 1 (Mailier et al. 2006). phi > 0 means storms cluster: some
    winters get several (a persistent, strong jet), others almost none.
    """
    if dispersion <= 0:
        return rng.poisson(lam, n_years)
    r = lam / dispersion  # NB(r, p): mean r(1-p)/p = lam, var = lam (1 + phi)
    return rng.negative_binomial(r, r / (r + lam), n_years)


def sample_ylt(
    loss: np.ndarray, freq: np.ndarray, n_years: int, seed: int = 0, dispersion: float = 0.0
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Returns (elt, ylt). ELT has one row per simulated storm occurrence.

    Which storms occur is drawn independently of the count, so clustering here raises the number
    of storms in bad years but not their severity (intensity-dependent clustering is not modelled).
    """
    rng = np.random.default_rng(seed)
    lam = float(freq.sum())
    counts = sample_counts(lam, n_years, rng, dispersion)
    year = np.repeat(np.arange(n_years), counts)
    event_idx = rng.choice(len(loss), size=counts.sum(), p=freq / lam)
    elt = build_elt(event_idx, year, loss[event_idx])
    return elt, build_ylt(elt, n_years)
