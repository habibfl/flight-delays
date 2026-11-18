# Rapport Power BI : guide de construction

Le pipeline écrit les tables dans `data/powerbi/` (Parquet). Ce guide décrit le
modèle, les mesures DAX, le thème et la construction page par page du rapport
`powerbi/flight-delays.pbix`.

**Principe de mise en page.** Le rapport se lit comme une data story, pas comme un
mur de graphiques :
- chaque page répond à **une question**, posée en titre ;
- un bandeau de **3 ou 4 chiffres clés** ouvre la page ;
- chaque graphique a un **titre qui énonce le constat** (« Les orages doublent le
  risque de retard ») et un sous-titre qui dit ce qui est mesuré ;
- une **zone de texte de 2 phrases** dit ce qu'il faut retenir ;
- l'orange est réservé aux **retards** et à ce que l'on veut faire remarquer, le bleu
  à tout le reste.

## 1. Thème

**Affichage → Thèmes → Rechercher les thèmes** → `powerbi/theme.json`.
Il fixe les couleurs (bleu pour les vols, orange pour les retards, même palette que
les figures des notebooks), les polices, les bordures arrondies et le fond.

Taille de page : **Affichage → Paramètres de la page → 16:9**.

## 2. Charger les données

**Obtenir les données → Parquet**, puis le chemin complet de chaque fichier
(par exemple `C:\Users\HP\Desktop\flight-delays\data\powerbi\fact_flights.parquet`).

| Fichier | Rôle | Lignes (ordre de grandeur) |
|---|---|---|
| `fact_flights` | un vol par ligne, avec la météo au départ | ~14 millions |
| `dim_date` | calendrier | 731 |
| `dim_carrier` | compagnies | ~20 |
| `dim_airport` | aéroports | ~350 |
| `agg_daily` | agrégat jour × aéroport × compagnie | ~200 000 |
| `quality_checks` | résultats des contrôles qualité | 8 |
| `model_scores`, `model_calibration`, `model_importance` | résultats du modèle (notebook `fd_modele`) | quelques lignes |

Dans Power Query, supprimer de `fact_flights` les colonnes inutiles au rapport
(`tail_number`, `flight_number`, `sched_dep_hhmm`, `flight_id`) : le fichier .pbix
sera nettement plus léger.

Ajouter dans `fact_flights` une colonne de tranche de rafales
(**Ajouter une colonne → Colonne personnalisée**) :

```powerquery
Rafales = if [gusts_kmh] = null then null
          else Text.From(Number.RoundDown(List.Min({[gusts_kmh], 80}) / 10) * 10) & " km/h"
```

## 3. Modèle (schéma en étoile)

| De | Vers | Cardinalité | Active |
|---|---|---|---|
| `fact_flights[flight_date]` | `dim_date[date]` | plusieurs à un | oui |
| `fact_flights[carrier_code]` | `dim_carrier[carrier_code]` | plusieurs à un | oui |
| `fact_flights[origin]` | `dim_airport[airport_code]` | plusieurs à un | oui |
| `fact_flights[dest]` | `dim_airport[airport_code]` | plusieurs à un | non (`USERELATIONSHIP`) |
| `agg_daily[flight_date]` | `dim_date[date]` | plusieurs à un | oui |
| `agg_daily[origin]` | `dim_airport[airport_code]` | plusieurs à un | oui |
| `agg_daily[carrier_code]` | `dim_carrier[carrier_code]` | plusieurs à un | oui |

- `dim_date` : **Marquer comme table de dates** (colonne `date`).
- Trier `month_name` par `month` et `weekday_name` par `weekday`.
- Masquer en vue rapport les colonnes de clés des tables de faits.

## 4. Mesures DAX

Créer une table vide `_Mesures` pour les ranger.

```dax
Vols = COUNTROWS ( fact_flights )

Vols en retard = CALCULATE ( [Vols], fact_flights[is_delayed] = TRUE () )

% Retard = DIVIDE ( [Vols en retard], [Vols] )

Vols annulés = CALCULATE ( [Vols], fact_flights[is_cancelled] = TRUE () )

% Annulés = DIVIDE ( [Vols annulés], [Vols] )

Retard moyen (min) =
AVERAGEX (
    FILTER ( fact_flights, fact_flights[is_delayed] = TRUE () ),
    fact_flights[arr_delay_min]
)

Heures de retard =
DIVIDE ( SUMX ( fact_flights, MAX ( fact_flights[arr_delay_min], 0 ) ), 60 )

Minutes de retard =
SUM ( fact_flights[delay_carrier_min] ) + SUM ( fact_flights[delay_late_aircraft_min] )
    + SUM ( fact_flights[delay_nas_min] ) + SUM ( fact_flights[delay_weather_min] )
    + SUM ( fact_flights[delay_security_min] )

% Minutes compagnie = DIVIDE ( SUM ( fact_flights[delay_carrier_min] ), [Minutes de retard] )
% Minutes avion en retard = DIVIDE ( SUM ( fact_flights[delay_late_aircraft_min] ), [Minutes de retard] )
% Minutes trafic aérien = DIVIDE ( SUM ( fact_flights[delay_nas_min] ), [Minutes de retard] )
% Minutes météo = DIVIDE ( SUM ( fact_flights[delay_weather_min] ), [Minutes de retard] )

% Retard ciel dégagé =
CALCULATE ( [% Retard], fact_flights[weather_condition] = "Dégagé" )

Écart vs ciel dégagé (pts) = ( [% Retard] - [% Retard ciel dégagé] ) * 100

% Retard N-1 = CALCULATE ( [% Retard], SAMEPERIODLASTYEAR ( dim_date[date] ) )

Évolution vs N-1 (pts) = ( [% Retard] - [% Retard N-1] ) * 100

% Retard arrivées =
CALCULATE ( [% Retard], USERELATIONSHIP ( fact_flights[dest], dim_airport[airport_code] ) )

Moyenne générale % Retard = CALCULATE ( [% Retard], ALL ( fact_flights ) )

Couleur au-dessus moyenne =
IF ( [% Retard] > [Moyenne générale % Retard], "#eb6834", "#2a78d6" )
```

