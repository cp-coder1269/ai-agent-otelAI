
from backend.code_executor import execute_function_safely_using_exec
from backend.llm_helper import get_openai_response
from backend.constants import OC_SHEET_CONFIG
from readFile import read_sheet_with_custom_header

if __name__ == "__main__":
    question = "Sum of Jan Rooms Revenue for all records",
    prompt = f"""
        Your task is to write a python function.
        
        This function takes a single argument as input. The argument is pandas dataframe.

        The dataframe has a column called "jan rooms revenue". Do not validate that it should have only this column. It can have other columns.
 
        The job of this function is to do the following job:

        {question}

        Only return the python function. The function should simply named 'f' Do not return anything extra in your response. 
        Any imports that need to be done should be done inside the function.

    """

    response = get_openai_response(prompt=prompt)
    print("response: ", response)


    file_path='/Users/sv/Desktop/ai-agent-otelAI/data/OCOnboardingInformation.xlsx'
    df = read_sheet_with_custom_header(filepath=file_path, sheet="Budget", sheet_configs=OC_SHEET_CONFIG).get('data')

    result = execute_function_safely_using_exec(response, 'f', df)

    print(result)