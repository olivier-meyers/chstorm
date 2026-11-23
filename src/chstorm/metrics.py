"""Risk metrics from a year loss table (YLT): AAL, OEP/AEP, return-period losses, TVaR, ES.

Conventions (empirical, no curve fitting):
- With N simulated years, the k-th largest annual value has exceedance frequency k/N, so the
  T-year return-period loss is the (N/T)-th largest value. N/T must be a whole number >= 1
  (10,000 years -> the 1000-year loss is the 10th largest; it rests on 10 years of data).
- AEP uses the annual aggregate loss, OEP the annual maximum event loss. Since a year's
  largest event can never exceed the year's total, OEP <= AEP at every return period.
- TVaR_T = mean of the N/T largest values, i.e. the expected loss given the T-year loss is
  reached. ES 99 % (Swiss Solvency Test convention) = TVaR at T = 100 on the AEP.
- AAL = total loss / N = mean of the YLT aggregate column (zero-loss years included).
"""

import numpy as np
import pandas as pd

RETURN_PERIODS = (50, 100, 200, 250, 500, 1000)


def aal(ylt: pd.DataFrame) -> float:
    """Average annual loss: mean annual aggregate over all simulated years."""
    return float(ylt["agg_loss"].mean())


def _rank(n_years: int, rp: float) -> int:
    k = n_years / rp
    if k < 1 or not np.isclose(k, round(k)):
        raise ValueError(f"{n_years} years cannot resolve the {rp}-year loss empirically")
    return int(round(k))


def return_period_loss(annual: np.ndarray, rp: float) -> float:
    """Loss exceeded (or equalled) with annual frequency 1/rp: the (N/rp)-th largest value."""
    annual = np.sort(np.asarray(annual, float))[::-1]
    return float(annual[_rank(len(annual), rp) - 1])


def tvar(annual: np.ndarray, rp: float) -> float:
    """Tail value at risk: mean of the N/rp largest annual values."""
    annual = np.sort(np.asarray(annual, float))[::-1]
    return float(annual[: _rank(len(annual), rp)].mean())


def expected_shortfall_99(ylt: pd.DataFrame) -> float:
    """99 % expected shortfall of the annual aggregate loss (= AEP TVaR at 100 years)."""
    return tvar(ylt["agg_loss"].to_numpy(), 100)


def exceedance_curve(annual: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    """Empirical EP curve: losses sorted high -> low and their exceedance frequency k/N."""
    losses = np.sort(np.asarray(annual, float))[::-1]
    return losses, np.arange(1, len(losses) + 1) / len(losses)


def ep_table(ylt: pd.DataFrame, return_periods: tuple = RETURN_PERIODS) -> pd.DataFrame:
    """OEP and AEP return-period losses with their TVaRs, one row per return period."""
    oep, aep = ylt["max_loss"].to_numpy(), ylt["agg_loss"].to_numpy()
    rows = {
        rp: {
            "OEP": return_period_loss(oep, rp),
            "AEP": return_period_loss(aep, rp),
            "TVaR_OEP": tvar(oep, rp),
            "TVaR_AEP": tvar(aep, rp),
        }
        for rp in return_periods
    }
    return pd.DataFrame.from_dict(rows, orient="index").rename_axis("return_period")


def convergence(annual: np.ndarray, rp: float, n_points: int = 20) -> pd.DataFrame:
    """Running AAL and rp-year loss using only the first n simulated years, for growing n.

    If the estimates are still drifting at n = N, the catalogue is too short for that metric.
    """
    annual = np.asarray(annual, float)
    ns = np.unique(np.linspace(rp, len(annual), n_points).astype(int) // rp * rp)
    return pd.DataFrame(
        {
            "n_years": ns,
            "aal": [annual[:n].mean() for n in ns],
            f"loss_{int(rp)}": [return_period_loss(annual[:n], rp) for n in ns],
        }
    )


def bootstrap_ci(
    annual: np.ndarray,
    rp: float,
    rng: np.random.Generator,
    n_boot: int = 1000,
    level: float = 0.90,
) -> dict[str, tuple[float, float]]:
    """Sampling-uncertainty interval for AAL and the rp-year loss, resampling whole years.

    Simulated years are independent (Poisson occurrence), so resampling years with
    replacement is valid. This measures only Monte Carlo noise from a finite catalogue,
    not model (epistemic) uncertainty.
    """
    annual = np.asarray(annual, float)
    n, k = len(annual), _rank(len(annual), rp)
    idx = rng.integers(0, n, size=(n_boot, n))
    samples = annual[idx]
    aals = samples.mean(axis=1)
    rpl = -np.partition(-samples, k - 1, axis=1)[:, k - 1]  # k-th largest per resample
    q = [(1 - level) / 2, (1 + level) / 2]
    return {
        "aal": tuple(np.quantile(aals, q)),
        f"loss_{int(rp)}": tuple(np.quantile(rpl, q)),
    }
