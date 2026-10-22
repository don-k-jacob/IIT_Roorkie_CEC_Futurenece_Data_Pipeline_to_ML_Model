CREATE OR REPLACE TABLE mart_delivery_sla AS
SELECT s.zone, s.store_id, s.store_name,
       count(*)                                        AS delivered_orders,
       round(avg(o.delivery_minutes), 1)               AS avg_delivery_minutes,
       round(100.0 * avg(o.within_15_min::INT), 1)     AS pct_within_15_min
FROM stg_orders o JOIN stg_stores s ON s.store_id = o.store_id AND s.dq_status = 'PASS'
WHERE o.dq_status = 'PASS' AND o.order_status = 'DELIVERED'
GROUP BY ALL ORDER BY s.store_id;
