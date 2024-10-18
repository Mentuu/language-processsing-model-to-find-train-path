import sys
from scipy.io.wavfile import write
import numpy as np
import threading
from faster_whisper import WhisperModel
import sounddevice as sd
from pynput import keyboard
import stanza
import geonamescache
import unidecode
from transformers import CamembertForSequenceClassification, CamembertTokenizer


freq = 44100
recording = []
recording_active = False
model = CamembertForSequenceClassification.from_pretrained('./trained_model')
tokenizer = CamembertTokenizer.from_pretrained('./trained_model')

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

def checkValidity(sentence):
    inputs = tokenizer(sentence, return_tensors='pt', padding=True, truncation=True)
    outputs = model(**inputs)
    probs = outputs.logits.softmax(dim=1)
    predicted_class = probs.argmax().item()
    print("Predicted class:", predicted_class)
    return 1 if predicted_class == 1 else 0

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
    # Prompt the user to choose input method
    print("Do you want to:")
    print("1. Type a sentence")
    print("2. Record audio")
    choice = input("Enter 1 or 2: ")

    if choice == '1':
        # User chooses to type sentences
        result = input("Please type your sentence(s): ")
    elif choice == '2':
        # User chooses to record audio
        print("Starting the recording and transcription engine")
        with keyboard.Listener(on_press=on_press) as listener:
            print("Press 'r' to start/stop recording.")
            listener.join()
        print('Finished recording. About to start the transcription engine.')

        # Initialize the Whisper model
        model = WhisperModel("medium", device="cpu", compute_type="int8")

        # Transcribe the audio file
        segments, info = model.transcribe("recording.wav", beam_size=5, language="fr")

        print("Detected language '%s' with probability %f" % (info.language, info.language_probability))
        result = ""
        for segment in segments:
            result += segment.text
    else:
        print("Invalid choice. Exiting.")
        return

    print("\nTranscribed Text:")
    print(result)
    print("\n checking validity of the sentence")
    validity = checkValidity(result)
    if validity == 1:
        print("Valid sentence")
    else:
        print("Invalid sentence so skipping NLP processing")

    print("\nStarting the natural language processing...")

    if validity == 1:
        # Initialize the Stanza pipeline for French
        stanza.download('fr', processors='tokenize,pos,lemma,depparse,ner', verbose=False)  # Run once
        nlp = stanza.Pipeline('fr', processors='tokenize,pos,lemma,depparse,ner', use_gpu=False)

        # Process the text
        doc = nlp(result)

        # Extract actions (verbs), specifically the root verbs
        actions = [
            word.lemma for sent in doc.sentences for word in sent.words
            if word.upos == 'VERB' and word.head == 0
        ]

        print("\nActions:", actions)

        # Extract locations (entities of type 'LOC' or 'GPE')
        extracted_locations = [ent.text for ent in doc.entities if ent.type in ['LOC', 'GPE']]

        # Get a list of city names
        gc = geonamescache.GeonamesCache()
        cities = gc.get_cities()

        # Create a set of city names for faster lookup
        city_names = set()
        for city in cities.values():
            if city['countrycode'] == 'FR':
                # Normalize and lower the city name
                city_name = unidecode.unidecode(city['name']).lower()
                city_names.add(city_name)
                # Also add alternate names if available
                for alt_name in city.get('alternatenames', []):
                    city_names.add(unidecode.unidecode(alt_name).lower())

        # Filter the extracted locations to include only cities
        cities_in_text = []
        for loc in extracted_locations:
            normalized_loc = unidecode.unidecode(loc).lower()
            if normalized_loc in city_names:
                cities_in_text.append(loc)


        print("Cities:", cities_in_text)

if __name__ == "__main__":
    main()
