import csv
import random
import re
import json
import os

nb_phrases = 20000
nb_phrases_test = 2500

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

# Définir un dictionnaire de synonymes étendu pour diversifier les phrases
synonyms = {
    'aller': ['se rendre', 'partir pour', 'visiter', 'rejoindre'],
    'partir': ['quitter', 'démarrer de', 's\'éloigner de', 'se diriger depuis'],
    'voyager': ['se déplacer', 'faire un voyage', 'parcourir', 'se promener'],
    'prendre': ['emprunter', 'monter dans', 'utiliser', 'attraper'],
    'train': ['TGV', 'TER', 'wagon', 'locomotive'],
    'avion': ['vol', 'appareil', 'aéronef', 'jet'],
    'voiture': ['automobile', 'véhicule', 'bagnole', 'auto'],
    'bus': ['autocar', 'car', 'minibus', 'navette'],
    'bateau': ['navire', 'vaisseau', 'ferry', 'croisière'],
    'aujourd\'hui': ['ce jour', 'en ce moment', 'actuellement'],
    'demain matin': ['le matin prochain', 'à l\'aube', 'demain à l\'aube'],
    'cet après-midi': ['cette après-midi', 'dans l\'après-midi', 'aujourd\'hui après-midi'],
    'je': ['moi', 'pour ma part', 'personnellement'],
    'vous': ['tu', 'te', 'toi'],
    'réunion': ['rendez-vous', 'entretien', 'meeting', 'séance'],
    'itinéraire': ['route', 'trajet', 'chemin', 'parcours'],
    'trajet': ['voyage', 'parcours', 'déplacement', 'périple'],
    'besoin': ['nécessité', 'envie', 'souhait', 'désir'],
    'meilleur': ['optimal', 'idéal', 'parfait', 'plus approprié'],
    'horaires': ['heures', 'planning', 'agenda', 'emploi du temps'],
    'pouvez-vous': ['peux-tu', 'est-il possible de', 'serait-il possible de'],
    'suggestion': ['proposition', 'idée', 'conseil', 'recommandation'],
    'météo': ['temps', 'climat', 'conditions météorologiques'],
    'restaurant': ['bistrot', 'brasserie', 'cantine', 'établissement'],
    'hôtel': ['auberge', 'logement', 'hébergement', 'pension'],
    'musée': ['galerie', 'exposition', 'centre culturel'],
    'université': ['faculté', 'école supérieure', 'établissement d\'enseignement'],
    'événement': ['manifestation', 'activité', 'fête', 'occasion'],
    'festival': ['carnaval', 'célébration', 'foire', 'kermesse'],
    'visiter': ['découvrir', 'explorer', 'parcourir', 'aller voir'],
    'réserver': ['booker', 'acheter', 'obtenir', 'procéder à la réservation'],
    'vol': ['avion', 'liaison aérienne', 'trajet aérien'],
    'destination': ['lieu', 'endroit', 'localisation', 'point d\'arrivée'],
    'heure': ['moment', 'temps', 'horaire'],
    'bagage': ['valise', 'sac', 'bagagerie'],
    'billet': ['ticket', 'titre de transport', 'pass'],
    'station': ['gare', 'arrêt', 'halte', 'terminus'],
    'route': ['chemin', 'voie', 'itinéraire', 'parcours'],
    'vacances': ['congés', 'repos', 'période de détente'],
    'marché': ['bazar', 'foire', 'place de marché'],
    'centre-ville': ['cœur de ville', 'hyper-centre', 'centre urbain'],
    'bus': ['autocar', 'car', 'navette', 'minibus'],
    'bonjour': ['salut', 'coucou', 'hello', 'bonsoir'],
    'aéroport': ['terminal', 'aérodrome', 'zone aéroportuaire'],
    'merci': ['gracias', 'thanks', 'merci beaucoup', 'je vous remercie'],
}

