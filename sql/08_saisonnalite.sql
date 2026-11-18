-- Saisonnalité : taux de retard par mois, avec la moyenne mobile sur 3 mois.
WITH m AS (
    SELECT d.year AS annee, d.month AS mois, d.month_name AS nom_mois,
           COUNT(*) AS vols,
           100.0 * AVG(f.is_delayed::INT) AS pct
    FROM fact_flights f JOIN dim_date d ON d.date = f.flight_date
    GROUP BY ALL
)
SELECT annee, mois, nom_mois, vols,
       ROUND(pct, 1) AS pct_retard,
       ROUND(AVG(pct) OVER (ORDER BY annee, mois ROWS BETWEEN 2 PRECEDING AND CURRENT ROW), 1) AS moyenne_3_mois
FROM m
ORDER BY annee, mois;
