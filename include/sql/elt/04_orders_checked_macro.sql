-- One set of order rules, used for orders.csv and for every increment file.
CREATE OR REPLACE MACRO orders_checked(file_pattern) AS TABLE
WITH src AS (
    SELECT * FROM raw_orders
    WHERE _file_hash IN (FROM current_hashes(file_pattern)) AND _source_file LIKE file_pattern
),
t AS (
    SELECT trim(order_id) AS order_id, order_ts AS raw_order_ts,
           try_strptime(trim(order_ts), '%Y-%m-%d %H:%M:%S') AS order_ts,
           nullif(trim(customer_id), '') AS customer_id, trim(store_id) AS store_id, trim(product_id) AS product_id,
           try_cast(quantity AS DOUBLE) AS quantity, try_cast(unit_price AS DOUBLE) AS unit_price,
           try_cast(discount_pct AS DOUBLE) AS discount_pct, try_cast(order_amount AS DOUBLE) AS order_amount,
           payment_mode AS raw_payment_mode,
           CASE lower(trim(payment_mode)) WHEN 'upi' THEN 'UPI' WHEN 'card' THEN 'Card' WHEN 'wallet' THEN 'Wallet'
                WHEN 'cash on delivery' THEN 'Cash on Delivery' WHEN 'cod' THEN 'Cash on Delivery'
                WHEN 'cashh' THEN 'Cash on Delivery' END AS payment_mode,
           order_status AS raw_order_status, upper(trim(order_status)) AS order_status, trim(channel) AS channel,
           try_cast(nullif(trim(delivery_minutes), '') AS DOUBLE) AS delivery_minutes,
           row_number() OVER (PARTITION BY trim(order_id) ORDER BY _row_num) AS _dup_rank,
           _source_file, _run_id, _row_num
    FROM src
)
SELECT t.* EXCLUDE (raw_order_ts, raw_payment_mode, raw_order_status),
    order_ts::DATE AS order_date,
    CASE WHEN order_status = 'DELIVERED' THEN order_amount ELSE 0 END AS net_revenue,
    CASE WHEN order_status = 'DELIVERED' THEN delivery_minutes <= 15 END AS within_15_min,
    _dup_rank > 1                                                     AS "c__Critical__Uniqueness__order_id_unique",
    customer_id IS NULL OR lower(customer_id) IN ('n/a', 'null')      AS "c__Critical__Completeness__customer_id_not_null",
    customer_id IS NOT NULL AND customer_id NOT IN (SELECT customer_id FROM stg_customers WHERE dq_status = 'PASS')
                                                                      AS "c__Critical__Consistency__customer_id_in_master",
    product_id NOT IN (SELECT product_id FROM stg_products WHERE dq_status = 'PASS')
                                                                      AS "c__Critical__Consistency__product_id_in_master",
    store_id NOT IN (SELECT store_id FROM stg_stores WHERE dq_status = 'PASS')
                                                                      AS "c__Critical__Consistency__store_id_in_master",
    lower(trim(coalesce(raw_order_ts, ''))) IN ('', 'n/a', 'null')    AS "c__Critical__Completeness__order_ts_not_null",
    lower(trim(coalesce(raw_order_ts, ''))) NOT IN ('', 'n/a', 'null') AND order_ts IS NULL
                                                                      AS "c__Critical__Validity__order_ts_valid_timestamp",
    coalesce(order_ts::DATE > getvariable('as_of'), false)            AS "c__Critical__Timeliness__order_ts_not_future",
    NOT coalesce(quantity > 0, false)                                 AS "c__Critical__Accuracy__quantity_positive",
    NOT coalesce(discount_pct BETWEEN 0 AND 100, false)               AS "c__Critical__Validity__discount_pct_0_to_100",
    NOT coalesce(abs(round(quantity * unit_price * (1 - discount_pct / 100), 2) - order_amount) <= 0.01, false)
                                                                      AS "c__Critical__Accuracy__order_amount_matches_formula",
    order_status NOT IN ('DELIVERED', 'CANCELLED', 'RETURNED')        AS "c__Critical__Validity__order_status_allowed",
    payment_mode IS NULL                                              AS "c__Critical__Validity__payment_mode_allowed",
    order_status = 'DELIVERED' AND delivery_minutes IS NULL           AS "c__Critical__Completeness__delivered_has_delivery_minutes",
    coalesce(delivery_minutes >= 120 OR delivery_minutes < 0, false)  AS "c__Critical__Accuracy__delivery_minutes_below_120",
    payment_mode IS NOT NULL AND raw_payment_mode <> payment_mode     AS "c__Warning__Consistency__payment_mode_standard_format",
    raw_order_status <> order_status                                  AS "c__Warning__Consistency__order_status_upper_case",
    coalesce(NOT delivery_minutes BETWEEN 8 AND 35, false)            AS "c__Warning__Accuracy__delivery_minutes_8_to_35",
    coalesce(abs(unit_price - p.mrp) > 0.01, false)                   AS "c__Warning__Accuracy__unit_price_equals_mrp"
FROM t LEFT JOIN (SELECT product_id, mrp FROM stg_products WHERE dq_status = 'PASS') p USING (product_id);
