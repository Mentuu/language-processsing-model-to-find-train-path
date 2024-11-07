import const_utils
import spacy
import csv
import fct_utils

spacy.prefer_gpu()
nlp = spacy.load('fr_core_news_lg')
dataset = 'dataset.csv'
sncf_dataset = 'liste-des-gares.csv'

communes_set = set()
commune_to_stations = {}

# Read the SNCF stations CSV file
with open(sncf_dataset, 'r', encoding='utf-8') as sncf_file:
    csvreader = csv.DictReader(sncf_file, delimiter=';')
    for row in csvreader:
        commune_raw = row['COMMUNE'].strip()
        station_name = row['LIBELLE'].strip()
        
        # Normalize the commune name
        commune = fct_utils.normalize_str(commune_raw)
        
        # Add the commune to the set
        communes_set.add(commune)
        
        # Map the commune to its stations
        if commune in commune_to_stations:
            commune_to_stations[commune].add(station_name)
        else:
            commune_to_stations[commune] = {station_name}


def extraire_lieux(phrase):
    doc = nlp(phrase)
    # Extract entities labeled as locations (LOC) or geopolitical entities (GPE)
    lieux = [ent.text for ent in doc.ents if ent.label_ in ["LOC", "GPE"]]
    
    verbe = [token.text for token in doc if token.pos_ in ["VERB", "AUX"]]
    
    # Extract specific location elements
    lieu_depart = lieux[0] if len(lieux) > 0 else None
    lieu_arrivee = lieux[1] if len(lieux) > 1 else None
    lieux_intermediaires = lieux[2:] if len(lieux) > 2 else []
    
    return verbe, lieu_depart, lieu_arrivee, lieux_intermediaires

def est_voyage_valide(phrase):
    doc = nlp(phrase)
    print(phrase)
    movement_verb_found = False
    print("Tokens and POS tags:")
    ##for debugging:
    for token in doc:
        print(f"Text: {token.text}, POS: {token.pos_}, Lemma: {token.lemma_}")
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
            print(f"Departure city '{lieu_depart_raw}' not found in SNCF communes list.")
            lieu_depart = None
            departure_stations = None

        if lieu_arrivee and lieu_arrivee in communes_set:
            # Get the arrival stations
            arrival_stations = commune_to_stations[lieu_arrivee]
        else:
            print(f"Arrival city '{lieu_arrivee_raw}' not found in SNCF communes list.")
            lieu_arrivee = None
            arrival_stations = None

        # Validate the mode of transport
        validite_predite = est_voyage_valide(phrase)
    
        # Check correctness
        if lieu_depart == ville_depart_attendue:
            correct_departure += 1
        else:
            print(f"Incorrect departure city detected: {lieu_depart_raw} (Expected: {ville_depart_attendue_raw})")

        if lieu_arrivee == ville_arrivee_attendue:
            correct_arrival += 1
        else:
            print(f"Incorrect arrival city detected: {lieu_arrivee_raw} (Expected: {ville_arrivee_attendue_raw})")

        if validite_predite == validite_attendue:
            correct_validity += 1

        # Display the results
        print(f"Phrase: {phrase}")
        print(f"Verbes trouvés : {verbe}")
        print(f"Lieu de départ détecté : {lieu_depart} (Attendu : {ville_depart_attendue})")
        print(f"Lieu d'arrivée détecté : {lieu_arrivee} (Attendu : {ville_arrivee_attendue})")
        print(f"Lieux intermédiaires : {lieux_intermediaires}")
        print(f"Validité détectée : {validite_predite} (Attendu : {validite_attendue})")
        print("\n")

# Calculate success rates
departure_success_rate = (correct_departure / total_phrases) * 100
arrival_success_rate = (correct_arrival / total_phrases) * 100
validity_success_rate = (correct_validity / total_phrases) * 100

# Display success rates
print(f"Taux de succès pour les lieux de départ : {departure_success_rate:.2f}%")
print(f"Taux de succès pour les lieux d'arrivée : {arrival_success_rate:.2f}%")
print(f"Taux de succès pour la validité : {validity_success_rate:.2f}%")