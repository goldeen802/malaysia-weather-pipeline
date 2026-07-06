# Weather Pipeline — Phase 1 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a thin end-to-end slice of the Malaysia weather ELT pipeline: pull the daily forecast from the data.gov.my Weather API, snapshot it into a BigQuery raw table, clean it with one dbt staging model, and visualize it in one Looker Studio chart.

**Architecture:** Python does Extract + Load (E-L); dbt does Transform (T) in-warehouse. Each forecast pull is stamped with an `ingested_at` timestamp so daily snapshots accumulate the history the API itself does not retain. Pure functions (`extract`, `transform`) are unit-tested; the BigQuery load and dbt run are verified with real smoke runs.

**Tech Stack:** Python 3.11+, `requests`, `google-cloud-bigquery`, `python-dotenv`, `pytest`, `responses`, `dbt-bigquery`, Looker Studio.

**Prerequisites (already in place):** Google Cloud project with BigQuery enabled, `gcloud` CLI authenticated, Python + Docker installed, GitHub account. Before starting, run once: `gcloud auth application-default login` (gives Python and dbt credentials via Application Default Credentials).

---

## File Structure

```
my-weather-pipeline/
  .env.example                         # documents required env vars
  requirements.txt                     # Python deps
  weather_pipeline/
    __init__.py
    config.py                          # reads env vars (project, dataset)
    extract.py                         # fetch forecast from the API
    transform.py                       # flatten API record -> BigQuery row
    load.py                            # BigQuery client + load rows
    main.py                            # orchestrates extract -> transform -> load
  tests/
    __init__.py
    test_extract.py
    test_transform.py
  dbt/
    weather/
      dbt_project.yml
      models/
        staging/
          stg_weather_forecast.sql
          schema.yml
  docs/
    specs/2026-07-06-malaysia-weather-elt-pipeline-design.md   (exists)
    plans/2026-07-06-weather-pipeline-phase1.md                (this file)
```

**Responsibilities:** `extract.py` only talks to the API. `transform.py` is pure (record -> row), no I/O. `load.py` only talks to BigQuery. `main.py` wires them together. This keeps the two pure units unit-testable without network or cloud access.

---

## Task 1: Project scaffolding & dependencies

**Files:**
- Create: `requirements.txt`
- Create: `.env.example`
- Create: `weather_pipeline/__init__.py` (empty)
- Create: `tests/__init__.py` (empty)

- [ ] **Step 1: Create `requirements.txt`**

```
requests==2.32.3
google-cloud-bigquery==3.25.0
python-dotenv==1.0.1
pytest==8.3.3
responses==0.25.3
dbt-bigquery==1.8.2
```

- [ ] **Step 2: Create `.env.example`**

```
# Copy to .env and fill in. .env is gitignored.
GCP_PROJECT=your-gcp-project-id
BQ_DATASET=weather_raw
```

- [ ] **Step 3: Create empty package files**

Create `weather_pipeline/__init__.py` and `tests/__init__.py` as empty files.

- [ ] **Step 4: Create a virtualenv and install deps**

Run (from repo root):
```bash
python -m venv .venv
source .venv/Scripts/activate   # Windows Git Bash; on PowerShell: .venv\Scripts\Activate.ps1
pip install -r requirements.txt
```
Expected: all packages install without error.

- [ ] **Step 5: Commit**

```bash
git add requirements.txt .env.example weather_pipeline/__init__.py tests/__init__.py
git commit -m "chore: project scaffolding and dependencies"
```

---

## Task 2: Extract — fetch the forecast

**Files:**
- Create: `weather_pipeline/extract.py`
- Test: `tests/test_extract.py`

- [ ] **Step 1: Write the failing test**

