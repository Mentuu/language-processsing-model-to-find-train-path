import requests
import os
import shutil
import zipfile

# URL de la data SNCF
url = "https://eu.ftp.opendatasoft.com/sncf/plandata/export-ter-gtfs-last.zip"

# Chemins pour le téléchargement et le dossier cible
temp_dir = "./temp_sncf"
temp_file = os.path.join(temp_dir, "sncf_data.zip")
dest_dir = "./dataSncf"

# Créer le dossier temporaire s'il n'existe pas
os.makedirs(temp_dir, exist_ok=True)

# Télécharger la data
print("Téléchargement de la data SNCF en cours...")
response = requests.get(url, stream=True)
if response.status_code == 200:
    with open(temp_file, "wb") as f:
        for chunk in response.iter_content(chunk_size=1024):
            f.write(chunk)
    print("Téléchargement terminé avec succès.")
else:
    print(f"Erreur lors du téléchargement. Code HTTP : {response.status_code}")
    exit(1)

# Extraire le fichier téléchargé (si c'est un ZIP)
if zipfile.is_zipfile(temp_file):
    print("Extraction des fichiers...")
    with zipfile.ZipFile(temp_file, "r") as zip_ref:
        # Supprimer l'ancien dossier dataSncf
        if os.path.exists(dest_dir):
            shutil.rmtree(dest_dir)
        # Extraire dans le dossier de destination
        os.makedirs(dest_dir, exist_ok=True)
        zip_ref.extractall(dest_dir)
    print(f"Fichiers extraits dans {dest_dir}.")
else:
    print("Le fichier téléchargé n'est pas une archive ZIP.")

# Nettoyage des fichiers temporaires
shutil.rmtree(temp_dir)
print("Dossier temporaire supprimé.")
