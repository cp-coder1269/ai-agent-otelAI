import re

import pandas as pd

# NOTE: agents library provides Agent, Runner, ModelSettings, function_tool
from agents import function_tool



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