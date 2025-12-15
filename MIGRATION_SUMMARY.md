# Vox Local-First Migration - Implementation Summary

## Overview
Vox has been successfully migrated from a cloud-based, multi-user application (using Supabase/PostgreSQL) to a local-first, single-user desktop application. This document summarizes the changes made.

## Major Changes

### 1. Database Migration: PostgreSQL → SQLite

**Before:**
- Cloud-hosted PostgreSQL via Supabase
- Required `SUPABASE_DB_URL` environment variable
- Used `asyncpg` library
- Multi-user with user accounts, authentication, sessions

**After:**
- Local SQLite database file (`vox_data.db`)
- Optional `DATABASE_PATH` environment variable (defaults to `vox_data.db`)
- Uses `aiosqlite` library
- Single-user with simplified schema

**Key Changes:**
- Replaced `asyncpg` with `aiosqlite` in `requirements.txt`
- Created new `docs/sqlite_schema.sql` with simplified single-user schema
- Updated `database.py` to use SQLite syntax and aiosqlite API
- Updated all SQL queries from PostgreSQL syntax (`$1, $2`) to SQLite syntax (`?, ?`)
- Removed connection pooling (not needed for SQLite)
- Database auto-initializes on first run

### 2. Authentication Removal

**Removed:**
- `vox/auth.py` - entire authentication module
- User registration and login endpoints
- Email verification system
- Password reset functionality
- Discord OAuth integration
- Session management
- User accounts table
- Password reset table
- Sessions table

**Rationale:**
- Local-first application = single user
- No need for user accounts or authentication
- Simplifies setup and usage
- Enhances privacy

### 3. LLM Integration Updates

**Before:**
- Hardcoded to OpenRouter
- Required `OPENROUTER_API_KEY` and `OPENROUTER_API_BASE`
- Hardcoded model: `google/gemini-2.0-flash-001`

**After:**
- Works with any OpenAI-compatible API
- Uses generic `OPENAI_API_KEY` environment variable
- Optional `OPENAI_API_BASE` for custom API endpoints
- Configurable model via `OPENAI_MODEL` (defaults to `gpt-3.5-turbo`)
- Better error handling for missing API keys

### 4. Data Model Changes

**New Schema:**
```sql
-- Single user preferences (enforced with CHECK constraint)
user_preferences (id, user_name, user_pronouns, target_gender, created_at, updated_at)

-- Vocal analysis data
vocal_data (id, timestamp, pitch, hnr, harmonics, formants, jitter_shimmer, praat_report, recording_path, transformed_path)

-- Chat history
chat_messages (id, user_role, message, timestamp)
```

**Removed Tables:**
- `users` - no longer needed (single user)
- `sessions` - no authentication/sessions
- `password_resets` - no authentication

### 5. Module Updates

#### `vox/database.py`
- Removed session management functions
- Added `get_user_preferences()` and `update_user_preferences()`
- Updated `save_vocal_data_async()` to not use session_id
- Updated `fetch_chat_history_async()` to not filter by session
- All functions now use direct database connection instead of pool

#### `vox/fastapi_app.py`
- Removed auth router import and registration
- Changed from PostgreSQL pool to single SQLite connection
- Added automatic database initialization on startup
- Simplified shutdown handler

#### `vox/socketio_handlers.py`
- Removed session lookups for user data
- Uses `get_user_preferences()` directly
- Simplified vocal data storage (no session_id)

#### `vox/user.py`
- Removed session-based user lookup
- Works directly with single user preferences
- Simplified all endpoints

#### `vox/chat.py`
- Removed session dependencies
- Uses `get_user_preferences()` for pronoun/name info
- Simplified chat history retrieval

#### `vox/recordings.py`
- Removed session-based directory organization
- All recordings stored in single `recordings/` directory
- Removed session lookups for user preferences
- Uses `get_user_preferences()` directly

### 6. Configuration Changes

**New `.env.example`:**
```env
FASTAPI_SECRET_KEY=your-secret-key-here
OPENAI_API_KEY=your-api-key-here
OPENAI_API_BASE=                    # Optional
OPENAI_MODEL=gpt-3.5-turbo         # Optional
DATABASE_PATH=vox_data.db          # Optional
```

