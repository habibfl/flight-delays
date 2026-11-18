# Méthodologie

## Définitions

| Terme | Définition |
|---|---|
| Vol en retard | arrivé avec **15 minutes ou plus** de retard sur l'horaire prévu (définition officielle du BTS, colonne `ArrDel15`) |
| Taux de retard | vols en retard / vols effectués ; les vols annulés ou déroutés n'ont pas d'heure d'arrivée et ne sont jamais comptés en retard |
| Taux d'annulation | vols annulés / vols programmés |
| Cause du retard | répartition des minutes de retard déclarée par la compagnie, pour les vols arrivés avec 15 minutes ou plus |
| Météo au départ | météo horaire de l'aéroport de départ, à l'heure locale prévue du décollage |

## Périmètre

- **Vols** : tous les vols intérieurs des compagnies qui déclarent leur ponctualité au
  ministère américain des Transports (les plus grandes compagnies et leurs
  régionales), du 1er janvier 2024 au 31 décembre 2025.
- **Météo** : les 50 aéroports de départ les plus fréquentés. Les vols partant des
  autres aéroports restent dans toutes les analyses, sauf celles qui portent sur la météo.

## Traitement

1. **Extraction des vols.** Un ZIP par mois est téléchargé, puis seules 22 des
   ~110 colonnes sont conservées et écrites en Parquet (environ 10 fois plus léger que le CSV).
2. **Référentiel des aéroports.** Seuls les aéroports avec un code IATA sont gardés.
   Quand un code apparaît deux fois (ancien terrain fermé), le plus grand aéroport l'emporte.
3. **Météo.** Un appel à l'API Open-Meteo par aéroport couvre toute la période,
   en heure locale (`timezone=auto`), comme les horaires des vols. Au passage à
   l'heure d'hiver, une heure locale existe deux fois : on n'en garde qu'une, sinon
   la jointure dupliquerait des vols.
4. **Entrepôt.** Schéma en étoile dans DuckDB. Chaque vol est relié à la météo par
   (aéroport de départ, date, heure prévue). Le pipeline s'arrête si cette jointure
   change le nombre de vols.
5. **Contrôles qualité.** Doublons, aéroports sans référentiel, compagnies sans nom,
   vols annulés avec un retard, cohérence entre causes déclarées et retard total,
   couverture météo, jours manquants. Résultats dans la table `quality_checks`.

## Analyses statistiques

- **Intervalles de confiance** des taux (méthode de Wilson) : avec des millions de
  vols, presque tout écart est « significatif » ; l'intervalle montre surtout si
  l'écart est assez grand pour compter.
- **Effet ajusté de la météo** : régression logistique du retard sur la condition
  météo, à heure, mois, jour de la semaine, aéroport et compagnie égaux, sur un
  échantillon aléatoire de 500 000 vols. Résultat en *odds ratio*.
- **Effet cascade** : fonction de fenêtre `LAG` sur l'immatriculation de l'avion et la
  date, pour relier chaque vol au vol précédent du même appareil.
- **Stabilité des compagnies** : corrélation des rangs (Spearman) entre 2024 et 2025.

## Modèle prédictif

- Cible : retard de 15 minutes ou plus à l'arrivée.
- Variables connues avant le départ : mois, jour, heure prévue, compagnie, aéroports
  de départ et d'arrivée, distance, météo au départ.
- Découpage **temporel** : apprentissage sur les vols jusqu'à fin 2024, test sur 2025.
- Comparaison à une référence naïve (taux moyen de retard) ; mesures : log loss,
  Brier, AUC, AUC précision-rappel, calibration.
- Apport de chaque groupe de variables : ablation et importance par permutation.

## Limites

- La cause du retard est **déclarée** par la compagnie, pas mesurée, et une partie de la
  météo est classée en « trafic aérien ».
- La météo provient d'une réanalyse (ERA5, via Open-Meteo) au point de l'aéroport, pas
  des stations météo des aéroports. Son code météo distingue ciel dégagé, nuageux, bruine,
  pluie et neige, mais ne signale ni les orages ni le brouillard.
- Seule la météo au **départ** est prise en compte, pas celle à l'arrivée ni en route.
- Le modèle utilise la météo observée, pas une prévision : l'apport mesuré de la météo
  est un plafond.
- Les vols des compagnies qui ne déclarent pas leur ponctualité (petites compagnies,
  charters) ne sont pas couverts.
