# Required data layout

Processed telemetry is not included in this repository. Use only data that you are authorized to redistribute or process.

Create the following layout:

```text
data/
├── flight_metadata.csv
├── flights/
│   ├── <28 train flight files>.csv
│   └── <6 outer-validation flight files>.csv
├── fractions/
│   ├── train_100pct.csv
│   ├── train_050pct.csv
│   ├── train_025pct.csv
│   ├── train_010pct.csv
│   └── train_005pct.csv
└── test_flights/
    └── <6 frozen held-out test flight files>.csv
```

The training loader expects exactly 34 per-flight CSV files in `data/flights/`: 28 with `partition=train` and 6 with `partition=validation`. Every flight contains 121 rows on the integer T+0 through T+120 second grid.

## Per-flight CSV schema

Required header:

```text
flight_id,mission,partition,block,orbit,payload_kg,source_stage,time_s,time_normalized,altitude_m,speed_m_s
```

- `time_s`: `0` through `120` seconds.
- `time_normalized`: `time_s / 120`.
- `partition`: `train`, `validation`, or—only inside `test_flights/`—`test`.
- `block`: one of `1`, `2`, `3`, `4`, or `5`.
- `payload_kg`: numeric or empty when unavailable.
- `altitude_m`, `speed_m_s`: targets in SI units.

The training loader deliberately rejects the six held-out flight identifiers if they appear in `data/flights/`.

## Observation-mask schema

Each `data/fractions/train_*pct.csv` file must contain at least:

```text
flight_id,time_s
```

The masks must be nested (`5% ⊆ 10% ⊆ 25% ⊆ 50% ⊆ 100%`) and correspond to training flights only. Expected row counts are 3,388; 1,680; 840; 336; and 168 for the 100%, 50%, 25%, 10%, and 5% files, respectively.

## Held-out test files

`evaluate_test.py` accepts exactly these six filenames:

```text
intelsat_35e.csv
iridium_next_5.csv
ses_9.csv
spacex_crs_11.csv
sso_a.csv
thaicom_8.csv
```

Do not place these files in `data/flights/`. Run the test evaluation only after the full validation outputs have been frozen and verified.
