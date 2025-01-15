import numpy as np
from scipy.io.wavfile import write
from faster_whisper import WhisperModel
import sounddevice as sd
import spacy

# Initialisez le modèle NLP une seule fois
nlp = spacy.load("fr_core_news_lg")

# Variables pour l'enregistrement
freq = 44100
recording = []
recording_active = False


def record_audio():
    global recording
    while recording_active:
        data = sd.rec(int(1 * freq), samplerate=freq, channels=2, dtype='float64')
        sd.wait()
        recording.append(data)


def start_recording():
    global recording, recording_active
    recording_active = True
    recording = []
    print("Recording... Press 'r' again to stop.")
    recording_thread = threading.Thread(target=record_audio)
    recording_thread.start()


def stop_recording():
    global recording_active
    recording_active = False
    print("Recording stopped.")


def save_recording(filename="recording.wav"):
    global recording
    if recording:
        recording_combined = np.concatenate(recording, axis=0)
        write(filename, freq, recording_combined)
        print(f"Recording saved as '{filename}'.")


def transcribe_and_analyze(audio_file):
    """
    Effectue la transcription d'un fichier audio ou vidéo, analyse le texte et retourne les informations pertinentes.
    """
    # Chargez le modèle Whisper
    model = WhisperModel("medium", device="CPU", compute_type="int8")
    
    # Transcrivez le fichier audio
    segments, info = model.transcribe(audio_file, beam_size=5, language="fr")
    transcription = "".join([segment.text for segment in segments])

    print(f"Detected language: {info.language} with probability {info.language_probability}")
    print("Transcription:", transcription)

    # Analyse NLP
    doc = nlp(transcription)
    locations = [ent.text for ent in doc.ents if ent.label_ in ['GPE', 'LOC']]
    actions = [token.text for token in doc if token.pos_ == "VERB" and token.dep_ == "ROOT"]

    return {
        "transcription": transcription,
        "language": info.language,
        "locations": locations,
        "actions": actions
    }
