import os
import sys
import traceback
import warnings 
# FIX: Import genai client directly from google
from google import genai 
from google.genai.errors import APIError
from flask import Flask, render_template, request, jsonify 

# =========================================================================
# Warning filter to suppress Pydantic warnings
# =========================================================================
warnings.filterwarnings(
    "ignore", 
    category=UserWarning,
    module="pydantic"
)
# =========================================================================


# --- API Key Setup ---

# The API Key is hardcoded here as requested.
API_KEY = "AQ.Ab8RN6JPlE7hl15e8-5vWpgiIUV61yV2NxLty1iG9zFzuuRVJw" # <-- Your hardcoded key

# Initialize the Gemini client
try:
    # FIX: Use genai.Client() from the correct import
    client = genai.Client(api_key=API_KEY)
    print(f"API Key loaded. Client initialized for Gemini. Key prefix: {API_KEY[:4]}...")
except Exception as e:
    print(f"FATAL ERROR: Could not initialize Gemini client: {e}")
    sys.exit(1)

# --- Flask App Setup ---
app = Flask(__name__) 

# --- Configuration ---

MODEL_NAME = "gemini-2.5-flash" 
SYSTEM_PROMPT = """You are a Mental Health Companion Chatbot designed to support students.
Your main destination is to address high levels of stress, anxiety, and loneliness.
You should provide empathetic, motivational responses and relaxation tips.
Offer support as a safe, AI-driven chatbot.
Prioritize student mental well-being. Try to connect with the patient with chat styling answer. 
Realize the patient's situation and provide a solution to the problem as a friend."""

# CHAT_HISTORY stores the turns in the format required by the API
CHAT_HISTORY = [] 


# --- Core Functions ---

def call_api_no_stream(user_input):
    """
    (Flask-Compatible) Sends the user input to the Gemini API and returns the full response text.
    """
    global CHAT_HISTORY
    
    # 1. Format and append the user message
    user_message_content = {
        "role": "user", 
        "parts": [{"text": user_input}] 
    }
    CHAT_HISTORY.append(user_message_content)

    try:
        # 2. Call the non-streaming API
        response = client.models.generate_content(
            model=MODEL_NAME,
            contents=CHAT_HISTORY,
            # FIX: Use genai.types.GenerateContentConfig()
            config=genai.types.GenerateContentConfig(
                temperature=0.7,
                system_instruction=SYSTEM_PROMPT 
            )
        )
        
        # 3. Extract the full response text
        full_response_text = response.text

        # 4. Format and append the model response correctly for history
        model_response_content = {
            "role": "model",
            "parts": [{"text": full_response_text}]
        }
        CHAT_HISTORY.append(model_response_content)
        
        return full_response_text

    except APIError as e:
        err = str(e)
        if "API_KEY_INVALID" in err or "permission_denied" in err.lower():
            return "ERROR: API Key is invalid or not authorized. Check your hardcoded key and ensure billing is enabled."
        traceback.print_exc()
        return f"API request failed: {err}"
    except Exception as e:
        traceback.print_exc()
        return f"An unexpected error occurred: {e}"


# --- Flask Routes --- 
@app.route('/')
def index():
    # Renders the index.html template (must be in the 'templates' folder)
    return render_template('index.html')

@app.route('/chat', methods=['POST'])
def chat():
    user_message = request.json.get('message')
    if not user_message:
        return jsonify({"response": "Please enter a message."}), 400

    bot_response = call_api_no_stream(user_message)
    
    return jsonify({"response": bot_response})

if __name__ == "__main__":
    # FIX: Bind the application to '0.0.0.0' and the required PORT environment variable
    port = int(os.environ.get('PORT', 5000)) # Use 5000 as a fallback for local testing
    app.run(host='0.0.0.0', port=port, debug=False)
