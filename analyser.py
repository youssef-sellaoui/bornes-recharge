from pathlib import Path
DOSSIER = Path(__file__).parent
import os
import pandas as pd
from dotenv import load_dotenv
from sqlalchemy import create_engine, text

load_dotenv()
moteur = create_engine(os.environ["DATABASE_URL"])
os.makedirs(DOSSIER / "resultats", exist_ok=True)

for nom in ["communes_sans_borne", "communes_sous_equipees", "communes_flottes"]:
    requete = open(DOSSIER / f"sql/{nom}.sql", encoding="utf-8").read()
    resultat = pd.read_sql(text(requete), moteur)
    resultat.to_csv(DOSSIER / f"resultats/{nom}.csv", index=False, encoding="utf-8-sig")
    print(nom, ":", len(resultat), "communes")