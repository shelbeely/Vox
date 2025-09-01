# Vox Modular Architecture Overview

## Entry Point

- **`vox/fastapi_app.py`**
  - This is the main entry point for the application, run with Hypercorn.
  - It initializes the FastAPI application (`app`) and the Socket.IO server (`sio`).
  - It creates an `sio_app` that wraps the FastAPI app to handle both HTTP and Socket.IO traffic.
  - It sets up middleware for sessions and rate limiting.
  - It mounts the `/static` directory for serving static files.
  - It initializes the database connection pool on startup.
  - It includes all the API routers from the other modules in the `vox` package.

## Package Structure (`vox/`)

```
vox/
├── __init__.py          # Makes the 'vox' directory a Python package.
├── fastapi_app.py       # Main application entry point (FastAPI and Socket.IO setup).
├── main.py              # Router for the main application routes (e.g., the home page).
├── user.py              # Router for user-related operations (profile, etc.).
├── auth.py              # Router for authentication (e.g., Discord OAuth).
├── recordings.py        # Router for handling recording-related API calls.
├── chat.py              # Router for the chat endpoint with the LLM.
├── socketio_handlers.py # Defines all Socket.IO event handlers.
├── audio_processing.py  # Contains functions for audio feature extraction (using parselmouth, aubio, etc.).
├── database.py          # Helper functions for interacting with the database.
├── utils.py             # Utility functions and constants.
├── llm.py               # Logic for interacting with the LLM (OpenRouter).
├── limiter.py           # Rate limiter configuration.
├── templates.py         # Template rendering setup.
```

## API Routers

The application is organized into several `APIRouter` modules, which are included in the main `FastAPI` app in `vox/fastapi_app.py`:

- **`main_router`**: `/` (home page)
- **`user_router`**: `/user` (user info, profile)
- **`auth_router`**: `/auth` (authentication)
- **`recordings_router`**: `/recordings` (saving/managing recordings)
- **`chat_router`**: `/chat` (chat endpoint)

## Socket.IO Events

Handlers for real-time communication are defined in `vox/socketio_handlers.py`:

- `connect`: Handles a new client connection.
- `disconnect`: Handles a client disconnection.
- `start_recording`: Signals the start of a recording session.
- `stop_recording`: Signals the end of a recording session and triggers LLM feedback.
- `raw_audio`: Receives raw audio data from the client for real-time analysis.
- `save_recording`: Handles the event to save a recording.

## Constants & Config

- **Environment Variables**: API keys, database URLs, and secret keys are managed through environment variables (loaded from a `.env` file).
- **LLM Prompt**: The base prompt for the LLM is defined in `vox/utils.py`.
- **Static Files**: Located in the `static/` directory.
- **Templates**: Located in the `templates/` directory.

## Database

- **PostgreSQL**: The application uses a PostgreSQL database, hosted on Supabase.
- **`asyncpg`**: The `asyncpg` library is used for asynchronous database access.
- **Connection Pool**: A connection pool is created on application startup in `vox/fastapi_app.py`.
- **Database Helpers**: Asynchronous database helper functions are located in `vox/database.py`.

## LLM Integration

- **OpenRouter**: The application integrates with the OpenRouter API to access various language models.
- **`vox/llm.py`**: This module contains the logic for constructing prompts and making API calls to the LLM.
- The LLM is used for generating personalized feedback on voice recordings and for the chat feature.

---

_Last updated: August 31, 2025_
