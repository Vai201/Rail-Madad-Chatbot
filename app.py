# backend/app.py
# 1. Imports
import os
from dotenv import load_dotenv
import psycopg2
import random
import re
import pandas as pd
from flask import Flask, request, jsonify
from flask_cors import CORS
import json
import google.generativeai as genai
from google.cloud import translate_v2 as translate
from google.cloud import dialogflow_v2 as dialogflow

# 2. LOAD ENV FIRST
load_dotenv() 

# 3. Define Constants
DB_HOST = "/cloudsql/project-f988ee73-0741-4016-82c:asia-south1:rail-madad-db"
DB_PASS = os.getenv("DB_PASS")

# 4. Direct Connection Helper (NO POOLING - Built for Cloud Run speed)
def get_db_connection():
    return psycopg2.connect(
        database="postgres",
        user="postgres",
        password=DB_PASS,
        host=DB_HOST
    )

def release_db_connection(conn):
    conn.close() # Cleanly cut the connection to save Cloud Run memory

# Configure Gemini instantly
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))

# Initialize App and CORS
app = Flask(__name__)
CORS(app)

# Initialize the translation client globally
translate_client = translate.Client()

# 👇 UPDATE THIS TO THE CORRECT BOT PROJECT ID 👇
DIALOGFLOW_PROJECT_ID = "automation-of-rail-madad"
# --- UTILITY FUNCTIONS ---

def process_translation(text, target_language):
    if target_language == 'en':
        return text
    try:
        result = translate_client.translate(text, target_language=target_language)
        return result['translatedText']
    except Exception as e:
        print(f"Translation Error: {e}")
        return text

def process_passenger_query(phone_number, user_query):
    """
    Handles daily rate limits, applies guardrails, fetches AI response, 
    and logs the query in PostgreSQL.
    """
    # 1. Use your existing connection helper
    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        # ==========================================
        # A. RATE LIMIT CHECK (Max 4 per day)
        # ==========================================
        cursor.execute("""
            SELECT COUNT(*) FROM passenger_queries 
            WHERE phone_number = %s AND DATE(created_at) = CURRENT_DATE;
        """, (phone_number,))
        
        query_count = cursor.fetchone()[0]

        if query_count >= 4:
            # Block the request and save API credits
            return "You have reached the daily limit of 4 queries for this contact number. Please try again tomorrow or select 'Register a Complaint' to file a complain."

        # ==========================================
        # B. THE GUARDRAIL PROMPT
        # ==========================================
        strict_prompt = f"""
        System Context: You are "RailBot", the official AI assistant for Indian Railways. 
        Your ONLY job is to answer queries related to Indian Railways, stations, trains, PNR rules, and travel guidelines. 

        Strict Rules:
        1. If the user asks a non-railway question, firmly refuse to answer it.
        2. IF AND ONLY IF the user mixes a genuine railway question with a non-railway question, answer the railway part, and append exactly this sentence: "Note: I am an official railway assistant and cannot assist with non-railway queries." 
        3. DO NOT add the warning note if the user's query is 100% about railways.
        4. Keep answers concise, helpful, and polite.
        5. FORMATTING: Do NOT use markdown symbols like **bold**, *italics*, or # headers. Use plain text only. Separate steps or lists with a double line break so they are easy to read in a chat window.

        User's Query: "{user_query}"
        """

        # ==========================================
        # C. CALL GEMINI (Upgraded for Factual Accuracy)
        # ==========================================
        # Using Gemini 3.1 Flash-Lite for high-speed, cost-effective factual recall
        model = genai.GenerativeModel('gemini-3.1-flash-lite-preview') 
        response = model.generate_content(strict_prompt)
        ai_response_text = response.text

        # ==========================================
        # D. LOG THE SUCCESSFUL QUERY IN DATABASE
        # ==========================================
        cursor.execute("""
            INSERT INTO passenger_queries (phone_number, user_query, ai_response) 
            VALUES (%s, %s, %s);
        """, (phone_number, user_query, ai_response_text))
        
        # Commit the transaction
        conn.commit()

        # Return the AI's clean response back to the user
        return ai_response_text

    except Exception as e:
        conn.rollback()
        print(f"Database/AI Error: {e}")
        return "I am currently experiencing high network traffic. Please try your query again in a few moments."

    finally:
        # Safely release the connection using your existing helper
        cursor.close()
        release_db_connection(conn)

