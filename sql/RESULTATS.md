# Résultats des requêtes SQL
Généré par `python sql/run_all.py` sur l'entrepôt DuckDB.

## 01_ponctualite_compagnies

Ponctualité par compagnie : part des vols arrivés avec 15 min de retard ou plus, taux d'annulation et retard moyen des vols en retard.

| compagnie          | type             |    vols |   pct_retard |   pct_annule |   retard_moyen_min |
|:-------------------|:-----------------|--------:|-------------:|-------------:|-------------------:|
| Endeavor Air       | Régionale        |  200094 |         15.4 |         2.3  |                 80 |
| Hawaiian Airlines  | Grande compagnie |  158614 |         16.2 |         0.93 |                 50 |
| Republic Airways   | Régionale        |  647501 |         17.5 |         2.61 |                 70 |
| Delta Air Lines    | Grande compagnie | 2035506 |         18.3 |         1    |                 73 |
| SkyWest Airlines   | Régionale        | 1584479 |         19.6 |         1.29 |                 82 |
| United Airlines    | Grande compagnie | 1555722 |         20.4 |         1.22 |                 73 |
| Envoy Air          | Régionale        |  579277 |         20.5 |         1.85 |                 64 |
| Southwest Airlines | Low cost         | 2811304 |         20.8 |         0.84 |                 55 |
| Alaska Airlines    | Grande compagnie |  491407 |         22.2 |         1.58 |                 51 |
| Spirit Airlines    | Ultra low cost   |  455618 |         22.4 |         1.74 |                 72 |
| Allegiant Air      | Ultra low cost   |  248109 |         23.1 |         1.06 |                 87 |
| PSA Airlines       | Régionale        |  476706 |         23.9 |         3.18 |                 88 |
| JetBlue Airways    | Low cost         |  471695 |         25.3 |         1.6  |                 77 |
| American Airlines  | Grande compagnie | 1957959 |         25.4 |         1.68 |                 85 |
| Frontier Airlines  | Ultra low cost   |  406689 |         27.7 |         2.05 |                 82 |

## 02_retard_par_heure

Effet boule de neige : les retards s'accumulent au fil de la journée.

|   heure_depart |   vols |   pct_retard |   retard_moyen_depart_min |
|---------------:|-------:|-------------:|--------------------------:|
|              0 |  23228 |         18.3 |                      13.1 |
|              1 |   7403 |         19.4 |                      12.7 |
|              2 |   2813 |         20.8 |                      10.8 |
|              3 |   1801 |         18.8 |                      11.3 |
|              4 |    824 |         17.7 |                      11.6 |
|              5 | 392775 |          8.9 |                       4.8 |
|              6 | 964370 |          9.8 |                       3.8 |
|              7 | 990372 |         12.5 |                       4.6 |
|              8 | 957285 |         14.1 |                       5.7 |
|              9 | 783216 |         15.5 |                       7.1 |
|             10 | 863163 |         16.8 |                       8.7 |
|             11 | 870728 |         18.5 |                      10.2 |
|             12 | 824678 |         20   |                      11.9 |
|             13 | 830873 |         21.9 |                      13.2 |
|             14 | 800258 |         24.5 |                      15.4 |
|             15 | 798814 |         26.3 |                      16.8 |
|             16 | 799271 |         28.2 |                      18.2 |
|             17 | 870190 |         29.5 |                      19.5 |
|             18 | 837578 |         30.5 |                      20.9 |
|             19 | 755247 |         31.2 |                      22.1 |
|             20 | 616337 |         31   |                      22.1 |
|             21 | 460619 |         28.7 |                      20.9 |
|             22 | 316383 |         27.9 |                      20.5 |
|             23 | 113263 |         20.6 |                      14   |

## 03_causes_des_retards

Répartition des minutes de retard par cause déclarée (vols arrivés avec 15 min ou plus).

