CREATE OR REPLACE TABLE summary.daily_city_metrics
    ENGINE = MergeTree
    ORDER BY (metric_date, city)
    AS
    SELECT
        toDate(Date) AS metric_date,
        City AS city,
        COUNT(*) AS total_transactions,
        SUM(Total_Cost) AS total_revenue,
        AVG(Total_Cost) AS avg_transaction_value
    FROM raw.retail_transactions
    GROUP BY metric_date, city;