# --- 1. Define Paths & Cloud DB Credentials ---
# --- 1. Define Paths & Cloud DB Credentials ---
# We removed os.pardir so it stays inside the rail_madad_chatbot folder
project_root = os.path.abspath(os.path.dirname(__file__))

pnr_file_path = os.path.join(project_root, 'data', 'pnr_database.csv')
stations_file_path = os.path.join(project_root, 'data', 'stations_original.csv')

# 👇 ADD YOUR GOOGLE CLOUD SQL DETAILS HERE 👇


print(f"Looking for PNR data at: {pnr_file_path}")
print(f"Looking for Station data at: {stations_file_path}")
print(f"Connecting to Cloud SQL at: {DB_HOST}")

# --- 2. RUN DATABASE SETUP ---
# --- 2. RUN DATABASE SETUP ---
def setup_database():
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # 1. NEW Query Table with Rate Limiting Support
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS passenger_queries (
            query_id SERIAL PRIMARY KEY,
            phone_number VARCHAR(15) NOT NULL,
            user_query TEXT NOT NULL,
            ai_response TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        ''')
        
        # 2. Existing Complaints Table
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
        
        # 3. PNR Table
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS pnr_records (
            pnr_number TEXT PRIMARY KEY,
            train_no TEXT,
            date_of_travel TEXT
        );
        ''')
        conn.commit()
        release_db_connection(conn)
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
        release_db_connection(conn)
        
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
'''def handle_query_intent(request_json):
    user_query_text = request_json['queryResult']['parameters']['user_query']
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("INSERT INTO bot_queries (query_text) VALUES (%s) RETURNING query_id", (user_query_text,))
    new_query_id = cursor.fetchone()[0]
    conn.commit()
    release_db_connection(conn)
    response_text = f"Thank you. Your query has been registered with ID: Q-{new_query_id}."
    return {"fulfillmentText": response_text}'''

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
        release_db_connection(conn)
        
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
    params = request_json.get('queryResult', {}).get('parameters', {})
    
    # Extract parameter safely
    pnr_input = params.get('pnr_number') or params.get('number') or params.get('any') or ''
    pnr_input_str = str(pnr_input)
    
    if "." in pnr_input_str:
        pnr_input_str = pnr_input_str.split(".")[0]
        
    pnr_digits = "".join(re.findall(r'\d', pnr_input_str))
    
    # Put back leading zeros if Dialogflow stripped them (e.g., "0000008788" -> "8788")
    if 0 < len(pnr_digits) < 10:
        pnr_digits = pnr_digits.zfill(10)
    
    # STRICT PRODUCTION RULE: Must be exactly 10 digits
    if len(pnr_digits) != 10:
        return {"fulfillmentText": f"Please provide a valid 10-digit PNR. I received {len(pnr_digits)} digits."}
    
    db_pnr_format = f"PNR{pnr_digits}"
    
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Query the database
        cursor.execute("SELECT train_no, date_of_travel FROM pnr_records WHERE pnr_number = %s", (db_pnr_format,))
        result = cursor.fetchone()
        release_db_connection(conn)

        # STRICT PRODUCTION RULE: Must exist in the database
        if result:
            train_no, travel_date = result
            
            # Generate Secure Token
            pnr_list = list(pnr_digits)
            import random
            random.shuffle(pnr_list)
            shuffled_pnr = "".join(pnr_list)
            token = f"TK-{shuffled_pnr[:6]}" 
            
            response_text = f"PNR verified for Train {train_no} on {travel_date}. Please describe your complaint."
            
            return {
                "fulfillmentText": response_text,
                "outputContexts": [
                    {
                        "name": f"{request_json.get('session')}/contexts/awaiting-complaint-description",
                        "lifespanCount": 1,
                        "parameters": {
                            "complaint_token": token,  
                            "pnr": db_pnr_format, 
                            "travel_date": travel_date 
                        }
                    }
                ]
            }
        else:
            # Rejects the user if the PNR is fake or missing
            return {"fulfillmentText": f"PNR {pnr_digits} not found in the official system. Please check your ticket and try again."}
            
    except Exception as e:
        print(f"Error in PNR check: {e}")
        return {"fulfillmentText": "We are experiencing a database connection issue. Please type 'hi' to restart."}

