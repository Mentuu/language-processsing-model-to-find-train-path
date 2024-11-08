import const_utils
import spacy
import csv
import fct_utils
from spacy.matcher import Matcher

spacy.prefer_gpu()
nlp = spacy.load('fr_core_news_lg')
dataset = 'dataset.csv'
sncf_dataset = 'liste-des-gares.csv'

communes_set = set()
commune_to_stations = {}

from spacy.matcher import Matcher

matcher = Matcher(nlp.vocab)
pattern_departure = [
    {'LOWER': {'IN': ['de', 'depuis']}},
    {'ENT_TYPE': 'LOC', 'OP': '+'}
]
matcher.add('DEPARTURE_PATTERN', [pattern_departure])

pattern_arrival = [
    {'LOWER': {'IN': ['à', 'vers']}},
    {'ENT_TYPE': 'LOC', 'OP': '+'}
]
matcher.add('ARRIVAL_PATTERN', [pattern_arrival])


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
    lieu_depart = None
    lieu_arrivee = None
    lieux_intermediaires = []
    
    # Initialize variables to keep track of matched cities
    departure_cities = []
    arrival_cities = []
    
    # Use Matcher to find patterns
    matches = matcher(doc)
    
    # Sort matches by their position in the text
    matches = sorted(matches, key=lambda x: x[1])
    
    for match_id, start, end in matches:
        span = doc[start:end]
        match_label = nlp.vocab.strings[match_id]
        
        # Collect city tokens (can be multi-word)
        city_tokens = []
        for token in span:
            if token.ent_type_ in ["LOC", "GPE"]:
                city_tokens.append(token.text)
            elif city_tokens and token.pos_ == "PROPN":
                # Include proper nouns following the city name (e.g., 'New York')
                city_tokens.append(token.text)
            else:
                # Stop collecting if the token is not part of the city name
                break
        city_name = ' '.join(city_tokens)
        
        # Assign cities based on the pattern matched
        if match_label == 'DEPARTURE_PATTERN' and city_name:
            if not lieu_depart:
                lieu_depart = city_name
        elif match_label == 'ARRIVAL_PATTERN' and city_name:
            if not lieu_arrivee:
                lieu_arrivee = city_name
    
    # If Matcher didn't find cities, fall back to entities
    entities = [(ent.text, ent.start_char, ent.label_) for ent in doc.ents if ent.label_ in ["LOC", "GPE"]]
    entities_text = [ent[0] for ent in entities]
    
    # Assign departure and arrival if still None
    if not lieu_depart and entities:
        lieu_depart = entities[0][0]
    if not lieu_arrivee and len(entities) > 1:
        lieu_arrivee = entities[-1][0]
    
    # Remove assigned cities from intermediate locations
    assigned_cities = set(filter(None, [lieu_depart, lieu_arrivee]))
    lieux_intermediaires = [fct_utils.normalize_str(city) for city in entities_text if fct_utils.normalize_str(city) not in assigned_cities]
    
    # Normalize extracted cities
    lieu_depart = fct_utils.normalize_str(lieu_depart) if lieu_depart else None
    lieu_arrivee = fct_utils.normalize_str(lieu_arrivee) if lieu_arrivee else None
    
    # Validate cities against communes_set
    if lieu_depart and lieu_depart not in communes_set:
        lieu_depart = None
    if lieu_arrivee and lieu_arrivee not in communes_set:
        lieu_arrivee = None
    
    verbe = [token.text for token in doc if token.pos_ in ["VERB", "AUX"]]
    
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
        if validite_predite != validite_attendue:
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