| cause           |          minutes |   pct |
|:----------------|-----------------:|------:|
| avion_en_retard |      8.58367e+07 |  39.8 |
| compagnie       |      7.21496e+07 |  33.4 |
| trafic_aerien   |      4.41057e+07 |  20.4 |
| meteo           |      1.33046e+07 |   6.2 |
| securite        | 332730           |   0.2 |

## 04_meteo_et_retards

Croisement vols × météo : retard et annulation selon le temps au départ.

| meteo_au_depart   |    vols |   pct_retard |   pct_annule |
|:------------------|--------:|-------------:|-------------:|
| Neige             |  103249 |         49.7 |        10.03 |
| Pluie             |  281779 |         35.7 |         4.58 |
| Bruine            | 1172079 |         28   |         2.3  |
| Nuageux           | 4013557 |         21.5 |         1.3  |
| Dégagé            | 5489503 |         19.5 |         0.92 |

## 05_vent_par_tranche

Effet du vent en rafales : taux de retard par tranche de 10 km/h.

|   rafales_kmh_min |             vols |   pct_retard |   pct_annule |
|------------------:|-----------------:|-------------:|-------------:|
|                 0 | 740150           |         17.7 |         1.19 |
|                10 |      3.45194e+06 |         19.2 |         1.21 |
|                20 |      3.45634e+06 |         22.1 |         1.29 |
|                30 |      2.06748e+06 |         24   |         1.45 |
|                40 | 908646           |         25.2 |         1.67 |
|                50 | 318296           |         27.6 |         2.1  |
|                60 |  93929           |         33.1 |         3.55 |
|                70 |  18215           |         38.1 |         6.51 |
|                80 |   5172           |         42.4 |        20.73 |

## 06_effet_cascade_avion

Effet cascade : un avion en retard sur son vol précédent du jour part-il en retard sur le suivant ? (fonction de fenêtre LAG par immatriculation)

| situation               |    vols |   pct_retard |
|:------------------------|--------:|-------------:|
| Vol précédent en retard | 1974741 |         65.2 |
| Vol précédent à l'heure | 8451656 |         14.4 |

## 07_aeroports

Aéroports de départ (plus de 5 000 vols) classés par taux de retard.

| code   | ville             | etat   |   vols |   pct_retard |   rang |
|:-------|:------------------|:-------|-------:|-------------:|-------:|
| ASE    | Aspen             | CO     |  15573 |         30.2 |      1 |
| EGE    | Eagle             | CO     |   7670 |         27.5 |      2 |
| SFB    | Orlando           | FL     |  19994 |         27.3 |      3 |
| DFW    | Dallas-Fort Worth | TX     | 629436 |         27.2 |      4 |
| TVC    | Traverse City     | MI     |   9286 |         26.5 |      5 |
| MIA    | Miami             | FL     | 221851 |         26.4 |      6 |
| CLT    | Charlotte         | NC     | 412980 |         25.5 |      7 |
| FLL    | Fort Lauderdale   | FL     | 179475 |         24.9 |      8 |
| ORD    | Chicago           | IL     | 607080 |         24.7 |      9 |
| FWA    | Fort Wayne        | IN     |  11336 |         24.7 |     10 |
| EYW    | Key West          | FL     |  15707 |         24.4 |     11 |
| CRW    | Charleston        | WV     |   6335 |         24.2 |     12 |
| FNT    | Flint             | MI     |   5527 |         24.1 |     13 |
| MCO    | Orlando           | FL     | 319601 |         24.1 |     14 |
| STS    | Santa Rosa        | CA     |   8356 |         24   |     15 |
| PIA    | Peoria            | IL     |   9179 |         24   |     16 |
| DEN    | Denver            | CO     | 626331 |         24   |     17 |
| JAC    | Jackson           | WY     |  12011 |         24   |     18 |
| PHL    | Philadelphia      | PA     | 198154 |         23.8 |     19 |
| SGF    | Springfield       | MO     |  18527 |         23.7 |     20 |

## 08_saisonnalite

