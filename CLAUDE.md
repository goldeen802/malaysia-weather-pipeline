# Project: Malaysia Weather Forecast-Accuracy ELT Pipeline

This file is auto-loaded by Claude Code. It packs the context from the brainstorming
session so any new session can continue without re-deriving decisions.

## What this project is
A portfolio data-engineering project: a **batch ELT pipeline** over the
**data.gov.my Weather API**. The API only exposes the *current* forecast, so the pipeline
snapshots it daily (stamping each row with `ingested_at`) to accumulate the historical
record needed to measure **forecast accuracy over time**. That "the pipeline creates data
that wouldn't otherwise exist" story is the project's core selling point in interviews.

## Who this is for
- **Owner:** Golden Wong — background in actuarial + data science; strong in **Python and SQL**.
- **Goal:** land an **entry-level / graduate Data Engineer role in Malaysia** (job-hunting now).
- **Starting point:** **new to Docker, cloud warehouses, dbt, and orchestration**; needs a
  gentle on-ramp, not a firehose of infra tools.
- **Time budget:** ~2-3 weeks, steady (a couple hours most evenings).

## Constraints (non-negotiable)
- **Free to run** — every component on an always-free or self-hosted tier. No bill risk.
- **Beginner-friendly** — SQL/Python-centric; avoid steep infra.
- **Useful + credible** — real Malaysian open-government data, real dashboard.

## Key decisions and rationale
- **Modern data stack over Kafka/Flink streaming.** Market research (July 2026) shows
  Malaysian entry-level DE roles lead with SQL + Python + hands-on projects, and that
  Snowflake/BigQuery + dbt + Airflow + PySpark are the in-demand tools. Streaming was the
  original JD trigger but is too steep as a first project and less common at entry level.
- **BigQuery over Snowflake.** BigQuery's free tier never expires, so the portfolio demo
  keeps working for recruiters indefinitely; a Snowflake trial dies after 30 days. dbt keeps
  the warehouse swappable (a good interview talking point).
- **One PySpark step included** (Phase 2) because Malaysian postings specifically name Spark/PySpark.
- **Malaysian open data** (data.gov.my) chosen for local relevance + genuine usefulness.
- **Weather forecast-accuracy** chosen over fuel prices (weekly) / economic data (monthly)
  because the Weather API refreshes several times daily — the freshest source that justifies
  a daily scheduled pipeline.

## Roadmap
- **Phase 1 (current):** thin end-to-end slice — Python extract -> BigQuery raw -> one dbt
  staging model -> one Looker Studio chart. See `docs/plans/2026-07-06-weather-pipeline-phase1.md`.
- **Phase 2:** forecast-vs-actual accuracy marts + dbt tests + a PySpark aggregation.
- **Phase 3:** Airflow orchestration, polished dashboard, README + demo GIF.
- **Phase 4 (stretch):** near-real-time **transit reliability** from data.gov.my GTFS-Realtime
  (live vehicle positions every 30s) into the same BigQuery + dbt + Looker backbone. Delays
  must be *derived* vs. the static timetable (official trip-updates feed not live yet).

## Tech stack
Python 3.11+, `requests`, `google-cloud-bigquery`, `python-dotenv`, `pytest`, `responses`,
`dbt-bigquery`, Looker Studio. BigQuery region: `asia-southeast1`.

## How to work on this
- **Design spec:** `docs/specs/2026-07-06-malaysia-weather-elt-pipeline-design.md`
- **Phase 1 plan:** `docs/plans/2026-07-06-weather-pipeline-phase1.md` (9 TDD tasks, copy-paste code)
- **To build Phase 1:** use the executing-plans skill, one task at a time.
- **One-time auth before building:** `gcloud auth application-default login`
  (gives both Python and dbt their BigQuery credentials via Application Default Credentials).
- **Have ready:** your GCP project id (for `.env` and the dataset).

## Prerequisites already in place
Google Cloud + BigQuery, GitHub account, Python + Docker installed locally.
