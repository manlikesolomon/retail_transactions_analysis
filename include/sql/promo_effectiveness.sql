CREATE OR REPLACE TABLE summary.promo_effectiveness
ENGINE = MergeTree
order by (metric_date, promotion)
AS
SELECT
    toDate(Date) AS metric_date,
    Promotion AS promotion,
    COUNT(*) AS total_transactions,
    SUM(Total_Cost) AS total_revenue,
    AVG(Total_Items) AS avg_basket_size
FROM raw.retail_transactions
WHERE Promotion != 'None'
GROUP BY metric_date, promotion;