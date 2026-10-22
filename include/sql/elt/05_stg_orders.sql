CREATE OR REPLACE TABLE stg_orders AS SELECT * FROM orders_checked('orders.csv');
