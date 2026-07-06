# Malaysia Weather Forecast-Accuracy Pipeline

A modern-data-stack ELT pipeline over Malaysian open government data
([data.gov.my Weather API](https://developer.data.gov.my/realtime-api/weather)).
The API only exposes the *current* forecast, so this pipeline snapshots it daily
(stamping each row with `ingested_at`) and accumulates the historical record needed
to measure **forecast accuracy over time** — data that would not otherwise exist.

## Architecture

```
data.gov.my Weather API
   --(Python: extract + load)-->  BigQuery  weather_raw.forecast
   --(dbt: staging / intermediate / marts + tests)-->  weather_staging.*
   --(PySpark aggregation, in CI)-->  weather_staging.spark_location_stats
   --(Looker Studio)-->  dashboard
   Orchestration: GitHub Actions (daily 09:00 MYT)
```

- **Extract / Load** — `weather_pipeline/` (Python): fetch the 7-day forecast, flatten each
  record, append to BigQuery with a snapshot timestamp (`ingested_at`).
- **Transform** — `dbt/weather/`:
  - `stg_weather_forecast` — cleans + de-duplicates to the latest snapshot per location/date.
  - `mart_weather_daily` — English condition categories (via a reusable macro) + `temp_range`.
  - `int_forecast_snapshots` — adds issue date + lead time per forecast.
  - `mart_forecast_accuracy` — forecast-vs-actual temp error and condition match by lead time.
  - 16 data-quality tests (`not_null`, `accepted_values`).
- **Spark** — `spark_jobs/forecast_stats.py`: per-location statistics via the Spark
  DataFrame API + a window function; runs on the CI runner, writes back to BigQuery.
- **Orchestration** — `.github/workflows/daily.yml`: daily run (tests → load → dbt → Spark).
- **Serve** — Looker Studio on the marts.

## Tech stack
Python 3.13, `requests`, `google-cloud-bigquery`, `dbt-bigquery`, Looker Studio.
BigQuery region `asia-southeast1`. Everything runs on always-free tiers.

## Run it locally
```bash
# 1. Environment
python -m venv .venv
source .venv/Scripts/activate        # PowerShell: .venv\Scripts\Activate.ps1
pip install -r requirements.txt

# 2. Authenticate to Google Cloud (one-time)
gcloud auth application-default login

# 3. Configure
cp .env.example .env                 # then set GCP_PROJECT to your project id

# 4. Create the raw dataset, then run the pipeline
python -c "from google.cloud import bigquery; c=bigquery.Client(); d=bigquery.Dataset(f'{c.project}.weather_raw'); d.location='asia-southeast1'; c.create_dataset(d, exists_ok=True)"
python -m weather_pipeline.main

# 5. Build + test the dbt model
cd dbt/weather
export GCP_PROJECT=<your-project-id>
dbt run  --profiles-dir .
dbt test --profiles-dir .
```

## Tests
```bash
python -m pytest -v      # extract + transform unit tests
```

## Verified run
- 2,520 forecast rows loaded (284 locations, 7-day window).
- dbt staging view built; 3/3 `not_null` tests passing.

## Dashboard
<!-- DASHBOARD_LINK -->
_Deferred: the Looker Studio dashboard will be built once the dataset is enriched
(English condition categories) and has accumulated several daily snapshots for the
forecast-accuracy view._

## Roadmap
- **Phase 1 — done:** ELT to BigQuery, staging model, tests, GitHub Actions daily schedule.
- **Phase 2 — done:** English-condition enrichment, forecast-accuracy marts, PySpark aggregation.
- **Phase 3:** polished Looker Studio dashboard (once accuracy data accumulates), demo GIF;
  optional Airflow orchestration for the résumé keyword.
- **Phase 4 (stretch):** near-real-time transit reliability from data.gov.my GTFS-Realtime.
