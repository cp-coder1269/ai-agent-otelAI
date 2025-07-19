import asyncio
from typing import Any
from agents import Agent, Runner, function_tool
from backend.constants import OC_SHEET_CONFIG
import re
import pandas as pd

from readFile import read_sheet_with_custom_header


def _extract_code_from_response(response: str) -> str:
    """Pull the first ```python ... ``` (or plain ```) block from a string."""
    match = re.search(r"```(?:python)?[ \t]*\r?\n([\s\S]*?)```", response)
    return match.group(1).strip() if match else response.strip()


@function_tool
def execute_function_safely_using_exec(
    func_string: str,
    function_name: str,
    *args,
    **kwargs,
) -> Any:
    """
    Evaluate a Python function (provided as a string) in a restricted namespace
    and execute it with the supplied args / kwargs.
    """
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
        },
        "pd": pd,
        "re": re,
    }
    local_vars: dict = {}

    code = _extract_code_from_response(func_string)
    exec(code, safe_globals, local_vars)

    if function_name not in local_vars:
        raise NameError(f"Function '{function_name}' not found")

    return local_vars[function_name](*args, **kwargs)

@function_tool
def getDataframe() -> pd.DataFrame:
    """Get the dataframe from the Excel file."""
    file_path = '/Users/sv/Desktop/ai-agent-otelAI/data/OCOnboardingInformation.xlsx'
    df = read_sheet_with_custom_header(
        filepath=file_path, 
        sheet="Budget", 
        sheet_configs=OC_SHEET_CONFIG
    ).get('data')
    return df


async def data_analyser():
    """Main function to analyze hotel data."""
    
    # Define the question and instructions
    question = "Sum of Jan Rooms Revenue for all records"
    
    instructions = f"""
    You are a data analyst.
    Your task is to write a python function and execute it with the function tool `execute_function_safely_using_exec`.
    
    0. Read dataframe df using the function tool getDataframe which returns dataframe
    1. **Write python function 'f'**:
       This function takes a single argument as input. The argument is pandas dataframe df.
       The dataframe has a column called "jan rooms revenue". Do not validate that it should have only this column. It can have other columns.
    
       The job of this function is to do the following job:
       {question}

       Only return the python function. The function should simply be named 'f'. Do not return anything extra in your response. 
       Any imports that need to be done should be done inside the function.
       
    2. **Execute the function 'f'**:
       Execute the function 'f' with `execute_function_safely_using_exec` eg execute_function_safely_using_exec(code, 'f', df)
       
    3. **Final response**:
       Use the result of step 2 and generate the final answer of the problem
    """

    # Create our specialized data analyst assistant
    data_analyser_assistant = Agent(
        name="Hotel Data Analyser",
        instructions=instructions,
        tools=[getDataframe, execute_function_safely_using_exec]
    )

    # Run the analysis
    user_question = "Sum of Jan Rooms Revenue?"
    result = await Runner.run(data_analyser_assistant, user_question)
    print(result.final_output)


if __name__ == "__main__":
    asyncio.run(data_analyser())