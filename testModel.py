import torch
from transformers import AutoTokenizer, AutoModelForSequenceClassification
import torch.nn.functional as F

# Load the saved model and tokenizer
model_path = './target/fine-tuned-bert'
tokenizer = AutoTokenizer.from_pretrained(model_path)
model = AutoModelForSequenceClassification.from_pretrained(model_path)

# Move the model to the appropriate device
device = torch.device('cuda') if torch.cuda.is_available() else torch.device('cpu')
model = model.to(device)

def predict_phrase_label(phrase):
    inputs = tokenizer(
        phrase,
        return_tensors='pt',
        truncation=True,
        padding=True,
        max_length=128
    )
    inputs = {key: value.to(device) for key, value in inputs.items()}

    with torch.no_grad():
        outputs = model(**inputs)

    logits = outputs.logits
    probabilities = F.softmax(logits, dim=-1)
    predicted_class_id = logits.argmax(-1).item()

    class_labels = ['Invalid', 'Valid']
    predicted_label = class_labels[predicted_class_id]
    predicted_probability = probabilities[0][predicted_class_id].item()

    return predicted_label, predicted_probability

# Get user input
new_phrase = input("Enter a phrase to classify: ")
label, probability = predict_phrase_label(new_phrase)
print(f"Predicted Label: {label}")
print(f"Confidence: {probability:.2f}")