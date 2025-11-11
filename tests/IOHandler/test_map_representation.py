"""Tests for map_representation.py."""

from unittest.mock import patch

import numpy as np

from src.IOHandler.map_representation import (
    add_cities_to_image,
    get_coord_from_lat_long,
    get_latitude,
    get_longitude,
    handle_mouse_move,
    parse_coordinate,
)


class TestParseCoordinate:
    """Test parse_coordinate function."""

    def test_parse_north_positive(self):
        """Test parsing northern latitude."""
        result = parse_coordinate("51 30 N")
        assert result == 51.5

    def test_parse_south_negative(self):
        """Test parsing southern latitude."""
        result = parse_coordinate("41 N")
        assert result == 41.0

    def test_parse_west_negative(self):
        """Test parsing western longitude."""
        result = parse_coordinate("005 48 W")
        assert result == -5.8

    def test_parse_east_positive(self):
        """Test parsing eastern longitude."""
        result = parse_coordinate("10 E")
        assert result == 10.0

    def test_parse_with_minutes(self):
        """Test parsing with minutes."""
        result = parse_coordinate("51 30 N")
        assert result == 51.5

    def test_parse_without_minutes(self):
        """Test parsing without minutes."""
        result = parse_coordinate("41 N")
        assert result == 41.0


class TestGetLongitude:
    """Test get_longitude function."""

    def test_get_longitude_west(self):
        """Test longitude calculation at west edge."""
        limits = ["005 48 W", "10 E", "51 30 N", "41 N"]
        result = get_longitude(0, 100, limits)
        expected = -5.8
        assert abs(result - expected) < 0.001

    def test_get_longitude_east(self):
        """Test longitude calculation at east edge."""
        limits = ["005 48 W", "10 E", "51 30 N", "41 N"]
        result = get_longitude(100, 100, limits)
        expected = 10.0
        assert abs(result - expected) < 0.001

    def test_get_longitude_middle(self):
        """Test longitude calculation in middle."""
        limits = ["005 48 W", "10 E", "51 30 N", "41 N"]
        result = get_longitude(50, 100, limits)
        expected = 2.1
        assert abs(result - expected) < 0.001


class TestGetLatitude:
    """Test get_latitude function."""

    def test_get_latitude_north(self):
        """Test latitude calculation at north edge."""
        limits = ["005 48 W", "10 E", "51 30 N", "41 N"]
        result = get_latitude(0, 100, limits)
        expected = 51.5
        assert abs(result - expected) < 0.001

    def test_get_latitude_south(self):
        """Test latitude calculation at south edge."""
        limits = ["005 48 W", "10 E", "51 30 N", "41 N"]
        result = get_latitude(100, 100, limits)
        expected = 41.0
        assert abs(result - expected) < 0.001

    def test_get_latitude_middle(self):
        """Test latitude calculation in middle."""
        limits = ["005 48 W", "10 E", "51 30 N", "41 N"]
        result = get_latitude(50, 100, limits)
        expected = 46.25
        assert abs(result - expected) < 0.001


class TestGetCoordFromLatLong:
    """Test get_coord_from_lat_long function."""

    def test_valid_coordinates(self):
        """Test conversion of valid lat/long to coordinates."""
        limits = ["005 48 W", "10 E", "51 30 N", "41 N"]
        result = get_coord_from_lat_long(48.8566, 2.3522, 100, 100, limits)
        assert result is not None
        x, y = result
        assert 0 < x < 100
        assert 0 < y < 100

    def test_out_of_bounds_west(self):
        """Test coordinates west of bounds."""
        limits = ["005 48 W", "10 E", "51 30 N", "41 N"]
        result = get_coord_from_lat_long(48.8566, -10.0, 100, 100, limits)
        assert result is None

    def test_out_of_bounds_east(self):
        """Test coordinates east of bounds."""
        limits = ["005 48 W", "10 E", "51 30 N", "41 N"]
        result = get_coord_from_lat_long(48.8566, 15.0, 100, 100, limits)
        assert result is None

    def test_out_of_bounds_north(self):
        """Test coordinates north of bounds."""
        limits = ["005 48 W", "10 E", "51 30 N", "41 N"]
        result = get_coord_from_lat_long(55.0, 2.3522, 100, 100, limits)
        assert result is None

    def test_out_of_bounds_south(self):
        """Test coordinates south of bounds."""
        limits = ["005 48 W", "10 E", "51 30 N", "41 N"]
        result = get_coord_from_lat_long(35.0, 2.3522, 100, 100, limits)
        assert result is None

    def test_edge_coordinates(self):
        """Test coordinates at the very edge (should return None)."""
        limits = ["005 48 W", "10 E", "51 30 N", "41 N"]
        # At west edge
        result = get_coord_from_lat_long(48.8566, -5.8, 100, 100, limits)
        assert result is None
        # At east edge
        result = get_coord_from_lat_long(48.8566, 10.0, 100, 100, limits)
        assert result is None
        # At north edge
        result = get_coord_from_lat_long(51.5, 2.3522, 100, 100, limits)
        assert result is None
        # At south edge
        result = get_coord_from_lat_long(41.0, 2.3522, 100, 100, limits)
        assert result is None


