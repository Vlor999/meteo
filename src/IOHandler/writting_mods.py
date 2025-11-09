"""Enum that represent the saving dataframe mode."""

from enum import Enum


class SaveMode(str, Enum):
    """Enum that represent the saving dataframe mode."""

    INIT = "init"
    ADD = "add"
    MERGE = "merge"
