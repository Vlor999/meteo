"""Enum that represent the Weather mode."""

from enum import Enum


class WeatherMode(str, Enum):
    """Enum that represent the weather mode."""

    DAILY = "daily"
    HOURLY = "hourly"
