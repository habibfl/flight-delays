-- Répartition des minutes de retard par cause déclarée (vols arrivés avec 15 min ou plus).
WITH t AS (
    SELECT SUM(delay_carrier_min) AS compagnie,
           SUM(delay_late_aircraft_min) AS avion_en_retard,
           SUM(delay_nas_min) AS trafic_aerien,
           SUM(delay_weather_min) AS meteo,
           SUM(delay_security_min) AS securite
    FROM fact_flights
    WHERE is_delayed
)
SELECT cause, minutes, ROUND(100.0 * minutes / SUM(minutes) OVER (), 1) AS pct
FROM t UNPIVOT (minutes FOR cause IN (compagnie, avion_en_retard, trafic_aerien, meteo, securite))
ORDER BY minutes DESC;
