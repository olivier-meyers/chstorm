# chstorm: a winter storm loss model for Swiss property

> Work in progress. This is a portfolio project, not a production model.

A small, reproducible extratropical windstorm catastrophe model for Swiss property, built on [CLIMADA](https://github.com/CLIMADA-project/climada_python):

**hazard → exposure → vulnerability → event loss table → EP metrics → cat XL layer**

The aim is a transparent "own view of risk" that runs from storm footprints to a reinsurance layer price, with the vulnerability assumption stress-tested and the model checked against a historical storm (Lothar, 1999). It is not a calibrated replica of a vendor model.

## Status

| Milestone | Content | Status |
|---|---|---|
| M0 | Scaffold (packaging, lint, tests, config with sources) | done |
| M1 | Hazard (StormEurope footprints) + exposure (LitPop, Switzerland) | done |
| M2 | Impact function (Schwierz) → event loss table → AAL, OEP/AEP | planned |
| M3 | Cat XL layer: expected layer loss, rate on line | planned |
| M4 | Uncertainty (Schwierz vs Welker curve) + Lothar 1999 check | planned |
| M5 | Final README, figures, one-page summary for underwriters | planned |

## Quick start

```
# OpenBLAS instead of MKL: MKL crashed numpy's linear algebra on the dev machine (Windows)
conda create -n climada -c conda-forge --override-channels python=3.11 climada "libblas=*=*openblas" pytest ruff -y
conda activate climada
pip install -e . --no-deps
# Windows: GDAL needs GDAL_DATA, e.g. $env:GDAL_DATA="$env:CONDA_PREFIX\Library\share\gdal"
pytest
python run.py m1_inputs
```

## Results so far

M1 only: hazard and exposure inputs, no losses yet.

| Input | Value |
|---|---|
| Hazard | StormEurope, Switzerland, v1.2: 4,260 events (142 historical), 1.95 events per year |
| Exposure | LitPop Switzerland v3, rescaled to CHF 2,500 bn (VKG 2024) |
| Reference storm | Lothar, event 15100, 26 Dec 1999 |

Loss metrics (AAL, 100/200/250-yr) will appear here after M2.

## Layout

`src/chstorm/` package (`inputs.py`, `metrics.py`, `financial.py`, `losses.py`; metrics and financial are reused from the chquake earthquake model), `config.yaml` (parameters with sources), `run.py`, `tests/`, `outputs/`.

## Extension

Severe convective storm (hail) is the natural second peril but needs radar and claims data that are not openly available.
