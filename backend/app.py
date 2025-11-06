# backend/app.py
import random
import re
import pandas as pd
from flask import Flask, request, jsonify
import sqlite3
import os

app = Flask(__name__)

# --- 1. Load Data at Startup (This is the correct path logic) ---
# __file__ is app.py. os.path.dirname gets the 'backend' folder.
backend_dir = os.path.dirname(os.path.abspath(__file__))
# os.path.pardir goes "up" one level to the main project root
project_root = os.path.abspath(os.path.join(backend_dir, os.pardir))

# Build the full paths to the data files
pnr_file_path = os.path.join(project_root, 'data', 'pnr_database.csv')
stations_file_path = os.path.join(project_root, 'data', 'stations_original.csv')
db_path = os.path.join(project_root, 'railmadad.db') # Use a db in the root

print(f"Looking for PNR data at: {pnr_file_path}")
print(f"Looking for Station data at: {stations_file_path}")
print(f"Looking for DB at: {db_path}")

# Load PNR Data
try:
    # Use the correct column name 'PNR Number' as the index
    pnr_data = pd.read_csv(pnr_file_path, index_col='PNR') 
    print("✅ PNR dataset loaded successfully.")
except Exception as e:
    print(f"❌ ERROR loading PNR data: {e}")
    pnr_data = None

# Load Station Data
try:
    station_data = pd.read_csv(stations_file_path)
    # Use the correct column names from your CSV: 'station' and 'id_code'
    station_data['station'] = station_data['station'].str.lower()
    station_data['id_code'] = station_data['id_code'].str.lower()
    print("✅ Station dataset loaded successfully.")
except Exception as e:
    print(f"❌ ERROR loading Station data: {e}")
    station_data = None

# --- 2. Helper Functions ---

def handle_query_intent(request_json):
    """Handles the 'capture_user_query' intent."""
    user_query_text = request_json['queryResult']['parameters']['user_query']
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("INSERT INTO queries (query_text) VALUES (?)", (user_query_text,))
    conn.commit()
    new_query_id = cursor.lastrowid
    conn.close()
    
    response_text = f"Thank you. Your query has been registered with ID: Q-{new_query_id}."
    return {"fulfillmentText": response_text}

def handle_phone_number(request_json):
    """Handles the 'provide_phone_number' intent."""
    raw_input = request_json['queryResult'].get('queryText', '')
    digits = re.findall(r'\d', raw_input)
    phone_number_str = "".join(digits)
    
    if len(phone_number_str) == 10:
        return {
            "fulfillmentText": "Thank you. Where is the issue occurring? Please select one:",
            "outputContexts": [
                {
                    "name": f"{request_json['session']}/contexts/awaiting-location",
                    "lifespanCount": 1,
                    "parameters": {"phone_number": phone_number_str}
                }
            ],
            "payload": {
                "richContent": [
                    [
                        {
                            "type": "chips",
                            "options": [
                                {"text": "On a Train"},
                                {"text": "On a Platform"}
                            ]
                        }
                    ]
                ]
            }
        }
    else:
        return {"fulfillmentText": "That doesn't seem to be a valid 10-digit number. Please try again."}

def handle_station_search(request_json):
    """Handles the 'provide_station_name' intent."""
    user_input = request_json['queryResult']['parameters'].get('station_input', '').lower()
    
    if station_data is None:
        return {"fulfillmentText": "Error: Station database is not loaded. Please contact support."}

    station_match = station_data[
    (station_data['Station Code'] == user_input) | 
    (station_data['Station Name'] == user_input)
    ]
    
    if not station_match.empty:
        # Load the original CSV *again* just to get the proper capitalization
        original_station_name = pd.read_csv(stations_file_path).iloc[station_match.index[0]].get('station')
        
        return {
            "fulfillmentText": f"Did you mean '{original_station_name}'?",
            "outputContexts": [
                {
                    "name": f"{request_json['session']}/contexts/awaiting-station-confirmation",
                    "lifespanCount": 1,
                    "parameters": {"station_confirmed": original_station_name}
                }
            ]
        }
    else:
        return {"fulfillmentText": "Sorry, I couldn't find that station. Please try the name or code again."}

