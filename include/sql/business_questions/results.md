# Business questions: results from both pipelines

Warehouse built from all six files (September + the 1 Oct increment), each DAG run twice.

**Q1. Net revenue by zone (ETL)**

| zone | net_revenue |
|---|---|
| East | 293090.4 |
| West | 289473.1 |
| South | 240159.05 |
| North | 229879.45 |
| Unassigned | 76474.45 |

**Q1. Net revenue by zone (ELT)**

| zone | net_revenue |
|---|---|
| East | 293090.4 |
| West | 289473.1 |
| South | 240159.05 |
| North | 229879.45 |
| Unassigned | 76474.45 |

**Q1. Net revenue by store (ETL | ELT)**

| store_id | store_name | zone | etl_net_revenue | elt_net_revenue |
|---|---|---|---|---|
| S06 | NammaMart Banashankari | South | 87573.6 | 87573.6 |
| S05 | NammaMart JP Nagar | South | 82229.75 | 82229.75 |
| S01 | NammaMart Hebbal | North | 80069.0 | 80069.0 |
| S10 | NammaMart Marathahalli | East | 79973.45 | 79973.45 |
| S13 | NammaMart Malleshwaram | West | 77848.6 | 77848.6 |
| S15 | NammaMart Basaveshwaranagar | West | 76634.85 | 76634.85 |
| S03 | NammaMart RT Nagar | North | 76506.0 | 76506.0 |
| S07 | NammaMart BTM Layout | Unassigned | 76474.45 | 76474.45 |
| S08 | NammaMart Whitefield | East | 75466.25 | 75466.25 |
| S11 | NammaMart HSR Layout | East | 74575.1 | 74575.1 |
| S14 | NammaMart Vijayanagar | West | 73946.45 | 73946.45 |
| S02 | NammaMart Yelahanka | North | 73304.45 | 73304.45 |
| S04 | NammaMart Jayanagar | South | 70355.7 | 70355.7 |
| S09 | NammaMart Indiranagar | East | 63075.6 | 63075.6 |
| S12 | NammaMart Rajajinagar | West | 61043.2 | 61043.2 |

**Q1. Daily net revenue, first 5 days by zone (ELT mart_daily_store_kpis)**

| order_date | zone | net_revenue |
|---|---|---|
| 2026-09-01 00:00:00 | East | 9337.05 |
| 2026-09-01 00:00:00 | North | 8380.15 |
| 2026-09-01 00:00:00 | South | 3615.0 |
| 2026-09-01 00:00:00 | Unassigned | 5844.75 |
| 2026-09-01 00:00:00 | West | 5790.15 |
| 2026-09-02 00:00:00 | East | 7984.6 |
| 2026-09-02 00:00:00 | North | 3573.8 |
| 2026-09-02 00:00:00 | South | 12423.0 |
| 2026-09-02 00:00:00 | Unassigned | 240.0 |
| 2026-09-02 00:00:00 | West | 9008.35 |

**Q2. Revenue and gross margin by category (ETL)**

| category | revenue | cost | gross_margin | margin_pct |
|---|---|---|---|---|
| Staples | 264456.9 | 198021.62 | 66435.28 | 25.1 |
| Household | 210607.95 | 156439.04 | 54168.91 | 25.7 |
| Personal Care | 208774.7 | 162065.13 | 46709.57 | 22.4 |
| Dairy & Bakery | 177404.85 | 130204.03 | 47200.82 | 26.6 |
| Snacks & Beverages | 174863.6 | 133465.47 | 41398.13 | 23.7 |
| Fruits & Vegetables | 92968.45 | 70950.23 | 22018.22 | 23.7 |

**Q2. Revenue and gross margin by category (ELT)**

| category | revenue | cost | gross_margin | margin_pct |
|---|---|---|---|---|
| Staples | 264456.9 | 198021.62 | 66435.28 | 25.1 |
| Household | 210607.95 | 156439.04 | 54168.91 | 25.7 |
| Personal Care | 208774.7 | 162065.13 | 46709.57 | 22.4 |
| Dairy & Bakery | 177404.85 | 130204.03 | 47200.82 | 26.6 |
| Snacks & Beverages | 174863.6 | 133465.47 | 41398.13 | 23.7 |
| Fruits & Vegetables | 92968.45 | 70950.23 | 22018.22 | 23.7 |

