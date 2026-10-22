-- ETL (masked values only)
SELECT c.customer_id, c.customer_name, c.loyalty_tier, c.email_masked, c.phone_masked, round(sum(f.net_revenue), 2) AS total_spend
FROM etl_fact_orders f JOIN etl_dim_customer c USING (customer_id)
WHERE f.order_status = 'DELIVERED' GROUP BY ALL ORDER BY total_spend DESC, c.customer_id LIMIT 10;
-- ELT
SELECT customer_id, customer_name, loyalty_tier, email_masked, phone_masked, total_spend FROM mart_top_customers;
