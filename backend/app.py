# This code is used to run and test agent locally
import logging
from typing import List, Literal, Optional

from dotenv import load_dotenv
import os

# NOTE: agents library provides Agent, Runner, ModelSettings, function_tool
from agents import Agent, InputGuardrailTripwireTriggered, Runner, function_tool
from fastapi import Depends, FastAPI, HTTPException
from fastapi.responses import StreamingResponse
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from pydantic import BaseModel

from backend.code_executor import _execute_function_safely_using_exec
from backend.excel_file_reader import ReadSheetResult, SheetConfig, _read_sheet_with_custom_header
from backend.agent_instructions import INSTRUCTIONS as instructions
from backend.input_guardrail import hotel_domain_guardrail


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

# Load TOKEN from environment
TOKEN = os.environ.get('TOKEN')
if not TOKEN:
    raise RuntimeError('TOKEN environment variable not set')


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

def latest_user_question(messages: List[ChatMessage]) -> str:
    for msg in reversed(messages):
        if msg.role == "user" and msg.content.strip():
            return msg.content.strip()
    raise ValueError("No user question found")

app = FastAPI(title="Hotel Data Chat API", version="1.0")
# Bearer Auth setup
security = HTTPBearer()

def verify_token(credentials: HTTPAuthorizationCredentials = Depends(security)):
    if credentials.credentials != TOKEN:
        raise HTTPException(status_code=401, detail="Invalid or missing token")

hotel_data_analyser_agent = Agent(
    name="Hotel Data Analyser",
    instructions=instructions,
    tools=[read_sheet_with_custom_header, execute_function_safely_using_exec],
    input_guardrails=[hotel_domain_guardrail]
)

# SSE-style generator for streaming agent response
async def agent_response_stream(question: str):
    try:

        # Use Runner.run_streamed() as a class method
        result = Runner.run_streamed(hotel_data_analyser_agent, input=question)
        
        # Stream events from the result
        async for event in result.stream_events():
            # Handle different event types
            if event.type == "run_item_stream_event":
                if event.item.type == "message_output_item":
                    # Extract text from message output
                    from agents import ItemHelpers
                    text_content = ItemHelpers.text_message_output(event.item)
                    if text_content:
                        yield f"data: {text_content}\n\n"
            elif event.type == "raw_response_event":
                # Handle raw response events for token-by-token streaming
                from openai.types.responses import ResponseTextDeltaEvent
                if isinstance(event.data, ResponseTextDeltaEvent):
                    if event.data.delta:
                        yield f"data: {event.data.delta}\n\n"



        yield "data: [DONE]\n\n"
    except InputGuardrailTripwireTriggered as e:
        # Try to extract reasoning if available
        reasoning = "Your question is not related to hotel data analysis."
        if e.args and hasattr(e.args[0], "output_info"):
            output_info = e.args[0].output_info
            reasoning = getattr(output_info, "reasoning", reasoning)

        # Stream the guardrail rejection message
        yield f"data: ❌ Your question was rejected by the hotel domain guardrail.\n\n"
        yield f"data: 🧠 Reason: {reasoning}\n\n"
        yield f"data: 💡 Try asking something related to hotels or hotel data analysis, like:\n\n"
        yield f"data:    - 'What is the room revenue in January?'\n\n"
        yield f"data:    - 'Compare occupancy between August and September.'\n\n"
        yield "data: [DONE]\n\n"

    except Exception as e:
        logging.exception("Agent processing failed")
        yield f"data: ERROR: {str(e)}\n\n"

# ───────────────────────────────
# POST endpoint to stream agent
# ───────────────────────────────
@app.post("/api/v1/chat", response_class=StreamingResponse)
async def chat_endpoint(
    body: ChatRequest,
    _: HTTPAuthorizationCredentials = Depends(verify_token)
):
    if not body.messages:
        raise HTTPException(status_code=400, detail="No messages provided")

    last_message = body.messages[-1].content.strip()

    return StreamingResponse(
        agent_response_stream(last_message),
        media_type="text/event-stream"
    )