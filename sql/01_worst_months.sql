-- Worst 5 months per city by average AQI (months with at least 20 days of AQI data)
WITH monthly AS (
    SELECT
        city,
        strftime('%Y-%m', date)  AS year_month,
        ROUND(AVG(AQI), 1)       AS avg_aqi,
        COUNT(AQI)               AS days_with_aqi
    FROM aqi_weather
    WHERE AQI IS NOT NULL
    GROUP BY city, strftime('%Y-%m', date)
    HAVING COUNT(AQI) >= 20
),
ranked AS (
    SELECT *,
           ROW_NUMBER() OVER (PARTITION BY city ORDER BY avg_aqi DESC) AS rnk
    FROM monthly
)
SELECT city, rnk AS rank, year_month, avg_aqi, days_with_aqi
FROM ranked
WHERE rnk <= 5
ORDER BY city, rnk;
