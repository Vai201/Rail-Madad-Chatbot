# backend/app.py
import random
import re
import pandas as pd
from flask import Flask, request, jsonify
import psycopg2
import os
from dotenv import load_dotenv # <-- Add this line near your other imports

load_dotenv() # <-- Add this line right after your imports

app = Flask(__name__)

@app.route('/')
def home():
    return "Rail Madad Chatbot Backend is Live!"

# --- 1. Define Paths & Cloud DB Credentials ---
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir))
pnr_file_path = os.path.join(project_root, 'data', 'pnr_database.csv')
stations_file_path = os.path.join(project_root, 'data', 'stations_original.csv')

# 👇 ADD YOUR GOOGLE CLOUD SQL DETAILS HERE 👇
DB_HOST = os.getenv("DB_HOST") 
DB_NAME = "postgres"
DB_USER = "postgres"
DB_PASS = os.getenv("DB_PASS")

def get_db_connection():
    # We use the /cloudsql/ prefix followed by your Instance Connection Name
    return psycopg2.connect(
        database="postgres",
        user="postgres",
        password=os.getenv("DB_PASS"), 
        host="/cloudsql/project-f988ee73-0741-4016-82c:asia-south1:rail-madad-db"
    )

print(f"Looking for PNR data at: {pnr_file_path}")
print(f"Looking for Station data at: {stations_file_path}")
print(f"Connecting to Cloud SQL at: {DB_HOST}")

# --- 2. RUN DATABASE SETUP ---
# --- 2. RUN DATABASE SETUP ---
def setup_database():
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS bot_queries (
            query_id SERIAL PRIMARY KEY,
            query_text TEXT NOT NULL,
            status TEXT DEFAULT 'Open',
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        ''')
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS bot_complaints (
            complaint_id SERIAL PRIMARY KEY,
            phone_number TEXT,
            pnr TEXT,
            token TEXT,
            station TEXT,
            travel_date TEXT, 
            complaint_text TEXT NOT NULL,
            department TEXT, 
            agency TEXT,
            status TEXT DEFAULT 'Open',
            closing_statement TEXT,
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        ''')
        # New table to hold your PNR dataset
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS pnr_records (
            pnr_number TEXT PRIMARY KEY,
            train_no TEXT,
            date_of_travel TEXT
        );
        ''')
        conn.commit()
        conn.close()
        print("✅ Cloud Database schema verified.")
        cleanup_old_complaints()
    except Exception as e:
        print(f"❌ ERROR setting up database: {e}")
        
def cleanup_old_complaints():
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # SQL query to delete rows older than 6 months that are 'Closed'
        # AND are NOT part of the Medical or RPF departments
        cleanup_query = '''
            DELETE FROM bot_complaints 
            WHERE status = 'Closed' 
            AND timestamp < CURRENT_TIMESTAMP - INTERVAL '6 months'
            AND department NOT IN ('Medical Assistance', 'RPF/Security');
        '''
        
        cursor.execute(cleanup_query)
        deleted_count = cursor.rowcount # Check how many rows were actually deleted
        
        conn.commit()
        conn.close()
        
        if deleted_count > 0:
            print(f"🧹 DATA RETENTION: Automatically cleared {deleted_count} old closed complaints.")
            
    except Exception as e:
        print(f"❌ ERROR during automated database cleanup: {e}")
# --- 3. Load Data at Startup ---
'''try:
    pnr_data = pd.read_csv(pnr_file_path, index_col='PNR') 
    print("✅ PNR dataset loaded successfully.")
