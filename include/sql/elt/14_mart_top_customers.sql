-- No raw email or phone: only the masked values from staging.
CREATE OR REPLACE TABLE mart_top_customers AS
SELECT c.customer_id, c.customer_name, c.loyalty_tier, c.email_masked, c.phone_masked,
       count(*) AS delivered_orders, round(sum(o.net_revenue), 2) AS total_spend
FROM stg_orders o JOIN stg_customers c ON c.customer_id = o.customer_id AND c.dq_status = 'PASS'
WHERE o.dq_status = 'PASS' AND o.order_status = 'DELIVERED'
GROUP BY ALL ORDER BY total_spend DESC, c.customer_id LIMIT 10;
