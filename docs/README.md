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
  - Stores past recordings and analysis results locally.  
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
    - Python FastAPI app (`vox/fastapi_app.py`) serving a REST API and using Socket.IO for real-time communication.
    - Uses `librosa`, `aubio`, and `parselmouth` for audio analysis (pitch, HNR, harmonics, formants).
    - Stores user info and vocal data in a PostgreSQL database (hosted on Supabase).
    - Connects to OpenRouter API for LLM-powered feedback and chat.
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
- **pip packages:** See `requirements.txt`

### Environment Variables

Create a `.env` file in the root directory or set environment variables:

- `FASTAPI_SECRET_KEY` — secret key for FastAPI sessions
- `SUPABASE_DB_URL` — your Supabase PostgreSQL connection string
- `OPENROUTER_API_KEY` — your OpenRouter API key for LLM access
- `DISCORD_CLIENT_ID` (optional) — for Discord authentication
- `DISCORD_CLIENT_SECRET` (optional) — for Discord authentication
- `DISCORD_REDIRECT_URI` (optional) — for Discord authentication

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
    - Make sure your `SUPABASE_DB_URL` is correctly set in your `.env` file.
    - Run the database initialization script:
        ```bash
        python init_db.py
        ```
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

- **Backend:** Python, FastAPI, python-socketio, PostgreSQL (Supabase), asyncpg, librosa, aubio, parselmouth
- **Frontend:** HTML5, CSS3, JavaScript, Socket.IO, Tone.js, Chart.js, JustGage, Raphael
- **AI Integration:** OpenRouter API
- **Security:** slowapi for rate limiting
- **License:** GPL-3.0

---

## Developer Notes

- Designed with trans inclusivity and accessibility at its core.
- The backend is a modular FastAPI application located in the `vox/` directory. See `docs/architecture_overview.md` for a detailed breakdown.
- The frontend consists of HTML templates in `templates/`, JavaScript in `static/scripts.js`, and CSS in `static/styles.css`.
- Real-time audio analysis combines browser-side (Tone.js) and server-side (librosa, parselmouth, aubio) processing.
- LLM prompts are carefully crafted to respect pronouns and uplift users.
- A background task cleans up old recordings to save space.
- Contributions are welcome! Please respect the GPL license and the trans-affirming mission of the project.

---

## License

This project is licensed under the GNU General Public License v3.0 (GPL-3.0).  
You are free to use, modify, and share it, but keep it open and respect the community.

---

**With love and pride,  
Shelbeely**