def handle_station_confirmed(request_json):
    """Handles the 'user_confirms_station_yes' intent."""
    try:
        confirmed_station = "Unknown"
        contexts = request_json['queryResult']['outputContexts']
        for c in contexts:
            if 'awaiting-station-confirmation' in c['name']:
                confirmed_station = c['parameters']['station_confirmed']
                break
        
        response_text = f"Great! Complaint at '{confirmed_station}'. Please describe your complaint (e.g., 'no water', 'dirty platform')."
        
        return {
            "fulfillmentText": response_text,
            "outputContexts": [
                {
                    "name": f"{request_json['session']}/contexts/awaiting-complaint-description",
                    "lifespanCount": 1,
                    "parameters": {"station_confirmed": confirmed_station}
                }
            ]
        }
    except Exception as e:
        print(f"Error in handle_station_confirmed: {e}")
        return {"fulfillmentText": "An error occurred. Please try again."}

def handle_pnr_verification(request_json):
    """Handles the 'provide_pnr' intent."""
    pnr_str = request_json['queryResult']['parameters'].get('pnr_number', '')

    if pnr_data is None:
        return {"fulfillmentText": "Error: PNR database is not loaded. Please contact support."}

    try:
        pnr_num_str = str(pnr_str)
        padded_pnr_num = pnr_num_str.zfill(10)
        pnr_to_check = f"PNR{padded_pnr_num}"
        
        if pnr_to_check in pnr_data.index:
            pnr_list = list(pnr_to_check)
            random.shuffle(pnr_list)
            token = "".join(pnr_list)
            
            pnr_details = pnr_data.loc[pnr_to_check]
            train_no = pnr_details['Train_No'] # Use the correct column name 'Train Number'

            response_text = f"PNR verified for Train {train_no}. Your complaint token is {token}. Please describe your complaint."
            
            return {
                "fulfillmentText": response_text,
                "outputContexts": [
                    {
                        "name": f"{request_json['session']}/contexts/awaiting-complaint-description",
                        "lifespanCount": 1,
                        "parameters": {
                            "complaint_token": token,
                            "pnr": pnr_to_check
                        }
                    }
                ]
            }
        else:
            return {"fulfillmentText": "That PNR was not found in our records. Please try again."}
    except Exception as e:
        print(f"Error in PNR check: {e}")
        return {"fulfillmentText": "That doesn't seem to be a valid PNR. Please enter a 10-digit PNR."}

# --- 3. Main Webhook Router ---

@app.route('/webhook', methods=['POST'])
def dialogflow_webhook():
    request_json = request.get_json()
    
    try:
        intent_name = request_json['queryResult']['intent']['displayName']
    except Exception:
        return jsonify({"fulfillmentText": "Error: Invalid request."})

    # This is the main "if-else" router for your bot
    if intent_name == 'capture_user_query':
        return jsonify(handle_query_intent(request_json))
        
    elif intent_name == 'provide_phone_number':
        return jsonify(handle_phone_number(request_json))

    elif intent_name == 'provide_station_name':
        return jsonify(handle_station_search(request_json))
        
    elif intent_name == 'user_confirms_station_yes':
        return jsonify(handle_station_confirmed(request_json))
    
    elif intent_name == 'provide_pnr':
        return jsonify(handle_pnr_verification(request_json))
    
    else:
        return jsonify({"fulfillmentText": "Error: Unrecognized intent in webhook."})

# --- 4. Run the Server ---
if __name__ == '__main__':
    # Render provides its own port via the PORT environment variable
    # We use 5000 as a default if we're testing locally
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=True)