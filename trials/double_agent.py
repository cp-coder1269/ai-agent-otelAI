
# ─────────────────────────────────────────────────────────────────────────────
# Setup & logging
# ─────────────────────────────────────────────────────────────────────────────
import asyncio
import logging
from typing import List, Optional
from agents import Agent, InputGuardrailTripwireTriggered, Runner, function_tool
from dotenv import load_dotenv

from backend.helpers.code_executor import _execute_function_safely_using_exec
from backend.helpers.excel_file_reader import ReadSheetResult, SheetConfig, _read_sheet_with_custom_header
from backend.helpers.agent_instructions import INSTRUCTIONS as instructions
from backend.input_guardrail_agent import hotel_domain_guardrail


load_dotenv(override=True)
logging.basicConfig(filename="function_calls.log", level=logging.INFO)


@function_tool
def read_sheet_with_custom_header(
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
    return _read_sheet_with_custom_header(filepath, sheet, config, columns)


@function_tool
def execute_function_safely_using_exec(func_string: str, function_name: str) -> str:
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
        tools=[read_sheet_with_custom_header, execute_function_safely_using_exec],
        input_guardrails=[hotel_domain_guardrail],
    )

    question = "what is the school?"
    question = "what is the revenue for january?"
    try:
        result = await Runner.run(data_analyser_assistant, question)
        print(result.final_output)
    except InputGuardrailTripwireTriggered as e:
        output_info = None

        if e.args and hasattr(e.args[0], "output_info"):
            output_info = e.args[0].output_info

        reasoning = getattr(
            output_info, "reasoning", "This input was rejected by the domain guardrail."
        )

        print("\n❌ Your question was rejected by the hotel domain guardrail.")
        print(f"🧠 Reason: {reasoning}")
        print(
            "💡 Try asking something which is unrelated to hotels or hotel data analysis like:"
        )
        print("   - 'What is the room revenue in January?'")
        print("   - 'Compare occupancy between August and September.'")


if __name__ == "__main__":
    asyncio.run(data_analyser())
    # print(read_sheet_with_custom_header(filepath="data/TheAlexIdeas27_June_2025.xlsx", sheet="Room Type", config={ "start": 0, "end": 5 } ) )
