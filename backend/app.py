# backend/app.py
import pandas as pd
from flask import Flask, request, jsonify
import sqlite3
import os # We've added 'os' to help debug

print("--- Starting app.py ---")

# --- 1. Initial Setup ---
app = Flask(__name__)

# Let's build the file path more safely
# __file__ is the current file (app.py)
# os.path.dirname(__file__) is the 'backend' folder
# os.path.join(...) builds a correct path for any OS
backend_dir = os.path.dirname(__file__)
project_root = os.path.abspath(os.path.join(backend_dir, os.pardir))
pnr_file_path = os.path.join(project_root, 'data', 'pnr_database.csv')

print(f"Looking for data file at: {pnr_file_path}")

try:
    pnr_data = pd.read_csv(pnr_file_path, index_col='PNR')
    print("✅ PNR dataset loaded successfully.")
except FileNotFoundError:
    print("❌ ERROR: FileNotFoundError. The file was not found at the path.")
    print("Please make sure your 'data' folder and 'pnr_database.csv' file exist.")
    pnr_data = None
except Exception as e:
    # This will catch ANY other error (e.g., file corrupt, permissions, etc.)
    print(f"❌ AN UNEXPECTED ERROR OCCURRED: {e}")
    pnr_data = None


# --- 2. API Endpoint Definition ---
@app.route('/webhook', methods=['POST'])
def dialogflow_webhook():
    request_json = request.get_json()
    
    try:
        intent_name = request_json['queryResult']['intent']['displayName']
    except (KeyError, TypeError):
        return jsonify({"fulfillmentText": "Error: Invalid request format."})

    if intent_name == 'capture_user_query':
        # Get the query text from the Dialogflow JSON
        try:
            user_query_text = request_json['queryResult']['parameters']['user_query']
        except KeyError:
            return jsonify({"fulfillmentText": "Error: Could not find user_query parameter."})
        
        # Save the query to the database
        try:
            conn = sqlite3.connect('railmadad.db')
            cursor = conn.cursor()
            cursor.execute("INSERT INTO queries (query_text) VALUES (?)", (user_query_text,))
            conn.commit()
            new_query_id = cursor.lastrowid
            conn.close()
            
            response_text = f"Thank you. Your query has been registered with ID: Q-{new_query_id}. We will get back to you shortly."
            
            return jsonify({"fulfillmentText": response_text})
        
        except Exception as db_e:
            print(f"DATABASE ERROR: {db_e}")
            return jsonify({"fulfillmentText": "Error: Could not write to the database."})
    
    else:
        return jsonify({"fulfillmentText": "Error: Unrecognized intent."})

# --- 3. Run the Server ---
if __name__ == '__main__':
    if pnr_data is None:
        print("--- Server NOT starting because pnr_data failed to load. ---")
    else:
        print("--- Starting Flask server... ---")
        app.run(host='0.0.0.0', port=5000, debug=True)