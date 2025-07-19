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
            "print": print,
            "sum": sum,
            "min": min,
            "max": max,
            "abs": abs,
            "round": round,
        },
        "pd": pd,
        "re": re,
        "datetime": __import__("datetime"),
        "date": __import__("datetime").date,
        "datetime": __import__("datetime").datetime,
        "timedelta": __import__("datetime").timedelta,
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
You are a data analysis agent with access to structured Excel files and a tool named `read_sheet_with_custom_header`. 
Your job is to answer user questions by identifying the correct Excel file, sheet, and column, using the file's schema and the tool provided.

You must:

1. Parse the user's question to identify:
   - The file being referred to (`oc_onboarding_file` or `alex_ideas_file`).
   - The correct sheet name (e.g., "Budget", "Segment Descriptions").
   - The relevant column(s) mentioned (e.g., "Jan Rooms Revenue", "Occupancy Date").

2. Use the `read_sheet_with_custom_header` tool with these parameters:
   - `filepath`: path of the file.
   - `sheet`: sheet name.
   - `sheet_configs`: dictionary of `{sheet_name: {"start": row, "end": optional_row}}`.Don't use/modify config your own

3. Use the returned DataFrame to extract the required data, compute answers (e.g., sum, count, find a value), and return the result.

4. Sanitize and normalize the columns before accessing them: 
   - Strip extra whitespace and convert to lowercase for matching.

Along with the final answer you should return information which files, sheets, columns are you referring.
for calculation purpose write a python function and execute it using function tool `execute_function_safely_using_exec`

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
                "The Alex Hotel Dublin": "str",
                "2025-06-26 00:00:00": "str",
                "2026-06-27 00:00:00": "str",
                "EUR": "str",
                "Property": "str",
                "Joanne McDonnell": "str",
                "27-Jun-2025 05:35:19 IST": "str",
                "3125-0002": "str"
            }
        },
        "sheet_configs": {
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
        tools=[read_sheet_with_custom_header, execute_function_safely_using_exec]
    )

    question = "read the report criteria ?"
    result = await Runner.run(data_analyser_assistant, question)
    print(result.final_output)

if __name__ == "__main__":
    asyncio.run(data_analyser())