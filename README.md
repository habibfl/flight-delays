# flight-delays — pourquoi les vols américains sont-ils en retard ?

Projet de data analyse de bout en bout sur **tous les vols intérieurs des grandes
compagnies américaines en 2024 et 2025** (environ 14 millions de vols), croisés avec la
météo horaire de leur aéroport de départ : pipeline de collecte, entrepôt DuckDB,
requêtes SQL, analyses statistiques, modèle prédictif évalué, data story en ligne et
rapport Power BI.

**Data story en ligne : _lien Vercel à ajouter après le déploiement_**

**14 M de vols · 2 ans · 50 aéroports suivis heure par heure · 4 sources croisées**

## Résultats clés

Analyses reproductibles dans `analysis/fd_analyses.ipynb` et `analysis/fd_modele.ipynb`.

**Le premier facteur de retard, c'est le retard lui-même.** Quand un avion arrive en retard
de son vol précédent, son vol suivant est en retard dans 65 % des cas, contre 14 % sinon.
C'est aussi la première cause déclarée par les compagnies : 40 % des minutes de retard.

**L'heure du départ compte énormément.** 9 % de retards pour un départ à 5 h, 31 % à 19 h :
le risque double entre le premier vol de l'avion dans la journée (14 %) et son sixième (30 %).

**La météo pèse peu en volume, mais lourd quand elle frappe.** La météo extrême ne représente
que 6 % des minutes de retard déclarées. Pourtant, sous la neige, la moitié des vols arrivent
en retard et 10 % sont annulés. À heure, mois, aéroport et compagnie égaux (régression
logistique sur 500 000 vols), la cote d'un retard est multipliée par 7 sous la neige et par
2,4 sous la pluie.

| Météo au départ | Vols | En retard | Annulés |
|---|---|---|---|
| Ciel dégagé | 5,5 M | 19,5 % | 0,9 % |
| Nuageux | 4,0 M | 21,5 % | 1,3 % |
| Bruine | 1,2 M | 28,0 % | 2,3 % |
| Pluie | 0,3 M | 35,7 % | 4,6 % |
| Neige | 0,1 M | 49,7 % | 10,0 % |

**Les compagnies ne se valent pas, et durablement.** De 15 % (Endeavor Air) à 28 % (Frontier)
de vols en retard ; le classement de 2024 se retrouve en 2025 (corrélation des rangs de 0,81).

**Octobre-novembre 2025 sort du lot** : 20 % de retards contre 13 à 15 % un an plus tôt, pendant
le shutdown du gouvernement fédéral (1er octobre au 12 novembre 2025). Les données montrent la
coïncidence, pas à elles seules la cause.

## Sommaire

