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

    # --- 1) Build separate matchers for departure, arrival, and intermediate
    departure_matcher = Matcher(nlp.vocab)
    arrival_matcher = Matcher(nlp.vocab)
    intermediate_matcher = Matcher(nlp.vocab)

    # --- 2) Define multiple patterns for departure
    # Pattern A: "depuis|de + <LOC>"
    dep_pattern_a = [
        {"LOWER": {"IN": ["depuis", "de"]}},
        {"ENT_TYPE": {"IN": ["LOC", "GPE"]}, "OP": "+"}
    ]
    # Pattern B: "je suis|je me trouve|je suis actuellement à <LOC>"
    #  - We'll allow optional words in between, e.g. "je suis actuellement à"
    dep_pattern_b = [
        {"LOWER": {"IN": ["je"]}, "OP": "?"},
        {"LEMMA": {"IN": ["être", "se_trouver"]}, "OP": "+"},  # "suis", "me trouve"
        {"LOWER": {"IN": ["actuellement"]}, "OP": "*"},
        {"LOWER": {"IN": ["à", "au", "en"]}, "OP": "+"},
        {"ENT_TYPE": {"IN": ["LOC", "GPE"]}, "OP": "+"}
    ]

    dep_pattern_c = [
        {"LEMMA": {"IN": ["partir", "voyager"]}, "OP": "+"},
        {"OP": "*"},
        {"LOWER": {"IN": ["de", "depuis"]}, "OP": "+"},
        {"ENT_TYPE": {"IN": ["LOC", "GPE"]}, "OP": "+"}
    ]

    dep_pattern_d = [
        {"LEMMA": {"IN": ["quitter"]}, "OP": "+"},
        {"OP": "*"},    
        {"ENT_TYPE": {"IN": ["LOC", "GPE"]}, "OP": "+"}
    ]

    # Add them to the departure_matcher
    departure_matcher.add("DEPARTURE_PATTERN", [dep_pattern_a, dep_pattern_b, dep_pattern_c, dep_pattern_d])

    # --- 3) Define multiple patterns for arrival
    # Pattern A: "aller|rendre|rejoindre|vouloir + à|pour|vers|en + <LOC>"

    arr_pattern_a = [
        {"LOWER": {"IN": ["pour", "afin"]}, "OP": "*"},
        {"LOWER": {"REGEX": r"^(me|te|se|m’|t’|s’)$"}, "OP": "*"},
        {"LEMMA": {"IN": ["aller", "arriver", "rendre", "rejoindre", "vouloir", "souhaiter"]}, "OP": "+"},
        {"OP": "*"},
        {"LOWER": {"IN": ["à", "pour", "vers", "en"]}, "OP": "+"},
        {"ENT_TYPE": {"IN": ["LOC", "GPE"]}, "OP": "+"}
    ]
    # Pattern B: "pour + <LOC>"
    arr_pattern_b = [
        {"LOWER": {"IN": ["pour", "vers", "à", "en"]}},
        {"ENT_TYPE": {"IN": ["LOC", "GPE"]}, "OP": "+"}
    ]

    arr_pattern_c = [
        {"LEMMA": {"IN": ["voyager"]}, "OP": "+"},
        {"LOWER": {"IN": ["à", "vers"]}, "OP": "+"},
        {"ENT_TYPE": {"IN": ["LOC", "GPE"]}, "OP": "+"}
    ]
    # Add them to the arrival_matcher
    arrival_matcher.add("ARRIVAL_PATTERN", [arr_pattern_a, arr_pattern_b, arr_pattern_c])

    # --- 4) Define patterns for intermediate locations
    # "en passant par <LOC>", "via <LOC>", "par <LOC>"
    inter_pattern_a = [
        {"LOWER": {"IN": ["par", "via"]}, "OP": "+"},
        {"ENT_TYPE": {"IN": ["LOC", "GPE"]}, "OP": "+"}
    ]
    inter_pattern_b = [
        {"LOWER": "passant"},
        {"LOWER": "par"},
        {"ENT_TYPE": {"IN": ["LOC", "GPE"]}, "OP": "+"}
    ]
    intermediate_matcher.add("INTER_PATTERN", [inter_pattern_a, inter_pattern_b])

    # --- 5) Apply matchers to doc
    dep_matches = departure_matcher(doc)
    arr_matches = arrival_matcher(doc)
    inter_matches = intermediate_matcher(doc)

    # Sort by start index so we read from left to right
    dep_matches = sorted(dep_matches, key=lambda x: x[1])
    arr_matches = sorted(arr_matches, key=lambda x: x[1])
    inter_matches = sorted(inter_matches, key=lambda x: x[1])

    lieu_depart = None
    lieu_arrivee = None
    lieux_intermediaires = []

    # --- 6) Extract departure from the earliest departure match
    if dep_matches:
        _, start, end = dep_matches[0]
        span = doc[start:end]
        # Check for recognized entity
        for ent in span.ents:
            if ent.label_ in ["LOC", "GPE"]:
                lieu_depart = ent.text
                break

    # --- 7) Extract arrival from the *last* arrival match
    # (or the first, depending on your logic)
    if arr_matches:
        _, start, end = arr_matches[-1]
        span = doc[start:end]
        for ent in span.ents:
            if ent.label_ in ["LOC", "GPE"]:
                lieu_arrivee = ent.text
                break

    # --- 8) Extract intermediates
    if inter_matches:
        for _, start, end in inter_matches:
            span = doc[start:end]
            for ent in span.ents:
                if ent.label_ in ["LOC", "GPE"]:
                    lieux_intermediaires.append(ent.text)

    # --- 9) Return your final result
    return [], lieu_depart, lieu_arrivee, lieux_intermediaires



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

            if (estTrajet(phrase) == "0" and validite_attendue == "1") or (validite_attendue == "0" and estTrajet(phrase) == "0"):
                print(f"Phrase: {phrase} is a INVALID trip, [NOT A TRIP], validité attendue: {validite_attendue}\n")
                continue    
            if is_banned_vehicle(phrase) == 1:
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
                    print(f"lieu_arrivee: {lieu_arrivee}")
                    print(f"Phrase: {phrase} is a INVALID trip, [VILLE NON FRANCAISE]: {validite_attendue}\n")
                arrival_stations = None
                lieu_arrivee = None
                continue

            print(f"Phrase: {phrase} is a VALID trip, validité attendue: {validite_attendue}")
            print(f"Ville de départ: {lieu_depart}, Ville de départ attendue: {ville_depart_attendue}")
            print(f"Ville d'arrivée: {lieu_arrivee}, Ville d'arrivée attendue: {ville_arrivee_attendue}")
            print(f"Villes intermédiaires: {lieux_intermediaires}, Ville intermédiaire attendue: {ville_intermediaire_attendue}\n")
            print(f"//////////////////////////////////////////////////////////////////////////////////////////////////////////////\n")

# print("COMMUNES SET",communes_set)
processPhrases(dataset)