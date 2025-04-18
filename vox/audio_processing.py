import numpy as np
import librosa
import parselmouth

def estimate_formants(audio, sr):
    try:
        audio = librosa.effects.preemphasis(audio)
        lpc_coeffs = librosa.lpc(audio, order=2 + sr // 1000)
        roots = np.roots(lpc_coeffs)
        roots = roots[np.imag(roots) >= 0]
        formant_freqs = np.angle(roots) * (sr / (2 * np.pi))
        formant_bws = -0.5 * (sr / np.pi) * np.log(np.abs(roots))
        formant_freqs = formant_freqs[formant_freqs > 0]
        formant_bws = formant_bws[formant_freqs > 0]
        indices = np.argsort(formant_freqs)
        formant_freqs = formant_freqs[indices][:3]
        formant_bws = formant_bws[indices][:3]
        return [{"freq": float(f), "bw": float(bw)} for f, bw in zip(formant_freqs, formant_bws)] if len(formant_freqs) >= 3 else [
            {"freq": 500, "bw": 50}, {"freq": 1500, "bw": 100}, {"freq": 2500, "bw": 150}
        ]
    except Exception:
        return [{"freq": 500, "bw": 50}, {"freq": 1500, "bw": 100}, {"freq": 2500, "bw": 150}]

def extract_pitch_parselmouth(audio, sr):
    try:
        snd = parselmouth.Sound(audio, sampling_frequency=sr)
        pitch_obj = snd.to_pitch()
        pitch_values = pitch_obj.selected_array['frequency']
        pitch_values = pitch_values[pitch_values > 0]
        if len(pitch_values) == 0:
            return 0.0
        return float(np.median(pitch_values))
    except Exception:
        return 0.0

def extract_formants_parselmouth(audio, sr, max_formants=3):
    try:
        snd = parselmouth.Sound(audio, sampling_frequency=sr)
        formant_obj = snd.to_formant_burg()
        t = snd.get_total_duration() / 2
        formants = []
        for i in range(1, max_formants + 1):
            freq = formant_obj.get_value_at_time(i, t)
            bw = formant_obj.get_bandwidth_at_time(i, t)
            if freq is None or np.isnan(freq):
                freq = 0.0
            if bw is None or np.isnan(bw):
                bw = 0.0
            formants.append({"freq": float(freq), "bw": float(bw)})
        return formants
    except Exception:
        return [{"freq": 500, "bw": 50}, {"freq": 1500, "bw": 100}, {"freq": 2500, "bw": 150}]

def extract_hnr_parselmouth(audio, sr):
    try:
        snd = parselmouth.Sound(audio, sampling_frequency=sr)
        harmonicity = snd.to_harmonicity_cc()
        hnr = harmonicity.get_mean()
        return float(hnr) if hnr is not None else 0.0
    except Exception:
        return 0.0

def extract_voice_quality_parselmouth(audio, sr):
    try:
        snd = parselmouth.Sound(audio, sampling_frequency=sr)
        point_process = snd.to_point_process_cc()
        jitter_local = parselmouth.praat.call(point_process, "Get jitter (local)", 0, 0, 0.0001, 0.02, 1.3)
        shimmer_local = parselmouth.praat.call([snd, point_process], "Get shimmer (local)", 0, 0, 0.0001, 0.02, 1.3, 1.6)
        return {
            "jitter_local": float(jitter_local),
            "shimmer_local": float(shimmer_local)
        }
    except Exception:
        return {"jitter_local": 0.0, "shimmer_local": 0.0}

def generate_voice_report_parselmouth(audio, sr):
    try:
        snd = parselmouth.Sound(audio, sampling_frequency=sr)
        point_process = snd.to_point_process_cc()
        report = parselmouth.praat.call([snd, point_process], "Voice report", 0, 0, 75, 500, 1.3, 1.6, 0.03, 0.45)
        return report
    except Exception:
        return ""

def extract_harmonics(audio, pitch, sr):
    try:
        harmonic_audio = librosa.effects.harmonic(audio)
        stft = np.abs(librosa.stft(harmonic_audio, n_fft=2048, hop_length=1024))
        freqs = librosa.fft_frequencies(sr=sr, n_fft=2048)
        spectrum = np.mean(stft, axis=1)

        harmonics = []
        for i in range(5):
            harmonic_freq = pitch * (i + 1)
            idx = np.argmin(np.abs(freqs - harmonic_freq))
            if idx < len(spectrum):
                amp = float(spectrum[idx])
                harmonics.append({"freq": float(harmonic_freq), "amp": amp, "ratio": i + 1})

        if not harmonics:
            harmonics = [{"freq": pitch * (i + 1), "amp": 1.0 / (i + 1), "ratio": i + 1} for i in range(5)]

        return harmonics
    except Exception:
        return [{"freq": pitch * (i + 1), "amp": 1.0 / (i + 1), "ratio": i + 1} for i in range(5)]