1. [Questions](#1-questions)
2. [Ce que montre le projet](#2-ce-que-montre-le-projet)
3. [Architecture](#3-architecture)
4. [Données et qualité](#4-données-et-qualité)
5. [Lancer le projet](#5-lancer-le-projet)
6. [Structure du dépôt](#6-structure-du-dépôt)
7. [Limites](#7-limites)

## 1. Questions

1. Quelle est l'ampleur du problème, et varie-t-elle dans l'année ?
2. D'où viennent les minutes de retard ?
3. La météo au départ change-t-elle vraiment la donne, à heure, saison et aéroport égaux ?
4. Un avion en retard contamine-t-il ses vols suivants ?
5. Quelles compagnies et quels aéroports sont les plus fiables, et ce classement est-il stable ?
6. Peut-on prédire un retard avant le départ, et que vaut la météo dans cette prédiction ?

## 2. Ce que montre le projet

| Compétence | Où |
|---|---|
| Lecture de fichiers volumineux (ZIP, CSV de 110 colonnes, Parquet) | `pipeline/extract_flights.py` |
| Appel d'API avec reprise sur erreur | `pipeline/extract_weather.py` (Open-Meteo) |
| Pipeline idempotent, relançable après une coupure | `pipeline/run_pipeline.py` |
| Volume : ~14 millions de lignes, agrégées en SQL | DuckDB, Parquet compressé |
| Croisement de 4 sources sur l'heure locale | vols × météo × aéroports × compagnies |
| Modélisation en étoile et contrôles qualité automatiques | `pipeline/build_warehouse.py` |
| SQL analytique (fenêtres, `LAG`, `UNPIVOT`, moyennes mobiles, `RANK`) | `sql/` |
| Statistiques : intervalles de confiance, khi-deux, régression logistique, Spearman | `analysis/fd_analyses.ipynb` |
| Machine learning évalué sur une période jamais vue, calibration, ablation | `analysis/fd_modele.ipynb` |
| Restitution web : data story interactive (React, D3.js) | `site/` |
| Restitution BI : rapport Power BI, mesures DAX, thème | `powerbi/`, `docs/powerbi.md` |
| Tests et intégration continue | `tests/`, GitHub Actions |

## 3. Architecture

```
BTS (ZIP mensuels, CSV) ──┐
OurAirports (CSV) ────────┼─► extract ─► Parquet ─► DuckDB (étoile) ─┬─► requêtes sql/
Open-Meteo (API JSON) ────┤                         + contrôles      ├─► notebooks (stats, modèle)
compagnies (CSV local) ───┘                                          ├─► JSON ─► site (React, D3)
                                                                     └─► Parquet ─► Power BI
```

| Étape | Outils | Rôle |
|---|---|---|
| Collecte | Python, requests | téléchargement avec reprise, fichiers jamais retéléchargés |
| Préparation | pandas, Parquet | 22 colonnes utiles sur 110, types fixés |
| Stockage | DuckDB | schéma en étoile, jointure météo à l'heure près |
| Contrôles | SQL | 8 contrôles, dont un bloquant |
| Analyse | SQL, scipy, statsmodels | tests et régressions sur les vols agrégés ou échantillonnés |
| Modèle | scikit-learn | gradient boosting et régression logistique, découpage temporel |
| Restitution web | React, D3.js, Vite | data story publiée sur Vercel |
| Restitution BI | Power BI | 6 pages, une question par page |

## 4. Données et qualité

| Source | Contenu | Format |
|---|---|---|
| [BTS, Reporting Carrier On-Time Performance](https://www.transtats.bts.gov/DatabaseInfo.asp?QO_VQ=EFD) | chaque vol : horaires, retards, annulations, causes | ZIP mensuel, CSV ~250 Mo |
| [Open-Meteo, archive historique](https://open-meteo.com/en/docs/historical-weather-api) | météo horaire : température, pluie, neige, vent, rafales | API JSON |
| [OurAirports](https://ourairports.com/data/) | noms et coordonnées des aéroports | CSV |
| `data/seeds/carriers.csv` | noms et types des compagnies | CSV |

**Modèle de données** : `fact_flights` (un vol par ligne, avec la météo au départ),
`fact_weather_hourly`, `dim_date`, `dim_carrier`, `dim_airport`, `quality_checks`.

**Contrôles automatiques** à chaque construction : doublons, aéroports sans
référentiel, compagnies sans nom, vols annulés avec un retard, cohérence entre les
causes déclarées et le retard total, part des vols croisés avec la météo, jours
manquants, et nombre de vols inchangé par la jointure météo (bloquant).

Définitions, traitement et limites détaillés : [docs/methodologie.md](docs/methodologie.md).

## 5. Lancer le projet

Prérequis : Python 3.11+, environ 3 Go d'espace disque, Power BI Desktop (Windows).

```bash
python -m venv venv
venv\Scripts\activate            # Linux/Mac : source venv/bin/activate
pip install -r requirements.txt

python pipeline/run_pipeline.py  # vols, aéroports, météo, entrepôt, export Power BI
python sql/run_all.py            # requêtes SQL -> sql/RESULTATS.md
jupyter notebook analysis/       # fd_analyses.ipynb puis fd_modele.ipynb
python analysis/export_site.py   # données du site -> site/public/data/story.json
```

Site (Node.js 20+) :

```bash
cd site
npm install
npm run dev                      # http://localhost:5173
```

Mise en ligne : sur vercel.com, importer le dépôt et choisir `site` comme dossier racine.

Une étape seule : `python pipeline/run_pipeline.py weather`. Chaque étape saute ce
qui est déjà fait.

Rapport Power BI : suivre [docs/powerbi.md](docs/powerbi.md) (thème dans `powerbi/theme.json`).

Tests (sur des données simulées au format exact des sources, sans réseau) :

```bash
pip install -r requirements-dev.txt
pytest -q tests
```

## 6. Structure du dépôt

```
flight-delays/
├── pipeline/          collecte, entrepôt, contrôles, export
├── sql/               requêtes analytiques commentées et résultats
├── analysis/          notebooks, fonctions d'accès aux données, modèle, charte, export du site
├── site/              data story (React, D3.js), publiée sur Vercel
├── data/seeds/        référentiel des compagnies (le reste est recréé par le pipeline)
├── powerbi/           rapport .pbix et thème
├── docs/              méthodologie, guide Power BI, captures
├── tests/             tests pytest
└── .github/workflows/ intégration continue
```

## 7. Limites

- La cause du retard est déclarée par la compagnie, pas mesurée.
- La météo est celle de l'aéroport de départ uniquement, à l'heure prévue, issue d'une
  réanalyse (ERA5) et non des stations des aéroports ; son code météo ne signale ni les orages
  ni le brouillard.
- Le modèle utilise la météo observée et non une prévision : l'apport mesuré de la
  météo est un plafond.

## Auteur

Cheikh Mouhamadou Habib FALL · [github.com/habibfl](https://github.com/habibfl)

Données publiques utilisées à des fins d'étude, sans usage commercial.
