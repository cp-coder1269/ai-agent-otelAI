from backend.helpers.sheet_configs import OC_SHEET_CONFIG, THE_ALEX_SHEET_CONFIG


SCHEMA = {
    "oc_onboarding_file": {
        "file_path": "data/OCOnboardingInformation.xlsx",
        "oc_onboarding_file_structure": {
            "Rooms per category": {
                "Room Type": "str",
                "Room Type per Ideas\n": "str",
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
        "sheet_configs": OC_SHEET_CONFIG
    },
    "alex_ideas_file": {
        "file_path": "data/TheAlexIdeas27_June_2025.xlsx",
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
                "Property Name": "str",
                "Start Date": "datetime",
                "End Date": "datetime",
                "Currency": "str",
                "Inventory Group": "str",
                "Created By": "str",
                "Generated On": "str",
                "Account ID": "str"
            }
        },
        "sheet_configs": THE_ALEX_SHEET_CONFIG
    }
}