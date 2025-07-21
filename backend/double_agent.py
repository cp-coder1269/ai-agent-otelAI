import asyncio
import logging
import re
from typing import List, Optional, TypedDict


import pandas as pd
from dotenv import load_dotenv

# NOTE: agents library provides Agent, Runner, ModelSettings, function_tool
from agents import Agent, Runner, function_tool  # type: ignore

# ─────────────────────────────────────────────────────────────────────────────
# Setup & logging
# ─────────────────────────────────────────────────────────────────────────────
load_dotenv()
logging.basicConfig(filename="function_calls.log", level=logging.INFO)

# Define strict types for function_tool compatibility
class SheetConfig(TypedDict, total=False):
    start: int
    end: Optional[int]=None

class ReadSheetResult(TypedDict):
    sheet: str
    columns: List[str]
    rows: List[dict]

def _read_sheet_with_custom_header(
    filepath: str,
    sheet: str,
    config: Optional[SheetConfig] = None,
    columns: Optional[List[str]] = None
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

        missing = [col for col in requested_normalized if col and col not in actual_header_map]
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

@function_tool
def read_sheet_with_custom_header(
    filepath: str,
    sheet: str,
    config: Optional[SheetConfig] = None,
    columns: Optional[List[str]] = None
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

        missing = [col for col in requested_normalized if col and col not in actual_header_map]
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


def _extract_code_from_response(response: str) -> str:
    """Pull the first ```python ... ``` (or plain ```) block from a string."""
    match = re.search(r"```(?:python)?[ \t]*\r?\n([\s\S]*?)```", response)
    return match.group(1).strip() if match else response.strip()


@function_tool
def execute_function_safely_using_exec(
    func_string: str,
    function_name: str
) -> str:
    """
    Executes a given Python function defined in a code block in the LLM's response.

    Parameters:
    - response (str): Code block containing the function definition.
    - function_name (str): The name of the function to call (must be defined in the response).

    Returns:
    - str: The result of the function execution.
    """
    print(f"[DEBUG] execute_function_safely_using_exec called with function_name={function_name}")
    print(f"[DEBUG] Function string:\n{func_string}")
    safe_globals = {
        "__builtins__": {
        "__import__": __import__,
        "len": len,
        "range": range,
        "str": str,
        "int": int,
        "float": float,
        "list": list,
        "dict": dict,
        "tuple": tuple,
        "set": set,
        "print": print,
        "sum": sum,
        "max": max,
        "min": min,
        "abs": abs,
        "round": round,
        "enumerate": enumerate,
        "zip": zip,
        "sorted": sorted,
        "any": any,
        "all": all,
    },
        "pd": pd,
        "re": re,
        "datetime": __import__("datetime"),
        "date": __import__("datetime").date,
        "datetime": __import__("datetime").datetime,
        "timedelta": __import__("datetime").timedelta,
        "read_sheet_with_custom_header": _read_sheet_with_custom_header
    }
    local_vars: dict = {}

    code = _extract_code_from_response(func_string)
    exec(code, safe_globals, local_vars)

    if function_name not in local_vars:
        raise NameError(f"Function '{function_name}' not found")

    result = local_vars[function_name]()
    print(f"[DEBUG] Result of {function_name}: {result}")
    return result


# ─────────────────────────────────────────────────────────────────────────────
# Agent instructions (full)
# ─────────────────────────────────────────────────────────────────────────────
instructions = """
You are a data analysis agent with access to structured Excel files and a tool named `read_sheet_with_custom_header`
. 
Your job is to answer user questions by identifying the correct Excel file, sheet, and column, using the file's sche
ma and the tool provided.

You must:

1. Parse the user's question to identify:
   - The file being referred to (`oc_onboarding_file` or `alex_ideas_file`).
   - The correct sheet name (e.g., "Budget", "Segment Descriptions").
   - The relevant column(s) mentioned (e.g., "Jan Rooms Revenue", "Occupancy Date").

2. Use the `read_sheet_with_custom_header` tool to inspect a sample of the sheet:
   - `filepath`: path of the file
   - `sheet`: sheet name
   - `config`: dictionary with `"start"` row and `"end"` as `start + 2` (this gives 2 rows of sample data only)
   - `columns`: provide a list of columns which are required for answering the question

   This is for schema detection and type hinting only. Do not analyze this partial data directly.

3. Write a Python function for final analysis
   This function reads the full data using `read_sheet_with_custom_header` and performs required computation Follow these:
   - Inside the function:
     - Use exact `filepath`, `sheet`, and `config` (no modification) from the provided `sheet_configs` in the schema.
     - Call: `read_sheet_with_custom_header(filepath, sheet, config)`
     - Normalize columns: lowercase, strip whitespace and newline characters
     - Perform required computations: `sum`, `average`, `filter`, `group`, `compare`, etc.
     - Return the final result of computaion. Always return sifficient data to make your conclusion based on data/facts

4. Execute this Python function using the tool `execute_function_safely_using_exec` and return the output to the user.
- Call the function directly as: read_sheet_with_custom_header(filepath, sheet, config)
- Do NOT use functions.read_sheet_with_custom_header() - there is no functions module

5. Always explain which file, sheet, and columns you used

6. Extra Info (if needed):
    Room capacity per night is 103 (from context, not in Excel).
    So:
    Jan has 31 days → total available rooms = 31 * 103 = 3193
    Use this only if your logic requires total room availability.


7. Allowed operations in the execution environment
   - **Built-in functions**: `len`, `range`, `str`, `int`, `float`, `list`, `dict`, `print`
   - **Libraries**: `pandas` as `pd`, `re`, `datetime` (`datetime`, `date`, `timedelta`)
   - **Reading data**: Only via `read_sheet_with_custom_header(filepath, sheet, config)`
   - **Not allowed**:
     - File I/O (no `open`, `write`, etc.)
     - Network calls or external APIs
     - Multiple function definitions — only one function per execution

8. IMPORTANT: When analyzing data for specific months/periods:
    1. Always convert date columns to datetime: pd.to_datetime(df['occupancy date'])
    2. Filter data for the specific period: df[df['occupancy date'].dt.month == target_month]
    3. Only perform calculations on the filtered data, not the entire dataset
    4. For monthly comparisons, ensure you're comparing like periods (same month/year)

You must only rely on the schema provided below for determining which columns exist in which sheets.
Here is the complete schema of available files and their sheets/columns:

{
    "oc_onboarding_file": {
        "file_path": "data/OCOnboardingInformation.xlsx",
        "oc_onboarding_file_structure": {
            "Rooms per category": {
                "Room Type": "str",
                "Room Type per Ideas\\n": "str",
                "Room Class per Ideas": "str",
                "Number of Rooms": "int",
                "Zip & Link": "float"
            },
            "Segment Descriptions": {
                "Segment Name": "str",
                "Definition": "str",
                "Desc": "str",
                "Macro Group": "str",
                "Owner": "str",
                "Lead Time": "str"
            },
            "OTA Commission Rates": {
                "Segment Name": "str",
                "Definition": "str",
                "Desc": "str",
                "Macro Group": "str",
                "Commission": "str"
            },
            "Budget": {
                "Group or Transient": "str",
                "Segment": "str",
                "Macro Group": "str",
                "Definition": "str",
                "Jan Rooms": "str",
                "Jan Rooms Revenue": "float",
                "Jan ADR": "float",
                "Feb Rooms": "str",
                "Feb Rooms Revenue": "float",
                "Feb ADR": "float",
                "March Rooms": "str",
                "March Rooms Revenue": "float",
                "March ADR": "float",
                "April Rooms": "str",
                "April Rooms Revenue": "float",
                "April ADR": "float",
                "May Rooms": "str",
                "May Rooms Revenue": "float",
                "May ADR": "float",
                "June Rooms": "str",
                "June Rooms Revenue": "float",
                "June ADR": "float",
                "July Rooms": "str",
                "July Rooms Revenue": "float",
                "July ADR": "float",
                "Aug Rooms": "str",
                "Aug Rooms Revenue": "float",
                "Aug ADR ": "float",
                "Sept Rooms": "str",
                "Sept Rooms Revenue": "float",
                "Sept ADR ": "float",
                "Oct Rooms": "str",
                "Oct Rooms Revenue": "float",
                "Oct ADR ": "float",
                "Nov Rooms": "str",
                "Nov Rooms Revenue": "float",
                "Nov ADR ": "float",
                "Dec Rooms": "str",
                "Dec Rooms Revenue": "float",
                "Dec ADR ": "float",
                "Total Rooms": "float",
                "Total Rooms Revenue": "float",
                "Total ADR": "float"
            },
            "PY Event Diary": {
                "Special Event Name": "str",
                "Description": "str",
                "Pre-Event days": "int",
                "Day of Week": "str",
                "Start Date": "datetime",
                "Day of Week.1": "str",
                "End Date": "str",
                "Post-event days": "int",
                "Information Only": "str",
                "Category": "str",
                "Created By": "str",
                "Created On": "str",
                "Updated By": "str",
                "Updated On": "str"
            }
        },
        "sheet_configs": {
            "Rooms per category": { "start": 3, "end": 8 },
            "Segment Descriptions": { "start": 1 },
            "OTA Commission Rates": { "start": 1 },
            "Budget": { "start": 2, "end": 18 },
            "PY Event Diary": { "start": 1 }
        }
    },
    "alex_ideas_file": {
        "file_path": "data/TheAlexIdeas27_June_2025.xlsx",
        "alex_ideas_structure": {
            "Property": {
                "Property Name": "str",
                "Day of Week": "str",
                "Occupancy Date": "datetime",
                "Special Event This Year": "str",
                "Physical Capacity This Year": "float",
                "Occupancy On Books This Year": "float",
                "Occupancy On Books STLY": "float",
                "Rooms Sold - Group This Year": "float",
                "Rooms Sold - Group STLY": "float",
                "Rooms Sold - Transient This Year": "float",
                "Rooms Sold - Transient STLY": "float",
                "Booked Room Revenue This Year": "float",
                "Booked Room Revenue STLY": "float",
                "Forecasted Room Revenue This Year": "float",
                "DLY1": "float"
            },
            "Room Type": {
                "Property Name": "str",
                "Day of Week": "str",
                "Occupancy Date": "datetime",
                "Room Type": "str",
                "Room Class": "str",
                "DLY1 This Year": "float"
            },
            "Business View": {
                "Property Name": "str",
                "Day of Week": "str",
                "Occupancy Date": "datetime",
                "Business View": "str",
                "Occupancy On Books This Year": "int",
                "Occupancy On Books STLY": "int",
                "Booked Room Revenue This Year": "float",
                "Booked Room Revenue STLY": "float",
                "Forecasted Room Revenue This Year": "float"
            },
            "Report Criteria": {
                "Property Name": "str",
                "Start Date": "datetime",
                "End Date": "datetime",
                "Currency": "str",
                "Inventory Group": "str",
                "Created By": "str",
                "Generated On": "str",
                "Account ID": "str"
            }
        },
        "sheet_configs": {
            "Property": { "start": 0 },
            "Room Type": { "start": 0 },
            "Business View": { "start": 0 },
            "Report Criteria": { "start": 2 }
        }
    }
}
"""


async def data_analyser():
    # Create our specialized weather assistant
    data_analyser_assistant = Agent(
        name="Hotel Data Analyser",
        instructions=instructions,
        # model="gpt-4o-mini",
        tools=[read_sheet_with_custom_header, execute_function_safely_using_exec]
    )

    question = "What is the on-the-books (OTB) revenue for August compared to the same time last year (STLY)?"
    result = await Runner.run(data_analyser_assistant, question)
    print(result.final_output)

if __name__ == "__main__":
    asyncio.run(data_analyser())
    # print(read_sheet_with_custom_header(filepath="data/TheAlexIdeas27_June_2025.xlsx", sheet="Room Type", config={ "start": 0, "end": 5 } ) )