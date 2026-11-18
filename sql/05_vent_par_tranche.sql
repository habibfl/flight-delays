-- Effet du vent en rafales : taux de retard par tranche de 10 km/h.
SELECT LEAST(FLOOR(gusts_kmh / 10) * 10, 80)::INT AS rafales_kmh_min,
       COUNT(*) AS vols,
       ROUND(100.0 * AVG(is_delayed::INT), 1) AS pct_retard,
       ROUND(100.0 * AVG(is_cancelled::INT), 2) AS pct_annule
FROM fact_flights
WHERE gusts_kmh IS NOT NULL
GROUP BY 1
ORDER BY 1;