`tests/test_extract.py`:
```python
import responses
from weather_pipeline.extract import fetch_forecast, API_URL

SAMPLE = [
    {
        "location": {"location_id": "Ds001", "location_name": "Langkawi"},
        "date": "2026-07-06",
        "morning_forecast": "Hujan di satu dua tempat",
        "afternoon_forecast": "Ribut petir di satu dua tempat",
        "night_forecast": "Tiada hujan",
        "summary_forecast": "Ribut petir di satu dua tempat",
        "summary_when": "Petang",
        "min_temp": 26,
        "max_temp": 32,
    }
]


@responses.activate
def test_fetch_forecast_returns_records():
    responses.add(responses.GET, API_URL, json=SAMPLE, status=200)
    result = fetch_forecast()
    assert len(result) == 1
    assert result[0]["location"]["location_name"] == "Langkawi"


@responses.activate
def test_fetch_forecast_passes_limit_param():
    responses.add(responses.GET, API_URL, json=SAMPLE, status=200)
    fetch_forecast(limit=3)
    assert "limit=3" in responses.calls[0].request.url
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest tests/test_extract.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'weather_pipeline.extract'`.

- [ ] **Step 3: Write minimal implementation**

`weather_pipeline/extract.py`:
```python
import requests

API_URL = "https://api.data.gov.my/weather/forecast"


def fetch_forecast(limit: int | None = None, timeout: int = 30) -> list[dict]:
    """Fetch the 7-day general forecast from the data.gov.my Weather API."""
    params = {}
    if limit is not None:
        params["limit"] = limit
    response = requests.get(API_URL, params=params, timeout=timeout)
    response.raise_for_status()
    return response.json()
```

- [ ] **Step 4: Run test to verify it passes**

Run: `python -m pytest tests/test_extract.py -v`
Expected: PASS (2 passed).

- [ ] **Step 5: Commit**

```bash
git add weather_pipeline/extract.py tests/test_extract.py
git commit -m "feat: fetch forecast from data.gov.my Weather API"
```

---

## Task 3: Transform — flatten a record into a BigQuery row

**Files:**
- Create: `weather_pipeline/transform.py`
- Test: `tests/test_transform.py`

- [ ] **Step 1: Write the failing test**

`tests/test_transform.py`:
```python
from weather_pipeline.transform import to_row

RECORD = {
    "location": {"location_id": "Ds001", "location_name": "Langkawi"},
    "date": "2026-07-06",
    "morning_forecast": "Hujan di satu dua tempat",
    "afternoon_forecast": "Ribut petir di satu dua tempat",
    "night_forecast": "Tiada hujan",
    "summary_forecast": "Ribut petir di satu dua tempat",
    "summary_when": "Petang",
    "min_temp": 26,
    "max_temp": 32,
}

INGESTED_AT = "2026-07-06T00:00:00+00:00"


def test_to_row_flattens_location():
    row = to_row(RECORD, INGESTED_AT)
    assert row["location_id"] == "Ds001"
    assert row["location_name"] == "Langkawi"


def test_to_row_maps_date_and_temps():
    row = to_row(RECORD, INGESTED_AT)
    assert row["forecast_date"] == "2026-07-06"
    assert row["min_temp"] == 26
    assert row["max_temp"] == 32


def test_to_row_stamps_ingested_at():
    row = to_row(RECORD, INGESTED_AT)
    assert row["ingested_at"] == INGESTED_AT
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest tests/test_transform.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'weather_pipeline.transform'`.

- [ ] **Step 3: Write minimal implementation**

`weather_pipeline/transform.py`:
```python
def to_row(record: dict, ingested_at: str) -> dict:
    """Flatten one Weather API record into a flat BigQuery row.

    ``ingested_at`` is the snapshot timestamp (ISO 8601). It is what turns a
    stateless API into an accumulating historical record.
    """
    location = record["location"]
    return {
        "location_id": location["location_id"],
        "location_name": location["location_name"],
        "forecast_date": record["date"],
        "morning_forecast": record["morning_forecast"],
        "afternoon_forecast": record["afternoon_forecast"],
        "night_forecast": record["night_forecast"],
        "summary_forecast": record["summary_forecast"],
        "summary_when": record["summary_when"],
        "min_temp": record["min_temp"],
        "max_temp": record["max_temp"],
        "ingested_at": ingested_at,
    }
```

- [ ] **Step 4: Run test to verify it passes**

