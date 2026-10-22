CREATE OR REPLACE TABLE stg_stores AS
WITH t AS (
    SELECT trim(store_id) AS store_id, trim(store_name) AS store_name,
           coalesce(nullif(trim(zone), ''), 'Unassigned') AS zone, zone AS _raw_zone,
           trim(area) AS area, trim(pincode) AS pincode,
           try_strptime(trim(open_date), '%Y-%m-%d')::DATE AS open_date, trim(manager_name) AS manager_name,
           try_cast(capacity_orders_per_day AS INTEGER) AS capacity_orders_per_day,
           row_number() OVER (PARTITION BY trim(store_id) ORDER BY _row_num) AS _dup_rank,
           _source_file, _run_id, _row_num
    FROM raw_stores WHERE _file_hash IN (FROM current_hashes('stores.csv'))
)
SELECT * EXCLUDE (_raw_zone),
    _dup_rank > 1                                       AS "c__Critical__Uniqueness__store_id_unique",
    coalesce(nullif(trim(_raw_zone), ''), '') = ''      AS "c__Warning__Completeness__zone_not_null",
    coalesce(capacity_orders_per_day, 0) <= 0           AS "c__Warning__Accuracy__capacity_positive",
    NOT coalesce(regexp_full_match(pincode, '\d{6}'), false) AS "c__Warning__Validity__pincode_6_digits"
FROM t;
