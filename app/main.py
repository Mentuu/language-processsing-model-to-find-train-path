from flask import Flask, request, jsonify
from flask_cors import CORS
import os
from RecordTranscribe import transcribe_and_analyze
from Converter.converter import processPhrases

app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": "http://localhost:3000"}})


# Configuration des fichiers temporaires
UPLOAD_FOLDER = './uploads'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

@app.route('/trips', methods=['POST'])
def trips():
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
        finally:
            # Supprimez le fichier temporaire après traitement
            if os.path.exists(temp_filename):
                os.remove(temp_filename)

        return jsonify(result)

    # Si un message JSON est envoyé
    if message:
        # Ajoutez ici votre logique pour traiter le message
        processed_message = processPhrases(message)

        return jsonify({"message": processed_message})

    # Retournez une erreur générique (ce cas ne devrait pas arriver)
    return jsonify({"error": "Unexpected error"}), 500


if __name__ == '__main__':
    app.run(debug=True)
