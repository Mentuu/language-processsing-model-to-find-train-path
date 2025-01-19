## Description

Le projet **Travel Order Resolver** vise à traiter des phrases textuelles, formulées en français, pour identifier et extraire des informations relatives à des trajets. Grâce à des techniques avancées de traitement du langage naturel (NLP), cette solution permet de :

- Détecter si une phrase correspond à un ordre de voyage valide.
- Extraire les villes de départ, d'arrivée, et les étapes intermédiaires.
- Valider les informations en croisant avec les données officielles des gares SNCF.
- Gérer une variété de phrases, y compris celles contenant des structures grammaticales complexes.

---

## Fonctionnalités principales

1. **Détection des ordres de voyage valides**
   - Classification des phrases en `VALID_TRIP` ou `INVALID_TRIP` à l'aide d'un modèle BERT fine-tuné.

2. **Extraction des informations clés**
   - Extraction précise des villes de départ, d'arrivée, et des étapes intermédiaires avec SpaCy.

3. **Validation des villes avec les données SNCF**
   - Intégration des communes issues de `liste-des-gares.csv` pour garantir la cohérence des trajets.

4. **Génération des phrases d’entraînement**
   - Script pour générer dynamiquement des phrases variées (valables et non valables).

5. **Traitement des contraintes**
   - Rejet des phrases contenant des modes de transport bannis.

---

## Mise en Route

### Prérequis

Avant de commencer, assurez-vous que votre environnement est configuré avec les éléments suivants :

- Python 3.8 ou supérieur
- Pip pour la gestion des dépendances
- GPU compatible avec CUDA (optionnel pour l'entraîment rapide)

### Installation des dépendances

Exécutez la commande suivante pour installer toutes les dépendances listées dans `requirements.txt` :

```bash
pip install -r requirements.txt
```

### Principales librairies incluses

- **SpaCy** : Traitement du langage naturel
- **Transformers (Hugging Face)** : Modèle BERT pour la classification
- **Pandas** : Manipulation des données
- **Torch** : Calculs pour BERT
- **JSON, CSV** : Gestion des données structurées

---

## Étapes du Projet

### 1. Génération des phrases d’entraînement

Utilisez le script `generate_phrases.py` pour créer des ensembles de phrases d'entraîment et de test.

```bash
python generate_phrases.py
```

Les phrases générées seront sauvegardées dans deux fichiers CSV :
- `phrases.csv` : Ensemble d'entraîment
- `test_phrases.csv` : Ensemble de test

### 2. Entraîner le modèle BERT

Entraînez le modèle BERT pour classer les phrases en fonction de leur validité.

```bash
python train_bert.py
```

### 3. Entraîner le modèle SpaCy

Le modèle SpaCy est utilisé pour extraire les entités nommées (villes de départ, d’arrivée, étapes intermédiaires).

1. Convertir les données au format SpaCy :
   ```bash
   python convert_to_spacy_format.py
   ```
2. Entraîner le modèle :
   ```bash
   python train_spacy_model.py
   ```

### 4. Utilisation du pipeline complet

Lancez le pipeline complet pour traiter une phrase et extraire les informations.

```bash
python main_pipeline.py --sentence "Je veux voyager de Paris à Lyon en passant par Dijon."
```

Sortie attendue :
- Ville de départ : Paris
- Ville d’arrivée : Lyon
- Villes intermédiaires : Dijon

---

## Architecture du Projet

1. **Modèle BERT** :
   - Classifie les phrases en `VALID_TRIP` ou `INVALID_TRIP`.

2. **Pipeline SpaCy** :
   - Identifie les entités nommées (villes et lieux).
   - Valide les informations avec les données SNCF.

---

## Ressources

- **Données SNCF** : `liste-des-gares.csv` doit être présent dans le répertoire.
- **Modèles pré-entraînés** : Les modèles SpaCy et BERT fine-tunés sont disponibles dans le répertoire `models/`.

---

## Auteur

Ce projet a été réalisé dans le cadre de l’étude des modèles NLP appliqués à la gestion des ordres de voyage.
