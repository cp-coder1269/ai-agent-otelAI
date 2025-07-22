import logging
from typing import List, Optional, TypedDict


import pandas as pd
from dotenv import load_dotenv


# Define strict types for function_tool compatibility
class SheetConfig(TypedDict, total=False):
    start: int
    end: Optional[int] = None


class ReadSheetResult(TypedDict):
    sheet: str
    columns: List[str]
    rows: List[dict]


def _read_sheet_with_custom_header(
    filepath: str,
    sheet: str,
    config: Optional[SheetConfig] = None,
    columns: Optional[List[str]] = None,
) -> ReadSheetResult:
    """
    Reads an Excel sheet using a custom header row.

    Args:
    - filepath: Path to the Excel file.
    - sheet: Sheet name to read.
    - config: Optional dict with 'start' (required) and 'end' (optional) row indices for reading.
    - columns: Optional list of column names to select (case-insensitive).

    Returns:
    - A dict with:
    - 'sheet': Sheet name.
    - 'columns': Sanitized lowercase column names.
    - 'rows': List of row dicts with selected or all columns.
    """
    logging.info(
        f"read_sheet_with_custom_header(filepath={filepath}, "
        f"sheet={sheet}, config={config})"
    )
    # Set robust defaults
    config = config or {}
    start_row = config.get("start", 0)
    end_row = config.get("end", None)

    df = pd.read_excel(filepath, sheet_name=sheet, header=None, engine="openpyxl")
    header_row = df.iloc[start_row].tolist()

    # Slice the data rows
    data_df = (
        df.iloc[start_row + 1 : end_row + 1].copy()
        if end_row is not None
        else df.iloc[start_row + 1 :].copy()
    )
    # Apply original headers
    data_df.columns = header_row
    # print("data_df.columns: ", data_df.columns)
    if columns:

        def normalize(col: str) -> str:
            return str(col).strip().lower()

        actual_header_map = {normalize(col): col for col in data_df.columns}
        requested_normalized = [normalize(col) for col in columns]

        missing = [
            col for col in requested_normalized if col and col not in actual_header_map
        ]
        if missing:
            raise ValueError(
                f"Some requested columns were not found in the header: {missing}\n"
                f"Available columns: {list(actual_header_map.keys())}"
            )

        selected_cols = [actual_header_map[col] for col in requested_normalized]
        data_df = data_df[selected_cols]
        # print("selected_cols: ", selected_cols)

    # print("data_df: ", data_df)
    # print("data_df.columns: ", data_df.columns)
    # Sanitise
    sanitised_cols = [
        str(col).strip().replace("\n", " ").replace("\r", "").replace("\t", " ").lower()
        for col in data_df.columns
    ]
    data_df.columns = sanitised_cols

    return {
        "sheet": sheet,
        "columns": sanitised_cols,
        "rows": data_df.to_dict(orient="records"),
    }
