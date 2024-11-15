import csv
import random
import re
import json

#delete file
import os
if os.path.exists("good_phrases.csv"):
    os.remove("good_phrases.csv")
if os.path.exists("wrong_phrases.csv"):
    os.remove("wrong_phrases.csv")
if os.path.exists("test_phrases.csv"):
    os.remove("test_phrases.csv")

#import json
with open('cities.json') as f:
    file = json.load(f)
    cities = []   
    for city in file:
        cities.append(city['COMMUNE'])
# Define lists of cities and modes of transport

international_cities = [
    'New York', 'Tokyo', 'Berlin', 'Amsterdam', 'Bruxelles', 'Genève', 'Lisbonne',
    'Madrid', 'Rome', 'Prague', 'Vienne', 'Copenhague', 'Oslo', 'Stockholm',
    'Helsinki', 'Dublin', 'Athènes', 'Moscou', 'Le Caire', 'Sydney', 'Pékin'
]

valid_modes = ['en train']
invalid_modes = [
    'en trottinette', 'en fusée', 'à dos de chameau', 'en sous-marin', 'en hélicoptère',
    'en montgolfière', 'en moto sous-marine', 'en voiture', 'en vélo', 'en bus', 'en ferry', 'à moto'
]

times = ['demain matin', 'cet après-midi', 'ce soir', 'la semaine prochaine', 'aujourd\'hui']

# Phrase templates with placeholders
phrases = [
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
    'Je suis à {departure} il fait quel temps à {arrival}.',
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
    'Quelle est la météo à {arrival} aujourd\'hui?',
    'Je prends le train de {departure} à {arrival}.',
    'Je vais de {departure} à {arrival} en train, quel est le prix du billet?',
    'Je pars de {departure} pour aller à {arrival} {time} en train.',
    'Je vais à {arrival} en partant de {departure} {time} en train.',
    'Je suis à {departure} et je veux aller à {arrival} en train.',
    'je suis strasbourgeois et je vais à {arrival} {time} en train.',
    'je vais à {arrival} {time} en train depuis {departure}, quel est la météo de {arrival}?',
    'je veux aller à {arrival} {time}',
    'je veux aller à {arrival} {time} en passant par {transit}',
    'je veux rejoindre {arrival} {time}',
    'je veux rejoindre {arrival} {time} en passant par {transit}',
    'en passant par {transit} je veux aller à {arrival} {time}',
    'en passant par {transit} je veux rejoindre {arrival} {time}',
    'en faisant un détour par {transit} je veux aller à {arrival} {time}',
    'en faisant un détour par {transit} je veux rejoindre {arrival} {time}',
    'Je prévois un trajet de {departure} à {arrival} via {transit}.',
    'Je cherche les horaires de {mode} de {departure} à {arrival}.',
    'Pouvez-vous suggérer un itinéraire de voyage de {departure} à {arrival} ?',
    'Veuillez me trouver le meilleur itinéraire de {departure} à {arrival}.',
    'J\'ai besoin de rejoindre {arrival} depuis {departure} pour un événement.',
    'Existe-t-il un train direct entre {departure} et {arrival} ?',
    'je voudrais aller à {departure} puis à {transit} et enfin à {arrival} en passant par {transit}',
    'je voudrais aller à {departure} puis à {transit} et enfin à {arrival} via {transit}',
    'je veux aller à {arrival} en passant par {transit} et {transit} depuis {departure}',
]

wrong_phrases = [
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
    'Je suis à {departure} il fait quel temps à {arrival}.',
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
    'Quelle est la météo à {arrival} aujourd\'hui?',
    'Je prends le train de {departure} à {arrival}.',
    'Je vais de {departure} à {arrival} en train, quel est le prix du billet?',
    'Je pars de {departure} pour aller à {arrival} {time} en train.',
    'Je vais à {arrival} en partant de {departure} {time} en train.',
    'Je suis à {departure} et je veux aller à {arrival} en train.',
    'je suis strasbourgeois et je vais à {arrival} {time} en train.',
    'je vais à {arrival} {time} en train depuis {departure}, quel est la météo de {arrival}?',
    'je vais à {arrival} {time} en train depuis {departure}, quel est la météo de berne?',
    'quel temps fait-il à {arrival} ?',
    'est-ce qu\'il pleut à {arrival} ?',
    'le festival de musique de {arrival} est-il annulé ?',
    'je suis à {departure}',
    'je vis à {departure}',
    'Je prévois un trajet de {departure} à {arrival} via {transit}.',
    'Je cherche les horaires de {mode} de {departure} à {arrival}.',
    'Pouvez-vous suggérer un itinéraire de voyage de {departure} à {arrival} ?',
    'Veuillez me trouver le meilleur itinéraire de {departure} à {arrival}.',
    'J\'ai besoin de rejoindre {arrival} depuis {departure} pour un événement.',
    'Existe-t-il un train direct entre {departure} et {arrival} ?',
    'Le festival à {arrival} est-il toujours prévu ce week-end ?',
    'Y a-t-il des vols disponibles de {departure} à {arrival} {time} ?',
    'Quel temps fait-il à {arrival} aujourd\'hui ?',
    'Pourriez-vous vérifier les prévisions météo pour {arrival} ?'
]

