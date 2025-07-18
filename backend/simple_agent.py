import asyncio
import pandas as pd
from dotenv import load_dotenv
from typing import Optional, Dict, Any, TypedDict, List
from agents import Agent, ModelSettings, Runner, function_tool
import logging

# Load environment variables (API key)
load_dotenv()

logging.basicConfig(filename='function_calls.log', level=logging.INFO)


# Define strict types for function_tool compatibility
class SheetConfig(TypedDict, total=False):
    start: int
    end: int

class ReadSheetResult(TypedDict):
    sheet: str
    header: List[Any]
    columns: List[str]
    rows: List[dict]

@function_tool
def read_sheet_with_custom_header(
    filepath: str,
    sheet: str,
    config: SheetConfig
) -> ReadSheetResult:
    logging.info(f"Called with filepath={filepath}, sheet={sheet}, config={config}")
    """
    Reads an Excel sheet with a custom header row location.

    Args:
        filepath: Path to the Excel file.
        sheet: Sheet name to read from.
        config: Row config for the sheet with keys: 'start' (required) and optionally 'end'.

    Returns:
        A dictionary with:
        - 'header': Original header row from Excel.
        - 'rows': List of row records (each as a dict).
        - 'columns': List of sanitized column names.
        - 'sheet': Name of the sheet read.
    """
    if not config or "start" not in config:
        raise ValueError(f"Invalid configuration for sheet '{sheet}'")

    start_row = config["start"]
    end_row = config.get("end")

    df = pd.read_excel(filepath, sheet_name=sheet, header=None, engine="openpyxl")

    header_row = df.iloc[start_row].tolist()

    if end_row is not None:
        data_df = df.iloc[start_row + 1:end_row + 1].copy()
    else:
        data_df = df.iloc[start_row + 1:].copy()

    data_df.columns = header_row
    sanitized_columns = [
        str(col).strip().replace("\n", " ").replace("\r", "").replace("\t", " ").lower()
        for col in data_df.columns
    ]
    data_df.columns = sanitized_columns

    return {
        "sheet": sheet,
        "header": header_row,
        "columns": sanitized_columns,
        "rows": data_df.to_dict(orient="records")
    }




