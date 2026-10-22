# NammaMart data profile

Source: `include/data/nammamart` · reference date for timeliness checks: 2026-10-01

| File | Rows |
|---|---|
| orders.csv | 2412 |
| payments.csv | 2228 |
| customers.csv | 405 |
| products.csv | 152 |
| stores.csv | 15 |
| orders_2026-10-01_increment.csv | 160 |
| **Total** | **5372** |

## orders.csv

Rows: **2412** · Columns: **13** · Key: `order_id`

| Column | Nulls/blank | Untrimmed | Distinct | Min | Max | Unparseable |
|---|---|---|---|---|---|---|
| order_id | 0 | 0 | 2400 |  |  |  |
| order_ts | 2 | 0 | 2393 | 2026-09-01 06:30:15 | 2027-01-01 09:00:00 | 4 |
| customer_id | 18 | 0 | 401 |  |  |  |
| store_id | 0 | 0 | 18 |  |  |  |
| product_id | 0 | 0 | 159 |  |  |  |
| quantity | 0 | 0 | 9 | -3.0 | 5.0 | 0 |
| unit_price | 0 | 0 | 133 | 10.0 | 883.0 | 0 |
| discount_pct | 0 | 0 | 8 | 0.0 | 250.0 | 0 |
| order_amount | 0 | 0 | 1155 | -1593.0 | 9576.0 | 0 |
| payment_mode | 0 | 2 | 9 |  |  |  |
| order_status | 0 | 0 | 5 |  |  |  |
| channel | 0 | 0 | 2 |  |  |  |
| delivery_minutes | 164 | 0 | 32 | 8.0 | 1440.0 | 0 |

Duplicate `order_id` values: **12** (24 rows): ORD001462, ORD001326, ORD001434, ORD000783, ORD001239, ORD001692, ORD001870, ORD001441, ORD002129, ORD001549, ORD001110, ORD000539  
Exact duplicate rows (every column identical): **12**

- `payment_mode` distinct values: UPI (1329), Card (493), Cash on Delivery (326), Wallet (254), upi (4), Cashh (2), 'UPI ' (2), CARD (1), cod (1)
- `order_status` distinct values: DELIVERED (2182), CANCELLED (156), RETURNED (69), Pending?? (3), delivered (2)
- `channel` distinct values: App (2044), Web (368)
- `store_id` distinct values: S08 (177), S07 (176), S14 (175), S13 (172), S15 (169), S11 (164), S06 (163), S01 (162), S03 (159), S10 (157), S02 (156), S04 (156), S05 (144), S09 (142), S12 (135), S17 (3), S99 (1), S00 (1)

## payments.csv

Rows: **2228** · Columns: **7** · Key: `payment_id`

| Column | Nulls/blank | Untrimmed | Distinct | Min | Max | Unparseable |
|---|---|---|---|---|---|---|
| payment_id | 0 | 0 | 2224 |  |  |  |
| order_id | 0 | 0 | 2224 |  |  |  |
| payment_ts | 0 | 0 | 2210 | 2026-09-01 06:30:24 | 2027-01-01 09:01:46 | 0 |
| payment_mode | 0 | 2 | 9 |  |  |  |
| amount_paid | 0 | 0 | 1127 | -1593.0 | 9576.0 | 0 |
| payment_status | 0 | 0 | 3 |  |  |  |
| gateway_ref | 301 | 0 | 1924 |  |  |  |

Duplicate `payment_id` values: **4** (8 rows): PAY0001651, PAY0000755, PAY0000509, PAY0002000  
Exact duplicate rows (every column identical): **4**

- `payment_mode` distinct values: UPI (1238), Card (445), Cash on Delivery (301), Wallet (234), upi (4), 'UPI ' (2), Cashh (2), cod (1), CARD (1)
- `payment_status` distinct values: SUCCESS (2116), REFUNDED (68), FAILED (44)

## customers.csv

Rows: **405** · Columns: **10** · Key: `customer_id`