**Q3. Delivery time and % within 15 min by store (ETL | ELT)**

| store_id | store_name | etl_avg_min | etl_pct_15 | elt_avg_min | elt_pct_15 |
|---|---|---|---|---|---|
| S01 | NammaMart Hebbal | 20.6 | 31.2 | 20.6 | 31.2 |
| S02 | NammaMart Yelahanka | 21.0 | 30.9 | 21.0 | 30.9 |
| S03 | NammaMart RT Nagar | 20.7 | 29.2 | 20.7 | 29.2 |
| S04 | NammaMart Jayanagar | 21.6 | 26.9 | 21.6 | 26.9 |
| S05 | NammaMart JP Nagar | 21.2 | 29.1 | 21.2 | 29.1 |
| S06 | NammaMart Banashankari | 22.3 | 22.1 | 22.3 | 22.1 |
| S07 | NammaMart BTM Layout | 21.1 | 33.6 | 21.1 | 33.6 |
| S08 | NammaMart Whitefield | 20.6 | 35.5 | 20.6 | 35.5 |
| S09 | NammaMart Indiranagar | 21.1 | 27.6 | 21.1 | 27.6 |
| S10 | NammaMart Marathahalli | 21.9 | 27.0 | 21.9 | 27.0 |
| S11 | NammaMart HSR Layout | 20.9 | 28.3 | 20.9 | 28.3 |
| S12 | NammaMart Rajajinagar | 22.0 | 23.7 | 22.0 | 23.7 |
| S13 | NammaMart Malleshwaram | 21.8 | 27.0 | 21.8 | 27.0 |
| S14 | NammaMart Vijayanagar | 21.5 | 31.5 | 21.5 | 31.5 |
| S15 | NammaMart Basaveshwaranagar | 22.3 | 21.0 | 22.3 | 21.0 |

**Q4. Revenue by payment mode (ETL | ELT)**

| payment_mode | etl_net_revenue | elt_net_revenue |
|---|---|---|
| UPI | 598618.2 | 598618.2 |
| Card | 231787.85 | 231787.85 |
| Cash on Delivery | 169692.6 | 169692.6 |
| Wallet | 128977.8 | 128977.8 |

**Q4. Amount that doesn't reconcile with the gateway (ETL)**

| reason | rows | amount |
|---|---|---|
| payment_for_quarantined_order | 206 | 158276.73 |
| payment_not_in_file_yet | 136 | 72191.2 |
| delivered_payment_failed | 42 | 25722.25 |
| delivered_no_payment | 27 | 16438.3 |
| payment_without_order | 8 | 4580.57 |
| returned_not_refunded | 10 | 812.0 |
| amount_mismatch | 12 | 585.0 |

**Q4. Amount that doesn't reconcile with the gateway (ELT)**

| reason | rows | amount |
|---|---|---|
| payment_for_quarantined_order | 206 | 158276.73 |
| payment_not_in_file_yet | 136 | 72191.2 |
| delivered_payment_failed | 42 | 25722.25 |
| delivered_no_payment | 27 | 16438.3 |
| payment_without_order | 8 | 4580.57 |
| returned_not_refunded | 10 | 812.0 |
| amount_mismatch | 12 | 585.0 |

**Q5. Top 10 customers by spend (ETL)**

| customer_id | customer_name | loyalty_tier | email_masked | phone_masked | total_spend |
|---|---|---|---|---|---|
| C00136 | Sanjay B. | Bronze | sa***@example.com | 96******88 | 8738.1 |
| C00236 | Sneha N. | Platinum | sn***@example.com | 90******01 | 7831.8 |
| C00115 | Sanjay K. | Bronze | sa***@example.com | 96******85 | 7337.7 |
| C00310 | Kiran P. | Bronze | ki***@example | 91******35 | 7258.95 |
| C00265 | Vikram H. | Gold | vi***@example.com | 91******69 | 7151.3 |
| C00338 | Bhavana I. | Silver | bh***@example.com | 94******05 | 6848.55 |
| C00283 | Nikhil R. | Bronze | ni***@example.com | 91******43 | 6766.4 |
| C00357 | Arjun N. | Bronze | ar***@example.com | 93*****12 | 6637.9 |
| C00209 | Kavya P. | Platinum | ka***@example.com | 98******97 | 6519.4 |
| C00072 | Nandini M. | Silver | na***@example.com | 98******05 | 6433.95 |

