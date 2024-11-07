import numpy as np
import threading
from faster_whisper import WhisperModel
import sounddevice as sd
from pynput import keyboard

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


def save_recording():
    global recording
    if recording:
        recording_combined = np.concatenate(recording, axis=0)
        write("recording.wav", freq, recording_combined)
        print("Recording saved as 'recording.wav'.")


def on_press(key):
    try:
        if key.char == 'r':
            if not recording_active:
                start_recording()
            else:
                stop_recording()
                save_recording()
                return False
    except AttributeError:
        pass


def main():
    print("Starting the recording and transcription engine")
    with keyboard.Listener(on_press=on_press) as listener:
        print("Press 'r' to start/stop recording.")
        listener.join()
    print(f'Finished recording about to start the transcription engine.')
    model = WhisperModel("medium", device="CPU", compute_type="int8")
    segments, info = model.transcribe("recording.wav", beam_size=5, language="fr")

    print("Detected language '%s' with probability %f" % (info.language, info.language_probability))
    result = ""
    for segment in segments:
        result += segment.text
    print(result)

main()
