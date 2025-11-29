# Vox ([GitHub Repository](https://github.com/shelbeely/Vox)) - A Voice Therapy Coach for Trans Individuals

Vox is an open-source, affirming voice training web app designed specifically for trans people. It empowers users to explore, analyze, and develop their authentic voice through real-time feedback, personalized coaching, and inclusive design.

Created with pride by [Shelbeely](https://github.com/shelbeely) ([Linktree](https://linktr.ee/Shelbeely)), a trans woman developer.  
Licensed under GPL-3.0 — share the love, keep it open!

---

## Links

- [Linktree](https://linktr.ee/Shelbeely)
- [GitHub Repository](https://github.com/shelbeely/Vox)

---

## Table of Contents

- [Features](#features)
- [How It Works](#how-it-works)
- [Setup & Installation](#setup--installation)
- [Usage Guide](#usage-guide)
- [Technologies Used](#technologies-used)
- [Developer Notes](#developer-notes)
- [License](#license)

---

## Features

- **Real-Time Voice Analysis:**  
  - Detects pitch, harmonic-to-noise ratio (HNR), harmonics, and formants live as you speak or sing.  
  - Visualizes data with charts and gauges for instant feedback.

- **Personalized Coaching:**  
  - Integrates with OpenRouter LLM API to provide supportive, pronoun-aware feedback tailored to your goals.  
  - Chat with Vox, your affirming AI coach, for guidance and encouragement.

- **Pronoun Inclusivity:**  
  - Extensive pronoun options, including neopronouns and mixed sets.  
  - Dynamic pronoun handling in feedback and chat, respecting your identity.

- **Target Pitch Practice:**  
  - Play a reference tone to help you match your desired pitch.  
  - Visual cues indicate if your pitch is within your target range.

- **Session History:**  
  - Stores past recordings and analysis results in the database.  
  - Review your progress over time and replay recordings.

- **User Customization:**  
  - Set your name, pronouns, and target gender presentation.  
  - Adjust target pitch frequency.

- **Security & Fair Use:**  
  - CSRF protection, rate limiting, and session management.  
  - Cleans up old recordings automatically.

---

## How It Works

### Architecture Overview

- **Backend:**  
  - Python FastAPI app (`vox/fastapi_app.py`) serving REST API with python-socketio for real-time communication.  
  - Uses `librosa`, `aubio`, and `praat-parselmouth` for audio analysis (pitch, harmonics, formants, HNR, jitter/shimmer).  
  - Stores user info and vocal data in PostgreSQL (Supabase).  
  - Connects to OpenRouter API for LLM-powered feedback and chat (using Gemini 2.0 Flash model).

- **Frontend:**  
  - HTML5 interface (`templates/index.html`) with accessible controls and visualizations.  
  - JavaScript (`static/scripts.js`) handles audio capture, visualization, Socket.IO events, and API calls.  
  - Styled with CSS (`static/styles.css`), including responsive design and animations.

### Data Flow

1. User records voice via browser microphone.
2. Audio is streamed to backend via Socket.IO.
3. Backend analyzes audio, extracts pitch, HNR, harmonics, formants.
4. Frontend updates charts and gauges in real time.
5. User can save recordings, which are stored on server and linked to their session.
6. LLM generates personalized feedback based on vocal metrics and user profile.
7. User can chat with Vox for additional support.

---

## Setup & Installation

### Prerequisites

- **Python 3.8+**
- **Node.js (for frontend development, optional)**
- **PostgreSQL database (Supabase recommended)**
- **pip packages:**  
  See `requirements.txt` for the full list. Key packages include FastAPI, Hypercorn, python-socketio, asyncpg, librosa, aubio, praat-parselmouth, and openai.

### Environment Variables

Create a `.env` file or set environment variables:

- `FASTAPI_SECRET_KEY` — secret key for session middleware
- `OPENROUTER_API_KEY` — your OpenRouter API key for LLM access
- `OPENROUTER_API_BASE` — (optional) OpenRouter API base URL, defaults to `https://openrouter.ai/api/v1`
- `SUPABASE_DB_URL` — PostgreSQL connection string for Supabase database

### Installation Steps

1. **Clone the repository**

```bash
git clone https://github.com/shelbeely/vox.git
cd vox
```

2. **Install Python dependencies**

```bash
pip install -r requirements.txt
```

3. **Set up the database**

Run the SQL schema in `docs/supabase_schema.sql` on your PostgreSQL/Supabase instance.

4. **Run the app with Hypercorn**

```bash
hypercorn vox.fastapi_app:sio_app --bind 0.0.0.0:3000
```

5. **Access Vox**

Open your browser and navigate to `http://localhost:3000`

---

## Usage Guide

### Recording & Analysis

- Click the **mic** button to start recording.
- Speak or sing; watch your **pitch**, **HNR**, **harmonics**, and **formants** update live.
- Click **stop** to end recording.
- Review your performance in the **history** list.
- Play back saved recordings.

### Setting Your Profile

- Enter your **name** and select your **pronouns** (including neopronouns or mixed sets).
- Choose your **target gender** (feminine, masculine, or unspecified).
- Save your info to personalize feedback and chat.

### Target Pitch Practice

- Set a **target pitch** frequency (Hz).
- Click **start target pitch** to hear a reference tone.
- Match your voice to the tone; visual cues help guide you.
- Click **stop target pitch** to silence the tone.

### Chat & Feedback

- Type messages in the chat box to talk with Vox.
- Receive affirming, pronoun-aware responses.
- After recordings, Vox provides detailed vocal feedback powered by LLM.

### Managing History

- View past performances with pitch, HNR, harmonics, and formants.
- Play back recordings.
- Clear history to start fresh.

---

## Technologies Used

- **Backend:** Python, FastAPI, python-socketio, PostgreSQL (Supabase), librosa, aubio, praat-parselmouth, requests, asyncpg, openai
- **Frontend:** HTML5, CSS3, JavaScript, Socket.IO, Tone.js, Chart.js, JustGage, Raphael
- **AI Integration:** OpenRouter API with Gemini 2.0 Flash model
- **Security:** slowapi rate limiting, session middleware with itsdangerous, bcrypt password hashing
- **License:** GPL-3.0

---

## Developer Notes

- Designed with trans inclusivity and accessibility at its core.
- Modular codebase:  
  - `vox/fastapi_app.py` — FastAPI server, routers, Socket.IO integration  
  - `vox/audio_processing.py` — audio analysis (pitch, formants, HNR, harmonics)  
  - `vox/llm.py` — LLM integration for feedback and chat  
  - `vox/socketio_handlers.py` — real-time Socket.IO event handlers  
  - `vox/database.py` — database operations (sessions, vocal data, chat)  
  - `vox/auth.py` — authentication (email/password, Discord OAuth)  
  - `vox/user.py` — user profile and preferences  
  - `vox/recordings.py` — recording management  
  - `templates/index.html` — UI layout  
  - `static/scripts.js` — client logic, audio capture, visualization  
  - `static/styles.css` — styling and animations
- Real-time audio analysis combines browser-side (Tone.js) and server-side (librosa, aubio, praat-parselmouth) processing.
- LLM prompts are carefully crafted to respect pronouns and uplift users.
- Cleans up old recordings after ~40 days to save space.
- Contributions welcome! Please respect the GPL license and trans-affirming mission.

---

## License

This project is licensed under the GNU General Public License v3.0 (GPL-3.0).  
You are free to use, modify, and share it, but keep it open and respect the community.

---

**With love and pride,  
Shelbeely**
