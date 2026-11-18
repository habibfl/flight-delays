-- Croisement vols × météo : retard et annulation selon le temps au départ.
SELECT weather_condition AS meteo_au_depart,
       COUNT(*) AS vols,
       ROUND(100.0 * AVG(is_delayed::INT), 1) AS pct_retard,
       ROUND(100.0 * AVG(is_cancelled::INT), 2) AS pct_annule
FROM fact_flights
WHERE weather_condition IS NOT NULL
GROUP BY 1
ORDER BY pct_retard DESC;
