import pandas as pd


import pandas as pd
from typing import Optional, List

from backend.helpers.sheet_configs import THE_ALEX_SHEET_CONFIG

def read_sheet_with_custom_header(
    filepath: str,
    sheet: str,
    sheet_configs: dict,
    columns: Optional[List[str]] = None
) -> dict:
    print(f"read_sheet_with_custom_header → filepath='{filepath}', sheet='{sheet}', sheet_configs={sheet_configs}, columns={columns}")
    config = sheet_configs.get(sheet, {})
    start_row = config.get("start", 0)
    end_row = config.get("end")

    # Read entire sheet without header
    df = pd.read_excel(filepath, sheet_name=sheet, header=None, engine="openpyxl")

    # Get header row as a list
    header_row = df.iloc[start_row].tolist()

    # Determine data range
    if end_row is not None:
        data_df = df.iloc[start_row + 1:end_row + 1].copy()
    else:
        data_df = df.iloc[start_row + 1:].copy()

    # Assign header
    data_df.columns = header_row

    # Sanitize headers
    sanitized_columns = [
        str(col).strip().replace('\n', ' ').replace('\r', '').replace('\t', ' ').lower()
        for col in data_df.columns
    ]
    data_df.columns = sanitized_columns

    # If columns filter is provided, normalize and filter
    if columns:
        # Normalize input column names to match sanitized ones
        normalized_columns = [
            str(col).strip().replace('\n', ' ').replace('\r', '').replace('\t', ' ').lower()
            for col in columns
        ]

        # Check which columns exist
        existing_columns = [col for col in normalized_columns if col in data_df.columns]

        if not existing_columns:
            raise ValueError(f"None of the requested columns {columns} were found in the sheet '{sheet}'.")

        data_df = data_df[existing_columns]
        header_row = [col for col in header_row if str(col).strip().lower() in existing_columns]

    return {
        "header": header_row,
        "data": data_df
    }



def sum_jan_rooms(df):
    """
    Returns the sum of all values in the 'Jan Rooms' column of the given DataFrame.
    Handles missing or non-numeric values gracefully.
    """
    column = str("Jan Rooms").lower()
    # Ensure the column exists
    if column not in df.columns:
        raise ValueError("Column 'Jan Rooms' not found in DataFrame.")
    # Convert to numeric, coerce errors to NaN, then sum (ignoring NaN)
    return df[column].apply(pd.to_numeric, errors="coerce").sum()


if __name__ == "__main__":
    file_path = 'data/TheAlexIdeas27_June_2025.xlsx'
    data = read_sheet_with_custom_header(filepath=file_path, sheet="Report Criteria", sheet_configs=THE_ALEX_SHEET_CONFIG, columns=["Property Name", "start date"])
    # print(data.get("header"))
    print(data.get("data"))
    # df = data.get("data")
    # total_jan_rooms = sum_jan_rooms(df)
    # print("Sum of Jan Rooms:", total_jan_rooms)