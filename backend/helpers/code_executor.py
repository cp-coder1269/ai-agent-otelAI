import re
import pandas as pd

from backend.helpers.excel_file_reader import _read_sheet_with_custom_header



def _extract_code_from_response(response: str) -> str:
    """Pull the first ```python ... ``` (or plain ```) block from a string."""
    match = re.search(r"```(?:python)?[ \t]*\r?\n([\s\S]*?)```", response)
    return match.group(1).strip() if match else response.strip()


def _execute_function_safely_using_exec(func_string: str, function_name: str) -> str:
    """
    Executes a given Python function defined in a code block in the LLM's response.

    Parameters:
    - response (str): Code block containing the function definition.
    - function_name (str): The name of the function to call (must be defined in the response).

    Returns:
    - str: The result of the function execution.
    """
    print(
        f"[DEBUG] execute_function_safely_using_exec called with function_name={function_name}"
    )
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
            "tuple": tuple,
            "set": set,
            "print": print,
            "sum": sum,
            "max": max,
            "min": min,
            "abs": abs,
            "round": round,
            "enumerate": enumerate,
            "zip": zip,
            "sorted": sorted,
            "any": any,
            "all": all,
        },
        "pd": pd,
        "re": re,
        "datetime": __import__("datetime"),
        "date": __import__("datetime").date,
        "datetime": __import__("datetime").datetime,
        "timedelta": __import__("datetime").timedelta,
        "read_sheet_with_custom_header": _read_sheet_with_custom_header,
    }
    local_vars: dict = {}

    code = _extract_code_from_response(func_string)
    exec(code, safe_globals, local_vars)

    if function_name not in local_vars:
        raise NameError(f"Function '{function_name}' not found")

    result = local_vars[function_name]()
    print(f"[DEBUG] Result of {function_name}: {result}")
    return result
