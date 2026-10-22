CREATE OR REPLACE TABLE mart_category_margin AS
SELECT p.category,
       round(sum(o.net_revenue), 2) AS revenue,
       round(sum(CASE WHEN o.order_status = 'DELIVERED' THEN o.quantity * p.cost_price ELSE 0 END), 2) AS cost,
       round(sum(o.net_revenue) - sum(CASE WHEN o.order_status = 'DELIVERED' THEN o.quantity * p.cost_price ELSE 0 END), 2) AS gross_margin,
       round(100 * (sum(o.net_revenue) - sum(CASE WHEN o.order_status = 'DELIVERED' THEN o.quantity * p.cost_price ELSE 0 END))
             / nullif(sum(o.net_revenue), 0), 1) AS margin_pct
FROM stg_orders o JOIN stg_products p ON p.product_id = o.product_id AND p.dq_status = 'PASS'
WHERE o.dq_status = 'PASS'
GROUP BY ALL ORDER BY revenue DESC;
