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
