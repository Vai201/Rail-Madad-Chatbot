# backend/app.py
import random
import re
import pandas as pd
from flask import Flask, request, jsonify
import sqlite3
import os

app = Flask(__name__)

# --- 1. Load Data at Startup (Correct Render Path Logic) ---
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir))
pnr_file_path = os.path.join(project_root, 'data', 'pnr_database.csv')
stations_file_path = os.path.join(project_root, 'data', 'stations_original.csv')
db_path = os.path.join(project_root, 'railmadad.db')

print(f"Looking for PNR data at: {pnr_file_path}")
print(f"Looking for Station data at: {stations_file_path}")
print(f"Looking for DB at: {db_path}")

# Load PNR Data
try:
    # --- FIX 1: Using your new column name 'PNR' ---
    pnr_data = pd.read_csv(pnr_file_path, index_col='PNR') 
    print("✅ PNR dataset loaded successfully.")
except Exception as e:
    print(f"❌ ERROR loading PNR data: {e}")
    pnr_data = None

# Load Station Data
try:
    station_data = pd.read_csv(stations_file_path)
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
    # This is handled by Dialogflow static response.
    return {"fulfillmentText": "Error: Phone handler was called, but should be static."}

def handle_station_search(request_json):
    """Handles the 'provide_station_name' intent."""
    user_input = request_json['queryResult']['parameters'].get('station_input', '').lower()
    if station_data is None:
        return {"fulfillmentText": "Error: Station database is not loaded. Please contact support."}
    station_match = station_data[
        (station_data['id_code'] == user_input) | 
        (station_data['station'] == user_input)
    ]
    if not station_match.empty:
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
        # This is the error that was happening
        return {"fulfillmentText": "Error: PNR database is not loaded. Please check server logs."}
    try:
        pnr_num_str = str(int(float(pnr_str)))
        padded_pnr_num = pnr_num_str.zfill(10)
        pnr_to_check = f"PNR{padded_pnr_num}"
        
        if pnr_to_check in pnr_data.index:
            pnr_list = list(pnr_to_check)
            random.shuffle(pnr_list)
            token = "".join(pnr_list)
            pnr_details = pnr_data.loc[pnr_to_check]
            
            # --- FIX 2: Using your new column name 'Train_No' ---
            train_no = pnr_details['Train_No'] 

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

def categorize_complaint(complaint_text):
    """Analyzes complaint text to route it to a department."""
    text = complaint_text.lower()
    food_keywords = ['food', 'overpriced', 'irctc', 'pantry', 'water', 'tea', 'meal', 'catering']
    if any(keyword in text for keyword in food_keywords):
        return "IRCTC Department"
    cleaning_keywords = ['clean', 'dirty', 'filthy', 'hygiene', 'washroom', 'toilet', 'coach', 'stink']
    if any(keyword in text for keyword in cleaning_keywords):
        return "Cleaning Department"
    ticket_keywords = ['ticket', 'tc', 'tte', 'ticketless', 'no ticket', 'collector']
    if any(keyword in text for keyword in ticket_keywords):
        return "TICKET COLLECTOR Department"
    return "General Operations"

def handle_complaint_logging(request_json):
    """Handles the final 'capture_complaint_description' intent."""
    try:
        complaint_text = request_json['queryResult']['parameters'].get('complaint_text', '')
        pnr = ""
        token = ""
        station = ""
        phone_number = ""
        
        contexts = request_json['queryResult']['outputContexts']
        for c in contexts:
            if 'awaiting-complaint-description' in c['name']:
                params = c.get('parameters', {})
                pnr = params.get('pnr', '')
                token = params.get('complaint_token', '')
                station = params.get('station_confirmed', '')
            if 'awaiting-location' in c['name']:
                phone_number = c['parameters'].get('phone_number', '')

        department = categorize_complaint(complaint_text)
        
        if pnr:
            station = ""
        if station:
            pnr = ""
            token = ""

        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO complaints (phone_number, pnr, token, station, complaint_text, department) VALUES (?, ?, ?, ?, ?, ?)",
            (phone_number, pnr, token, station, complaint_text, department)
        )
        conn.commit()
        new_complaint_id = cursor.lastrowid
        conn.close()

        response_text = f"Thank you. Your complaint (ID: C-{new_complaint_id}) has been successfully routed to the {department}."
        return {
            "fulfillmentText": response_text,
            "outputContexts": [] # Clear contexts to end the conversation
        }
    except Exception as e:
        print(f"Error in complaint logging: {e}")
        return {"fulfillmentText": "Sorry, there was an error lodging your complaint. Please try again."}

# --- 3. Main Webhook Router ---
@app.route('/webhook', methods=['POST'])
def dialogflow_webhook():
    request_json = request.get_json()
    try:
        intent_name = request_json['queryResult']['intent']['displayName']
    except Exception:
        return jsonify({"fulfillmentText": "Error: Invalid request."})

    if intent_name == 'capture_user_query':
        return jsonify(handle_query_intent(request_json))
    elif intent_name == 'provide_phone_number':
        return jsonify({"fulfillmentText": "Error: Phone handler was called, but should be static."})
    elif intent_name == 'provide_station_name':
        return jsonify(handle_station_search(request_json))
    elif intent_name == 'user_confirms_station_yes':
        return jsonify(handle_station_confirmed(request_json))
    elif intent_name == 'provide_pnr':
        return jsonify(handle_pnr_verification(request_json))
    elif intent_name == 'capture_complaint_description':
        return jsonify(handle_complaint_logging(request_json))
    else:
        return jsonify({"fulfillmentText": "Error: Unrecognized intent in webhook."})

# --- 4. Run the Server ---
if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=True)