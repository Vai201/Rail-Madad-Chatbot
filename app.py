# backend/app.py
import random
import re
import pandas as pd
from flask import Flask, request, jsonify
from flask_cors import CORS
import psycopg2
import os
import json
import google.generativeai as genai
from dotenv import load_dotenv # <-- Add this line near your other imports

load_dotenv() # <-- Add this line right after your imports

# Configure Gemini instantly
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))

app = Flask(__name__)
CORS(app)
@app.route('/')
def home():
    return "Rail Madad Chatbot Backend is Live!"

# --- 1. Define Paths & Cloud DB Credentials ---
# --- 1. Define Paths & Cloud DB Credentials ---
# We removed os.pardir so it stays inside the rail_madad_chatbot folder
project_root = os.path.abspath(os.path.dirname(__file__))

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
# --- 3. Load Data at Startup ---
# We no longer load CSVs locally because we migrated to Cloud SQL!
pnr_data = None 
station_data_raw = None
station_data_processed = None
print("✅ Skipping local CSV load - connected directly to Cloud SQL.")

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
                    "lifespanCount": 10,
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
    session_id = request_json['session']
    
    try:
        # Note: In your original code you queried a table named 'stations'. 
        # Make sure this table exists in your Cloud SQL! 
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute(
            "SELECT station FROM stations WHERE id_code = %s OR station ILIKE %s OR station ILIKE %s", 
            (user_input, f"%{user_input}%", f"{user_input} %")
        )
        result = cursor.fetchone()
        conn.close()
        
        if result:
            original_station_name = result[0]
            return {
                "fulfillmentText": f"Did you mean '{original_station_name}'?",
                "outputContexts": [
                    {
                        "name": f"{session_id}/contexts/awaiting-station-confirmation",
                        "lifespanCount": 1,
                        "parameters": {"station_confirmed": original_station_name}
                    }
                ]
            }
        else:
            # If not found, tell the user AND kill the context so they aren't stuck in a loop
            return {
                "fulfillmentText": "Sorry, I couldn't find that station in the database. Please type 'hi' to start over or try another name.",
                "outputContexts": [
                     {
                         # Setting lifespanCount to 0 clears the current context memory
                        "name": f"{session_id}/contexts/awaiting-location",
                        "lifespanCount": 0 
                     }
                ]
            }
    except Exception as e:
        print(f"Error in station search: {e}")
        return {
            "fulfillmentText": "Station database error. Please type 'hi' to restart your complaint.",
            "outputContexts": [
                 {
                    "name": f"{session_id}/contexts/awaiting-location",
                    "lifespanCount": 0 
                 }
            ]
        }

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
    
    # Safely handle Dialogflow's float conversion (e.g., turning 51.0 or "51.0" into "51")
    pnr_input_str = str(pnr_input)
    if "." in pnr_input_str:
        pnr_input_str = pnr_input_str.split(".")[0]
        
    # 2. Extract just the digits
    pnr_digits = "".join(re.findall(r'\d', pnr_input_str))
    
    # 🚨 NEW STRICT CHECK: If it is not exactly 10 digits, reject it instantly!
    if len(pnr_digits) != 10:
        return {"fulfillmentText": f"Invalid PNR length. You entered {len(pnr_digits)} digits. Please provide a valid 10-digit PNR number."}
    
    # Format the PNR to match your database format (e.g., "PNR0000003333")
    db_pnr_format = f"PNR{pnr_digits}"
    
    try:
        # 3. Connect to SQL and search using the exact database format
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT train_no, date_of_travel FROM pnr_records WHERE pnr_number = %s", (db_pnr_format,))
        result = cursor.fetchone()
        conn.close()

        if result:
            train_no, travel_date = result
            
            # Create a token by shuffling the user's actual PNR digits
            pnr_list = list(pnr_digits)
            random.shuffle(pnr_list)
            shuffled_pnr = "".join(pnr_list)
            token = f"TK-{shuffled_pnr[:6]}" # Uses the first 6 shuffled digits
            
            # Hide the token from the user, just ask for the complaint
            response_text = f"PNR verified for Train {train_no} on {travel_date}. Please describe your complaint."
            
            return {
                "fulfillmentText": response_text,
                "outputContexts": [
                    {
                        "name": f"{request_json['session']}/contexts/awaiting-complaint-description",
                        "lifespanCount": 1,
                        "parameters": {
                            "complaint_token": token,  # The token lives secretly in the background here!
                            "pnr": db_pnr_format, 
                            "travel_date": travel_date 
                        }
                    }
                ]
            }
        else:
            # Tell the user the exact PNR wasn't found
            return {"fulfillmentText": f"{db_pnr_format} not found in the database. Please check your ticket and try again."}
            
    except Exception as e:
        print(f"Error in PNR check: {e}")
        return {"fulfillmentText": "System error connecting to database. Please try again."}

