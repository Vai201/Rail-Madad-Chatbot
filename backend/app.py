# backend/app.py
import random
import re
import pandas as pd
from flask import Flask, request, jsonify
import sqlite3
import os

app = Flask(__name__)

# --- 1. Define Paths ---
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir))
pnr_file_path = os.path.join(project_root, 'data', 'pnr_database.csv')
stations_file_path = os.path.join(project_root, 'data', 'stations_original.csv')
db_path = os.path.join(project_root, 'railmadad.db')

print(f"Looking for PNR data at: {pnr_file_path}")
print(f"Looking for Station data at: {stations_file_path}")
print(f"Looking for DB at: {db_path}")

# --- 2. RUN DATABASE SETUP ---
# This runs EVERY time the server starts, ensuring the tables always exist.
def setup_database():
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS queries (
            query_id INTEGER PRIMARY KEY AUTOINCREMENT,
            query_text TEXT NOT NULL,
            status TEXT DEFAULT 'Open',
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
        );
        ''')
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS complaints (
            complaint_id INTEGER PRIMARY KEY AUTOINCREMENT,
            phone_number TEXT,
            pnr TEXT,
            token TEXT,
            station TEXT,
            complaint_text TEXT NOT NULL,
            department TEXT, 
            status TEXT DEFAULT 'Open',
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
        );
        ''')
        print("✅ Database tables checked/created successfully.")
        conn.commit()
        conn.close()
    except Exception as e:
        print(f"❌ ERROR setting up database: {e}")

setup_database() # Run the setup function on startup

# --- 3. Load Data at Startup ---
try:
    pnr_data = pd.read_csv(pnr_file_path, index_col='PNR') 
    print("✅ PNR dataset loaded successfully.")
except Exception as e:
    print(f"❌ ERROR loading PNR data: {e}")
    pnr_data = None

try:
    station_data_raw = pd.read_csv(stations_file_path, quotechar='"') 
    station_data_processed = station_data_raw.copy()
    station_data_processed['station'] = station_data_processed['station'].str.lower()
    station_data_processed['id_code'] = station_data_processed['id_code'].str.lower()
    print("✅ Station dataset loaded successfully.")
except Exception as e:
    print(f"❌ ERROR loading Station data: {e}")
    station_data_raw = None
    station_data_processed = None

# --- 4. Helper Functions for Chatbot ---

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
    user_input = request_json['queryResult']['parameters'].get('station_input', '').lower().strip('"')
    if station_data_processed is None:
        return {"fulfillmentText": "Error: Station database is not loaded. Please contact support."}
    
    station_match = station_data_processed[
        (station_data_processed['id_code'] == user_input) | 
        (station_data_processed['station'] == user_input)
    ]
    
    if not station_match.empty:
        original_station_name = station_data_raw.iloc[station_match.index[0]].get('station')
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
    
    # --- BUG FIX 2: Added 'bad' to the food keywords ---
    food_keywords = ['food', 'overpriced', 'overcharged', 'irctc', 'pantry', 'water', 'tea', 'meal', 'catering', 'bad food']
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
            "outputContexts": [] 
        }
    except Exception as e:
        print(f"Error in complaint logging: {e}")
        return {"fulfillmentText": "Sorry, there was an error lodging your complaint. Please try again."}

# --- 5. Main Webhook Router ---
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

# --- 6. ADMIN DASHBOARD PAGES ---

def get_db_as_html_table(query):
    """Helper function to query the DB and return an HTML table."""
    try:
        # --- BUG FIX 3: Run the setup function here to guarantee tables exist ---
        setup_database() 
        conn = sqlite3.connect(db_path)
        df = pd.read_sql_query(query, conn)
        conn.close()
        return df.to_html(index=False, border=1, classes="table table-striped")
    except Exception as e:
        return f"<p>Error reading database: {e}. (The table may be empty.)</p>"

def get_page_template(title, table_html):
    """Helper function to wrap the tables in a styled HTML page."""
    return f"""
    <html>
        <head>
            <title>{title}</title>
            <style>
                body {{ font-family: Arial, sans-serif; padding: 20px; }}
                h1 {{ color: #333; }}
                .table {{ width: 100%; border-collapse: collapse; margin-top: 20px; }}
                .table th, .table td {{ padding: 8px; text-align: left; border: 1px solid #ddd; }}
                .table th {{ background-color: #f2f2f2; }}
                .table tr:nth-child(even) {{ background-color: #f9f9f9; }}
                a {{ font-size: 1.2em; }}
            </style>
        </head>
        <body>
            <h1>{title}</h1>
            <p><a href="/admin">Back to Admin Dashboard</a></p>
            {table_html}
        </body>
    </html>
    """

@app.route('/admin')
def admin_dashboard():
    """Main admin page with links to the data."""
    return """
    <html>
        <head><title>Admin Dashboard</title></head>
        <body style="font-family: Arial, sans-serif; padding: 30px;">
            <h1>Rail Madad Admin Dashboard</h1>
            <p>Select a database to view:</p>
            <ul>
                <li><a href="/view-complaints" style="font-size: 1.5em;">View Complaints Log</a></li>
                <li><a href="/view-pnrs" style="font-size: 1.5em;">View PNR Database (Sample)</a></li>
                <li><a href="/view-stations" style="font-size: 1.5em;">View Station Database (Sample)</a></li>
            </ul>
        </body>
    </html>
    """

@app.route('/view-complaints')
def view_complaints():
    """Shows the complaints table."""
    query = "SELECT * FROM complaints ORDER BY timestamp DESC"
    table_html = get_db_as_html_table(query)
    return get_page_template("Complaints Log", table_html)

@app.route('/view-pnrs')
def view_pnrs():
    """Shows a sample of the PNR CSV."""
    if pnr_data is None:
        return "<p>Error: PNR data is not loaded.</p>"
    table_html = pnr_data.head(100).reset_index().to_html(index=False, border=1, classes="table table-striped")
    return get_page_template("PNR Database (First 100 Rows)", table_html)

@app.route('/view-stations')
def view_stations():
    """Shows a sample of the Station CSV."""
    if station_data_raw is None:
        return "<p>Error: Station data is not loaded.</p>"
    table_html = station_data_raw.head(100).to_html(index=False, border=1, classes="table table-striped")
    return get_page_template("Station Database (First 100 Rows)", table_html)

# --- 7. Run the Server ---
if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=True)