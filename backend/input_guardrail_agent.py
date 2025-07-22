from pydantic import BaseModel
from agents import (
    Agent,
    GuardrailFunctionOutput,
    RunContextWrapper,
    Runner,
    TResponseInputItem,
    input_guardrail,
)


class HotelRelatedOutput(BaseModel):
    is_hotel_data_related: bool
    reasoning: str


hotel_guardrail_agent = Agent(
    name="Hoteln Data Domain Guardrail",
    instructions="""
        You are a guardrail agent that checks if a question is related to hotel data analysis.

        Mark `is_hotel_data_related: true` if the question involves:
        - Hotel metrics like occupancy, revenue, bookings, ADR, check-in/out
        - Comparison of dates, months, segments
        - Any type of insight that can reasonably be derived from hotel Excel files
        - Even if the question does not explicitly mention sheet/file/column names

        Mark `is_hotel_data_related: false` only if:
        - The question is completely unrelated to hotels (e.g., math, news, general trivia)
        - It refers to topics like weather, politics, finance, or science

        Respond ONLY in JSON:
        {
        "is_hotel_data_related": true/false,
        "reasoning": "Short reasoning"
        }
    """,
    output_type=HotelRelatedOutput,
)


@input_guardrail
async def hotel_domain_guardrail(
    ctx: RunContextWrapper[None],
    agent: Agent,
    input: str | list[TResponseInputItem],
) -> GuardrailFunctionOutput:
    result = await Runner.run(hotel_guardrail_agent, input, context=ctx.context)

    output = result.final_output
    if isinstance(output, dict):  # fallback
        output = HotelRelatedOutput(**output)
    print("hotel guardrail output: ", output)
    return GuardrailFunctionOutput(
        output_info=output,
        tripwire_triggered=not output.is_hotel_data_related,
    )
