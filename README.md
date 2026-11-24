# chstorm: a winter storm loss model for Swiss property

> Portfolio project, not a production model. One-page summary for underwriters: [docs/underwriter_summary.md](docs/underwriter_summary.md).

A small, reproducible extratropical windstorm catastrophe model for Swiss property, built on [CLIMADA](https://github.com/CLIMADA-project/climada_python):

**hazard → exposure → vulnerability → event loss table → EP metrics → cat XL layer**

The aim is a transparent "own view of risk" that runs from storm footprints to a reinsurance layer price, with the vulnerability assumption stress-tested and the model checked against a historical storm (Lothar, 1999). It is not a calibrated replica of a vendor model.

## Status

| Milestone | Content                                                          | Status  |
| --------- | ---------------------------------------------------------------- | ------- |
| M0        | Scaffold (packaging, lint, tests, config with sources)           | done    |
| M1        | Hazard (StormEurope footprints) + exposure (LitPop, Switzerland) | done    |
| M2        | Impact function (Schwierz, calibrated to Lothar) → ELT/YLT → AAL, OEP/AEP | done |
| M3        | Cat XL layer: expected layer loss, rate on line                  | done    |
| M4        | Uncertainty (vulnerability curve shape, sampling CI) + Lothar return period | done |
| M5        | Final README, assumptions review, one-page summary for underwriters | done |

## Quick start

```
# OpenBLAS instead of MKL: MKL crashed numpy's linear algebra on the dev machine (Windows)
conda create -n climada -c conda-forge --override-channels python=3.11 climada "libblas=*=*openblas" pytest ruff -y
conda activate climada
pip install -e . --no-deps
# Windows: GDAL needs GDAL_DATA, e.g. $env:GDAL_DATA="$env:CONDA_PREFIX\Library\share\gdal"
pytest
python run.py   # runs M1-M4 in order, prints the tables and writes the figures to outputs/
```

## Results

Inputs:

| Input           | Value                                                                               |
| --------------- | ----------------------------------------------------------------------------------- |
| Hazard          | StormEurope, Switzerland, v1.2: 4,260 events (142 historical), 1.95 events per year |
| Exposure        | LitPop Switzerland v3, rescaled to CHF 2,500 bn (VKG 2024)                          |
| Reference storm | Lothar, event 15100, 26 Dec 1999                                                    |

Losses (10,000 simulated years, Schwierz curve scaled x6.18 so Lothar = CHF 0.9 bn in today's values; the scaling target is illustrative):

| Metric                         | CHF        |
| ------------------------------ | ---------- |
| Average annual loss (AAL)      | 23 m       |
| 100 / 200 / 250-yr OEP loss    | 0.89 / 1.27 / 1.44 bn |
| Expected shortfall 99%         | 1.35 bn    |

Illustrative cat XL layer, CHF 1,000 m xs 250 m, one reinstatement at 100%: expected layer loss CHF 11.1 m, rate on line 1.10%, attaches about once in 58 years.

Without calibration the Schwierz curve gives Lothar only CHF 0.15 bn, roughly a sixth of the observed building loss. CLIMADA's Welker curve is a constant multiple (~1.78x) of Schwierz, so after calibration it gives the same answer; M4 therefore tests the curve's *shape* instead.

### Uncertainty (M4)

Three alternative curves, damage = ((gust − 25) / 35)^n with n = 2, 3, 5 (n = 3 is the cubic law of Klawa & Ulbrich 2003), each re-calibrated to Lothar and run on the same simulated years:

| Curve     | 200-yr OEP (CHF bn) |
| --------- | ------------------- |
| Schwierz  | 1.27                |
| n = 2     | 1.15                |
| n = 3     | 1.25                |
| n = 5     | 1.39                |

Across curves the AAL is CHF 20–23 m, the layer rate on line 1.08–1.14%, and Lothar's modelled return period 94–104 years, which is plausible for the benchmark storm of the past century. The shape spread (×1.20) is about the same size as the sampling noise: the 90% bootstrap interval on the base 200-yr loss is CHF 1.09–1.44 bn.

Why the shape matters so little: the OEP curve jumps from CHF 0.18 bn at 50 years to 0.89 bn at 100 years. The tail is the Lothar family (Lothar plus its 29 synthetic perturbations), so calibrating to Lothar pins the tail and every curve agrees there.

![Curve-shape sensitivity](outputs/m4_shape_uncertainty.png)

## Main assumptions and limitations

Ranked by how much they could move the 200-yr loss:

1. **Calibration target.** Lothar building loss CHF 600 m (sources range 500–600 m) × an illustrative trend factor of 1.5 to today's portfolio. The tail scales almost one-for-one with this number, so it matters more than the curve choice.
2. **Hazard catalogue.** 142 historical storms (1940–2013), each with 29 perturbations. The perturbations stay close to the parent storm, so the tail rests on very few independent events. No climate trend is applied.
3. **No clustering.** Storms arrive as independent Poisson events. European windstorms cluster (Lothar and Martin hit two days apart in 1999), so the AEP and the value of reinstatements are likely understated.
4. **Exposure.** LitPop's spatial pattern (economic activity, not building locations), rescaled to the CHF 2,500 bn insured by the cantonal building insurers and applied to all of Switzerland. Buildings only: no contents, no business interruption, no deductibles or policy limits.
5. **Footprint resolution.** 4.4 km gusts smooth local peaks; the calibration absorbs this on average but not location by location.

The layer (CHF 1,000 m xs 250 m) is illustrative and is not a real treaty.

## Layout

`src/chstorm/` package (`inputs.py`, `impact.py`, `metrics.py`, `financial.py`, `losses.py`; metrics and financial are reused from the chquake earthquake model), `config.yaml` (parameters with sources), `run.py`, `tests/`, `outputs/`.

## Extension

Severe convective storm (hail) is the natural second peril but needs radar and claims data that are not openly available.
