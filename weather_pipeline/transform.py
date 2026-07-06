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
