# main.py
import pandas as pd
import sqlite3
import os

# --- 1. Global Setup (Loads the PNR data) ---
# This part is a bit tricky, we must load the file from the function's environment
# For now, we will skip this to get the query part working.
# We will add the PNR verification in the next phase.

def handle_query_intent(request_json):
    """Handles the logic for the 'capture_user_query' intent."""
    
    # 1. Get the query text from the Dialogflow JSON
    try:
        user_query_text = request_json['queryResult']['parameters']['user_query']
    except KeyError:
        return {"fulfillmentText": "Error: Could not find user_query parameter."}

    # 2. Save the query to a database
    # NOTE: Cloud Functions can't easily write to a local .db file.
    # For a prototype, the best way is to just skip the database.
    # We will just generate a fake ID.
    
    # In a real project, this is where you would write to Google Firestore (database)
    
    fake_query_id = 1001 # Simulating a database ID
    
    # 3. Create the response text for the user
    response_text = f"Thank you. Your query has been registered with ID: Q-{fake_query_id}. We will get back to you shortly."
    
    # 4. Send this text back to Dialogflow
    return {"fulfillmentText": response_text}

def dialogflow_webhook(request):
    """This is the main function that Google Cloud will run."""
    
    # Get the JSON data that Dialogflow sent
    request_json = request.get_json()
    
    try:
        intent_name = request_json['queryResult']['intent']['displayName']
    except (KeyError, TypeError):
        return {"fulfillmentText": "Error: Invalid request format."}

    # This is the "if-else" logic to decide what to do
    if intent_name == 'capture_user_query':
        response_data = handle_query_intent(request_json)
    
    # (Later, we will add: elif intent_name == 'verify_pnr':)
    
    else:
        response_data = {"fulfillmentText": "Error: Unrecognized intent."}
    
    # Send the final JSON response back to Dialogflow
    from flask import jsonify
    return jsonify(response_data)