Run: `python -m pytest tests/test_transform.py -v`
Expected: PASS (3 passed).

- [ ] **Step 5: Commit**

```bash
git add weather_pipeline/transform.py tests/test_transform.py
git commit -m "feat: flatten API record into BigQuery row"
```

---

## Task 4: Config — read environment variables

**Files:**
- Create: `weather_pipeline/config.py`

No unit test: this is a thin wrapper over `os.environ`. It is exercised by the smoke run in Task 6.

- [ ] **Step 1: Write the implementation**

`weather_pipeline/config.py`:
```python
import os

from dotenv import load_dotenv

load_dotenv()


def get_project() -> str:
    """GCP project id. Raises KeyError if GCP_PROJECT is unset."""
    return os.environ["GCP_PROJECT"]


def get_dataset() -> str:
    return os.getenv("BQ_DATASET", "weather_raw")


def get_forecast_table() -> str:
    """Fully-qualified BigQuery table id: project.dataset.forecast."""
    return f"{get_project()}.{get_dataset()}.forecast"
```

- [ ] **Step 2: Verify it imports**

Run: `python -c "import weather_pipeline.config"`
Expected: no output, exit code 0.

- [ ] **Step 3: Commit**

```bash
git add weather_pipeline/config.py
git commit -m "feat: env-based config for project and dataset"
```

---

## Task 5: Load — write rows to BigQuery

**Files:**
- Create: `weather_pipeline/load.py`

No unit test (BigQuery has no lightweight local mock worth the complexity here). The explicit BigQuery `SchemaField` list *is* the contract; it is verified by the real load in Task 6.

- [ ] **Step 1: Write the implementation**

`weather_pipeline/load.py`:
```python
from google.cloud import bigquery

FORECAST_SCHEMA = [
    bigquery.SchemaField("location_id", "STRING"),
    bigquery.SchemaField("location_name", "STRING"),
    bigquery.SchemaField("forecast_date", "DATE"),
    bigquery.SchemaField("morning_forecast", "STRING"),
    bigquery.SchemaField("afternoon_forecast", "STRING"),
    bigquery.SchemaField("night_forecast", "STRING"),
    bigquery.SchemaField("summary_forecast", "STRING"),
    bigquery.SchemaField("summary_when", "STRING"),
    bigquery.SchemaField("min_temp", "INTEGER"),
    bigquery.SchemaField("max_temp", "INTEGER"),
    bigquery.SchemaField("ingested_at", "TIMESTAMP"),
]


def get_client(project: str) -> bigquery.Client:
    return bigquery.Client(project=project)


def load_rows(client: bigquery.Client, table_id: str, rows: list[dict]) -> int:
    """Append rows to the raw forecast table, creating it if needed.

    Returns the number of rows written. WRITE_APPEND keeps every daily
    snapshot; de-duplication happens later in the dbt staging model.
    """
    job_config = bigquery.LoadJobConfig(
        schema=FORECAST_SCHEMA,
        write_disposition=bigquery.WriteDisposition.WRITE_APPEND,
    )
    job = client.load_table_from_json(rows, table_id, job_config=job_config)
    job.result()  # wait for completion; raises on failure
    return job.output_rows
```

- [ ] **Step 2: Verify it imports**

Run: `python -c "import weather_pipeline.load"`
Expected: no output, exit code 0.

- [ ] **Step 3: Commit**

```bash
git add weather_pipeline/load.py
git commit -m "feat: load rows into BigQuery raw forecast table"
```

---

## Task 6: Orchestrate + first real run

**Files:**
- Create: `weather_pipeline/main.py`

- [ ] **Step 1: Write the implementation**

`weather_pipeline/main.py`:
```python
from datetime import datetime, timezone

from weather_pipeline.config import get_forecast_table, get_project
from weather_pipeline.extract import fetch_forecast
from weather_pipeline.load import get_client, load_rows
from weather_pipeline.transform import to_row


def run() -> int:
    records = fetch_forecast()
    ingested_at = datetime.now(timezone.utc).isoformat()
    rows = [to_row(record, ingested_at) for record in records]

    client = get_client(get_project())
    table_id = get_forecast_table()
    written = load_rows(client, table_id, rows)
    print(f"Loaded {written} rows into {table_id} (ingested_at={ingested_at})")
    return written


if __name__ == "__main__":
    run()
```