| Column | Nulls/blank | Untrimmed | Distinct | Min | Max | Unparseable |
|---|---|---|---|---|---|---|
| customer_id | 0 | 0 | 400 |  |  |  |
| full_name | 0 | 0 | 280 |  |  |  |
| email | 4 | 0 | 397 |  |  |  |
| phone | 0 | 0 | 405 |  |  |  |
| city | 6 | 0 | 2 |  |  |  |
| area | 0 | 0 | 15 |  |  |  |
| pincode | 0 | 0 | 17 |  |  |  |
| signup_date | 0 | 0 | 315 | 2024-06-01 00:00:00 | 2027-01-05 00:00:00 | 0 |
| loyalty_tier | 0 | 0 | 7 |  |  |  |
| is_active | 0 | 0 | 2 |  |  |  |

Duplicate `customer_id` values: **5** (10 rows): C00103, C00252, C00036, C00226, C00313  
Exact duplicate rows (every column identical): **0**

- `city` distinct values: Bengaluru (399), '' (6)
- `area` distinct values: Indiranagar (43), RT Nagar (37), BTM Layout (34), Yelahanka (32), Malleshwaram (30), JP Nagar (27), Banashankari (27), Marathahalli (25), Basaveshwaranagar (24), HSR Layout (24), Whitefield (23), Rajajinagar (23), Hebbal (22), Jayanagar (19), Vijayanagar (15)
- `loyalty_tier` distinct values: Bronze (185), Silver (133), Gold (54), Platinum (25), BRONZE (3), bronze (3), SILVER (2)
- `is_active` distinct values: Y (352), N (53)

## products.csv

Rows: **152** · Columns: **10** · Key: `product_id`

| Column | Nulls/blank | Untrimmed | Distinct | Min | Max | Unparseable |
|---|---|---|---|---|---|---|
| product_id | 0 | 0 | 150 |  |  |  |
| product_name | 0 | 0 | 152 |  |  |  |
| category | 3 | 0 | 7 |  |  |  |
| sub_category | 0 | 0 | 21 |  |  |  |
| brand | 0 | 0 | 23 |  |  |  |
| mrp | 0 | 0 | 135 | -203.0 | 883.0 | 0 |
| cost_price | 0 | 0 | 150 | 6.79 | 631.79 | 0 |
| unit | 0 | 0 | 3 |  |  |  |
| is_perishable | 0 | 0 | 2 |  |  |  |
| launch_date | 0 | 0 | 145 | 2023-01-03 00:00:00 | 2025-09-20 00:00:00 | 0 |

Duplicate `product_id` values: **2** (4 rows): P0030, P0140  
Exact duplicate rows (every column identical): **0**

- `category` distinct values: Dairy & Bakery (26), Household (26), Fruits & Vegetables (25), Snacks & Beverages (25), Personal Care (25), Staples (22), '' (3)
- `sub_category` distinct values: Detergent (14), Fresh Fruits (10), Shampoo (10), Herbs (8), Milk (8), Rice (8), Soft Drinks (8), Tea & Coffee (8), Soap (8), Kitchen Supplies (8), Fresh Vegetables (7), Curd & Paneer (7), Atta (7), Biscuits (7), Oral Care (7), Bread (6), Cheese (5), Dal (5), Oil (5), Cleaners (4), Chips (2)
- `brand` distinct values: Kaveri Dairy (14), DalBazaar (12), Desi Farms (10), CleanPro (10), TeaTime (9), PureGlow (9), FarmFresh (8), GoldenGrain (8), ShineAll (8), GreenLeaf (7), Chandana (7), BrewHouse (6), SnackSutra (6), OvenCraft (5), HerbVeda (5), ScrubMate (5), CowBell (4), CrunchCo (4), SmileBright (4), MilkWay (3), SunPress (3), SparkWash (3), Annapurna Mills (2)
- `unit` distinct values: pack (76), unit (51), kg (25)
- `is_perishable` distinct values: False (101), True (51)

## stores.csv

Rows: **15** · Columns: **8** · Key: `store_id`

