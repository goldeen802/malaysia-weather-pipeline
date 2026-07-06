# Malaysia Weather Forecast-Accuracy ELT Pipeline — Design

**Date:** 2026-07-06
**Author:** Golden Wong
**Status:** Approved design — ready for implementation planning

## 1. Purpose

A portfolio data-engineering project that demonstrates hands-on experience with the
**modern data stack** — the tooling most commonly listed in Malaysian data-engineer
job postings (cloud data warehouse + dbt + orchestration + Spark). It is designed to be:

- **Free to run** — every component sits on an always-free or self-hosted tier.
- **Beginner-friendly** — SQL/Python-centric, playing to the author's existing strengths;
  gentle on-ramp for someone new to Docker, warehouses, and orchestration.
- **Useful and credible** — built on real Malaysian open government data, producing a
  genuine dashboard rather than a toy dataset.
- **Interview-ready** — tells a clear "why does this need a pipeline?" story.

### Target audience / market fit
Entry-level / graduate data-engineer roles in Malaysia. Market research (July 2026)
confirms these roles lead with **SQL + Python + hands-on projects**, and that
**Snowflake/BigQuery, dbt, Airflow, and PySpark** are the dominant, in-demand tools.

## 2. Core concept

Build a **batch ELT pipeline** over the **data.gov.my Weather API**.

The API only exposes the *current* forecast. It does not retain history. Therefore the
pipeline's job is to **snapshot the daily forecast, accumulate a historical record, then
later join what actually happened** to measure **forecast accuracy over time**.

This is the project's central narrative: **the pipeline is what creates data that would
not otherwise exist** — the clearest demonstration of why data engineering is needed.

## 3. Scope

### In scope (Core — B)
Weather forecast-accuracy ELT pipeline, Phases 1–3 (see §7).

### Parked stretch (D)
A second, near-real-time ingestion path over the **data.gov.my GTFS-Realtime** transit
feed (live vehicle positions, refreshed every 30 seconds) that derives transit reliability
by comparing live positions against the static GTFS timetable. It reuses the same
BigQuery + dbt + Looker Studio backbone. **Attempted only after B is complete** (Phase 4).

### Explicitly out of scope
- Kafka / Flink infrastructure (deliberately avoided as too steep for a first project).
- Any paid cloud tier or service with bill risk.
- Multi-cloud deployment.

## 4. Data sources (verified July 2026)

| Source | API | Refresh cadence | Used in |
|---|---|---|---|
| Weather forecast | data.gov.my Weather API | Several times daily | Core (B) |
| Transit vehicle positions | data.gov.my GTFS-Realtime | Every 30 seconds | Stretch (D) |
| Transit timetables | data.gov.my GTFS-Static | Daily (KTMB 00:01) | Stretch (D) |

Note on D: only **vehicle positions** are currently live. Official trip-updates and
service-alerts (ready-made delay data) are pending for 2026, so delays must be **derived**
by comparing positions to the static schedule.

## 5. Architecture

```
  data.gov.my Weather API  (free, no key)
        |  Python extract script            -- Extract
        v
  BigQuery: raw dataset  (always-free)       -- Load
        |
        +-- dbt: staging -> marts + tests    -- Transform (SQL)
        |
        +-- PySpark job: heavier historical  -- Spark
        |   aggregation, writes back to BigQuery
        v
  BigQuery: curated marts
        |
        v
  Looker Studio dashboard  (free)            -- Serve

  Orchestration: GitHub Actions cron (Phase 1) -> Airflow (Phase 3)
```

### Design decisions (the "shows understanding" section)
- **BigQuery over Snowflake:** BigQuery's free tier never expires, so the portfolio demo
  keeps working indefinitely; a Snowflake trial dies after 30 days. dbt keeps the warehouse
  swappable, so the pipeline is warehouse-agnostic.
- **ELT over ETL:** load raw first, transform in-warehouse with dbt — the modern norm and
  what employers list.
- **Idempotent daily snapshots:** each run writes a partition keyed by forecast date so
  re-runs do not duplicate data.
- **Data quality as a first-class step:** dbt tests (not-null, accepted ranges, uniqueness)
  enforce "clean, reliable data products."
- **Layered modeling:** `raw` -> `staging` (clean/typecast) -> `marts` (business logic).

## 6. Components

1. **Extract** — Python script calls the Weather API daily, saves raw JSON.
2. **Load** — push raw records into a `raw` dataset in BigQuery.
3. **Transform (dbt)** — `staging` models clean and typecast; `marts` models compute
   forecast-vs-actual accuracy metrics; dbt tests validate the data.
4. **Spark step (PySpark)** — one heavier historical aggregation (e.g. rolling accuracy by
   region) written back to BigQuery. Covers the Spark keyword.
5. **Orchestration** — GitHub Actions cron runs the daily pipeline for free (Phase 1);
   Airflow added in Phase 3 as the industry-standard keyword.
6. **Serve** — Looker Studio dashboard showing forecast-accuracy trends over time.

## 7. Phase plan

- **Phase 1 (week 1) — thin end-to-end slice:** Python extract -> BigQuery raw -> one dbt
  staging model -> one basic Looker Studio chart. Goal: something working end-to-end.
- **Phase 2 (week 2) — real logic:** full dbt marts + tests, forecast-vs-actual accuracy
  logic, the PySpark aggregation.
- **Phase 3 (week 2–3) — polish:** Airflow orchestration, polished dashboard, README with
  architecture diagram + design-decisions section, demo GIF.
- **Phase 4 (stretch) — transit (D):** GTFS-Realtime ingestion into the same warehouse,
  dbt models deriving delays vs. schedule, a reliability panel.

## 8. Prerequisites (already in place)
- Google Cloud account with BigQuery + Looker Studio access.
- GitHub account (repo + free GitHub Actions).
- Python and Docker Desktop installed locally (Docker needed only from Phase 2/3 for
  Spark/Airflow).

## 9. Success criteria
- Phase 1: a scheduled run lands fresh weather data in BigQuery and a Looker chart reflects it.
- Phase 3: a public GitHub repo with a clear README, running daily via Airflow/Actions,
  a live dashboard, dbt tests passing, and 2–3 résumé-ready bullets derived from the build.

## 10. Résumé mapping

| Component | Résumé-ready claim |
|---|---|
| Extract + Load | "Built a Python ELT pipeline ingesting Malaysian open-government data into BigQuery" |
| dbt | "Modeled curated marts in BigQuery with dbt, enforcing data quality via automated tests" |
| PySpark | "Wrote a PySpark job for historical aggregation over warehouse data" |
| Airflow | "Orchestrated a daily pipeline with Apache Airflow" |
| Looker Studio | "Delivered a self-serve dashboard on forecast-accuracy trends" |
