import spacy
import csv
import fct_utils
from spacy.matcher import Matcher
import pandas as pd
from transformers import AutoTokenizer, AutoModelForSequenceClassification
import torch

model_path = './target/fine-tuned-bert'
tokenizer = AutoTokenizer.from_pretrained(model_path)
model = AutoModelForSequenceClassification.from_pretrained(model_path)

# Move the model to the appropriate device (GPU or CPU)
device = torch.device('cuda') if torch.cuda.is_available() else torch.device('cpu')
model = model.to(device)

spacy.prefer_gpu()
nlp = spacy.load('fr_core_news_lg')
dataset = 'dataset.csv'
sncf_dataset = 'liste-des-gares.csv'

communes_set = set()
commune_to_stations = {}

df = pd.read_csv('dataset.csv')

df = df[['Sentence', 'Departure City', 'Arrival City', 'Trip Validity']]

df['Validity Label'] = df['Trip Validity'].map({'VALID_TRIP': 1, 'INVALID_TRIP': 0})

df = df.dropna(subset=['Sentence', 'Validity Label'])

banned_vehicles = ["moto", "voiture", "scooter", "camion", "quad", "buggy", "chameau", "montgolfière", "trottinette", "vélo", "vélo électrique", "tapis volant", "hélicoptère", "avion", "bateau", "yacht", "sous-marin", "fusée", "vaisseau spatial"]

matcher = Matcher(nlp.vocab)
pattern_trip = [
    # Sujet (optionnel)
    {'POS': 'PRON', 'OP': '?'},

    # Verbe de départ
    {'LEMMA': {'IN': ['quitter', 'partir', 'prendre', 'laisser', 'sortir']}, 'POS': 'VERB'},

    # Préposition de départ (optionnelle)
    {'LOWER': {'IN': ['de', 'depuis']}, 'OP': '?'},

    # Ville de départ
    {'ENT_TYPE': 'LOC', 'OP': '+'},

    # Préposition de destination
    {'LOWER': {'IN': ['pour', 'afin de', 'vers']}, 'OP': '?'},

    # Verbe de mouvement ou d'intention (optionnel)
    {'LEMMA': {'IN': ['aller', 'rejoindre', 'rendre', 'visiter']}, 'OP': '*'},

    # Préposition avant la ville d'arrivée (optionnelle)
    {'LOWER': {'IN': ['à', 'vers']}, 'OP': '?'},

    # Ville d'arrivée
    {'ENT_TYPE': 'LOC', 'OP': '+'},

    # Mots supplémentaires (optionnels)
    {'OP': '*'},
]

matcher.add('TRIP_PATTERN', [pattern_trip])


########################################## map des communes aux gares depuis le csv sncf ###############

with open(sncf_dataset, 'r', encoding='utf-8') as sncf_file:
    csvreader = csv.DictReader(sncf_file, delimiter=';')
    for row in csvreader:
        commune_raw = row['COMMUNE'].strip()
        station_name = row['LIBELLE'].strip()
        
        # Normalize the commune name
        commune = fct_utils.normalize_str(commune_raw)
        
        # Add the commune to the set
        communes_set.add(commune)
        # After loading communes_set
        # Map the commune to its stations
        if commune in commune_to_stations:
            commune_to_stations[commune].add(station_name)
        else:
            commune_to_stations[commune] = {station_name}

#################################################################################### fonctions ############################

from spacy.matcher import Matcher

def extraireLieux(phrase):
    doc = nlp(phrase)
    lieu_depart = None
    lieu_arrivee = None

    matcher = Matcher(nlp.vocab)

    # Motif pour la ville de départ
    dep_pattern = [
        {"LEMMA": {"IN": ["être", "se trouver", "résider", "habiter"]}, "POS": {"IN": ["VERB", "AUX"]}},
        {"OP": "*"},
        {"LOWER": {"IN": ["à", "en"]}},
        {"OP": "*"},
        {"ENT_TYPE": {"IN": ["LOC", "GPE"]}}
    ]
    matcher.add("DEPARTURE_PATTERN", [dep_pattern])

    # Motif pour la ville d'arrivée
    arr_pattern = [
        {"LEMMA": {"IN": ["aller", "arriver", "rejoindre", "partir", "souhaiter", "vouloir", "devoir", "prendre", "quitter"]}, "POS": {"IN": ["VERB", "AUX"]}},
        {"OP": "*"},
        {"LOWER": {"IN": ["à", "pour", "vers", "en"]}, "OP": "?"},
        {"OP": "*"},
        {"ENT_TYPE": {"IN": ["LOC", "GPE"]}}
    ]
    matcher.add("ARRIVAL_PATTERN", [arr_pattern])

    matches = matcher(doc)
    for match_id, start, end in matches:
        span = doc[start:end]
        match_label = nlp.vocab.strings[match_id]
        if match_label == "DEPARTURE_PATTERN" and not lieu_depart:
            # Rechercher le dernier token qui est une entité de lieu
            for token in reversed(span):
                if token.ent_type_ in ["LOC", "GPE"]:
                    lieu_depart = token.text
                    break
        elif match_label == "ARRIVAL_PATTERN" and not lieu_arrivee:
            for token in reversed(span):
                if token.ent_type_ in ["LOC", "GPE"]:
                    lieu_arrivee = token.text
                    break

    # Normalisation et validation
    lieu_depart = fct_utils.normalize_str(lieu_depart) if lieu_depart else None
    lieu_arrivee = fct_utils.normalize_str(lieu_arrivee) if lieu_arrivee else None

    if lieu_depart and lieu_depart not in communes_set:
        print(f"lieu_depart: {lieu_depart} n'est pas une commune française.")
        lieu_depart = None
    if lieu_arrivee and lieu_arrivee not in communes_set:
        print(f"lieu_arrivee: {lieu_arrivee} n'est pas une commune française.")
        lieu_arrivee = None

    return [], lieu_depart, lieu_arrivee, []


