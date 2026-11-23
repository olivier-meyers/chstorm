"""Entry point: runs the pipeline end to end, filled in per milestone."""

from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import yaml

from chstorm.inputs import event_by_date, historical_mask, load_exposure, load_hazard

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


def main() -> None:
    cfg = yaml.safe_load(CONFIG.read_text(encoding="utf-8"))
    m1_inputs(cfg)


if __name__ == "__main__":
    main()
