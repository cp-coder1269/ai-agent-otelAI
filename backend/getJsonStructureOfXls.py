# Script to inspect each sheet's columns and dtypes, building dict
import pandas as pd, json
import os

def getJsonStructureOfXls(file_path, sheet_headers=None):
    if not os.path.exists(file_path):
        print(f"File not found: {file_path}")
        return {}
    xls = pd.ExcelFile(file_path)
    result = {}
    for sheet in xls.sheet_names:
        try:
            header_row = sheet_headers.get(sheet, 0) if sheet_headers else 0
            df = pd.read_excel(xls, sheet_name=sheet, header=header_row)
        except Exception as e:
            print(f'Failed to load {sheet}: {e}')
            continue
        # Map pandas dtypes to simple
        type_map = {}
        for col, dtype in df.dtypes.items():
            if pd.api.types.is_integer_dtype(dtype):
                type_map[str(col)] = 'int'
            elif pd.api.types.is_float_dtype(dtype):
                type_map[str(col)] = 'float'
            elif pd.api.types.is_bool_dtype(dtype):
                type_map[str(col)] = 'bool'
            elif pd.api.types.is_datetime64_any_dtype(dtype):
                type_map[str(col)] = 'datetime'
            else:
                type_map[str(col)] = 'str'
        result[sheet] = type_map
    json_output = json.dumps(result, indent=2)
    return json_output