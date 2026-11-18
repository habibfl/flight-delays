-- Aéroports de départ (plus de 5 000 vols) classés par taux de retard.
SELECT a.airport_code AS code, a.city AS ville, a.state AS etat,
       COUNT(*) AS vols,
       ROUND(100.0 * AVG(f.is_delayed::INT), 1) AS pct_retard,
       RANK() OVER (ORDER BY AVG(f.is_delayed::INT) DESC) AS rang
FROM fact_flights f
JOIN dim_airport a ON a.airport_code = f.origin
GROUP BY ALL
HAVING COUNT(*) >= 5000
ORDER BY rang
LIMIT 20;
