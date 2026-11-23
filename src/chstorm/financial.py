"""Cat XL layer with reinstatements (copied from chquake.financial).

Cat XL "X xs Y" per occurrence, with n reinstatements at rate r (pro rata capita):
    recovery per event   R_e = min(max(G_e - Y, 0), X)
    annual recovery          = min(sum_e R_e, (n + 1) X)
    reinstatement premium    = r * P * min(sum_e R_e, n X) / X
Neither depends on the order of events within a year, which the event set does not have.
Pure premium P (no loading): E[recovery] = P + E[reinstatement premium], so
    P = E[recovery] / (1 + r * E[min(sum_e R_e, n X)] / X).
"""

import numpy as np
import pandas as pd


def layer_recoveries(event_loss: np.ndarray, limit: float, attachment: float) -> np.ndarray:
    """Per-occurrence recovery of an X xs Y layer: min(max(G - Y, 0), X)."""
    return np.clip(np.asarray(event_loss, float) - attachment, 0.0, limit)


def cat_xl(
    event_loss: np.ndarray,
    year: np.ndarray,
    n_years: int,
    limit: float,
    attachment: float,
    reinstatements: int,
    reinstatement_rate: float,
) -> tuple[pd.DataFrame, dict[str, float]]:
    """Apply an X xs Y cat XL with reinstatements; return per-year table and summary.

    Year table: recovery (after the annual aggregate limit) and reinstated (fraction of the
    limit reinstated, which drives the reinstatement premium). Summary: expected recovery,
    pure premium, rate on line, attachment and exhaustion probabilities, std of recovery.
    """
    limit, attachment = float(limit), float(attachment)
    r_e = layer_recoveries(event_loss, limit, attachment)
    total = np.bincount(np.asarray(year), weights=r_e, minlength=n_years)
    if len(total) > n_years:
        raise ValueError("event years outside 0..n_years-1")
    recovery = np.minimum(total, (reinstatements + 1) * limit)
    reinstated = np.minimum(total, reinstatements * limit) / limit
    ylt = pd.DataFrame(
        {"recovery": recovery, "reinstated": reinstated},
        index=pd.RangeIndex(n_years, name="year"),
    )
    expected = recovery.mean()
    premium = expected / (1.0 + reinstatement_rate * reinstated.mean())
    summary = {
        "expected_recovery": float(expected),
        "pure_premium": float(premium),
        "rate_on_line": float(premium / limit),
        "p_attach": float((total > 0).mean()),
        "p_exhaust": float((recovery >= (reinstatements + 1) * limit).mean()),
        "std_recovery": float(recovery.std()),
    }
    return ylt, summary
