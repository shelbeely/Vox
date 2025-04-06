# Vox - A Voice Therapy Coach for Trans Individuals
# Migrated to Supabase PostgreSQL with asyncpg

# Hey beautiful soul! 💖
# This is Vox, crafted lovingly by a trans woman (hi, it's Shelbeely!) for our vibrant trans community.
# This app is your gentle, affirming space to explore, train, and celebrate your authentic voice.
# Every line of code here is meant to uplift, empower, and support you on your journey. You deserve it!

# --- Importing all the magical libraries we need ---
import os  # For handling file paths and environment secrets, keeping things tidy and secure
import uuid  # To create unique session IDs, because you're one of a kind!
import time  # Timing utilities, for timestamps and more
import requests  # For making HTTP requests, like chatting with AI friends
import logging  # To keep a diary of what the app is doing, super helpful for fixing bugs
import json  # For working with data in a friendly, structured way
import numpy as np  # Math and signal processing, to analyze your lovely voice
import openai  # To connect with the AI that gives you personalized, caring feedback
import librosa  # Audio analysis magic, helping us understand your unique sound
from aubio import pitch as aubio_pitch  # For detecting your pitch in real-time
from flask import Flask, request, jsonify, render_template, session, make_response  # The cozy web framework wrapping it all
from flask_limiter import Limiter  # To gently prevent overload, keeping things smooth
from flask_limiter.util import get_remote_address  # To identify users for rate limiting
from flask_socketio import SocketIO, emit  # For real-time, heart-to-heart communication
from flask_wtf.csrf import CSRFProtect  # To protect you from sneaky web attacks
from datetime import datetime, timedelta  # For handling time, like cookie expiry and cleanup
import atexit  # To tidy up when the app closes, like a good hostess
import glob  # For finding files, like your recordings
import random  # For a sprinkle of randomness, if needed
import asyncio  # For async magic, making things fast and smooth
import asyncpg  # To chat with our Supabase PostgreSQL database asynchronously

# --- Setting up our cozy Flask app and friends ---
app = Flask(__name__)
app.secret_key = os.environ.get("FLASK_SECRET_KEY", "default_secret_key")  # Secret key to keep your session safe
socketio = SocketIO(app, cors_allowed_origins="*")  # Real-time communication with love
csrf = CSRFProtect(app)  # Protecting your data like a mama bear
limiter = Limiter(get_remote_address, app=app, default_limits=["200 per day", "50 per hour"])  # Gentle limits to keep the app happy

# --- Setting up some important constants and folders ---
UPLOAD_FOLDER = 'uploads'  # Where your uploaded files will be kept safe
RECORDINGS_FOLDER = 'recordings'  # Where your beautiful voice recordings live
os.makedirs(UPLOAD_FOLDER, exist_ok=True)  # Create the uploads folder if it doesn't exist yet
os.makedirs(RECORDINGS_FOLDER, exist_ok=True)  # Same for recordings
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['RECORDINGS_FOLDER'] = RECORDINGS_FOLDER

# --- API keys and database connection info ---
openai.api_key = os.environ.get("OPENAI_API_KEY", "your-openai-api-key-here")  # Your OpenAI key for AI magic ✨

SUPABASE_DB_URL = os.environ.get("SUPABASE_DB_URL")  # Your Supabase PostgreSQL URL, where your data is stored safely
COOKIE_EXPIRY_DAYS = 30  # How long your login cookie lasts, so you stay logged in comfortably
CLEANUP_DAYS = COOKIE_EXPIRY_DAYS + 10  # When to clean up old recordings, giving you extra grace time

# --- Audio processing settings ---
CHUNK = 2048  # Size of audio chunks we analyze, balancing detail and speed
RATE = 44100  # Standard audio sample rate, capturing all the richness of your voice
HOP_SIZE = CHUNK // 2  # Overlap between chunks, for smoother analysis

