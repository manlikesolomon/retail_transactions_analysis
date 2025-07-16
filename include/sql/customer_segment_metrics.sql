CREATE OR REPLACE TABLE summary.customer_segment_metrics 
ENGINE = MergeTree
ORDER BY (metric_date, customer_category)
AS
SELECT
    toDate(Date) AS metric_date,
    Customer_Category AS customer_category,
    COUNT(*) AS total_transactions,
    SUM(Total_Cost) AS total_revenue,
    AVG(Total_Items) AS avg_basket_size,
    COUNTIf(Discount_Applied = 1) AS discount_txn_count
FROM raw.retail_transactions
GROUP BY metric_date, customer_category;