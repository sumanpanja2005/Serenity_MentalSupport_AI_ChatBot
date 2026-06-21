# Serenity Mental Support AI ChatBot

A Flask web app that provides empathetic mental health support for students, powered by Google's Gemini API.

## Prerequisites

- Python 3.10 or newer
- A [Gemini API key](https://aistudio.google.com/apikey)

## Project Structure

```
Serenity_MentalSupport_AI_ChatBot/
├── app.py              # Flask server and Gemini API integration
├── requirements.txt    # Python dependencies
├── templates/
│   └── index.html      # Chat UI
└── README.md
```

## Setup

### 1. Clone or download the project

```powershell
cd "D:\FOOTBALL TOURNAMENT\Serenity_MentalSupport_AI_ChatBot"
```

### 2. Create a virtual environment (recommended)

**Windows (PowerShell):**

```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
```

**macOS / Linux:**

```bash
python3 -m venv venv
source venv/bin/activate
```

### 3. Install dependencies

```powershell
pip install -r requirements.txt
```

### 4. Set your Gemini API key

The app reads the key from the `GEMINI_API_KEY` or `GOOGLE_API_KEY` environment variable.

**Windows (PowerShell):**

```powershell
$env:GEMINI_API_KEY = "your_api_key_here"
```

**Windows (Command Prompt):**

```cmd
set GEMINI_API_KEY=your_api_key_here
```

**macOS / Linux:**

```bash
export GEMINI_API_KEY=your_api_key_here
```

> Do not commit your API key to git. Keep it in an environment variable only.

## Run the App

```powershell
python app.py
```

You should see:

```
API Key loaded. Client initialized for Gemini. Key prefix: AIza...
 * Running on http://0.0.0.0:5000
```

Open your browser and go to:

```
http://localhost:5000
```

Type a message in the chat UI to talk with the bot.

## Configuration

| Variable | Description | Default |
|----------|-------------|---------|
| `GEMINI_API_KEY` | Gemini API key (preferred) | — |
| `GOOGLE_API_KEY` | Alternative API key variable | — |
| `GEMINI_MODEL` | Primary Gemini model | `gemini-2.5-flash-lite` |
| `GEMINI_FALLBACK_MODELS` | Comma-separated fallback models | `gemini-2.0-flash-lite,gemini-2.0-flash` |
| `MAX_HISTORY_MESSAGES` | Max chat history messages kept | `20` |
| `PORT` | Server port | `5000` |

Example with a custom port:

```powershell
$env:PORT = 8080
python app.py
```

## Troubleshooting

### `FATAL ERROR: No Gemini API key found`

Set `GEMINI_API_KEY` before running the app (see step 4 above).

### `401 UNAUTHENTICATED` or `ACCESS_TOKEN_TYPE_UNSUPPORTED`

Your API key is invalid, expired, or revoked. Create a new key at [Google AI Studio](https://aistudio.google.com/apikey), update the environment variable, and restart the app.

### `API Key is invalid or not authorized`

Confirm the key is correct and that the **Generative Language API** is enabled for your Google Cloud project. Billing may be required depending on your usage.

### `429 RESOURCE_EXHAUSTED` / quota exceeded

This usually means your Google Cloud project has **no quota left** (often shown as `quota_limit_value: 0`).

1. Open [Google AI Studio](https://aistudio.google.com) and verify your plan/billing.
2. Create a **new API key** in a **new Google Cloud project** if the current one shows 0 quota.
3. Enable the **Generative Language API** for that project.
4. Wait a few minutes after enabling billing, then restart the app.
5. If quotas still show `0 to 0` in [Google Cloud Console](https://console.cloud.google.com/apis/api/generativelanguage.googleapis.com/quotas), [request a quota increase](https://cloud.google.com/docs/quotas/help/request_increase).

The app automatically retries transient rate limits and falls back to lighter models (`gemini-2.5-flash-lite` by default).

### Port already in use

Change the port:

```powershell
$env:PORT = 8080
python app.py
```

## Tech Stack

- **Backend:** Flask
- **AI:** Google Gemini (`gemini-2.5-flash-lite` by default) via `google-genai`
- **Frontend:** HTML/CSS/JavaScript (`templates/index.html`)

## Disclaimer

This chatbot is for general emotional support only. It is not a substitute for professional medical advice, diagnosis, or treatment. If you are in crisis, contact a qualified mental health professional or emergency services.