**Q5. Top 10 customers by spend (ELT)**

| customer_id | customer_name | loyalty_tier | email_masked | phone_masked | total_spend |
|---|---|---|---|---|---|
| C00136 | Sanjay B. | Bronze | sa***@example.com | 96******88 | 8738.1 |
| C00236 | Sneha N. | Platinum | sn***@example.com | 90******01 | 7831.8 |
| C00115 | Sanjay K. | Bronze | sa***@example.com | 96******85 | 7337.7 |
| C00310 | Kiran P. | Bronze | ki***@example | 91******35 | 7258.95 |
| C00265 | Vikram H. | Gold | vi***@example.com | 91******69 | 7151.3 |
| C00338 | Bhavana I. | Silver | bh***@example.com | 94******05 | 6848.55 |
| C00283 | Nikhil R. | Bronze | ni***@example.com | 91******43 | 6766.4 |
| C00357 | Arjun N. | Bronze | ar***@example.com | 93*****12 | 6637.9 |
| C00209 | Kavya P. | Platinum | ka***@example.com | 98******97 | 6519.4 |
| C00072 | Nandini M. | Silver | na***@example.com | 98******05 | 6433.95 |

**Q6. Rows rejected in the latest run, by file and reason**

| dag_id | file | reason | rows_failed |
|---|---|---|---|
| nammamart_elt_yourname | customers | customer_id_unique | 5 |
| nammamart_elt_yourname | customers | signup_date_not_future | 3 |
| nammamart_elt_yourname | orders | product_id_in_master | 135 |
| nammamart_elt_yourname | orders | customer_id_not_null | 18 |
| nammamart_elt_yourname | orders | order_amount_matches_formula | 18 |
| nammamart_elt_yourname | orders | customer_id_in_master | 18 |
| nammamart_elt_yourname | orders | order_id_unique | 12 |
| nammamart_elt_yourname | orders | quantity_positive | 10 |
| nammamart_elt_yourname | orders | delivered_has_delivery_minutes | 8 |
| nammamart_elt_yourname | orders | order_ts_not_future | 7 |
| nammamart_elt_yourname | orders | delivery_minutes_below_120 | 6 |
| nammamart_elt_yourname | orders | store_id_in_master | 5 |
| nammamart_elt_yourname | orders | order_ts_valid_timestamp | 4 |
| nammamart_elt_yourname | orders | order_status_allowed | 3 |
| nammamart_elt_yourname | orders | discount_pct_0_to_100 | 3 |
| nammamart_elt_yourname | orders | order_ts_not_null | 2 |
| nammamart_elt_yourname | orders_increment | product_id_in_master | 14 |
| nammamart_elt_yourname | orders_increment | customer_id_in_master | 1 |
| nammamart_elt_yourname | payments | success_amount_positive | 10 |
| nammamart_elt_yourname | payments | order_id_in_orders | 8 |
| nammamart_elt_yourname | payments | payment_ts_not_future | 7 |
| nammamart_elt_yourname | payments | payment_id_unique | 4 |
| nammamart_elt_yourname | products | cost_price_le_mrp | 5 |
| nammamart_elt_yourname | products | category_not_null | 3 |
| nammamart_elt_yourname | products | product_id_unique | 2 |
| nammamart_elt_yourname | products | mrp_positive | 1 |
| nammamart_etl_yourname | customers | customer_id_unique | 5 |
| nammamart_etl_yourname | customers | signup_date_not_future | 3 |
| nammamart_etl_yourname | orders | product_id_in_master | 135 |
| nammamart_etl_yourname | orders | customer_id_in_master | 18 |
| nammamart_etl_yourname | orders | customer_id_not_null | 18 |
| nammamart_etl_yourname | orders | order_amount_matches_formula | 18 |
| nammamart_etl_yourname | orders | order_id_unique | 12 |
| nammamart_etl_yourname | orders | quantity_positive | 10 |
| nammamart_etl_yourname | orders | delivered_has_delivery_minutes | 8 |
| nammamart_etl_yourname | orders | order_ts_not_future | 7 |
| nammamart_etl_yourname | orders | delivery_minutes_below_120 | 6 |
| nammamart_etl_yourname | orders | store_id_in_master | 5 |
| nammamart_etl_yourname | orders | order_ts_valid_timestamp | 4 |
| nammamart_etl_yourname | orders | order_status_allowed | 3 |
| nammamart_etl_yourname | orders | discount_pct_0_to_100 | 3 |
| nammamart_etl_yourname | orders | order_ts_not_null | 2 |
| nammamart_etl_yourname | orders_2026-10-01_increment | product_id_in_master | 14 |
| nammamart_etl_yourname | orders_2026-10-01_increment | customer_id_in_master | 1 |
| nammamart_etl_yourname | payments | success_amount_positive | 10 |
| nammamart_etl_yourname | payments | order_id_in_orders | 8 |
| nammamart_etl_yourname | payments | payment_ts_not_future | 7 |
| nammamart_etl_yourname | payments | payment_id_unique | 4 |
| nammamart_etl_yourname | products | cost_price_le_mrp | 5 |
| nammamart_etl_yourname | products | category_not_null | 3 |
| nammamart_etl_yourname | products | product_id_unique | 2 |
| nammamart_etl_yourname | products | mrp_positive | 1 |

