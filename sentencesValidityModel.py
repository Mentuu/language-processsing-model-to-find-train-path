from datasets import load_dataset
from transformers import CamembertTokenizer, CamembertForSequenceClassification, Trainer, TrainingArguments
import numpy as np
from sklearn.metrics import accuracy_score, precision_recall_fscore_support

# Load dataset
dataset = load_dataset('csv', data_files={'train': 'train_data.csv', 'test': 'test_data.csv'})

# Initialize tokenizer
tokenizer = CamembertTokenizer.from_pretrained('camembert-base')

# Tokenization function
def tokenize_function(examples):
    return tokenizer(examples['sentence'], padding='max_length', truncation=True)

# Tokenize dataset
tokenized_datasets = dataset.map(tokenize_function, batched=True)

# Prepare datasets
tokenized_datasets = tokenized_datasets.remove_columns(['sentence'])
tokenized_datasets = tokenized_datasets.rename_column('label', 'labels')
tokenized_datasets.set_format('torch')
train_dataset = tokenized_datasets['train']
eval_dataset = tokenized_datasets['test']

# Initialize model
model = CamembertForSequenceClassification.from_pretrained('camembert-base', num_labels=2)

# Define compute_metrics
def compute_metrics(pred):
    labels = pred.label_ids
    preds = np.argmax(pred.predictions, axis=1)
    precision, recall, f1, _ = precision_recall_fscore_support(labels, preds, average='binary')
    acc = accuracy_score(labels, preds)
    return {
        'accuracy': acc,
        'f1': f1,
        'precision': precision,
        'recall': recall
    }

# Training arguments
training_args = TrainingArguments(
    output_dir='./results',
    num_train_epochs=3,
    per_device_train_batch_size=16,
    per_device_eval_batch_size=64,
    warmup_steps=500,
    weight_decay=0.01,
    evaluation_strategy='epoch',
    logging_dir='./logs',
    logging_steps=10,
)

# Initialize Trainer with compute_metrics
trainer = Trainer(
    model=model,
    args=training_args,
    train_dataset=train_dataset,
    eval_dataset=eval_dataset,
    compute_metrics=compute_metrics,
)

# Train model
trainer.train()

# Save model and tokenizer
model.save_pretrained('./trained_model')
tokenizer.save_pretrained('./trained_model')