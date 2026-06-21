import os
import sys
import time
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

API_KEY = os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY")

if not API_KEY:
    print(
        "FATAL ERROR: No Gemini API key found.\n"
        "Create one at https://aistudio.google.com/apikey then set:\n"
        "  set GEMINI_API_KEY=your_key_here   (Windows)\n"
        "  export GEMINI_API_KEY=your_key_here (Mac/Linux)"
    )
    sys.exit(1)

# Initialize the Gemini client
try:
    client = genai.Client(api_key=API_KEY)
    print(f"API Key loaded. Client initialized for Gemini. Key prefix: {API_KEY[:4]}...")
except Exception as e:
    print(f"FATAL ERROR: Could not initialize Gemini client: {e}")
    sys.exit(1)

# --- Flask App Setup ---
app = Flask(__name__) 

# --- Configuration ---

MODEL_NAME = os.environ.get("GEMINI_MODEL", "gemini-2.5-flash-lite")
FALLBACK_MODELS = [
    m.strip()
    for m in os.environ.get(
        "GEMINI_FALLBACK_MODELS", "gemini-2.0-flash-lite,gemini-2.0-flash"
    ).split(",")
    if m.strip()
]
MAX_HISTORY_MESSAGES = int(os.environ.get("MAX_HISTORY_MESSAGES", "20"))
MAX_RETRIES = 3
RETRY_BASE_DELAY_SEC = 2

print(f"Primary model: {MODEL_NAME} | Fallbacks: {', '.join(FALLBACK_MODELS) or 'none'}")
SYSTEM_PROMPT = """You are a Mental Health Companion Chatbot designed to support students.
Your main destination is to address high levels of stress, anxiety, and loneliness.
You should provide empathetic, motivational responses and relaxation tips.
Offer support as a safe, AI-driven chatbot.
Prioritize student mental well-being. Try to connect with the patient with chat styling answer. 
Realize the patient's situation and provide a solution to the problem as a friend."""

# CHAT_HISTORY stores the turns in the format required by the API
CHAT_HISTORY = [] 


# --- Core Functions ---

def trim_history():
    """Keep only the most recent messages to reduce token usage and quota pressure."""
    global CHAT_HISTORY
    if len(CHAT_HISTORY) > MAX_HISTORY_MESSAGES:
        CHAT_HISTORY = CHAT_HISTORY[-MAX_HISTORY_MESSAGES:]


def is_zero_quota_error(err: str) -> bool:
    return (
        "RESOURCE_EXHAUSTED" in err
        and "quota_limit_value" in err
        and ("'0'" in err or '"0"' in err)
    )


def quota_exhausted_message() -> str:
    return (
        "The Gemini API quota for your Google Cloud project is currently 0, so requests "
        "cannot be processed. To fix this:\n"
        "1. Open https://aistudio.google.com and check your plan/billing status.\n"
        "2. Create a new API key in a new Google Cloud project if needed.\n"
        "3. Ensure the Generative Language API is enabled for that project.\n"
        "4. Wait a few minutes after enabling billing, then restart this app.\n"
        "5. If quotas still show 0, request an increase at "
        "https://cloud.google.com/docs/quotas/help/request_increase"
    )


def generate_content_with_retry(models, contents, config):
    """Try models in order; retry transient 429 rate limits with exponential backoff."""
    last_error = None

    for model in models:
        for attempt in range(MAX_RETRIES):
            try:
                return client.models.generate_content(
                    model=model,
                    contents=contents,
                    config=config,
                )
            except APIError as e:
                last_error = e
                err = str(e)
                if e.code != 429:
                    raise

                if is_zero_quota_error(err):
                    raise

                if attempt < MAX_RETRIES - 1:
                    delay = RETRY_BASE_DELAY_SEC * (2 ** attempt)
                    print(f"Rate limited on {model}, retrying in {delay}s...")
                    time.sleep(delay)
                    continue

                print(f"Rate limited on {model}, trying next fallback model...")
                break

    if last_error:
        raise last_error
    raise RuntimeError("No models configured for Gemini API requests.")


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
    trim_history()

    models_to_try = [MODEL_NAME] + [
        m for m in FALLBACK_MODELS if m != MODEL_NAME
    ]
    config = genai.types.GenerateContentConfig(
        temperature=0.7,
        system_instruction=SYSTEM_PROMPT,
    )

    try:
        response = generate_content_with_retry(models_to_try, CHAT_HISTORY, config)
        
        # 3. Extract the full response text
        full_response_text = response.text

        # 4. Format and append the model response correctly for history
        model_response_content = {
            "role": "model",
            "parts": [{"text": full_response_text}]
        }
        CHAT_HISTORY.append(model_response_content)
        trim_history()
        
        return full_response_text

    except APIError as e:
        CHAT_HISTORY.pop()
        err = str(e)
        if "ACCESS_TOKEN_TYPE_UNSUPPORTED" in err or "UNAUTHENTICATED" in err:
            return (
                "ERROR: Gemini API authentication failed. Your API key may be invalid, "
                "expired, or revoked. Create a new key at https://aistudio.google.com/apikey "
                "and set the GEMINI_API_KEY environment variable, then restart the app."
            )
        if is_zero_quota_error(err) or (
            e.code == 429 and "RESOURCE_EXHAUSTED" in err
        ):
            return quota_exhausted_message()
        if "API_KEY_INVALID" in err or "permission_denied" in err.lower():
            return "ERROR: API Key is invalid or not authorized. Check GEMINI_API_KEY and ensure billing is enabled."
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