Formats : les mesures `%` en pourcentage à une décimale, les autres en nombre
entier avec séparateur de milliers.

**Couleur conditionnelle** : sur les barres des compagnies et des aéroports,
**Couleurs des barres → fx → Valeur du champ → `Couleur au-dessus moyenne`**.

## 5. Pages

Toutes les pages ont la même structure : titre-question en haut à gauche, segments
(Année, Compagnie, Aéroport de départ) en haut à droite, bandeau de chiffres clés,
puis les graphiques. Synchroniser les segments entre les pages
(**Affichage → Synchroniser les segments**).

### Page 1 : « Pourquoi les vols américains sont-ils en retard ? »

- **Bandeau de chiffres clés** (cartes) : `Vols`, `% Retard`, `% Annulés`,
  `Heures de retard`.
- **Courbe** : `% Retard` par `dim_date[month_name]`, une ligne par `year`.
  Titre : le mois le plus touché ; ligne de référence = `Moyenne générale % Retard`.
- **Carte** (visuel Carte ou Azure Maps) : `dim_airport[latitude]`,
  `[longitude]`, taille = `Vols`, couleur = `% Retard` (dégradé bleu du thème).
- **Zone de texte** : les 3 constats principaux du projet, une phrase chacun.

### Page 2 : « La météo est-elle coupable ? »

- **Bandeau** : `% Retard ciel dégagé`, `% Retard` par orage, par neige
  (cartes filtrées sur `weather_condition`).
- **Barres horizontales** : `% Retard` par `weather_condition`, triées,
  info-bulle avec `Vols` et `Écart vs ciel dégagé (pts)`.
- **Courbe** : `% Retard` et `% Annulés` par tranche de `Rafales`.
- **Boutons « Afficher : retards | annulations »** : deux signets
  (**Affichage → Signets**) qui basculent le graphique principal entre
  `% Retard` et `% Annulés`, avec deux boutons en haut du graphique.
- **Zone de texte** : rappeler que la cause « météo » déclarée ne couvre que la
  météo extrême, et donner l'odds ratio ajusté du notebook (effet à heure, mois,
  aéroport et compagnie égaux).

### Page 3 : « D'où viennent les minutes de retard ? »

- **Anneau ou barres empilées 100 %** : les 4 mesures `% Minutes ...`
  (les minutes « avion en retard » en orange).
- **Histogramme** : `% Retard` par `sched_dep_hour` (effet boule de neige),
  titre : l'heure la plus sûre et la plus risquée.
- **Barres empilées par mois** : minutes par cause, pour voir l'été et l'hiver.

### Page 4 : « Quelles compagnies et quels aéroports sont fiables ? »

- **Barres horizontales** : `% Retard` par `dim_carrier[carrier_name]`, couleur
  conditionnelle au-dessus / au-dessous de la moyenne, ligne constante = moyenne.
- **Nuage de points** : `Vols` en X, `% Retard` en Y, une bulle par compagnie,
  légende = `carrier_type`.
- **Tableau** : 15 premiers aéroports de départ avec `Vols`, `% Retard`,
  `% Annulés`, `Évolution vs N-1 (pts)` (barres de données dans les cellules).
- **Info-bulle personnalisée** : une page masquée de taille « Info-bulle » avec la
  courbe mensuelle de `% Retard`, attachée aux barres des compagnies.

### Page 5 : « Peut-on prédire un retard avant le départ ? »

- **Barres** : `model_scores[auc]` par modèle (la référence naïve en gris).
- **Courbe** : `model_calibration[predit]` en X, `[observe]` en Y, avec la
  diagonale (ligne de référence).
- **Barres** : `model_importance[hausse_log_loss]` par groupe de variables
  (la météo en orange).
- **Zone de texte** : limites du modèle (météo observée et non prévue).

### Page 6 : « Méthode et qualité des données »

- **Tableau** `quality_checks` avec une icône (mise en forme conditionnelle sur
  `passed`).
- **Histogramme** : `Vols` par mois (vérifie qu'aucun mois ne manque).
- **Zone de texte** : sources, définition du retard (15 min et plus à l'arrivée),
  périmètre de la météo (50 aéroports), limites.

## 6. Finitions

- Navigation : un **navigateur de pages** (Insérer → Boutons → Navigateur) en haut
  de chaque page.
- Aligner tous les visuels sur une grille (Affichage → Grille, Aligner sur la grille).
- Désactiver les interactions inutiles (Format → Modifier les interactions).
- Exporter chaque page en image dans `docs/screenshots/` pour le README.
- Publier : **Fichier → Exporter → PDF** pour un aperçu partageable ; la publication
  web nécessite un compte Power BI professionnel ou scolaire.
