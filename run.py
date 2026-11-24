"""Entry point: runs the pipeline end to end, filled in per milestone."""

from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import yaml

from chstorm.financial import cat_xl
from chstorm.impact import calibration_scale, event_losses, make_impf_set, sample_ylt
from chstorm.inputs import event_by_date, historical_mask, load_exposure, load_hazard
from chstorm.metrics import (
    aal,
    bootstrap_ci,
    ep_table,
    exceedance_curve,
    expected_shortfall_99,
    return_period_loss,
)

ROOT = Path(__file__).parent
CONFIG = ROOT / "config.yaml"
OUT = ROOT / "outputs"


def m1_inputs(cfg: dict):
    haz, exp = load_hazard(cfg), load_exposure(cfg)
    hist = historical_mask(haz)
    lothar = event_by_date(haz, "1999-12-26")
    gust = np.asarray(haz.intensity.max(axis=1).todense()).ravel()
    print(
        f"Hazard: {haz.size} events ({hist.sum()} historical), "
        f"{haz.frequency.sum():.2f} storms/yr, {haz.centroids.size} grid cells"
    )
    print(
        f"  peak gust per event, median / 99th pct / max: "
        f"{np.median(gust):.1f} / {np.percentile(gust, 99):.1f} / {gust.max():.1f} m/s"
    )
    print(
        f"  Lothar (1999-12-26): event {haz.event_name[lothar]}, peak gust {gust[lothar]:.1f} m/s"
    )
    print(f"Exposure: {len(exp.gdf)} points, total CHF {exp.gdf.value.sum() / 1e9:,.0f} bn")

    OUT.mkdir(exist_ok=True)
    g = exp.gdf
    fig, ax = plt.subplots(1, 2, figsize=(12, 4.5))
    sc = ax[0].scatter(g.geometry.x, g.geometry.y, c=np.log10(g.value), s=6, cmap="viridis")
    fig.colorbar(sc, ax=ax[0], label="log10 value (CHF)")
    ax[0].set_title(f"Exposure: LitPop scaled to CHF {g.value.sum() / 1e9:,.0f} bn")
    lon, lat = haz.centroids.lon, haz.centroids.lat
    w = haz.intensity[lothar].toarray().ravel()
    sc = ax[1].scatter(lon, lat, c=w, s=6, cmap="magma_r", vmin=15)
    fig.colorbar(sc, ax=ax[1], label="peak gust (m/s)")
    ax[1].set_title("Hazard: Lothar footprint, 26 Dec 1999")
    for a in ax:
        a.set_aspect(1 / np.cos(np.deg2rad(46.8)))
        a.set_xlabel("lon")
        a.set_ylabel("lat")
    fig.tight_layout()
    fig.savefig(OUT / "m1_exposure_lothar.png", dpi=120)
    return haz, exp


def lothar_target(cfg: dict) -> float:
    c = cfg["calibration"]
    return float(c["lothar_building_loss_1999_chf"]) * float(c["trend_factor_to_2024"])


def calibrated_losses(cfg: dict, haz, exp, curve: str) -> tuple[np.ndarray, float]:
    """Per-event losses with the curve scaled so Lothar matches its trended building loss."""
    lothar = event_by_date(haz, cfg["calibration"]["historical_storm_date"])
    raw = event_losses(haz, exp, make_impf_set(curve))
    scale = calibration_scale(raw[lothar], lothar_target(cfg))
    return event_losses(haz, exp, make_impf_set(curve, scale)), scale


def m2_losses(cfg: dict, haz, exp, curve: str | None = None):
    curve = curve or cfg["vulnerability"]["base"]
    n_years = int(cfg["hazard"]["n_sim_years"])
    lothar = event_by_date(haz, cfg["calibration"]["historical_storm_date"])
    loss, scale = calibrated_losses(cfg, haz, exp, curve)
    print(f"[{curve}] calibrated to Lothar: damage scale x{scale:.2f}")
    elt, ylt = sample_ylt(loss, np.asarray(haz.frequency), n_years)
    print(f"[{curve}] Lothar modelled loss today: CHF {loss[lothar] / 1e9:.2f} bn")
    permille = aal(ylt) / float(cfg["exposure"]["total_value_chf"]) * 1e3
    print(
        f"  events with loss>0: {(loss > 0).sum()} of {haz.size}; "
        f"AAL CHF {aal(ylt) / 1e6:,.0f} m ({permille:.3f} permille of value)"
    )
    print(f"  ES 99%: CHF {expected_shortfall_99(ylt) / 1e9:.2f} bn")
    print((ep_table(ylt)[["OEP", "AEP"]] / 1e9).round(2).to_string())
    return loss, elt, ylt


def plot_ep(ylt, path):
    fig, ax = plt.subplots(figsize=(6, 4))
    for col, lab in (("agg_loss", "AEP"), ("max_loss", "OEP")):
        x, f = exceedance_curve(ylt[col].to_numpy())
        ax.plot(1 / f, x / 1e9, label=lab)
    ax.set_xscale("log")
    ax.set_xlabel("return period (years)")
    ax.set_ylabel("loss (CHF bn)")
    ax.legend()
    ax.grid(alpha=0.3)
    fig.tight_layout()
    fig.savefig(path, dpi=120)


