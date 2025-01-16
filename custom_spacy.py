import spacy
from spacy.training import Example
import pandas as pd

# Loading the CSV file
csv_file_path = "liste-des-gares.csv"
data = pd.read_csv(csv_file_path, delimiter=";")

# Extracting unique communes
communes = data["COMMUNE"].unique().tolist()
print(f"Loaded {len(communes)} communes.")

TRAIN_DATA = []

# Creating training examples
for commune in communes:
    text = f"I live in {commune}."
    start_idx = text.find(commune)
    end_idx = start_idx + len(commune)
    TRAIN_DATA.append((text, {"entities": [(start_idx, end_idx, "LOC")]}))

# Loading the pre-trained SpaCy model
nlp = spacy.load("fr_core_news_lg")
ner = nlp.get_pipe("ner")

# Creating examples
examples = [Example.from_dict(nlp.make_doc(text), annotations) for text, annotations in TRAIN_DATA]

# Train the NER
print("Training the NER...")
optimizer = nlp.resume_training()

for i, (text, annotations) in enumerate(TRAIN_DATA):
    if not isinstance(text, str) or not isinstance(annotations, dict):
        print(f"Issue at index {i}: {text}, {annotations}")
        break

for epoch in range(3):
    for example in examples:
        try:
            nlp.update([example], sgd=optimizer)
        except Exception as e:
            print(f"Error at epoch {epoch}, example: {example}, exception: {e}")
    print(f"Epoch {epoch + 1} completed.")

print("Training completed. Saving the model...")
nlp.to_disk("custom_spacy_model")
print("Model updated and saved!")