# --- Setting up logging ---
logging.basicConfig(level=logging.INFO)  # Log important info, so we can keep things running smoothly
logger = logging.getLogger(__name__)  # Our app's personal diary

# --- Database connection pool ---
db_pool = None  # This will hold our async connection pool to Supabase

async def init_pg_pool():
    """Initialize the asyncpg connection pool to Supabase."""
    global db_pool
    db_pool = await asyncpg.create_pool(SUPABASE_DB_URL, max_size=10)  # Up to 10 lovely connections at once

# Create the pool right away so we're ready to serve you!
asyncio.get_event_loop().run_until_complete(init_pg_pool())

# --- The heart and soul of Vox's AI personality ---
LLM_PERSONALITY_PROMPT_BASE = (
    # This prompt lovingly guides the AI to be your supportive, affirming voice coach.
    # It was crafted by a trans woman (me!) to ensure you feel truly seen, respected, and uplifted.
    # The AI will:
    # - Use your name and pronouns, because your identity matters deeply.
    # - Alternate pronouns naturally, especially for mixed sets, honoring your fluidity.
    # - Mix in fun neopronouns if you like, celebrating your uniqueness.
    # - Provide warm, practical, encouraging feedback grounded in real data.
    # Because you deserve a coach who *gets* you, every step of the way. 💖
    "You are Vox, a supportive voice therapy coach built for trans individuals, created by Shelbeely, a trans woman developer. "
    "Your tone is warm, encouraging, and affirming, with a deep understanding of gender expression and voice training. "
    "Use the user's name and pronouns (provided below) in your responses to make them feel seen and supported. "
    "Use the subject pronoun(s) (e.g., 'she', 'pup') for subjects, the object pronoun(s) (e.g., 'her', 'pup') for objects, "
    "the possessive pronoun (e.g., 'hers', 'puppy') for possession, and the reflexive pronoun (e.g., 'herself', 'pupself') "
    "for reflexive actions (e.g., 'she hears herself', 'pup hears pupself'). "
    "For mixed pronouns (e.g., 'she/they'), alternate between the two subject pronouns (e.g., 'she’s great' then 'they’re amazing') "
    "and their corresponding object pronouns (e.g., 'her' then 'them') naturally across sentences for variety. "
    "If the user has 'any' pronouns, default to 'they/them/theirs/themselves' but mix in other pronouns creatively "
    "(e.g., 'xe', 'pup', 'zirself') for fun. "
    "Provide clear, practical feedback grounded in the data, and always aim to uplift the user in their journey to find their authentic voice.\n"
)

