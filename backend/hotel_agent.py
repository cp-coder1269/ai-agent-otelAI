from typing import AsyncGenerator
from agents import Agent, Runner
from fastapi.responses import StreamingResponse
from openai.types.responses import ResponseTextDeltaEvent

from backend.function_tools import execute_function_safely_using_exec, read_sheet_with_custom_header
from backend.helpers import instructions


HOTEL_DATA_ANALYSER_AGENT = Agent(
    name="Hotel Data Analyser",
    instructions=instructions,
    # model="gpt-4o-mini",
    # model_settings=ModelSettings(
    #     temperature=0.3,  # Lower for more deterministic outputs (0.0-2.0)
    #     max_tokens=1024,  # Maximum length of response
    # ),
    tools=[read_sheet_with_custom_header, execute_function_safely_using_exec]
)

def agent_stream(question: str) -> StreamingResponse:
    """
    Return a StreamingResponse that yields text deltas from the agent.
    """

    async def _generator() -> AsyncGenerator[str, None]:
        runner = Runner.run_streamed(HOTEL_DATA_ANALYSER_AGENT, question)
        async for event in runner.stream_events():
            if (
                event.type == "raw_response_event"
                and isinstance(event.data, ResponseTextDeltaEvent)
                and event.data.delta
            ):
                print(event.data.delta, end="", flush=True)
                # Yield each delta chunk to the client
                yield str(event.data.delta)

    # Wrap the async generator in a StreamingResponse.
    return StreamingResponse(_generator(), media_type="text/plain")