Saisonnalité : taux de retard par mois, avec la moyenne mobile sur 3 mois.

|   annee |   mois | nom_mois   |   vols |   pct_retard |   moyenne_3_mois |
|--------:|-------:|:-----------|-------:|-------------:|-----------------:|
|    2024 |      1 | janv.      | 547271 |         23.1 |             23.1 |
|    2024 |      2 | févr.      | 519221 |         15.8 |             19.4 |
|    2024 |      3 | mars       | 591767 |         20.6 |             19.8 |
|    2024 |      4 | avr.       | 582185 |         18.9 |             18.4 |
|    2024 |      5 | mai        | 609743 |         26   |             21.8 |
|    2024 |      6 | juin       | 611132 |         24.5 |             23.1 |
|    2024 |      7 | juil.      | 634613 |         28.7 |             26.4 |
|    2024 |      8 | août       | 619025 |         22.9 |             25.4 |
|    2024 |      9 | sept.      | 582622 |         15.4 |             22.3 |
|    2024 |     10 | oct.       | 615497 |         13.1 |             17.1 |
|    2024 |     11 | nov.       | 575404 |         14.6 |             14.3 |
|    2024 |     12 | déc.       | 590581 |         20.9 |             16.2 |
|    2025 |      1 | janv.      | 539747 |         18.2 |             17.9 |
|    2025 |      2 | févr.      | 504884 |         20.4 |             19.9 |
|    2025 |      3 | mars       | 600872 |         19.3 |             19.3 |
|    2025 |      4 | avr.       | 583950 |         19.5 |             19.7 |
|    2025 |      5 | mai        | 605648 |         23.3 |             20.7 |
|    2025 |      6 | juin       | 611575 |         27.7 |             23.5 |
|    2025 |      7 | juil.      | 631428 |         28   |             26.3 |
|    2025 |      8 | août       | 602378 |         22.2 |             26   |
|    2025 |      9 | sept.      | 562439 |         16.5 |             22.3 |
|    2025 |     10 | oct.       | 605844 |         20.2 |             19.6 |
|    2025 |     11 | nov.       | 570550 |         20   |             18.9 |
|    2025 |     12 | déc.       | 582304 |         26.3 |             22.2 |

## 09_routes

Liaisons les plus fréquentées et leur fiabilité.

| liaison   |   vols |   distance_km |   pct_retard |   pct_annule |
|:----------|-------:|--------------:|-------------:|-------------:|
| LGA → ORD |  22516 |          1179 |         24.3 |         2.47 |
| ORD → LGA |  22511 |          1179 |         25.9 |         2.33 |
| LAX → SFO |  22366 |           542 |         29.5 |         0.67 |
| OGG → HNL |  22350 |           161 |         11.3 |         1.07 |
| SFO → LAX |  22345 |           542 |         22.5 |         0.73 |
| HNL → OGG |  22340 |           161 |         10.4 |         0.93 |
| JFK → LAX |  20183 |          3982 |         18.7 |         0.65 |
| LAX → JFK |  20180 |          3982 |         18   |         0.71 |
| DCA → BOS |  18789 |           642 |         22.7 |         2.44 |
| BOS → DCA |  18789 |           642 |         21.7 |         2.35 |
| PHX → DEN |  18569 |           969 |         21.1 |         1.03 |
| DEN → PHX |  18460 |           969 |         24.2 |         0.99 |
| LAX → LAS |  18344 |           380 |         23.4 |         0.74 |
| LAS → LAX |  18322 |           380 |         21.6 |         0.62 |
| MCO → ATL |  17107 |           650 |         25.8 |         1.33 |
| ATL → MCO |  17078 |           650 |         29   |         1.39 |
| LIH → HNL |  16722 |           164 |         11.9 |         1.14 |
| HNL → LIH |  16720 |           164 |         11.4 |         1.05 |
| DEN → SLC |  15860 |           629 |         23.5 |         0.62 |
| ATL → LGA |  15857 |          1226 |         23.5 |         1.73 |