| Column | Nulls/blank | Untrimmed | Distinct | Min | Max | Unparseable |
|---|---|---|---|---|---|---|
| store_id | 0 | 0 | 15 |  |  |  |
| store_name | 0 | 0 | 15 |  |  |  |
| zone | 1 | 0 | 5 |  |  |  |
| area | 0 | 0 | 15 |  |  |  |
| pincode | 0 | 0 | 15 |  |  |  |
| open_date | 0 | 0 | 15 | 2024-02-14 00:00:00 | 2025-07-28 00:00:00 | 0 |
| manager_name | 0 | 0 | 15 |  |  |  |
| capacity_orders_per_day | 0 | 0 | 5 | 0.0 | 600.0 | 0 |

Duplicate `store_id` values: **0** (0 rows)  
Exact duplicate rows (every column identical): **0**

- `zone` distinct values: East (4), West (4), North (3), South (3), '' (1)
- `area` distinct values: Hebbal (1), Yelahanka (1), RT Nagar (1), Jayanagar (1), JP Nagar (1), Banashankari (1), BTM Layout (1), Whitefield (1), Indiranagar (1), Marathahalli (1), HSR Layout (1), Rajajinagar (1), Malleshwaram (1), Vijayanagar (1), Basaveshwaranagar (1)

## orders_2026-10-01_increment.csv

Rows: **160** · Columns: **13** · Key: `order_id`

| Column | Nulls/blank | Untrimmed | Distinct | Min | Max | Unparseable |
|---|---|---|---|---|---|---|
| order_id | 0 | 0 | 160 |  |  |  |
| order_ts | 0 | 0 | 152 | 2026-09-01 09:38:13 | 2026-10-01 22:33:00 | 0 |
| customer_id | 0 | 0 | 143 |  |  |  |
| store_id | 0 | 0 | 15 |  |  |  |
| product_id | 0 | 0 | 98 |  |  |  |
| quantity | 0 | 0 | 4 | 1.0 | 4.0 | 0 |
| unit_price | 0 | 0 | 90 | 10.0 | 883.0 | 0 |
| discount_pct | 0 | 0 | 5 | 0.0 | 20.0 | 0 |
| order_amount | 0 | 0 | 148 | 11.0 | 2052.0 | 0 |
| payment_mode | 0 | 0 | 4 |  |  |  |
| order_status | 0 | 0 | 2 |  |  |  |
| channel | 0 | 0 | 1 |  |  |  |
| delivery_minutes | 0 | 0 | 24 | 8.0 | 34.0 | 0 |

Duplicate `order_id` values: **0** (0 rows)  
Exact duplicate rows (every column identical): **0**

- `payment_mode` distinct values: UPI (46), Card (44), Cash on Delivery (40), Wallet (30)
- `order_status` distinct values: DELIVERED (150), RETURNED (10)
- `channel` distinct values: App (160)

---

# Rule and integrity checks

### Rule checks — orders.csv

