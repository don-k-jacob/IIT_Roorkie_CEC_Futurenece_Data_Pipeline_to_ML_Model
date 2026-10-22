-- ETL
SELECT payment_mode, round(sum(net_revenue), 2) AS net_revenue FROM etl_fact_orders GROUP BY 1 ORDER BY 2 DESC;
SELECT reason, count(*) AS rows, round(sum(abs(difference)), 2) AS amount FROM etl_payment_reconciliation GROUP BY 1 ORDER BY 3 DESC;
-- ELT
SELECT payment_mode, net_revenue FROM mart_payment_mode_revenue;
SELECT reason, count(*) AS rows, round(sum(abs(difference)), 2) AS amount FROM mart_payment_reconciliation GROUP BY 1 ORDER BY 3 DESC;
