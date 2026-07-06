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
