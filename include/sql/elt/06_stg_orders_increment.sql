CREATE OR REPLACE TABLE stg_orders_increment AS SELECT * FROM orders_checked('%_increment.csv');
