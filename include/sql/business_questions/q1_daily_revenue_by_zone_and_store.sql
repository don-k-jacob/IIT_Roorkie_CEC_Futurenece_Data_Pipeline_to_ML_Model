-- ETL
SELECT s.zone, s.store_id, s.store_name, round(sum(f.net_revenue), 2) AS net_revenue
FROM etl_fact_orders f JOIN etl_dim_store s USING (store_id) GROUP BY ALL ORDER BY net_revenue DESC;
-- ELT (daily grain is in mart_daily_store_kpis: order_date, zone, store)
SELECT zone, store_id, store_name, round(sum(net_revenue), 2) AS net_revenue
FROM mart_daily_store_kpis GROUP BY ALL ORDER BY net_revenue DESC;
