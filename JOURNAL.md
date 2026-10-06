# Journal du projet bornes-recharge

Notes brutes au fil de l'eau. Serviront à écrire le README final.

## Question
Dans quelles communes y a-t-il le plus de voitures électriques par point de recharge ?

## Sources (téléchargées le 02/10/2026)
- `data/bornes.csv` : Base nationale IRVE, consolidation statique transport.data.gouv.fr (validée, dédoublonnée, mise à jour chaque nuit). 116 Mo, 169 875 points de recharge.
  https://www.data.gouv.fr/datasets/beta-bases-nationales-des-points-de-recharge-pour-vehicules-electriques-en-france-irve
- `data/voitures.csv` : Voitures particulières immatriculées par commune et par type de recharge (Agence ORE / AAA Data). 49 Mo, 703 545 lignes (commune × trimestre).
  https://www.data.gouv.fr/datasets/voitures-particulieres-immatriculees-par-commune-et-par-type-de-recharge-jeu-de-donnees-aaadata

## Choix et pièges rencontrés
1. **Source des bornes** : l'ancienne base data.gouv sera supprimée le 31/12/2026 → choix de la nouvelle consolidation du Point d'Accès National.
2. **Fraîcheur décalée** : bornes à jour au 02/10/2026, voitures arrêtées au 30/09/2025 (fréquence de mise à jour non respectée côté source).
3. **Séparateur** : virgule dans les deux fichiers (vérifié avec `Get-Content -TotalCount 3`).
4. **Code INSEE** : `01022` doit rester du texte (`dtype=str`), sinon le zéro disparaît et le JOIN échoue en silence.
5. **Granularité** : bornes.csv = une ligne par point de recharge (pas par station). voitures.csv = une ligne par commune et par trimestre → filtrer sur le dernier trimestre.
6. **Encodage** : voitures.csv est en latin-1, pas en UTF-8 → `UnicodeDecodeError` sur `0xc9` (É). Corrigé avec `encoding="latin-1"`.
7. **Accès à PostgreSQL** : conteneur recréé avec un port (`127.0.0.1:5433`, limité au PC) et un volume persistant (`sql-perso-data`).
8. **Vérification du transfert** : mêmes nombres de lignes dans Python et dans PostgreSQL.
9. **Majuscules** : PostgreSQL met les noms de colonnes en minuscules → guillemets doubles obligatoires pour `"CODGEO"`. À corriger : renommer en minuscules dans Python.
10. **44 233 points sans code commune** (plus d'un quart) → exclus du JOIN. Piste : retrouver la commune via les coordonnées GPS.
11. **Classement faussé par les flottes** : Lucciana, Poissy, Sochaux en tête → voitures d'entreprise/loueurs immatriculées au siège, pas là où elles roulent.
12. **Communes sans aucune borne** : disparaissent avec un JOIN simple → passer à un LEFT JOIN.
13. **Sécurité** : mot de passe en clair dans `charger.py` → à sortir avant publication sur GitHub.

## Marche 5 — corriger les surprises
14. **Noms de colonnes** : voitures passées en minuscules dans Python (`voitures.columns.str.lower()`) → plus besoin de guillemets dans PostgreSQL.
15. **Position GPS ajoutée** aux bornes (`consolidated_longitude`, `consolidated_latitude`).
16. **Diagnostic** : les 44 233 points sans code commune ont TOUS une position GPS → tous récupérables. (`IS NULL` / `IS NOT NULL` : une case vide ne s'écrit pas `= NULL`.)
17. **Méthode retenue** : jointure spatiale avec les contours des communes (Etalab, `communes-100m.geojson`, d'après Admin Express IGN, mis à jour en mai 2026). 35 014 communes, colonne `code` (texte, zéro conservé), coordonnées en longitude/latitude (EPSG:4326), comme les bornes.
18. **Piège du téléchargement** : Chrome a enregistré le fichier en `communes.geojson.txt` → renommé.
19. **Piège Paris / Lyon / Marseille** : le fichier des contours contient À LA FOIS la ville entière (75056, 69123, 13055) et ses arrondissements (75101…). Les pièces se superposent. Le fichier des voitures, lui, compte par arrondissement → on retire les 3 villes entières des contours.
20. **Test de la jointure spatiale** (avant de la donner) : 44 058 orphelines retrouvées sur 44 233. Restent 175 bornes : positions hors de France (Belgique, Allemagne…) ou latitude/longitude inversées (ex. -61,7 / -20,9 au lieu de La Réunion). Laissées de côté et documentées.
21. **À traiter ensuite** : 1 974 bornes ont un code commune qui n'existe pas côté voitures : codes postaux saisis à la place du code INSEE (86000, 75014…), code bidon `99999`, Paris entier `75056`.
22. **Classement refait après la jointure spatiale** : Lucciana passe de 2 à 22 points de recharge (4 164 → 378 VE par point), Poissy de 28 à 49 (1 118 → 639). Le classement change beaucoup : preuve que les bornes sans commune faussaient le résultat. Reste en tête des communes « sièges de flottes » (Villers-Cotterêts, Poissy, Sochaux) → surprise n°2 à traiter.
23. **Erreur rencontrée** : `can't open file 'C:\Users\33658\charger.py'` → `python charger.py` lancé depuis le mauvais dossier. Python cherche le fichier là où on se trouve → faire `cd C:\projets\bornes-recharge` d'abord.
24. **Surprise n°2, méthode validée** : indice = voitures par habitant (`NB_VP` ÷ population). Au-dessus de 1,5 → commune « siège de flottes », retirée du classement mais listée à part. Exemple : Villers-Cotterêts, 10 489 habitants pour 46 204 voitures.
25. **Population via l'API Géo** (`geo.api.gouv.fr/communes?type=commune-actuelle,arrondissement-municipal&fields=code,population`) : un seul appel depuis Python (`pd.read_json`), 35 014 communes reçues. Même piège du zéro : `dtype={"code": str}`.
26. **Erreur rencontrée** : taper un chemin seul (`C:\projets\bornes-recharge`) dans PowerShell → « n'est pas reconnu comme nom d'applet de commande ». Un chemin n'est pas un ordre : il faut `cd` devant.
27. **Erreur `function round(double precision, integer) does not exist`** : la population est arrivée en `double precision` (nombre à virgule approché, à cause des cases vides) et `ROUND(x, 1)` ne marche qu'avec `numeric` → `p.population::numeric`.
28. **Division par zéro** évitée avec `NULLIF(population, 0)` : des villages ont 0 habitant (villages détruits en 1914-1918, toujours officiellement communes).
29. **2 101 communes au-dessus de 1,5 voiture par habitant.** En tête : de vrais sièges de flottes (Tillé 70,5 voitures/habitant, Avrigny 62,6, Roissy-en-France 9,2, Lucciana 4,9, Lesquin 4,8, Villers-Cotterêts 4,4, Poissy 3,4, Rueil-Malmaison 3,0…). Mais aussi de tout petits villages (Rochefourchat : 7 voitures, 2 habitants) où quelques voitures suffisent à dépasser le seuil → bruit statistique sur les petits nombres, sans effet notable sur le classement final (très peu de VE). À documenter.
30. **Classement sans les flottes** (`NOT IN` sur une liste construite dans un 2e brouillon `WITH`) : Villers-Cotterêts, Poissy, Sochaux, Lucciana, Noisy-le-Grand, Clichy, Montigny ont disparu. Surprise n°2 réglée.
31. **Nouveau biais visible** : la tête du classement est maintenant faite de communes avec 1 à 4 points de recharge (Saint-Didier-au-Mont-d'Or 802 VE / 2 points, Les Avirons 312 / 1…). Avec si peu de bornes, le ratio saute au moindre changement → « petits nombres ». De plus, on ne voit toujours pas les communes avec ZÉRO borne (JOIN simple) ni les 1 974 bornes mal codées (codes postaux, 99999).

## Bloc 1 — finir l'analyse
32. **Correction de raisonnement** : en tête du classement, toutes les communes ont 180+ VE → leurs 1-2 bornes sont un vrai sous-équipement, pas du hasard. Le vrai risque « petits nombres » = villages avec très peu de VE. Seuil retenu : au moins 100 VE → 3 754 communes, 76 % des VE de France.
33. **`LEFT JOIN` + `COALESCE`** : fait apparaître les communes sans aucune borne publique (invisibles avec un JOIN simple). Communes ≥ 100 VE, hors flottes, avec 0 borne : La Bouilladisse (372 VE), Matoury (330), Aucamville (322), Remire-Montjoly (303), Petite-Île (290)… (≈ 257 au total d'après le test hors filtre flottes : 258).
34. **Effet de bord du filtre flottes** : Saint-Julien-du-Sault (403 VE, 0 borne) sort de la liste car classée « flotte » par le seuil de 1,5 voiture/habitant → possible faux positif à vérifier et documenter.
35. **Attention** : certaines de ces communes « sans borne » en ont peut-être, mais codées avec un code postal (piège n°21) → à vérifier après la correction des codes.
36. **Correction des codes faux** : une seule ligne changée — une borne « orpheline » devient une borne dont le code n'est PAS dans la liste officielle (`~bornes["code_insee_commune"].isin(communes["code"])`). Attrape d'un coup les cases vides, les codes postaux, `99999` et `75056`. Test : 2 135 codes faux recorrigés par la position GPS. Reste 222 bornes sans commune (175 + 47 codes faux avec une position hors de France). Vérifié : La Bouilladisse, Matoury, Aucamville ont réellement 0 borne publique après correction.
37. **Classement final (communes ≥ 100 VE, hors flottes, avec au moins 1 borne)** : Saint-Didier-au-Mont-d'Or (802 VE / 2 points), Saint-Ismier (635 / 2), Les Avirons (312 / 1), Harnes, Fillière, Cayenne… Le haut du classement est quasi identique avant et après la correction des 2 135 codes faux et le seuil des 100 VE → résultat **robuste** : les corrections n'ont pas inventé le classement, elles l'ont confirmé.
38. **Livrable de l'analyse = deux listes** : (1) communes sans aucune borne publique (LEFT JOIN), (2) communes avec trop peu de bornes (VE par point). On ne mélange pas : 0 borne = division impossible.
39. **Erreur rencontrée** : `\q` tapé dans PowerShell → « n'est pas reconnu ». `\q` est une commande de `psql` uniquement (pour sortir de la base), pas de PowerShell.

## Bloc 2 — ranger le code
40. **Mot de passe sorti du code** : adresse complète de la base rangée dans un fichier `.env` (« le coffre »), lue par `python-dotenv` (`load_dotenv()` puis `os.environ["DATABASE_URL"]`). Le `.env` ne sera jamais publié sur GitHub. Vérifié : `charger.py` tourne toujours (222 / 35014 / Rangé).
41. **Erreur rencontrée** : lignes Python (`import os`, `from dotenv import load_dotenv`) tapées dans PowerShell → refusées. PowerShell et Python ne parlent pas la même langue : le code Python va dans le fichier `.py`, PowerShell sert seulement à le lancer.
42. **Requêtes SQL rangées dans des fichiers** (`sql/`) : `communes_sans_borne.sql`, `communes_sous_equipees.sql`, `communes_flottes.sql` (liste complète, sans LIMIT, avec le code commune). Fini de les retaper à la main.

43. **Premier lancement de `analyser.py`** : une boucle `for` lit les 3 fichiers `.sql`, interroge la base et écrit 3 fichiers CSV dans `resultats/` (encodage `utf-8-sig` pour qu'Excel affiche bien les accents). 248 communes sans borne, 3 424 sous-équipées, 2 101 flottes.
44. **Piège des codes communes qui changent avec le temps** : Orée d'Anjou apparaît n°2 des « sans borne » (357 VE) alors qu'elle a des bornes. Cause : le fichier voitures (arrêté 2025) utilise l'ancien code `49069`, les contours et l'API (2026) le nouveau `49126` (vérifié : l'API renvoie 404 sur 49069). La correction GPS a donc rangé ses bornes sous 49126, et côté voitures 49069 ne trouve plus rien. Au total 184 codes du fichier voitures n'existent plus en 2026 (fusions de communes), mais seulement 1 421 VE (0,2 %) ; 3 ont 100 VE ou plus (Orée d'Anjou, Pierrefitte-sur-Seine, Porte des Pierres Dorées). Correction : `communes_sans_borne.sql` ne garde que les codes présents dans la table `population` (liste 2026). Amélioration possible plus tard : table de passage officielle de l'INSEE ancien code → nouveau code. **Vérifié** : 248 → 245 communes sans borne (les 3 attendues sont sorties), les deux autres listes inchangées.
45. **`.gitignore`** : liste des fichiers que Git ne doit jamais envoyer sur GitHub — `.env` (mot de passe), `data/` (fichiers bruts trop lourds : bornes.csv = 116 Mo, limite GitHub 100 Mo ; ils seront retéléchargés par le code).
46. **Une seule commande** : `lancer.py` (« chef d'orchestre ») lance `charger.py` puis `analyser.py` avec `subprocess.run(..., check=True)`. `check=True` = si une étape plante, on s'arrête : jamais d'analyse sur des données cassées. Vérifié : 222 / 35014 / Rangé puis 245 / 3424 / 2101. **Bloc 2 terminé.**

## Bloc 3 — automatiser
47. **Adresse des contours** : `https://etalab-datasets.geo.data.gouv.fr/contours-administratifs/latest/geojson/communes-100m.geojson` (`latest` = toujours la dernière version, ici celle du 04/05/2026).
48. **`telecharger.py`** : un « carnet d'adresses » (dictionnaire `sources` : nom du fichier → adresse) et une boucle `for` qui télécharge chaque fichier dans `data/` avec `urllib.request.urlretrieve` (inclus dans Python, rien à installer). Fini le téléchargement à la main dans Chrome (et le piège du `.geojson.txt`). Fichiers vérifiés : datés du 03/10/2026 à 9 h 04. Résultats identiques (222 / 35014 / 245 / 3424 / 2101) : la source n'a pas bougé depuis la veille.
49. **Chaîne complète en une commande** : `lancer.py` enchaîne maintenant `telecharger.py` → `charger.py` → `analyser.py`. Vérifié : téléchargement, 222 / 35014 / Rangé, 245 / 3424 / 2101.
50. **Choix du cloud (pour la version 2)** : AWS, le plus demandé dans les offres. Ordre décidé : d'abord finir et publier la version PC, ensuite migrer sur AWS. Pistes : outils payés seulement quand ils travaillent (S3, Lambda, EventBridge, Athena) plutôt qu'une base allumée 24 h/24 ; démarrage en plan Gratuit (6 mois, aucun prélèvement) + alerte budget.
51. **Préparer le lancement automatique** : `docker update --restart unless-stopped sql-perso` (la base se rallume à chaque démarrage de Docker) + Docker Desktop réglé pour démarrer à l'ouverture de session (déjà coché).
52. **Piège du raccourci Python** : `(Get-Command python).Source` renvoie `...\WindowsApps\python.exe`, un simple raccourci (alias) de Windows, pas le vrai Python. Le Planificateur de tâches peut ne pas le comprendre → on utilise la vraie adresse, et dans `lancer.py`, `sys.executable` (« le Python qui est en train de tourner ») au lieu du mot `"python"`. Vérifié : `Test-Path` → `True`, chaîne complète OK (245 / 3424 / 2101).
53. **Lancement automatique quotidien** : Planificateur de tâches Windows, tâche `bornes-recharge quotidien`, tous les jours à 7 h. Programme = vrai Python (`...\pythoncore-3.14-64\python.exe`), argument `lancer.py`, « Commencer dans » = dossier du projet (sinon Python ne trouve pas les fichiers). Options : sortir le PC de la veille, rattraper un lancement manqué. Limite : la session Windows doit être ouverte (Docker en a besoin). Test manuel (« Exécuter ») : fenêtre noire, statut « En cours » puis « Prêt » ; les 3 fichiers de `resultats/` réécrits à 10 h 53 → la tâche a bien tourné seule. **Bloc 3 terminé.**

## Bloc 4 — vitrine
54. **La source change toute seule** : le 06/10/2026, la tâche de 7 h a bien tourné seule (fichiers réécrits à 7 h 01). Mais toutes les bornes de Guyane ont disparu de la consolidation nationale (0 code 973, 0 position GPS en Guyane) → Cayenne passe dans « sans borne » (246 au lieu de 245). Le total national, lui, monte (170 482 points) : une perte locale ne se voit pas dans un total. Leçon : il faut des contrôles de qualité (comparer chaque jour par département et alerter si chute).
55. **Préparation GitHub** : compte `youssef-sellaoui`, licence MIT. Captures vérifiées avant publication : 5 contenaient des informations hors projet (mot de passe local dans la commande Docker, noms d'autres projets dans les onglets Notepad et Docker, dossiers personnels) → masquées dans les copies publiées, originaux gardés sur le PC.
56. **Chemins écrits en dur supprimés** : `C:/projets/bornes-recharge/...` ne marche que sur ce PC. Remplacé par `DOSSIER = Path(__file__).parent` (« le dossier où se trouve le script ») et `DOSSIER / "data/..."` dans les 4 scripts ; `lancer.py` lance chaque étape avec `cwd=DOSSIER`. Piège rencontré : l'ordre des remplacements (`f"` d'abord) → un `fDOSSIER` est apparu, repéré à la relecture avant de lancer. Test : lancé depuis `C:\` (hors du projet) → tout fonctionne (222 / 35014 / 246 / 3423 / 2101). Le projet marche désormais chez n'importe qui, quel que soit l'endroit où il le range.

## Captures (dossier `captures/`)
01 fichiers téléchargés · 02 aperçu CSV · 03 code v1 · 04 erreur encodage · 05 chargement OK · 06 reconstruction conteneur · 07 port 5433 · 08 rangé dans la base · 09 tables · 10 comptages + guillemets · 11 premier JOIN et surprises · 12 orphelines toutes avec GPS · 13 jointure spatiale (175 restantes) · 14 classement après jointure spatiale · 15 API population · 16 communes sièges de flottes · 17 classement sans flottes · 18 communes zéro borne (LEFT JOIN) · 19 correction des codes faux · 20 classement final · 21 mot de passe sorti du code · 22 analyser.py avant/après correction des codes 2026 (248 → 245) · 23 une seule commande (lancer.py) · 24 téléchargement par le code · 25 chaîne complète (lancer.py) · 26 vrai Python + sys.executable · 27 tâche planifiée terminée · 28 lancé depuis un autre dossier
