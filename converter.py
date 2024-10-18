import spacy
import re
import csv
import io

# Charger le modèle de langue français de Spacy
nlp = spacy.load("fr_core_news_sm")

# Liste de moyens de transport invalides pour la validation du voyage
invalid_transports = [
    "bus", "hélicoptère", "vol spatial", "moto sous-marine", "vélo", "trottinette", 
    "montgolfière", "fusée", "chameau", "sous-marin", "patins à roulettes"
]

expressions_depart = [
    "je pars de", "je quitte", "depuis", "en partant de", 
    "je viens de", "je suis parti de", "je suis à" , "je suis actuellement"
    "en provenance de", "je démarre de", "je débute à",
    "je me trouve à", "je commence depuis", "je sors de",
    "à l'origine de", "je prends la route de", "mon point de départ est",
    "je débute ma route à", "en quittant", "je m'élance depuis",
    "j'entame mon trajet à", "je trace ma route à partir de",
    "je fais mes premiers pas depuis", "je mets les voiles de",
    "je décolle depuis", "je démarre mon chemin à", "je commence mon voyage à",
    "je prends le départ à", "je débute à l'endroit de", "je me lance de",
    "je quitte le point de", "je suis en départ de", "mon périple commence à","je suis actuellement à","je suis à", "je suis actuellement à" 
]

expressions_arrivee = [
    "je vais à", "je me rends à", "je souhaite rejoindre", "je veux rejoindre", 
    "je veux aller à", "en direction de", "vers", "pour rejoindre", "pour aller à",
    "je vise", "je me dirige vers", "je prends la direction de", "j'arrive à",
    "j'atteins", "je fais route vers", "mon but est d'atteindre", "je souhaite arriver à",
    "je compte arriver à", "je prévois d'atteindre", "mon objectif est d'aller à",
    "je me rapproche de", "je finis mon trajet à", "mon chemin me conduit à", 
    "je termine à", "je vais en direction de", "je rejoins", "je poursuis jusqu'à",
    "je cherche à atteindre", "je compte rejoindre", "je vise comme destination",
    "je projette d'arriver à", "je progresse vers","je veux partir pour",
    "j'aimerais rejoindre","je souhaite aller à" ,"pour", "en route pour","terminera à",
]

def extraire_lieux(phrase):
    doc = nlp(phrase)
    lieux = [ent for ent in doc.ents if ent.label_ == "LOC"]
    lieu_depart = None
    lieu_arrivee = None
    lieux_intermediaires = []
    movement_verb_found = False  # Initialiser le drapeau pour les verbes de mouvement

    print(lieux)
    # Liste des verbes de mouvement
    movement_verbs = [
        "aller", "partir", "quitter", "rejoindre", "venir",
        "arriver", "voyager", "prendre", "rendre", "se déplacer", "marcher", "courir"
    ]

    # Phrases indiquant des étapes intermédiaires
    intermediate_phrases = ["en passant par", "via", "par", "en route par"]

    # Fonction pour vérifier si une séquence de tokens correspond à une phrase dans intermediate_phrases
    def match_intermediate_phrase(start_token):
        phrase_text = " ".join([t.text for t in doc[start_token.i:start_token.i+3]])  # Prendre jusqu'à 3 tokens
        for phrase in intermediate_phrases:
            if phrase in phrase_text.lower():
                return phrase
        return None

    # Première étape : gestion des prépositions pour le départ, l'arrivée et les intermédiaires
    for token in doc:
        # Gérer les prépositions de départ
        if token.text.lower() in ["de", "depuis", "à partir de"]:
            next_token = token.nbor(1)
            if next_token.ent_type_ == "LOC":
                lieu_depart = next_token.text

        # Gérer les prépositions d'arrivée, y compris "pour"
        elif token.text.lower() in ["à", "vers", "pour", "en direction de"]:
            next_token = token.nbor(1)
            if next_token.ent_type_ == "LOC":
                lieu_arrivee = next_token.text

        # Vérifier s'il y a une phrase intermédiaire comme "en passant par", "via", etc.
        matched_phrase = match_intermediate_phrase(token)
        if matched_phrase:
            next_token = token.nbor(len(matched_phrase.split()))  # Avancer après la phrase correspondante
            if next_token.ent_type_ == "LOC" and next_token.text not in lieux_intermediaires:
                lieux_intermediaires.append(next_token.text)

    print(lieu_depart, lieu_arrivee, lieux_intermediaires)
    # Deuxième étape : gestion des verbes de mouvement et des prépositions
    for token in doc:
        if token.lemma_ in movement_verbs:
            movement_verb_found = True  # Un verbe de mouvement a été trouvé
            for child in token.children:
                if child.dep_ == "prep":
                    # Gérer les prépositions de départ
                    if child.text.lower() in ["de", "depuis", "à partir de"]:
                        for obj in child.children:
                            if obj.ent_type_ == "LOC":
                                lieu_depart = obj.text
                    # Gérer les prépositions d'arrivée
                    elif child.text.lower() in ["à", "vers", "pour", "en direction de"]:
                        for obj in child.children:
                            if obj.ent_type_ == "LOC":
                                lieu_arrivee = obj.text
                    # Gérer les étapes intermédiaires
                    elif child.text.lower() in ["par", "via"]:
                        for obj in child.children:
                            if obj.ent_type_ == "LOC" and obj.text not in lieux_intermediaires:
                                lieux_intermediaires.append(obj.text)

    # Vérifier que les lieux de départ et d'arrivée ne sont pas dans les lieux intermédiaires
    if lieu_depart in lieux_intermediaires:
        lieux_intermediaires.remove(lieu_depart)
    if lieu_arrivee in lieux_intermediaires:
        lieux_intermediaires.remove(lieu_arrivee)

    # Si le lieu de départ ou d'arrivée n'est pas défini, utiliser les entités de lieu disponibles
    if not lieu_depart or not lieu_arrivee:
        if lieux:
            if not lieu_depart:
                lieu_depart = lieux[0].text
            if len(lieux) > 1 and not lieu_arrivee:
                lieu_arrivee = lieux[1].text
            if len(lieux) > 2:
                for loc in lieux[2:]:
                    if loc.text not in lieux_intermediaires:
                        lieux_intermediaires.append(loc.text)


    return lieu_depart, lieu_arrivee, lieux_intermediaires


