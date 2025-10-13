import os
import sys
import traceback
import warnings # <-- Ensure this import is present
from google import genai
from google.genai.errors import APIError
from flask import Flask, render_template, request, jsonify # <-- Add Flask imports

# =========================================================================
# FIX: Simplified and moved the warning filter to execute immediately
# This suppresses the Pydantic serialization warnings that clutter the CLI.
# The warnings are harmless and indicate an internal type conversion in the SDK.
# =========================================================================
warnings.filterwarnings(
    "ignore", 
    category=UserWarning,
    module="pydantic"
)
# =========================================================================


# --- API Key Setup ---

# The API Key is hardcoded here as requested.
API_KEY = "AIzaSyDQsbb02MzpSADHm0VwYCxKKCYyawNiQeQ" # <-- Your hardcoded key

# Initialize the Gemini client
try:
    client = genai.Client(api_key=API_KEY)
    print(f"API Key loaded. Client initialized for Gemini. Key prefix: {API_KEY[:4]}...")
except Exception as e:
    print(f"FATAL ERROR: Could not initialize Gemini client: {e}")
    sys.exit(1)

# --- Flask App Setup ---
app = Flask(__name__) # <-- Initialize Flask app

# --- Configuration ---

MODEL_NAME = "gemini-2.5-flash" 
SYSTEM_PROMPT = """You are a Mental Health Companion Chatbot designed to support students.
Your main destination is to address high levels of stress, anxiety, and loneliness.
You should provide empathetic, motivational responses and relaxation tips.
Detect user mood through sentiment analysis (internally, not explicitly stating it).
Offer support as a safe, AI-driven chatbot.
Prioritize student mental well-being.try to Connect with the patient with chat styling answer 
realize the patient's situation and provide a solution to the problem as a friend.""" # <-- Updated SYSTEM_PROMPT

# CHAT_HISTORY stores the turns in the format required by the API
CHAT_HISTORY = [] 


# --- Core Functions ---

def call_api_stream(user_input):
    """
    Sends the user input to the Gemini API and streams the response.
    Returns the complete response text.
    """
    global CHAT_HISTORY
    
    # 1. Format and append the user message correctly (This is NOT the source of the warning)
    user_message_content = {
        "role": "user", 
        "parts": [{"text": user_input}] 
    }
    CHAT_HISTORY.append(user_message_content)

    full_response_text = ""
    try:
        # 2. Call the streaming API
        response_stream = client.models.generate_content_stream(
            model=MODEL_NAME,
            contents=CHAT_HISTORY,
            config=genai.types.GenerateContentConfig(
                temperature=0.7,
                system_instruction=SYSTEM_PROMPT 
            )
        )

        # 3. Stream the response chunks
        sys.stdout.write("Chatbot: ")
        for chunk in response_stream:
            text = chunk.text
            sys.stdout.write(text)
            sys.stdout.flush()
            full_response_text += text
        sys.stdout.write("\n") 

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
            return ("ERROR: API Key is invalid or not authorized. "
                    "Please check your hardcoded key and ensure billing is enabled.")
        traceback.print_exc()
        return f"\nAPI request failed: {err}"
    except Exception as e:
        traceback.print_exc()
        return f"\nAn unexpected error occurred: {e}"


def main():
    print(f"Chatbot (Model: {MODEL_NAME}): Hello! Type 'quit' to exit.\n")

    while True:
        try:
            user_input = input("You: ").strip()
        except EOFError: 
            break
        
        if not user_input:
            continue
            
        if user_input.lower() in ("quit", "exit"):
            print("\nChatbot: Goodbye! 👋")
            break
            
        call_api_stream(user_input)

# --- Flask Routes --- # <-- Add Flask routes
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/chat', methods=['POST'])
def chat():
    user_message = request.json.get('message')
    if not user_message:
        return jsonify({"response": "Please enter a message."}), 400

    bot_response = call_api_stream(user_message)
    return jsonify({"response": bot_response})

if __name__ == "__main__":
    # main() # <-- Comment out the command line main function
    app.run(debug=True) # <-- Run the Flask app in debug mode