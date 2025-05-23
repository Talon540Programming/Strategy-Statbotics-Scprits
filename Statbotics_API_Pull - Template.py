import pandas as pd
import gspread
import statbotics
from oauth2client.service_account import ServiceAccountCredentials

sb = statbotics.Statbotics()

# constants 
L1 = 'coral_l1'
L2 = 'coral_l2'
L3 = 'coral_l3'
L4 = 'coral_l4'
points = 'total_points'
year = 2025

# change to search for events
event_code = "hop"

# first run will make a new sheet
# if you keep the same name you can update any workseet inside the sheet 
sheet_name = "Test_import"
worksheet_name = "Sheet1"

# pulls value bassed on constant passed 
def extract_values(team_data, type):
    """Extract values from team_data"""
    try:
        return team_data['epa']['breakdown'][type]
    except (TypeError, KeyError):
        return None
    
# pulls teams name
def extract_team_name(name_data):
    """Extract team name from dict"""
    if isinstance(name_data, dict):
        return name_data.get('team_name', 'Unknown')
    return str(name_data)

def export_to_sheets(data_list, sheet_name, worksheet_name):
    """Export data to a Google Sheet; update if it exists or create if not."""
    scope = ['https://www.googleapis.com/auth/spreadsheets', 'https://www.googleapis.com/auth/drive']
    creds = ServiceAccountCredentials.from_json_keyfile_name('json file here', scope)
    client = gspread.authorize(creds)

    # Try to open existing sheet; if not, create it
    try:
        sheet = client.open(sheet_name)
    except gspread.SpreadsheetNotFound:
        print(f"Spreadsheet '{sheet_name}' not found. Creating new one.")
        sheet = client.create(sheet_name)

    # Try to open worksheet; if not, create it
    try:
        worksheet = sheet.worksheet(worksheet_name)
    except gspread.WorksheetNotFound:
        print(f"Worksheet '{worksheet_name}' not found. Creating new one.")
        worksheet = sheet.add_worksheet(title=worksheet_name, rows="100", cols="10")

    # Clear existing content
    worksheet.clear()

    # stores rows as 2d array 
    total_rows = []

    # Headers
    headers = ['Team', 'Year', 'Name', 'EPA', 'Coral L4', 'Coral L3', 'Coral L2', 'Coral L1']
    total_rows.append(headers)

    # Append rows
    for data in data_list:
        row = [
            data['team'],
            data['year'],
            data['name'],
            data['epa_value'],
            data['coral_l4'],
            data['coral_l3'],
            data['coral_l2'],
            data['coral_l1']
        ]
        total_rows.append(row)

    worksheet.append_rows(total_rows)

    # Make sheet public (optional)
    sheet.share(None, perm_type='anyone', role='writer')

    print(f"Spreadsheet updated: {sheet.url}")
    return sheet.url

def main(year, event_key):
    # Get all team-event data for the given event
    team_events = sb.get_team_events(event=event_key, limit=100)
    teams = sorted(set(te['team'] for te in team_events))
    epa_list = ["epa"]
    name_list = ["team_name"]

    results = []

    for team in teams:
        try:
            # trys to get epa and name from each team will throw if null
            epa = sb.get_team_event(team, event_key, epa_list)
            name = sb.get_team_event(team, event_key, name_list)
        except Exception as e:
            print(f"Failed to get data for team {team}: {e}")
            continue

        # pulls specific data from all data
        coral_l4 = extract_values(epa, L4)
        coral_l3 = extract_values(epa, L3)
        coral_l2 = extract_values(epa, L2)
        coral_l1 = extract_values(epa, L1)
        epa_value = extract_values(epa, points)
        team_name = extract_team_name(name)

        if team_name is not None:
            print(f"Team {team} ({team_name}): EPA = {epa_value:.2f}, L4 = {coral_l4:.2f}, L3 = {coral_l3:.2f}, L2 = {coral_l2:.2f}, L1 = {coral_l1:.2f}")

            result = {
                'team': team,
                'year': year,
                'name': team_name,
                'epa_value': epa_value,
                'coral_l4': coral_l4,
                'coral_l3': coral_l3,
                'coral_l2': coral_l2,
                'coral_l1': coral_l1
            }
            results.append(result)

    if results:
        df = pd.DataFrame(results)
        print("\nResults as DataFrame:")
        print(df)
        export_to_sheets(results, sheet_name, worksheet_name)
    

if __name__ == "__main__":
    event_code_input = str(year) + event_code
    main(year, event_code_input)