# --- A celebration of pronouns in all their beautiful diversity ---
# This dictionary gives the AI examples of how to use many different pronoun sets,
# including neopronouns, mixed sets, and more.
# Because your pronouns are valid, powerful, and deserve to be honored fully.
# Whether you're she, he, they, xe, pup, star, void, or any magical mix,
# Vox is here to affirm *your* truth, every single time. 🌈✨
PRONOUN_EXAMPLES = {
    "she/her/hers/herself": "'She/her/hers/herself': 'She’s hitting great notes, I hear her clearly, hers is a strong voice, and she’s proud of herself.'",
    "he/him/his/himself": "'He/him/his/himself': 'He’s got a solid pitch, I hear him well, his tone is great, and he’s confident in himself.'",
    "they/them/theirs/themselves": "'They/them/theirs/themselves': 'They’re doing amazing, I hear them clearly, theirs is a unique voice, and they’re proud of themselves.'",
    "xe/xem/xirs/xemself": "'Xe/xem/xirs/xemself': 'Xe’s pitch is lovely, I hear xem clearly, xirs tone is unique, and xe’s proud of xemself.'",
    "ze/zir/zirs/zirself": "'Ze/zir/zirs/zirself': 'Ze’s resonance shines, encourage zir, zirs voice is strong, and ze sees zirself improving.'",
    "ze/hir/hirs/hirself": "'Ze’s voice is vibrant, I hear hir clearly, hirs tone is warm, and ze loves hirself.'",
    "ey/em/eirs/emself": "'Ey/em/eirs/emself': 'Ey’s pitch is steady, I hear em well, eirs voice is clear, and ey trusts emself.'",
    "ve/ver/vis/verself": "'Ve/ver/vis/verself': 'Ve’s tone is smooth, I hear ver easily, vis voice is distinct, and ve honors verself.'",
    "tey/ter/tem/terself": "'Tey/ter/tem/terself': 'Tey’s pitch is bright, I hear ter clearly, tem voice is lovely, and tey uplifts terself.'",
    "e/em/es/eself": "'E/em/es/eself': 'E’s resonance is strong, I hear em well, es tone is unique, and e supports eself.'",
    "zie/zim/zir/zirself": "'Zie/zim/zir/zirself': 'Zie’s voice glows, I hear zim clearly, zir tone is bold, and zie cherishes zirself.'",
    "sie/sir/hir/hirself": "'Sie/sir/hir/hirself': 'Sie’s pitch is rich, I hear sir well, hir voice is striking, and sie celebrates hirself.'",
    "it/it/its/itself": "'It/it/its/itself': 'It’s got a cool vibe, I hear it clearly, its tone is neat, and it’s happy with itself.'",
    "fae/faer/faers/faerself": "'Fae/faer/faers/faerself': 'Fae’s voice sparkles, I hear faer gently, faers tone is magical, and fae adores faerself.'",
    "ae/aer/aers/aerself": "'Ae/aer/aers/aerself': 'Ae’s pitch flows, I hear aer smoothly, aers voice is serene, and ae nurtures aerself.'",
    "per/per/pers/perself": "'Per/per/pers/perself': 'Per’s tone is steady, I hear per clearly, pers voice is calm, and per values perself.'",
    "pup/pup/puppy/pupself": "'Pup/pup/puppy/pupself': 'Pup’s pitch is adorable, I hear pup softly, puppy tone is sweet, and pup loves pupself.'",
    "kit/kit/kits/kitself": "'Kit/kit/kits/kitself': 'Kit’s voice is playful, I hear kit brightly, kits tone is fun, and kit enjoys kitself.'",
    "bun/bun/buns/bunself": "'Bun/bun/buns/bunself': 'Bun’s pitch is cozy, I hear bun warmly, buns tone is soft, and bun comforts bunself.'",
    "star/star/stars/starself": "'Star/star/stars/starself': 'Star’s voice shines, I hear star clearly, stars tone is radiant, and star celebrates starself.'",
    "void/void/voids/voidself": "'Void/void/voids/voidself': 'Void’s pitch is deep, I hear void softly, voids tone is vast, and void embraces voidself.'",
    "nyx/nyx/nyxs/nyxself": "'Nyx/nyx/nyxs/nyxself': 'Nyx’s voice is mysterious, I hear nyx gently, nyxs tone is dark, and nyx honors nyxself.'",
    "she/they/her/them/hers/theirs/herself/themselves": "'She/they/her/them/hers/theirs/herself/themselves': 'She’s doing great, I hear them clearly, hers is a lovely voice, and they’re proud of themselves.'",
    "he/they/him/them/his/theirs/himself/themselves": "'He/they/him/them/his/theirs/himself/themselves': 'He’s got a strong pitch, I hear them well, his tone is solid, and they trust themselves.'"
}

