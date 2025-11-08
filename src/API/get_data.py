"""Get the current data of the weather API."""

import time
from collections import deque
from os import environ
from typing import Any

import openmeteo_requests
import pandas as pd
import requests_cache
from dotenv import load_dotenv
from loguru import logger
from openmeteo_requests.Client import WeatherApiResponse
from retry_requests import retry

load_dotenv()


def create_new_rectangles(
    north: float, south: float, west: float, est: float
) -> list[tuple[float, float, float, float]]:
    """Create 4 new sub rectangles.

    Args:
        north (float) : float represent the north coordinate
        south (float) : float represent the south coordinate
        west (float) : float represent the west coordinate
        est (float) : float represent the est coordinate

    Returns:
        - return 4 new sub bounding boxes (top-left, top-right, etc)
    """
    mid_lat = (north + south) / 2
    mid_lon = (west + est) / 2
    return [
        (north, mid_lat, west, mid_lon),
        (north, mid_lat, mid_lon, est),
        (mid_lat, south, west, mid_lon),
        (mid_lat, south, mid_lon, est),
    ]


def estimate_grid_size(north: float, south: float, west: float, est: float) -> float:
    """Rough heuristic: 0.1° step ≈ 11 km, used by Open-Meteo models."""
    return abs(north - south) * abs(est - west) / 0.1**2


def get_response(
    openmeteo: openmeteo_requests.Client,
    url: str,
    north: float,
    south: float,
    west: float,
    est: float,
    params_template: dict[str, Any],
    waiting_time: int = 70,
    max_locations: int = 1000,
    max_retries: int = 200,
) -> list[list[WeatherApiResponse]]:
    """Sub cut the bouding boxe to have all the meteo data."""
    params = params_template.copy()
    bounding_boxes = deque([(north, south, west, est)])
    results = []
    checked_boxes = set()
    failures = 0

    while bounding_boxes and failures < max_retries:
        curr_north, curr_south, curr_west, curr_est = bounding_boxes.popleft()

        # Skip duplicate boxes
        key = (
            round(curr_north, 3),
            round(curr_south, 3),
            round(curr_west, 3),
            round(curr_est, 3),
        )
        if key in checked_boxes:
            continue
        checked_boxes.add(key)

        # Avoid infinite recursion with too small boxes
        if abs(curr_north - curr_south) < 0.05 or abs(curr_est - curr_west) < 0.05:
            logger.debug(f"Skipping too small box {key}")
            continue

        # Estimate whether this box is too large before calling API
        if (
            estimate_grid_size(curr_north, curr_south, curr_west, curr_est)
            > max_locations
        ):
            new_boxes = create_new_rectangles(
                curr_north, curr_south, curr_west, curr_est
            )
            bounding_boxes.extend(new_boxes)
            continue

        params["bounding_box"] = (
            params_template["bounding_box"]
            .replace("<SOUTH>", str(curr_south))
            .replace("<NORTH>", str(curr_north))
            .replace("<WEST>", str(curr_west))
            .replace("<EST>", str(curr_est))
        )

        try:
            result = openmeteo.weather_api(url, params)
            results.append(result)
            logger.info(f"Success for box {key}, total results: {len(results)}")
        except Exception as e:
            reason = e.args[0] if e.args else str(e)

            if "1000 locations" in reason or "too many" in reason.lower():
                # Split this box immediately (too large)
                logger.warning(f"Box too large, splitting {key}")
                new_boxes = create_new_rectangles(
                    curr_north, curr_south, curr_west, curr_est
                )
                bounding_boxes.extend(new_boxes)

            elif "API request limit exceeded" in reason:
                logger.warning(f"Rate limit hit. Sleeping {waiting_time}s...")
                time.sleep(waiting_time)
                waiting_time = min(waiting_time * 2, 300)

            else:
                logger.warning(f"Unexpected error for {key}: {reason}")
                time.sleep(2)

            failures += 1
        logger.info(
            f"Currently have: {len(result)} results and [{failures}/{max_retries}] failures"
        )
    return results


