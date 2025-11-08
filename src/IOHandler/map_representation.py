"""The french map with meteo informations on it."""

import json
from typing import Any

import cv2 as cv
import numpy as np
from dotenv import load_dotenv
from loguru import logger

from src.params import LIMIT_EST, LIMIT_NORTH, LIMIT_SOUTH, LIMIT_WEST

load_dotenv()


def parse_coordinate(coord_str: str) -> float:
    """Transform string coordinates to angle."""
    # Remove degree symbol and extract direction
    parts = coord_str.split()
    degrees = float(parts[0])
    minutes = float(parts[1]) if len(parts) > 2 and parts[1].isdigit() else 0
    direction = parts[-1]

    decimal = degrees + minutes / 60

    # Apply sign based on direction
    if direction in ["W", "S"]:
        decimal = -decimal

    return decimal


def get_longitude(x: int, max_cols: int, limits: list[str]) -> float:
    """Convert pixel x-coordinate to longitude."""
    west_limit = parse_coordinate(limits[0])
    east_limit = parse_coordinate(limits[1])
    longitude = west_limit + (x / max_cols) * (east_limit - west_limit)
    return round(longitude, 6)


def get_latitude(y: int, max_y: int, limits: list[str]) -> float:
    """Convert pixel y-coordinate to latitude."""
    north_limit = parse_coordinate(limits[2])
    south_limit = parse_coordinate(limits[3])
    latitude = north_limit - (y / max_y) * (north_limit - south_limit)
    return round(latitude, 6)


def get_coord_from_lat_long(
    lat: float, long: float, number_lines: int, number_col: int, limits: list[str]
) -> tuple[int, int] | None:
    """Convert latitude and longitude to pixel coordinates (x, y)."""
    # Parse the geographical limits
    west_limit = parse_coordinate(limits[0])
    east_limit = parse_coordinate(limits[1])
    north_limit = parse_coordinate(limits[2])
    south_limit = parse_coordinate(limits[3])

    # Check if coordinates are within bounds
    if not (west_limit <= long <= east_limit and south_limit <= lat <= north_limit):
        return None

    # Convert longitude to x coordinate (west to east = 0 to number_col)
    x = int((long - west_limit) / (east_limit - west_limit) * number_col)

    # Convert latitude to y coordinate (north to south = 0 to number_lines)
    y = int((north_limit - lat) / (north_limit - south_limit) * number_lines)

    # Ensure coordinates are within image bounds
    x = max(0, min(x, number_col - 1))
    y = max(0, min(y, number_lines - 1))
    if x == 0 or x == number_col - 1 or y == 0 or y == number_lines - 1:
        return None

    return (x, y)


def handle_mouse_move(
    event: int, x: int, y: int, flags: int, params: Any | None
) -> None:
    """Handle the mouse events."""
    logger.debug(f"{x}, {y}, {event}, {flags}")
    if params is None:
        return
    copy_image = params["image"].copy()
    limits = params["limits"]
    nl, nc, _ = copy_image.shape
    lat = get_latitude(y, nl, limits=limits)
    long = get_longitude(x, nc, limits=limits)
    cv.putText(
        copy_image,
        f"({lat}, {long})",
        (x, y),
        cv.FONT_HERSHEY_COMPLEX,
        1,
        (0, 255, 0),
        2,
    )
    cv.imshow(params["win_name"], copy_image)


def display_map(image: np.ndarray, win_name: str, params: dict[str, Any]) -> None:
    """Main loop that handle mouse and display the map."""
    # Make a copy of the image so we don't modify the original
    image_copy = image.copy()
    cv.imshow(winname=win_name, mat=image_copy)
    params["image"] = image_copy
    params["win_name"] = win_name
    cv.setMouseCallback(win_name, handle_mouse_move, params)
    while True:
        key = cv.waitKey(1)
        if key == ord("q"):
            break
        if key == ord("c"):
            add_cities_to_image(params)


def add_cities_to_image(params: dict[str, Any]) -> None:
    """Add all the cities to the current image (location and name)."""
    win_name = params["win_name"]
    if not params["toggle_cities"]:
        params["toggle_cities"] = not params["toggle_cities"]
        params["image"] = params["init_map"]
        cv.imshow(winname=win_name, mat=params["image"])
        return
    current_map = params["image"]
    cities: list[dict[str, Any]] = params["cities"]
    limits = params["limits"]
    nl, nc, _ = current_map.shape
    new_cities = []
    useless_cities = 0
    for city in cities:
        lat, long = city["lat_long"]
        coord = get_coord_from_lat_long(
            lat=lat, long=long, number_col=nc, number_lines=nl, limits=limits
        )
        if coord is not None:
            x, y = coord
            cv.putText(
                current_map,
                city["title"],
                (x, y),
                cv.FONT_HERSHEY_COMPLEX,
                1,
                (0, 0, 0),
                2,
            )
            cv.imshow(winname=win_name, mat=current_map)
            new_cities.append(city)
        else:
            logger.warning(
                f"The current latitude and longitude ({lat}, {long}) of this location does not belong to this map: {city['title']}"
            )
            useless_cities += 1
    params["cities"] = new_cities
    logger.info(f"Deleted {useless_cities} cities")
    params["toggle_cities"] = not params["toggle_cities"]


if __name__ == "__main__":
    map_france = cv.imread(
        filename="data/France_location_map-Regions_and_departements-2016.png"
    )
    with open("data/french_cities_coord.json", encoding="utf-8") as f:
        cities = json.load(f)
    LIMITS = [LIMIT_WEST, LIMIT_EST, LIMIT_NORTH, LIMIT_SOUTH]
    display_map(
        image=map_france,
        win_name="france",
        params={
            "limits": LIMITS,
            "cities": cities,
            "init_map": map_france,
            "toggle_cities": True,
        },
    )