def estTrajet(phrase):
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
    predicted_class_id = logits.argmax(-1).item()

    class_labels = ['Invalid', 'Valid']
    predicted_label = class_labels[predicted_class_id]
    if (predicted_label == 'Invalid'):
        return "0"
    else:
        return "1"
    
def is_banned_vehicle(phrase):
    doc = nlp(phrase.lower())
    for token in doc:
        # Vérifier si le token est un nom commun
        if token.pos_ == "NOUN":
            # Normaliser le mot en enlevant les accents et en le mettant en minuscule
            vehicle = token.lemma_.lower()
            if vehicle in banned_vehicles:
                return 1
    return 0


def processPhrases(datasetToProcess):
    with open(datasetToProcess, 'r', encoding='utf-8') as csvfile:
        csvreader = csv.DictReader(csvfile)

        for row in csvreader:
            phrase = row['Sentence']
            ville_depart_attendue_raw = row['Departure City'].strip()
            ville_arrivee_attendue_raw = row['Arrival City'].strip()
            ville_intermediaire_attendue_raw = row['Intermediate City'].strip()
            validite_attendue = row['Trip Validity'].strip()
            
            ville_depart_attendue = fct_utils.normalize_str(ville_depart_attendue_raw)
            ville_arrivee_attendue = fct_utils.normalize_str(ville_arrivee_attendue_raw)
            ville_intermediaire_attendue = fct_utils.normalize_str(ville_intermediaire_attendue_raw)

            if estTrajet(phrase) == "0" and validite_attendue == "1":
                print(f"Phrase: {phrase} is a INVALID trip, [NOT A TRIP], validité attendue: {validite_attendue}\n")
                continue
            if is_banned_vehicle(phrase) == 1:
                # print(f"Phrase: {phrase} is a INVALID trip, [BANNED VEHICULE],validité attendue: {validite_attendue}\n")
                continue

            verbe, lieu_depart_raw, lieu_arrivee_raw, lieux_intermediaires_raw = extraireLieux(phrase)
            lieu_depart = fct_utils.normalize_str(lieu_depart_raw) if lieu_depart_raw else None
            lieu_arrivee = fct_utils.normalize_str(lieu_arrivee_raw) if lieu_arrivee_raw else None
            lieux_intermediaires = [fct_utils.normalize_str(city) for city in lieux_intermediaires_raw] if lieux_intermediaires_raw else []
            if lieu_depart and lieu_depart in communes_set:
                departure_stations = commune_to_stations[lieu_depart]
            else:
                if validite_attendue == "1":
                    print(f"lieu_depart: {lieu_depart}")
                    print(f"Phrase: {phrase} is a INVALID trip, [VILLE NON FRANCAISE], validité attendu: {validite_attendue}\n")
                lieu_depart = None
                departure_stations = None
                continue
            if lieu_arrivee and lieu_arrivee in communes_set:
                arrival_stations = commune_to_stations[lieu_arrivee]
            else:
                if validite_attendue == "1":
                    print(f"lieu_arrivee",{lieu_arrivee})
                    print(f"Phrase: {phrase} is a INVALID trip, [VILLE NON FRANCAISE]: {validite_attendue}\n")
                arrival_stations = None
                lieu_arrivee = None
                continue
            if ville_arrivee_attendue != lieu_arrivee:
                print(f"Phrase: {phrase}")
                print(f"Ville de d'arrive attendue: {ville_arrivee_attendue} |||| Ville de d'arrivee extraite: {lieu_arrivee}\n")
                break
            elif ville_depart_attendue != lieu_depart:
                print(f"Phrase: {phrase}")
                print(f"Ville de départ attendue: {ville_depart_attendue} |||| Ville de départ extraite: {lieu_depart}\n")
                break
            elif ville_intermediaire_attendue == "NONE" and lieux_intermediaires != []:
                print(f"Phrase: {phrase}")
                print(f"Ville intermédiaire attendue: {ville_intermediaire_attendue} |||| Ville intermédiaire extraite: {lieux_intermediaires}\n")
                break

            # print(f"Phrase: {phrase} is a VALID trip, validité attendue: {validite_attendue}")
            # print(f"Ville de départ: {lieu_depart}, Ville de départ attendue: {ville_depart_attendue}")
            # print(f"Ville d'arrivée: {lieu_arrivee}, Ville d'arrivée attendue: {ville_arrivee_attendue}")
            # print(f"Villes intermédiaires: {lieux_intermediaires}, Ville intermédiaire attendue: {ville_intermediaire_attendue}\n")
            # print(f"//////////////////////////////////////////////////////////////////////////////////////////////////////////////\n")

# print("COMMUNES SET",communes_set)
processPhrases(dataset)