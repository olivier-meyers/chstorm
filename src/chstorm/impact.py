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
from climada.entity import ImpactFuncSet
from climada.entity.impact_funcs.storm_europe import ImpfStormEurope

from chstorm.losses import build_elt, build_ylt


def make_impf_set(name: str = "schwierz2010") -> ImpactFuncSet:
    """Impact function set (haz_type WS, id 1) for the named curve."""
    builders = {
        "schwierz2010": ImpfStormEurope.from_schwierz,
        "welker2021": ImpfStormEurope.from_welker,
    }
    if name not in builders:
        raise ValueError(f"unknown vulnerability curve: {name}")
    return ImpactFuncSet([builders[name]()])


def event_losses(haz, exp, impf_set) -> np.ndarray:
    """Ground-up loss (CHF) per event in the hazard set."""
    return ImpactCalc(exp, impf_set, haz).impact(save_mat=False).at_event


def sample_ylt(
    loss: np.ndarray, freq: np.ndarray, n_years: int, seed: int = 0
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Poisson occurrence: returns (elt, ylt). ELT has one row per simulated storm occurrence."""
    rng = np.random.default_rng(seed)
    lam = float(freq.sum())
    counts = rng.poisson(lam, n_years)
    year = np.repeat(np.arange(n_years), counts)
    event_idx = rng.choice(len(loss), size=counts.sum(), p=freq / lam)
    elt = build_elt(event_idx, year, loss[event_idx])
    return elt, build_ylt(elt, n_years)
