-- Liaisons les plus fréquentées et leur fiabilité.
SELECT origin || ' → ' || dest AS liaison,
       COUNT(*) AS vols,
       ROUND(AVG(distance_miles) * 1.609, 0) AS distance_km,
       ROUND(100.0 * AVG(is_delayed::INT), 1) AS pct_retard,
       ROUND(100.0 * AVG(is_cancelled::INT), 2) AS pct_annule
FROM fact_flights
GROUP BY 1
ORDER BY vols DESC
LIMIT 20;