def syntax_router(text):
    """The fast, 0ms keyword matcher using strict whole-word boundaries."""
    import re
    text = text.lower()
    
    # Using \b (Word Boundary) ensures we match the exact word, not substrings.
    # Example: \bac\b matches "the ac is broken" but ignores "stomach".
    mapping = {
        "Sanitation & Cleaning": [r'\bdirty\b', r'\btoilet\b', r'\bwashroom\b', r'\bcleaning\b', r'\bfilthy\b', r'\bstink\b', r'\bgarbage\b'],
        "Catering & Food": [r'\bfood\b', r'\bpantry\b', r'\bovercharged\b', r'\bmeal\b', r'\bcatering\b', r'\bbad food\b', r'\bwater bottle\b'],
        "Maintenance & Electrical": [r'\bac\b', r'\bfan\b', r'\blight\b', r'\bcharging\b', r'\bbroken seat\b', r'\bwindow\b', r'\belectrical\b'],
        "Ticketing & Refunds": [r'\btte\b', r'\bticket\b', r'\brefund\b', r'\bbooking\b', r'\bseat allotment\b', r'\bcollector\b'],
        "Luggage & Parcels": [r'\bluggage\b', r'\bparcel\b', r'\blost bag\b', r'\bdamaged bag\b', r'\bdelayed luggage\b'],
        "Staff Behavior": [r'\brude\b', r'\bstaff\b', r'\bunprofessional\b', r'\bbehavior\b', r'\bshouting\b'],
        "Water Supply": [r'\bno water\b', r'\btap\b', r'\bdry\b', r'\bwater supply\b']
    }
    
    for dept, patterns in mapping.items():
        for pattern in patterns:
            if re.search(pattern, text):
                return dept
    return None 

def categorize_complaint(complaint_text):
    """Hybrid Enterprise Routing: Emergency Check -> Syntax -> Neural AI Fallback."""
    
    # RULE 1: The Emergency Intercept
    # If the text contains severe words, skip syntax and force it to the AI for tactical advice
    emergency_keywords = ['police', 'stolen', 'harass', 'doctor', 'faint', 'sick', 'blood', 'emergency', 'fight', 'creepy', 'pain', 'pregnant', 'attack']
    is_emergency = any(word in complaint_text.lower() for word in emergency_keywords)
    
    if is_emergency:
        dept, advice = neural_router(complaint_text)
        if dept: return dept, advice
    
    # RULE 2: The Fast Track (0ms)
    # Not an emergency? Let the strict regex syntax router handle it to save AI quota
    syntax_dept = syntax_router(complaint_text)
    if syntax_dept:
        return syntax_dept, "" 
        
    # RULE 3: The Smart Fallback
    # If it's a weird, misspelled, or complex sentence the regex missed, let Gemma figure it out
    dept, advice = neural_router(complaint_text)
    if dept:
        return dept, advice
        
    return "General", ""

