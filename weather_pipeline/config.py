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