**Q6. Rows rejected in the latest run, by file (row counts)**

| pipeline | where_ | rows |
|---|---|---|
| ETL | see include/quarantine/<name>/ | <NA> |
| ELT | stg_stores | 0 |
| ELT | stg_products | 10 |
| ELT | stg_customers | 8 |
| ELT | stg_orders (incl. increment) | 247 |
| ELT | stg_payments | 29 |

**pipeline_runs**

| dag_id | run_id | start_time | end_time | rows_extracted | rows_loaded | rows_quarantined | status |
|---|---|---|---|---|---|---|---|
| nammamart_etl_yourname | local__2026-10-22T11:36:16.356616 | 2026-10-22 11:36:16.356635 | 2026-10-22 11:36:16.809069 | 5372 | 2324 | 295 | success |
| nammamart_elt_yourname | local__2026-10-22T11:36:16.814752 | 2026-10-22 11:36:16.814775 | 2026-10-22 11:36:17.550740 | 5372 | 2315 | 295 | success |
| nammamart_etl_yourname | local__2026-10-22T11:36:18.683351 | 2026-10-22 11:36:18.683369 | 2026-10-22 11:36:18.980088 | 5372 | 2324 | 295 | success |
| nammamart_elt_yourname | local__2026-10-22T11:36:18.987397 | 2026-10-22 11:36:18.987420 | 2026-10-22 11:36:19.573779 | 5372 | 2315 | 295 | success |

**Re-run check: fact row counts**

| etl_fact_orders | elt_stg_orders_pass | raw_orders | raw_load_log_rows |
|---|---|---|---|
| 2315 | 2315 | 2572 | 12 |

**Increment corrections: final status of the 10 corrected orders**

| order_id | etl_status | elt_status | elt_dq | failure_reason |
|---|---|---|---|---|
| ORD000017 | RETURNED | RETURNED | PASS | nan |
| ORD000271 | RETURNED | RETURNED | PASS | nan |
| ORD000332 | RETURNED | RETURNED | PASS | nan |
| ORD000337 | RETURNED | RETURNED | PASS | nan |
| ORD000584 | RETURNED | RETURNED | PASS | nan |
| ORD000708 | RETURNED | RETURNED | PASS | nan |
| ORD000822 | nan | DELIVERED | FAIL | product_id_in_master |
| ORD001025 | RETURNED | RETURNED | PASS | nan |
| ORD001067 | RETURNED | RETURNED | PASS | nan |
| ORD001990 | RETURNED | RETURNED | PASS | nan |

