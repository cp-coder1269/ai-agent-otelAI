import logging
from typing import List, Optional, TypedDict

import pandas as pd

# NOTE: agents library provides Agent, Runner, ModelSettings, function_tool
from agents import function_tool


# Define strict types for function_tool compatibility
class SheetConfig(TypedDict, total=False):
    start: int
    end: Optional[int]=None

class ReadSheetResult(TypedDict):
    sheet: str
    header: List[str]
    columns: List[str]
    rows: List[dict]

@function_tool
def read_sheet_with_custom_header(
    filepath: str,
    sheet: str,
    config: Optional[SheetConfig] = None
) -> ReadSheetResult:
    """
    Reads an Excel sheet with a custom header row, returning both raw and sanitized data.

    Args:
        filepath (str): The file path to the Excel workbook.
        sheet (str): The name of the sheet to read.
        config (dict, optional): Configuration dict with the following keys:
            - 'start' (int, optional): Row index to use as the column header. Defaults to 0.
            - 'end' (int, optional): Row index to stop reading (inclusive). By default, reads until the last row.

    Returns:
        dict: A dictionary containing:
            - 'sheet': Name of the sheet.
            - 'header': The original header row, as a list.
            - 'columns': Sanitized column names.
            - 'rows': List of records, each as a dictionary.

    Raises:
        ValueError: If the `start` index is out of range for the dataframe.
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
    # Sanitise
    sanitised_cols = [
        str(col).strip().replace("\n", " ").replace("\r", "").replace("\t", " ").lower()
        for col in data_df.columns
    ]
    data_df.columns = sanitised_cols

    return {
        "sheet": sheet,
        "header": header_row,
        "columns": sanitised_cols,
        "rows": data_df.to_dict(orient="records"),
    }
