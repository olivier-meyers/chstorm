# chstorm: winter storm risk view for Swiss property

From hazard to a reinsurance layer, built on [CLIMADA](https://github.com/CLIMADA-project/climada_python).
Peril: extratropical windstorm (the largest European wind cat driver).

**Status: skeleton only.** No results yet; milestones below.

## Milestones
- [ ] M1 Hazard (StormEurope footprints) + exposure (LitPop, Switzerland)
- [ ] M2 Impact function -> event loss table -> AAL, OEP/AEP, 100/200/250-yr losses
- [ ] M3 Cat XL layer: expected layer loss, rate on line
- [ ] M4 Uncertainty: swap the vulnerability curve (Schwierz vs Welker); check against Lothar 1999
- [ ] M5 One-page summary for a non-technical underwriter

## Setup
```
conda create -n climada -c conda-forge --override-channels python=3.11 climada "libblas=*=*openblas" pytest ruff
conda activate climada
pip install -e . --no-deps
pytest
```
OpenBLAS is pinned because MKL crashed numpy on the author's machine.

## Layout
`src/chstorm/` package (`metrics.py`, `financial.py`, `losses.py` reused from the chquake earthquake model),
`config.yaml` (parameters with sources), `run.py`, `tests/`.

## Extension
Severe convective storm (hail) is the natural second peril but needs radar and claims data that are not openly available.
