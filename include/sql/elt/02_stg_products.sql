CREATE OR REPLACE TABLE stg_products AS
WITH t AS (
    SELECT trim(product_id) AS product_id, trim(product_name) AS product_name,
           nullif(trim(category), '') AS category, trim(sub_category) AS sub_category, trim(brand) AS brand,
           try_cast(mrp AS DOUBLE) AS mrp, try_cast(cost_price AS DOUBLE) AS cost_price, trim(unit) AS unit,
           lower(trim(is_perishable)) = 'true' AS is_perishable,
           try_strptime(trim(launch_date), '%Y-%m-%d')::DATE AS launch_date,
           -- a product listed twice: the row tagged "(old)" loses
           row_number() OVER (PARTITION BY trim(product_id)
                              ORDER BY contains(product_name, '(old)'), _row_num) AS _dup_rank,
           _source_file, _run_id, _row_num
    FROM raw_products WHERE _file_hash IN (FROM current_hashes('products.csv'))
)
SELECT *,
    _dup_rank > 1                              AS "c__Critical__Uniqueness__product_id_unique",
    category IS NULL                           AS "c__Critical__Completeness__category_not_null",
    NOT coalesce(mrp > 0, false)               AS "c__Critical__Accuracy__mrp_positive",
    NOT coalesce(cost_price <= mrp, false)     AS "c__Critical__Accuracy__cost_price_le_mrp",
    coalesce(launch_date > getvariable('as_of'), false) AS "c__Warning__Timeliness__launch_date_not_future"
FROM t;