**Totals: ETL vs ELT**

| etl_net_revenue | elt_net_revenue | etl_september | elt_september |
|---|---|---|---|
| 1129076.45 | 1129076.45 | 1056885.25 | 1056885.25 |

**dq_results sample (latest ETL run, failing checks)**

| check_name | dimension | severity | rows_checked | rows_failed | status |
|---|---|---|---|---|---|
| customers.customer_id_unique | Uniqueness | Critical | 405 | 5 | FAIL |
| customers.signup_date_not_future | Timeliness | Critical | 405 | 3 | FAIL |
| orders.customer_id_in_master | Consistency | Critical | 2412 | 18 | FAIL |
| orders.customer_id_not_null | Completeness | Critical | 2412 | 18 | FAIL |
| orders.delivered_has_delivery_minutes | Completeness | Critical | 2412 | 8 | FAIL |
| orders.delivery_minutes_below_120 | Accuracy | Critical | 2412 | 6 | FAIL |
| orders.discount_pct_0_to_100 | Validity | Critical | 2412 | 3 | FAIL |
| orders.order_amount_matches_formula | Accuracy | Critical | 2412 | 18 | FAIL |
| orders.order_id_unique | Uniqueness | Critical | 2412 | 12 | FAIL |
| orders.order_status_allowed | Validity | Critical | 2412 | 3 | FAIL |
| orders.order_ts_not_future | Timeliness | Critical | 2412 | 7 | FAIL |
| orders.order_ts_not_null | Completeness | Critical | 2412 | 2 | FAIL |
| orders.order_ts_valid_timestamp | Validity | Critical | 2412 | 4 | FAIL |
| orders.product_id_in_master | Consistency | Critical | 2412 | 135 | FAIL |
| orders.quantity_positive | Accuracy | Critical | 2412 | 10 | FAIL |
| orders.store_id_in_master | Consistency | Critical | 2412 | 5 | FAIL |
| orders_2026-10-01_increment.customer_id_in_master | Consistency | Critical | 160 | 1 | FAIL |
| orders_2026-10-01_increment.product_id_in_master | Consistency | Critical | 160 | 14 | FAIL |
| payments.order_id_in_orders | Consistency | Critical | 2228 | 8 | FAIL |
| payments.payment_id_unique | Uniqueness | Critical | 2228 | 4 | FAIL |
| payments.payment_ts_not_future | Timeliness | Critical | 2228 | 7 | FAIL |
| payments.success_amount_positive | Accuracy | Critical | 2228 | 10 | FAIL |
| products.category_not_null | Completeness | Critical | 152 | 3 | FAIL |
| products.cost_price_le_mrp | Accuracy | Critical | 152 | 5 | FAIL |
| products.mrp_positive | Accuracy | Critical | 152 | 1 | FAIL |
| products.product_id_unique | Uniqueness | Critical | 152 | 2 | FAIL |
| customers.city_not_null | Completeness | Warning | 405 | 6 | WARN |
| customers.email_format | Validity | Warning | 405 | 8 | WARN |
| customers.email_not_null | Completeness | Warning | 405 | 4 | WARN |
| customers.loyalty_tier_casing | Consistency | Warning | 405 | 8 | WARN |
| customers.phone_10_digits | Validity | Warning | 405 | 7 | WARN |
| customers.pincode_6_digits | Validity | Warning | 405 | 5 | WARN |
| orders.delivery_minutes_8_to_35 | Accuracy | Warning | 2412 | 6 | WARN |
| orders.order_status_upper_case | Consistency | Warning | 2412 | 5 | WARN |
| orders.payment_mode_standard_format | Consistency | Warning | 2412 | 10 | WARN |
| payments.payment_mode_standard_format | Consistency | Warning | 2228 | 10 | WARN |
| stores.capacity_positive | Accuracy | Warning | 15 | 1 | WARN |
| stores.zone_not_null | Completeness | Warning | 15 | 1 | WARN |
