-- PII is masked here: raw email / phone / full name never leave the raw layer.
CREATE OR REPLACE TABLE stg_customers AS
WITH t AS (
    SELECT trim(customer_id) AS customer_id, full_name,
           CASE WHEN lower(trim(email)) IN ('', 'n/a', 'na', 'null', 'none') THEN NULL ELSE trim(email) END AS email,
           trim(phone) AS phone, nullif(trim(city), '') AS city, trim(area) AS area, trim(pincode) AS raw_pincode,
           try_strptime(trim(signup_date), '%Y-%m-%d')::DATE AS signup_date,
           loyalty_tier AS raw_tier, is_active,
           row_number() OVER (PARTITION BY trim(customer_id) ORDER BY _row_num DESC) AS _dup_rank,
           _source_file, _run_id, _row_num
    FROM raw_customers WHERE _file_hash IN (FROM current_hashes('customers.csv'))
)
SELECT customer_id,
    CASE WHEN len(string_split(trim(full_name), ' ')) > 1
         THEN string_split(trim(full_name), ' ')[1] || ' ' || left(string_split(trim(full_name), ' ')[-1], 1) || '.'
         ELSE trim(full_name) END                                        AS customer_name,
    CASE WHEN email LIKE '%@%' THEN left(email, 2) || '***@' || split_part(email, '@', 2)
         WHEN email IS NOT NULL THEN left(email, 2) || '***' END           AS email_masked,
    CASE WHEN length(regexp_replace(phone, '\D', '', 'g')) >= 4
         THEN left(regexp_replace(phone, '\D', '', 'g'), 2)
              || repeat('*', length(regexp_replace(phone, '\D', '', 'g')) - 4)
              || right(regexp_replace(phone, '\D', '', 'g'), 2) END       AS phone_masked,
    city, area,
    CASE WHEN regexp_full_match(raw_pincode, '560\d{3}') THEN raw_pincode END AS pincode,
    signup_date,
    CASE lower(trim(raw_tier)) WHEN 'bronze' THEN 'Bronze' WHEN 'silver' THEN 'Silver'
         WHEN 'gold' THEN 'Gold' WHEN 'platinum' THEN 'Platinum' END       AS loyalty_tier,
    upper(trim(is_active)) = 'Y'                                           AS is_active,
    _dup_rank, _source_file, _run_id, _row_num,
    _dup_rank > 1                                                          AS "c__Critical__Uniqueness__customer_id_unique",
    signup_date IS NULL                                                    AS "c__Critical__Validity__signup_date_valid",
    coalesce(signup_date > getvariable('as_of'), false)                    AS "c__Critical__Timeliness__signup_date_not_future",
    email IS NULL                                                          AS "c__Warning__Completeness__email_not_null",
    email IS NOT NULL AND NOT regexp_full_match(email, '[^@\s]+@[^@\s]+\.[A-Za-z]{2,}') AS "c__Warning__Validity__email_format",
    NOT coalesce(regexp_full_match(phone, '\d{10}'), false)               AS "c__Warning__Validity__phone_10_digits",
    NOT coalesce(regexp_full_match(raw_pincode, '560\d{3}'), false)       AS "c__Warning__Validity__pincode_6_digits",
    city IS NULL                                                           AS "c__Warning__Completeness__city_not_null",
    raw_tier NOT IN ('Bronze', 'Silver', 'Gold', 'Platinum')               AS "c__Warning__Consistency__loyalty_tier_casing",
    lower(trim(raw_tier)) NOT IN ('bronze', 'silver', 'gold', 'platinum')  AS "c__Critical__Validity__loyalty_tier_allowed"
FROM t;
