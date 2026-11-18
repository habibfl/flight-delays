-- Effet boule de neige : les retards s'accumulent au fil de la journée.
SELECT sched_dep_hour AS heure_depart,
       COUNT(*) AS vols,
       ROUND(100.0 * AVG(is_delayed::INT), 1) AS pct_retard,
       ROUND(AVG(dep_delay_min), 1) AS retard_moyen_depart_min
FROM fact_flights
WHERE NOT is_cancelled
GROUP BY 1
ORDER BY 1;
