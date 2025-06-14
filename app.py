# backend/app.py

import os
from flask import Flask, request, jsonify
from flask_cors import CORS
from dotenv import load_dotenv
# Import the RAG service function from the new rag_service.py file
from rag_service import get_rag_response, initialize_rag_components # Also import the init function


# Load environment variables from .env file
# dotenv_path=os.path.join(os.path.dirname(__file__), '.env') points to .env in the same directory as app.py
load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), '.env'))

# Initialize Flask app
app = Flask(__name__)
# Enable CORS for all origins during development.
# IMPORTANT: For production, configure CORS more strictly!
CORS(app)

# --- Initialize RAG components when the Flask app starts ---
# This ensures the embedding model, vector store, and LLM are loaded/initialized
# before the first request hits the /api/chat endpoint.
# We call this here in the main app file.
initialize_rag_components()


@app.route('/')
def home():
    """Basic route to confirm the backend is running."""
    return "Mezan Backend is running!"

@app.route('/api/chat', methods=['POST'])
def chat_endpoint():
    """Handles incoming chat requests from the frontend."""
    print('Received request on /api/chat')

    # The RAG service function checks for initialized components internally
    # if llm_model_instance is None: # This check is now inside get_rag_response
    #      print("Error: AI Model instance is not initialized. Cannot process request.")
    #      return jsonify({"error": "AI service not available. Check backend logs."}), 500


    try:
        # Get message and category from the frontend's JSON request
        data = request.get_json()
        user_message = data.get('message')
        category = data.get('category')

        # Basic Input Validation
        if not user_message or not category:
            print('Validation failed: Missing message or category')
            return jsonify({"error": "Bad Request: 'message' and 'category' are required."}), 400
        if not isinstance(user_message, str) or not isinstance(category, str):
            print('Validation failed: Invalid data types')
            return jsonify({"error": "Bad Request: 'message' and 'category' must be strings."}), 400


        print(f"Processing chat for category: '{category}', message: '{user_message}' (Using RAG)")

        # --- Call the RAG service function ---
        # This function now handles retrieval, prompting, and calling the LLM
        print("Calling RAG service for AI response...")
        ai_reply = get_rag_response(user_message, category) # Call the RAG function
        print(f"RAG service returned: {ai_reply[:100]}...") # Log a snippet of the reply

        # Send the AI's reply back to the frontend as JSON
        # If get_rag_response returned an error message string, jsonify handles it.
        return jsonify({"reply": ai_reply})

    except Exception as e:
        # Handle any unexpected errors during request processing in this endpoint
        print(f"Error in /api/chat endpoint: {e}")
        import traceback
        traceback.print_exc()
        # Return a generic error to the frontend
        return jsonify({"error": "Internal Server Error processing request."}), 500

# This block allows running the app directly using `python app.py`
# when FLASK_APP and FLASK_DEBUG are not set as environment variables.
# Using `flask run` is generally preferred when .env is configured.
if __name__ == '__main__':
    # Read host and port from environment if set, otherwise use defaults
    host = os.getenv('FLASK_RUN_HOST', '0.0.0.0')
    port = int(os.getenv('FLASK_RUN_PORT', 5000))
    debug = os.getenv('FLASK_DEBUG', '0') == '1'

    print(f"Attempting to run app with host={host}, port={port}, debug={debug}")
    # Note: initialize_rag_components is called when rag_service is imported above
    app.run(host=host, port=port, debug=debug)