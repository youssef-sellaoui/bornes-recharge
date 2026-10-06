from pathlib import Path
DOSSIER = Path(__file__).parent
import pandas as pd
from sqlalchemy import create_engine
import geopandas as gpd
import os
from dotenv import load_dotenv
load_dotenv()
voitures = pd.read_csv(
	DOSSIER / "data/voitures.csv",
	usecols=["CODGEO", "LIBGEO",  "DATE_ARRETE", "NB_VP_RECHARGEABLES_EL", "NB_VP"],
	dtype={"CODGEO": str},
	encoding="latin-1",
)
voitures.columns = voitures.columns.str.lower()
bornes = pd.read_csv(
	DOSSIER / "data/bornes.csv",
	usecols=["code_insee_commune", "id_pdc_itinerance", "consolidated_longitude", "consolidated_latitude"],
	dtype={"code_insee_commune": str},
)

communes = gpd.read_file(DOSSIER / "data/communes.geojson")
communes = communes[~communes["code"].isin(["75056", "69123", "13055"])]
communes = communes[["code", "geometry"]]

orphelines = bornes[~bornes["code_insee_commune"].isin(communes["code"])]
points = gpd.GeoDataFrame(
    orphelines,
    geometry=gpd.points_from_xy(orphelines["consolidated_longitude"], orphelines["consolidated_latitude"]),
    crs="EPSG:4326",
)

retrouvees = gpd.sjoin(points, communes, how="left", predicate="within")
bornes.loc[retrouvees.index, "code_insee_commune"] = retrouvees["code"]
print(bornes["code_insee_commune"].isna().sum(), "bornes toujours sans commune")

adresse = "https://geo.api.gouv.fr/communes?type=commune-actuelle,arrondissement-municipal&fields=code,population"
population = pd.read_json(adresse, dtype={"code": str})
print(len(population), "communes reçues de l'API")

moteur = create_engine(os.environ["DATABASE_URL"])

voitures.to_sql("voitures", moteur, if_exists="replace", index=False)
bornes.to_sql("bornes", moteur, if_exists="replace", index=False)
population.to_sql("population", moteur, if_exists="replace", index=False)

print("Rangé dans la base !")