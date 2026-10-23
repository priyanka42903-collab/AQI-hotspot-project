-- Number and share of days per CPCB AQI category, per city
SELECT
    city,
    CASE
        WHEN AQI <= 50  THEN '1 Good'
        WHEN AQI <= 100 THEN '2 Satisfactory'
        WHEN AQI <= 200 THEN '3 Moderate'
        WHEN AQI <= 300 THEN '4 Poor'
        WHEN AQI <= 400 THEN '5 Very Poor'
        ELSE                 '6 Severe'
    END AS aqi_category,
    COUNT(*) AS days,
    ROUND(100.0 * COUNT(*) / SUM(COUNT(*)) OVER (PARTITION BY city), 1) AS pct_of_city_days
FROM aqi_weather
WHERE AQI IS NOT NULL
GROUP BY city, aqi_category
ORDER BY city, aqi_category;
