# This code is used to run and test agent locally
import logging
from typing import AsyncGenerator, List, Literal, Optional

from dotenv import load_dotenv

# NOTE: agents library provides Agent, Runner, ModelSettings, function_tool
from agents import Agent, Runner, function_tool
from fastapi import FastAPI, HTTPException
from fastapi.responses import StreamingResponse
from openai.types.responses import ResponseTextDeltaEvent
from pydantic import BaseModel

from backend.code_executor import _execute_function_safely_using_exec
from backend.excel_file_reader import ReadSheetResult, SheetConfig, _read_sheet_with_custom_header
from backend.agent_instructions import INSTRUCTIONS as instructions


load_dotenv(override=True)
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler("api.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)




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
    try:
        return _read_sheet_with_custom_header(filepath,sheet,config,columns)
    except Exception as e:
        logger.error(f"Error reading sheet: {str(e)}")
        raise


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
    try:
        return _execute_function_safely_using_exec(func_string, function_name)
    except Exception as e:
        logger.error(f"Error executing function: {str(e)}")
        raise


class ChatMessage(BaseModel):
    role: Literal["user", "assistant"]
    content: str

class ChatRequest(BaseModel):
    messages: List[ChatMessage]

HOTEL_DATA_ANALYSER_AGENT = Agent(
        name="Hotel Data Analyser",
        instructions=instructions,
        # model="gpt-4o-mini",
        tools=[read_sheet_with_custom_header, execute_function_safely_using_exec]
    )

def latest_user_question(messages: List[ChatMessage]) -> str:
    for msg in reversed(messages):
        if msg.role == "user" and msg.content.strip():
            return msg.content.strip()
    raise ValueError("No user question found")

app = FastAPI(title="Hotel Data Chat API", version="1.0")

@app.post("/api/v1/chat")
async def chat_endpoint(request: ChatRequest):
    """
    POST /api/v1/chat
    {
        "messages": [
            {"role": "user", "content": "How are you?"},
            {"role": "ai",   "content": "I am good"},
            {"role": "user", "content": "read the report criteria ?"}
        ]
    }
    """
    try:
        question = latest_user_question(request.messages)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    async def stream() -> AsyncGenerator[str, None]:
        runner = Runner.run_streamed(HOTEL_DATA_ANALYSER_AGENT, question)
        async for event in runner.stream_events():
            if (
                event.type == "raw_response_event"
                and isinstance(event.data, ResponseTextDeltaEvent)
                and event.data.delta
            ):
                print(event.data.delta, end="", flush=True)
                # Convert any delta payload (obj / dict / str) → str for the wire
                yield str(event.data.delta)

    return StreamingResponse(stream(), media_type="text/plain")