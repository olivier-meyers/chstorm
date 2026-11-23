"""Event loss table (ELT) and year loss table (YLT).

CLIMADA returns one loss per event plus an annual frequency, not a simulated timeline.
M2 turns that into simulated years (Poisson occurrence) so OEP and AEP can be read off a YLT;
the two builders below are the shared format, copied from chquake.
"""

import numpy as np
import pandas as pd


def build_elt(event_id: np.ndarray, year: np.ndarray, loss: np.ndarray) -> pd.DataFrame:
    """Event loss table: one row per event with its simulated year and ground-up loss."""
    return pd.DataFrame({"event_id": event_id, "year": year, "loss": loss})


def build_ylt(elt: pd.DataFrame, n_years: int, loss_col: str = "loss") -> pd.DataFrame:
    """Year loss table over years 0..n_years-1, including years with no events or no loss.

    agg_loss = sum of event losses in the year (-> AEP); max_loss = largest single event
    loss in the year (-> OEP).
    """
    if len(elt) and (elt["year"].min() < 0 or elt["year"].max() >= n_years):
        raise ValueError("ELT years outside 0..n_years-1")
    g = elt.groupby("year")[loss_col]
    ylt = pd.DataFrame(index=pd.RangeIndex(n_years, name="year"))
    ylt["agg_loss"] = g.sum().reindex(ylt.index, fill_value=0.0)
    ylt["max_loss"] = g.max().reindex(ylt.index, fill_value=0.0)
    ylt["n_events"] = g.size().reindex(ylt.index, fill_value=0).astype(int)
    return ylt
