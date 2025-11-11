"""File to help to save dataframe into csv files."""

import pandas as pd
from loguru import logger

from src.IOHandler.writting_mods import SaveMode


def save_dataframe(
    dataframes: list[pd.DataFrame] | pd.DataFrame,
    filenames: list[str] | str,
    sep: str = ",",
    mode: str = SaveMode.INIT,
    index_label: str = "index",
) -> None:
    """Main function that save dataframe to csv files by using the coherent mode."""
    if isinstance(dataframes, pd.DataFrame):
        dataframes = [dataframes]
        logger.debug("Updating the format of dataframes")
    if isinstance(filenames, str):
        filenames = [filenames]
        logger.debug("Updating the format of filenames")

    if len(dataframes) != len(filenames):
        logger.warning(
            f"Not the same size between the filename({len(filenames)}) and the dataframes({len(dataframes)})"
        )
        return

    for i, frame in enumerate(dataframes):
        filename = filenames[i]
        logger.info(
            f"Processing dataframe {i}: shape={frame.shape}, empty={frame.empty}"
        )
        if filename.endswith(".csv"):
            if mode == SaveMode.MERGE:
                logger.info(f"Starting to merge the data between input and {filename}")
                df = pd.DataFrame(pd.read_csv(filename))
                if index_label in df.columns:
                    df = df.drop(columns=index_label)
                updated_df = pd.concat([df, frame]).drop_duplicates(keep="last")
                updated_df.to_csv(
                    path_or_buf=filename, sep=sep, mode="w", index_label=index_label
                )
            elif mode == SaveMode.ADD:
                logger.info(f"Starting to add data to the current file: {filename}")
                frame.to_csv(
                    path_or_buf=filename,
                    sep=sep,
                    mode="a",
                    header=False,
                    index_label=index_label,
                )
            elif mode == SaveMode.INIT:
                logger.info(
                    f"Creating or overwrtting the data from the file: {filename}"
                )
                try:
                    logger.info(
                        f"About to write to {filename}, dataframe shape: {frame.shape}"
                    )
                    frame.to_csv(
                        path_or_buf=filename,
                        sep=sep,
                        mode="w",
                        header=True,
                        index_label=index_label,
                    )
                    logger.info(f"Successfully wrote to {filename}")
                except Exception as e:
                    logger.error(f"Error writing to {filename}: {e}")
                    raise
        else:
            logger.warning(f'The filename: {filename} does not the ".csv" format')
            continue
        logger.success(
            f"No errors while using mode: {mode} to save the data into : {filename}"
        )


if __name__ == "__main__":
    df = pd.DataFrame({"sizes": [10, 10, 20], "origines": ["paris", "london", "pekin"]})
    save_dataframe(df, "data/temp.csv")
    df = pd.DataFrame(
        {
            "sizes": [10, 10, 20, 200],
            "origines": ["paris", "london", "pekin", "hong kong"],
        }
    )
    save_dataframe(df, "data/temp.csv", mode="merge")