def m3_layer(cfg: dict, elt, n_years: int, verbose: bool = True) -> dict:
    lay = cfg["layer"]
    lim, att = float(lay["limit_chf"]), float(lay["attachment_chf"])
    _, s = cat_xl(
        elt["loss"].to_numpy(),
        elt["year"].to_numpy(),
        n_years,
        lim,
        att,
        int(lay["reinstatements"]),
        float(lay["reinstatement_rate"]),
    )
    if not verbose:
        return s
    print(f"Layer CHF {lim / 1e6:,.0f} m xs {att / 1e6:,.0f} m:")
    print(
        f"  expected loss CHF {s['expected_recovery'] / 1e6:.1f} m, pure premium "
        f"{s['pure_premium'] / 1e6:.1f} m, ROL {s['rate_on_line']:.2%}, "
        f"P(attach) {s['p_attach']:.2%} (1 in {1 / s['p_attach']:.0f} yrs), "
        f"P(exhaust) {s['p_exhaust']:.2%}"
    )
    return s


def m4_uncertainty(cfg: dict, haz, exp, ylt_base) -> pd.DataFrame:
    """Curve-shape spread (epistemic) next to Monte Carlo noise (bootstrap) on the 200-yr loss.

    Every curve is calibrated to Lothar and run on the SAME simulated years (same seed), so any
    difference comes from the curve shape alone: how loss is spread between moderate and
    extreme storms once the Lothar anchor is fixed.
    """
    v = cfg["vulnerability"]
    n_years = int(cfg["hazard"]["n_sim_years"])
    lothar = event_by_date(haz, cfg["calibration"]["historical_storm_date"])
    freq = np.asarray(haz.frequency)
    rows, eps, impfs = {}, {}, {}
    for curve in [v["base"], *v["shape_alternatives"]]:
        loss, scale = calibrated_losses(cfg, haz, exp, curve)
        elt, ylt = sample_ylt(loss, freq, n_years)
        oep = ylt["max_loss"].to_numpy()
        s = m3_layer(cfg, elt, n_years, verbose=False)
        rows[curve] = {
            "AAL_m": aal(ylt) / 1e6,
            "OEP100_bn": return_period_loss(oep, 100) / 1e9,
            "OEP200_bn": return_period_loss(oep, 200) / 1e9,
            "lothar_rp_yr": 1 / (oep >= loss[lothar] * (1 - 1e-9)).mean(),
            "layer_EL_m": s["expected_recovery"] / 1e6,
            "ROL_pct": s["rate_on_line"] * 100,
        }
        eps[curve], impfs[curve] = oep, make_impf_set(curve, scale).get_func()["WS"][1]
    tab = pd.DataFrame(rows).T
    print("M4 curve-shape sensitivity (all calibrated to Lothar, same simulated years):")
    print(tab.round(2).to_string())
    o200 = tab["OEP200_bn"]
    print(
        f"  200-yr OEP range: {o200.min():.2f}-{o200.max():.2f} bn ({o200.max() / o200.min():.2f}x)"
    )

    ci = bootstrap_ci(
        ylt_base["max_loss"].to_numpy(),
        200,
        np.random.default_rng(1),
        n_boot=int(v["bootstrap_resamples"]),
    )
    lo, hi = ci["loss_200"]
    print(f"  base 200-yr OEP 90% bootstrap CI (sampling noise): {lo / 1e9:.2f}-{hi / 1e9:.2f} bn")

    fig, ax = plt.subplots(1, 2, figsize=(12, 4.5))
    for curve, impf in impfs.items():
        ax[0].plot(impf.intensity, impf.mdd * impf.paa * 100, label=curve)
        x, f = exceedance_curve(eps[curve])
        ax[1].plot(1 / f, x / 1e9, label=curve)
    ax[0].set_xlim(20, 60)
    ax[0].set_ylim(0, 10)
    ax[0].set_xlabel("peak gust (m/s)")
    ax[0].set_ylabel("mean damage ratio (%)")
    ax[0].set_title("Calibrated curves (all reproduce Lothar)")
    ax[1].axhspan(lo / 1e9, hi / 1e9, xmin=0, xmax=1, color="grey", alpha=0.15)
    ax[1].axvline(200, color="grey", ls=":")
    ax[1].set_xscale("log")
    ax[1].set_xlim(2, n_years)
    ax[1].set_xlabel("return period (years)")
    ax[1].set_ylabel("OEP loss (CHF bn)")
    ax[1].set_title("OEP by curve shape; band = base 200-yr 90% CI")
    for a in ax:
        a.legend()
        a.grid(alpha=0.3)
    fig.tight_layout()
    fig.savefig(OUT / "m4_shape_uncertainty.png", dpi=120)
    return tab


def main() -> None:
    cfg = yaml.safe_load(CONFIG.read_text(encoding="utf-8"))
    n_years = int(cfg["hazard"]["n_sim_years"])
    haz, exp = m1_inputs(cfg)
    loss, elt, ylt = m2_losses(cfg, haz, exp)
    plot_ep(ylt, OUT / "m2_ep_curve.png")
    m3_layer(cfg, elt, n_years)
    m4_uncertainty(cfg, haz, exp, ylt)


if __name__ == "__main__":
    main()
