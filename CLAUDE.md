# CLIMADA winter-storm project: working notes

## Goal
A small GitHub portfolio project for the Swiss Re "Nat Cat Analyst - Graduate" role (EMEA Cat Perils & Methods,
Zurich; application deadline 21 Dec 2026). The role's main perils are extratropical windstorm and severe convective storm.
The audience is GitHub viewers who work in nat cat / re-insurance, so the project has to read as a risk view, not a tutorial.
Time budget: 2–3 evenings.

## Working rules (from Olivier)
- Be very token-efficient: one prompt per session, short answers, no long surveys.
- Keep Olivier on board: explain each modelling choice briefly (what it is and why an underwriter cares) so he learns it.
- At the end of each session, update the "Status / next step" section below, because he runs /clear after every step.

## Scope (agreed)
"Winter storm risk view for Swiss property: from hazard to a reinsurance layer"
1. CLIMADA: StormEurope footprints + LitPop exposure (CH) + storm impact function -> event loss table
2. AAL, OEP/AEP, 100/200/250-yr losses
3. Cat XL layer: expected layer loss, rate on line
4. Uncertainty: swap the vulnerability curve (e.g. Schwierz vs Welker) and see how the 200-yr loss moves;
   check against a historical storm (Lothar 1999)
5. A one-page summary for a non-technical underwriter

## Model per step
- Sonnet 5.5, low effort: environment, skeleton, copying code, README polish
- Opus 5.5, medium effort: modelling steps M1–M4 (after the weekly limit resets Wednesday night) and a final assumptions review

## Reuse from ../nat_cat_model (chquake, Swiss earthquake model)
- Copy the structure: src/ package, config.yaml with a cited source for every parameter, run.py, tests/, ruff, pytest
- Copy almost verbatim: src/chquake/metrics.py (AAL, EP table, TVaR, bootstrap) and financial.py (cat_xl with reinstatements)
- Its env recipe used conda-forge python 3.11 with OpenBLAS (MKL crashed numpy on this machine)
- Possible extra: a combined EQ + windstorm view of Swiss property

## Environment
- `python` and `conda` are not on PATH. Conda is at `C:\Users\Admin\miniforge3` (use `Scripts\conda.exe`, env path `envs\climada`).

## Status / next step
- [x] Idea + scope agreed, chquake reviewed
- [x] Peril decision: extratropical winter storm (StormEurope; Schwierz/Welker curves). Hail/SCS = README extension only
      (needs MeteoSwiss radar + GVZ claims, not open).
- [x] Conda located; skeleton built (pyproject, config.yaml with TODO(Mx) placeholders, src/chstorm/{metrics,financial,losses}.py,
      tests, README, .gitignore, git init). No commit yet.
- [x] `climada` env built; 10 tests pass, ruff clean; first local commit 7b09d96 (not pushed; push after M1/M2).
- [x] M1 hazard + exposure: src/chstorm/inputs.py, run.py m1_inputs, tests/test_inputs.py (12 tests pass, ruff clean),
      outputs/m1_exposure_lothar.png. StormEurope CHE v1.2 (4260 events, 142 hist, 1.95/yr; Lothar = event 15100,
      date 1999-12-26), LitPop CHE v3 rescaled to CHF 2,500 bn (VKG 2024). Not committed yet.
      Set GDAL_DATA=<env>/Library/share/gdal to silence GDAL warnings. YAML: write floats as 2.5e+12 or cast.
- [ ] NEXT: Olivier commits M1, then M2 impact/ELT/EP (Opus 5.5, medium): ImpfStormEurope.from_schwierz, ImpactCalc,
      Poisson YLT from event freq, AAL/OEP/AEP via metrics.py.
- [ ] M3 cat XL; M4 uncertainty (Welker curve) + Lothar check vs insured loss; M5 README + underwriter one-pager
