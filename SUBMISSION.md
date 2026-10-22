# NammaMart ETL & ELT — Submission

## Part 0: Discovery and data profiling

**How:** `python3 include/profiling/profile_nammamart.py > include/profiling/data_profile.md` (standard library only).
The full output, with every row key, is in [`include/profiling/data_profile.md`](include/profiling/data_profile.md).
Timeliness checks use **1 Oct 2026** as "today" (the data covers September; the increment file is 1 Oct).

### Headline numbers

| File | Rows | Issues found |
|---|---|---|
| orders.csv | 2,412 | 15 |
| payments.csv | 2,228 | 8 |
| customers.csv | 405 | 8 |
| products.csv | 152 | 4 |
| stores.csv | 15 | 2 |
| orders_2026-10-01_increment.csv | 160 | 1 (inherited from products) |

- **102 of 2,412 orders (4.2%)** fail at least one of the Critical order checks (#1–15).
- Summing every DELIVERED `order_amount`, as the current Excel report does, gives **₹12,19,020.88**. After the Critical checks (with casing standardised) it's **₹11,35,628.80**. September revenue is **overstated by ₹83,392.08 (7.3%)**:

  | Cause | Revenue it adds |
  |---|---|
  | order_amount 10× too high | ₹39,345.50 |
  | Duplicate order rows | ₹8,244.10 |
  | Null customer | ₹7,880.05 |
  | Missing / impossible delivery time | ₹7,257.70 |
  | order_amount 1.5× | ₹6,753.15 |
  | Unknown product or store | ₹6,720.70 |
  | Bad or future timestamp | ₹6,518.00 |
  | Discount over 100% | ₹3,447.20 |
  | order_amount 0.5× | ₹1,181.68 |
  | Quantity ≤ 0 (reduces revenue) | −₹3,956.00 |

  Each bad row is counted once, under its first failing check in the order above.
- Only **2,099 orders** are DELIVERED with a SUCCESS payment. 44 DELIVERED orders have a FAILED payment and 27 have no payment at all, which is why order revenue never matches the gateway.

### Data Issues Log

Severity: **Critical** = quarantine the row. **Warning** = load the row, log the check in `dq_results`.

| # | File | Row key(s) | Column | Problem | Dimension | Proposed rule | Severity |
|---|---|---|---|---|---|---|---|
| 1 | orders | 12 ids, e.g. ORD000539, ORD001110 (24 rows) | order_id | Same order appears twice; every column identical | Uniqueness | Keep the first copy, quarantine the rest as `duplicate order_id` | Critical |
| 2 | orders | 18 rows, e.g. ORD000580, ORD002255 | customer_id | Null (16 DELIVERED, 1 RETURNED, 1 CANCELLED) | Completeness | `customer_id` not null | Critical |
| 3 | orders | ORD000070, ORD000134, ORD000596 … (9) | product_id | References P9xxx ids that don't exist in products | Consistency | `product_id` exists in products | Critical |
| 4 | orders | ORD001046, ORD001275, ORD001492 (S17), ORD001799 (S99), ORD002126 (S00) | store_id | Store not in store master | Consistency | `store_id` exists in stores | Critical |
| 5 | orders | ORD000403 (`N/A`), ORD000362 (blank) | order_ts | Missing timestamp | Completeness | `order_ts` not null | Critical |
| 6 | orders | ORD000534, ORD001610 (`2026-13-05`), ORD000946, ORD002012 (`31/09/2026 10:00`) | order_ts | Month 13; wrong format and 31 September doesn't exist | Validity | Parses as `YYYY-MM-DD HH:MM:SS` | Critical |
| 7 | orders | ORD001089, ORD001693 (21 Oct), ORD001121, ORD001965 (2 Nov), ORD001725, ORD001765, ORD002119 (1 Jan 2027) | order_ts | Future-dated | Timeliness | `order_ts` ≤ run date | Critical |
| 8 | orders | ORD000099, ORD000469, ORD001724, ORD002360 (qty 0); ORD000462, ORD000867, ORD001124, ORD001296, ORD001384, ORD001459 (negative) | quantity | Zero or negative quantity, giving zero/negative revenue | Accuracy | `quantity > 0` | Critical |
| 9 | orders | ORD001468 (120), ORD001237 (150), ORD002103 (250) | discount_pct | Discount over 100% | Validity | 0 ≤ `discount_pct` ≤ 100 | Critical |
| 10 | orders | 15 rows: 6 at 10× (e.g. ORD001624 ₹9,576 vs ₹957.60), 5 at 1.5×, 4 at 0.5× | order_amount | Doesn't match `qty × price × (1 − disc/100)` | Accuracy | Abs. difference ≤ ₹0.01 | Critical |
| 11 | orders | ORD000159, ORD000433, ORD000691, ORD000934 (`upi`), ORD001874, ORD002356 (`UPI␠`), ORD001364 (`CARD`), ORD001640 (`cod`), ORD001414, ORD001812 (`Cashh`) | payment_mode | Casing, trailing space, abbreviations, typo | Validity | Trim + map to UPI / Card / Cash on Delivery / Wallet; quarantine anything unmappable | Warning (standardised) |
| 12 | orders | ORD000153, ORD001066 | order_status | `delivered` lower-case | Consistency | Upper-case before validating | Warning (standardised) |
| 13 | orders | ORD000500, ORD001637, ORD001970 | order_status | `Pending??`, not an allowed status (yet each has a SUCCESS payment) | Validity | Status in {DELIVERED, CANCELLED, RETURNED} | Critical |
| 14 | orders | ORD000326, ORD000731, ORD000878 … (8) | delivery_minutes | DELIVERED with no delivery time | Completeness | DELIVERED ⇒ `delivery_minutes` not null | Critical |
| 15 | orders | ORD000424, ORD001037, ORD002101 (480), ORD000020, ORD001104 (900), ORD000455 (1440) | delivery_minutes | Hours/days entered as minutes; distorts the 10-minute KPI | Accuracy | `delivery_minutes` < 120 | Critical |
| 16 | payments | PAY0000509, PAY0000755, PAY0001651, PAY0002000 | payment_id | Exact duplicate rows (also duplicates `gateway_ref`) | Uniqueness | Keep first copy | Critical |
| 17 | payments | PAY0002217 – PAY0002224 (8) | order_id | Point to ORD9xxxxx orders that don't exist. All share one timestamp (18 Sep 14:22:10), all UPI, ₹4,580.57 total. Looks like gateway **test transactions** | Consistency | `order_id` exists in orders | Critical |
| 18 | payments | PAY0000116, PAY0000751, PAY0001568, PAY0002175 … (10) | amount_paid | Zero or negative SUCCESS payments (9 of 10 exactly mirror the bad quantities in #8) | Accuracy | SUCCESS ⇒ `amount_paid > 0` | Critical |
| 19 | payments | PAY0000044, PAY0000354, PAY0000909 … (14) | amount_paid | SUCCESS payment short of `order_amount` by exactly ₹10 / 25 / 50 / 100 | Consistency | Paid = order amount; mismatch → reconciliation table | Warning |
| 20 | payments | PAY0000127, PAY0000267, PAY0000337, PAY0000396, PAY0001037, PAY0001488, PAY0001908 | payment_ts | Future-dated (they belong to the future orders in #7) | Timeliness | `payment_ts` ≤ run date | Critical |
| 21 | payments | 10 rows, same variants as #11 | payment_mode | Non-standard values | Validity | Same mapping as #11 | Warning (standardised) |
| 22 | payments ↔ orders | 44 orders, e.g. ORD000106, ORD000398; plus 27 DELIVERED and 1 RETURNED (ORD001675) with no payment row | payment_status | Order DELIVERED but payment FAILED or missing | Consistency | Every DELIVERED order has one SUCCESS payment; else → reconciliation table | Warning |
| 23 | payments | PAY0000522, PAY0000044 (`Cashh`), PAY0001954 (`cod`) | gateway_ref | Cash payments that *have* a gateway ref (all 301 genuine COD rows have none) | Consistency | Ask the client (Q4) | Warning |
| 24 | customers | C00036, C00103, C00226, C00252, C00313 | customer_id | Appears twice with a different phone (4 also differ in area/pincode); no `updated_at` to pick the current row | Uniqueness | One row per `customer_id`; keep last, quarantine the other | Critical |
| 25 | customers | C00062, C00063, C00067, C00112, C00307, C00310, C00363, C00392 | email | Missing the `@`, or the domain has no `.com` | Validity | Matches `^[^@\s]+@[^@\s]+\.[a-z]{2,}$` | Warning |
| 26 | customers | C00045, C00193, C00327, C00337 | email | `N/A` | Completeness | Treat `N/A` as null | Warning |
| 27 | customers | C00095, C00130, C00151, C00240, C00290, C00339, C00357 | phone | 7–9 digits instead of 10 | Validity | Exactly 10 digits | Warning |
| 28 | customers | C00083, C00132, C00166 (`5600XX`); C00342, C00395 (`000000`) | pincode | Placeholder / not a Bengaluru pincode | Validity | 6 digits, starts with 560 | Warning |
| 29 | customers | C00142, C00219, C00233, C00328, C00355, C00394 | city | Blank (all others are Bengaluru) | Completeness | `city` not null | Warning |
| 30 | customers | C00038 (2026-12-20), C00398 (2026-11-12), C00400 (2027-01-05) | signup_date | Future signup date; these customers placed 18 September orders "before signing up" | Timeliness | `signup_date` ≤ run date | Critical* |
| 31 | customers | C00031, C00032, C00196 (`bronze`), C00092, C00133, C00136 (`BRONZE`), C00171, C00199 (`SILVER`) | loyalty_tier | Inconsistent casing | Consistency | Title-case to Bronze / Silver / Gold / Platinum | Warning (standardised) |
| 32 | products | P0030, P0140 | product_id | Appears twice; the second row is named "… (old)" with a lower MRP. Orders are priced at the newer MRP | Uniqueness | Keep the row without "(old)" | Critical |
| 33 | products | P0051, P0060, P0068 | category | Blank | Completeness | `category` not null | Critical |
| 34 | products | P0109 | mrp | −203.0 (orders sell it at ₹203, so the sign is flipped). Used by 11 Sept orders and 1 increment order | Accuracy | `mrp > 0` | Critical |
| 35 | products | P0019, P0073, P0074, P0117 | cost_price | Cost is exactly 1.2× MRP, so every sale shows a loss | Accuracy | `cost_price ≤ mrp` | Critical |
| 36 | stores | S07 (BTM Layout, 176 orders) | zone | Blank | Completeness | `zone` not null; load as `Unassigned` until the client confirms (BTM Layout is in south Bengaluru) | Warning |
| 37 | stores | S12 (Rajajinagar, 135 orders in Sept) | capacity_orders_per_day | 0, but the store is clearly trading | Accuracy | `capacity_orders_per_day > 0` | Warning |
| 38 | increment | ORD002465 | product_id | Uses P0109, the negative-MRP product (#34). Otherwise the file is clean | Consistency | Same product checks as orders | Critical |

\* **Decision needed on #30:** quarantining these 3 customers also fails their 18 orders on the foreign-key check. The softer option is to null the bad `signup_date`, keep the customer, and log a Warning.

**Not an issue:** all 301 blank `gateway_ref` values are Cash on Delivery payments, which never go through the gateway.

**The increment file** has 150 new orders (1 Oct, 06:02–22:33) and 10 corrections. In all 10 corrections the only change is `order_status` going DELIVERED → RETURNED (ORD000017, ORD000271, ORD000332, ORD000337, ORD000584, ORD000708, ORD000822, ORD001025, ORD001067, ORD001990). The ELT staging MERGE must update these, not insert them again.

### Questions for the client

1. **Negative and zero quantities:** 10 orders have quantity ≤ 0, and each has a "SUCCESS" payment for the same negative or zero amount. Are these returns recorded as negative orders, or data-entry errors?
2. **What counts as revenue:** 44 DELIVERED orders have a FAILED payment and 27 have no payment row. Does finance count revenue when the order is delivered or when the money is collected?
3. **Short payments:** 14 SUCCESS payments are exactly ₹10, 25, 50 or 100 less than the order. Is that a gateway coupon or cashback the order system doesn't know about? Which amount is the truth?
4. `Cashh` and `cod` payments have gateway refs, but real cash payments never do. Are these actually cash?
5. Duplicate customers (#24) differ only in phone and area. Which row is current, and can the CRM export include an `updated_at`?
6. An order delivered in September and returned on 1 October: should September revenue be restated, or should the return be booked in October?

---

## How to run

| What | Where |
|---|---|
| ETL DAG | [`dags/nammamart_etl_yourname.py`](dags/nammamart_etl_yourname.py) → logic in [`include/nammamart/etl.py`](include/nammamart/etl.py) |
| ELT DAG | [`dags/nammamart_elt_yourname.py`](dags/nammamart_elt_yourname.py) → logic in [`include/nammamart/elt.py`](include/nammamart/elt.py), SQL in [`include/sql/elt/`](include/sql/elt/) |
| Shared config, masking, `dq_results`, `pipeline_runs` | [`include/nammamart/common.py`](include/nammamart/common.py) |
| Business-question SQL and results | [`include/sql/business_questions/`](include/sql/business_questions/) · [results](include/sql/business_questions/results.md) |
| Observability experiments | [`include/nammamart/experiments.py`](include/nammamart/experiments.py) · [full output](include/nammamart/experiments_output.txt) |
| Warehouse | `include/warehouse_yourname.duckdb` (git-ignored: its raw layer holds unmasked customer data) |

In Airflow: `astro dev start`, then trigger `nammamart_etl_yourname` and `nammamart_elt_yourname`.
Without Airflow (same functions, same task order): `.venv/bin/python include/nammamart/run_local.py etl elt`.

> **Status:** both DAGs load in Airflow with no import errors and have run **green** in Airflow (`astro dev start`): one manual run each plus the scheduled run stamped `scheduled__2026-10-22T03:30:00+00:00` (= 9:00 AM IST). The Airflow runs produced exactly the same numbers as the local runs (5,372 in, 295 quarantined, 2,315 orders, ₹11,29,076.45). The experiments were run through `run_local.py`, which calls the same functions. Still to add: screenshots and the Airflow-only observations (retry states, Clear), marked **⏳ Airflow** below.

## Part A: ETL pipeline

**Flow:** six parallel extract tasks (stores, products, customers, orders, payments, plus any `orders_*_increment.csv`) → `validate` → `transform` → `load` → `reconcile` → `report` → `run_audit` (`trigger_rule="all_done"`).

- **Extract:** reads every column as text and **checks the schema first**. A renamed or missing column fails the task with a clear error.
- **Validate:** Python checks for all six dimensions (Part D). Each file is split into passed and failed rows. Failed rows go to `include/quarantine/yourname/<file>_failed_<run_id>.csv` exactly as received, plus a `failure_reason` column. Quarantined customers keep only masked email and phone.
- **Transform:** trim and standardise (`upi`, `UPI ` and `CARD` → `UPI` / `Card`; `cod` and `Cashh` → `Cash on Delivery`; tiers → Bronze/Silver/Gold/Platinum; S07's blank zone → `Unassigned`). Dedupe customers (keep last) and products (drop the "(old)" row). Mask email (`pr***@example.com`), phone (`97******21`) and name (`Priya H.`). Join to the dimensions and derive `order_date`, `net_revenue` (DELIVERED `order_amount`, after discount), `cost_amount`, `gross_margin` and `within_15_min`.
- **Load (idempotent):** the dimensions `etl_dim_customer`, `etl_dim_product` and `etl_dim_store` are replaced on every run. `etl_fact_orders` is loaded in one transaction: rows from `orders.csv` are replaced in full (so an order that fails today disappears), and increment rows are upserted on `order_id`.
- **Reconcile:** `etl_payment_reconciliation` has one row per mismatch, with a `reason` and `difference`.
- **Report:** builds `etl_daily_zone_revenue` and `etl_category_margin` and prints both to the task log.

**Run result:** 5,372 rows in, 295 quarantined (products 10, customers 8, orders 233, increment 15, payments 29), and **2,315 orders** in `etl_fact_orders`.

## Part B: ELT pipeline

**Flow:** six parallel `load_raw_*` tasks → `build_staging` → `merge_increment` → `build_marts` (which also runs `stg_payments`) → `run_audit` (`all_done`).

| Layer | Tables | How |
|---|---|---|
| Raw | `raw_orders`, `raw_payments`, `raw_customers`, `raw_products`, `raw_stores` | DuckDB `read_csv(all_varchar = true)`: every row and value as received, plus `_source_file`, `_run_id`, `_loaded_at`, `_file_hash`, `_row_num`. Never cleaned or deleted. A file whose md5 was already loaded is not appended again, so re-runs don't duplicate raw. `raw_load_log` records every file seen. |
| Staging | `stg_stores`, `stg_products`, `stg_customers`, `stg_orders`, `stg_payments` | SQL files `01`–`08` in `include/sql/elt/`: cast, standardise, dedupe, mask PII. Each quality check is a boolean column `c__<Severity>__<Dimension>__<check>`, which produces `dq_status`, `failure_reason` and one `dq_results` row per check. |
| Mart | `mart_daily_store_kpis`, `mart_category_margin`, `mart_delivery_sla`, `mart_payment_reconciliation`, `mart_top_customers`, `mart_payment_mode_revenue` | SQL files `10`–`15`; only `dq_status = 'PASS'` rows. |

**Incremental load:** the increment's 160 rows are appended to `raw_orders`. They are validated by the same SQL macro as `orders.csv` (`04_orders_checked_macro.sql`), then `07_merge_increment.sql` runs a `MERGE INTO stg_orders ... ON order_id`. A correction overwrites the old row only if the new version passes its checks; new orders are inserted.
Result: **150 inserted, 9 updated, 15 FAIL**. The 10th correction, ORD000822, fails `product_id_in_master` in both its September and October versions, so it isn't in either pipeline's revenue.

**ETL vs ELT totals match exactly:**

| | ETL | ELT |
|---|---|---|
| Clean orders | 2,315 | 2,315 |
| Net revenue, all | ₹11,29,076.45 | ₹11,29,076.45 |
| Net revenue, September only | ₹10,56,885.25 | ₹10,56,885.25 |
| Rows quarantined | 295 | 295 |

They match because both pipelines apply the same rules with the same severities, and the reconciliation SQL is generated from one template.

## Business questions

Full SQL is in [`include/sql/business_questions/`](include/sql/business_questions/) and the full results from both pipelines are in [`results.md`](include/sql/business_questions/results.md). Both pipelines return identical figures:

**1. Net revenue by zone:** East ₹2,93,090.40 · West ₹2,89,473.10 · South ₹2,40,159.05 · North ₹2,29,879.45 · Unassigned (S07, zone missing) ₹76,474.45. Daily and per-store detail is in `mart_daily_store_kpis` / `etl_daily_zone_revenue`.

**2. Revenue and margin by category:**

| Category | Revenue | Gross margin | Margin % |
|---|---|---|---|
| Staples | ₹2,64,456.90 | ₹66,435.28 | 25.1 |
| Household | ₹2,10,607.95 | ₹54,168.91 | 25.7 |
| Personal Care | ₹2,08,774.70 | ₹46,709.57 | 22.4 |
| Dairy & Bakery | ₹1,77,404.85 | ₹47,200.82 | 26.6 |
| Snacks & Beverages | ₹1,74,863.60 | ₹41,398.13 | 23.7 |
| Fruits & Vegetables | ₹92,968.45 | ₹22,018.22 | 23.7 |

**3. Delivery SLA:** average minutes and % within 15 minutes per store are in `mart_delivery_sla` (see results.md).

**4. Revenue by payment mode:** UPI ₹5,98,618.20 · Card ₹2,31,787.85 · Cash on Delivery ₹1,69,692.60 · Wallet ₹1,28,977.80.
**Not reconciled with the gateway:**

| Reason | Rows | Amount |
|---|---|---|
| SUCCESS payment for an order we quarantined | 206 | ₹1,58,276.73 |
| Order newer than the payments file (1 Oct) | 136 | ₹72,191.20 |
| DELIVERED, payment FAILED | 42 | ₹25,722.25 |
| DELIVERED, no payment at all | 27 | ₹16,438.30 |
| Payment for an order that doesn't exist (test transactions) | 8 | ₹4,580.57 |
| RETURNED but not refunded (the 1 Oct corrections) | 10 | ₹812.00 |
| SUCCESS amount ≠ order amount | 12 | ₹585.00 |

Excluding the 1 Oct orders whose payments haven't arrived yet, **₹2,06,414.85** doesn't reconcile. That figure is the sum of the absolute differences for the other six reasons in the table.

**5. Top 10 customers:** led by C00136 Sanjay B. (Bronze, ₹8,738.10) and C00236 Sneha N. (Platinum, ₹7,831.80). Only masked email and phone are shown.

**6. Rows rejected today:** 295 rows: products 10, customers 8, orders 233, increment 15, payments 29. The per-check breakdown comes from `dq_results` (query `q6`).

## Part C: Scheduling

Both DAGs: `schedule="0 9 * * 1-6"`, `start_date=pendulum.datetime(2026, 10, 1, tz="Asia/Kolkata")`, `catchup=False`, and `default_args` with `retries=2`, `retry_delay=2 min` and `execution_timeout=15 min`.

- **Cron expression:** `0 9 * * 1-6`, minute 0, hour 9, Monday (1) to Saturday (6).
- **Time in UTC in the Airflow UI:** 03:30 UTC (IST is UTC+5:30). Confirmed: Airflow created the run `scheduled__2026-10-22T03:30:00+00:00`.
- **If `start_date` were left in UTC:** the cron would run at 09:00 UTC = **2:30 PM IST**, five hours after the 9:30 AM stand-up.
- **If the laptop or Docker is off at 9 AM:** nothing runs and there is no data at 9:30. When Airflow starts again, `catchup=False` means it creates at most one run for the latest missed slot, not one per missed day. That's why this must run on an always-on host (Astro / a server), not a laptop, with an alert if `pipeline_runs` has no `success` row by 9:15.
- **Why `catchup=False`:** each file is a full snapshot. Backfilling every weekday since 1 Oct would re-process the same files many times for no new information.
- **Retries and timeout:** a whole run takes about a second, so 2 retries 2 minutes apart absorb transient problems (a file landing late, the DuckDB writer lock), and a 15-minute timeout kills a hung task long before the 9:30 stand-up.
- **Note:** the data is ready at about 9:01. If Kavya needs it *before* 9:00, change the cron to `30 8 * * 1-6`.

## Part D: Data quality dimensions

The same checks run in both pipelines (Python in `etl.py`, SQL in `include/sql/elt/`). Each run writes every check to `dq_results` (`run_id, dag_id, check_name, dimension, severity, rows_checked, rows_failed, status, checked_at`). Critical failures are quarantined; Warnings load and are logged.

| Dimension | Critical checks | Warning checks |
|---|---|---|
| Completeness | `customer_id_not_null`, `order_ts_not_null`, `delivered_has_delivery_minutes`, `category_not_null` | `email_not_null`, `city_not_null`, `zone_not_null`, `gateway_ref_present_for_non_cash`, `row_count_vs_previous_run` (volume) |
| Uniqueness | `order_id_unique`, `payment_id_unique`, `customer_id_unique`, `product_id_unique`, `store_id_unique` | — |
| Validity | `order_status_allowed`, `payment_mode_allowed`, `payment_status_allowed`, `order_ts_valid_timestamp`, `payment_ts_valid_timestamp`, `discount_pct_0_to_100`, `signup_date_valid`, `loyalty_tier_allowed` | `email_format`, `phone_10_digits`, `pincode_6_digits` |
| Accuracy | `quantity_positive`, `order_amount_matches_formula`, `delivery_minutes_below_120`, `mrp_positive`, `cost_price_le_mrp`, `success_amount_positive` | `delivery_minutes_8_to_35`, `unit_price_equals_mrp` (distribution), `capacity_positive` |
| Consistency | `customer_id_in_master`, `product_id_in_master`, `store_id_in_master`, `order_id_in_orders` (payments) | `payment_mode_standard_format`, `order_status_upper_case`, `loyalty_tier_casing`, plus the payment reconciliation table |
| Timeliness | `order_ts_not_future`, `payment_ts_not_future`, `signup_date_not_future` | `latest_order_within_1_day` (freshness), `launch_date_not_future` |

"Today" for the timeliness checks is the Airflow Variable `NAMMAMART_AS_OF`, which defaults to 2026-10-01 because the files are frozen. In production it would be the run date.

## Part E: Data governance

1. **Ownership.** Orders: Head of Operations (owner of the order management system). Payments: Finance / CFO. Customers: the CRM owner, with the Data Protection Officer accountable for the personal data. Products: Category / Merchandising. Stores: Operations. Warehouse tables: the data team (the FDE now, NammaMart's data engineer later). A rule change such as the 120-minute delivery limit is proposed by the data team and approved by the dataset owner (Ops). Finance signs off on any rule that changes revenue. Every change goes through a reviewed PR to `etl.py` / `include/sql/elt/`.
2. **Data dictionary** (fact and dimensions):

   | Table.column | Type | Meaning | Source | Allowed values | PII |
   |---|---|---|---|---|---|
   | fact.order_id | text | Order key | orders.csv | unique, ORDnnnnnn | No |
   | fact.order_ts / order_date | timestamp / date | When the order was placed (IST) | orders.order_ts | ≤ run date | No |
   | fact.customer_id / store_id / product_id | text | Keys to the dimensions | orders.csv | must exist in the dimension | Pseudonymous |
   | fact.quantity, unit_price, discount_pct | int, double, double | Line details | orders.csv | qty > 0, discount 0–100 | No |
   | fact.order_amount | double | qty × price × (1 − disc/100) | orders.csv | matches formula ±₹0.01 | No |
   | fact.payment_mode | text | How the customer paid | orders.csv, standardised | UPI, Card, Cash on Delivery, Wallet | No |
   | fact.order_status | text | Latest status (increments applied) | orders + increment | DELIVERED, CANCELLED, RETURNED | No |
   | fact.delivery_minutes / within_15_min | int / bool | Delivery time; ≤ 15 min flag | orders.csv | 0–119 | No |
   | fact.net_revenue / cost_amount / gross_margin | double | Revenue, qty × cost price, and their difference (DELIVERED only) | derived | ≥ 0 | No |
   | dim_customer.customer_name | text | First name + last initial | customers.full_name | — | **Yes (masked)** |
   | dim_customer.email_masked / phone_masked | text | Masked contact details | customers.email / phone | `pr***@domain`, `97******21` | **Yes (masked)** |
   | dim_customer.area, pincode, city, loyalty_tier, signup_date, is_active | text/date/bool | Profile | customers.csv | tier in Bronze–Platinum; pincode 560xxx | Quasi-identifier (area, pincode) |
   | dim_product.category, mrp, cost_price … | text/double | Catalogue | products.csv | mrp > 0, cost ≤ mrp | No |
   | dim_store.zone, capacity_orders_per_day … | text/int | Store master | stores.csv | North/South/East/West/Unassigned | manager_name: employee personal data |
3. **Lineage.** Take S05's net revenue on 2026-09-01 in `mart_daily_store_kpis`. In **ELT** it traces to `stg_orders WHERE store_id='S05' AND order_date='2026-09-01' AND dq_status='PASS'`, then each row's `_source_file`, `_file_hash` and `_row_num` lead to the exact line of the exact version of `orders.csv` in `raw_orders`. In **ETL** the fact row carries `_source_file` and `_run_id`, but the source rows weren't kept: if the file has since been overwritten, the trace stops. ELT is easier because the raw layer is the evidence.
4. **Personal data.** `full_name`, `email` and `phone` are direct identifiers; `area` + `pincode` (+ `signup_date`) are quasi-identifiers; `customer_id` is pseudonymous; `stores.manager_name` is employee personal data. Email, phone and name are masked in staging/transform and every reporting table. Masking rather than deleting keeps the data useful: support can confirm "the number ending 21", duplicate customers stay visible, and one customer's data still joins across tables. India's **Digital Personal Data Protection Act, 2023 (DPDP Act)** applies. It expects processing only for a stated purpose with consent, collecting the minimum needed, reasonable security safeguards, reporting breaches to the Data Protection Board and the affected people, erasing data once the purpose is served, and honouring people's rights to access, correct and erase their data.
5. **Access control.** Raw: the pipeline's service account and named data engineers only. Staging: data engineers and analysts (already masked). Marts: business users (COO, store managers, finance). Quarantine: data engineers and the owner of each dataset, who fix the source. **Unmasked phone numbers in `raw_customers`:** nobody for reporting. Only the pipeline reads them; support uses the CRM itself. DuckDB has no user permissions, so production needs a warehouse with roles (or raw in a separate encrypted store).
6. **Retention** (to confirm with NammaMart legal). Raw orders and payments: 8 years, the books-of-account period under the Companies Act. Raw customer PII: only while the account is active plus the statutory period, then deleted or anonymised. Quarantine files: 90 days after the issue is resolved. Masked customer data in marts: while the customer is active plus 3 years, then aggregated. Deletion should be a scheduled DAG, not a manual job.
7. **Secrets.** Credentials such as `SLACK_WEBHOOK_URL` go in an Airflow Variable or Connection (locally `airflow_settings.yaml` / `.env`, both git-ignored) and are read with `Variable.get()`. They must never be in a DAG file or on GitHub: the repo is forked and shared, git history keeps secrets forever, and anyone holding the webhook URL can post into the company's Slack. A leaked secret must be rotated, not just deleted.
8. **Audit:** "show a rejected order as received, the rule it broke, and prove it isn't in revenue." Example ORD001624 (₹9,576, 10× too high):
   - **ETL:** `include/quarantine/yourname/orders_failed_<run_id>.csv` has the row exactly as received with `failure_reason = order_amount_matches_formula`, and `SELECT count(*) FROM etl_fact_orders WHERE order_id = 'ORD001624'` returns 0.
   - **ELT:** `SELECT * FROM raw_orders WHERE order_id = 'ORD001624'` shows the original line with file, hash and row number. `stg_orders` shows `dq_status = 'FAIL'` with the reason, and the marts only read `PASS` rows.
9. **Change history.** ORD000271 was DELIVERED on 4 Sep and RETURNED on 1 Oct. After the incremental load both pipelines show it as RETURNED, so **September revenue is restated down by ₹445**: the books for a closed month change. Finance normally wants the September number frozen and the return booked in October. To keep both views, keep history instead of overwriting: an SCD Type 2 fact (`valid_from` / `valid_to`) or an append-only `order_status_changes` table dated by the change. ELT already has both versions in `raw_orders` (orders.csv and the increment row), so an "as at 30 Sep" view can be rebuilt. ETL overwrote the row, so it cannot.

## Part F: Observability tests

Run with [`include/nammamart/experiments.py`](include/nammamart/experiments.py), which swaps a modified copy of a file in, runs both pipelines, and restores the original. Full log: [`experiments_output.txt`](include/nammamart/experiments_output.txt).

| # | Experiment | Expected | Observed (both pipelines unless noted) | Where I saw it | What I would change |
|---|---|---|---|---|---|
| 1 | Happy path | All tasks green; extracts in parallel | Both succeed. 5,372 in, 295 quarantined, 2,315 loaded; about 0.5 s (ETL) and 0.7 s (ELT) end to end. ⏳ Airflow: per-task durations and the parallel extracts in Graph/Gantt view | `pipeline_runs`, `[validate]` log, quarantine folder | — |
| 2 | Re-run | Fact counts unchanged | `etl_fact_orders` stays 2,179 (2,315 with the increment). `raw_orders` does **not** grow: the file's md5 was already loaded, which is correct (raw is an audit log of *distinct* files received, and `raw_load_log` records the re-run) | `experiments_output.txt`, `raw_load_log` | — |
| 3 | Incremental load | 150 new, 10 status updates, no duplicates | **136 inserted, 9 updated**, 14 new orders and 1 correction quarantined (product master). Raw +160 rows. Revenue +₹68,528.50. No duplicate `order_id`s | `[merge]` log, fact counts | Alert when a correction is rejected: ORD000822 kept its old status |
| 4 | Missing `products.csv` | `extract_products` retries twice then fails; downstream `upstream_failed`; audit records `failed` | ⏳ Airflow. The code raises `FileNotFoundError("Source file missing: …/products.csv")`; `run_audit` is `all_done`, so the failure still reaches `pipeline_runs` | Task log, Grid view | Add a Slack alert (`on_failure_callback` + `Variable.get("SLACK_WEBHOOK_URL")`) |
| 5 | 5 new bad rows | Each quarantined with the right reason | ORD90001 `customer_id_not_null` · ORD90002 `quantity_positive; order_amount_matches_formula` · ORD90003 `store_id_in_master` · ORD90004 `order_status_allowed` · ORD90005 `order_ts_not_future`. The matching checks' `rows_failed` in `dq_results` went up | Quarantine CSV, `stg_orders.failure_reason`, `dq_results` | — |
| 6 | `order_amount` → `total` | Fail loudly | Fails at extract / raw load: `ValueError: Schema drift in orders.csv: missing columns ['order_amount'], unexpected columns ['total']`. Nothing loaded; run marked `failed` | Task log, `pipeline_runs` | — |
| 7 | Only 50 orders | Volume warning | `orders.row_count_vs_previous_run` = **WARN** (50 vs 2,417). Side effect: 2,172 payments quarantined (their orders are missing) | `[volume]` log, `dq_results` | Make a >90% drop Critical (stop the load) and alert |
| 8 | `unit_price` × 100 at S05 | A check catches it | `order_amount_matches_formula` **FAIL** on 162 rows (normally 18) and `unit_price_equals_mrp` **WARN** on 138 rows. All 144 S05 September orders were quarantined, so total net revenue fell ₹74,738.55 (₹11,29,076.45 → ₹10,54,337.90) and S05's September revenue disappeared from `mart_daily_store_kpis` | `dq_results`, mart totals | If `order_amount` had been inflated too, only the Warning would catch it; add a per-store revenue z-score check |
| 9 | Orders 30 days old | Freshness warning | `orders.latest_order_within_1_day` = **WARN** | `[freshness]` log, `dq_results` | Make it Critical on production days |
| 10 | Recovery with Clear | Only the failed task and its downstream tasks re-run | ⏳ Airflow. Re-running is safe by design: every load is idempotent (#2) | Grid view | — |

**Experiments 2–9 also proved ETL and ELT stay identical** (same counts and revenue after every experiment). They also caught two bugs that I fixed: the ETL fact table kept rows that later failed, and the freshness check looked at future-dated rows.

**The five pillars of data observability:**

| Pillar | Coverage |
|---|---|
| Freshness | `latest_order_within_1_day`, future-date checks |
| Volume | `row_count_vs_previous_run`; `rows_extracted / loaded / quarantined` in `pipeline_runs` |
| Schema | `check_schema` fails the task before any load |
| Distribution | Rule-based only: `unit_price_equals_mrp`, delivery 8–35, formula check |
| Lineage | ELT: file, hash, row number and run on every raw and staging row; ETL: file and run on the fact table |

**Best covered:** schema, which fails loudly before any data moves. **Weakest:** distribution. There are no statistical baselines (for example, revenue per store versus its 4-week average), and the `dq_results` trend isn't charted or alerted on yet.

## Part G: Recommendation to Sameer (CTO)

**Recommendation: adopt ELT, but keep ETL's guarantee.** Finance only ever reads marts built from rows that passed every Critical check.

Both pipelines produced the same answer on the same data: ₹11,29,076.45 net revenue, 2,315 clean orders and 295 rejected rows. So the choice comes down to what each makes easy.

- **Auditability.** ELT keeps every row exactly as received, with its file, version and line number. When finance asked "show me a rejected order and prove it isn't in revenue", ELT answered with one query. ETL needed the quarantine file from the right day. ELT can also rebuild "September as reported" after the 1 Oct returns; ETL overwrote it.
- **Data quality guarantees.** These are equal. The same rules and severities run in both, the marts read only `PASS` rows, and every check is recorded in `dq_results`. Bad rows never reach the CFO's tables in either design.
- **Ease of change.** A new rule in ELT is a SQL edit followed by a re-run over raw, with no need to re-extract anything. With ETL, history that was rejected or overwritten is gone. Schema drift was caught equally fast by both.
- **Performance at 1000×** (about 2.4M orders and 2.2M payments a month). The ETL holds whole files in pandas memory, which becomes several GB and fragile. DuckDB processes this volume in seconds to minutes and later moves to a server warehouse unchanged (same SQL).
- **Cost.** Both use only open-source tools. ELT stores more (raw keeps every distinct file version), but that's a few GB a year: negligible next to half a day a week of Finance reconciling by hand.

**Top 3 risks of the recommended design**

1. **Raw holds unmasked personal data** (names, emails, phones). DuckDB has no access control. Restrict raw to the pipeline service account, encrypt it, and set DPDP-compliant retention before go-live.
2. **One DuckDB file on one machine, with one writer.** If the laptop is off at 9 AM there is no report. Move to an always-on host (Astro or a server) with backups and a "no success by 9:15" alert.
3. **Strict master-data rules can silently hide real revenue.** 135 September orders were rejected because their product row was bad or missing (for example, P0109's negative MRP), and 18 because of future signup dates. Each rule needs an owner, and `dq_results` trends need an alert, so a bad master file doesn't quietly understate the 9 AM number.

## Screenshots (⏳ to add after the first Airflow run)

- [ ] Both DAGs in Graph view, green run
- [ ] Schedule showing 9:00 AM IST / next run time
- [ ] One quarantine file (already generated in `include/quarantine/yourname/`)
- [ ] Query results: `dq_results`, `pipeline_runs`, the payment reconciliation table (already in [results.md](include/sql/business_questions/results.md))