- **customer_id null**: ❌ 18 — ORD002255, ORD000701, ORD000997, ORD000580, ORD002019, ORD002262, ORD002149, ORD002367, ORD001332, ORD001918, ORD002156, ORD000583 … (+6 more)
- **customer_id not in customers.csv**: ✅ 0
- **product_id not in products.csv**: ❌ 9 — ORD000986→P9455, ORD001058→P9212, ORD001685→P9816, ORD000070→P9893, ORD000789→P9989, ORD000596→P9784, ORD000134→P9822, ORD000965→P9399, ORD002179→P9761
- **store_id not in stores.csv**: ❌ 5 — ORD001799→S99, ORD001046→S17, ORD001492→S17, ORD001275→S17, ORD002126→S00
- **order_ts null/blank/N/A**: ❌ 2 — ORD000403='N/A', ORD000362=''
- **order_ts not in YYYY-MM-DD HH:MM:SS or not a real date**: ❌ 4 — ORD001610='2026-13-05 11:00:00', ORD000534='2026-13-05 11:00:00', ORD002012='31/09/2026 10:00', ORD000946='31/09/2026 10:00'
- **order_ts in the future (after 1 Oct 2026)**: ❌ 7 — ORD002119=2027-01-01 09:00:00, ORD001693=2026-10-21 10:15:00, ORD001089=2026-10-21 10:15:00, ORD001121=2026-11-02 18:40:00, ORD001765=2027-01-01 09:00:00, ORD001965=2026-11-02 18:40:00, ORD001725=2027-01-01 09:00:00
- **quantity ≤ 0 or not a number**: ❌ 10 — ORD000469=0.0, ORD001296=-2.0, ORD001459=-3.0, ORD000867=-1.0, ORD000462=-3.0, ORD002360=0.0, ORD001724=0.0, ORD000099=0.0, ORD001124=-1.0, ORD001384=-1.0
- **quantity not a whole number**: ✅ 0
- **quantity > 20 (suspiciously large for q-commerce)**: ✅ 0
- **unit_price ≤ 0 or not a number**: ✅ 0
- **discount_pct outside 0–100**: ❌ 3 — ORD002103=250, ORD001468=120, ORD001237=150
- **unit_price ≠ current product MRP**: ✅ 0  
  _Distribution check: in clean data every order is sold at MRP_
- **Ordered product has a negative MRP in products.csv**: ❌ 11 — ORD001295 P0109, ORD000331 P0109, ORD000957 P0109, ORD000023 P0109, ORD000352 P0109, ORD001360 P0109, ORD001748 P0109, ORD000616 P0109, ORD000871 P0109, ORD002023 P0109, ORD000446 P0109
- **order_amount ≠ quantity × unit_price × (1 − discount/100)**: ❌ 18 — ORD002103 exp=-738.0 got=492.0, ORD001468 exp=-136.8 got=547.2, ORD001237 exp=-1505.0 got=2408.0, ORD002305 exp=675.75 got=6757.5, ORD002004 exp=672.0 got=6720.0, ORD000845 exp=471.2 got=4712.0, ORD000964 exp=837.0 got=8370.0, ORD002031 exp=321.0 got=3210.0, ORD001624 exp=957.6 got=9576.0, ORD002298 exp=610.2 got=305.1, ORD001274 exp=220.0 got=110.0, ORD002223 exp=73.15 got=36.58 … (+6 more)  
  _discount_pct > 100, amount ignores discount: 3; 10× too high (decimal shift): 6; 0.5× expected: 4; 1.5× expected: 5_
- **payment_mode not exactly in allowed list**: ❌ 10 — ORD001812='Cashh', ORD001414='Cashh', ORD000159='upi', ORD001364='CARD', ORD000433='upi', ORD002356='UPI ', ORD001640='cod', ORD001874='UPI ', ORD000934='upi', ORD000691='upi'
- **order_status not exactly in allowed list**: ❌ 5 — ORD001066='delivered', ORD000500='Pending??', ORD000153='delivered', ORD001970='Pending??', ORD001637='Pending??'
- **DELIVERED with no delivery_minutes**: ❌ 8 — ORD001554, ORD001800, ORD000731, ORD001277, ORD000326, ORD001515, ORD002229, ORD000878
- **delivery_minutes ≥ 120 (hours, not minutes)**: ❌ 6 — ORD001037=480.0, ORD002101=480.0, ORD000455=1440.0, ORD001104=900.0, ORD000020=900.0, ORD000424=480.0
- **delivery_minutes ≤ 0**: ✅ 0
- **delivery_minutes outside normal 8–35 (but < 120)**: ✅ 0  
  _Warning-level: possible but unusual_
- **CANCELLED order with a delivery_minutes value**: ✅ 0
- **Looks like a test entry (test/dummy/demo in any field)**: ✅ 0
- **Same customer+product+timestamp+qty under different order_ids**: ✅ 0

### Rule checks — payments.csv

