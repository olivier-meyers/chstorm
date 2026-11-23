"""M1: hazard (StormEurope footprints) and exposure (LitPop) for Switzerland.

Hazard: CLIMADA data-API dataset storm_europe_150arcsec_CHE (WISC). 142 historical winter
storms (1940-2013) plus 29 perturbed synthetic variants of each = 4260 events. Intensity is the
peak wind gust per grid cell (m/s). Every event gets the same annual frequency,
1 / (73 years x 30 variants), so the set as a whole reproduces the historical storm rate.

Exposure: LitPop (night lights x population) only gives the *spatial pattern* of value. We keep
the pattern and rescale the total to a cited Swiss building value, so the exposure reads as a
national property portfolio in CHF rather than World Bank produced capital in USD.
"""

import datetime as dt

import numpy as np
from climada.entity import Exposures
from climada.hazard import Hazard
from climada.util.api_client import Client


def load_hazard(cfg: dict) -> Hazard:
    """StormEurope event set for the configured country, current climate."""
    h = cfg["hazard"]
    return Client().get_hazard(
        "storm_europe",
        properties={"country_iso3alpha": h["region_country"], "climate_scenario": "None"},
        version=h["dataset_version"],
    )


def scale_to_total(values: np.ndarray, total: float) -> np.ndarray:
    """Keep each point's share of the total, rescale the sum to `total`."""
    s = values.sum()
    if s <= 0:
        raise ValueError("exposure values must have a positive sum")
    return values * (total / s)


def load_exposure(cfg: dict) -> Exposures:
    """LitPop CHE, rescaled to the configured building value and relabelled CHF."""
    e = cfg["exposure"]
    exp = Client().get_litpop(cfg["hazard"]["region_country"], version=e["litpop_version"])
    exp.gdf["value"] = scale_to_total(exp.gdf["value"].to_numpy(), float(e["total_value_chf"]))
    exp.value_unit = "CHF"
    # StormEurope impact functions are registered under haz_type "WS", id 1
    exp.gdf["impf_WS"] = 1
    return exp


def historical_mask(haz: Hazard) -> np.ndarray:
    """True for the 142 original (historical) storms, False for synthetic variants."""
    return np.asarray(haz.orig, dtype=bool)


def event_by_date(haz: Hazard, iso_date: str) -> int:
    """Index of the historical event on a given date (e.g. Lothar, '1999-12-26')."""
    ordinal = dt.date.fromisoformat(iso_date).toordinal()
    idx = np.where((haz.date == ordinal) & historical_mask(haz))[0]
    if len(idx) != 1:
        raise ValueError(f"expected one historical event on {iso_date}, found {len(idx)}")
    return int(idx[0])
