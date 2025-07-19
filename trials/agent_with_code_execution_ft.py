import asyncio
import re
from agents import Agent, Runner, function_tool


def _extract_code_from_response(response):
    # Extract code block from markdown
    code_match = re.search(r"```(?:python)?[ \t]*\r?\n([\s\S]*?)```", response)
    if code_match:
        return code_match.group(1).strip()
    return response.strip()


@function_tool
def execute_function_safely_using_exec(response: str, function_name: str) -> str:
    """
    Executes a given Python function defined in a code block in the LLM's response.

    Parameters:
    - response (str): Code block containing the function definition.
    - function_name (str): The name of the function to call (must be defined in the response).

    Returns:
    - str: The result of the function execution.
    """
    safe_globals = {
        '__builtins__': {
            '__import__': __import__,
            'len': len,
            'range': range,
            'str': str,
            'int': int,
            'float': float,
            'list': list,
            'dict': dict,
            'print': print,
            'sum': sum
        }
    }

    local_vars = {}
    func_string = _extract_code_from_response(response=response)
    print("code: \n", func_string)

    try:
        # Run the code safely
        exec(func_string, safe_globals, local_vars)

        if function_name in local_vars:
            result = local_vars[function_name]()
            return str(result)
        else:
            raise NameError(f"Function '{function_name}' not found")
    except Exception as e:
        return f"Error during execution: {str(e)}"


instructions = """
You are a calculator assistant. Your job is to understand the user's question, 
write a Python function named `calc`, and call the tool `execute_function_safely_using_exec` 
with the function definition and the function name. Then respond with the output of the function.
"""

async def data_analyser():
    data_calculator_assistant = Agent(
        name="Data Calculator",
        instructions=instructions,
        tools=[execute_function_safely_using_exec]
    )

    question = "what is e power 24.1"
    result = await Runner.run(data_calculator_assistant, question)
    print(result.final_output)


if __name__ == "__main__":
    asyncio.run(data_analyser())
