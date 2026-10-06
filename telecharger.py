from pathlib import Path
DOSSIER = Path(__file__).parent
import os
import urllib.request

os.makedirs(DOSSIER / "data", exist_ok=True)

sources = {
    "bornes.csv": "https://www.data.gouv.fr/api/1/datasets/r/4ca78c71-4ea4-475d-bd3a-d4aef88f7bf8",
    "voitures.csv": "https://www.data.gouv.fr/api/1/datasets/r/90e0d717-deda-4bdc-9987-f82faac5bc93",
    "communes.geojson": "https://etalab-datasets.geo.data.gouv.fr/contours-administratifs/latest/geojson/communes-100m.geojson",
}

for nom, adresse in sources.items():
    print("Téléchargement de", nom, "...")
    urllib.request.urlretrieve(adresse, DOSSIER / f"data/{nom}")

print("Téléchargement terminé !")