def call_api(url: str, lat: float | int, long: float | int) -> None:
    """Main function that get the responses and add informations together."""
    cache_session = requests_cache.CachedSession(".cache", expire_after=3600)
    retry_session = retry(cache_session, retries=5, backoff_factor=0.2)
    openmeteo = openmeteo_requests.Client(session=retry_session)
    # Setup the Open-Meteo API client with cache and retry on error
    params = {
        "latitude": lat,
        "longitude": long,
        "daily": [
            "uv_index_max",
            "apparent_temperature_max",
            "apparent_temperature_min",
        ],
        "hourly": ["temperature_2m", "rain", "is_day", "sunshine_duration"],
        "models": ["arpege_europe", "arome_france", "arome_france_hd"],
        "timezone": "Europe/Berlin",
        "wind_speed_unit": "ms",
        "bounding_box": "<SOUTH>,<WEST>,<NORTH>,<EST>",  # South, West, North, Est
        "start_date": "2025-11-01",  # YYYY-MM-DD
        "end_date": "2025-11-15",
    }

    responses = get_response(
        openmeteo=openmeteo,
        url=url,
        north=51.0,
        south=41.0,
        west=5.0,
        est=10.0,
        params_template=params,
    )
    if responses is None:
        return
    print(len(responses))

    # Process 1 location and 3 models
    for local_reponse in responses:
        for response in local_reponse:
            print(f"\nCoordinates: {response.Latitude()}°N {response.Longitude()}°E")
            print(f"Elevation: {response.Elevation()} m asl")
            print(f"Timezone: {response.Timezone()}{response.TimezoneAbbreviation()}")
            print(f"Timezone difference to GMT+0: {response.UtcOffsetSeconds()}s")
            print(f"Model Nº: {response.Model()}")

            # Process hourly data.
            # The order of variables needs to be the same as requested.
            hourly = response.Hourly()
            if hourly is None:
                continue
            hourly_temperature_2m = hourly.Variables(0).ValuesAsNumpy()
            hourly_rain = hourly.Variables(1).ValuesAsNumpy()
            hourly_is_day = hourly.Variables(2).ValuesAsNumpy()
            hourly_sunshine_duration = hourly.Variables(3).ValuesAsNumpy()

            hourly_data: dict[str, Any] = {
                "date": pd.date_range(
                    start=pd.to_datetime(hourly.Time(), unit="s", utc=True),
                    end=pd.to_datetime(hourly.TimeEnd(), unit="s", utc=True),
                    freq=pd.Timedelta(seconds=hourly.Interval()),
                    inclusive="left",
                )
            }

            hourly_data["temperature_2m"] = hourly_temperature_2m
            hourly_data["rain"] = hourly_rain
            hourly_data["is_day"] = hourly_is_day
            hourly_data["sunshine_duration"] = hourly_sunshine_duration

            hourly_dataframe = pd.DataFrame(data=hourly_data)
            print("\nHourly data\n", hourly_dataframe)

            # Process daily data.
            # The order of variables needs to be the same as requested.
            daily = response.Daily()
            if daily is None:
                continue
            daily_uv_index_max = daily.Variables(0).ValuesAsNumpy()
            daily_apparent_temperature_max = daily.Variables(1).ValuesAsNumpy()
            daily_apparent_temperature_min = daily.Variables(2).ValuesAsNumpy()

            daily_data: dict[str, Any] = {
                "date": pd.date_range(
                    start=pd.to_datetime(daily.Time(), unit="s", utc=True),
                    end=pd.to_datetime(daily.TimeEnd(), unit="s", utc=True),
                    freq=pd.Timedelta(seconds=daily.Interval()),
                    inclusive="left",
                )
            }

            daily_data["uv_index_max"] = daily_uv_index_max
            daily_data["apparent_temperature_max"] = daily_apparent_temperature_max
            daily_data["apparent_temperature_min"] = daily_apparent_temperature_min

            daily_dataframe = pd.DataFrame(data=daily_data)
            print("\nDaily data\n", daily_dataframe)


if __name__ == "__main__":
    URL = environ["URL"]
    call_api(url=URL, lat=48.866667, long=2.333333)