# Fonction pour valider le voyage en fonction du mode de transport et des verbes de mouvement
def est_voyage_valide(phrase):
    # Liste des verbes de mouvement (formes de base)
    movement_verbs = [
        "aller", "partir", "quitter", "rejoindre", "venir",
        "arriver", "voyager", "prendre", "rendre", "se déplacer", "marcher", "courir"
    ]
    
    # Liste des modes de transport invalides
    invalid_transports = ["hélicoptère", "vaisseau spatial"]  # Exemples à adapter
    
    # Analyser la phrase avec spaCy
    doc = nlp(phrase)
    movement_verb_found = False  # Initialiser le drapeau pour les verbes de mouvement
    detected_verb = None  # Variable pour stocker le verbe trouvé

    # Vérifier la présence de verbes de mouvement
    for token in doc:
        # Affichage pour le débogage
        print(f"Token : {token.text}, Lemme : {token.lemma_}, Étiquette : {token.pos_}")
        
        # Vérifier si le lemme du token est dans la liste des verbes de mouvement
        # Forcer la détection du verbe si spaCy se trompe dans le POS
        if (token.lemma_ in movement_verbs) or (token.text.lower() in movement_verbs):
            movement_verb_found = True
            detected_verb = token.lemma_  # Stocker le verbe détecté
            break  # Un verbe de mouvement a été trouvé, on peut arrêter la boucle

    # Si aucun verbe de mouvement n'est trouvé, retourner "INVALID_TRIP"
    if not movement_verb_found:
        return "INVALID_TRIP"

    # Vérifier la présence de modes de transport invalides
    invalid_transports_regex = r"(" + "|".join(invalid_transports) + ")"
    match_transport = re.search(invalid_transports_regex, phrase, re.IGNORECASE)
    
    # Affichage pour débogage
    print(f"Mode de transport invalide détecté : {match_transport}")
    
    # Si un mode de transport invalide est trouvé, retourner "INVALID_TRIP"
    if match_transport:
        return "INVALID_TRIP"
    
    # Afficher le verbe de mouvement détecté
    print(f"Verbe de mouvement détecté : {detected_verb}")
    
    # Si tout est correct, retourner "VALID_TRIP"
    return "VALID_TRIP"

