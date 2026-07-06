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
