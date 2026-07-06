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