def syntax_router(text):
    """The fast, 0ms keyword matcher for standard complaints."""
    text = text.lower()
    mapping = {
        "Sanitation & Cleaning": ['dirty', 'toilet', 'washroom', 'cleaning', 'filthy', 'stink', 'garbage'],
        "Catering & Food": ['food', 'pantry', 'overcharged', 'meal', 'catering', 'bad food', 'water bottle'],
        "Maintenance & Electrical": ['ac', 'fan', 'light', 'charging', 'broken seat', 'window', 'electrical'],
        "Ticketing & Refunds": ['tte', 'ticket', 'refund', 'booking', 'seat allotment', 'collector'],
        "Luggage & Parcels": ['luggage', 'parcel', 'lost bag', 'damaged bag', 'delayed luggage'],
        "Staff Behavior": ['rude', 'staff', 'unprofessional', 'behavior', 'shouting'],
        "Water Supply": ['no water', 'tap', 'dry', 'water supply']
    }
    for dept, keywords in mapping.items():
        if any(k in text for k in keywords):
            return dept
    return None # Return None if it's confusing, forcing it to Gemini

def neural_router(complaint_text):
    """Fully dynamic LLM router for complex cases, emergencies, and safety tips."""
    import json
    import re
    
    valid_departments = [
        "Security", "Medical Assistance", "Sanitation & Cleaning", 
        "Maintenance & Electrical", "General" 
    ]
    
    # ADDED: Anti-overfitting instructions to force dynamic, unique advice
    prompt = f"""You are a backend routing API for Indian Railways. You receive a complaint and output ONLY raw JSON. 
    Complaint: "{complaint_text}"
    Valid Departments: {', '.join(valid_departments)}
    
    Rules for 'advice' field:
    1. If "Medical Assistance": Provide 1 sentence of highly actionable, practical first-aid steps the bystander can do right now to help.
    2. If "Security": Provide 1 sentence of tactical safety advice.
    3. If any other department: The advice field MUST be "".
    
    CRITICAL: Generate unique advice based on the passenger's exact situation. Do NOT copy the example text below. Do NOT say "Here is the JSON". Start exactly with {{ and end with }}.
    
    Example format:
    {{"department": "Medical Assistance", "advice": "Loosen their collar, elevate their legs, and clear the area."}}
    """
    
    try:
        # THE FIX: Gemma 3 27B (14,400 RPD Quota)
        model = genai.GenerativeModel('models/gemma-3-27b-it')
        
        safety_settings = [
            {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_NONE"},
            {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_NONE"},
            {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_NONE"},
            {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_NONE"}
        ]
        
        # THE FIX: Removed the JSON mime-type so Gemma stops throwing 500 errors
        response = model.generate_content(
            prompt, 
            safety_settings=safety_settings,
            generation_config={
                "max_output_tokens": 300 
            }
        )
        
        if not response.text:
            return "General", ""

        raw_response = response.text.strip()
        print(f"DEBUG GEMINI RAW: {raw_response}") 
        
        # Our Regex hunter will perfectly extract the JSON from the raw text
        match = re.search(r'\{.*\}', raw_response, re.DOTALL)
        
        if match:
            clean_json_string = match.group(0)
            data = json.loads(clean_json_string)
            dept = data.get("department", "General")
            advice = data.get("advice", "")
            
            if dept not in valid_departments:
                dept = "General"
                
            return dept, advice
        else:
            print("CRITICAL: No JSON brackets found in Gemini response.")
            return "General", ""
            
    except Exception as e:
        print(f"CRITICAL GEMINI ERROR: {e}")
        return "General", ""
            
    except Exception as e:
        print(f"CRITICAL GEMINI ERROR: {e}")
        return "General", ""

def categorize_complaint(complaint_text):
    """Dynamic routing that uses Syntax for speed, and AI for complexity."""
    
    # 1. Try Syntax Router first for simple, obvious things (e.g., "fan not working")
    syntax_dept = syntax_router(complaint_text)
    if syntax_dept:
        return syntax_dept, "" 
        
    # 2. If it's weird, complex, or an emergency, let the AI dynamically think!
    return neural_router(complaint_text)

def categorize_complaint(complaint_text):
    """Routes the complaint based on speed, cost, and emergency status."""
    
    # RULE 1: Is it an obvious emergency? Force it to the Neural AI for tips!
    emergency_keywords = ['police', 'stolen', 'harassment', 'doctor', 'faint', 'sick', 'blood', 'emergency', 'fight', 'creepy']
    is_emergency = any(word in complaint_text.lower() for word in emergency_keywords)
    
    if is_emergency:
        dept, advice = neural_router(complaint_text)
        if dept: return dept, advice
    
    # RULE 2: Not an emergency? Try the 0ms Syntax Router first.
    syntax_dept = syntax_router(complaint_text)
    if syntax_dept:
        return syntax_dept, "" # Fast categorization, no advice needed
        
    # RULE 3: Syntax failed (vague/weird text)? Fallback to Neural AI.
    dept, advice = neural_router(complaint_text)
    if dept:
        return dept, advice
        
    # RULE 4: If EVERYTHING fails (Gemini API quota is 0 AND syntax failed), return General
    return "General", ""

def get_agency_name(pnr_str):
    try:
        # Extract numeric part of PNR (e.g., PNR0000001234 -> 1234)
        pnr_num = int(re.search(r'\d+', pnr_str).group())
        if pnr_num <= 5000: agency = "M/s Ambuj Hotel Pvt. Ltd"
        elif pnr_num <= 10000: agency = "M/s. R.K.Associates & Hoteliers Pvt.Ltd"
        elif pnr_num <= 15000: agency = " M/s. Boon Catg. Co."
        elif pnr_num <= 20000: agency = "M/s A.S Sales Corporation"
        elif pnr_num <= 25000: agency = "M/s. Rathour Services"
        else: agency = "M/s. A. A. Catg. Co"
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

        contexts = request_json['queryResult'].get('outputContexts', []) 
        for c in contexts:
            params = c.get('parameters', {})
            
            # Priority 1: Grab phone number wherever it appears in memory
            if not phone_number:
                phone_number = params.get('phone_number', '')
            
            # Priority 2: Grab specific complaint details
            if 'awaiting-complaint-description' in c.get('name', ''):
                pnr = params.get('pnr', pnr) 
                token = params.get('complaint_token', token)
                station = params.get('station_confirmed', station)
                if not travel_date:
                    travel_date = params.get('travel_date', '')

        # 2. Identify Department (Categorization)
        dept, advice_tip = categorize_complaint(complaint_text)
        
        # 3. Agency Assignment Logic
        agency = "Internal Staff"
        if pnr:
            try:
                pnr_match = re.search(r'\d{10}', pnr) 
                if pnr_match:
                    pnr_num = int(pnr_match.group())
                    if pnr_num <= 5000: agency = "M/s Ambuj Hotel Pvt. Ltd"
                    elif pnr_num <= 10000: agency = "M/s. R.K.Associates & Hoteliers Pvt.Ltd"
                    elif pnr_num <= 15000: agency = " M/s. Boon Catg. Co."
                    elif pnr_num <= 20000: agency = "M/s A.S Sales Corporation"
                    elif pnr_num <= 25000: agency = "M/s. Rathour Services"
                    else: agency = "M/s. A. A. Catg. Co"
                else:
                    # If it's not 10 digits, we can handle it or log it as invalid
                    print(f"Invalid PNR length detected: {pnr}")
            except Exception as e:
                print(f"Agency assignment error: {e}")

        # 4. PRIVACY LOGIC: Full Data vs. Redacted
        if dept in ["Security", "Medical Assistance"]:
            pnr_to_store = pnr  # Full PNR for RPF/Medical
        else:
            pnr_to_store = f"REDACTED ({token})" # Hidden for others

        # 5. ALL Complaints start as 'Open' (No instant closing)
        status = "Open"
        closing_msg = "" 

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

        # 7. Final Response to User (Using Multi-Bubble Logic)
        base_msg = f"Complaint registered (ID: C-{new_id}) routed to {dept} ({agency})."
        
        # Format the response as a list of messages for separate chat bubbles
        reply_payload = {
            "fulfillmentMessages": [
                {
                    "text": {
                        "text": [base_msg]
                    }
                }
            ]
        }
        
        # If it is an emergency, add a SECOND text bubble to the chat
        if dept in ["Security", "Medical Assistance"]:
            emergency_alert = f"🚨 EMERGENCY ACTION: On-duty {dept} personnel have been alerted and are being dispatched to your location instantly."
            reply_payload["fulfillmentMessages"].append({
                "text": {
                    "text": [emergency_alert]
                }
            })
        # If Gemini generated an emergency tip, display it as an extra chat bubble!
        if advice_tip:
            emergency_alert = f"🚨 IMMEDIATE ADVICE: {advice_tip} Help is on the way."
            reply_payload["fulfillmentMessages"].append({
                "text": {"text": [emergency_alert]}
            })    
        return reply_payload

    except Exception as e:
        print(f"Error in complaint logging: {e}")
        return {"fulfillmentText": "Sorry, there was an error lodging your complaint. Please try again."}

# --- 5. Main Webhook Router ---
@app.route('/webhook', methods=['POST'])
def webhook():
    req = request.get_json(silent=True)
    
    # Get the name of the intent from Dialogflow
    intent_name = req.get('queryResult', {}).get('intent', {}).get('displayName')

    # Route to the correct helper function based on the intent
    if intent_name == 'provide_phone_number':
        return jsonify(handle_phone_number(req))
        
    elif intent_name == 'provide_station_name':
        return jsonify(handle_station_search(req))
        
    elif intent_name == 'user_confirms_station_yes':
        return jsonify(handle_station_confirmed(req))
        
    elif intent_name == 'provide_pnr':
        return jsonify(handle_pnr_verification(req))
        
    elif intent_name == 'capture_complaint_description':
        return jsonify(handle_complaint_logging(req))

    elif intent_name == 'capture_user_query':
        return jsonify(handle_query_intent(req))

    # Fallback if intent is not recognized or doesn't need backend processing
    return jsonify({"fulfillmentText": "Webhook received the intent, but no backend action was required."})


@app.route('/api/track', methods=['POST'])
def track_by_phone():
    data = request.get_json()
    phone_number = data.get('phone_number', '')

    if not phone_number:
        return jsonify({"error": "Phone number is required"}), 400

    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # --- NEW LOGIC: AUTO-CLOSE STALE COMPLAINTS ---
        # 1. Find Open complaints older than 1 minute for this user
        cursor.execute("""
            SELECT complaint_id, department FROM bot_complaints 
            WHERE phone_number = %s AND status = 'Open' 
            AND timestamp <= NOW() - INTERVAL '1 minute'
        """, (phone_number,))
        stale_complaints = cursor.fetchall()
        
        # 2. Update them with random closing statements
        for row in stale_complaints:
            comp_id = row[0]
            dept = row[1]
            closing_statement = get_random_closing_statement(dept)
            
            cursor.execute("""
                UPDATE bot_complaints 
                SET status = 'Closed', closing_statement = %s 
                WHERE complaint_id = %s
            """, (closing_statement, comp_id))
        
        if stale_complaints:
            conn.commit() # Save the auto-closes to the database
        # ----------------------------------------------
        
        # Now fetch the (potentially updated) records to show the user
        cursor.execute(
            "SELECT complaint_id, department, status, timestamp, complaint_text, closing_statement FROM bot_complaints WHERE phone_number = %s ORDER BY timestamp DESC",
            (phone_number,)
        )
        records = cursor.fetchall()
        conn.close()

        if not records:
            return jsonify({"message": "No complaints found for this number.", "complaints": []})

        complaints_list = []
        for row in records:
            # We now grab the closing statement (row[5]) if it exists
            resolution_text = row[5] if row[5] else ""
            
            complaints_list.append({
                "id": f"C-{row[0]}",
                "department": row[1],
                "status": row[2],
                "date": row[3].strftime("%Y-%m-%d %H:%M"),
                "description": row[4],
                "resolution": resolution_text # Send the closing statement to the frontend
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
            return "<p>No records found in this database table.</p>"
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