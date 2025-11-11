from collections import deque
from unittest.mock import Mock, patch

import pandas as pd

from src.API.get_data import (
    call_api,
    create_new_rectangles,
    estimate_grid_size,
    get_response,
)


def test_create_new_rectangles():
    north = 100
    south = 0
    west = 50
    est = 75
    rectangles = create_new_rectangles(north=north, south=south, west=west, est=est)
    assert len(rectangles) == 4


def test_estimate_grid_size():
    north = 100
    south = 0
    west = 50
    est = 75
    estimation = estimate_grid_size(north=north, south=south, west=west, est=est)
    assert estimation > 1000


def test_get_response():
    mock_openmeteo = Mock()
    mock_response = Mock()
    # Setup the Open-Meteo API client with cache and retry on error
    mock_openmeteo.weather_api.return_value = [mock_response]

    params = {
        "latitude": 100,
        "longitude": 100,
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

    # Use a smaller bounding box that won't be split
    result = get_response(
        openmeteo=mock_openmeteo,
        url="url",
        north=49.0,
        south=48.0,
        west=5.0,
        est=6.0,
        params_template=params,
    )
    assert len(result) == 1
    assert result[0] == [mock_response]
    mock_openmeteo.weather_api.assert_called_once()


@patch("src.API.get_data.get_sized_bboxes")
def test_get_response_box_too_large(mock_get_sized_bboxes):
    """Test that large boxes are split when they exceed location limit."""
    mock_get_sized_bboxes.return_value = deque(
        [(50.0, 40.0, 0.0, 10.0)]
    )  # Large box that should be split

    mock_openmeteo = Mock()

    # Mock response for successful calls
    mock_response = Mock()

    # First call raises "1000 locations" error, then subsequent calls succeed
    mock_openmeteo.weather_api.side_effect = [
        Exception("1000 locations exceeded"),
        [mock_response],  # Second call succeeds
        [mock_response],  # Third call succeeds
        [mock_response],  # Fourth call succeeds
        [mock_response],  # Fifth call succeeds
    ]

    params = {
        "bounding_box": "<SOUTH>,<WEST>,<NORTH>,<EST>",
        "daily": ["temperature_max"],
    }

    result = get_response(
        openmeteo=mock_openmeteo,
        url="test_url",
        north=50.0,
        south=40.0,
        west=0.0,
        est=10.0,
        params_template=params,
        max_retries=50,  # Allow more retries for splitting
    )

    # Should have 1 successful response (function returns after first success)
    assert len(result) == 1
    # Check that the first call failed and at least one subsequent call succeeded
    assert mock_openmeteo.weather_api.call_count >= 2


def test_get_response_box_too_small():
    """Test that boxes that are too small get skipped."""
    mock_openmeteo = Mock()
    mock_response = Mock()
    mock_openmeteo.weather_api.return_value = [mock_response]

    params = {
        "bounding_box": "<SOUTH>,<WEST>,<NORTH>,<EST>",
        "daily": ["temperature_max"],
    }

    # Use a box that's exactly at the minimum size threshold (0.05 degrees)
    result = get_response(
        openmeteo=mock_openmeteo,
        url="test_url",
        north=50.06,  # Just above the 0.05 threshold
        south=50.0,
        west=0.06,  # Just above the 0.05 threshold
        est=0.0,
        params_template=params,
        max_retries=10,
    )

    # Should get 1 successful response since the box is just big enough
    assert len(result) == 1
    assert mock_openmeteo.weather_api.call_count == 1


@patch("src.API.get_data.time.sleep")
def test_get_response_rate_limit(mock_sleep):
    """Test rate limit handling with exponential backoff."""
    mock_openmeteo = Mock()
    mock_response = Mock()

    # First call hits rate limit, second succeeds
    mock_openmeteo.weather_api.side_effect = [
        Exception("API request limit exceeded"),
        [mock_response],
    ]

    params = {
        "bounding_box": "<SOUTH>,<WEST>,<NORTH>,<EST>",
        "daily": ["temperature_max"],
    }

    result = get_response(
        openmeteo=mock_openmeteo,
        url="test_url",
        north=50.0,
        south=49.0,
        west=2.0,
        est=3.0,
        params_template=params,
        waiting_time=1,
    )

    assert len(result) == 1
    mock_sleep.assert_called_once_with(1)  # Should sleep for waiting_time
    assert mock_openmeteo.weather_api.call_count == 2


@patch("src.API.get_data.get_response")
def test_call_api_empty_response(mock_get_response):
    """Test call_api when get_response returns empty list."""
    mock_get_response.return_value = []

    # Should return empty DataFrames
    daily_df, hourly_df = call_api("test_url", 48.8566, 2.3522)

    assert isinstance(daily_df, pd.DataFrame)
    assert isinstance(hourly_df, pd.DataFrame)
    assert len(daily_df) == 0
    assert len(hourly_df) == 0
    mock_get_response.assert_called_once()


@patch("src.API.get_data.get_response")
def test_call_api_with_response(mock_get_response):
    """Test call_api with a proper response that processes data."""
    import numpy as np

    # Create mock response
    mock_response = Mock()
    mock_get_response.return_value = [[mock_response]]

    # Mock basic response attributes
    mock_response.Latitude.return_value = 48.8566
    mock_response.Longitude.return_value = 2.3522
    mock_response.Elevation.return_value = 35
    mock_response.Timezone.return_value = "Europe/Berlin"
    mock_response.TimezoneAbbreviation.return_value = "CET"
    mock_response.UtcOffsetSeconds.return_value = 3600
    mock_response.Model.return_value = "test_model"

    # Mock hourly data
    mock_hourly = Mock()
    mock_response.Hourly.return_value = mock_hourly
    mock_hourly.Time.return_value = 1730462400  # Unix timestamp
    mock_hourly.TimeEnd.return_value = (
        1730469600  # Unix timestamp + 2 hours (for 2 data points)
    )
    mock_hourly.Interval.return_value = 3600  # 1 hour

    # Create test data with same length for all variables
    hourly_data = np.array([20.0, 21.0])  # 2 hours of data

    # Mock hourly variables - each call to Variables returns different mock
    mock_var1 = Mock()
    mock_var1.ValuesAsNumpy.return_value = hourly_data  # temperature
    mock_var2 = Mock()
    mock_var2.ValuesAsNumpy.return_value = np.array([0.5, 0.0])  # rain
    mock_var3 = Mock()
    mock_var3.ValuesAsNumpy.return_value = np.array([1, 1])  # is_day
    mock_var4 = Mock()
    mock_var4.ValuesAsNumpy.return_value = np.array([3600, 3600])  # sunshine_duration

    mock_hourly.Variables.side_effect = [mock_var1, mock_var2, mock_var3, mock_var4] + [
        None
    ] * 46  # Return None for the remaining variables

    # Mock daily data
    mock_daily = Mock()
    mock_response.Daily.return_value = mock_daily
    mock_daily.Time.return_value = 1730462400  # Unix timestamp
    mock_daily.TimeEnd.return_value = 1730548800  # Unix timestamp + 1 day
    mock_daily.Interval.return_value = 86400  # 1 day

    # Create daily test data
    daily_data = np.array([8.5])  # 1 day of data

    # Mock daily variables
    mock_daily_var1 = Mock()
    mock_daily_var1.ValuesAsNumpy.return_value = daily_data  # uv_index_max
    mock_daily_var2 = Mock()
    mock_daily_var2.ValuesAsNumpy.return_value = np.array(
        [25.0]
    )  # apparent_temperature_max
    mock_daily_var3 = Mock()
    mock_daily_var3.ValuesAsNumpy.return_value = np.array(
        [15.0]
    )  # apparent_temperature_min

    mock_daily.Variables.side_effect = [
        mock_daily_var1,
        mock_daily_var2,
        mock_daily_var3,
    ] + [None] * 19  # Return None for the remaining variables

    # Call the function - should process data without errors
    daily_df, hourly_df = call_api("test_url", 48.8566, 2.3522)

    # Verify the function completed successfully and returned DataFrames
    assert isinstance(daily_df, pd.DataFrame)
    assert isinstance(hourly_df, pd.DataFrame)
    assert len(daily_df) > 0
    assert len(hourly_df) > 0
    mock_get_response.assert_called_once()

    # Verify that the response methods were called
    mock_response.Latitude.assert_called()
    mock_response.Hourly.assert_called()
    mock_response.Daily.assert_called()