# Traitement du dataset
dataset = [
    "Je pars de Paris pour aller à Lyon demain matin.,Paris, Lyon, VALID_TRIP",
    "Je pars de Paris pour aller à Lyon demain matin.,Paris, Lyon, VALID_TRIP",
    "Je vais de Marseille à Bordeaux en train.,Marseille, Bordeaux, VALID_TRIP",
    "Je pars de Nice pour Toulouse cet après-midi.,Nice, Toulouse, VALID_TRIP",
    "Je voyage de Lille à Montpellier ce soir.,Lille, Montpellier, VALID_TRIP",
    "Je vais de Nantes à Strasbourg la semaine prochaine.,Nantes, Strasbourg, VALID_TRIP",
    "Je quitte Lyon pour me rendre à Paris demain.,Lyon, Paris, VALID_TRIP",
    "Je m'envole de Marseille pour rejoindre Bordeaux.,Marseille, Bordeaux, VALID_TRIP",
    "Je pars de Nice ce soir pour arriver à Toulouse demain.,Nice, Toulouse, VALID_TRIP",
    "Je me rends de Lille à Montpellier en voiture.,Lille, Montpellier, VALID_TRIP",
    "Je prends un train de Nantes pour aller à Strasbourg.,Nantes, Strasbourg, VALID_TRIP",
    "Je vais de Paris à Lyon sans arrêt.,Paris, Lyon, VALID_TRIP",
    "Je pars de Lyon ce soir pour arriver à Paris demain matin.,Lyon, Paris, VALID_TRIP",
    "Je voyage de Marseille à Bordeaux la semaine prochaine.,Marseille, Bordeaux, VALID_TRIP",
    "Je pars de Nantes pour rejoindre Strasbourg en train.,Nantes, Strasbourg, VALID_TRIP",
    "Je prends un bus de Lille pour Montpellier demain.,Lille, Montpellier, VALID_TRIP",
    "Je vais à Lyon en partant de Paris demain matin.,Paris, Lyon, VALID_TRIP",
    "Je suis à Paris et je veux aller à Lyon.,Paris, Lyon, VALID_TRIP",
    "Je pars de Paris pour aller à Tokyo en bus.,Paris, Tokyo, INVALID_TRIP",
    "Je prends un bateau de Marseille pour aller à Bordeaux demain.,Marseille, Bordeaux, INVALID_TRIP",
    "Je voyage de Nice à Toulouse en hélicoptère.,Nice, Toulouse, INVALID_TRIP",
    "Je me rends à Lille en prenant un vol spatial.,Destination inconnue, Lille, INVALID_TRIP",
    "Je vais de Nantes à Strasbourg en moto sous-marine.,Nantes, Strasbourg, INVALID_TRIP",
    "Je quitte Lyon pour me rendre à New York à vélo.,Lyon, New York, INVALID_TRIP",
    "Je prends une trottinette pour aller de Marseille à Bordeaux.,Marseille, Bordeaux, INVALID_TRIP",
    "Je pars de Nice en montgolfière pour rejoindre Toulouse.,Nice, Toulouse, INVALID_TRIP",
    "Je me rends de Lille à la lune en fusée.,Destination inconnue, Lille, INVALID_TRIP",
    "Je vais de Paris à Lyon à dos de chameau.,Paris, Lyon, INVALID_TRIP",
    "Je pars de Lyon ce soir pour arriver à Paris en sous-marin demain matin.,Lyon, Paris, INVALID_TRIP",
    "Je voyage de Marseille à la jungle Amazonienne en train.,Marseille, Jungle Amazonienne, INVALID_TRIP",
    "Je pars de Nantes pour rejoindre la mer en patins à roulettes.,Nantes, Mer, INVALID_TRIP",
    "Je suis à Strasbourg et je veux aller à Paris demain.,Strasbourg, Paris, VALID_TRIP",
    "Je suis à Lyon et je veux partir pour Marseille cet après-midi.,Lyon, Marseille, VALID_TRIP",
    "Je me trouve à Bordeaux et j'aimerais rejoindre Lille ce soir.,Bordeaux, Lille, VALID_TRIP",
    "Je suis actuellement à Nice et je souhaite aller à Toulouse demain matin.,Nice, Toulouse, VALID_TRIP",
    "Je suis à Paris et je veux prendre un vol pour New York.,Paris, New York, INVALID_TRIP",
    "Je suis à Nantes et je veux rejoindre la Lune en fusée.,Nantes, Lune, INVALID_TRIP",
    "Je me trouve à Marseille et je veux aller à Bordeaux en trottinette.,Marseille, Bordeaux, INVALID_TRIP",
    "Je suis à Lille et je veux voyager vers Montpellier en bateau.,Lille, Montpellier, INVALID_TRIP",
    "Je suis à Strasbourg et je veux aller à Paris à dos de chameau.,Strasbourg, Paris, INVALID_TRIP",
    "Après avoir passé la nuit à Paris, je partirai demain pour Berlin.,Paris, Berlin, VALID_TRIP",
    "Mon voyage commencera à Lyon et se terminera à Amsterdam.,Lyon, Amsterdam, VALID_TRIP",
    "Je dois quitter Marseille afin de rejoindre Bruxelles pour une réunion.,Marseille, Bruxelles, VALID_TRIP",
    "En provenance de Nice, je me dirigerai vers Genève en train.,Nice, Genève, VALID_TRIP",
    "Ayant séjourné à Bordeaux, je compte me rendre à Lisbonne en voiture.,Bordeaux, Lisbonne, VALID_TRIP",
    "Je suis basé à Lille mais je dois me déplacer jusqu'à Madrid.,Lille, Madrid, VALID_TRIP",
    "Mon point de départ est Strasbourg, avec une destination finale à Rome.,Strasbourg, Rome, VALID_TRIP",
    "Je quitterai Nantes pour atteindre Prague via un vol direct.,Nantes, Prague, VALID_TRIP",
    "Après mon départ de Toulouse, je voyagerai vers Vienne.,Toulouse, Vienne, VALID_TRIP",
    "Partant de Grenoble, mon chemin me mènera à Copenhague.,Grenoble, Copenhague, VALID_TRIP",
    "Je suis actuellement à Montpellier et je prévois d'aller à Oslo.,Montpellier, Oslo, VALID_TRIP",
    "Résidant à Rennes, je dois aller à Stockholm la semaine prochaine.,Rennes, Stockholm, VALID_TRIP",
    "Je m'apprête à quitter Brest pour rejoindre Helsinki.,Brest, Helsinki, VALID_TRIP",
    "De Dijon, je souhaite me rendre à Dublin en ferry.,Dijon, Dublin, INVALID_TRIP",
    "Je compte partir de Limoges pour aller à Athènes en montgolfière.,Limoges, Athènes, INVALID_TRIP",
    "En quittant Perpignan, je voyagerai jusqu'à Moscou en hélicoptère.,Perpignan, Moscou, INVALID_TRIP",
    "Je vais quitter Metz pour atteindre Le Caire en sous-marin.,Metz, Le Caire, INVALID_TRIP",
    "Mon voyage débutera à Tours et se terminera à Sydney en fusée.,Tours, Sydney, INVALID_TRIP",
    "Je prévois de partir de Reims pour aller à Tokyo en trottinette.,Reims, Tokyo, INVALID_TRIP",
    "Je suis à Clermont-Ferrand et je souhaite rejoindre Pékin à vélo.,Clermont-Ferrand, Pékin, INVALID_TRIP",
    "Je suis à Strasbourg il fait quel temps à Paris.,Strasbourg,Paris, INVALID_TRIP",
    "Je vais de Paris à Marseille en passant par Lyon.,Paris, Marseille, VALID_TRIP",
    "Je suis à Strasbourg et je veux aller à Marseille.,Strasbourg, Marseille, VALID_TRIP",
    "Je vais à Lyon depuis Strasbourg en passant par Metz., Strasbourg, Lyon, VALID_TRIP",
    "Je voudrais un billet de train pour Lyon depuis Marseille., Marseille, Lyon, VALID_TRIP",
    "Je vais à Grenoble depuis Strasbourg en passant par Metz en hélicoptère., Strasbourg, Grenoble, INVALID_TRIP",
    "Quelle est la météo à Tours aujourd'hui?, Tours, None, INVALID_TRIP",
    "Réserve un vol pour New York depuis Paris., Paris, New York, INVALID_TRIP",
    "Je prends le train de Paris à Bordeaux., Paris, Bordeaux, VALID_TRIP",
]

