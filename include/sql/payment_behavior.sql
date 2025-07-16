CREATE OR REPLACE TABLE summary.payment_behavior
ENGINE = MergeTree
ORDER BY (metric_date, payment_method)
AS
SELECT
    toDate(Date) AS metric_date,
    Payment_Method AS payment_method,
    COUNT(*) AS total_transactions,
    SUM(Total_Cost) AS total_revenue,
    AVG(Total_Cost) AS avg_transaction_value
FROM raw.retail_transactions
GROUP BY metric_date, payment_method;