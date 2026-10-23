-- Days with AQI above 300 per city per year, with percentage of days with data
SELECT
    city,
    strftime('%Y', date)                         AS year,
    COUNT(AQI)                                   AS days_with_aqi,
    SUM(CASE WHEN AQI > 300 THEN 1 ELSE 0 END)   AS days_above_300,
    ROUND(100.0 * SUM(CASE WHEN AQI > 300 THEN 1 ELSE 0 END) / COUNT(AQI), 1) AS pct_above_300
FROM aqi_weather
WHERE AQI IS NOT NULL
GROUP BY city, strftime('%Y', date)
ORDER BY city, year;
