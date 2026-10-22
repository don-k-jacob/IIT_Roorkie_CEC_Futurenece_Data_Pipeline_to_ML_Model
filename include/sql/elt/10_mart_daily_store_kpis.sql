CREATE OR REPLACE TABLE mart_daily_store_kpis AS
SELECT o.order_date, s.zone, s.store_id, s.store_name,
       count(*)                                              AS orders,
       count(*) FILTER (WHERE o.order_status = 'DELIVERED')  AS delivered_orders,
       round(sum(o.net_revenue), 2)                          AS net_revenue,
       round(avg(o.delivery_minutes) FILTER (WHERE o.order_status = 'DELIVERED'), 1) AS avg_delivery_minutes
FROM stg_orders o JOIN stg_stores s ON s.store_id = o.store_id AND s.dq_status = 'PASS'
WHERE o.dq_status = 'PASS'
GROUP BY ALL ORDER BY o.order_date, s.zone, s.store_id;
