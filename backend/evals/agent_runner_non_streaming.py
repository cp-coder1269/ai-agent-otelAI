from agents import Runner
from backend.app import hotel_data_analyser_agent

async def run_agent(question: str) -> str:
    agent = hotel_data_analyser_agent
    result = await Runner.run(agent, question)
    return result.final_output