- **order_id not in orders.csv**: ❌ 8 — PAY0002219→ORD970544, PAY0002220→ORD968496, PAY0002223→ORD988106, PAY0002221→ORD941071, PAY0002224→ORD981600, PAY0002218→ORD997176, PAY0002222→ORD953136, PAY0002217→ORD966342  
  _payment_ts values: ['2026-09-18 14:22:10']; total ₹4,580.57_
- **More than one payment row for an order**: ❌ 4 — ORD000188×2, ORD000094×2, ORD002122×2, ORD000513×2
- **payment_ts in the future (after 1 Oct 2026)**: ❌ 7 — PAY0000396=2026-11-02 18:40:52, PAY0000127=2027-01-01 09:01:37, PAY0001908=2027-01-01 09:01:46, PAY0001037=2027-01-01 09:01:02, PAY0000337=2026-10-21 10:15:38, PAY0001488=2026-11-02 18:41:31, PAY0000267=2026-10-21 10:16:40
- **payment_mode not exactly in allowed list**: ❌ 10 — PAY0002188='upi', PAY0001850='upi', PAY0001954='cod', PAY0000817='upi', PAY0001359='CARD', PAY0002208='upi', PAY0002113='UPI ', PAY0001862='UPI ', PAY0000522='Cashh', PAY0000044='Cashh'
- **amount_paid ≤ 0 or not a number**: ❌ 10 — PAY0001568=-43.05, PAY0002175=-188.7, PAY0000116=0.0, PAY0000751=-1593.0, PAY0000944=-1279.65, PAY0000791=-500.65, PAY0001111=0.0, PAY0001322=0.0, PAY0000954=0.0, PAY0000737=-394.0
- **SUCCESS payment amount ≠ order_amount**: ❌ 14 — PAY0001568/ORD001031 paid=-43.05 due=56.95 short=100.00, PAY0000354/ORD001937 paid=455.0 due=505.0 short=50.00, PAY0000779/ORD001840 paid=2.6 due=102.6 short=100.00, PAY0000323/ORD001864 paid=182.95 due=192.95 short=10.00, PAY0001167/ORD001753 paid=452.35 due=502.35 short=50.00, PAY0001499/ORD001832 paid=349.3 due=374.3 short=25.00, PAY0000909/ORD001360 paid=103.0 due=203.0 short=100.00, PAY0000586/ORD000481 paid=2.6 due=102.6 short=100.00, PAY0000161/ORD001039 paid=232.2 due=282.2 short=50.00, PAY0002183/ORD000371 paid=955.4 due=980.4 short=25.00, PAY0000044/ORD001812 paid=353.0 due=378.0 short=25.00, PAY0001813/ORD001572 paid=402.4 due=502.4 short=100.00 … (+2 more)
- **payment_mode differs from the order's payment_mode**: ✅ 0
- **payment_ts earlier than order_ts**: ✅ 0
- **Payment exists for a CANCELLED order**: ✅ 0

order_status × payment_status:

| order_status | payment_status | orders |
|---|---|---|
| CANCELLED | NO PAYMENT | 156 |
| DELIVERED | FAILED | 44 |
| DELIVERED | NO PAYMENT | 27 |
| DELIVERED | SUCCESS | 2099 |
| Pending?? | SUCCESS | 3 |
| RETURNED | NO PAYMENT | 1 |
| RETURNED | REFUNDED | 68 |
| delivered | SUCCESS | 2 |

- **DELIVERED order whose only payment FAILED**: ❌ 44 — ORD000398, ORD000518, ORD000747, ORD002235, ORD000896, ORD000666, ORD001300, ORD000106, ORD001613, ORD001842, ORD000564, ORD000580 … (+32 more)  
  _Revenue counted with no money collected_
- **RETURNED order not REFUNDED**: ❌ 1 — ORD001675
- **gateway_ref blank on a non-cash payment**: ✅ 0  
  _301 blank refs in total; Cash on Delivery never goes through the gateway, so blanks there are expected_