- [ ] **Step 2: Create the `.env` file**

Copy `.env.example` to `.env` and set `GCP_PROJECT` to your real project id:
```bash
cp .env.example .env
# then edit .env: GCP_PROJECT=<your-project-id>
```

- [ ] **Step 3: Create the BigQuery dataset**

Run (replace `<your-project-id>`):
```bash
bq --location=asia-southeast1 mk --dataset <your-project-id>:weather_raw
```
Expected: `Dataset '<your-project-id>:weather_raw' successfully created.` (If it already exists, that is fine.)

- [ ] **Step 4: Run the pipeline for real**

Run: `python -m weather_pipeline.main`
Expected: a line like `Loaded 200 rows into <project>.weather_raw.forecast (ingested_at=2026-07-06T...)`. Row count matches the number of location/day forecasts returned.

- [ ] **Step 5: Verify the data landed**

Run:
```bash
bq query --use_legacy_sql=false "SELECT COUNT(*) AS n, MIN(forecast_date) AS first_day, MAX(forecast_date) AS last_day FROM \`<your-project-id>.weather_raw.forecast\`"
```
Expected: `n` > 0 and a spread of forecast dates.

- [ ] **Step 6: Commit**

```bash
git add weather_pipeline/main.py
git commit -m "feat: orchestrate extract-transform-load pipeline"
```

---

## Task 7: dbt — staging model + tests

