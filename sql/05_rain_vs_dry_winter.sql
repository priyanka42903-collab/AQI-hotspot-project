-- Average AQI on rainy (>=2.5 mm) vs dry (<0.1 mm) days, winter months only
SELECT
    city,
    COUNT(CASE WHEN precipitation_sum >= 2.5 THEN 1 END)             AS rainy_days,
    COUNT(CASE WHEN precipitation_sum < 0.1  THEN 1 END)             AS dry_days,
    ROUND(AVG(CASE WHEN precipitation_sum >= 2.5 THEN AQI END), 1)   AS rainy_day_avg_aqi,
    ROUND(AVG(CASE WHEN precipitation_sum < 0.1  THEN AQI END), 1)   AS dry_day_avg_aqi
FROM aqi_weather
WHERE AQI IS NOT NULL
  AND CAST(strftime('%m', date) AS INTEGER) IN (11, 12, 1, 2)
GROUP BY city
ORDER BY city;
