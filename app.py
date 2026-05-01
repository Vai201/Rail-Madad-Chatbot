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
from google.protobuf.json_format import MessageToDict
from google.cloud import storage
import datetime
import uuid
import requests
import requests
import google.auth
from google.auth import impersonated_credentials

# 2. LOAD ENV FIRST
load_dotenv() 

# Define your bucket name
EVIDENCE_BUCKET_NAME = "rail-madad-evidence-bucket"

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
    conn.close()

# Configure Gemini instantly
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))

# Initialize App and CORS
app = Flask(__name__)
CORS(app)

# Initialize the translation client globally
translate_client = translate.Client()

# 👇 UPDATE THIS TO THE CORRECT BOT PROJECT ID 👇
DIALOGFLOW_PROJECT_ID = "automation-of-rail-madad"

# --- 2. RUN DATABASE SETUP ---
def setup_database():
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS passenger_queries (
            query_id SERIAL PRIMARY KEY,
            phone_number VARCHAR(15) NOT NULL,
            user_query TEXT NOT NULL,
            ai_response TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
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
            media_url TEXT,
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        ''')
        
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS pnr_records (
            pnr_number TEXT PRIMARY KEY,
            train_no TEXT,
            date_of_travel TEXT
        );
        ''')
        
        # --- NEW TABLE: Safely holds media URLs while Dialogflow processes the text ---
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS session_media (
            session_id TEXT PRIMARY KEY,
            media_url TEXT
        );
        ''')
        
        cursor.execute("ALTER TABLE bot_complaints ADD COLUMN IF NOT EXISTS sos_logs TEXT DEFAULT '';")
        conn.commit()
        release_db_connection(conn)
        print("✅ Cloud Database schema verified & Session Media Table Created.")
        cleanup_old_complaints()
    except Exception as e:
        print(f"❌ ERROR setting up database: {e}")

def cleanup_old_complaints():
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cleanup_query = '''
            DELETE FROM bot_complaints 
            WHERE status = 'Closed' 
            AND timestamp < CURRENT_TIMESTAMP - INTERVAL '6 months'
            AND department NOT IN ('Medical Assistance', 'RPF/Security');
        '''
        
        cursor.execute(cleanup_query)
        deleted_count = cursor.rowcount 
        conn.commit()
        release_db_connection(conn)
        
        if deleted_count > 0:
            print(f"🧹 DATA RETENTION: Automatically cleared {deleted_count} old closed complaints.")
            
    except Exception as e:
        print(f"❌ ERROR during automated database cleanup: {e}")

# 🚨 FORCE DB SETUP ON STARTUP 🚨
try:
    setup_database()
except:
    pass

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
    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        cursor.execute("""
            SELECT COUNT(*) FROM passenger_queries 
            WHERE phone_number = %s AND DATE(created_at) = CURRENT_DATE;
        """, (phone_number,))
        
        query_count = cursor.fetchone()[0]

        if query_count >= 4:
            return "You have reached the daily limit of 4 queries for this contact number. Please try again tomorrow or select 'Register a Complaint' to file a complain."

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

        model = genai.GenerativeModel('gemini-3.1-flash-lite-preview') 
        response = model.generate_content(strict_prompt)
        ai_response_text = response.text

        cursor.execute("""
            INSERT INTO passenger_queries (phone_number, user_query, ai_response) 
            VALUES (%s, %s, %s);
        """, (phone_number, user_query, ai_response_text))
        conn.commit()

        return ai_response_text

    except Exception as e:
        conn.rollback()
        print(f"Database/AI Error: {e}")
        return "I am currently experiencing high network traffic. Please try your query again in a few moments."

    finally:
        cursor.close()
        release_db_connection(conn)

# --- 1. Define Paths & Cloud DB Credentials ---
project_root = os.path.abspath(os.path.dirname(__file__))

pnr_file_path = os.path.join(project_root, 'data', 'pnr_database.csv')
stations_file_path = os.path.join(project_root, 'data', 'stations_original.csv')

# --- 3. Load Data at Startup ---
station_data_raw = None
station_data_processed = None
print("✅ Connected directly to Cloud SQL.")

try:
    station_data_raw = pd.read_csv(stations_file_path, quotechar='"') 
    station_data_processed = station_data_raw.copy()
    station_data_processed['station'] = station_data_processed['station'].str.lower()
    station_data_processed['id_code'] = station_data_processed['id_code'].str.lower()
except Exception as e:
    pass

# --- 4. Helper Functions for Chatbot ---
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
                "fulfillmentMessages": [
                    {
                        "text": {
                            "text": [f"Did you mean '{original_station_name}'?"]
                        }
                    },
                    {
                        "payload": {
                            "richContent": [
                                [
                                    {
                                        "type": "chips",
                                        "options": [
                                            {"text": "Yes"},
                                            {"text": "No, let me retype"}
                                        ]
                                    }
                                ]
                            ]
                        }
                    }
                ],
                "outputContexts": [
                    {
                        "name": f"{session_id}/contexts/awaiting-station-confirmation",
                        "lifespanCount": 1,
                        "parameters": {"station_confirmed": original_station_name}
                    }
                ]
            }
        else:
            return {
                "fulfillmentMessages": [
                    {
                        "text": {
                            "text": ["Sorry, I couldn't find that station in the database. Please type 'hi' to start over or try another name."]
                        }
                    }
                ],
                "outputContexts": [
                     {
                        "name": f"{session_id}/contexts/awaiting-location",
                        "lifespanCount": 0 
                     }
                ]
            }
    except Exception as e:
        print(f"Error in station search: {e}")
        return {
            "fulfillmentMessages": [
                {
                    "text": {
                        "text": ["Station database error. Please type 'hi' to restart your complaint."]
                    }
                }
            ],
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
    
    pnr_input = params.get('pnr_number') or params.get('number') or params.get('any') or ''
    pnr_input_str = str(pnr_input)
    
    if "." in pnr_input_str:
        pnr_input_str = pnr_input_str.split(".")[0]
        
    pnr_digits = "".join(re.findall(r'\d', pnr_input_str))
    
    if 0 < len(pnr_digits) < 10:
        pnr_digits = pnr_digits.zfill(10)
    
    if len(pnr_digits) != 10:
        return {"fulfillmentText": f"Please provide a valid 10-digit PNR. I received {len(pnr_digits)} digits."}
    
    db_pnr_format = f"PNR{pnr_digits}"
    
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute("SELECT train_no, date_of_travel FROM pnr_records WHERE pnr_number = %s", (db_pnr_format,))
        result = cursor.fetchone()
        release_db_connection(conn)

        if result:
            train_no, travel_date = result
            
            pnr_list = list(pnr_digits)
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
            return {"fulfillmentText": f"PNR {pnr_digits} not found in the official system. Please check your ticket and try again."}
            
    except Exception as e:
        print(f"Error in PNR check: {e}")
        return {"fulfillmentText": "We are experiencing a database connection issue. Please type 'hi' to restart."}

def syntax_router(text):
    import re
    text = text.lower()
    
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
    emergency_keywords = ['police', 'stolen', 'harass', 'doctor', 'faint', 'sick', 'blood', 'emergency', 'fight', 'creepy', 'pain', 'pregnant', 'attack']
    is_emergency = any(word in complaint_text.lower() for word in emergency_keywords)
    
    if is_emergency:
        dept, advice = neural_router(complaint_text)
        if dept: return dept, advice
    
    syntax_dept = syntax_router(complaint_text)
    if syntax_dept:
        return syntax_dept, "" 
        
    dept, advice = neural_router(complaint_text)
    if dept:
        return dept, advice
        
    return "General", ""

def neural_router(complaint_text):
    import json
    import re
    
    valid_departments = [
        "Security", "Medical Assistance", "Sanitation & Cleaning", 
        "Maintenance & Electrical", "General" 
    ]
    
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
        model = genai.GenerativeModel('models/gemma-3-27b-it')
        
        safety_settings = [
            {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_NONE"},
            {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_NONE"},
            {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_NONE"},
            {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_NONE"}
        ]
        
        response = model.generate_content(
            prompt, 
            safety_settings=safety_settings,
            generation_config={"max_output_tokens": 300}
        )
        
        if not response.text:
            return "General", ""

        raw_response = response.text.strip()
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
            return "General", ""
            
    except Exception as e:
        print(f"CRITICAL GEMINI ERROR: {e}")
        return "General", ""

def get_agency_name(pnr_str):
    try:
        pnr_num = int(re.search(r'\d+', pnr_str).group())
        if pnr_num <= 5000: return "M/s Ambuj Hotel Pvt. Ltd"
        elif pnr_num <= 10000: return "M/s. R.K.Associates & Hoteliers Pvt.Ltd"
        elif pnr_num <= 15000: return " M/s. Boon Catg. Co."
        elif pnr_num <= 20000: return "M/s A.S Sales Corporation"
        elif pnr_num <= 25000: return "M/s. Rathour Services"
        else: return "M/s. A. A. Catg. Co"
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
    if dept in ["Water Supply", "Maintenance & Electrical"]:
        return random.choice(statements["Sanitation & Cleaning"])
    
    return random.choice(statements.get(dept, statements["Default"]))

def handle_complaint_logging(request_json):
    conn = None
    try:
        session_path = request_json.get('session', '')
        session_id = session_path.split('/')[-1]

        # 1. Establish ONE database connection for the entire function
        conn = get_db_connection()
        cursor = conn.cursor()

        # 2. Grab the URL from the secure DB table
        media_url = None
        try:
            cursor.execute("SELECT media_url FROM session_media WHERE session_id = %s", (session_id,))
            row = cursor.fetchone()
            if row:
                media_url = row[0]
                cursor.execute("DELETE FROM session_media WHERE session_id = %s", (session_id,))
        except Exception as e:
            print(f"Error fetching media URL from DB: {e}")
            conn.rollback() 

        # 3. Extract Dialogflow parameters
        parameters = request_json['queryResult'].get('parameters', {})
        complaint_text = parameters.get('complaint_text', '')
        
        if not complaint_text:
            complaint_text = request_json['queryResult'].get('queryText', '')

        pnr = ""
        token = ""
        station = ""
        phone_number = ""
        travel_date = ""

        contexts = request_json['queryResult'].get('outputContexts', []) 
        for c in contexts:
            params = c.get('parameters', {})
            
            if not phone_number:
                phone_number = params.get('phone_number', '')
            
            if 'awaiting-complaint-description' in c.get('name', ''):
                pnr = params.get('pnr', pnr) 
                token = params.get('complaint_token', token)
                station = params.get('station_confirmed', station)
                if not travel_date:
                    travel_date = params.get('travel_date', '')

        # 4. Route and Categorize
        dept, advice_tip = categorize_complaint(complaint_text)
        
        if dept == "Medical Assistance":
            agency = "Indian Railway Medical Service (IRMS)"
        elif dept == "Security":
            agency = "The Railway Protection Force (RPF)"
        else:
            agency = get_agency_name(pnr)

        pnr_to_store = pnr if pnr else "UNRESERVED"
        status = "Open"
        closing_msg = "" 

        # 5. Insert the final complaint
        cursor.execute(
            """INSERT INTO bot_complaints 
               (phone_number, pnr, token, station, travel_date, complaint_text, department, agency, status, closing_statement, media_url) 
               VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s) RETURNING complaint_id""",
            (phone_number, pnr_to_store, token, station, travel_date, complaint_text, dept, agency, status, closing_msg, media_url)
        )
        new_id = cursor.fetchone()[0]
        
        # 6. COMMIT the entire transaction 
        conn.commit()

        base_msg = f"Complaint registered (ID: C-{new_id}) routed to {dept} ({agency})."
        
        reply_payload = {
            "fulfillmentMessages": [{"text": {"text": [base_msg]}}]
        }
        
        if dept in ["Security", "Medical Assistance"]:
            emergency_alert = f"🚨 EMERGENCY ACTION: On-duty {dept} personnel have been alerted and are being dispatched to your location instantly."
            reply_payload["fulfillmentMessages"].append({"text": {"text": [emergency_alert]}})
            
        if advice_tip:
            emergency_alert = f"🚨 IMMEDIATE ADVICE: {advice_tip} Help is on the way."
            reply_payload["fulfillmentMessages"].append({"text": {"text": [emergency_alert]}})
            
        reply_payload["outputContexts"] = [
            {"name": f"{session_path}/contexts/awaiting-location", "lifespanCount": 0},
            {"name": f"{session_path}/contexts/awaiting-station-confirmation", "lifespanCount": 0},
            {"name": f"{session_path}/contexts/awaiting-complaint-description", "lifespanCount": 0}
        ]    
        return reply_payload

    except Exception as e:
        print(f"Error in complaint logging: {e}")
        if conn:
            conn.rollback() 
        return {"fulfillmentText": "Sorry, there was an error lodging your complaint. Please try again."}
    
    finally:
        if conn:
            release_db_connection(conn)

# --- 5. Main Webhook Router ---
@app.route('/webhook', methods=['POST'])
def webhook():
    req = request.get_json(silent=True)
    intent_name = req.get('queryResult', {}).get('intent', {}).get('displayName')

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

    elif intent_name == 'Handle_General_Query':
        parameters = req.get('queryResult', {}).get('parameters', {})
        phone = parameters.get('phone_number')
        query_text = parameters.get('user_query')
        
        final_response = process_passenger_query(phone, query_text)
        
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
    data = request.get_json()
    
    user_message = data.get('message', '')
    selected_language = data.get('language', 'en')
    session_id = data.get('session_id', 'default-session')
    
    media_url = data.get('media_url')
    
    try:
        url_match = re.search(r'\[Evidence:\s*(https?://[^\s\]]+)\]', user_message)
        if url_match:
            if not media_url:
                media_url = url_match.group(1)
            user_message = user_message.replace(url_match.group(0), '').strip()

        if media_url and str(media_url).strip().lower() == 'none':
            media_url = None

        if media_url:
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO session_media (session_id, media_url)
                VALUES (%s, %s)
                ON CONFLICT (session_id) DO UPDATE SET media_url = EXCLUDED.media_url;
            """, (session_id, media_url))
            conn.commit()
            release_db_connection(conn)

        if not user_message and media_url:
            user_message = "I have attached a photo as evidence for my complaint."

        english_input = process_translation(user_message, 'en')
        
        session_client = dialogflow.SessionsClient()
        session = session_client.session_path(DIALOGFLOW_PROJECT_ID, session_id)
        text_input = dialogflow.TextInput(text=english_input, language_code="en")
        query_input = dialogflow.QueryInput(text=text_input)
        
        response = session_client.detect_intent(request={"session": session, "query_input": query_input})
        
        bot_responses = []
        for msg in response.query_result.fulfillment_messages:
            if msg.text and msg.text.text:
                bot_responses.append(msg.text.text[0])
                
        if bot_responses:
            bot_response_english = "<br><br>".join(bot_responses)
        else:
            bot_response_english = response.query_result.fulfillment_text
        
        if not bot_response_english:
            bot_response_english = "The database is waking up and took a little too long. Could you please send that last message again?"
            
        buttons = []
        for msg in response.query_result.fulfillment_messages:
            try:
                raw_proto = msg._pb if hasattr(msg, '_pb') else msg
                msg_dict = MessageToDict(raw_proto)
                if 'payload' in msg_dict and 'richContent' in msg_dict['payload']:
                    buttons = msg_dict['payload']['richContent'][0][0].get('options', [])
            except Exception as e:
                pass

        final_response_text = process_translation(bot_response_english, selected_language)
        
        translated_buttons = []
        for btn in buttons:
            translated_btn_text = process_translation(btn['text'], selected_language)
            translated_buttons.append({"text": translated_btn_text})

        allow_upload = False
        if hasattr(response, 'query_result') and hasattr(response.query_result, 'output_contexts'):
            for ctx in response.query_result.output_contexts:
                if 'awaiting-complaint-description' in ctx.name:
                    allow_upload = True
                    break

        return jsonify({
            "reply": final_response_text,
            "buttons": translated_buttons,
            "allow_upload": allow_upload
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
        
        cursor.execute("""
            SELECT complaint_id, department FROM bot_complaints 
            WHERE phone_number = %s AND status = 'Open' 
            AND timestamp <= NOW() - INTERVAL '1 minute'
        """, (phone_number,))
        stale_complaints = cursor.fetchall()
        
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
            conn.commit() 
            
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
            resolution_text = row[5] if row[5] else ""
            complaints_list.append({
                "id": f"C-{row[0]}",
                "department": row[1],
                "status": row[2],
                "date": row[3].strftime("%Y-%m-%d %H:%M"),
                "description": row[4],
                "resolution": resolution_text 
            })

        return jsonify({"message": "Success", "complaints": complaints_list})

    except Exception as e:
        print(f"Error fetching tracking data: {e}")
        return jsonify({"error": "Database error"}), 500

@app.route('/api/cron/auto-close', methods=['GET', 'POST'])
def cron_auto_close():
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
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
        conn = get_db_connection()
        import warnings
        with warnings.catch_warnings():
            warnings.simplefilter('ignore', UserWarning)
            df = pd.read_sql_query(query, conn)
        release_db_connection(conn)
        
        if df.empty: return "<p>No records found.</p>"
        
        if 'media_url' in df.columns and 'complaint_id' in df.columns:
            df['Evidence'] = df.apply(
                lambda row: f'<a href="{row["media_url"]}" target="_blank" style="color:#1a73e8; font-weight:bold; text-decoration:underline;">C-{row["complaint_id"]}</a>' 
                if pd.notna(row["media_url"]) and str(row["media_url"]).strip() != "" and str(row["media_url"]).strip().lower() != "none" else "None", 
                axis=1
            )
            idx = df.columns.get_loc('media_url')
            df.insert(idx, 'Evidence', df.pop('Evidence'))
            df = df.drop(columns=['media_url'])

        return df.to_html(index=False, border=0, classes="table", escape=False)
    except Exception as e:
        return f"<p>Error reading database: {e}</p>"

def get_page_template(title, table_html):
    return f"""
    <html>
        <head>
            <title>{title}</title>
            <style>
                body {{ font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; background: #f4f6f9; padding: 20px; }}
                h1 {{ color: #1a2035; margin-bottom: 5px; }}
                .table-container {{ background: white; padding: 20px; border-radius: 8px; margin-top: 20px; box-shadow: 0 4px 6px rgba(0,0,0,0.1); overflow-x: auto; }}
                table {{ width: 100%; border-collapse: collapse; text-align: left; min-width: 1000px; }}
                th, td {{ padding: 12px; border-bottom: 1px solid #ddd; vertical-align: top; font-size: 14px; }}
                th {{ background: #f8f9fa; color: #333; position: sticky; top: 0; font-weight: 600; }}
                tr:hover {{ background-color: #f1f1f1; }}
                a.btn {{ font-size: 14px; color: #1a73e8; text-decoration: none; font-weight: bold; display: inline-block; margin-bottom: 15px; background: white; padding: 8px 16px; border-radius: 6px; box-shadow: 0 1px 3px rgba(0,0,0,0.1); border: 1px solid #e0e0e0; }}
                a.btn:hover {{ background: #f8f9fa; }}
            </style>
        </head>
        <body>
            <h1>{title}</h1>
            <a href="/admin" class="btn">⬅ Back to Admin Dashboard</a>
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
        <head>
            <title>Admin Dashboard</title>
            <style>
                body { font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; background: #f4f6f9; padding: 40px; display: flex; flex-direction: column; align-items: center; }
                .card { background: white; padding: 40px; border-radius: 12px; box-shadow: 0 10px 15px rgba(0,0,0,0.05); text-align: center; max-width: 600px; width: 100%; }
                h1 { color: #1a2035; margin-bottom: 30px; }
                a { display: block; padding: 15px 20px; margin-bottom: 15px; border-radius: 8px; text-decoration: none; font-weight: bold; font-size: 18px; transition: all 0.2s; }
                .portal-btn { background: #d93025; color: white; border: 2px solid #d93025; }
                .portal-btn:hover { background: #b3261d; box-shadow: 0 4px 8px rgba(217,48,37,0.3); }
                .standard-btn { background: white; color: #1a73e8; border: 2px solid #1a73e8; }
                .standard-btn:hover { background: #f4f8fe; box-shadow: 0 4px 8px rgba(26,115,232,0.2); }
            </style>
        </head>
        <body>
            <div class="card">
                <h1>Rail Madad Admin Center</h1>
                <a href="/department-dashboard" class="portal-btn">🔒 Secure Department Portal (RBAC)</a>
                <a href="/view-complaints" class="standard-btn">View Master Complaints Log</a>
                <a href="/view-pnrs" class="standard-btn">View PNR Database</a>
                <a href="/view-stations" class="standard-btn">View Station Database</a>
            </div>
        </body>
    </html>
    """

@app.route('/view-complaints')
def view_complaints():
    query = "SELECT complaint_id, timestamp, phone_number, pnr, token, station, travel_date, complaint_text, department, agency, media_url, status, closing_statement, sos_logs FROM bot_complaints ORDER BY timestamp DESC"
    return get_page_template("Master Complaints Log", get_db_as_html_table(query))

@app.route('/view-pnrs')
def view_pnrs():
    query = "SELECT * FROM pnr_records LIMIT 100"
    table_html = get_db_as_html_table(query)
    if "No records found" in table_html or "Error" in table_html:
        table_html = "<p>No PNR records found. Please import your CSV into Cloud SQL.</p>"
    return get_page_template("PNR Database Ledger", table_html)

@app.route('/view-stations')
def view_stations():
    query = "SELECT * FROM stations LIMIT 100" 
    return get_page_template("Station Database Registry", get_db_as_html_table(query))

@app.route('/department-dashboard')
def department_dashboard():
    selected_dept = request.args.get('dept', 'Catering & Food')
    departments = [
        "Sanitation & Cleaning", "Catering & Food", "Maintenance & Electrical", 
        "Ticketing & Refunds", "Luggage & Parcels", "Staff Behavior", 
        "Water Supply", "Security", "Medical Assistance", "General"
    ]
    
    # 1. Added c.sos_logs to the SQL Query
    query = """
        SELECT c.complaint_id, c.timestamp, c.phone_number, c.pnr, c.token, 
               c.complaint_text, c.status, p.train_no, c.travel_date, c.closing_statement, c.station, c.media_url, c.sos_logs
        FROM bot_complaints c
        LEFT JOIN pnr_records p ON c.pnr = p.pnr_number
        WHERE c.department = %s
        ORDER BY c.timestamp DESC
    """
    table_rows = ""
    conn = None
    
    # Determine if we should show the SOS column
    show_sos_column = selected_dept in ["Security", "Medical Assistance"]
    
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute(query, (selected_dept,))
        records = cursor.fetchall()
        
        for row in records:
            comp_id, ts, phone, pnr, token, text, status, train_no, travel_date, closing_statement, station, media_url, sos_logs = row
            
            mock_coach = f"{random.choice(['B','A','S'])}{hash(pnr) % 9 + 1}" if pnr and pnr != "UNRESERVED" and not str(pnr).startswith("REDACTED") else "N/A"
            mock_seat = str(hash(pnr) % 72 + 1) if pnr and pnr != "UNRESERVED" and not str(pnr).startswith("REDACTED") else "N/A"
            
            # Keep Phone & PNR Masked for standard departments
            if selected_dept in ["Security", "Medical Assistance"]:
                display_phone = phone
                display_pnr = pnr
            else:
                display_phone = f"******{phone[-4:]}" if phone and len(phone) >= 4 else "REDACTED"
                display_pnr = f"REDACTED (TK-{token[-4:]})" if token else "REDACTED"
                
            # 2. UPDATED LOGIC: Only Catering & Food masks the Coach and Seat!
            if selected_dept != "Catering & Food":
                display_coach = mock_coach
                display_seat = mock_seat
            else:
                display_coach = "🔒 MASKED"
                display_seat = "🔒 MASKED"
            
            train_display = train_no if train_no else "N/A"
            date_display = travel_date if travel_date else "N/A"
            station_display = station if station else "Not Provided"
            
            media_html = "None"
            if media_url and str(media_url).strip().lower() != 'none':
                media_html = f'<a href="{media_url}" target="_blank" style="color:#1a73e8; font-weight:bold; text-decoration:underline;">C-{comp_id}</a>'
            
            status_color = "green" if status == "Closed" else "orange"
            status_html = f'<b style="color:{status_color};">{status}</b>'
            if status == "Closed" and closing_statement:
                status_html += f'<br><span style="font-size: 0.85em; color: #555; display:block; margin-top:4px;">{closing_statement}</span>'
            
            # 3. Format the SOS Logs for the new column
            sos_td = ""
            if show_sos_column:
                if sos_logs:
                    sos_content = f"<div style='max-height: 120px; overflow-y: auto; font-size: 0.85em; background: #fff5f5; padding: 6px; border: 1px solid #ffe3e3; border-radius: 4px;'>{sos_logs}</div>"
                else:
                    sos_content = "<span style='color:#aaa; font-style:italic;'>No SOS active</span>"
                sos_td = f"<td style='min-width: 250px;'>{sos_content}</td>"
            
            table_rows += f"""
            <tr>
                <td>C-{comp_id}</td>
                <td>{ts.strftime('%Y-%m-%d %H:%M')}</td>
                <td style="font-family: monospace; font-weight: bold;">{display_phone}</td>
                <td style="font-family: monospace; color: #d93025;">{display_pnr}</td>
                <td><b>{train_display}</b></td>
                <td>{date_display}</td>
                <td style="color: #0f9d58; font-weight: bold;">{station_display}</td>
                <td style="color: #1a73e8; font-weight: bold;">{display_coach}</td>
                <td style="color: #1a73e8; font-weight: bold;">{display_seat}</td>
                <td>{text}</td>
                <td>{media_html}</td>
                {sos_td}
                <td>{status_html}</td>
            </tr>
            """
    except Exception as e:
        colspan = 13 if show_sos_column else 12
        table_rows = f"<tr><td colspan='{colspan}'>Database Error: {e}</td></tr>"
    finally:
        if conn: release_db_connection(conn)

    dropdown_options = ""
    for d in departments:
        selected_attr = "selected" if str(d) == str(selected_dept) else ""
        dropdown_options += f'<option value="{d}" {selected_attr}>{d} Portal</option>'

    # Add the SOS Header dynamically
    sos_th = "<th>SOS Live Logs</th>" if show_sos_column else ""

    return f"""
    <html>
        <head>
            <title>Secure Department Portal</title>
            <style>
                body {{ font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; background: #f4f6f9; padding: 20px; }}
                .header {{ background: #1a2035; color: white; padding: 20px; border-radius: 8px; display: flex; justify-content: space-between; align-items: center; }}
                select {{ padding: 10px; font-size: 16px; border-radius: 5px; cursor: pointer; border: none; outline: none; }}
                .table-container {{ background: white; padding: 20px; border-radius: 8px; margin-top: 20px; box-shadow: 0 4px 6px rgba(0,0,0,0.1); overflow-x: auto; }}
                table {{ width: 100%; border-collapse: collapse; text-align: left; min-width: 1200px; }}
                th, td {{ padding: 12px; border-bottom: 1px solid #ddd; vertical-align: top; font-size: 14px; }}
                th {{ background: #f8f9fa; color: #333; position: sticky; top: 0; }}
                tr:hover {{ background-color: #f1f1f1; }}
                a.btn {{ font-size: 14px; color: #1a73e8; text-decoration: none; font-weight: bold; display: inline-block; margin-top: 20px; background: white; padding: 8px 16px; border-radius: 6px; box-shadow: 0 1px 3px rgba(0,0,0,0.1); border: 1px solid #e0e0e0; }}
            </style>
        </head>
        <body>
            <div class="header">
                <div>
                    <h1 style="margin:0;">🔒 Secure Department Portal</h1>
                    <p style="margin:5px 0 0 0; color: #aaa;">Role-Based Access Control (RBAC) & Dynamic Data Masking</p>
                </div>
                <form method="GET" action="/department-dashboard" style="margin:0;">
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
                        <th>Station / Location</th>
                        <th>Coach</th>
                        <th>Seat</th>
                        <th style="width: 20%;">Complaint Details</th>
                        <th>Evidence</th>
                        {sos_th}
                        <th>Status & Resolution</th>
                    </tr>
                    {table_rows}
                </table>
            </div>
            <a href="/admin" class="btn">⬅ Back to Master Admin</a>
        </body>
    </html>
    """

@app.route('/api/generate-upload-url', methods=['POST'])
def generate_upload_url():
    try:
        data = request.get_json()
        file_name = data.get('fileName')
        content_type = data.get('contentType')

        if not file_name or not content_type:
            return jsonify({"error": "Missing fileName or contentType"}), 400

        # 1. Fetch the Service Account Email dynamically from Cloud Run
        metadata_url = "http://metadata.google.internal/computeMetadata/v1/instance/service-accounts/default/email"
        sa_email = requests.get(metadata_url, headers={"Metadata-Flavor": "Google"}).text

        # 2. Get the default, restricted Cloud Run credentials
        default_creds, project = google.auth.default()

        # 3. THE FIX: Create Impersonated Credentials
        # This forcefully unlocks the "Service Account Token Creator" power we added earlier!
        impersonated_creds = impersonated_credentials.Credentials(
            source_credentials=default_creds,
            target_principal=sa_email,
            target_scopes=["https://www.googleapis.com/auth/cloud-platform"],
            lifetime=3600
        )

        unique_filename = f"{uuid.uuid4().hex}_{file_name}"
        
        # 4. Initialize the Storage Client using the IMPERSONATED credentials
        storage_client = storage.Client(credentials=impersonated_creds)
        bucket = storage_client.bucket(EVIDENCE_BUCKET_NAME)
        blob = bucket.blob(unique_filename)

        # 5. Generate the URL (It will now succeed because the impersonated creds have a "signer")
        signed_url = blob.generate_signed_url(
            version="v4",
            expiration=datetime.timedelta(minutes=15),
            method="PUT",
            content_type=content_type
        )

        public_url = f"https://storage.googleapis.com/{EVIDENCE_BUCKET_NAME}/{unique_filename}"

        return jsonify({"signedUrl": signed_url, "publicUrl": public_url})

    except Exception as e:
        print(f"Error generating signed URL: {e}")
        return jsonify({"error": "Could not generate upload URL"}), 500

@app.route('/api/sos', methods=['POST'])
def handle_sos():
    data = request.get_json()
    comp_id_raw = data.get('complaint_id', '')
    user_message = data.get('message', '')

    comp_id_str = str(comp_id_raw).replace('C-', '').replace('c-', '').strip()
    if not comp_id_str.isdigit():
        return jsonify({"reply": "Invalid Complaint ID format. Please use numbers only or 'C-XX'."})

    comp_id = int(comp_id_str)

    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute("SELECT department, timestamp, sos_logs FROM bot_complaints WHERE complaint_id = %s", (comp_id,))
        record = cursor.fetchone()
        if not record:
            release_db_connection(conn)
            return jsonify({"reply": "Complaint ID not found in our system."})
            
        dept, ts, sos_logs = record
        
        from datetime import datetime, timedelta
        if datetime.now() - ts > timedelta(hours=48):
            release_db_connection(conn)
            return jsonify({"reply": "SOS Assistance has expired (only available for 48 hours post-complaint)."})
            
        if dept not in ["Security", "Medical Assistance"]:
            release_db_connection(conn)
            return jsonify({"reply": f"SOS mode is strictly for Security and Medical emergencies. Your original complaint is registered under {dept}."})

        prompt = f"""
        You are the RailMadad SOS Emergency Responder. 
        The passenger is referencing a recent {dept} emergency.
        User's SOS Message: "{user_message}"
        
        Strict Rules:
        1. Limit response to 1-2 sentences.
        2. Provide immediate, practical safety/first-aid advice.
        3. Do NOT provide medical diagnoses or dangerous tactical advice.
        4. ANTI-ABUSE: If the user's message is abusive, testing the system, or unrelated to an emergency, reply EXACTLY with: "SOS mode is strictly for emergency assistance. Please refrain from non-emergency queries."
        5. Be calm and authoritative.
        """
        
        model = genai.GenerativeModel('gemini-3.1-flash-lite-preview')
        response = model.generate_content(prompt)
        ai_reply = response.text
        
        new_log = f"<b>User:</b> {user_message}<br><span style='color:#1a73e8'><b>AI:</b> {ai_reply}</span><br><hr style='border-top:1px solid #ddd; margin:8px 0;'>"
        updated_logs = (sos_logs or "") + new_log
        
        cursor.execute("UPDATE bot_complaints SET sos_logs = %s WHERE complaint_id = %s", (updated_logs, comp_id))
        conn.commit()
        release_db_connection(conn)
        
        return jsonify({"reply": ai_reply})
        
    except Exception as e:
        print(f"SOS Error: {e}")
        return jsonify({"reply": "SOS System Error. Please contact railway staff immediately."})

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=True)