@patch("src.IOHandler.map_representation.cv")
@patch("src.IOHandler.map_representation.logger")
class TestHandleMouseMove:
    """Test handle_mouse_move function."""

    def test_handle_mouse_move_with_params(self, mock_logger, mock_cv):
        """Test mouse move handler with valid params."""
        params = {
            "image": np.zeros((100, 100, 3), dtype=np.uint8),
            "limits": ["005 48 W", "10 E", "51 30 N", "41 N"],
            "win_name": "test_window",
        }
        handle_mouse_move(1, 50, 50, 0, params)
        mock_cv.putText.assert_called_once()
        mock_cv.imshow.assert_called_once()

    def test_handle_mouse_move_no_params(self, mock_logger, mock_cv):
        """Test mouse move handler with None params."""
        handle_mouse_move(1, 50, 50, 0, None)
        mock_cv.putText.assert_not_called()
        mock_cv.imshow.assert_not_called()


@patch("src.IOHandler.map_representation.cv")
@patch("src.IOHandler.map_representation.logger")
class TestAddCitiesToImage:
    """Test add_cities_to_image function."""

    def test_toggle_cities_off(self, mock_logger, mock_cv):
        """Test toggling cities off (when they are currently shown)."""
        params = {
            "toggle_cities": False,  # Cities not shown, so pressing 'c' should reset to init_map
            "win_name": "test_window",
            "image": np.zeros((100, 100, 3), dtype=np.uint8),
            "init_map": np.ones((100, 100, 3), dtype=np.uint8),
        }
        add_cities_to_image(params)
        mock_cv.imshow.assert_called_once()
        assert params["toggle_cities"] is True
        # Image should be reset to init_map
        np.testing.assert_array_equal(params["image"], params["init_map"])

    def test_add_cities_with_valid_coords(self, mock_logger, mock_cv):
        """Test adding cities with valid coordinates."""
        cities = [
            {"title": "Paris", "lat_long": [48.8566, 2.3522]},
            {"title": "Lyon", "lat_long": [45.7640, 4.8357]},
        ]
        params = {
            "toggle_cities": True,  # Cities shown, so pressing 'c' should add cities
            "win_name": "test_window",
            "image": np.zeros((100, 100, 3), dtype=np.uint8),
            "cities": cities,
            "limits": ["005 48 W", "10 E", "51 30 N", "41 N"],
        }
        add_cities_to_image(params)
        # Should call putText for each city
        assert mock_cv.putText.call_count == 2
        mock_cv.imshow.assert_called()
        assert params["toggle_cities"] is False

    def test_add_cities_with_invalid_coords(self, mock_logger, mock_cv):
        """Test adding cities with invalid coordinates."""
        cities = [
            {"title": "Invalid City", "lat_long": [55.0, 2.3522]},  # North of bounds
        ]
        params = {
            "toggle_cities": True,  # Cities shown
            "win_name": "test_window",
            "image": np.zeros((100, 100, 3), dtype=np.uint8),
            "cities": cities,
            "limits": ["005 48 W", "10 E", "51 30 N", "41 N"],
        }
        add_cities_to_image(params)
        # Should not call putText or imshow for invalid city
        mock_cv.putText.assert_not_called()
        mock_cv.imshow.assert_not_called()
        assert params["toggle_cities"] is False
        # Should log warning
        mock_logger.warning.assert_called_once()
        # Should have deleted the useless city
        assert len(params["cities"]) == 0
        mock_logger.info.assert_called_once_with("Deleted 1 cities")