**Removed:**
- `SUPABASE_DB_URL`
- `OPENROUTER_API_KEY`
- `OPENROUTER_API_BASE`
- `DISCORD_CLIENT_ID`
- `DISCORD_CLIENT_SECRET`
- `DISCORD_REDIRECT_URI`
- SMTP email configuration

### 7. New Files

**Documentation:**
- `README.md` - Comprehensive guide for local-first setup
- This file (`MIGRATION_SUMMARY.md`)

**Launcher Scripts:**
- `run.sh` - Unix/Linux/Mac launcher
- `run.bat` - Windows launcher

**Database:**
- `docs/sqlite_schema.sql` - SQLite schema definition

### 8. Updated Files

**Configuration:**
- `.gitignore` - Added `*.db` exclusion, allowed `.env.example`
- `requirements.txt` - Changed `asyncpg` to `aiosqlite`
- `.env.example` - Simplified configuration
- `init_db.py` - Updated for SQLite

**Code:**
- `vox/__init__.py` - Removed PostgreSQL pool initialization
- All module files listed in section 5

## Installation & Usage

### Quick Start

1. **Clone and install:**
   ```bash
   git clone https://github.com/shelbeely/Vox.git
   cd Vox
   pip install -r requirements.txt
   ```

2. **Configure:**
   ```bash
   cp .env.example .env
   # Edit .env and add your OPENAI_API_KEY
   ```

3. **Run:**
   ```bash
   # Linux/Mac
   ./run.sh
   
   # Windows
   run.bat
   
   # Or manually:
   python init_db.py
   hypercorn vox.fastapi_app:sio_app --bind 0.0.0.0:3000
   ```

4. **Access:**
   Open http://localhost:3000 in your browser

## Benefits of Local-First Architecture

1. **Privacy:** All data stays on user's computer
2. **No Cloud Dependency:** Works offline (except for AI features)
3. **Simplicity:** No user accounts or authentication to manage
4. **Control:** Users own their data completely
5. **Cost:** No cloud hosting costs
6. **Portability:** Can be packaged as standalone desktop app

## Future Enhancements

### Packaging (Recommended Next Steps)

1. **Create `pyproject.toml`** for modern Python packaging
2. **Use PyInstaller or similar** to create standalone executables
3. **Platform-specific installers:**
   - Windows: Inno Setup or NSIS
   - macOS: create `.app` bundle and `.dmg`
   - Linux: AppImage or Flatpak

### Optional Features

1. **Data Export:** Add ability to export data (JSON, CSV)
2. **Data Import:** Import from previous Vox installations
3. **Backup/Restore:** Automated backup functionality
4. **Offline Mode:** Cache AI responses for offline playback
5. **Multi-Language Support:** Internationalization

## Testing Checklist

- [x] Database initialization works
- [x] Schema creates correctly with default user preferences
- [ ] Voice recording and analysis functions (needs running server + audio)
- [ ] LLM integration works with API key (needs valid API key)
- [ ] User preferences update correctly
- [ ] Chat functionality works
- [ ] Recordings are saved and retrievable
- [ ] History clearing works properly

## Notes for Developers

### Database Access Pattern

Always use the `get_db()` dependency to access the database:

```python
from fastapi import Depends

def get_db(request: Request):
    return request.app.state.db

@router.get("/example")
async def example(db=Depends(get_db)):
    # Use db directly with aiosqlite
    async with db.execute("SELECT * FROM user_preferences") as cursor:
        row = await cursor.fetchone()
```

### User Preferences

Always use helper functions from `database.py`:

```python
from vox.database import get_user_preferences, update_user_preferences

# Get preferences
prefs = await get_user_preferences(db)
name = prefs['user_name']

# Update preferences
await update_user_preferences(db, user_name="Alex", user_pronouns="she/her")
```

### SQL Syntax

Remember to use SQLite syntax:
- Placeholders: `?` not `$1, $2`
- Boolean: `0` or `1` not `TRUE`/`FALSE`
- Timestamps: `CURRENT_TIMESTAMP` not `now()`
- No `RETURNING` clause in INSERT/UPDATE

## Conclusion

Vox has been successfully transformed into a privacy-focused, local-first application that requires minimal configuration and runs entirely on the user's machine. The codebase is simpler, more maintainable, and better aligned with the values of user privacy and data ownership.