# --- Keeping your space tidy and safe ---
def cleanup_old_recordings():
    """
    This gentle housekeeper deletes old recordings and empty folders after a while,
    so your space stays neat and your privacy is respected.
    Think of it as a little spring cleaning, with love. 🧹💖
    """
    now = datetime.now()
    cutoff = now - timedelta(days=CLEANUP_DAYS)
    cutoff_timestamp = cutoff.timestamp()
    for session_dir in glob.glob(os.path.join(RECORDINGS_FOLDER, '*')):
        if os.path.isdir(session_dir):
            for file in glob.glob(os.path.join(session_dir, '*.wav')):
                if os.path.getmtime(file) < cutoff_timestamp:
                    try:
                        os.remove(file)
                        logger.info(f"Deleted old recording: {file}")
                    except Exception as e:
                        logger.error(f"Error deleting {file}: {e}")
            if not os.listdir(session_dir):
                os.rmdir(session_dir)
                logger.info(f"Deleted empty session directory: {session_dir}")

cleanup_old_recordings()  # Do a quick tidy-up on startup
atexit.register(cleanup_old_recordings)  # And every time the app closes, too

# --- Logging your journey ---
def log_activity(sid, action, details):
    """
    Logs what you're up to (like saving a recording or setting pronouns),
    so we can celebrate your progress and fix any hiccups.
    """
    logger.info(f"Session {sid} - {action}: {details}")

