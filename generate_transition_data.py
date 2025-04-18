import os
import uuid
import psycopg2
from datetime import datetime, timedelta
import json
from dotenv import load_dotenv

# Load environment variables from .env if present
load_dotenv(os.path.join(os.path.dirname(__file__), ".env"))

# Supabase/Postgres connection details
DB_URL = os.getenv("SUPABASE_DB_URL")
DB_HOST = os.getenv("SUPABASE_DB_HOST", "localhost")
DB_PORT = os.getenv("SUPABASE_DB_PORT", "5432")
DB_NAME = os.getenv("SUPABASE_DB_NAME", "postgres")
DB_USER = os.getenv("SUPABASE_DB_USER", "postgres")
DB_PASSWORD = os.getenv("SUPABASE_DB_PASSWORD", "")

def interpolate(start, end, step, total_steps):
    return start + (end - start) * (step / (total_steps - 1))

def main():
    if DB_URL:
        conn = psycopg2.connect(DB_URL)
    else:
        conn = psycopg2.connect(
            host=DB_HOST,
            port=DB_PORT,
            dbname=DB_NAME,
            user=DB_USER,
            password=DB_PASSWORD
        )
    cur = conn.cursor()

    # 1. Insert a user
    user_id = str(uuid.uuid4())
    user_name = "transition_user"
    user_pronouns = "they/them"
    target_gender = "female"
    email = "transition_user@example.com"
    # Password: "testpassword" hashed with bcrypt
    import bcrypt
    password = "testpassword"
    password_hash = bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()
    created_at = datetime.now()
    updated_at = created_at

    cur.execute(
        """
        INSERT INTO users (user_id, user_name, user_pronouns, target_gender, email, password_hash, created_at, updated_at, email_verified)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, TRUE)
        ON CONFLICT (email) DO UPDATE SET updated_at = EXCLUDED.updated_at
        RETURNING user_id
        """,
        (user_id, user_name, user_pronouns, target_gender, email, password_hash, created_at, updated_at)
    )
    user_id = cur.fetchone()[0]

    # 2. Generate 100 recordings over 30 days
    num_samples = 100
    days = 30
    start_time = datetime.now() - timedelta(days=days)
    time_step = timedelta(seconds=(days * 24 * 3600) // num_samples)

    # Generate a single session_id for all samples (simulate a session for the user)
    session_id = str(uuid.uuid4())

    # Feature ranges (typical values)
    pitch_start, pitch_end = 120.0, 220.0  # Hz
    hnr_start, hnr_end = 10.0, 18.0        # dB
    f1_start, f1_end = 120.0, 220.0        # Hz
    f2_start, f2_end = 1200.0, 1800.0      # Hz
    f3_start, f3_end = 2500.0, 3000.0      # Hz
    h1h2_start, h1h2_end = 6.0, 10.0       # dB
    jitter_start, jitter_end = 1.5, 0.5    # percent
    shimmer_start, shimmer_end = 4.0, 2.0  # percent

    for i in range(num_samples):
        timestamp = start_time + i * time_step

        # Interpolated features
        pitch = interpolate(pitch_start, pitch_end, i, num_samples)
        hnr = interpolate(hnr_start, hnr_end, i, num_samples)
        f1 = interpolate(f1_start, f1_end, i, num_samples)
        f2 = interpolate(f2_start, f2_end, i, num_samples)
        f3 = interpolate(f3_start, f3_end, i, num_samples)
        h1h2 = interpolate(h1h2_start, h1h2_end, i, num_samples)
        jitter = interpolate(jitter_start, jitter_end, i, num_samples)
        shimmer = interpolate(shimmer_start, shimmer_end, i, num_samples)

        harmonics = {"H1-H2": h1h2}
        formants = {"F1": f1, "F2": f2, "F3": f3}
        jitter_shimmer = {"jitter": jitter, "shimmer": shimmer}
        praat_report = (
            f"Sample {i+1}: pitch={pitch:.1f}Hz, HNR={hnr:.1f}dB, "
            f"F1={f1:.1f}Hz, F2={f2:.1f}Hz, F3={f3:.1f}Hz, "
            f"jitter={jitter:.2f}%, shimmer={shimmer:.2f}%"
        )
        recording_path = f"/recordings/sample_{i+1}.wav"

        cur.execute(
            """
            INSERT INTO vocal_data (
                user_id, session_id, timestamp, pitch, hnr, harmonics, formants, jitter_shimmer, praat_report, recording_path
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """,
            (
                user_id,
                session_id,
                timestamp,
                pitch,
                hnr,
                json.dumps(harmonics),
                json.dumps(formants),
                json.dumps(jitter_shimmer),
                praat_report,
                recording_path
            )
        )

    conn.commit()
    cur.close()
    conn.close()
    print(f"Inserted user {user_id} and {num_samples} vocal_data samples.")

if __name__ == "__main__":
    main()
