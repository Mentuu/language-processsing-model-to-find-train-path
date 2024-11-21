import pandas as pd
from transformers import BertTokenizer, BertForSequenceClassification, Trainer, TrainingArguments, AutoTokenizer, AutoModelForSequenceClassification
import torch
from sklearn.model_selection import train_test_split
from sklearn.metrics import (
    accuracy_score,
    precision_recall_fscore_support,
    confusion_matrix,
    classification_report,
    roc_curve,
    auc,
    ConfusionMatrixDisplay
)
import matplotlib.pyplot as plt
from scipy.special import expit  # Sigmoid function

# Load valid and invalid phrases
valid_phrases = pd.read_csv('good_phrases.csv')
invalid_phrases = pd.read_csv('wrong_phrases.csv')
test_phrases = pd.read_csv('test_phrases.csv')

def compute_metrics(pred):
    labels = pred.label_ids
    preds = pred.predictions.argmax(-1)

    # Calculate accuracy
    acc = accuracy_score(labels, preds)

    # Calculate precision, recall, and F1 score
    precision, recall, f1, _ = precision_recall_fscore_support(
        labels, preds, average='binary'
    )

    return {
        'accuracy': acc,
        'precision': precision,
        'recall': recall,
        'f1': f1,
    }

# Combine and label the data
valid_phrases['Trip Validity'] = 1  # Valid phrases labeled as 1
invalid_phrases['Trip Validity'] = 0  # Invalid phrases labeled as 0

# Combine datasets
data = pd.concat([valid_phrases, invalid_phrases], ignore_index=True)

# Select only the 'Sentence' and 'label' columns
data = data[['Sentence', 'Trip Validity']]

tokenizer = AutoTokenizer.from_pretrained('camembert-base')
# tokenizer = BertTokenizer.from_pretrained('bert-base-uncased')

# Tokenization function
def tokenize(batch):
    return tokenizer(batch['Sentence'], padding=True, truncation=True, max_length=128)

class PhraseDataset(torch.utils.data.Dataset):
    def __init__(self, encodings, labels):
        self.encodings = encodings
        self.labels = labels
    def __getitem__(self, idx):
        item = {key: torch.tensor(val[idx]) for key, val in self.encodings.items()}
        item['labels'] = torch.tensor(self.labels[idx])
        return item
    def __len__(self):
        return len(self.labels)

train_texts, val_texts, train_labels, val_labels = train_test_split(
    data['Sentence'].tolist(),
    data['Trip Validity'].tolist(),
    test_size=0.2,
    random_state=42
)

# Tokenize the datasets
train_encodings = tokenizer(train_texts, truncation=True, padding=True, max_length=128)
val_encodings = tokenizer(val_texts, truncation=True, padding=True, max_length=128)

# Create dataset objects
train_dataset = PhraseDataset(train_encodings, train_labels)
val_dataset = PhraseDataset(val_encodings, val_labels)

# model = BertForSequenceClassification.from_pretrained('bert-base-uncased')
model = AutoModelForSequenceClassification.from_pretrained('camembert-base')
device = torch.device('cuda') if torch.cuda.is_available() else torch.device('cpu')
model = model.to(device)

training_args = TrainingArguments(
    output_dir='./results',          # Output directory
    num_train_epochs=3,              # Number of epochs
    per_device_train_batch_size=16,  # Batch size per device
    per_device_eval_batch_size=16,   # Batch size for evaluation
    evaluation_strategy='epoch',     # Evaluate at the end of each epoch
    logging_dir='./logs',            # Log directory
    save_steps=500,                  # Save model every 500 steps
    logging_steps=50,                # Log every 50 steps
)

trainer = Trainer(
    model=model,
    args=training_args,
    train_dataset=train_dataset,
    eval_dataset=val_dataset,
    compute_metrics=compute_metrics
)


trainer.train()
trainer.evaluate()


# Tokenize test phrases
test_texts = test_phrases['Sentence'].tolist()
test_labels = test_phrases['Trip Validity'].tolist()
test_encodings = tokenizer(test_texts, truncation=True, padding=True, max_length=128)

# Create test dataset
######## Saving the model
model.save_pretrained('./target/fine-tuned-bert')
tokenizer.save_pretrained('./target/fine-tuned-bert')
test_dataset = PhraseDataset(test_encodings, test_labels)  # Labels are placeholders

# After getting predictions from the model
predictions = trainer.predict(test_dataset)
pred_labels = predictions.predictions.argmax(-1)  # Predicted class labels
labels = predictions.label_ids  # True labels

# Generate classification report
report = classification_report(labels, pred_labels, target_names=['Invalid', 'Valid'])
print(report)

# Compute confusion matrix
cm = confusion_matrix(labels, pred_labels)
disp = ConfusionMatrixDisplay(confusion_matrix=cm, display_labels=['Invalid', 'Valid'])
disp.plot(cmap=plt.cm.Blues)
plt.title('Confusion Matrix')
plt.show()
## ROC curve
# Get probabilities for the positive class
probs = predictions.predictions[:, 1]
fpr, tpr, thresholds = roc_curve(labels, probs)
roc_auc = auc(fpr, tpr)

plt.figure()
plt.plot(fpr, tpr, color='darkorange', lw=2, label=f'ROC curve (AUC = {roc_auc:.2f})')
plt.plot([0, 1], [0, 1], color='navy', lw=2, linestyle='--')
plt.xlabel('False Positive Rate')
plt.ylabel('True Positive Rate')
plt.title('Receiver Operating Characteristic')
plt.legend(loc='lower right')
plt.show()


# Add predictions to the DataFrame
test_phrases['Predicted Label'] = pred_labels




