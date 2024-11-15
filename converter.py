import const_utils
import spacy
import csv
import fct_utils
from spacy.matcher import Matcher
import pandas as pd

spacy.prefer_gpu()
nlp = spacy.load('fr_core_news_lg')
dataset = 'dataset.csv'
sncf_dataset = 'liste-des-gares.csv'

communes_set = set()
commune_to_stations = {}

# Load the dataset
df = pd.read_csv('dataset.csv')

# Keep relevant columns
df = df[['Sentence', 'Departure City', 'Arrival City', 'Trip Validity']]

# Convert 'Trip Validity' to numerical labels
df['Validity Label'] = df['Trip Validity'].map({'VALID_TRIP': 1, 'INVALID_TRIP': 0})

# Drop rows with missing values or invalid labels
df = df.dropna(subset=['Sentence', 'Validity Label'])


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

def extraire_lieux(phrase):
    doc = nlp(phrase)
    verbe = []

    # Utiliser le Matcher pour trouver les motifs
    matches = matcher(doc)
    
    # Trier les correspondances par leur position dans le texte
    matches = sorted(matches, key=lambda x: x[1])
    
    # Liste pour stocker les villes avec leur contexte
    cities_with_context = []

    for match_id, start, end in matches:
        span = doc[start:end]
        match_label = nlp.vocab.strings[match_id]
        
        if match_label == 'TRIP_PATTERN':
            # Initialiser le contexte
            current_context = None
            tokens = span
            for token in tokens:
                # Collecter les verbes
                if token.pos_ in ["VERB", "AUX"]:
                    verbe.append(token.lemma_)
                
                # Identifier les prépositions et ajuster le contexte
                if token.lower_ in ['de', 'depuis']:
                    current_context = 'DEPARTURE'
                elif token.lower_ in ['à', 'vers', 'jusqu\'à', 'pour', 'afin de']:
                    current_context = 'ARRIVAL'
                elif token.lower_ in ['en', 'passant', 'par', 'via']:
                    current_context = 'INTERMEDIATE'
                
                # Extraire les villes avec leur contexte
                if token.ent_type_ in ["LOC", "GPE"]:
                    city_name = token.text
                    cities_with_context.append((city_name, current_context))
                    # Réinitialiser le contexte après avoir assigné le lieu
                    current_context = None

    # Traitement des villes collectées
    lieu_depart = None
    lieu_arrivee = None
    lieux_intermediaires = []

    for city_name, context in cities_with_context:
        if context == 'DEPARTURE' and not lieu_depart:
            lieu_depart = city_name
        elif context == 'ARRIVAL':
            lieu_arrivee = city_name
        elif context == 'INTERMEDIATE':
            lieux_intermediaires.append(city_name)
        else:
            # Si le contexte est None
            if not lieu_depart:
                lieu_depart = city_name
            elif not lieu_arrivee:
                lieu_arrivee = city_name
            else:
                lieux_intermediaires.append(city_name)
                
    # Si aucun lieu n'a été trouvé par le Matcher, utiliser les entités
    if not lieu_depart or not lieu_arrivee:
        # Extraire les entités de type lieu
        entities = [ent.text for ent in doc.ents if ent.label_ in ["LOC", "GPE"]]
        if entities:
            if not lieu_depart:
                lieu_depart = entities[0]
            if not lieu_arrivee and len(entities) > 1:
                lieu_arrivee = entities[-1]
            # Les lieux intermédiaires sont les entités entre départ et arrivée
            lieux_intermediaires = entities[1:-1]
    
    # Normaliser les noms de villes
    lieu_depart = fct_utils.normalize_str(lieu_depart) if lieu_depart else None
    lieu_arrivee = fct_utils.normalize_str(lieu_arrivee) if lieu_arrivee else None
    lieux_intermediaires = [fct_utils.normalize_str(city) for city in lieux_intermediaires]

    # Valider les villes contre le set de communes
    if lieu_depart and lieu_depart not in communes_set:
        lieu_depart = None
    if lieu_arrivee and lieu_arrivee not in communes_set:
        lieu_arrivee = None
    lieux_intermediaires = [city for city in lieux_intermediaires if city in communes_set]

    # Enlever les lieux déjà assignés des lieux intermédiaires
    assigned_cities = set(filter(None, [lieu_depart, lieu_arrivee]))
    lieux_intermediaires = [city for city in lieux_intermediaires if city not in assigned_cities]

    # Supprimer les doublons dans les verbes
    verbe = list(set(verbe))

    return verbe, lieu_depart, lieu_arrivee, lieux_intermediaires