# Phrases qui représentent des trajets (trip)
trip_phrases_all = [
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
    'Je vais de {departure} à {arrival} en passant par {transits}.',
    'Je voyage de {departure} à {arrival} en passant par {transits}.',
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
non_trip_phrases_all = [
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
    'Le festival de {city} est-il annulé ?',
    'L\'exposition de {city} est-elle annulée ?',
    'L\'événement de {city} est-il annulé ?',
    'Quels restaurants sont ouverts à {city} ?',
    'Quels restaurants sont fermés à {city} ?',
    'Quels restaurants sont ouverts à {city} aujourd\'hui ?',
    'Quels restaurants sont fermés à {city} aujourd\'hui ?',
    'Quels sont les meilleurs restaurants à {city} et {city} ?',
    'Quelle est la météo à {city} et à {city}?',
    'Je préfère le climat de {city} à celui de {city}.',
    'Les équipes de football de {city} et {city} jouent ce soir.',
    'Les universités de {city} sont parmi les meilleures du pays.',
    'Je suis intéressé par le marché immobilier à {city}.',
    'Les films tournés à {city} ont remporté de nombreux prix.',
    'Je veux savoir quelles sont les options de carrière à {city}.',
    'Les systèmes de santé à {city} sont-ils efficaces ?',
    'Je souhaite connaître les taux de criminalité à {city}.',
    'Les écoles à {city} sont-elles réputées ?',
    'La qualité de vie à {city} est-elle bonne ?',
    'Les parcs technologiques de {city} sont en plein essor.',
    'Je me demande si {city} est une bonne ville pour élever des enfants.',
    'Les festivals annuels de {city} attirent des milliers de visiteurs.',
    'Les opportunités d\'affaires à {city} sont-elles nombreuses ?',
    'Je suis curieux de la scène musicale à {city}.',
    'Les programmes culturels à {city} sont diversifiés.',
    'Je cherche des informations sur le climat économique de {city}.',
    'Les transports publics à {city} sont-ils fiables ?',
    'Je voudrais connaître les horaires des bibliothèques à {city}.',
    'Les cafés à {city} offrent-ils du Wi-Fi gratuit ?',
    'Les zones vertes à {city} sont-elles bien entretenues ?',
    'Les événements sportifs à {city} sont-ils accessibles au public ?',
    'Je veux en savoir plus sur les initiatives écologiques à {city}.',
    'Les marchés fermiers de {city} proposent-ils des produits locaux ?',
    'Les services d\'urgence à {city} sont-ils rapides ?',
    'La vie nocturne à {city} est-elle active en semaine ?',
    'Les plages de {city} sont-elles propres et sécurisées ?',
    'Je souhaite visiter les monuments historiques de {city}.',
    'Les festivals culinaires à {city} sont réputés dans le monde entier.',
    'Les infrastructures de {city} sont-elles adaptées aux personnes handicapées ?',
    'Je cherche des cours de langue à {city}.',
    'Les centres de recherche à {city} sont-ils reconnus ?',
    'La biodiversité autour de {city} est-elle riche ?',
    'Les quartiers de {city} ont-ils chacun une identité propre ?',
    'Je suis intéressé par les légendes locales de {city}.',
    'Les salons professionnels à {city} sont-ils importants pour mon secteur ?',
    'Les taux de pollution sonore à {city} sont-ils élevés ?',
    'Je me demande comment est le réseau internet à {city}.',
    'Les festivals de films à {city} présentent-ils des œuvres internationales ?',
    'Les écoles d\'art à {city} sont-elles réputées ?',
    'Je souhaite connaître les traditions locales de {city}.',
    'Les jardins publics à {city} sont-ils fréquentés ?',
    'Les offres d\'emploi à {city} sont-elles abondantes ?',
    'Les zones commerciales de {city} sont-elles animées ?',
    'Je veux savoir si {city} a un bon système éducatif.',
    'Les transports en commun de {city} fonctionnent-ils la nuit ?',
    'Les événements scientifiques à {city} sont-ils ouverts au public ?',
    'Les festivals de littérature à {city} attirent-ils de grands auteurs ?',
    'Je souhaite m\'informer sur les programmes sportifs à {city}.',
    'Les conditions de travail à {city} sont-elles favorables ?',
    'Les taux d\'imposition à {city} sont-ils élevés ?',
    'Les services de santé mentale à {city} sont-ils accessibles ?',
    'Je voudrais connaître les heures d\'ouverture des musées à {city}.',
    'Les expositions d\'art à {city} sont-elles régulières ?',
    'Les infrastructures pour le cyclisme à {city} sont-elles développées ?',
    'Les cafés littéraires de {city} sont-ils actifs ?',
    'Je cherche des recommandations pour des librairies à {city}.',
    'Les espaces de coworking à {city} sont-ils nombreux ?',
    'Les événements technologiques à {city} sont-ils innovants ?',
    'Je veux savoir si {city} est bien connectée par le train.',
    'Les spécialités locales de {city} sont-elles appréciées ?',
    'Les cinémas de {city} projettent-ils des films en version originale ?',
    'Je souhaite connaître les jours de marché à {city}.',
    'Les services de livraison à {city} sont-ils rapides ?',
    'Les salles de concert à {city} accueillent-elles des artistes internationaux ?',
    'Les clubs de sport à {city} offrent-ils des activités pour enfants ?',
    'Je me demande si {city} est une ville touristique.',
    'Les monuments de {city} sont-ils accessibles aux personnes à mobilité réduite ?',
    'Les options de formation professionnelle à {city} sont-elles variées ?',
    'Les festivals d\'art contemporain à {city} sont-ils reconnus ?',
    'Les zones rurales autour de {city} sont-elles développées ?',
    'Les communautés expatriées à {city} sont-elles importantes ?',
    'Je suis intéressé par le développement durable à {city}.',
    'Les systèmes de recyclage à {city} sont-ils efficaces ?',
    'Les restaurants de {city} proposent-ils des options végétaliennes ?',
    'Les centres commerciaux de {city} sont-ils ouverts le dimanche ?',
    'Je voudrais savoir si {city} est une ville chère pour les étudiants.',
    'Les quartiers de {city} sont-ils sûrs la nuit ?',
    'Les festivals de jazz à {city} sont-ils populaires ?',
    'Je cherche des cours de yoga à {city}.',
    'Les salons de thé à {city} ont-ils une bonne ambiance ?',
    'Les transports maritimes à {city} sont-ils utilisés ?',
    'Je souhaite connaître le calendrier des vacances scolaires à {city}.',
    'Les musées interactifs à {city} sont-ils adaptés aux enfants ?',
    'Les foires artisanales à {city} ont-elles lieu toute l\'année ?',
    'Les options de bénévolat à {city} sont-elles nombreuses ?',
    'Les bibliothèques de {city} proposent-elles des activités culturelles ?',
    'Je veux savoir si {city} a un opéra célèbre.',
    'Les événements caritatifs à {city} soutiennent-ils des causes locales ?',
    'Les festivals de rue à {city} sont-ils animés ?',
    'Les parcs à thème à {city} valent-ils la peine ?',
    'Je suis curieux de la scène comique à {city}.',
    'Les studios de danse à {city} offrent-ils des cours pour débutants ?',
    'Les centres de bien-être à {city} sont-ils réputés ?',
    'Les boutiques d\'artisanat à {city} vendent-elles des produits uniques ?',
    'Je cherche des recommandations pour des visites guidées à {city}.',
    'Les événements culturels à {city} sont-ils accessibles financièrement ?',
    'Les festivals de lumière à {city} sont-ils impressionnants ?',
    'Les transports urbains à {city} sont-ils écologiques ?',
    'Je souhaite connaître les réglementations locales de {city}.',
    'Les conditions météorologiques à {city} sont-elles extrêmes ?',
    'Les galeries d\'art à {city} soutiennent-elles les artistes locaux ?',
    'Les options de restauration à {city} sont-elles diversifiées ?',
    'Les programmes éducatifs à {city} sont-ils innovants ?',
    'Je veux en savoir plus sur les espaces verts à {city}.',
    'Les services de sécurité à {city} sont-ils efficaces ?',
    'Les festivals de bière à {city} sont-ils populaires ?',
    'Les bibliothèques de {city} offrent-elles des ressources numériques ?',
    'Je suis intéressé par les ateliers créatifs à {city}.',
    'Les places publiques à {city} sont-elles animées ?',
    'Les traditions culinaires de {city} sont-elles anciennes ?',
    'Les services pour les seniors à {city} sont-ils développés ?',
    'Je souhaite connaître les options de transport depuis l\'aéroport de {city}.',
    'Les zones industrielles à {city} sont-elles en croissance ?',
    'Les centres sportifs de {city} proposent-ils des activités aquatiques ?',
    'Les parcs animaliers près de {city} sont-ils bien notés ?',
    'Je me demande si {city} organise des festivals médiévaux.',
    'Les sentiers de randonnée autour de {city} sont-ils balisés ?',
    'Les salles de cinéma de {city} projettent-elles des films d\'auteur ?',
    'Les infrastructures routières à {city} sont-elles en bon état ?',
    'Je cherche des recommandations pour des spectacles à {city}.',
    'Les services de taxi à {city} sont-ils fiables ?',
    'Les zones piétonnes à {city} sont-elles agréables pour se promener ?',
    'Les compétitions sportives à {city} sont-elles accessibles gratuitement ?',
    'Je souhaite connaître les heures de pointe à {city}.',
    'Les services de livraison de repas à {city} sont-ils variés ?',
    'Les marchés aux puces à {city} sont-ils intéressants ?',
    'Les festivals de théâtre de rue à {city} attirent-ils du monde ?',
    'Les traditions folkloriques de {city} sont-elles préservées ?',
    'Je suis curieux des légendes urbaines de {city}.',
    'Les options de colocation à {city} sont-elles abordables ?',
    'Les quartiers artistiques de {city} sont-ils dynamiques ?',
    'Les services bancaires à {city} sont-ils modernes ?',
    'Je veux savoir si {city} a une bonne connectivité mobile.',
    'Les marchés de Noël à {city} sont-ils populaires ?',
    'Les événements d\'entreprise à {city} sont-ils fréquents ?',
    'Les options de stage à {city} sont-elles intéressantes pour les étudiants ?',
    'Les piscines publiques à {city} sont-elles bien entretenues ?',
    'Je souhaite connaître les clubs de lecture à {city}.',
    'Les stations de ski près de {city} sont-elles ouvertes ?',
    'Les cours de cuisine à {city} sont-ils réputés ?',
    'Les services postaux à {city} sont-ils fiables ?',
    'Les événements gastronomiques à {city} sont-ils reconnus ?',
    'Je suis intéressé par les formations en ligne proposées à {city}.',
    'Les festivals de science-fiction à {city} attirent-ils beaucoup de fans ?',
    'Les cafés à thème à {city} sont-ils nombreux ?',
    'Les zones Wi-Fi gratuites à {city} sont-elles répandues ?',
    'Les services de garde d\'enfants à {city} sont-ils abordables ?',
    'Je veux savoir si {city} a des jardins zoologiques.',
    'Les stations de radio locales à {city} sont-elles populaires ?',
    'Les services d\'urgence à {city} sont-ils bien coordonnés ?',
    'Les activités de plein air à {city} sont-elles nombreuses ?',
    'Les événements pour célibataires à {city} sont-ils fréquents ?',
    'Je cherche des groupes de randonnée à {city}.',
    'Les options de transport écologique à {city} sont-elles encouragées ?',
    'Les festivals de photographie à {city} sont-ils reconnus ?',
    'Les services de réparation à {city} sont-ils efficaces ?',
    'Je souhaite connaître les traditions sportives de {city}.',
    'Les marchés nocturnes à {city} sont-ils animés ?',
    'Les services de streaming à {city} offrent-ils un bon débit ?',
    'Les programmes d\'échange culturel à {city} sont-ils accessibles ?',
    'Je suis curieux de la faune locale autour de {city}.',
    'Les centres d\'innovation à {city} sont-ils soutenus par le gouvernement ?',
    'Les événements de mode à {city} sont-ils influents ?',
    'Les programmes de recyclage à {city} sont-ils bien implantés ?',
    'Je veux en savoir plus sur les programmes sociaux à {city}.',
    'Les festivals de musique électronique à {city} attirent-ils des DJ internationaux ?',
    'Les options de restauration rapide à {city} sont-elles variées ?',
    'Les centres d\'appels à {city} recrutent-ils actuellement ?',
    'Je cherche des cours d\'artisanat à {city}.',
    'Les services de nettoyage à {city} sont-ils abordables ?',
    'Les programmes pour les jeunes à {city} sont-ils actifs ?',
    'Les salons de coiffure à {city} proposent-ils des styles modernes ?',
    'Je souhaite connaître les horaires des transports en commun à {city} pendant les jours fériés.',
    'Quel est le code postal de {city} ?',
    'Je souhaite connaître les événements culturels à {city}.',
    'Les universités de {city} sont-elles réputées ?',
    'Quelles sont les attractions touristiques à {city} ?',
    'Y a-t-il un hôpital à {city} ?',
    'Je veux savoir les actualités de {city}.',
    'je vais niquer ta mère à {city}',
    'je vais niquer tous le monde de {city}',
    'je vais niquer tous le monde de {city} à {city}'
]

# Mélanger les templates et les diviser
random.shuffle(trip_phrases_all)
random.shuffle(non_trip_phrases_all)

split_ratio = 0.8  # Utiliser 80% des templates pour l'entraînement, 20% pour le test

trip_phrases_train = trip_phrases_all[:int(len(trip_phrases_all) * split_ratio)]
trip_phrases_test = trip_phrases_all[int(len(trip_phrases_all) * split_ratio):]

non_trip_phrases_train = non_trip_phrases_all[:int(len(non_trip_phrases_all) * split_ratio)]
non_trip_phrases_test = non_trip_phrases_all[int(len(non_trip_phrases_all) * split_ratio):]


# Fonction pour remplacer les mots par des synonymes
def replace_with_synonyms(sentence):
    words = sentence.split()
    new_sentence = []
    for word in words:
        word_clean = word.lower().strip('.,;?!\'"')
        synonym = synonyms.get(word_clean, [word])
        new_word = random.choice(synonym) if word_clean in synonyms else word
        # Préserver la ponctuation attachée au mot
        punctuation = ''.join([char for char in word if char in '.,;?!\'"'])
        new_sentence.append(new_word + punctuation)
    return ' '.join(new_sentence)

# Fonction pour générer des phrases
def generate_phrases(phrases_list, label, nb_phrases, existing_sentences):
    generated_data = []
    attempts = 0
    max_attempts = nb_phrases * 10  # Pour éviter une boucle infinie
    while len(generated_data) < nb_phrases and attempts < max_attempts:
        attempts += 1
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

        if sentence not in existing_sentences:
            existing_sentences.add(sentence)
            generated_data.append({
                'Sentence': sentence,
                'Departure City': data.get('departure', 'None'),
                'Arrival City': data.get('arrival', 'None'),
                'Transit Cities': transit_cities,
                'Is Trip': label
            })

    return generated_data

# Génération des phrases pour l'entraînement
train_existing_sentences = set()
with open('phrases.csv', 'w', newline='', encoding='utf-8') as csvfile:
    fieldnames = ['Sentence', 'Departure City', 'Arrival City', 'Transit Cities', 'Is Trip']
    writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
    writer.writeheader()

    # Générer des phrases de trajet (Is Trip = 1)
    trip_phrases_train_data = generate_phrases(trip_phrases_train, '1', nb_phrases, train_existing_sentences)
    for data in trip_phrases_train_data:
        writer.writerow(data)

    # Générer des phrases non liées aux trajets (Is Trip = 0)
    non_trip_phrases_train_data = generate_phrases(non_trip_phrases_train, '0', nb_phrases, train_existing_sentences)
    for data in non_trip_phrases_train_data:
        writer.writerow(data)

# Génération des phrases pour le test
test_existing_sentences = set()
with open('test_phrases.csv', 'w', newline='', encoding='utf-8') as csvfile:
    fieldnames = ['Sentence', 'Departure City', 'Arrival City', 'Transit Cities', 'Is Trip']
    writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
    writer.writeheader()

    # Générer des phrases de test sans chevauchement
    total_test_phrases = nb_phrases_test
    nb_test_phrases_per_label = total_test_phrases // 2

    # Générer des phrases de trajet pour le test
    trip_phrases_test_data = generate_phrases(trip_phrases_test, '1', nb_test_phrases_per_label, train_existing_sentences)
    for data in trip_phrases_test_data:
        writer.writerow(data)
        test_existing_sentences.add(data['Sentence'])

    # Générer des phrases non liées aux trajets pour le test
    non_trip_phrases_test_data = generate_phrases(non_trip_phrases_test, '0', nb_test_phrases_per_label, train_existing_sentences)
    for data in non_trip_phrases_test_data:
        writer.writerow(data)
        test_existing_sentences.add(data['Sentence'])

print("Génération des phrases terminée !")