- **Duplicate gateway_ref**: ❌ 4 — GW7909341632, GW2899060380, GW5719011844, GW2663042309
- **DELIVERED/RETURNED order with no payment row**: ❌ 28 — ORD001113, ORD000737, ORD001398, ORD002078, ORD001570, ORD000994, ORD000984, ORD000504, ORD001881, ORD000525, ORD000805, ORD001675 … (+16 more)

### Rule checks — customers.csv

- **Same customer_id with different details**: ❌ 5 — C00103, C00252, C00036, C00226, C00313
- **full_name blank**: ✅ 0
- **email invalid format**: ❌ 8 — C00307, C00063, C00363, C00310, C00112, C00392, C00062, C00067
- **email blank or N/A**: ❌ 4 — C00337='N/A', C00045='N/A', C00327='N/A', C00193='N/A'
- **Same email on different customer_ids**: ✅ 0
- **phone not exactly 10 digits**: ❌ 7 — C00151 (9 digits), C00240 (8 digits), C00095 (9 digits), C00357 (9 digits), C00130 (9 digits), C00290 (7 digits), C00339 (9 digits)
- **phone not starting 6–9 (Indian mobile)**: ✅ 0
- **pincode not exactly 6 digits**: ❌ 3 — C00132='5600XX', C00083='5600XX', C00166='5600XX'
- **pincode not a Bengaluru 560xxx code**: ❌ 2 — C00395=000000, C00342=000000
- **city blank**: ❌ 6 — C00355, C00394, C00233, C00142, C00328, C00219
- **signup_date unparseable or in the future**: ❌ 3 — C00400=2027-01-05, C00398=2026-11-12, C00038=2026-12-20
- **loyalty_tier not one of Bronze/Silver/Gold/Platinum (casing)**: ❌ 8 — C00199='SILVER', C00171='SILVER', C00133='BRONZE', C00032='bronze', C00031='bronze', C00196='bronze', C00136='BRONZE', C00092='BRONZE'

### Rule checks — products.csv

- **Same product_id with different details**: ❌ 2 — P0030, P0140
- **category blank**: ❌ 3 — P0051, P0060, P0068
- **mrp ≤ 0 or not a number**: ❌ 1 — P0109=-203.0
- **cost_price ≤ 0 or not a number**: ✅ 0
- **cost_price > mrp (sold at a loss)**: ❌ 5 — P0019 cost=264.0 mrp=220.0, P0073 cost=334.8 mrp=279.0, P0074 cost=420.0 mrp=350.0, P0109 cost=162.5 mrp=-203.0, P0117 cost=92.4 mrp=77.0
- **launch_date unparseable or in the future**: ✅ 0
- **Same product_name on different product_ids**: ✅ 0

### Rule checks — stores.csv

- **zone blank**: ❌ 1 — S07
- **capacity_orders_per_day ≤ 0**: ❌ 1 — S12=0
- **pincode not exactly 6 digits**: ✅ 0
- **open_date unparseable or in the future**: ✅ 0
- **manager_name blank**: ✅ 0

### Cross-file checks

- **Order placed before the customer signed up**: ❌ 18 — ORD000039 C00038 order=2026-09-01 signup=2026-12-20, ORD001409 C00038 order=2026-09-19 signup=2026-12-20, ORD002167 C00400 order=2026-09-28 signup=2027-01-05, ORD002061 C00400 order=2026-09-26 signup=2027-01-05, ORD002351 C00400 order=2026-09-30 signup=2027-01-05, ORD002344 C00400 order=2026-09-30 signup=2027-01-05, ORD001955 C00400 order=2026-09-25 signup=2027-01-05, ORD002371 C00398 order=2026-09-30 signup=2026-11-12, ORD002298 C00398 order=2026-09-29 signup=2026-11-12, ORD000151 C00398 order=2026-09-02 signup=2026-11-12, ORD000399 C00400 order=2026-09-06 signup=2027-01-05, ORD001355 C00398 order=2026-09-18 signup=2026-11-12 … (+6 more)
- **Orders from customers marked is_active = N**: ❌ 319 — ORD001791, ORD001200, ORD001249, ORD000314, ORD001533, ORD001892, ORD000228, ORD000283, ORD002236, ORD001603, ORD002132, ORD002196 … (+307 more)  
  _Probably fine (customer churned after ordering); confirm what is_active means_
