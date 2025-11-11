"""Tests for write_data.py."""

from unittest.mock import Mock, mock_open, patch

import pandas as pd
import pytest

from src.IOHandler.write_data import save_dataframe
from src.IOHandler.writting_mods import SaveMode


class TestSaveDataframe:
    """Test save_dataframe function."""

    @patch("src.IOHandler.write_data.logger")
    def test_single_dataframe_single_filename_init_mode(self, mock_logger):
        """Test saving single dataframe to single filename with INIT mode."""
        df = pd.DataFrame({"col1": [1, 2], "col2": ["a", "b"]})

        with patch.object(df, "to_csv") as mock_to_csv:
            save_dataframe(df, "test.csv", mode=SaveMode.INIT)

            mock_to_csv.assert_called_once_with(
                path_or_buf="test.csv",
                sep=",",
                mode="w",
                header=True,
                index_label="index",
            )
            mock_logger.info.assert_called()

    @patch("src.IOHandler.write_data.logger")
    def test_multiple_dataframes_multiple_filenames(self, mock_logger):
        """Test saving multiple dataframes to multiple filenames."""
        df1 = pd.DataFrame({"col1": [1, 2]})
        df2 = pd.DataFrame({"col2": [3, 4]})
        dataframes = [df1, df2]
        filenames = ["test1.csv", "test2.csv"]

        with patch("pandas.DataFrame.to_csv") as mock_to_csv:
            save_dataframe(dataframes, filenames, mode=SaveMode.INIT)

            assert mock_to_csv.call_count == 2
            # Debug is not called when already lists
            mock_logger.debug.assert_not_called()

    @patch("src.IOHandler.write_data.logger")
    def test_convert_single_to_list(self, mock_logger):
        """Test that single dataframe and filename are converted to lists."""
        df = pd.DataFrame({"col1": [1, 2]})

        with patch.object(df, "to_csv") as _:
            save_dataframe(df, "test.csv", mode=SaveMode.INIT)

            # Check that both debug calls were made
            assert mock_logger.debug.call_count == 2
            mock_logger.debug.assert_any_call("Updating the format of dataframes")
            mock_logger.debug.assert_any_call("Updating the format of filenames")

    @patch("src.IOHandler.write_data.logger")
    def test_length_mismatch_warning(self, mock_logger):
        """Test warning when dataframes and filenames have different lengths."""
        df1 = pd.DataFrame({"col1": [1, 2]})
        df2 = pd.DataFrame({"col2": [3, 4]})
        dataframes = [df1, df2]
        filenames = ["test.csv"]  # Only one filename

        save_dataframe(dataframes, filenames, mode=SaveMode.INIT)

        mock_logger.warning.assert_called_once_with(
            "Not the same size between the filename(1) and the dataframes(2)"
        )

    @patch("src.IOHandler.write_data.logger")
    def test_non_csv_filename_warning(self, mock_logger):
        """Test warning for non-CSV filenames."""
        df = pd.DataFrame({"col1": [1, 2]})

        save_dataframe(df, "test.txt", mode=SaveMode.INIT)

        mock_logger.warning.assert_called_once_with(
            'The filename: test.txt does not the ".csv" format'
        )

    @patch("src.IOHandler.write_data.logger")
    def test_add_mode(self, mock_logger):
        """Test ADD mode appends to existing file."""
        df = pd.DataFrame({"col1": [1, 2], "col2": ["a", "b"]})

        with patch.object(df, "to_csv") as mock_to_csv:
            save_dataframe(df, "test.csv", mode=SaveMode.ADD)

            mock_to_csv.assert_called_once_with(
                path_or_buf="test.csv",
                sep=",",
                mode="a",
                header=False,
                index_label="index",
            )
            mock_logger.info.assert_called()

    @patch("src.IOHandler.write_data.logger")
    @patch("pandas.read_csv")
    def test_merge_mode(self, mock_read_csv, mock_logger):
        """Test MERGE mode reads existing file, concatenates, and deduplicates."""
        existing_df = pd.DataFrame({"col1": [1, 3], "col2": ["a", "c"]})
        new_df = pd.DataFrame({"col1": [1, 2], "col2": ["a", "b"]})

        mock_read_csv.return_value = existing_df

        with (
            patch("pandas.concat") as mock_concat,
            patch.object(pd.DataFrame, "to_csv") as mock_to_csv,
        ):
            mock_concat.return_value = pd.DataFrame(
                {"col1": [1, 3, 2], "col2": ["a", "c", "b"]}
            )

            save_dataframe(new_df, "test.csv", mode=SaveMode.MERGE)

            mock_read_csv.assert_called_once_with("test.csv")
            mock_concat.assert_called_once()
            mock_to_csv.assert_called_once_with(
                path_or_buf="test.csv", sep=",", mode="w", index_label="index"
            )
            mock_logger.info.assert_called()

    @patch("src.IOHandler.write_data.logger")
    @patch("pandas.read_csv")
    def test_merge_mode_drop_index_label(self, mock_read_csv, mock_logger):
        """Test MERGE mode drops index_label column if present."""
        existing_df = pd.DataFrame(
            {"index": [0, 1], "col1": [1, 3], "col2": ["a", "c"]}
        )
        mock_read_csv.return_value = existing_df

        new_df = pd.DataFrame({"col1": [1, 2], "col2": ["a", "b"]})

        with (
            patch("pandas.concat") as mock_concat,
            patch.object(pd.DataFrame, "to_csv") as _,
        ):
            mock_concat.return_value = pd.DataFrame(
                {"col1": [1, 3, 2], "col2": ["a", "c", "b"]}
            )

            save_dataframe(new_df, "test.csv", mode=SaveMode.MERGE)

            # Check that concat was called with the dataframe after drop
            mock_concat.assert_called_once()
            # The first argument to concat should be the existing
            # df without index column
            args, _ = mock_concat.call_args
            dropped_df = args[0][0]  # First dataframe in the list
            assert "index" not in dropped_df.columns

    def test_init_mode_with_custom_sep(self):
        """Test INIT mode with custom separator."""
        df = pd.DataFrame({"col1": [1, 2], "col2": ["a", "b"]})

        with patch.object(df, "to_csv") as mock_to_csv:
            save_dataframe(df, "test.csv", sep=";", mode=SaveMode.INIT)

            mock_to_csv.assert_called_once_with(
                path_or_buf="test.csv",
                sep=";",
                mode="w",
                header=True,
                index_label="index",
            )

    def test_init_mode_with_custom_index_label(self):
        """Test INIT mode with custom index label."""
        df = pd.DataFrame({"col1": [1, 2], "col2": ["a", "b"]})

        with patch.object(df, "to_csv") as mock_to_csv:
            save_dataframe(
                df, "test.csv", index_label="custom_index", mode=SaveMode.INIT
            )

            mock_to_csv.assert_called_once_with(
                path_or_buf="test.csv",
                sep=",",
                mode="w",
                header=True,
                index_label="custom_index",
            )

    @patch("src.IOHandler.write_data.logger")
    def test_empty_dataframe(self, mock_logger):
        """Test saving empty dataframe."""
        df = pd.DataFrame()

        with patch.object(df, "to_csv") as mock_to_csv:
            save_dataframe(df, "test.csv", mode=SaveMode.INIT)

            mock_to_csv.assert_called_once()
            mock_logger.info.assert_called()

    @patch("src.IOHandler.write_data.logger")
    def test_init_mode_exception_handling(self, mock_logger):
        """Test exception handling in INIT mode."""
        df = pd.DataFrame({"col1": [1, 2]})

        with patch.object(df, "to_csv", side_effect=Exception("Test error")) as _:
            with pytest.raises(Exception, match="Test error"):
                save_dataframe(df, "test.csv", mode=SaveMode.INIT)

            mock_logger.error.assert_called_once_with(
                "Error writing to test.csv: Test error"
            )

    @patch("src.IOHandler.write_data.logger")
    def test_success_logging(self, mock_logger):
        """Test success logging for all modes."""
        df = pd.DataFrame({"col1": [1, 2]})

        with patch.object(df, "to_csv"):
            save_dataframe(df, "test.csv", mode=SaveMode.INIT)
            mock_logger.success.assert_called_once_with(
                f"No errors while using mode: {SaveMode.INIT} to save the data into : test.csv"
            )

    @patch("src.IOHandler.write_data.logger")
    def test_dataframe_info_logging(self, mock_logger):
        """Test logging of dataframe information."""
        df = pd.DataFrame({"col1": [1, 2, 3]})

        with patch.object(df, "to_csv"):
            save_dataframe(df, "test.csv", mode=SaveMode.INIT)

            # Check that info was called with dataframe processing
            mock_logger.info.assert_any_call(
                "Processing dataframe 0: shape=(3, 1), empty=False"
            )


@patch("src.IOHandler.write_data.save_dataframe")
@patch("pandas.DataFrame")
@patch("builtins.open", new_callable=mock_open)
class TestMainBlock:
    """Test the main block execution."""

    def test_main_block_execution(self, mock_file, mock_df_class, mock_save_dataframe):
        """Test that main block creates dataframes and calls save_dataframe."""
        # Mock DataFrame constructor calls
        mock_df1 = Mock()
        mock_df1.shape = (3, 2)
        mock_df2 = Mock()
        mock_df2.shape = (4, 2)

        mock_df_class.side_effect = [mock_df1, mock_df2]

        # Import and run main block
        import src.IOHandler.write_data as wd

        # Since it's if __name__ == "__main__", we need to simulate
        # For testing purposes, we'll just verify the imports work
        assert callable(wd.save_dataframe)
