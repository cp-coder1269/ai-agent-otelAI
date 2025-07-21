# This code is used to run and test agent locally
import asyncio
import logging
from typing import List, Optional

from dotenv import load_dotenv

# NOTE: agents library provides Agent, Runner, ModelSettings, function_tool
from agents import Agent, Runner, function_tool

from backend.code_executor import _execute_function_safely_using_exec
from backend.excel_file_reader import ReadSheetResult, SheetConfig, _read_sheet_with_custom_header
from backend.agent_instructions import INSTRUCTIONS as instructions

# ─────────────────────────────────────────────────────────────────────────────
# Setup & logging
# ─────────────────────────────────────────────────────────────────────────────
load_dotenv()
logging.basicConfig(filename="function_calls.log", level=logging.INFO)


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
    return _read_sheet_with_custom_header(filepath,sheet,config,columns)


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
    return _execute_function_safely_using_exec(func_string, function_name)

async def data_analyser():
    # Create our specialized weather assistant
    data_analyser_assistant = Agent(
        name="Hotel Data Analyser",
        instructions=instructions,
        # model="gpt-4o-mini",
        tools=[read_sheet_with_custom_header, execute_function_safely_using_exec]
    )

    question = "in the month of august which date has the maximum occupancy?"
    result = await Runner.run(data_analyser_assistant, question)
    print(result.final_output)

if __name__ == "__main__":
    asyncio.run(data_analyser())
    # print(read_sheet_with_custom_header(filepath="data/TheAlexIdeas27_June_2025.xlsx", sheet="Room Type", config={ "start": 0, "end": 5 } ) )