# EML validation data (not in Git)

LTER/BNZ downloads and derived shapefile extracts are large and reproducible.
This directory stays empty in a code-only clone.

From the repository root (with `.venv-thermokarst` installed):

```sh
make thermokarst-eml-fetch-data
make thermokarst-eml-fetch-gps
make thermokarst-eml-fetch-wtd
make thermokarst-eml-climate
```

Phase harnesses also accept `--fetch` on `eml_validation.py`. Small observation
CSVs used for gates live under `../obs/`.
