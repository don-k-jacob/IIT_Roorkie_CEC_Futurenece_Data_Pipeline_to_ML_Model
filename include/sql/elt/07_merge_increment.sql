-- Upsert on order_id: corrections overwrite the old row (only if the new version passes its checks),
-- new orders are inserted whether they pass or fail (failed ones stay visible with their failure_reason).
MERGE INTO stg_orders AS t
USING (SELECT * FROM stg_orders_increment WHERE _dup_rank = 1) AS s
ON t.order_id = s.order_id AND t._dup_rank = 1
WHEN MATCHED AND s.dq_status = 'PASS' THEN UPDATE
WHEN NOT MATCHED THEN INSERT;
