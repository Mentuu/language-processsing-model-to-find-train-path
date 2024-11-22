import csv
import random
import re
import json
import os

nb_phrases = 10000
nb_phrases_test = 1500

# Supprimer les fichiers existants
if os.path.exists("phrases.csv"):
    os.remove("phrases.csv")
if os.path.exists("test_phrases.csv"):
    os.remove("test_phrases.csv")

# Importer les villes françaises depuis le fichier JSON
with open('cities.json') as f:
    file = json.load(f)
    cities = [city['COMMUNE'] for city in file]

# Ajouter les villes internationales à la liste des villes
international_cities = [
    'New York', 'Tokyo', 'Berlin', 'Amsterdam', 'Bruxelles', 'Genève', 'Lisbonne',
    'Madrid', 'Rome', 'Prague', 'Vienne', 'Copenhague', 'Oslo', 'Stockholm',
    'Helsinki', 'Dublin', 'Athènes', 'Moscou', 'Le Caire', 'Sydney', 'Pékin'
]
cities.extend(international_cities)

# Définir les modes de transport et les temps
modes = ['en train', 'en voiture', 'en bus', 'en avion', 'en bateau', 'à pied', 'à vélo', 'en métro']
times = ['demain matin', 'cet après-midi', 'ce soir', 'la semaine prochaine', 'aujourd\'hui']

# Définir des synonymes pour diversifier les phrases
synonyms = {
    'aller': ['se rendre', 'partir pour', 'visiter', 'rejoindre'],
    'partir': ['quitter', 'démarrer de', 's\'éloigner de'],
    'voyager': ['se déplacer', 'faire un voyage', 'parcourir'],
    'prendre': ['emprunter', 'monter dans', 'utiliser'],
    'train': ['TGV', 'TER', 'wagon'],
    'avion': ['vol', 'appareil', 'aéronef'],
    'voiture': ['automobile', 'véhicule', 'bagnole'],
    'bus': ['autocar', 'car'],
    'bateau': ['navire', 'vaisseau', 'ferry'],
    'aujourd\'hui': ['ce jour', 'en ce moment'],
    'demain matin': ['le matin prochain', 'à l\'aube'],
    'cet après-midi': ['cette après-midi', 'dans l\'après-midi'],
    'je': ['moi', 'pour ma part'],
    'vous': ['tu', 'te'],
    'réunion': ['rendez-vous', 'entretien', 'meeting'],
    'itinéraire': ['route', 'trajet', 'chemin'],
    'trajet': ['voyage', 'parcours', 'déplacement'],
    'besoin': ['nécessité', 'envie', 'souhait'],
    'meilleur': ['optimal', 'idéal', 'parfait'],
    'horaires': ['heures', 'planning', 'agenda'],
    'pouvez-vous': ['peux-tu', 'est-il possible de'],
    'suggestion': ['proposition', 'idée', 'conseil'],
}

# Phrases qui représentent des trajets (trip)
trip_phrases = [
    'Je pars de {departure} pour aller à {arrival} {time}.',
    'Je vais de {departure} à {arrival} {mode}.',
    'Je quitte {departure} pour me rendre à {arrival} {time}.',
    'Je voyage de {departure} à {arrival} {time}.',
    'Je prends un {mode} de {departure} pour aller à {arrival} {time}.',
    'Je suis à {departure} et je veux aller à {arrival} {time}.',
    'Je me rends de {departure} à {arrival} {mode}.',
    'Je vais à {arrival} en partant de {departure} {time}.',
    'Je suis à {departure} et je veux prendre un vol pour {arrival}.',
    'Je voudrais un billet de train pour {arrival} depuis {departure}.',
    'Après mon départ de {departure}, je voyagerai vers {arrival}.',
    'Mon voyage commencera à {departure} et se terminera à {arrival}.',
    'Je dois quitter {departure} afin de rejoindre {arrival} pour une réunion.',
    'En provenance de {departure}, je me dirigerai vers {arrival} {mode}.',
    'Je me trouve à {departure} et je veux aller à {arrival} {mode}.',
    'Je pars de {departure} pour rejoindre {arrival} {mode}.',
    'Je compte partir de {departure} pour aller à {arrival} {mode}.',
    'Je vais de {departure} à {arrival} en passant par {transit}.',
    'Je voyage de {departure} à {arrival} en passant par {transit}.',
    'Je m\'apprête à quitter {departure} pour rejoindre {arrival}.',
    'Je prends le train de {departure} à {arrival}.',
    'Je vais de {departure} à {arrival} en train, quel est le prix du billet?',
    'Je pars de {departure} pour aller à {arrival} {time} en train.',
    'Je vais à {arrival} en partant de {departure} {time} en train.',
    'Je suis à {departure} et je veux aller à {arrival} en train.',
    'Je prévois un trajet de {departure} à {arrival} via {transits}.',
    'Je cherche les horaires de {mode} de {departure} à {arrival}.',
    'Pouvez-vous suggérer un itinéraire de voyage de {departure} à {arrival} ?',
    'Veuillez me trouver le meilleur itinéraire de {departure} à {arrival}.',
    'J\'ai besoin de rejoindre {arrival} depuis {departure} pour un événement.',
    'Existe-t-il un train direct entre {departure} et {arrival} ?',
    'Je cherche un itinéraire pour aller de {departure} à {arrival} {mode}.',
    'Y a-t-il des trains partant de {departure} vers {arrival} {time}?',
    'Je dois être à {arrival} en partant de {departure}, pouvez-vous m\'aider?',
    'Comment puis-je me rendre de {departure} à {arrival} {time}?',
    'Est-il possible de visiter {transits} en route vers {arrival} depuis {departure}?',
    'Je souhaite voyager de {departure} à {arrival} en passant par {transits}.',
    'Quel est le meilleur chemin pour aller de {departure} à {arrival} via {transits}?',
    'Je planifie un voyage de {departure} à {arrival} avec des escales à {transits}.',
    'Pouvez-vous me donner les options pour aller de {departure} à {arrival} en passant par {transits}?',
    'Je voudrais passer par {transits} lors de mon trajet de {departure} à {arrival}.',
]