**Files:**
- Create: `dbt/weather/dbt_project.yml`
- Create: `dbt/weather/models/staging/stg_weather_forecast.sql`
- Create: `dbt/weather/models/staging/schema.yml`
- Create: `~/.dbt/profiles.yml` (dbt's default profiles location)

- [ ] **Step 1: Create the dbt profile**

Create `~/.dbt/profiles.yml` (on Windows: `C:\Users\<you>\.dbt\profiles.yml`):
```yaml
weather:
  target: dev
  outputs:
    dev:
      type: bigquery
      method: oauth
      project: "{{ env_var('GCP_PROJECT') }}"
      dataset: weather_staging
      location: asia-southeast1
      threads: 4
```
This uses your `gcloud auth application-default login` credentials. `env_var('GCP_PROJECT')` reads the same variable from your shell/.env — make sure `GCP_PROJECT` is exported in the shell you run dbt from: `export GCP_PROJECT=<your-project-id>`.

- [ ] **Step 2: Create `dbt/weather/dbt_project.yml`**

```yaml
name: 'weather'
version: '1.0.0'
profile: 'weather'
model-paths: ["models"]
models:
  weather:
    staging:
      +materialized: view
```

- [ ] **Step 3: Create the source + tests in `dbt/weather/models/staging/schema.yml`**

```yaml
version: 2

sources:
  - name: weather_raw
    database: "{{ env_var('GCP_PROJECT') }}"
    schema: weather_raw
    tables:
      - name: forecast

models:
  - name: stg_weather_forecast
    description: "Latest snapshot per location per forecast date."
    columns:
      - name: location_id
        tests:
          - not_null
      - name: forecast_date
        tests:
          - not_null
      - name: max_temp
        tests:
          - not_null
```

- [ ] **Step 4: Create the model `dbt/weather/models/staging/stg_weather_forecast.sql`**

```sql
with source as (
    select * from {{ source('weather_raw', 'forecast') }}
),

deduped as (
    select
        location_id,
        location_name,
        forecast_date,
        morning_forecast,
        afternoon_forecast,
        night_forecast,
        summary_forecast,
        summary_when,
        min_temp,
        max_temp,
        ingested_at,
        row_number() over (
            partition by location_id, forecast_date
            order by ingested_at desc
        ) as row_num
    from source
)

select
    location_id,
    location_name,
    forecast_date,
    morning_forecast,
    afternoon_forecast,
    night_forecast,
    summary_forecast,
    summary_when,
    min_temp,
    max_temp,
    ingested_at
from deduped
where row_num = 1
```

- [ ] **Step 5: Run dbt**

Run (from `dbt/weather`):
```bash
cd dbt/weather
dbt run
```
Expected: `Completed successfully`, model `stg_weather_forecast` built as a view in the `weather_staging` dataset.

- [ ] **Step 6: Run dbt tests**

Run: `dbt test`
Expected: all `not_null` tests PASS.

- [ ] **Step 7: Commit**

```bash
cd ../..
git add dbt/weather
git commit -m "feat: dbt staging model with dedup and not-null tests"
```

---

## Task 8: Looker Studio chart (manual UI step)

No code. This is done in the Looker Studio web UI.

- [ ] **Step 1: Create a data source**

Go to https://lookerstudio.google.com → **Create → Data source → BigQuery** → select your project → dataset `weather_staging` → table `stg_weather_forecast` → **Connect**.

- [ ] **Step 2: Add a chart**

**Create Report** with this data source. Add a **Bar chart**:
- Dimension: `location_name`
- Metric: `max_temp` (aggregation: Average)
Optionally add a **Time series** chart: Dimension `forecast_date`, Metric `max_temp` (Average).

- [ ] **Step 3: Confirm it renders**

Expected: the chart shows average max temperature per location from the live BigQuery data. Rename the report `Malaysia Weather Forecast — Phase 1`.

- [ ] **Step 4: Capture the link**

Copy the report's share link (viewer access) to paste into the README in Task 9.

---

## Task 9: README + final Phase 1 commit

**Files:**
- Create: `README.md`

- [ ] **Step 1: Write `README.md`**

```markdown
# Malaysia Weather Forecast-Accuracy Pipeline

A modern-data-stack ELT pipeline over Malaysian open government data
([data.gov.my Weather API](https://developer.data.gov.my/realtime-api/weather)).
The API only exposes the *current* forecast, so this pipeline snapshots it daily
and accumulates the historical record needed to measure forecast accuracy over time.

## Architecture (Phase 1)

```
data.gov.my Weather API --(Python: extract)--> BigQuery raw.forecast
   --(dbt: staging + tests)--> weather_staging.stg_weather_forecast
   --(Looker Studio)--> dashboard
```

## Stack
Python, BigQuery, dbt, Looker Studio. All on free tiers.

## Run locally
1. `python -m venv .venv && source .venv/Scripts/activate && pip install -r requirements.txt`
2. `gcloud auth application-default login`
3. Copy `.env.example` to `.env`, set `GCP_PROJECT`.
4. `bq --location=asia-southeast1 mk --dataset $GCP_PROJECT:weather_raw`
5. `python -m weather_pipeline.main`
6. `cd dbt/weather && dbt run && dbt test`

## Tests
`python -m pytest -v`

## Dashboard
<paste Looker Studio link here>

## Roadmap
- Phase 2: forecast-vs-actual accuracy marts, PySpark aggregation
- Phase 3: Airflow orchestration, polished dashboard
- Phase 4 (stretch): real-time transit reliability from GTFS-Realtime
```

- [ ] **Step 2: Paste the Looker Studio link** from Task 8 into the README.

- [ ] **Step 3: Run the full test suite one last time**

Run: `python -m pytest -v`
Expected: all tests PASS (5 total).

- [ ] **Step 4: Commit**

```bash
git add README.md
git commit -m "docs: Phase 1 README with architecture and run instructions"
```

---

## Phase 1 Definition of Done
- [ ] `python -m pytest -v` passes (extract + transform units).
- [ ] `python -m weather_pipeline.main` loads fresh rows into `weather_raw.forecast`.
- [ ] `dbt run` builds `stg_weather_forecast`; `dbt test` passes.
- [ ] A Looker Studio chart renders live data.
- [ ] README documents architecture, run steps, and the dashboard link.
- [ ] All work committed to git.
