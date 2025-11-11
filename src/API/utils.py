"""Utils file that give store the functions that are used all over the API dir."""

import os
from collections import deque
from pathlib import Path

import pandas as pd
from loguru import logger

from src.params import BBOX_DIR, DATA_DIR
from src.utils.default_values import get_coordinates


def write_bbox(
    bbox: deque[tuple[float, float, float, float]],
    file: str = f"{DATA_DIR}/{BBOX_DIR}/bbox.csv",
) -> None:
    """Write bounding box data to a CSV file.

    Args:
        bbox (deque): A deque containing tuples of bounding box coordinates.
            Each tuple should contain (north, south, west, east) coordinates.
        file (str, optional): Path to the output CSV file.
            Defaults to f"{DATA_DIR}/{BBOX_DIR}/bbox.csv".

    Returns:
        None

    Example:
        >>> bbox_data = deque([(45.0, 44.0, 2.0, 3.0), (46.0, 45.0, 3.0, 4.0)])
        >>> write_bbox(bbox_data, "output/bbox.csv")
    """
    logger.debug(f"🏁 Starting to write bbox data ({len(bbox)}) into the file: {file}")
    df = pd.DataFrame(list(bbox))
    dir_file = file.split("/")[:-1]
    os.makedirs("/".join(dir_file), exist_ok=True)
    with open(file, "w") as f:
        df.to_csv(f, header=["north", "south", "west", "est"], index=False)
    logger.success(f"File({file}) properly written with the bbox datas")


def read_data_bbox(
    file: str = f"{DATA_DIR}/{BBOX_DIR}/bbox.csv",
) -> deque[tuple[float, float, float, float]]:
    """Read bounding box data from a CSV file.

    Args:
        file (str, optional): Path to the input CSV file containing bbox data.
            Defaults to f"{DATA_DIR}/{BBOX_DIR}/bbox.csv".

    Returns:
        deque: A deque containing tuples of bounding box coordinates.
            Each tuple contains (north, south, west, east) coordinates.

    Example:
        >>> bbox_data = read_data_bbox("input/bbox.csv")
        >>> print(bbox_data[0])
        (45.0, 44.0, 2.0, 3.0)
    """
    logger.debug(f"🏁 Starting to read the data from the file({file})")
    if not Path(file).exists():
        logger.warning("The file does not exists")
        return deque()
    df = pd.read_csv(file)
    rows = df.to_numpy().tolist()
    logger.success(f"Succesfully red the file({file}) and found {len(rows)} bbox")
    return deque([tuple(row) for row in rows])


def get_sized_bboxes(
    file: str = f"{DATA_DIR}/{BBOX_DIR}/bbox.csv",
    default_bbox: tuple[float, float, float, float] | None = None,
) -> deque[tuple[float, float, float, float]]:
    """Get the sized boxes that need to be process.

    Args:
        file (str, optional): Path to the input CSV file containing bbox data.
            Defaults to f"{DATA_DIR}/{BBOX_DIR}/bbox.csv".
        default_bbox (tuple[float, float, float, float]): The default bbox to start

    Returns:
        deque: A deque containing tuples of bounding box coordinates.
            Each tuple contains (north, south, west, east) coordinates.

    Example:
        >>> bbox_data = read_data_bbox("input/bbox.csv")
        >>> print(bbox_data[0])
        (45.0, 44.0, 2.0, 3.0)

    """
    bbox = read_data_bbox(file)
    default_bbox_deque = deque(
        [default_bbox] if default_bbox is not None else [get_coordinates()]
    )
    return bbox if len(bbox) != 0 else default_bbox_deque


if __name__ == "__main__":
    write_bbox(deque([(1, 1, 2, 3)]))