# Phrases qui ne représentent pas des trajets (non-trip)
non_trip_phrases = [
    'Quel temps fait-il à {city} aujourd\'hui?',
    'Je suis à {city}, il fait quel temps ?',
    'Le festival à {city} est-il toujours prévu ce week-end ?',
    'Est-ce qu\'il pleut à {city} ?',
    'Quel est le meilleur restaurant à {city} ?',
    'Je vis à {city}.',
    'Je travaille à {city}.',
    'Je suis actuellement à {city}.',
    'L\'école est à {city}.',
    'Le musée de {city} est-il ouvert aujourd\'hui ?',
    'Je veux savoir les actualités de {city}.',
    'Quelles sont les attractions touristiques à {city} ?',
    'Le concert à {city} a-t-il été annulé ?',
    'Je recherche un hôtel à {city}.',
    'Quelle heure est-il à {city} ?',
    'Je voudrais commander une pizza à {city}.',
    'Y a-t-il un hôpital à {city} ?',
    'Je veux en savoir plus sur l\'histoire de {city}.',
    'Quel est le code postal de {city} ?',
    'Montre-moi les images de {city}.',
    'Quels sont les événements culturels à {city} cette semaine?',
    'Je souhaite déménager à {city} l\'année prochaine.',
    'La météo à {city} est-elle favorable pour une visite?',
    'Y a-t-il des alertes de sécurité à {city} actuellement?',
    'Comment est la vie nocturne à {city}?',
    'Je cherche un bon médecin à {city}.',
    'Quelles sont les spécialités culinaires de {city}?',
    'Le parc central de {city} est-il ouvert?',
    'Y a-t-il des feux d\'artifice à {city} ce soir?',
]

# Fonction pour remplacer les mots par des synonymes
def replace_with_synonyms(sentence):
    words = sentence.split()
    new_sentence = []
    for word in words:
        word_lower = word.lower().strip('.,;?!')
        if word_lower in synonyms:
            synonym = random.choice(synonyms[word_lower])
            new_sentence.append(synonym)
        else:
            new_sentence.append(word)
    return ' '.join(new_sentence)

# Fonction pour générer des phrases
def generate_phrases(phrases_list, label, nb_phrases, writer):
    for _ in range(nb_phrases):
        phrase_template = random.choice(phrases_list)
        placeholders = re.findall(r'{(.*?)}', phrase_template)
        data = {}
        transit_cities = 'None'

        if 'departure' in placeholders:
            data['departure'] = random.choice(cities)
        if 'arrival' in placeholders:
            data['arrival'] = random.choice(cities)
            # Éviter que la ville d'arrivée soit la même que celle de départ
            while 'departure' in data and data['arrival'] == data['departure']:
                data['arrival'] = random.choice(cities)
        if 'transits' in placeholders:
            available_cities = [city for city in cities if city not in data.values()]
            # Nombre aléatoire d'escales entre 1 et 3
            n_transits = random.randint(1, 3)
            transit_cities_list = random.sample(available_cities, k=n_transits)
            transit_cities = ', '.join(transit_cities_list)
            data['transits'] = transit_cities
        elif 'transit' in placeholders:
            available_cities = [city for city in cities if city not in data.values()]
            transit_city = random.choice(available_cities)
            transit_cities = transit_city
            data['transit'] = transit_city
        if 'mode' in placeholders:
            data['mode'] = random.choice(modes)
        if 'time' in placeholders:
            data['time'] = random.choice(times)
        if 'city' in placeholders:
            data['city'] = random.choice(cities)

        try:
            sentence = phrase_template.format(**data)
            # Remplacer les mots par des synonymes
            sentence = replace_with_synonyms(sentence)
        except KeyError as e:
            continue

        writer.writerow({
            'Sentence': sentence,
            'Departure City': data.get('departure', 'None'),
            'Arrival City': data.get('arrival', 'None'),
            'Transit Cities': transit_cities,
            'Is Trip': label
        })

# Génération des phrases pour l'entraînement
with open('phrases.csv', 'w', newline='', encoding='utf-8') as csvfile:
    fieldnames = ['Sentence', 'Departure City', 'Arrival City', 'Transit Cities', 'Is Trip']
    writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
    writer.writeheader()

    # Générer des phrases de trajet (Is Trip = 1)
    generate_phrases(trip_phrases, '1', nb_phrases, writer)

    # Générer des phrases non liées aux trajets (Is Trip = 0)
    generate_phrases(non_trip_phrases, '0', nb_phrases, writer)

# Génération des phrases pour le test
with open('test_phrases.csv', 'w', newline='', encoding='utf-8') as csvfile:
    fieldnames = ['Sentence', 'Departure City', 'Arrival City', 'Transit Cities', 'Is Trip']
    writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
    writer.writeheader()

    for _ in range(nb_phrases_test):
        label = random.choice(['0', '1'])
        if label == '1':
            generate_phrases(trip_phrases, label, 1, writer)
        else:
            generate_phrases(non_trip_phrases, label, 1, writer)

print("Génération des phrases terminée !")
