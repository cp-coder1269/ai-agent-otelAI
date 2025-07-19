import re
import pandas as pd


def _extract_code_from_response(response):
    # Extract code block from markdown (```python ... ``` or ``` ... ```)
    code_match = re.search(r"```(?:python)?[ \t]*\r?\n([\s\S]*?)```", response)
    if code_match:
        return code_match.group(1).strip()
    return response.strip()  # fallback: return as-is

def execute_function_safely_using_exec(response, function_name, *args, **kwargs):
    # Create a restricted environment
    # __builtins__ is for safety. remove it if we need to increase the scope.
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
            'print': print
            # Add only the built-ins you need
        },
        'pd': pd
    }
    
    local_vars = {}
    func_string = _extract_code_from_response(response=response)
    # Execute the function definition
    exec(func_string, safe_globals, local_vars)
    
    # Call the function
    if function_name in local_vars:
        return local_vars[function_name](*args, **kwargs)
    else:
        raise NameError(f"Function '{function_name}' not found")
if __name__ == "__main__":
    code = """
        def square(x):
            return x * x
            print('Square of 5 is', square(5))
        """
    result = execute_function_safely_using_exec(code, "square", 5)
    print("sqr of 5: ", result)