# Define detailed instructions for our weather assistant
instructions = """
You are a data analysis agent with access to structured Excel files and a tool named `read_sheet_with_custom_header`. 
Your job is to answer user questions by identifying the correct Excel file, sheet, and column, using the file's schema and the tool provided.

You must:

1. Parse the user's question to identify:
   - The file being referred to (`oc_onboarding_file` or `alex_ideas_file`).
   - The correct sheet name (e.g., "Budget", "Segment Descriptions").
   - The relevant column(s) mentioned (e.g., "Jan Rooms Revenue", "Occupancy Date").

2. Use the `read_sheet_with_custom_header` tool with these parameters:
   - `filepath`: path of the file.
   - `sheet`: sheet name.
   - `sheet_configs`: dictionary of `{sheet_name: {"start": row, "end": optional_row}}`.

3. Use the returned DataFrame to extract the required data, compute answers (e.g., sum, count, find a value), and return the result.

4. Sanitize and normalize the columns before accessing them: 
   - Strip extra whitespace and convert to lowercase for matching.

Along with the final answer you should return information which files, sheets, columns are you referring.
print the value of the data which you are using for calculation.
perform calculation using writing a program and execute it.

You must only rely on the schema provided below for determining which columns exist in which sheets.
Here is the complete schema of available files and their sheets/columns:

{
    "oc_onboarding_file": {
        "file_path": "data/OCOnboardingInformation.xlsx",
        "oc_onboarding_file_structure": {
            "Rooms per category": {
                "Room Type": "str",
                "Room Type per Ideas\\n": "str",
                "Room Class per Ideas": "str",
                "Number of Rooms": "int",
                "Zip & Link": "float"
            },
            "Segment Descriptions": {
                "Segment Name": "str",
                "Definition": "str",
                "Desc": "str",
                "Macro Group": "str",
                "Owner": "str",
                "Lead Time": "str"
            },
            "OTA Commission Rates": {
                "Segment Name": "str",
                "Definition": "str",
                "Desc": "str",
                "Macro Group": "str",
                "Commission": "str"
            },
            "Budget": {
                "Group or Transient": "str",
                "Segment": "str",
                "Macro Group": "str",
                "Definition": "str",
                "Jan Rooms": "str",
                "Jan Rooms Revenue": "float",
                "Jan ADR": "float",
                "Feb Rooms": "str",
                "Feb Rooms Revenue": "float",
                "Feb ADR": "float",
                "March Rooms": "str",
                "March Rooms Revenue": "float",
                "March ADR": "float",
                "April Rooms": "str",
                "April Rooms Revenue": "float",
                "April ADR": "float",
                "May Rooms": "str",
                "May Rooms Revenue": "float",
                "May ADR": "float",
                "June Rooms": "str",
                "June Rooms Revenue": "float",
                "June ADR": "float",
                "July Rooms": "str",
                "July Rooms Revenue": "float",
                "July ADR": "float",
                "Aug Rooms": "str",
                "Aug Rooms Revenue": "float",
                "Aug ADR ": "float",
                "Sept Rooms": "str",
                "Sept Rooms Revenue": "float",
                "Sept ADR ": "float",
                "Oct Rooms": "str",
                "Oct Rooms Revenue": "float",
                "Oct ADR ": "float",
                "Nov Rooms": "str",
                "Nov Rooms Revenue": "float",
                "Nov ADR ": "float",
                "Dec Rooms": "str",
                "Dec Rooms Revenue": "float",
                "Dec ADR ": "float",
                "Total Rooms": "float",
                "Total Rooms Revenue": "float",
                "Total ADR": "float"
            },
            "PY Event Diary": {
                "Special Event Name": "str",
                "Description": "str",
                "Pre-Event days": "int",
                "Day of Week": "str",
                "Start Date": "datetime",
                "Day of Week.1": "str",
                "End Date": "str",
                "Post-event days": "int",
                "Information Only": "str",
                "Category": "str",
                "Created By": "str",
                "Created On": "str",
                "Updated By": "str",
                "Updated On": "str"
            }
        },
        "sheet_configs": {
            "Rooms per category": { "start": 3, "end": 8 },
            "Segment Descriptions": { "start": 1 },
            "OTA Commission Rates": { "start": 1 },
            "Budget": { "start": 2, "end": 18 },
            "PY Event Diary": { "start": 1 }
        }
    },
    "alex_ideas_file": {
        "file_path": "data/TheAlexIdeas 27_June_2025.xlsx",
        "alex_ideas_structure": {
            "Property": {
                "Property Name": "str",
                "Day of Week": "str",
                "Occupancy Date": "datetime",
                "Special Event This Year": "str",
                "Physical Capacity This Year": "float",
                "Occupancy On Books This Year": "float",
                "Occupancy On Books STLY": "float",
                "Rooms Sold - Group This Year": "float",
                "Rooms Sold - Group STLY": "float",
                "Rooms Sold - Transient This Year": "float",
                "Rooms Sold - Transient STLY": "float",
                "Booked Room Revenue This Year": "float",
                "Booked Room Revenue STLY": "float",
                "Forecasted Room Revenue This Year": "float",
                "DLY1": "float"
            },
            "Room Type": {
                "Property Name": "str",
                "Day of Week": "str",
                "Occupancy Date": "datetime",
                "Room Type": "str",
                "Room Class": "str",
                "DLY1 This Year": "float"
            },
            "Business View": {
                "Property Name": "str",
                "Day of Week": "str",
                "Occupancy Date": "datetime",
                "Business View": "str",
                "Occupancy On Books This Year": "int",
                "Occupancy On Books STLY": "int",
                "Booked Room Revenue This Year": "float",
                "Booked Room Revenue STLY": "float",
                "Forecasted Room Revenue This Year": "float"
            },
            "Report Criteria": {
                "The Alex Hotel Dublin": "str",
                "2025-06-26 00:00:00": "str",
                "2026-06-27 00:00:00": "str",
                "EUR": "str",
                "Property": "str",
                "Joanne McDonnell": "str",
                "27-Jun-2025 05:35:19 IST": "str",
                "3125-0002": "str"
            }
        },
        "sheet_configs": {
            "Report Criteria": { "start": 3 }
        }
    }
}
"""


async def data_analyser():
    # Create our specialized weather assistant
    data_analyser_assistant = Agent(
        name="Hotel Data Analyser",
        instructions=instructions,
        tools=[read_sheet_with_custom_header]
    )

    question = "Sum of Jan Rooms Revenue?"
    result = await Runner.run(data_analyser_assistant, question)
    print(result.final_output)


if __name__ == "__main__":
    asyncio.run(data_analyser())