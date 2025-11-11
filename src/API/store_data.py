"""Store the extracted data into files and merge if needed."""

from typing import Any

import pandas as pd
from loguru import logger
from openmeteo_sdk.VariablesWithTime import VariablesWithTime

from src.API.weather_mods import WeatherMode
from src.params import QUERY_TEMPLATE


def extract_data(
    data: dict[str, Any],
    variables: VariablesWithTime | None,
    mode: WeatherMode = WeatherMode.DAILY,
) -> dict[str, Any]:
    """Extract the data from the answer of the API."""
    logger.debug("🏁 Starting to extract all the informations.")
    if variables is None:
        logger.warning("variables are None")
        return data

    data["date"] = pd.date_range(
        start=pd.to_datetime(variables.Time(), unit="s", utc=True),
        end=pd.to_datetime(variables.TimeEnd(), unit="s", utc=True),
        freq=pd.Timedelta(seconds=variables.Interval()),
        inclusive="left",
    )

    key: str
    for i, key in enumerate(QUERY_TEMPLATE[mode.value]):  # type: ignore[arg-type]
        current_var = variables.Variables(i)
        if current_var is None:
            logger.warning(
                f"The current variable: {key} is not availble into the {mode.value} data."
            )
            continue
        data[key] = current_var.ValuesAsNumpy()
    return data


if __name__ == "__main__":
    hourly_data: dict[str, Any] = {
        "latitude": 10,
        "longitude": 10,
        "elevation": 10,
        "timezone": 10,
        "model": "model",
        "date": "hello",
    }
    extract_data(hourly_data, None, WeatherMode.DAILY)
