-- ETL
SELECT s.store_id, s.store_name, round(avg(f.delivery_minutes), 1) AS avg_delivery_minutes,
       round(100.0 * avg(f.within_15_min::INT), 1) AS pct_within_15_min
FROM etl_fact_orders f JOIN etl_dim_store s USING (store_id)
WHERE f.order_status = 'DELIVERED' GROUP BY ALL ORDER BY s.store_id;
-- ELT
SELECT store_id, store_name, avg_delivery_minutes, pct_within_15_min FROM mart_delivery_sla;