def est_voyage_valide(phrase, lieu_depart, lieu_arrivee):
    # Check if both departure and arrival cities are valid
    if not lieu_depart or not lieu_arrivee or lieu_depart == lieu_arrivee:
        return "INVALID_TRIP"
    
    if lieu_depart not in communes_set or lieu_arrivee not in communes_set:
        return "INVALID_TRIP"
    
    doc = nlp(phrase)
    movement_verb_found = False
    
    for token in doc:
        if token.pos_ == 'VERB':
            lemma = token.lemma_.lower()
            if lemma in const_utils.movement_verbs:
                # Check for negation
                negation_words = {'ne', 'pas', 'jamais', 'plus', 'rien', 'personne', 'aucun', 'guère'}
                negated = any(
                    child.dep_ == 'advmod' and child.lemma_.lower() in negation_words
                    for child in token.children
                )
                if negated:
                    return "INVALID_TRIP"
                movement_verb_found = True
                break
    if not movement_verb_found:
        return "INVALID_TRIP"
    
    # Check for invalid modes of transport using lemmatization
    invalid_transports = set(const_utils.invalid_transports)
    tokens_lemmatized = [token.lemma_.lower() for token in doc]
    if invalid_transports.intersection(tokens_lemmatized):
        return "INVALID_TRIP"
    
    return "VALID_TRIP"


# Processing the utils.dataset
total_phrases = 0
correct_departure = 0
correct_arrival = 0
correct_validity = 0

############################################################################# Main #####################
with open(dataset, 'r', encoding='utf-8') as csvfile:
    csvreader = csv.DictReader(csvfile)
    
    for row in csvreader:
        # Extract data from each row
        phrase = row['Sentence']
        ville_depart_attendue_raw = row['Departure City'].strip()
        ville_arrivee_attendue_raw = row['Arrival City'].strip()
        validite_attendue = row['Trip Validity'].strip()
        
        # Normalize the expected cities
        ville_depart_attendue = fct_utils.normalize_str(ville_depart_attendue_raw)
        ville_arrivee_attendue = fct_utils.normalize_str(ville_arrivee_attendue_raw)
        
        # Keep track of the total number of phrases
        total_phrases += 1

        # Extract departure and arrival locations
        verbe, lieu_depart_raw, lieu_arrivee_raw, lieux_intermediaires = extraire_lieux(phrase)
        
        # Normalize the extracted cities
        lieu_depart = fct_utils.normalize_str(lieu_depart_raw) if lieu_depart_raw else None
        lieu_arrivee = fct_utils.normalize_str(lieu_arrivee_raw) if lieu_arrivee_raw else None

        # Check if the extracted cities are in the communes list
        if lieu_depart and lieu_depart in communes_set:
            # Get the departure stations
            departure_stations = commune_to_stations[lieu_depart]
        else:
            # print(f"Departure city '{lieu_depart_raw}' not found in SNCF communes list.")
            lieu_depart = None
            departure_stations = None

        if lieu_arrivee and lieu_arrivee in communes_set:
            # Get the arrival stations
            arrival_stations = commune_to_stations[lieu_arrivee]
        else:
            # print(f"Arrival city '{lieu_arrivee_raw}' not found in SNCF communes list.")
            lieu_arrivee = None
            arrival_stations = None

        # Validate the mode of transport
        validite_predite = est_voyage_valide(phrase, lieu_depart, lieu_arrivee)
    
        # Check correctness
        if validite_predite == validite_attendue:
            correct_validity += 1

        # Display the results for debugging
        if ((validite_predite != validite_attendue and validite_attendue != 'INVALID_TRIP') or (lieu_depart != ville_depart_attendue and lieu_depart in communes_set) or (lieu_arrivee != ville_arrivee_attendue)):
            print(f"Phrase: {phrase}")
            print(f"Verbes trouvés : {verbe}")
            print(f"Lieu de départ détecté : {lieu_depart} (Attendu : {ville_depart_attendue})")
            print(f"Lieu d'arrivée détecté : {lieu_arrivee} (Attendu : {ville_arrivee_attendue})")
            print(f"Lieux intermédiaires : {lieux_intermediaires}")
            print(f"Validité détectée : {validite_predite} (Attendu : {validite_attendue})")
            print("\n")

# Calculate the success rates
validity_success_rate = (correct_validity / total_phrases) * 100

# Display the success rates
print(f"Taux de succès pour la validité : {validity_success_rate:.2f}%")