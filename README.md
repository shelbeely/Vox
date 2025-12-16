# Vox - A Local-First Voice Therapy Coach

Vox is an open-source, affirming voice training application designed specifically for trans people. It empowers users to explore, analyze, and develop their authentic voice through real-time feedback, personalized coaching, and inclusive design.

**Now available as a local-first application** - no cloud services required! Your data stays on your computer.

Created with pride by [Shelbeely](https://github.com/shelbeely) ([Linktree](https://linktr.ee/Shelbeely)), a trans woman developer.  
Licensed under GPL-3.0 — share the love, keep it open!

---

## ✨ Features

- **Real-Time Voice Analysis:**  
  - Detects pitch, harmonic-to-noise ratio (HNR), harmonics, and formants live as you speak or sing.  
  - Visualizes data with charts and gauges for instant feedback.

- **Personalized AI Coaching:**  
  - Integrates with OpenAI-compatible APIs (OpenAI, OpenRouter, etc.) to provide supportive, pronoun-aware feedback tailored to your goals.  
  - Chat with Vox, your affirming AI coach, for guidance and encouragement.

- **Pronoun Inclusivity:**  
  - Extensive pronoun options, including neopronouns and mixed sets.  
  - Dynamic pronoun handling in feedback and chat, respecting your identity.

- **Target Pitch Practice:**  
  - Play a reference tone to help you match your desired pitch.  
  - Visual cues indicate if your pitch is within your target range.

- **Session History:**  
  - Stores past recordings and analysis results locally in a SQLite database.  
  - Review your progress over time and replay recordings.

- **Privacy-First:**  
  - All data stored locally on your computer.  
  - No cloud services, no user accounts, no external servers.
  - You control your data completely.

---

## 🚀 Quick Start

### Prerequisites

- **Python 3.8+**
- **pip** (Python package manager)

### Installation

1. **Clone the repository**

```bash
git clone https://github.com/shelbeely/Vox.git
cd Vox
```

2. **Install Python dependencies**

```bash
pip install -r requirements.txt
```

3. **Configure your environment**

Copy the example environment file and add your OpenAI-compatible API key:

```bash
cp .env.example .env
```

Edit `.env` and add your API key:

```env
OPENAI_API_KEY=your-api-key-here
```

For OpenRouter, also set:
```env
OPENAI_API_BASE=https://openrouter.ai/api/v1
OPENAI_MODEL=google/gemini-2.0-flash-001
```

4. **Initialize the database**

```bash
python init_db.py
```

5. **Run the application**

```bash
hypercorn vox.fastapi_app:sio_app --bind 0.0.0.0:3000
```

6. **Open your browser**

Navigate to `http://localhost:3000` and start using Vox!

---

## 🎯 Usage Guide

### Setting Your Profile

- Enter your **name** and select your **pronouns** (including neopronouns or mixed sets).
- Choose your **target gender** (feminine, masculine, or unspecified).
- Save your info to personalize feedback and chat.

### Recording & Analysis

- Click the **mic** button to start recording.
- Speak or sing; watch your **pitch**, **HNR**, **harmonics**, and **formants** update live.
- Click **stop** to end recording.
- Review your performance in the **history** list.
- Play back saved recordings.

### Target Pitch Practice

- Set a **target pitch** frequency (Hz).
- Click **start target pitch** to hear a reference tone.
- Match your voice to the tone; visual cues help guide you.
- Click **stop target pitch** to silence the tone.

### Chat & Feedback

- Type messages in the chat box to talk with Vox.
- Receive affirming, pronoun-aware responses.
- After recordings, Vox provides detailed vocal feedback powered by AI.

### Managing History

- View past performances with pitch, HNR, harmonics, and formants.
- Play back recordings.
- Clear history to start fresh.

---

## 🔧 Configuration

All configuration is done through environment variables in the `.env` file:

### Required Settings

- `OPENAI_API_KEY` - Your OpenAI or OpenAI-compatible API key

### Optional Settings

- `OPENAI_API_BASE` - Custom API base URL (e.g., `https://openrouter.ai/api/v1` for OpenRouter)
- `OPENAI_MODEL` - Model to use (default: `gpt-3.5-turbo`)
- `DATABASE_PATH` - Path to SQLite database file (default: `vox_data.db`)
- `FASTAPI_SECRET_KEY` - Secret key for session management (change from default in production)

---

## 🛠️ Technologies Used

- **Backend:** Python, FastAPI, Hypercorn, Socket.IO, SQLite, librosa, aubio, Parselmouth
- **Frontend:** HTML5, CSS3, JavaScript, Socket.IO client, Tone.js, Chart.js, JustGage
- **AI Integration:** OpenAI-compatible APIs (OpenAI, OpenRouter, etc.)
- **Database:** SQLite (local, file-based)
- **License:** GPL-3.0

---

## 📦 Building a Standalone Application

(Coming soon - instructions for packaging as a desktop application)

---

## 💝 Privacy & Data

- **All data is stored locally** on your computer in a SQLite database file (`vox_data.db` by default).
- **No cloud services** are used for storing your recordings or personal information.
- **No user accounts** or authentication required.
- **Your API key** is only used to communicate directly with your chosen AI provider.
- **You own your data** - you can back up, export, or delete the database file at any time.

---

## 🤝 Contributing

Contributions welcome! Please respect the GPL license and trans-affirming mission.

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Submit a pull request

---

## 📄 License

This project is licensed under the GNU General Public License v3.0 (GPL-3.0).  
You are free to use, modify, and share it, but keep it open and respect the community.

---

## 🌈 Support

If you find Vox helpful, please:
- ⭐ Star the repository
- 🐛 Report bugs via GitHub Issues
- 💬 Share feedback and suggestions
- 🔗 Share with others who might benefit

---

**With love and pride,  
Shelbeely**

[Linktree](https://linktr.ee/Shelbeely) • [GitHub](https://github.com/shelbeely)
