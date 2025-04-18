# Vox Modular Architecture Overview

## Entry Point

- **`main.py`**  
  Starts the app by importing `app` and `socketio` from the package and running the server.

## Package Structure (`app/`)

```
app/
├── __init__.py          # Initializes Flask app, SocketIO, CSRF, Limiter, DB pool, registers Blueprints
├── main.py              # Home page route
├── user.py              # User info, target gender, profile, performances
├── auth.py              # Registration, login, email verification, password reset, Discord OAuth
├── recordings.py        # Save recordings, clear history, convert recordings
├── chat.py              # Chat endpoint with LLM
├── socket_handlers.py   # SocketIO event handlers (start/stop recording, audio stream, save recording)
├── audio_processing.py  # Audio feature extraction (pitch, formants, HNR, jitter/shimmer, harmonics)
├── database.py          # Async database helper functions
├── utils.py             # Utility functions, constants, pronoun examples, cleanup
├── llm.py               # LLM prompt construction and OpenAI API calls
```

## Blueprints

- **`main_bp`**: `/` (home page)
- **`user_bp`**: `/user` (user info, profile, performances)
- **`auth_bp`**: `/auth` (registration, login, OAuth)
- **`recordings_bp`**: `/recordings` (save, clear, convert recordings)
- **`chat_bp`**: `/chat` (chat endpoint)

Registered in `app/__init__.py`.

## SocketIO Events

- `start_recording`
- `stop_recording`
- `raw_audio`
- `save_recording`

Handlers in `app/socket_handlers.py`.

## Constants & Config

- **`LLM_PERSONALITY_PROMPT_BASE`**: in `app/utils.py`
- **`PRONOUN_EXAMPLES`**: in `app/utils.py`
- **Folders**: `uploads/`, `recordings/`
- **API keys**: via environment variables
- **Database URL**: via environment variable

## Database

- Supabase PostgreSQL via `asyncpg`
- Connection pool initialized in `app/__init__.py`
- Helpers in `app/database.py`

## LLM Integration

- OpenAI API (via OpenRouter)
- Functions in `app/llm.py`
- Used in chat and feedback generation

## Deprecated

- **`app.py`**:  
  Monolithic legacy file, now deprecated.  
  **Do not edit.**  
  Will be removed in the future.

---

_Last updated: April 9, 2025_
