import librosa
import soundfile as sf
import numpy as np

def transform_audio_to_gender(input_path, output_path, target_gender):
    """
    Modify the input audio file to match the target gender profile.
    Saves the transformed audio to output_path.
    """
    y, sr = librosa.load(input_path, sr=None)

    # Define pitch shift (in semitones) and formant scaling factors
    if target_gender.lower() == "female":
        pitch_shift = 4  # up 4 semitones
        formant_scale = 1.2
    elif target_gender.lower() == "male":
        pitch_shift = -4  # down 4 semitones
        formant_scale = 0.8
    elif target_gender.lower() == "androgynous":
        pitch_shift = 0
        formant_scale = 1.0
    else:
        # Unknown or unspecified, do not modify
        pitch_shift = 0
        formant_scale = 1.0

    # Pitch shifting
    y_shifted = librosa.effects.pitch_shift(y, sr, n_steps=pitch_shift)

    # Formant shifting (approximate via resampling)
    if formant_scale != 1.0:
        y_len = len(y_shifted)
        y_stretched = librosa.effects.time_stretch(y_shifted, rate=1/formant_scale)
        if len(y_stretched) > y_len:
            y_stretched = y_stretched[:y_len]
        else:
            y_stretched = np.pad(y_stretched, (0, y_len - len(y_stretched)))
    else:
        y_stretched = y_shifted

    # Save transformed audio
    sf.write(output_path, y_stretched, sr)
