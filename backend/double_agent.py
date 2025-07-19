import asyncio
import json
import logging
import re
from typing import List, Optional, TypedDict

import pandas as pd
from dotenv import load_dotenv

# NOTE: agents library provides Agent, Runner, ModelSettings, function_tool
from agents import Agent, Runner, function_tool

from backend.helpers.schema import SCHEMA

# ─────────────────────────────────────────────────────────────────────────────
# Setup & logging
# ─────────────────────────────────────────────────────────────────────────────
load_dotenv(override=True)
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
instructions = instructions = f"""
You are a data analysis agent with access to structured Excel files and a tool named read_sheet_with_custom_header. 
Your job is to answer user questions by identifying the correct Excel file, sheet, and column, using the file's schema and the tool provided.

You must:

1. Parse the user's question to identify:
   - The file being referred to (oc_onboarding_file or alex_ideas_file).
   - The correct sheet name (e.g., "Budget", "Segment Descriptions").
   - The relevant column(s) mentioned (e.g., "Jan Rooms Revenue", "Occupancy Date").

2. Use the read_sheet_with_custom_header tool with these parameters:
   - filepath: path of the file.
   - sheet: sheet name.
   - sheet_configs: dictionary of `{{"sheet_name": {{"start": row, "end": optional_row}}}}`. Don't use/modify config your own

3. Use the returned DataFrame to extract the required data, compute answers (e.g., sum, count, find a value), and return the result.

4. Sanitize and normalize the columns before accessing them: 
   - Strip extra whitespace and convert to lowercase for matching.

Along with the final answer you should return information which files, sheets, columns are you referring.
For calculation purpose, write a Python function and execute it using function tool execute_function_safely_using_exec.

You must only rely on the schema provided below for determining which columns exist in which sheets.
Here is the complete schema of available files and their sheets/columns:
SCHEMA_JSON = {json.dumps(SCHEMA, indent=2)}
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
    # print(instructions)