test_phrases = [
    "Je souhaite voyager de {departure} à {arrival} {time}."
    "Pouvez-vous me dire comment me rendre à {arrival} depuis {departure} ?",
    "Quelle est la façon la plus rapide d'atteindre {arrival} en partant de {departure} ?",
    "Je prévois un trajet de {departure} à {arrival} via {transit}.",
    "Y a-t-il des vols disponibles de {departure} à {arrival} {time} ?",
    "Je veux réserver un billet de {departure} à {arrival} en utilisant le {mode}.",
    "Quel temps fait-il à {arrival} aujourd'hui ?",
    "Est-ce qu'il pleut actuellement à {arrival} ?",
    "Quel est le coût pour voyager en {mode} de {departure} à {arrival} ?",
    "Je suis actuellement à {departure}; comment puis-je aller à {arrival} ?",
    "Veuillez me trouver le meilleur itinéraire de {departure} à {arrival}.",
    "Existe-t-il un train direct entre {departure} et {arrival} ?",
    "Je prévois de quitter {departure} et d'arriver à {arrival} en {mode}.",
    "Pourriez-vous vérifier les prévisions météo pour {arrival} ?",
    "J'ai besoin de rejoindre {arrival} depuis {departure} pour un événement.",
    "Quelle est la distance entre {departure} et {arrival} ?",
    "Y a-t-il des retards sur les routes de {departure} à {arrival} ?",
    "Je cherche les horaires de {mode} de {departure} à {arrival}.",
    "Pouvez-vous suggérer un itinéraire de voyage de {departure} à {arrival} ?",
    "Le festival à {arrival} est-il toujours prévu ce week-end ?"
    ]


# Open the CSV file for writing
with open('good_phrases.csv', 'w', newline='', encoding='utf-8') as csvfile:
    fieldnames = ['Sentence', 'Departure City', 'Arrival City', 'transit cities', 'Trip Validity']
    writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
    writer.writeheader()

    # Generate 50 phrases
    for _ in range(7500):
        phrase_template = random.choice(phrases)
        departure_city = random.choice(cities)

        # Find placeholders in the phrase template
        placeholders = re.findall(r'{(.*?)}', phrase_template)
        data = {}

        # Assign departure city
        if 'departure' in placeholders:
            data['departure'] = departure_city
        else:
            data['departure'] = 'None'

        # Valid trip: Use French cities and valid modes
        if 'arrival' in placeholders:
            arrival_city = random.choice(cities)
        else:
            arrival_city = 'None'

        while arrival_city == departure_city:
            arrival_city = random.choice(cities)
        data['arrival'] = arrival_city
        trip_validity = '1'

        if 'mode' in placeholders:
            data['mode'] = random.choice(valid_modes)
        if 'time' in placeholders:
            data['time'] = random.choice(times)
        n_transits = phrase_template.count('{transit}')
        if n_transits > 0:
            available_cities = [city for city in cities if city not in [departure_city, arrival_city]]
            transit_cities = random.choices(available_cities, k=n_transits)
            while arrival_city in transit_cities or departure_city in transit_cities:
                transit_cities = random.choices(available_cities, k=n_transits)
            for transit_city in transit_cities:
                phrase_template = phrase_template.replace('{transit}', transit_city, 1)
        else:
            transit_cities = 'None'

        arrival_city_output = arrival_city
        # Build the sentence
        try:
            sentence = phrase_template.format(**data)
        except KeyError:
            # If placeholders are missing, skip this iteration
            continue

        writer.writerow({
            'Sentence': sentence,
            'Departure City': departure_city,
            'Arrival City': arrival_city_output,
            'transit cities': transit_cities,
            'Trip Validity': trip_validity
        })

