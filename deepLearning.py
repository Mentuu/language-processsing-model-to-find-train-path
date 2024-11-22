import pandas as pd
from transformers import AutoTokenizer, AutoModelForSequenceClassification, Trainer, TrainingArguments
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
from sklearn.utils.class_weight import compute_class_weight
import numpy as np

# Charger les données depuis phrases.csv et test_phrases.csv
data = pd.read_csv('phrases.csv')
test_phrases = pd.read_csv('test_phrases.csv')

# Sélectionner uniquement les colonnes 'Sentence' et 'Is Trip'
data = data[['Sentence', 'Is Trip']]
test_phrases = test_phrases[['Sentence', 'Is Trip']]

# Convertir la colonne 'Is Trip' en entier
data['Is Trip'] = data['Is Trip'].astype(int)
test_phrases['Is Trip'] = test_phrases['Is Trip'].astype(int)

# Fonction pour calculer les métriques
def compute_metrics(pred):
    labels = pred.label_ids
    preds = pred.predictions.argmax(-1)

    # Calculer l'accuracy
    acc = accuracy_score(labels, preds)

    # Calculer la précision, le rappel et le F1-score
    precision, recall, f1, _ = precision_recall_fscore_support(
        labels, preds, average='binary'
    )

    return {
        'accuracy': acc,
        'precision': precision,
        'recall': recall,
        'f1': f1,
    }

# Charger le tokenizer
tokenizer = AutoTokenizer.from_pretrained('camembert-base')

# Classe pour créer un dataset compatible avec PyTorch
class PhraseDataset(torch.utils.data.Dataset):
    def __init__(self, texts, labels):
        self.encodings = tokenizer(texts, truncation=True, padding=True, max_length=256)
        self.labels = labels
    def __getitem__(self, idx):
        item = {key: torch.tensor(val[idx]) for key, val in self.encodings.items()}
        item['labels'] = torch.tensor(self.labels[idx])
        return item
    def __len__(self):
        return len(self.labels)

# Séparer les données en ensembles d'entraînement et de validation
train_texts, val_texts, train_labels, val_labels = train_test_split(
    data['Sentence'].tolist(),
    data['Is Trip'].tolist(),
    test_size=0.2,
    random_state=42,
    stratify=data['Is Trip']  # Stratifier pour conserver la distribution des classes
)

# Créer les datasets
train_dataset = PhraseDataset(train_texts, train_labels)
val_dataset = PhraseDataset(val_texts, val_labels)

# Calculer les poids des classes pour gérer le déséquilibre éventuel
class_weights = compute_class_weight(
    class_weight='balanced',
    classes=np.unique(train_labels),
    y=train_labels
)
class_weights = torch.tensor(class_weights, dtype=torch.float)

# Charger le modèle CamemBERT
model = AutoModelForSequenceClassification.from_pretrained(
    'camembert-base',
    num_labels=2
)

# Définir le dispositif (GPU si disponible)
device = torch.device('cuda') if torch.cuda.is_available() else torch.device('cpu')
class_weights = class_weights.to(device)
model = model.to(device)

# Définir les arguments d'entraînement
training_args = TrainingArguments(
    output_dir='./results',          # Répertoire de sortie
    num_train_epochs=3,              # Nombre d'époques
    per_device_train_batch_size=8,  # Taille du batch par périphérique
    per_device_eval_batch_size=8,   # Taille du batch pour l'évaluation
    eval_strategy='epoch',           # Évaluer à la fin de chaque époque
    save_strategy='epoch',           # Sauvegarder le modèle à la fin de chaque époque
    logging_dir='./logs',            # Répertoire pour les logs
    load_best_model_at_end=True,     # Charger le meilleur modèle à la fin
    save_total_limit=2,              # Conserver seulement les deux meilleurs modèles
)

# Subclasser Trainer pour utiliser une fonction de perte personnalisée
class CustomTrainer(Trainer):
    def __init__(self, *args, class_weights=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.class_weights = class_weights

    def compute_loss(self, model, inputs, return_outputs=False, **kwargs):
        labels = inputs.get("labels").to(model.device)
        outputs = model(**inputs)
        logits = outputs.get('logits')
        loss_fct = torch.nn.CrossEntropyLoss(weight=self.class_weights)
        loss = loss_fct(logits.view(-1, model.config.num_labels), labels.view(-1))
        return (loss, outputs) if return_outputs else loss

# Créer le CustomTrainer
trainer = CustomTrainer(
    model=model,
    args=training_args,
    train_dataset=train_dataset,
    eval_dataset=val_dataset,
    compute_metrics=compute_metrics,
    class_weights=class_weights
)

# Entraîner le modèle
trainer.train()
trainer.evaluate()

# Préparer le dataset de test
test_texts = test_phrases['Sentence'].tolist()
test_labels = test_phrases['Is Trip'].tolist()
test_dataset = PhraseDataset(test_texts, test_labels)

######## debugging ################
print('balancing :',data['Is Trip'].value_counts())
train_sentences = set(train_texts)
test_sentences = set(test_texts)
overlap = train_sentences.intersection(test_sentences)
if overlap:
    print(f"Number of overlapping sentences: {len(overlap)}")
    data = data[~data['Sentence'].isin(overlap)]
######## debugging ################



######## Saving the model ################
model.save_pretrained('./target/fine-tuned-bert')
tokenizer.save_pretrained('./target/fine-tuned-bert')
test_dataset = PhraseDataset(test_texts, test_labels)  # Labels are placeholders
######## Saving the model ################

# Tester le modèle
predictions = trainer.predict(test_dataset)
pred_labels = predictions.predictions.argmax(-1)  # Étiquettes prédites
labels = predictions.label_ids  # Vraies étiquettes

# Générer le rapport de classification
report = classification_report(labels, pred_labels, target_names=['Non-Trajet', 'Trajet'])
print(report)

# Calculer et afficher la matrice de confusion
cm = confusion_matrix(labels, pred_labels)
disp = ConfusionMatrixDisplay(confusion_matrix=cm, display_labels=['Non-Trajet', 'Trajet'])
disp.plot(cmap=plt.cm.Blues)
plt.title('Matrice de Confusion')
plt.show()

# Courbe ROC
from sklearn.preprocessing import LabelBinarizer
lb = LabelBinarizer()
lb.fit(labels)
labels_binarized = lb.transform(labels)
probs = torch.nn.functional.softmax(torch.tensor(predictions.predictions), dim=-1)[:, 1].numpy()
fpr, tpr, thresholds = roc_curve(labels_binarized, probs)
roc_auc = auc(fpr, tpr)

plt.figure()
plt.plot(fpr, tpr, color='darkorange', lw=2, label=f'Courbe ROC (AUC = {roc_auc:.2f})')
plt.plot([0, 1], [0, 1], color='navy', lw=2, linestyle='--')
plt.xlabel('Taux de Faux Positifs')
plt.ylabel('Taux de Vrais Positifs')
plt.title('Caractéristique de Fonctionnement du Récepteur (ROC)')
plt.legend(loc='lower right')
plt.show()

# Ajouter les prédictions au DataFrame de test
test_phrases['Predicted Label'] = pred_labels
