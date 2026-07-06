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
