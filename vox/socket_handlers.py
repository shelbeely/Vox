from vox.fastapi_app import get_socketio, get_db_pool, app
from vox.database import save_vocal_data_async, update_recording_path_async
import numpy as np
import asyncio
import json
from flask import session

@socketio.on('start_recording')
def handle_start_recording():
    sid = session.get('id', 'default')
    logger.info(f"Session {sid} - Starting recording")
    socketio.emit('recording_status', {'status': 'started', 'message': 'Recording started'}, room=sid)

@socketio.on('stop_recording')
def handle_stop_recording():
    sid = session.get('id', 'default')
    logger.info(f"Session {sid} - Stopping recording")
    socketio.emit('recording_status', {'status': 'stopped', 'message': 'Recording stopped'}, room=sid)

    async def generate_and_emit_feedback():
        try:
            async with db_pool.acquire() as conn:
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

                async with db_pool.acquire() as conn:
                    user = await conn.fetchrow(
                        "SELECT user_name, user_pronouns FROM users WHERE session_id = $1",
                        sid
                    )
                user_name = user['user_name'] if user and user['user_name'] else 'friend'
                user_pronouns = user['user_pronouns'] if user and user['user_pronouns'] else 'they/them/theirs/themselves'

                from vox.utils import LLM_PERSONALITY_PROMPT_BASE

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

                import openai
                import os
                from dotenv import load_dotenv

                # Load environment variables from .env file
                load_dotenv()
                openai.api_base = os.environ.get("OPENROUTER_API_BASE", "https://openrouter.ai/api/v1")
                openai.api_key = os.environ.get("OPENROUTER_API_KEY")

                def do_request():
                    response = openai.ChatCompletion.create(
                        model="google/gemini-2.0-flash-001",
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

    db_pool = get_db_pool()
    asyncio.run_coroutine_threadsafe(generate_and_emit_feedback(), asyncio.get_event_loop())


@socketio.on('raw_audio')
def handle_raw_audio(data):
    sid = session.get('id', 'default')
    audio = np.array(data['audio'], dtype=np.float32)
    timestamp = data['timestamp']

    from aubio import pitch as aubio_pitch
    from vox.audio_processing import extract_pitch_parselmouth, extract_hnr_parselmouth, extract_voice_quality_parselmouth, generate_voice_report_parselmouth, extract_harmonics, extract_formants_parselmouth

    pitch_detector = aubio_pitch("yin", 2048, 1024, 44100)
    pitch_detector.set_tolerance(0.8)
    pitch = pitch_detector(audio)[0]
    confidence = pitch_detector.get_confidence()

    if confidence > 0.9 and pitch > 20:
        final_pitch = pitch
    else:
        final_pitch = extract_pitch_parselmouth(audio, 44100)

    try:
        hnr = extract_hnr_parselmouth(audio, 44100)
    except Exception as e:
        logger.error(f"Parselmouth HNR extraction error: {e}")
        hnr = 0.0

    jitter_shimmer = extract_voice_quality_parselmouth(audio, 44100)
    praat_report = generate_voice_report_parselmouth(audio, 44100)
    harmonics = extract_harmonics(audio, final_pitch, 44100)
    formants = extract_formants_parselmouth(audio, 44100)

    db_pool = get_db_pool()
    logger = getattr(app.state, "logger", None)
    asyncio.run_coroutine_threadsafe(
        save_vocal_data_async(db_pool, sid, timestamp, final_pitch, hnr, harmonics, formants, jitter_shimmer, praat_report, logger),
        asyncio.get_event_loop()
    )

    socketio.emit('audio_analysis', {
        'pitch': float(final_pitch),
        'hnr': float(hnr),
        'harmonics': harmonics,
        'formants': formants,
        'jitter_shimmer': jitter_shimmer,
        'praat_report': praat_report
    }, room=sid)
    socketio.emit('history_update', {
        'timestamp': timestamp,
        'pitch': float(final_pitch),
        'hnr': float(hnr),
        'harmonics': harmonics,
        'formants': formants,
        'jitter_shimmer': jitter_shimmer,
        'praat_report': praat_report,
        'recording_path': None
    }, room=sid)


@socketio.on('save_recording')
def handle_save_recording_socket(data):
    sid = session.get('id', 'default')
    timestamp = data['timestamp']
    recording_path = data['recording_path']

    db_pool = get_db_pool()
    asyncio.run_coroutine_threadsafe(
        update_recording_path_async(db_pool, sid, timestamp, recording_path),
        asyncio.get_event_loop()
    )

    socketio.emit('history_update', {
        'timestamp': timestamp,
        'pitch': data.get('pitch'),
        'hnr': data.get('hnr'),
        'harmonics': data.get('harmonics'),
        'formants': data.get('formants'),
        'recording_path': recording_path
    }, room=sid)
