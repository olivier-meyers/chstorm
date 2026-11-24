"""Entry point: runs the pipeline end to end, filled in per milestone."""

from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import yaml

from chstorm.impact import event_losses, make_impf_set, sample_ylt
from chstorm.inputs import event_by_date, historical_mask, load_exposure, load_hazard
from chstorm.metrics import aal, ep_table, exceedance_curve, expected_shortfall_99

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


def m2_losses(cfg: dict, haz, exp, curve: str | None = None):
    curve = curve or cfg["vulnerability"]["base"]
    n_years = int(cfg["hazard"]["n_sim_years"])
    loss = event_losses(haz, exp, make_impf_set(curve))
    elt, ylt = sample_ylt(loss, np.asarray(haz.frequency), n_years)
    lothar = event_by_date(haz, "1999-12-26")
    print(f"[{curve}] Lothar modelled loss today: CHF {loss[lothar] / 1e9:.2f} bn")
    permille = aal(ylt) / float(cfg["exposure"]["total_value_chf"]) * 1e3
    print(f"  events with loss>0: {(loss > 0).sum()} of {haz.size}; "
          f"AAL CHF {aal(ylt) / 1e6:,.0f} m ({permille:.3f} permille of value)")
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


def main() -> None:
    cfg = yaml.safe_load(CONFIG.read_text(encoding="utf-8"))
    haz, exp = m1_inputs(cfg)
    loss, elt, ylt = m2_losses(cfg, haz, exp)
    plot_ep(ylt, OUT / "m2_ep_curve.png")


if __name__ == "__main__":
    main()
