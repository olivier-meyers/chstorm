"""Serial clustering of winter storms: is the historical record more clustered than Poisson?

The dispersion statistic phi = var / mean - 1 of storm counts per winter is 0 for a Poisson
process and > 0 when storms come in runs (Mailier et al. 2006, Mon. Wea. Rev. 134).
"""

import datetime as dt

import numpy as np
import pandas as pd


def winter_counts(date_ordinals: np.ndarray) -> pd.Series:
    """Storms per winter season. A season is labelled by the year it starts in (Jul-Jun)."""
    d = pd.to_datetime([dt.date.fromordinal(int(o)) for o in date_ordinals])
    season = np.where(d.month >= 7, d.year, d.year - 1)
    c = pd.Series(season).value_counts()
    return c.reindex(pd.RangeIndex(season.min(), season.max() + 1), fill_value=0).sort_index()


def dispersion(counts: np.ndarray) -> tuple[float, float]:
    """phi = var / mean - 1 and its standard error under Poisson, sqrt(2 / (n - 1)).

    The standard error is the large-sample value for the index of dispersion; with short records it
    is the main point: 70-odd winters cannot separate phi = 0 from moderate clustering.
    """
    c = np.asarray(counts, float)
    return float(c.var(ddof=1) / c.mean() - 1.0), float(np.sqrt(2.0 / (len(c) - 1)))
