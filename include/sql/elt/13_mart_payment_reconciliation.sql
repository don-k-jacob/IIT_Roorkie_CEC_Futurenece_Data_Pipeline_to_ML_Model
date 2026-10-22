-- Same rules as etl_payment_reconciliation (template in include/nammamart/etl.py).
CREATE OR REPLACE TABLE mart_payment_reconciliation AS
WITH pay AS (
    SELECT order_id,
           count(*) FILTER (WHERE payment_status = 'SUCCESS')  AS n_success,
           sum(amount_paid) FILTER (WHERE payment_status = 'SUCCESS') AS amount_success,
           bool_or(payment_status = 'FAILED')   AS any_failed,
           bool_or(payment_status = 'REFUNDED') AS any_refunded,
           string_agg(payment_id, ',' ORDER BY payment_id) AS payment_ids
    FROM (SELECT * FROM stg_payments WHERE dq_status = 'PASS') GROUP BY order_id
),
o AS (
    SELECT f.order_id, f.order_ts, f.order_status, f.order_amount, p.payment_ids, p.n_success, p.amount_success,
           p.any_failed, p.any_refunded
    FROM (SELECT * FROM stg_orders WHERE dq_status = 'PASS') f LEFT JOIN pay p USING (order_id)
),
mismatches AS (
    SELECT order_id, payment_ids AS payment_id, order_status, order_amount, amount_success AS amount_paid,
        CASE
            WHEN payment_ids IS NULL AND order_ts > (SELECT max(payment_ts) FROM (SELECT * FROM stg_payments WHERE dq_status = 'PASS'))
                THEN 'payment_not_in_file_yet'
            WHEN order_status = 'DELIVERED' AND coalesce(n_success, 0) = 0 AND any_failed THEN 'delivered_payment_failed'
            WHEN order_status = 'DELIVERED' AND coalesce(n_success, 0) = 0 THEN 'delivered_no_payment'
            WHEN order_status = 'DELIVERED' AND n_success > 1 THEN 'multiple_success_payments'
            WHEN order_status = 'DELIVERED' AND abs(amount_success - order_amount) > 0.01 THEN 'amount_mismatch'
            WHEN order_status = 'RETURNED' AND NOT coalesce(any_refunded, false) THEN 'returned_not_refunded'
            WHEN order_status = 'CANCELLED' AND coalesce(n_success, 0) > 0 THEN 'cancelled_but_paid'
        END AS reason
    FROM o
),
orphan AS (
    SELECT order_id, payment_id, NULL AS order_status, NULL::DOUBLE AS order_amount, amount_paid,
           CASE WHEN order_id IN (SELECT order_id FROM stg_orders)
                THEN 'payment_for_quarantined_order' ELSE 'payment_without_order' END AS reason
    FROM (SELECT * FROM stg_payments WHERE _dup_rank = 1)
    WHERE payment_status = 'SUCCESS' AND order_id NOT IN (SELECT order_id FROM (SELECT * FROM stg_orders WHERE dq_status = 'PASS'))
)
SELECT *, round(coalesce(amount_paid, 0) - coalesce(CASE WHEN order_status = 'CANCELLED' THEN 0 ELSE order_amount END, 0), 2)
          AS difference
FROM (SELECT * FROM mismatches WHERE reason IS NOT NULL UNION ALL SELECT * FROM orphan)
ORDER BY reason, order_id;