with open('wrong_phrases.csv', 'w', newline='', encoding='utf-8') as csvfile:
    fieldnames = ['Sentence', 'Departure City', 'Arrival City', 'transit cities', 'Trip Validity']
    writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
    writer.writeheader()
    # Invalid trip: Use international cities or invalid modes
    for _ in range(7500):
        phrase_template = random.choice(wrong_phrases)
        # Find placeholders in the phrase template
        placeholders = re.findall(r'{(.*?)}', phrase_template)
        data = {}

        if 'departure' in placeholders:
            departure_city = random.choice(cities + international_cities)
            data['departure'] = departure_city
        else:
            departure_city = 'None'

        if 'arrival' in placeholders:
            arrival_city = random.choice(international_cities + ['Destination inconnue', 'None'])
            data['arrival'] = arrival_city
        else:
            arrival_city = 'None'

        trip_validity = '0'

        if 'mode' in placeholders:
            data['mode'] = random.choice(invalid_modes + valid_modes)
            if data['mode'] in invalid_modes:
                while arrival_city == departure_city:
                    arrival_city = random.choice(international_cities + ['Destination inconnue', 'None'] + cities)
                data['arrival'] = arrival_city
        if 'time' in placeholders:
            data['time'] = random.choice(times)
        n_transits = phrase_template.count('{transit}')
        if n_transits > 0:
            available_cities = [city for city in cities + international_cities if city not in [departure_city, arrival_city]]
            transit_cities = random.choices(available_cities, k=n_transits)
            while arrival_city in transit_cities or departure_city in transit_cities:
                transit_cities = random.choices(available_cities, k=n_transits)
            for transit_city in transit_cities:
                phrase_template = phrase_template.replace('{transit}', transit_city, 1)
        else:
            transit_cities = 'None'

        if arrival_city in ['Destination inconnue', 'None']:
            arrival_city_output = 'None'
        else:
            arrival_city_output = arrival_city

        # Build the sentence
        try:
            sentence = phrase_template.format(**data)
        except KeyError as e:
            # If placeholders are missing, skip this iteration
            print(f"Missing key {e} in data for phrase: {phrase_template}")
            continue

        # Write the row to the CSV file
        writer.writerow({
            'Sentence': sentence,
            'Departure City': departure_city,
            'Arrival City': arrival_city_output,
            'transit cities': transit_cities,
            'Trip Validity': trip_validity
        })

with open('test_phrases.csv', 'w', newline='', encoding='utf-8') as csvfile:
    fieldnames = ['Sentence', 'Departure City', 'Arrival City', 'transit cities', 'Trip Validity']
    writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
    writer.writeheader()
    for _ in range(3000):
        choice = random.choice([0, 1])
        data = {}
        if choice == 0:
            # Generate invalid trip
            phrase_template = random.choice(wrong_phrases)
            placeholders = re.findall(r'{(.*?)}', phrase_template)

            if 'departure' in placeholders:
                departure_city = random.choice(cities + international_cities)
                data['departure'] = departure_city
            else:
                departure_city = 'None'

            if 'arrival' in placeholders:
                arrival_city = random.choice(international_cities + ['Destination inconnue', 'None'])
                data['arrival'] = arrival_city
            else:
                arrival_city = 'None'

            trip_validity = '0'

            if 'mode' in placeholders:
                data['mode'] = random.choice(invalid_modes + valid_modes)
                if data['mode'] in invalid_modes and arrival_city == departure_city:
                    while arrival_city == departure_city:
                        arrival_city = random.choice(international_cities + ['Destination inconnue', 'None'] + cities)
                    data['arrival'] = arrival_city
            if 'time' in placeholders:
                data['time'] = random.choice(times)
            n_transits = phrase_template.count('{transit}')
            if n_transits > 0:
                available_cities = [city for city in cities if city not in [departure_city, arrival_city]]
                transit_cities = random.choices(available_cities, k=n_transits)
                while arrival_city in transit_cities or departure_city in transit_cities:
                    transit_cities = random.choices(available_cities, k=n_transits)
                for transit_city in transit_cities:
                    phrase_template = phrase_template.replace('{transit}', transit_city, 1)

        elif choice == 1:
            # Generate valid trip
            phrase_template = random.choice(phrases)
            placeholders = re.findall(r'{(.*?)}', phrase_template)

            if 'departure' in placeholders:
                departure_city = random.choice(cities)
                data['departure'] = departure_city
            else:
                departure_city = 'None'

            if 'arrival' in placeholders:
                arrival_city = random.choice(cities)
                while arrival_city == departure_city:
                    arrival_city = random.choice(cities)
                data['arrival'] = arrival_city
            else:
                arrival_city = 'None'

            trip_validity = '1'

            if 'mode' in placeholders:
                data['mode'] = random.choice(valid_modes)
            if 'time' in placeholders:
                data['time'] = random.choice(times)
            n_transits = phrase_template.count('{transit}')
            if n_transits > 0:
                available_cities = [city for city in cities + international_cities if city not in [departure_city, arrival_city]]
                transit_cities = random.choices(available_cities, k=n_transits)
                while arrival_city in transit_cities or departure_city in transit_cities:
                    transit_cities = random.choices(available_cities, k=n_transits)
                for transit_city in transit_cities:
                    phrase_template = phrase_template.replace('{transit}', transit_city, 1)
            else:
                transit_cities = 'None'
        else:
            continue  # Should not happen

        # Build the sentence
        try:
            sentence = phrase_template.format(**data)
        except KeyError as e:
            print(f"Missing key {e} in data for phrase: {phrase_template}")
            continue

        # Write the row to the CSV file
        writer.writerow({
            'Sentence': sentence,
            'Departure City': data.get('departure', 'None'),
            'Arrival City': data.get('arrival', 'None'),
            'transit cities': transit_cities,
            'Trip Validity': trip_validity
        })


print("Done generating phrases!")