- **Customer pincode doesn't match the area's pincode**: ❌ 5 — C00132 JP Nagar 5600XX, C00395 Indiranagar 000000, C00083 Indiranagar 5600XX, C00342 Hebbal 000000, C00166 Indiranagar 5600XX
- **Order placed before its store opened**: ✅ 0
- **Store-days over capacity_orders_per_day**: ❌ 31 — S12 2026-09-26: 4>0.0, S12 2026-09-18: 5>0.0, S12 2026-09-10: 3>0.0, S12 2026-09-03: 3>0.0, S12 2026-09-24: 6>0.0, S12 2026-09-28: 8>0.0, S12 2026-09-23: 8>0.0, S12 2026-09-05: 8>0.0, S12 2026-09-21: 6>0.0, S12 2026-09-13: 8>0.0, S12 2026-09-29: 9>0.0, S12 2026-09-22: 3>0.0 … (+19 more)

### Rule checks — orders_2026-10-01_increment.csv

- **customer_id null**: ✅ 0
- **customer_id not in customers.csv**: ✅ 0
- **product_id not in products.csv**: ✅ 0
- **store_id not in stores.csv**: ✅ 0
- **order_ts null/blank/N/A**: ✅ 0
- **order_ts not in YYYY-MM-DD HH:MM:SS or not a real date**: ✅ 0
- **order_ts in the future (after 1 Oct 2026)**: ✅ 0
- **quantity ≤ 0 or not a number**: ✅ 0
- **quantity not a whole number**: ✅ 0
- **quantity > 20 (suspiciously large for q-commerce)**: ✅ 0
- **unit_price ≤ 0 or not a number**: ✅ 0
- **discount_pct outside 0–100**: ✅ 0
- **unit_price ≠ current product MRP**: ✅ 0  
  _Distribution check: in clean data every order is sold at MRP_
- **Ordered product has a negative MRP in products.csv**: ❌ 1 — ORD002465 P0109
- **order_amount ≠ quantity × unit_price × (1 − discount/100)**: ✅ 0
- **payment_mode not exactly in allowed list**: ✅ 0
- **order_status not exactly in allowed list**: ✅ 0
- **DELIVERED with no delivery_minutes**: ✅ 0
- **delivery_minutes ≥ 120 (hours, not minutes)**: ✅ 0
- **delivery_minutes ≤ 0**: ✅ 0
- **delivery_minutes outside normal 8–35 (but < 120)**: ✅ 0  
  _Warning-level: possible but unusual_
- **CANCELLED order with a delivery_minutes value**: ✅ 0
- **Looks like a test entry (test/dummy/demo in any field)**: ✅ 0
- **Same customer+product+timestamp+qty under different order_ids**: ✅ 0

### Incremental file vs orders.csv

- Existing order_ids (corrections): **10** · new order_ids: **150**
- Corrections:
  - ORD000017 (order_status: 'DELIVERED'→'RETURNED')
  - ORD000271 (order_status: 'DELIVERED'→'RETURNED')
  - ORD000332 (order_status: 'DELIVERED'→'RETURNED')
  - ORD000337 (order_status: 'DELIVERED'→'RETURNED')
  - ORD000584 (order_status: 'DELIVERED'→'RETURNED')
  - ORD000708 (order_status: 'DELIVERED'→'RETURNED')
  - ORD000822 (order_status: 'DELIVERED'→'RETURNED')
  - ORD001025 (order_status: 'DELIVERED'→'RETURNED')
  - ORD001067 (order_status: 'DELIVERED'→'RETURNED')
  - ORD001990 (order_status: 'DELIVERED'→'RETURNED')
- New orders span 2026-10-01 06:02:00 → 2026-10-01 22:33:00
