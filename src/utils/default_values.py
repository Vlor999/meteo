"""Create the default values from the bouding boxes coordinates."""

from src.params import LIMIT_EST, LIMIT_NORTH, LIMIT_SOUTH, LIMIT_WEST


def get_default_coordinates_from_limits(
    limits: list[str],
) -> tuple[float, float, float, float]:
    """Return the current coordinates from the limits."""
    if len(limits) == 4:
        coordinates = [float(lim.split(" ")[0]) for lim in limits]
        return (coordinates[0], coordinates[1], coordinates[2], coordinates[3])
    raise ValueError(
        "The length of the limit list is not 4 which means we do have more than (NORTH, SOUTH, WEST, EST)"
    )


def get_coordinates() -> tuple[float, float, float, float]:
    """Use the cooridnates defined into the python file."""
    return get_default_coordinates_from_limits(
        [LIMIT_NORTH, LIMIT_SOUTH, LIMIT_WEST, LIMIT_EST]
    )


if __name__ == "__main__":
    print(get_coordinates())
