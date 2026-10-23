-- Average AQI in winter (Nov-Feb) vs summer (Mar-Jun) per city, and their ratio
WITH seasonal AS (
    SELECT
        city,
        CASE
            WHEN CAST(strftime('%m', date) AS INTEGER) IN (11, 12, 1, 2) THEN 'winter'
            WHEN CAST(strftime('%m', date) AS INTEGER) IN (3, 4, 5, 6)   THEN 'summer'
        END AS season_group,
        AQI
    FROM aqi_weather
    WHERE AQI IS NOT NULL
)
SELECT
    city,
    ROUND(AVG(CASE WHEN season_group = 'winter' THEN AQI END), 1) AS winter_avg,
    ROUND(AVG(CASE WHEN season_group = 'summer' THEN AQI END), 1) AS summer_avg,
    ROUND(AVG(CASE WHEN season_group = 'winter' THEN AQI END)
        / AVG(CASE WHEN season_group = 'summer' THEN AQI END), 2) AS winter_to_summer_ratio
FROM seasonal
WHERE season_group IS NOT NULL
GROUP BY city
ORDER BY winter_to_summer_ratio DESC;
