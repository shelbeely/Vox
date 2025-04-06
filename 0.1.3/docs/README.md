# Vox - A Voice Therapy Coach for Trans Individuals

Vox is an open-source, affirming voice training web app designed specifically for trans people. It empowers users to explore, analyze, and develop their authentic voice through real-time feedback, personalized coaching, and inclusive design.

Created with pride by [Shelbeely](https://github.com/shelbeely), a trans woman developer.  
Licensed under GPL-3.0 — share the love, keep it open!

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
  - Python Flask app (`app.py`) serving REST API and Socket.IO for real-time communication.  
  - Uses `librosa` and `aubio` for audio analysis (pitch, harmonics, formants).  
  - Stores user info and vocal data in SQLite (`vocal_data.db`).  
  - Connects to OpenRouter API for LLM-powered feedback and chat.

- **Frontend:**  
  - HTML5 interface (`index.html`) with accessible controls and visualizations.  
  - JavaScript (`scripts.js`) handles audio capture, visualization, Socket.IO events, and API calls.  
  - Styled with CSS (`styles.css`), including responsive design and animations.

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
- **pip packages:**  
  `flask flask-socketio flask-wtf flask-limiter requests numpy librosa aubio`

### Environment Variables

Create a `.env` file or set environment variables:

- `FLASK_SECRET_KEY` — secret key for Flask sessions
- `OPENROUTER_API_KEY` — your OpenRouter API key for LLM access

### Installation Steps

1. **Clone the repository**

```bash
git clone https://github.com/shelbeely/vox.git
cd vox/0.1.3
```

2. **Install Python dependencies**

```bash
pip install flask flask-socketio flask-wtf flask-limiter requests numpy librosa aubio
```

3. **Run the Flask app**

```bash
python app.py
```

4. **Access Vox**

Open your browser and navigate to `http://localhost:5000`

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

- **Backend:** Python, Flask, Flask-SocketIO, SQLite, librosa, aubio, requests
- **Frontend:** HTML5, CSS3, JavaScript, Socket.IO, Tone.js, Chart.js, JustGage, Raphael
- **AI Integration:** OpenRouter API with DeepSeek Chat model
- **Security:** Flask-WTF CSRF, Flask-Limiter rate limiting
- **License:** GPL-3.0

---

## Developer Notes

- Designed with trans inclusivity and accessibility at its core.
- Modular codebase:  
  - `app.py` — backend server, API, audio analysis, LLM integration  
  - `index.html` — UI layout  
  - `scripts.js` — client logic, audio capture, visualization  
  - `styles.css` — styling and animations
- Real-time audio analysis combines browser-side (Tone.js) and server-side (librosa, aubio) processing.
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