# --- Estimating your beautiful formants ---
def estimate_formants(audio, sr):
    """
    Estimate the resonant frequencies (formants) of your voice,
    which help shape how feminine, masculine, or unique your sound is.
    This uses some fancy math (LPC) to peek inside your vocal tract's signature.
    If it can't figure it out, it gives gentle defaults instead.
    """
    try:
        audio = librosa.effects.preemphasis(audio)  # Boosts clarity by emphasizing higher frequencies
        lpc_coeffs = librosa.lpc(audio, order=2 + sr // 1000)  # Linear prediction to model your vocal tract
        roots = np.roots(lpc_coeffs)  # Find the roots of the LPC polynomial
        roots = roots[np.imag(roots) >= 0]  # Keep only positive frequencies
        formant_freqs = np.angle(roots) * (sr / (2 * np.pi))  # Convert to Hz
        formant_bws = -0.5 * (sr / np.pi) * np.log(np.abs(roots))  # Bandwidths
        formant_freqs = formant_freqs[formant_freqs > 0]
        formant_bws = formant_bws[formant_freqs > 0]
        indices = np.argsort(formant_freqs)
        formant_freqs = formant_freqs[indices][:3]  # Grab the first 3 formants (F1, F2, F3)
        formant_bws = formant_bws[indices][:3]
        return [{"freq": float(f), "bw": float(bw)} for f, bw in zip(formant_freqs, formant_bws)] if len(formant_freqs) >= 3 else [
            {"freq": 500, "bw": 50}, {"freq": 1500, "bw": 100}, {"freq": 2500, "bw": 150}
        ]
    except Exception as e:
        logger.error(f"Formant estimation error: {e}")
        # If anything goes wrong, return gentle defaults
        return [{"freq": 500, "bw": 50}, {"freq": 1500, "bw": 100}, {"freq": 2500, "bw": 150}]

# --- Extracting the harmonics that make your voice sparkle ---
def extract_harmonics(audio, pitch, sr):
    """
    Find the main harmonics in your voice, which add richness and color.
    This helps Vox understand your unique sound signature.
    """
    try:
        # Separate out the harmonic (musical) part of your voice
        harmonic_audio = librosa.effects.harmonic(audio)

        # Look at the frequency spectrum of those harmonics
        stft = np.abs(librosa.stft(harmonic_audio, n_fft=CHUNK, hop_length=HOP_SIZE))
        freqs = librosa.fft_frequencies(sr=sr, n_fft=CHUNK)
        spectrum = np.mean(stft, axis=1)

        harmonics = []
        for i in range(5):  # Let's find the first 5 harmonics
            harmonic_freq = pitch * (i + 1)
            idx = np.argmin(np.abs(freqs - harmonic_freq))
            if idx < len(spectrum):
                amp = float(spectrum[idx])
                harmonics.append({"freq": float(harmonic_freq), "amp": amp, "ratio": i + 1})

        # If we didn't find any, use gentle defaults
        if not harmonics:
            harmonics = [{"freq": pitch * (i + 1), "amp": 1.0 / (i + 1), "ratio": i + 1} for i in range(5)]

        return harmonics
    except Exception as e:
        logger.error(f"Harmonics extraction error: {e}")
        # On error, return gentle defaults
        return [{"freq": pitch * (i + 1), "amp": 1.0 / (i + 1), "ratio": i + 1} for i in range(5)]

# --- The home page: your cozy starting point ---
@app.route('/')
async def index():
    """
    When you visit Vox, this is the first warm hug you get.
    It creates a unique session just for you, or welcomes you back if you've been here before.
    It also makes sure your name and pronouns are saved (or defaulted to 'friend' and 'they/them'),
    so every interaction feels personal and affirming.
    """
    session.permanent = True  # Keep your session cozy and lasting
    if 'id' not in session:
        session['id'] = str(uuid.uuid4())  # Unique ID, because you're one of a kind!
    sid = session['id']

    async with db_pool.acquire() as conn:
        user = await conn.fetchrow("SELECT user_name, user_pronouns FROM users WHERE session_id = $1", sid)
        if not user:
            # If you're new, set sweet defaults
            await conn.execute(
                "INSERT INTO users (session_id, user_name, user_pronouns) VALUES ($1, $2, $3)",
                sid, 'friend', 'they/them/theirs/themselves'
            )

    log_activity(sid, "login", "User accessed Vox")
    response = make_response(render_template('index.html'))  # Serve the lovely homepage
    response.set_cookie('session_id', sid, max_age=2592000, httponly=True)  # Keep your session safe and sound
    return response

# --- Setting your target gender goals ---
@app.route('/set_target_gender', methods=['POST'])
@limiter.limit("50/hour")
async def set_target_gender():
    """
    Save your target gender expression (like femme, masc, nonbinary, etc.)
    so Vox can tailor feedback and support your beautiful goals.
    """
    sid = session.get('id', 'default')
    data = request.get_json()
    target_gender = data.get("target", "unspecified").strip()

    async with db_pool.acquire() as conn:
        await conn.execute(
            "UPDATE users SET target_gender = $1 WHERE session_id = $2",
            target_gender, sid
        )

    log_activity(sid, "set_target_gender", f"Target gender set to {target_gender}")
    return jsonify({"status": "success", "target_gender": target_gender})

# --- Setting your name and pronouns, because you deserve to be seen ---
@app.route('/set_user_info', methods=['POST'])
@limiter.limit("50/hour")
async def set_user_info():
    """
    Save or update your chosen name and pronouns,
    so every interaction feels personal, respectful, and affirming.
    """
    sid = session.get('id', 'default')
    data = request.get_json()
    user_name = data.get("name", "friend").strip()[:50]  # Keep it sweet and short
    user_pronouns = data.get("pronouns", "they/them/theirs/themselves").strip()
    if not user_name:
        logger.error(f"Session {sid} - set_user_info failed: Name cannot be empty")
        return jsonify({"status": "error", "message": "Name cannot be empty"}), 400

    async with db_pool.acquire() as conn:
        await conn.execute(
            "INSERT INTO users (session_id, user_name, user_pronouns) VALUES ($1, $2, $3) "
            "ON CONFLICT (session_id) DO UPDATE SET user_name = EXCLUDED.user_name, user_pronouns = EXCLUDED.user_pronouns",
            sid, user_name, user_pronouns
        )

    logger.info(f"Session {sid} - user_info_set: Name: {user_name}, Pronouns: {user_pronouns}")
    return jsonify({"status": "success", "user_name": user_name, "pronouns": user_pronouns})

# --- Getting your past performances, so you can celebrate progress ---
@app.route('/get_performances')
async def get_performances():
    """
    Fetch all your lovely past voice recordings and analysis results,
    so you can see how far you've come on your journey.
    """
    sid = session.get('id', 'default')
    async with db_pool.acquire() as conn:
        rows = await conn.fetch(
            "SELECT timestamp, pitch, hnr, harmonics, formants, recording_path FROM vocal_data WHERE session_id = $1 ORDER BY timestamp DESC",
            sid
        )
    performances = [
        {
            "timestamp": row['timestamp'].isoformat() if row['timestamp'] else None,
            "pitch": row['pitch'],
            "hnr": row['hnr'],
            "harmonics": row['harmonics'],
            "formants": row['formants'],
            "recording_path": row['recording_path']
        }
        for row in rows
    ]
    return jsonify(performances)

# --- Saving your beautiful voice recordings ---
@app.route('/save_recording', methods=['POST'])
@limiter.limit("50/hour")
async def save_recording():
    """
    Save a new voice recording you just made,
    so you can get feedback and track your growth.
    """
    sid = session.get('id', 'default')
    if 'recording' not in request.files:
        return jsonify({"status": "error", "message": "No recording file provided"}), 400

    file = request.files['recording']
    timestamp = request.form.get('timestamp', datetime.now().isoformat())
    filename = f"{timestamp.replace(':', '-')}.wav"
    session_dir = os.path.join(app.config['RECORDINGS_FOLDER'], sid)
    os.makedirs(session_dir, exist_ok=True)
    filepath = os.path.join(session_dir, filename)
    file.save(filepath)

    async with db_pool.acquire() as conn:
        await conn.execute(
            "INSERT INTO vocal_data (session_id, timestamp, pitch, hnr, harmonics, formants, recording_path) "
            "VALUES ($1, $2, NULL, NULL, NULL, NULL, $3)",
            sid, timestamp, filepath
        )

    log_activity(sid, "save_recording", f"Recording saved at {filepath}")
    return jsonify({"status": "success", "recording_path": f"/{RECORDINGS_FOLDER}/{sid}/{filename}"})


# --- Clearing your history, because privacy matters ---
@app.route('/clear_history', methods=['POST'])
@limiter.limit("50/hour")
async def clear_history():
    """
    Delete all your past recordings and data,
    giving you a fresh start whenever you want.
    Your privacy and comfort come first, always.
    """
    sid = session.get('id', 'default')

    async with db_pool.acquire() as conn:
        rows = await conn.fetch(
            "SELECT recording_path FROM vocal_data WHERE session_id = $1",
            sid
        )
        await conn.execute(
            "DELETE FROM vocal_data WHERE session_id = $1",
            sid
        )

    # Delete files from disk
    for row in rows:
        path = row['recording_path']
        if path and os.path.exists(path):
            try:
                os.remove(path)
            except Exception:
                pass

    # Delete your session folder if empty
    session_dir = os.path.join(RECORDINGS_FOLDER, sid)
    if os.path.exists(session_dir):
        try:
            for file in glob.glob(os.path.join(session_dir, '*.wav')):
                os.remove(file)
            os.rmdir(session_dir)
        except Exception:
            pass

    socketio.emit("history_cleared", room=sid)
    log_activity(sid, "clear_history", "History and recordings cleared")
    return jsonify({"status": "success"})


# --- Real-time SocketIO event handlers: instant, caring feedback ---
@socketio.on('start_recording')
def handle_start_recording():
    """
    When you start recording, this event lets Vox know,
    so it can update the UI and get ready to support you.
    """
    sid = session.get('id', 'default')
    logger.info(f"Session {sid} - Starting recording")
    emit('recording_status', {'status': 'started', 'message': 'Recording started'}, room=sid)

@socketio.on('stop_recording')
def handle_stop_recording():
    """
    When you stop recording, this event triggers feedback generation,
    so you get instant, personalized encouragement and tips.
    """
    sid = session.get('id', 'default')
    logger.info(f"Session {sid} - Stopping recording")
    emit('recording_status', {'status': 'stopped', 'message': 'Recording stopped'}, room=sid)

    async def generate_and_emit_feedback():
        try:
            async with db_pool.acquire() as conn:
                # Fetch your latest vocal data
                row = await conn.fetchrow(
                    "SELECT pitch, hnr, harmonics, formants FROM vocal_data WHERE session_id = $1 ORDER BY timestamp DESC LIMIT 1",
                    sid
                )
            if not row:
                feedback_text = "No recent vocal data found to generate feedback."
            else:
                pitch = row['pitch']
                hnr = row['hnr']
                harmonics = row['harmonics']
                formants = row['formants']

                # Fetch your name and pronouns for a personal touch
                async with db_pool.acquire() as conn:
                    user = await conn.fetchrow(
                        "SELECT user_name, user_pronouns FROM users WHERE session_id = $1",
                        sid
                    )
                user_name = user['user_name'] if user and user['user_name'] else 'friend'
                user_pronouns = user['user_pronouns'] if user and user['user_pronouns'] else 'they/them/theirs/themselves'

                # Compose the AI prompt with your info and vocal data
                prompt = LLM_PERSONALITY_PROMPT_BASE + f"""
User info:
Name: {user_name}
Pronouns: {user_pronouns}

Latest vocal metrics:
- Pitch: {pitch:.2f} Hz
- Harmonics-to-Noise Ratio (HNR): {hnr:.2f}
- Harmonics: {harmonics}
- Formants: {formants}

Provide personalized, supportive feedback on the user's voice based on these metrics. Be encouraging and offer practical tips if appropriate.
"""

                import asyncio

                def do_request():
                    response = openai.ChatCompletion.create(
                        model="gpt-3.5-turbo",
                        messages=[
                            {"role": "system", "content": prompt}
                        ],
                        temperature=0.7
                    )
                    return response

                response_data = await asyncio.to_thread(do_request)

                choices = response_data.get("choices", [])
                if not choices:
                    feedback_text = "No feedback generated."
                else:
                    feedback_text = choices[0]["message"]["content"].strip()

            socketio.emit('llm_feedback', {'feedback': feedback_text}, room=sid)

        except Exception as e:
            logger.error(f"Feedback generation error: {e}")
            socketio.emit('llm_feedback', {'feedback': 'Error generating feedback.'}, room=sid)

    import asyncio
    asyncio.run_coroutine_threadsafe(generate_and_emit_feedback(), asyncio.get_event_loop())

@socketio.on('raw_audio')
def handle_raw_audio(data):
    """
    Receive raw audio chunks during live recording,
    analyze them instantly, and send back real-time feedback.
    This helps you adjust and learn on the fly, like a gentle coach by your side.
    """
    sid = session.get('id', 'default')
    audio = np.array(data['audio'], dtype=np.float32)
    timestamp = data['timestamp']

    pitch_detector = aubio_pitch("yin", CHUNK, HOP_SIZE, RATE)
    pitch_detector.set_tolerance(0.8)
    pitch = pitch_detector(audio)[0]
    confidence = pitch_detector.get_confidence()

    if confidence > 0.9 and pitch > 20:
        try:
            hnr = float(librosa.effects.hnr(audio))
        except Exception as e:
            logger.error(f"HNR calculation error: {e}")
            hnr = 0.0
        harmonics = extract_harmonics(audio, pitch, RATE)
        formants = estimate_formants(audio, RATE)

        asyncio.run_coroutine_threadsafe(
            save_vocal_data_async(sid, timestamp, pitch, hnr, harmonics, formants),
            asyncio.get_event_loop()
        )

        emit('audio_analysis', {
            'pitch': float(pitch),
            'hnr': float(hnr),
            'harmonics': harmonics,
            'formants': formants
        }, room=sid)
        emit('history_update', {
            'timestamp': timestamp,
            'pitch': float(pitch),
            'hnr': float(hnr),
            'harmonics': harmonics,
            'formants': formants,
            'recording_path': None
        }, room=sid)

async def save_vocal_data_async(sid, timestamp, pitch, hnr, harmonics, formants):
    """
    Save your vocal analysis data asynchronously,
    so Vox can keep up with your beautiful voice in real-time.
    """
    async with db_pool.acquire() as conn:
        await conn.execute(
            "INSERT INTO vocal_data (session_id, timestamp, pitch, hnr, harmonics, formants, recording_path) "
            "VALUES ($1, $2, $3, $4, $5, $6, NULL)",
            sid, timestamp, float(pitch), float(hnr), json.dumps(harmonics), json.dumps(formants)
        )

@socketio.on('save_recording')
def handle_save_recording_socket(data):
    """
    Update the database with the saved recording's file path,
    linking your beautiful voice to its analysis data.
    """
    sid = session.get('id', 'default')
    timestamp = data['timestamp']
    recording_path = data['recording_path']

    asyncio.run_coroutine_threadsafe(
        update_recording_path_async(sid, timestamp, recording_path),
        asyncio.get_event_loop()
    )

    emit('history_update', {
        'timestamp': timestamp,
        'pitch': data.get('pitch'),
        'hnr': data.get('hnr'),
        'harmonics': data.get('harmonics'),
        'formants': data.get('formants'),
        'recording_path': recording_path
    }, room=sid)

async def update_recording_path_async(sid, timestamp, recording_path):
    """
    Actually update the database record with the saved file path.
    """
    async with db_pool.acquire() as conn:
        await conn.execute(
            "UPDATE vocal_data SET recording_path = $1 WHERE session_id = $2 AND timestamp = $3",
            recording_path, sid, timestamp
        )


# --- Chat endpoint: your affirming AI friend ---
@app.route('/chat', methods=['POST'])
@limiter.limit("50/hour")
async def chat():
    """
    Send a message to Vox's AI chat,
    and get back warm, supportive, personalized conversation.
    Perfect for encouragement, questions, or just a little trans joy. 💖
    """
    sid = session.get('id', 'default')
    data = request.get_json()
    user_message = data.get("message", "").strip()

    if not user_message:
        return jsonify({"status": "error", "message": "Empty message"}), 400

    # Fetch your name and pronouns for a personal touch
    async with db_pool.acquire() as conn:
        user = await conn.fetchrow(
            "SELECT user_name, user_pronouns FROM users WHERE session_id = $1",
            sid
        )
    user_name = user['user_name'] if user and user['user_name'] else 'friend'
    user_pronouns = user['user_pronouns'] if user and user['user_pronouns'] else 'they/them/theirs/themselves'

    # Compose the AI's system prompt
    system_prompt = LLM_PERSONALITY_PROMPT_BASE + f"\nUser info:\nName: {user_name}\nPronouns: {user_pronouns}\n"

    payload = {
        "model": "openai/gpt-3.5-turbo",
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_message}
        ],
        "temperature": 0.7
    }

    headers = {
        "Authorization": f"Bearer {LLM_API_KEY}",
        "Content-Type": "application/json"
    }

    try:
        import asyncio

        def do_request():
            response = openai.ChatCompletion.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_message}
                ],
                temperature=0.7
            )
            return response

        response_data = await asyncio.to_thread(do_request)

        choices = response_data.get("choices", [])
        if not choices:
            return jsonify({"status": "error", "message": "No response from LLM"}), 500

        reply = choices[0]["message"]["content"].strip()

        return jsonify({"status": "success", "message": reply})

    except Exception as e:
        logger.error(f"Chat error: {e}")
        return jsonify({"status": "error", "message": "Failed to get response from LLM"}), 500

if __name__ == '__main__':
    socketio.run(app, debug=True, host='0.0.0.0', port=5000)