# Processing the dataset
for ligne in dataset:
    # Create a StringIO object for csv.reader to read the string
    ligne_io = io.StringIO(ligne)
    reader = csv.reader(ligne_io, delimiter=';', quotechar='"')
    phrase = None
    ville_depart_attendue = None
    ville_arrivee_attendue = None
    for row in reader:
        split_row = row[0].split(',')

        print(len(split_row))
        if len(split_row) > 4:
            phrase = split_row[0] + split_row[1]
            ville_depart_attendue = split_row[2].strip()
            ville_arrivee_attendue = split_row[3].strip()
            validite_attendue = split_row[4].strip()

        else: 
            phrase, ville_depart_attendue, ville_arrivee_attendue, validite_attendue = ligne.split(',')
            # Appliquer le modèle Spacy pour analyser la phrase
            doc = nlp(phrase)
            

        # Extract departure and arrival locations
        lieu_depart, lieu_arrivee, lieux_intermediaires = extraire_lieux(phrase)

        # Validate the mode of transport
        validite_predite = est_voyage_valide(phrase)

        # Display the results
        print(f"Phrase: {phrase}")
        print(f"Lieu de départ détecté : {lieu_depart} (Attendu : {ville_depart_attendue})")
        print(f"Lieu d'arrivée détecté : {lieu_arrivee} (Attendu : {ville_arrivee_attendue})")
        print(f"Lieux intermédiaires : {lieux_intermediaires}")
        print(f"Validité détectée : {validite_predite} (Attendu : {validite_attendue})")
        print("\n")
