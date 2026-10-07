# Samoylov Phase 2 validation report

**Mode:** full run
**Output:** `samoylov_phase2_validation_results/`

## Configuration

- Spin-up: 1 PR + 150 EQ (baseline 1930–1950)
- Transient: 114 TR years (1901–2014)
- Forcing: gswp3_boike

## Gates

- Hard: 2/2 passed
- Soft: 0/3 passed

### Soft gate failures

- **century cumulative subsidence (paired)**: {"(0, 0)": 0.0, "(0, 1)": 0.0}
- **Center ALT deepening since 1901**: {"trend_m": NaN, "target_m": 0.1}
- **Center summer pond > Rim**: {"delta_m": -1.0986035628779538}

