"""Param file that handle all the parameters."""

# File
FILE = "data/MN_01_2000-2009.csv"
DATA_DIR = "data"
BBOX_DIR = "bbox"

## Replace token
REPLACE_TOKEN = "<INFO>"
## API
TEMPLATE_DAILY_CSV = f"daily_{REPLACE_TOKEN}.csv"
TEMPLATE_HOURLY_CSV = f"hourly_{REPLACE_TOKEN}.csv"

## Query template
QUERY_TEMPLATE = {
    "latitude": 0.0,
    "longitude": 0.0,
    "daily": [
        "uv_index_max",
        "apparent_temperature_max",
        "apparent_temperature_min",
        "weather_code",
        "temperature_2m_max",
        "temperature_2m_min",
        "sunshine_duration",
        "daylight_duration",
        "sunset",
        "sunrise",
        "uv_index_clear_sky_max",
        "precipitation_probability_max",
        "precipitation_hours",
        "precipitation_sum",
        "snowfall_sum",
        "showers_sum",
        "rain_sum",
        "et0_fao_evapotranspiration",
        "shortwave_radiation_sum",
        "wind_direction_10m_dominant",
        "wind_gusts_10m_max",
        "wind_speed_10m_max",
    ],
    "hourly": [
        "temperature_2m",
        "is_day",
        "sunshine_duration",
        "relative_humidity_2m",
        "apparent_temperature",
        "precipitation",
        "weather_code",
        "pressure_msl",
        "surface_pressure",
        "cloud_cover",
        "wind_speed_10m",
        "wind_direction_10m",
        "dew_point_2m",
        "rain",
        "snowfall",
        "cloud_cover_low",
        "cloud_cover_mid",
        "cloud_cover_high",
        "et0_fao_evapotranspiration",
        "vapour_pressure_deficit",
        "wind_gusts_10m",
        "wind_direction_200m",
        "wind_direction_150m",
        "wind_direction_100m",
        "wind_direction_50m",
        "wind_direction_20m",
        "wind_speed_200m",
        "wind_speed_150m",
        "wind_speed_100m",
        "wind_speed_50m",
        "wind_speed_20m",
        "temperature_20m",
        "temperature_50m",
        "temperature_100m",
        "temperature_150m",
        "temperature_200m",
        "cape",
        "wet_bulb_temperature_2m",
        "shortwave_radiation",
        "direct_radiation",
        "diffuse_radiation",
        "direct_normal_irradiance",
        "global_tilted_irradiance",
        "terrestrial_radiation",
        "shortwave_radiation_instant",
        "direct_radiation_instant",
        "diffuse_radiation_instant",
        "direct_normal_irradiance_instant",
        "global_tilted_irradiance_instant",
        "terrestrial_radiation_instant",
    ],
    "models": ["arpege_europe", "arome_france", "arome_france_hd"],
    "timezone": "Europe/Berlin",
    "wind_speed_unit": "ms",
    "bounding_box": "<SOUTH>,<WEST>,<NORTH>,<EST>",  # South, West, North, Est
    "start_date": "2025-11-01",  # YYYY-MM-DD
    "end_date": "2025-11-15",
}

# Limits:
LIMIT_WEST = "005 48 W"
LIMIT_EST = "10 E"
LIMIT_NORTH = "51 30 N"
LIMIT_SOUTH = "41 N"
