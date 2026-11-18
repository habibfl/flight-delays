-- Effet cascade : un avion en retard sur son vol précédent du jour
-- part-il en retard sur le suivant ? (fonction de fenêtre LAG par immatriculation)
WITH legs AS (
    SELECT tail_number, flight_date, sched_dep_hhmm, is_delayed,
           LAG(is_delayed) OVER (PARTITION BY tail_number, flight_date ORDER BY sched_dep_hhmm) AS prev_delayed
    FROM fact_flights
    WHERE tail_number IS NOT NULL AND NOT is_cancelled
)
SELECT CASE WHEN prev_delayed THEN 'Vol précédent en retard' ELSE 'Vol précédent à l''heure' END AS situation,
       COUNT(*) AS vols,
       ROUND(100.0 * AVG(is_delayed::INT), 1) AS pct_retard
FROM legs
WHERE prev_delayed IS NOT NULL
GROUP BY 1
ORDER BY 1;
