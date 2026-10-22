CREATE OR REPLACE TABLE mart_payment_mode_revenue AS
SELECT payment_mode, count(*) FILTER (WHERE order_status = 'DELIVERED') AS delivered_orders,
       round(sum(net_revenue), 2) AS net_revenue
FROM stg_orders WHERE dq_status = 'PASS'
GROUP BY ALL ORDER BY net_revenue DESC;
