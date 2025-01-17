from flask import Flask, request, jsonify
from flask_cors import CORS
import os
from RecordTranscribe import transcribe_and_analyze
from Converter.converter import processPhrases
from itinéraireTrain import itineraireTrain
from datetime import datetime, timedelta


app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": "http://localhost:3000"}})


# Configuration des fichiers temporaires
UPLOAD_FOLDER = './uploads'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

@app.route('/trips', methods=['POST'])
def trips():
    transcriptionMessage = ""
    # Vérifiez si le contenu est JSON
    if request.is_json:
        data = request.get_json()
        message = data.get('message', None)
    else:
        message = None

    # Vérifiez si un fichier est envoyé
    audio_file = request.files.get('audio_file', None)

    # Bloquez si ni message ni audio_file ne sont présents
    if not audio_file and not message:
        return jsonify({"error": "Either 'message' (in JSON) or 'audio_file' (in form-data) is required"}), 400

    # Si un fichier audio est envoyé
    if audio_file:
        # Sauvegardez le fichier temporairement
        temp_filename = os.path.join(UPLOAD_FOLDER, audio_file.filename)
        audio_file.save(temp_filename)

        try:
            # Appelez la fonction de transcription et d'analyse depuis RecordTranscribe.py
            result = transcribe_and_analyze(temp_filename)
            transcriptionMessage = result["transcription"]  

        finally:
            # Supprimez le fichier temporaire après traitement
            if os.path.exists(temp_filename):
                os.remove(temp_filename)

    if message:
        transcriptionMessage = message

    processed_message = processPhrases(transcriptionMessage)
   

    if processed_message is not None:
        
        lieu_depart, lieu_arrivee, lieux_intermediaires, departure_stations, arrival_stations = processed_message
    
        # Paramètres par défaut ou récupérés depuis les paramètres de requête
        stops_filename = os.path.join(os.path.dirname(__file__), '../dataSncf/stops.txt')
        stop_times_filename = os.path.join(os.path.dirname(__file__), '../dataSncf/stop_times.txt')

         # Date et heure actuelles
        now = datetime.now()
        current_date = now.date()
        current_time_sec = now.hour * 3600 + now.minute * 60 + now.second

        # 1) Calcul de l'itinéraire le plus rapide (simple)
        path_names, duree_str, next_dep_time  = itineraireTrain(
            stops_filename, 
            stop_times_filename, 
            lieu_depart.lower(), 
            lieu_arrivee.lower(),
            current_date,
            current_time_sec,
            lieux_intermediaires
        )

        if path_names is None:
            return jsonify({"error": "Aucun itinéraire trouvé."}), 200

        return jsonify({
            "itineraire": " -> ".join(path_names),
            "duree": duree_str,
            "next_dep_time": next_dep_time
        })
    else:
        return jsonify({"error": "Je n'ai pas compris votre message, veuillez réessayer."}), 200
    

if __name__ == '__main__':
    app.run(debug=True)
