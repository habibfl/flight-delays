-- Ponctualité par compagnie : part des vols arrivés avec 15 min de retard ou plus,
-- taux d'annulation et retard moyen des vols en retard.
SELECT c.carrier_name AS compagnie,
       c.carrier_type AS type,
       COUNT(*) AS vols,
       ROUND(100.0 * AVG(f.is_delayed::INT), 1) AS pct_retard,
       ROUND(100.0 * AVG(f.is_cancelled::INT), 2) AS pct_annule,
       ROUND(AVG(f.arr_delay_min) FILTER (WHERE f.is_delayed), 0) AS retard_moyen_min
FROM fact_flights f
JOIN dim_carrier c USING (carrier_code)
GROUP BY ALL
HAVING COUNT(*) >= 1000
ORDER BY pct_retard;