except Exception as e:
    print(f"❌ ERROR loading PNR data: {e}")
    pnr_data = None'''
pnr_data = None # Placeholder to prevent errors in other parts of the script

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
    user_query_text = request_json['queryResult']['parameters']['user_query']
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("INSERT INTO bot_queries (query_text) VALUES (%s) RETURNING query_id", (user_query_text,))
    new_query_id = cursor.fetchone()[0]
    conn.commit()
    conn.close()
    response_text = f"Thank you. Your query has been registered with ID: Q-{new_query_id}."
    return {"fulfillmentText": response_text}

def handle_phone_number(request_json):
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
    user_input = request_json['queryResult']['parameters'].get('station_input', '').lower().strip('"')
    
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        # Search by code or name in the SQL table
        cursor.execute("SELECT station_name FROM stations WHERE id_code = %s OR LOWER(station_name) = %s", (user_input, user_input))
        result = cursor.fetchone()
        conn.close()
        
        if result:
            original_station_name = result[0]
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
    except Exception as e:
        print(f"Error in station search: {e}")
        return {"fulfillmentText": "Station database error. Please try again later."}

def handle_station_confirmed(request_json):
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
    # 1. Get the PNR from Dialogflow parameters
    pnr_input = request_json['queryResult']['parameters'].get('pnr_number', '')
    
    # 2. Clean the input (remove "PNR" prefix if user typed it, keep only digits)
    pnr_digits = "".join(re.findall(r'\d', str(pnr_input)))
    
    try:
        # 3. Connect to SQL and search the new pnr_records table
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT train_no, date_of_travel FROM pnr_records WHERE pnr_number = %s", (pnr_digits,))
        result = cursor.fetchone()
        conn.close()

        if result:
            train_no, travel_date = result
            # Create a unique token for this session
            token = f"TK-{random.randint(1000, 9999)}"
            
            response_text = f"PNR verified for Train {train_no} on {travel_date}. Your complaint token is {token}. Please describe your complaint."
            
            return {
                "fulfillmentText": response_text,
                "outputContexts": [
                    {
                        "name": f"{request_json['session']}/contexts/awaiting-complaint-description",
                        "lifespanCount": 1,
                        "parameters": {
                            "complaint_token": token,
                            "pnr": pnr_digits,
                            "travel_date": travel_date 
                        }
                    }
                ]
            }
        else:
            # This triggers if the PNR isn't in your SQL table yet
            return {"fulfillmentText": f"PNR {pnr_digits} not found. Please ensure you have imported your CSV to the Cloud SQL 'pnr_records' table."}
            
    except Exception as e:
        print(f"Error in PNR check: {e}")
        return {"fulfillmentText": "System error connecting to database. Please try again."}

def categorize_complaint(complaint_text):
    text = complaint_text.lower()
    
    mapping = {
        "Security": ['theft', 'harassment', 'unauthorized', 'rpf', 'police', 'fight', 'stolen', 'security'],
        "Sanitation & Cleaning": ['dirty', 'toilet', 'washroom', 'cleaning', 'filthy', 'stink', 'garbage'],
        "Catering & Food": ['food', 'pantry', 'overcharged', 'meal', 'catering', 'bad food', 'water bottle'],
        "Maintenance & Electrical": ['ac', 'fan', 'light', 'charging', 'broken seat', 'window', 'electrical'],
        "Ticketing & Refunds": ['tte', 'ticket', 'refund', 'booking', 'seat allotment', 'collector'],
        "Medical Assistance": ['doctor', 'medical', 'emergency', 'sick', 'injury', 'medicine', 'faint'],
        "Luggage & Parcels": ['luggage', 'parcel', 'lost bag', 'damaged bag', 'delayed luggage'],
        "Staff Behavior": ['rude', 'staff', 'unprofessional', 'behavior', 'shouting'],
        "Water Supply": ['no water', 'tap', 'dry', 'water supply']
    }

    for dept, keywords in mapping.items():
        if any(k in text for k in keywords):
            return dept
            
    return "General" # Fallback instead of Train Delays

def get_agency_name(pnr_str):
    try:
        # Extract numeric part of PNR (e.g., PNR0000001234 -> 1234)
        pnr_num = int(re.search(r'\d+', pnr_str).group())
        if pnr_num <= 5000: return "Agency 1"
        elif pnr_num <= 10000: return "Agency 2"
        elif pnr_num <= 15000: return "Agency 3"
        elif pnr_num <= 20000: return "Agency 4"
        elif pnr_num <= 25000: return "Agency 5"
        else: return "Agency 6"
    except:
        return "Internal Staff"

def get_random_closing_statement(dept):
    statements = {
        "Catering & Food": [
            "The Pantry management has been fined ₹10 Lakhs.",
            "The catering contract has been terminated due to hygiene violations.",
            "Strict warning issued to the service provider."
        ],
        "Sanitation & Cleaning": [
            "The issue has been resolved; the coach has been deep cleaned.",
            "On-board housekeeping staff has been penalized.",
            "Water and sanitation levels restored."
        ],
        "Maintenance & Electrical": [
            "The electrical fault has been rectified by the technician.",
            "The component has been replaced; AC/Lights are now functional.",
            "Issue noted; maintenance will be completed at the primary depot."
        ],
        "Security": [
            "The RPF has been informed and is investigating.",
            "Action has been taken by the on-duty RPF personnel.",
            "Security patrol has been increased in the affected coach."
        ],
        "Medical Assistance": [
            "The doctor will be attending to the passenger at the next station.",
            "Medical help has been provided to the person in need.",
            "Emergency medical services have been alerted."
        ],
        "General": ["The complaint will be attended by our support team shortly."],
        "Default": ["The issue has been resolved and verified."]
    }
    # Fallback for departments not explicitly listed
    if dept in ["Water Supply", "Maintenance & Electrical"]:
        return random.choice(statements["Sanitation & Cleaning"])
    
    return random.choice(statements.get(dept, statements["Default"]))

def handle_complaint_logging(request_json):
    try:
        parameters = request_json['queryResult']['parameters']
        complaint_text = parameters.get('complaint_text', '')
        
        # 1. Initialize variables and retrieve from Dialogflow Contexts
        pnr = ""
        token = ""
        station = ""
        phone_number = ""
        travel_date = ""
        
        contexts = request_json['queryResult']['outputContexts']
        for c in contexts:
            if 'awaiting-complaint-description' in c.get('name', ''):
                params = c.get('parameters', {})
                pnr = params.get('pnr', '') 
                token = params.get('complaint_token', '')
                station = params.get('station_confirmed', '')
                travel_date = params.get('travel_date', '')
            if 'awaiting-location' in c.get('name', ''):
                phone_number = c.get('parameters', {}).get('phone_number', '')

        # 2. Identify Department (Categorization)
        dept = categorize_complaint(complaint_text)
        
        # 3. Agency Assignment Logic
        # Assigns Agency based on PNR range as per your original requirement
        agency = "Internal Staff"
        if pnr:
            try:
                pnr_match = re.search(r'\d+', pnr)
                if pnr_match:
                    pnr_num = int(pnr_match.group())
                    if pnr_num <= 5000: agency = "Agency 1"
                    elif pnr_num <= 10000: agency = "Agency 2"
                    elif pnr_num <= 15000: agency = "Agency 3"
                    elif pnr_num <= 20000: agency = "Agency 4"
                    elif pnr_num <= 25000: agency = "Agency 5"
                    else: agency = "Agency 6"
            except Exception as e:
                print(f"Agency assignment error: {e}")

        # 4. PRIVACY LOGIC: Full Data vs. Redacted
        if dept in ["Security", "Medical Assistance"]:
            pnr_to_store = pnr  # Full PNR for RPF/Medical
        else:
            pnr_to_store = f"REDACTED ({token})" # Hidden for others

        # 5. Mock Resolution Logic (Randomly closing some complaints)
        status = "Open"
        closing_msg = ""
        if random.random() < 0.3: # 30% chance to be auto-resolved for the demo
            status = "Closed"
            closing_msg = get_random_closing_statement(dept)

        # 6. Save to Cloud Database
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute(
            """INSERT INTO bot_complaints 
               (phone_number, pnr, token, station, travel_date, complaint_text, department, agency, status, closing_statement) 
               VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s) RETURNING complaint_id""",
            (phone_number, pnr_to_store, token, station, travel_date, complaint_text, dept, agency, status, closing_msg)
        )
        new_id = cursor.fetchone()[0]
        conn.commit()
        conn.close()

        # 7. Final Response to User
        msg = f"Complaint registered (ID: C-{new_id}) routed to {dept} ({agency})."
        if status == "Closed":
            msg += f" Update: {closing_msg}"
            
        return {"fulfillmentText": msg}

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
        return jsonify(handle_phone_number(request_json))
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

@app.route('/api/track', methods=['POST'])
def track_by_phone():
    data = request.get_json()
    phone_number = data.get('phone_number', '')

    if not phone_number:
        return jsonify({"error": "Phone number is required"}), 400

    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Fetch all complaints linked to this exact phone number
        cursor.execute(
            "SELECT complaint_id, department, status, timestamp, complaint_text FROM bot_complaints WHERE phone_number = %s ORDER BY timestamp DESC",
            (phone_number,)
        )
        records = cursor.fetchall()
        conn.close()

        if not records:
            return jsonify({"message": "No complaints found for this number.", "complaints": []})

        # Package the data neatly for your HTML/JS frontend to read
        complaints_list = []
        for row in records:
            complaints_list.append({
                "id": f"C-{row[0]}",
                "department": row[1],
                "status": row[2],
                "date": row[3].strftime("%Y-%m-%d %H:%M"),
                "description": row[4]
            })

        return jsonify({"message": "Success", "complaints": complaints_list})

    except Exception as e:
        print(f"Error fetching tracking data: {e}")
        return jsonify({"error": "Database error"}), 500

# --- 6. ADMIN DASHBOARD PAGES ---
def get_db_as_html_table(query):
    try:
        setup_database() 
        conn = get_db_connection()
        import warnings
        with warnings.catch_warnings():
            warnings.simplefilter('ignore', UserWarning)
            df = pd.read_sql_query(query, conn)
        conn.close()
        if df.empty:
            return "<p>No complaints found in the log.</p>"
        return df.to_html(index=False, border=1, classes="table table-striped")
    except Exception as e:
        return f"<p>Error reading database: {e}. (The table may be empty.)</p>"

def get_page_template(title, table_html):
    return f"""
    <html>
        <head>
            <title>{title}</title>
            <style>
                body {{ font-family: Arial, sans-serif; padding: 20px; line-height: 1.6; }}
                h1 {{ color: #333; }}
                
                /* This container makes the table scrollable side-to-side */
                .table-container {{ overflow-x: auto; width: 100%; border: 1px solid #ddd; box-shadow: 0 4px 8px rgba(0,0,0,0.1); }}
                
                /* The table itself */
                .table {{ width: 100%; border-collapse: collapse; margin-top: 0; white-space: nowrap; }}
                .table th, .table td {{ padding: 12px 16px; text-align: left; border-bottom: 1px solid #ddd; }}
                
                /* Blue sticky header so it stays visible when scrolling down */
                .table th {{ background-color: #1a73e8; color: white; position: sticky; top: 0; z-index: 10; }}
                
                /* Alternating row colors for readability */
                .table tr:nth-child(even) {{ background-color: #f8f9fa; }}
                .table tr:hover {{ background-color: #f1f1f1; }}
                
                a {{ font-size: 1.2em; color: #1a73e8; text-decoration: none; display: inline-block; margin-bottom: 15px; }}
                a:hover {{ text-decoration: underline; }}
            </style>
        </head>
        <body>
            <h1>{title}</h1>
            <p><a href="/admin">⬅ Back to Admin Dashboard</a></p>
            
            <div class="table-container">
                {table_html}
            </div>
            
        </body>
    </html>
    """

@app.route('/admin')
def admin_dashboard():
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
    query = "SELECT * FROM bot_complaints ORDER BY timestamp DESC"
    table_html = get_db_as_html_table(query)
    return get_page_template("Complaints Log", table_html)

@app.route('/view-pnrs')
def view_pnrs():
    # Fetch data directly from the SQL table
    query = "SELECT * FROM pnr_records LIMIT 100"
    table_html = get_db_as_html_table(query)
    
    # If the table is empty, show a helpful message
    if "No complaints found" in table_html or "error" in table_html.lower():
        table_html = "<p>No PNR records found. Please import your CSV into the 'pnr_records' table in Cloud SQL.</p>"
        
    return get_page_template("PNR Database (SQL Cloud Storage)", table_html)

@app.route('/view-stations')
def view_stations():
    # This now asks the SQL database instead of looking for a CSV file
    query = "SELECT * FROM stations LIMIT 100" 
    table_html = get_db_as_html_table(query)
    return get_page_template("Station Database (First 100 Rows)", table_html)

# --- 7. Run the Server ---
if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=True)