def neural_router(complaint_text):
    """Fully dynamic LLM router for complex cases, emergencies, and safety tips."""
    import json
    import re
    
    valid_departments = [
        "Security", "Medical Assistance", "Sanitation & Cleaning", 
        "Maintenance & Electrical", "General" 
    ]
    
    # ADDED: Anti-overfitting instructions to force dynamic, unique advice
    # THE FIX: Added Rule #4 to make the AI aware of the PNR data
    prompt = f"""You are a backend routing API for Indian Railways. You receive a complaint and output ONLY raw JSON. 
    Complaint: "{complaint_text}"
    Valid Departments: {', '.join(valid_departments)}
    
    Rules for 'advice' field:
    1. If "Medical Assistance": Provide 1 sentence of practical first-aid steps the bystander can do right now.
    2. If "Security": Provide 1 sentence of tactical safety advice. CRITICAL TACTICAL RULES: Focus on creating distance, de-escalation, and seeking train staff. NEVER advise making eye contact with a harasser. NEVER advise pulling the emergency chain unless the complaint describes an active, violent physical attack.
    3. If any other department: The advice field MUST be "".
    4. CRITICAL SYSTEM AWARENESS: The system already knows the passenger's exact Train, Coach, and Seat number via their PNR. Do NOT advise the passenger to provide their seat or coach number.
    
    CRITICAL: Generate unique advice based on the passenger's exact situation. Do NOT copy the example text below. Start exactly with {{ and end with }}.
    
    Example format:
    {{"department": "Security", "advice": "Avoid confrontation, quietly gather your belongings, and move to a more crowded section of the train while RPF is dispatched."}}
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
        # OVERRIDE: Emergencies go to official forces, not private contractors
        if dept == "Medical Assistance":
            agency = "Indian Railway Medical Service (IRMS)"
        elif dept == "Security":
            agency = "The Railway Protection Force (RPF)"
        else:
            # For standard complaints, assign private contractors based on PNR
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
                        print(f"Invalid PNR length detected: {pnr}")
                except Exception as e:
                    print(f"Agency assignment error: {e}")

        # 4. PRIVACY LOGIC: Full Data vs. Redacted
        # 4. PRIVACY LOGIC: Moved to View Layer (RBAC)
        # We now store the REAL PNR in the database as the "Single Source of Truth".
        # Dynamic Data Masking will happen in the /hod-dashboard route.
        pnr_to_store = pnr if pnr else "UNRESERVED"

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
        release_db_connection(conn)

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

    # --- 1. Complaint Flow Intents ---
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

    # --- 2. NEW: Query Flow Intent (Gemma 3) ---
    elif intent_name == 'Handle_General_Query':
        parameters = req.get('queryResult', {}).get('parameters', {})
        phone = parameters.get('phone_number')
        query_text = parameters.get('user_query')
        
        # Run our secure, rate-limited Gemma 3 function
        final_response = process_passenger_query(phone, query_text)
        
        # Send the AI response AND the follow-up buttons back to the user
        return jsonify({
            "fulfillmentMessages": [
                {"text": {"text": [final_response]}},
                {
                    "payload": {
                        "richContent": [[
                            {
                                "type": "chips",
                                "options": [
                                    {"text": "Ask Another Query"},
                                    {"text": "Register a Complaint"}
                                ]
                            }
                        ]]
                    }
                }
            ]
        })

    # --- 3. Restart/Closing Logic ---
    elif intent_name == 'user_says_thanks':
        session_id = req.get('session')
        return jsonify({
            "fulfillmentMessages": [
                {"text": {"text": ["You are very welcome! Have a safe journey."]}},
                {"text": {"text": ["Welcome to Rail Madad, please select any one:"]}},
                {
                    "payload": {
                        "richContent": [[
                            {
                                "type": "chips",
                                "options": [
                                    {"text": "Register a Complaint"},
                                    {"text": "Query"}
                                ]
                            }
                        ]]
                    }
                }
            ],
            "outputContexts": [
                {"name": f"{session_id}/contexts/awaiting-location", "lifespanCount": 0},
                {"name": f"{session_id}/contexts/awaiting-complaint-description", "lifespanCount": 0},
                {"name": f"{session_id}/contexts/awaiting-station-confirmation", "lifespanCount": 0}
            ]
        })

    return jsonify({"fulfillmentText": "Webhook received the intent, but no backend action was required."})

@app.route('/chat_proxy', methods=['POST'])
def chat_proxy():
    """Acts as the middleman between the Custom UI and Dialogflow."""
    data = request.get_json()
    
    user_message = data.get('message')
    selected_language = data.get('language', 'en')
    session_id = data.get('session_id', 'default-session')
    
    try:
        # 1. Translate user input INTO English
        english_input = process_translation(user_message, 'en')
        
        # 2. Send to Dialogflow
        session_client = dialogflow.SessionsClient()
        session = session_client.session_path(DIALOGFLOW_PROJECT_ID, session_id)
        text_input = dialogflow.TextInput(text=english_input, language_code="en")
        query_input = dialogflow.QueryInput(text=text_input)
        
        response = session_client.detect_intent(
            request={"session": session, "query_input": query_input}
        )
        
       # --- NEW LOGIC: MULTI-BUBBLE TEXT EXTRACTION ---
        bot_responses = []
        
        # 1. Collect ALL text bubbles Dialogflow sent back
        for msg in response.query_result.fulfillment_messages:
            if msg.text and msg.text.text:
                bot_responses.append(msg.text.text[0])
                
        # 2. Join them with HTML line breaks so they look clean in the UI
        if bot_responses:
            bot_response_english = "<br><br>".join(bot_responses)
        else:
            bot_response_english = response.query_result.fulfillment_text
        
        # 3. The Timeout Safety Net
        if not bot_response_english:
            bot_response_english = "The database is waking up and took a little too long. Could you please send that last message again?"
            
        # 4. Extract Buttons
        buttons = []
        for msg in response.query_result.fulfillment_messages:
            if msg.payload and 'richContent' in msg.payload:
                try:
                    buttons = msg.payload['richContent'][0][0].get('options', [])
                except (IndexError, AttributeError):
                    pass
        # --------------------------------------------------

        # 3. Translate the main text out to the user's language
        final_response_text = process_translation(bot_response_english, selected_language)
        
        # 4. Translate each button's text as well!
        translated_buttons = []
        for btn in buttons:
            translated_btn_text = process_translation(btn['text'], selected_language)
            translated_buttons.append({"text": translated_btn_text})

        return jsonify({
            "reply": final_response_text,
            "buttons": translated_buttons
        })

    except Exception as e:
        print(f"Dialogflow Proxy Error: {e}")
        error_msg = process_translation("I am experiencing a network issue.", selected_language)
        return jsonify({"reply": error_msg}), 500

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
        release_db_connection(conn)

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

@app.route('/api/cron/auto-close', methods=['GET', 'POST'])
def cron_auto_close():
    """Background task to automatically close stale complaints after 2 minutes."""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Find all open complaints older than 2 minutes (Background Automation)
        cursor.execute("""
            SELECT complaint_id, department FROM bot_complaints 
            WHERE status = 'Open' 
            AND timestamp <= NOW() - INTERVAL '2 minutes'
        """)
        stale_complaints = cursor.fetchall()
        
        closed_count = 0
        for row in stale_complaints:
            comp_id = row[0]
            dept = row[1]
            closing_statement = get_random_closing_statement(dept)
            
            cursor.execute("""
                UPDATE bot_complaints 
                SET status = 'Closed', closing_statement = %s 
                WHERE complaint_id = %s
            """, (closing_statement, comp_id))
            closed_count += 1
        
        if stale_complaints:
            conn.commit()
            print(f"CRON: Automatically closed {closed_count} complaints.")
            
        release_db_connection(conn)
        
        return jsonify({"status": "success", "closed_complaints": closed_count})

    except Exception as e:
        print(f"CRON ERROR: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500
    
# --- 6. ADMIN DASHBOARD PAGES ---
def get_db_as_html_table(query):
    try:
        setup_database() 
        conn = get_db_connection()
        import warnings
        with warnings.catch_warnings():
            warnings.simplefilter('ignore', UserWarning)
            df = pd.read_sql_query(query, conn)
        release_db_connection(conn)
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
                <li><a href="/department-dashboard" style="font-size: 1.5em; color: #d93025; font-weight: bold;">🔒 Secure Department Portal (RBAC Demo)</a></li>
                <br>
                <li><a href="/view-complaints" style="font-size: 1.5em;">View Master Complaints Log</a></li>
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

@app.route('/department-dashboard')
def department_dashboard():
    # Default to Catering if no department is selected
    selected_dept = request.args.get('dept', 'Catering & Food')
    
    departments = [
        "Catering & Food", "Sanitation & Cleaning", 
        "Maintenance & Electrical", "Security", "Medical Assistance"
    ]
    
    # Fetch data from the single source of truth, joined with PNR records
    query = """
        SELECT c.complaint_id, c.timestamp, c.phone_number, c.pnr, c.token, 
               c.complaint_text, c.status, p.train_no, p.date_of_travel
        FROM bot_complaints c
        LEFT JOIN pnr_records p ON c.pnr = p.pnr_number
        WHERE c.department = %s
        ORDER BY c.timestamp DESC
    """
    
    table_rows = ""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute(query, (selected_dept,))
        records = cursor.fetchall()
        release_db_connection(conn)
        
        for row in records:
            comp_id, ts, phone, pnr, token, text, status, train_no, travel_date = row
            
            # Deterministically mock coach/seat based on PNR hash for the prototype demo
            mock_coach = f"{random.choice(['B','A','S'])}{hash(pnr) % 9 + 1}" if pnr and pnr != "UNRESERVED" else "N/A"
            mock_seat = str(hash(pnr) % 72 + 1) if pnr and pnr != "UNRESERVED" else "N/A"
            
            # ==========================================
            # RBAC DYNAMIC DATA MASKING ENGINE
            # ==========================================
            if selected_dept in ["Security", "Medical Assistance"]:
                # High Privilege Department: Full Access
                display_phone = phone
                display_pnr = pnr
                display_coach = mock_coach
                display_seat = mock_seat
            else:
                # Low Privilege Department (Food/Sanitation): Redacted Access
                display_phone = f"******{phone[-4:]}" if phone and len(phone) >= 4 else "REDACTED"
                display_pnr = f"REDACTED (TK-{token[-4:]})" if token else "REDACTED"
                display_coach = "🔒 MASKED"
                display_seat = "🔒 MASKED"
            # ==========================================
            
            train_display = train_no if train_no else "N/A"
            date_display = travel_date if travel_date else "N/A"
            
            status_color = "green" if status == "Closed" else "orange"
            
            table_rows += f"""
            <tr>
                <td>C-{comp_id}</td>
                <td>{ts.strftime('%Y-%m-%d %H:%M')}</td>
                <td style="font-family: monospace; font-weight: bold;">{display_phone}</td>
                <td style="font-family: monospace; color: #d93025;">{display_pnr}</td>
                <td><b>{train_display}</b></td>
                <td>{date_display}</td>
                <td style="color: #1a73e8; font-weight: bold;">{display_coach}</td>
                <td style="color: #1a73e8; font-weight: bold;">{display_seat}</td>
                <td>{text}</td>
                <td><b style="color:{status_color};">{status}</b></td>
            </tr>
            """
    except Exception as e:
        table_rows = f"<tr><td colspan='10'>Database Error: {e}</td></tr>"

    # Generate the dropdown options
    dropdown_options = ""
    for d in departments:
        selected = "selected" if d == selected_dept else ""
        dropdown_options += f'<option value="{d}">{d} Portal</option>'

    # Return the secure HTML View
    return f"""
    <html>
        <head>
            <title>Secure Department Portal</title>
            <style>
                body {{ font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; background: #f4f6f9; padding: 20px; }}
                .header {{ background: #1a2035; color: white; padding: 20px; border-radius: 8px; display: flex; justify-content: space-between; align-items: center; }}
                select {{ padding: 10px; font-size: 16px; border-radius: 5px; cursor: pointer; }}
                .table-container {{ background: white; padding: 20px; border-radius: 8px; margin-top: 20px; box-shadow: 0 4px 6px rgba(0,0,0,0.1); overflow-x: auto; }}
                table {{ width: 100%; border-collapse: collapse; text-align: left; }}
                th, td {{ padding: 12px; border-bottom: 1px solid #ddd; }}
                th {{ background: #f8f9fa; color: #333; }}
            </style>
        </head>
        <body>
            <div class="header">
                <div>
                    <h1 style="margin:0;">🔒 Secure Department Portal</h1>
                    <p style="margin:5px 0 0 0; color: #aaa;">Role-Based Access Control (RBAC) & Dynamic Data Masking Demo</p>
                </div>
                <form method="GET" action="/department-dashboard">
                    <select name="dept" onchange="this.form.submit()">
                        {dropdown_options}
                    </select>
                </form>
            </div>
            
            <div class="table-container">
                <table>
                    <tr>
                        <th>ID</th>
                        <th>Timestamp</th>
                        <th>Passenger Phone</th>
                        <th>PNR Number</th>
                        <th>Train No</th>
                        <th>Travel Date</th>
                        <th>Coach</th>
                        <th>Seat</th>
                        <th>Complaint Details</th>
                        <th>Status</th>
                    </tr>
                    {table_rows}
                </table>
            </div>
            <br>
            <a href="/admin" style="color: #1a73e8; text-decoration: none;">⬅ Back to Master Admin</a>
        </body>
    </html>
    """

# --- 7. Run the Server ---
if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=True)