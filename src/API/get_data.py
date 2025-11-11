"""Get the current data of the weather API."""

import time
from os import environ
from typing import Any

import openmeteo_requests
import pandas as pd
import requests_cache
from dotenv import load_dotenv
from loguru import logger
from openmeteo_requests.Client import WeatherApiResponse
from retry_requests import retry

from src.API.store_data import extract_data
from src.API.utils import get_sized_bboxes, write_bbox
from src.API.weather_mods import WeatherMode
from src.IOHandler.write_data import save_dataframe
from src.params import (
    DATA_DIR,
    QUERY_TEMPLATE,
    REPLACE_TOKEN,
    TEMPLATE_DAILY_CSV,
    TEMPLATE_HOURLY_CSV,
)
from src.utils.default_values import get_coordinates

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
    val = abs(north - south) * abs(est - west) / 0.01
    logger.debug(f"Current estimation of the grid size: {val}")
    return val


def get_response(
    openmeteo: openmeteo_requests.Client,
    url: str,
    north: float,
    south: float,
    west: float,
    est: float,
    params_template: dict[str, Any],
    waiting_time: int = 70,
    max_locations: int = 100,
    max_retries: int = 2000,
) -> list[list[WeatherApiResponse]]:
    """Sub cut the bouding boxe to have all the meteo data."""
    params = params_template.copy()
    # bounding_boxes = deque([(north, south, west, est)])
    bounding_boxes = get_sized_bboxes(default_bbox=(north, south, west, est))
    results = []
    checked_boxes = set()
    failures = 0
    must_save = True

    while bounding_boxes and failures < max_retries:
        head = bounding_boxes.popleft()
        curr_north, curr_south, curr_west, curr_est = head

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
            if must_save:
                cp_bouding = bounding_boxes.copy()
                cp_bouding.extend([(curr_north, curr_south, curr_west, curr_est)])
                write_bbox(cp_bouding)
                must_save = False
            return results  # TODO: change it later for multiple results
        except Exception as e:
            reason = e.args[0] if e.args else str(e)

            if "1000 locations" in reason or "too many" in reason.lower():
                # Split this box immediately (too large)
                logger.warning(f"Box too large, splitting {key}")
                new_boxes = create_new_rectangles(
                    curr_north, curr_south, curr_west, curr_est
                )
                bounding_boxes.extend(new_boxes)
                failures += 1

            elif "API request limit exceeded" in reason:
                logger.warning(f"Rate limit hit. Sleeping {waiting_time}s...")
                time.sleep(waiting_time)
                waiting_time = min(waiting_time << 1, 300)
                bounding_boxes.appendleft((curr_north, curr_south, curr_west, curr_est))
                checked_boxes.discard(key)

            else:
                logger.warning(f"Unexpected error for {key}: {reason}")
                time.sleep(2)
                failures += 1

        logger.info(
            f"Currently have: {len(results)} results and [{failures}/{max_retries}] failures"
        )
    return results


def call_api(
    url: str, lat: float | int, long: float | int
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Main function that get the responses and add informations together."""
    cache_session = requests_cache.CachedSession(".cache", expire_after=3600)
    retry_session = retry(cache_session, retries=5, backoff_factor=0.2)
    openmeteo = openmeteo_requests.Client(session=retry_session)

    # Setup the Open-Meteo API client with ALL available weather variables
    params = QUERY_TEMPLATE.copy()

    params["latitude"] = lat
    params["longitude"] = long

    north, south, west, est = get_coordinates()

    responses = get_response(
        openmeteo=openmeteo,
        url=url,
        north=north,
        south=south,
        west=west,
        est=est,
        params_template=params,
    )
    logger.info(f"Received {len(responses)} response groups")

    dataframes_hourly_daily = {mode: pd.DataFrame() for mode in WeatherMode}

    for local_reponse in responses:
        for response in local_reponse:
            current_lat, current_long = response.Latitude(), response.Longitude()
            elevation = response.Elevation()
            timezone = response.Timezone()
            model = response.Model()

            # Process hourly and daily data - ALL VARIABLES
            hourly = response.Hourly()
            daily = response.Daily()
            responses_daily_hourly = {
                WeatherMode.HOURLY: hourly,
                WeatherMode.DAILY: daily,
            }

            for mode in WeatherMode:
                current_data: dict[str, Any] = {
                    "latitude": current_lat,
                    "longitude": current_long,
                    "elevation": elevation,
                    "timezone": timezone,
                    "model": model,
                }

                extracted_data = extract_data(
                    current_data, responses_daily_hourly[mode], mode
                )
                df_extracted = pd.DataFrame(extracted_data)
                dataframes_hourly_daily[mode] = pd.concat(
                    [dataframes_hourly_daily[mode], df_extracted]
                )

    daily_dataframe = dataframes_hourly_daily[WeatherMode.DAILY]
    hourly_dataframe = dataframes_hourly_daily[WeatherMode.HOURLY]
    return daily_dataframe, hourly_dataframe


def get_and_save_data(
    url: str,
    latitude: float = 8.866667,
    longitude: float = 2.333333,
    replace_tok_daily: str = "",
    replace_tok_hourly: str = "",
) -> None:
    """Extract all the informations and store everything into the defined csv."""
    daily_dataframe, hourly_dataframe = call_api(url=url, lat=latitude, long=longitude)
    daily_csv = f"{DATA_DIR}/{TEMPLATE_DAILY_CSV}".replace(
        REPLACE_TOKEN, replace_tok_daily
    )
    hourly_csv = f"{DATA_DIR}/{TEMPLATE_HOURLY_CSV}".replace(
        REPLACE_TOKEN, replace_tok_hourly
    )
    save_dataframe([daily_dataframe, hourly_dataframe], [daily_csv, hourly_csv])


if __name__ == "__main__":
    URL = environ["URL"]
    get_and_save_data(url=URL)
