# Samoylov observation references (Phase 1)

These CSV files are **paper-derived reference targets** from Bender et al.
(2026), Fig. 2 and §3.1–3.2, not raw Boike station downloads.

Replace with primary observations from the Samoylov flux tower / soil probe
archive when available. Until then, the harness uses these curves for
qualitative model–reference comparison gates.

| File | Content | Source |
|---|---|---|
| `samoylov_soilT_rim_10cm.csv` | Monthly mean soil T (°C) at 0.10 m, Rim | Paper Fig. 2b (approx.) |
| `samoylov_soilT_center_10cm.csv` | Monthly mean at 0.10 m, Center | Paper Fig. 2b (approx.) |
| `samoylov_soilT_rim_65cm.csv` | Monthly mean at 0.65 m, Rim | Paper Fig. 2c (approx.) |
| `samoylov_soilT_center_65cm.csv` | Monthly mean at 0.65 m, Center | Paper Fig. 2c (approx.) |
| `samoylov_snow_depth.csv` | Monthly mean snow depth (m), Rim and Center | Paper §3.1 ranges |
| `samoylov_alt_sept.csv` | September max ALT (m), Rim and Center | Paper §3.2 (0.47 / 0.49 m) |
| `boike_samoylov_monthly_2002-2014.csv` | Monthly T and precip for bias correction | Aggregated from PANGAEA.806203 (2002–2011) |
| `boike_samoylov_daily_2002-2011.csv` | Daily T/precip for DOY anomaly calibration | Aggregated from PANGAEA.806203 |
| `boike_samoylov_monthly_2002-2014.csv.provenance.json` | Processing metadata | `process_boike_data.py` output |

Primary source is now [PANGAEA.905230](https://doi.org/10.1594/PANGAEA.905230)
(`met_lv1_V201908.zip`, 2002–2018 level-1). Calibration window **2002–2014**.
Regenerate:

```sh
make thermokarst-samoylov-fetch-data
```
