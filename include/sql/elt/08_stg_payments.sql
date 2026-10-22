CREATE OR REPLACE TABLE stg_payments AS
WITH t AS (
    SELECT trim(payment_id) AS payment_id, trim(order_id) AS order_id,
           try_strptime(trim(payment_ts), '%Y-%m-%d %H:%M:%S') AS payment_ts,
           payment_mode AS raw_payment_mode,
           CASE lower(trim(payment_mode)) WHEN 'upi' THEN 'UPI' WHEN 'card' THEN 'Card' WHEN 'wallet' THEN 'Wallet'
                WHEN 'cash on delivery' THEN 'Cash on Delivery' WHEN 'cod' THEN 'Cash on Delivery'
                WHEN 'cashh' THEN 'Cash on Delivery' END AS payment_mode,
           try_cast(amount_paid AS DOUBLE) AS amount_paid, upper(trim(payment_status)) AS payment_status,
           nullif(trim(gateway_ref), '') AS gateway_ref,
           row_number() OVER (PARTITION BY trim(payment_id) ORDER BY _row_num) AS _dup_rank,
           _source_file, _run_id, _row_num
    FROM raw_payments WHERE _file_hash IN (FROM current_hashes('payments.csv'))
)
SELECT * EXCLUDE (raw_payment_mode),
    _dup_rank > 1                                                   AS "c__Critical__Uniqueness__payment_id_unique",
    order_id NOT IN (SELECT order_id FROM stg_orders)               AS "c__Critical__Consistency__order_id_in_orders",
    payment_ts IS NULL                                              AS "c__Critical__Validity__payment_ts_valid_timestamp",
    coalesce(payment_ts::DATE > getvariable('as_of'), false)        AS "c__Critical__Timeliness__payment_ts_not_future",
    payment_mode IS NULL                                            AS "c__Critical__Validity__payment_mode_allowed",
    payment_status NOT IN ('SUCCESS', 'FAILED', 'REFUNDED')         AS "c__Critical__Validity__payment_status_allowed",
    payment_status = 'SUCCESS' AND NOT coalesce(amount_paid > 0, false) AS "c__Critical__Accuracy__success_amount_positive",
    payment_mode IS NOT NULL AND raw_payment_mode <> payment_mode   AS "c__Warning__Consistency__payment_mode_standard_format",
    payment_mode <> 'Cash on Delivery' AND gateway_ref IS NULL      AS "c__Warning__Completeness__gateway_ref_present_for_non_cash"
FROM t;
