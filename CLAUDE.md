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
- [x] M2 impact/ELT/YLT: src/chstorm/impact.py (ImpfStormEurope.from_schwierz = paa x mdd, 12-pt curve; ImpactCalc;
      Poisson YLT, 10,000 yrs, seeded), run.py m2_losses + outputs/m2_ep_curve.png, tests/test_impact.py (14 tests pass in total, ruff clean).
      RESULT (uncalibrated Schwierz): AAL CHF 4 m, Lothar CHF 0.15 bn, 200-yr OEP/AEP 0.21 bn, ES99 0.22 bn.
      FLAG: far too low. Lothar insured loss in CH was ~CHF 1.3 bn (1999; verify source). Cause: curve gives ~0.3% damage at 45 m/s
      and 4.4 km gusts are smoothed. Decide in M4: calibrate a scale factor to Lothar, and/or use Welker (mdd 1.4% at 43 m/s).
- [x] Calibration: impact.calibration_scale + make_impf_set(scale) (mdd x scale, capped at 1). Target = Lothar CH building
      loss CHF 600 m (1999; Blick/PLANAT, PLANAT says 500 m) x trend 1.5 (ILLUSTRATIVE, verify vs VKG insured-value series)
      = CHF 0.9 bn. Schwierz scale x6.18. RESULT: AAL CHF 23 m, OEP 100/200/250-yr 0.89/1.27/1.44 bn, ES99 1.35 bn.
      (Europe-wide Lothar EUR 5 bn / USD 11.7 bn is NOT the CH target; CH total 1.78 bn was mostly forest.)
      FINDING: CLIMADA's Welker curve is ~1.78 x Schwierz (constant ratio per event), so after calibration it gives
      identical results -> a Welker swap tests nothing. M4 needs a SHAPE alternative instead.
- [x] M3: run.py m3_layer, config layer = CHF 1,000 m xs 250 m, 1 reinst @100% (illustrative). Expected loss CHF 11.1 m,
      pure premium 11.0 m, ROL 1.10%, attaches 1 in 58 yrs. Not committed (M1-M3 all uncommitted).
- [ ] NEXT: Olivier commits. Then M4: shape uncertainty = damage ∝ (gust - threshold)^n, n in {2,3,5} (cubic = Klawa &
      Ulbrich 2003), each calibrated to Lothar -> show spread of 200-yr loss and layer ROL; plus convergence/bootstrap CI
      on 200-yr (metrics.bootstrap_ci). Also check modelled Lothar return period (~100 yr) for plausibility.
- [ ] M5 README + underwriter one-pager
