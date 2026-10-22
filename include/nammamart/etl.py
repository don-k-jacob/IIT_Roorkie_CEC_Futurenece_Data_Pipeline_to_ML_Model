"""ETL pipeline logic: Extract -> Validate (Python) -> Transform (pandas) -> Load (DuckDB star schema).

The DAG calls these functions; run_local.py calls the same functions without Airflow.
Intermediate data moves between tasks as pickles in include/tmp/<name>/<dag_id>/<run_id>/.
"""

import pandas as pd

from nammamart.common import (
    DATA_DIR, FILES, LOYALTY_TIERS, PAYMENT_MODE_MAP, QUARANTINE_DIR, VALID_PAYMENT_STATUS, VALID_STATUS,
    as_of_date, check_schema, connect, increment_files, is_blank, mask_email, mask_name, mask_phone,
    previous_volume, read_csv_text, read_metrics, record_metric, run_dir, safe_run_id, write_dq_results,
)


# ── Extract ──────────────────────────────────────────────────────────────────

def extract(name, run_id, dag_id, path=None):
    """Read one source file as text, check its schema, park it for the validate task."""
    path = path or DATA_DIR / FILES[name]
    if not path.exists():
        raise FileNotFoundError(f"Source file missing: {path}")
    df = read_csv_text(path)
    check_schema("orders" if name.startswith("increment") else name, path, list(df.columns))
    df["_source_file"] = path.name
    df.to_pickle(run_dir(run_id, dag_id) / f"extract_{name}.pkl")
    record_metric(run_id, dag_id, f"extracted_{name}", len(df))
    print(f"[extract] {path.name}: {len(df)} rows, {len(df.columns) - 1} columns")
    return len(df)


def extract_increments(run_id, dag_id):
    files = increment_files()
    for i, path in enumerate(files):
        extract(f"increment_{i}", run_id, dag_id, path)
    return len(files)


# ── Validate ─────────────────────────────────────────────────────────────────

class Checker:
    """Runs checks on one dataframe; Critical failures collect a failure_reason, every check goes to dq_results."""

    def __init__(self, df, file, results):
        self.df, self.file, self.results = df, file, results
        self.raw = df.copy()  # quarantine shows rows exactly as received, before standardising
        self.reasons = pd.Series([""] * len(df), index=df.index, dtype=object)

    def check(self, name, dimension, severity, failed, rows_checked=None):
        failed = pd.Series(failed, index=self.df.index).fillna(True).astype(bool) \
            if not isinstance(failed, bool) else failed
        n_failed = int(failed.sum()) if not isinstance(failed, bool) else int(failed)
        self.results.append(dict(check_name=f"{self.file}.{name}", dimension=dimension, severity=severity,
                                 rows_checked=rows_checked if rows_checked is not None else len(self.df),
                                 rows_failed=n_failed))
        if severity == "Critical" and not isinstance(failed, bool):
            self.reasons[failed] = self.reasons[failed] + name + "; "

    def split(self):
        failed = self.reasons != ""
        bad = self.raw[failed].copy()
        bad["failure_reason"] = self.reasons[failed].str.rstrip("; ")
        return self.df[~failed].copy(), bad


def num(s):
    return pd.to_numeric(s.astype(str).str.strip(), errors="coerce")


def check_volume(c, con, dag_id, run_id):
    """Volume pillar: warn when a file shrinks by more than 90% against the previous run."""
    check_name = f"{c.file}.row_count_vs_previous_run"
    prev = previous_volume(con, dag_id, check_name, run_id)
    dropped = prev is not None and len(c.df) < 0.1 * prev
    c.check("row_count_vs_previous_run", "Completeness", "Warning", dropped, rows_checked=len(c.df))
    if dropped:
        print(f"[volume] WARNING {c.file}: {len(c.df)} rows vs {prev} on the previous run (>90% drop)")


def validate_stores(df, results):
    c = Checker(df, "stores", results)
    cap = num(df["capacity_orders_per_day"])
    c.check("store_id_unique", "Uniqueness", "Critical", df["store_id"].str.strip().duplicated())
    c.check("zone_not_null", "Completeness", "Warning", is_blank(df["zone"]))
    c.check("capacity_positive", "Accuracy", "Warning", ~(cap > 0))
    c.check("pincode_6_digits", "Validity", "Warning", ~df["pincode"].str.strip().str.fullmatch(r"\d{6}"))
    return c


def validate_products(df, results, as_of):
    c = Checker(df, "products", results)
    mrp, cost = num(df["mrp"]), num(df["cost_price"])
    launch = pd.to_datetime(df["launch_date"].str.strip(), format="%Y-%m-%d", errors="coerce")
    # keep the current row when a product appears twice: rows tagged "(old)" lose
    is_old = df["product_name"].str.contains("(old)", regex=False)
    dup = df.assign(_old=is_old).sort_values("_old", kind="stable")["product_id"].str.strip().duplicated()
    c.check("product_id_unique", "Uniqueness", "Critical", dup.reindex(df.index))
    c.check("category_not_null", "Completeness", "Critical", is_blank(df["category"]))
    c.check("mrp_positive", "Accuracy", "Critical", ~(mrp > 0))
    c.check("cost_price_le_mrp", "Accuracy", "Critical", ~(cost <= mrp))
    c.check("launch_date_not_future", "Timeliness", "Warning", launch > pd.Timestamp(as_of))
    return c


def validate_customers(df, results, as_of):
    c = Checker(df, "customers", results)
    signup = pd.to_datetime(df["signup_date"].str.strip(), format="%Y-%m-%d", errors="coerce")
    email = df["email"].str.strip()
    c.check("customer_id_unique", "Uniqueness", "Critical", df["customer_id"].str.strip().duplicated(keep="last"))
    c.check("signup_date_valid", "Validity", "Critical", signup.isna())
    c.check("signup_date_not_future", "Timeliness", "Critical", signup > pd.Timestamp(as_of))
    c.check("email_not_null", "Completeness", "Warning", is_blank(email))
    c.check("email_format", "Validity", "Warning",
            ~is_blank(email) & ~email.str.fullmatch(r"[^@\s]+@[^@\s]+\.[A-Za-z]{2,}"))
    c.check("phone_10_digits", "Validity", "Warning", ~df["phone"].str.strip().str.fullmatch(r"\d{10}"))
    c.check("pincode_6_digits", "Validity", "Warning", ~df["pincode"].str.strip().str.fullmatch(r"560\d{3}"))
    c.check("city_not_null", "Completeness", "Warning", is_blank(df["city"]))
    c.check("loyalty_tier_casing", "Consistency", "Warning",
            ~df["loyalty_tier"].isin(set(LOYALTY_TIERS.values())))
    c.check("loyalty_tier_allowed", "Validity", "Critical",
            ~df["loyalty_tier"].str.strip().str.lower().isin(LOYALTY_TIERS))
    return c


def validate_orders(df, file, results, customer_ids, products, store_ids, as_of):
    c = Checker(df, file, results)
    s = {col: df[col].astype(str).str.strip() for col in df.columns}
    ts = pd.to_datetime(s["order_ts"], format="%Y-%m-%d %H:%M:%S", errors="coerce")
    qty, price, disc, amt, mins = (num(df[k]) for k in
                                   ("quantity", "unit_price", "discount_pct", "order_amount", "delivery_minutes"))
    status = s["order_status"].str.upper()
    mode = s["payment_mode"].str.lower().map(PAYMENT_MODE_MAP)
    expected = (qty * price * (1 - disc / 100)).round(2)
    mrp = s["product_id"].map(products.set_index("product_id")["mrp"])

    c.check("order_id_unique", "Uniqueness", "Critical", df["order_id"].duplicated(keep="first"))
    c.check("customer_id_not_null", "Completeness", "Critical", is_blank(df["customer_id"]))
    c.check("customer_id_in_master", "Consistency", "Critical",
            ~is_blank(df["customer_id"]) & ~s["customer_id"].isin(customer_ids))
    c.check("product_id_in_master", "Consistency", "Critical", ~s["product_id"].isin(products["product_id"]))
    c.check("store_id_in_master", "Consistency", "Critical", ~s["store_id"].isin(store_ids))
    c.check("order_ts_not_null", "Completeness", "Critical", is_blank(df["order_ts"]))
    c.check("order_ts_valid_timestamp", "Validity", "Critical", ~is_blank(df["order_ts"]) & ts.isna())
    c.check("order_ts_not_future", "Timeliness", "Critical", ts.dt.normalize() > pd.Timestamp(as_of))
    c.check("quantity_positive", "Accuracy", "Critical", ~(qty > 0))
    c.check("discount_pct_0_to_100", "Validity", "Critical", ~disc.between(0, 100))
    c.check("order_amount_matches_formula", "Accuracy", "Critical", ~((expected - amt).abs() <= 0.01))
    c.check("order_status_allowed", "Validity", "Critical", ~status.isin(VALID_STATUS))
    c.check("payment_mode_allowed", "Validity", "Critical", mode.isna())
    c.check("delivered_has_delivery_minutes", "Completeness", "Critical", (status == "DELIVERED") & mins.isna())
    c.check("delivery_minutes_below_120", "Accuracy", "Critical", (mins >= 120) | (mins < 0))
    c.check("payment_mode_standard_format", "Consistency", "Warning", mode.notna() & (df["payment_mode"] != mode))
    c.check("order_status_upper_case", "Consistency", "Warning", df["order_status"] != status)
    c.check("delivery_minutes_8_to_35", "Accuracy", "Warning", mins.notna() & ~mins.between(8, 35))
    c.check("unit_price_equals_mrp", "Accuracy", "Warning", mrp.notna() & ((price - mrp).abs() > 0.01))
    latest = ts[ts.dt.normalize() <= pd.Timestamp(as_of)].max()  # ignore future-dated rows
    stale = pd.isna(latest) or latest < pd.Timestamp(as_of) - pd.Timedelta(days=1)
    c.check("latest_order_within_1_day", "Timeliness", "Warning", bool(stale), rows_checked=1)
    if stale:
        print(f"[freshness] WARNING {file}: latest order_ts {latest} is more than 1 day before {as_of}")

    # standardise the values that passed so transform gets clean types
    df["order_ts"], df["order_status"], df["payment_mode"] = ts, status, mode
    for col, val in (("quantity", qty), ("unit_price", price), ("discount_pct", disc), ("order_amount", amt),
                     ("delivery_minutes", mins)):
        df[col] = val
    for col in ("order_id", "customer_id", "store_id", "product_id", "channel"):
        df[col] = s[col]
    return c


def validate_payments(df, results, order_ids, as_of):
    c = Checker(df, "payments", results)
    ts = pd.to_datetime(df["payment_ts"].str.strip(), format="%Y-%m-%d %H:%M:%S", errors="coerce")
    mode = df["payment_mode"].str.strip().str.lower().map(PAYMENT_MODE_MAP)
    status = df["payment_status"].str.strip().str.upper()
    amt = num(df["amount_paid"])
    c.check("payment_id_unique", "Uniqueness", "Critical", df["payment_id"].duplicated(keep="first"))
    c.check("order_id_in_orders", "Consistency", "Critical", ~df["order_id"].str.strip().isin(order_ids))
    c.check("payment_ts_valid_timestamp", "Validity", "Critical", ts.isna())
    c.check("payment_ts_not_future", "Timeliness", "Critical", ts.dt.normalize() > pd.Timestamp(as_of))
    c.check("payment_mode_allowed", "Validity", "Critical", mode.isna())
    c.check("payment_status_allowed", "Validity", "Critical", ~status.isin(VALID_PAYMENT_STATUS))
    c.check("success_amount_positive", "Accuracy", "Critical", (status == "SUCCESS") & ~(amt > 0))
    c.check("payment_mode_standard_format", "Consistency", "Warning", mode.notna() & (df["payment_mode"] != mode))
    c.check("gateway_ref_present_for_non_cash", "Completeness", "Warning",
            (mode != "Cash on Delivery") & is_blank(df["gateway_ref"]))
    df["payment_ts"], df["payment_mode"], df["payment_status"], df["amount_paid"] = ts, mode, status, amt
    return c


def validate(run_id, dag_id):
    """Split every file into passed and failed rows; failed rows go to quarantine with a failure_reason."""
    d = run_dir(run_id, dag_id)
    as_of = as_of_date()
    raw = {p.stem.replace("extract_", ""): pd.read_pickle(p) for p in d.glob("extract_*.pkl")}
    results, passed, quarantined = [], {}, 0
    con = connect()
    try:
        checkers = {}
        checkers["stores"] = validate_stores(raw["stores"], results)
        checkers["products"] = validate_products(raw["products"], results, as_of)
        checkers["customers"] = validate_customers(raw["customers"], results, as_of)
        for name in ("stores", "products", "customers"):
            passed[name], bad = checkers[name].split()
            quarantined += write_quarantine(name, bad, run_id)

        products = passed["products"].assign(mrp=lambda x: num(x["mrp"]))
        args = (set(passed["customers"]["customer_id"]), products, set(passed["stores"]["store_id"]), as_of)
        checkers["orders"] = validate_orders(raw["orders"], "orders", results, *args)
        passed["orders"], bad = checkers["orders"].split()
        quarantined += write_quarantine("orders", bad, run_id)
        order_ids = set(raw["orders"]["order_id"].str.strip())
        for key in sorted(k for k in raw if k.startswith("increment_")):
            name = raw[key]["_source_file"].iloc[0].removesuffix(".csv")
            checkers[key] = validate_orders(raw[key], name, results, *args)
            passed[key], bad = checkers[key].split()
            quarantined += write_quarantine(name, bad, run_id)
            order_ids |= set(raw[key]["order_id"].str.strip())

        checkers["payments"] = validate_payments(raw["payments"], results, order_ids, as_of)
        passed["payments"], bad = checkers["payments"].split()
        quarantined += write_quarantine("payments", bad, run_id)

        for c in checkers.values():
            check_volume(c, con, dag_id, run_id)
        write_dq_results(con, run_id, dag_id, results)
    finally:
        con.close()

    for name, df in passed.items():
        df.to_pickle(d / f"passed_{name}.pkl")
    extracted = sum(len(df) for df in raw.values())
    record_metric(run_id, dag_id, "rows_extracted", extracted)
    record_metric(run_id, dag_id, "rows_quarantined", quarantined)
    failed_checks = [r for r in results if r["rows_failed"]]
    print(f"[validate] {extracted} rows in, {quarantined} quarantined. Checks with failures:")
    for r in failed_checks:
        print(f"  {r['severity']:8s} {r['dimension']:12s} {r['check_name']}: {r['rows_failed']}/{r['rows_checked']}")
    return {"rows_extracted": extracted, "rows_quarantined": quarantined}


def write_quarantine(name, bad, run_id):
    if bad.empty:
        return 0
    QUARANTINE_DIR.mkdir(parents=True, exist_ok=True)
    path = QUARANTINE_DIR / f"{name}_failed_{safe_run_id(run_id)}.csv"
    out = bad.drop(columns=[c for c in bad.columns if c.startswith("_")], errors="ignore")
    out = out.drop(columns=["email", "phone", "full_name"], errors="ignore") if name == "customers" else out
    # customers' raw PII stays in the source system; quarantine keeps the key, the masked values and the reason
    if name == "customers":
        out.insert(1, "email_masked", bad["email"].map(mask_email))
        out.insert(2, "phone_masked", bad["phone"].map(mask_phone))
    out.to_csv(path, index=False)
    print(f"[quarantine] {len(bad)} rows -> {path}")
    return len(bad)


# ── Transform ────────────────────────────────────────────────────────────────

def transform(run_id, dag_id):
    d = run_dir(run_id, dag_id)
    p = {f.stem.replace("passed_", ""): pd.read_pickle(f) for f in d.glob("passed_*.pkl")}

    stores = p["stores"].copy()
    stores["zone"] = stores["zone"].where(~is_blank(stores["zone"]), "Unassigned")
    stores["capacity_orders_per_day"] = num(stores["capacity_orders_per_day"]).astype("Int64")
    stores["open_date"] = pd.to_datetime(stores["open_date"], errors="coerce").dt.date

    products = p["products"].copy()
    for col in ("mrp", "cost_price"):
        products[col] = num(products[col])
    products["is_perishable"] = products["is_perishable"].str.strip().str.lower() == "true"
    products["launch_date"] = pd.to_datetime(products["launch_date"], errors="coerce").dt.date

    cust = p["customers"].copy()
    customers = pd.DataFrame({
        "customer_id": cust["customer_id"].str.strip(),
        "customer_name": cust["full_name"].map(mask_name),
        "email_masked": cust["email"].map(mask_email),
        "phone_masked": cust["phone"].map(mask_phone),
        "city": cust["city"].where(~is_blank(cust["city"]), None),
        "area": cust["area"],
        "pincode": cust["pincode"].where(cust["pincode"].str.fullmatch(r"560\d{3}"), None),
        "signup_date": pd.to_datetime(cust["signup_date"]).dt.date,
        "loyalty_tier": cust["loyalty_tier"].str.strip().str.lower().map(LOYALTY_TIERS),
        "is_active": cust["is_active"].str.strip().str.upper() == "Y",
    })

    def build_fact(orders):
        f = orders.merge(products[["product_id", "cost_price"]], on="product_id", how="left")
        delivered = f["order_status"] == "DELIVERED"
        f["order_date"] = f["order_ts"].dt.date
        f["net_revenue"] = f["order_amount"].where(delivered, 0.0).round(2)
        f["cost_amount"] = (f["quantity"] * f["cost_price"]).where(delivered, 0.0).round(2)
        f["gross_margin"] = (f["net_revenue"] - f["cost_amount"]).round(2)
        f["within_15_min"] = (f["delivery_minutes"] <= 15).where(delivered)
        f["quantity"] = f["quantity"].astype("Int64")
        f["delivery_minutes"] = f["delivery_minutes"].astype("Int64")
        f["_run_id"] = run_id
        f["_loaded_at"] = pd.Timestamp.now()
        return f.drop(columns=["cost_price"])

    stores.to_pickle(d / "dim_store.pkl")
    products.drop(columns=["_source_file"]).to_pickle(d / "dim_product.pkl")
    customers.to_pickle(d / "dim_customer.pkl")
    batches = ["orders"] + sorted(k for k in p if k.startswith("increment_"))
    for i, key in enumerate(batches):
        build_fact(p[key]).to_pickle(d / f"fact_batch_{i}.pkl")
    p["payments"].to_pickle(d / "payments_clean.pkl")
    print(f"[transform] dims: {len(stores)} stores, {len(products)} products, {len(customers)} customers; "
          f"fact batches: {[len(p[k]) for k in batches]}")


# ── Load ─────────────────────────────────────────────────────────────────────

FACT_COLUMNS = ["order_id", "order_ts", "order_date", "customer_id", "store_id", "product_id", "quantity",
                "unit_price", "discount_pct", "order_amount", "payment_mode", "order_status", "channel",
                "delivery_minutes", "net_revenue", "cost_amount", "gross_margin", "within_15_min",
                "_source_file", "_run_id", "_loaded_at"]


def load(run_id, dag_id):
    """Idempotent: dimensions are replaced, facts are upserted on order_id (delete + insert in one transaction)."""
    d = run_dir(run_id, dag_id)
    con = connect()
    try:
        for dim in ("dim_store", "dim_product", "dim_customer"):
            df = pd.read_pickle(d / f"{dim}.pkl")
            con.register("df", df)
            con.execute(f"CREATE OR REPLACE TABLE etl_{dim} AS SELECT * FROM df")
            con.unregister("df")
        loaded = 0
        for path in sorted(d.glob("fact_batch_*.pkl")):
            df = pd.read_pickle(path)[FACT_COLUMNS]
            con.register("df", df)
            con.execute("CREATE TABLE IF NOT EXISTS etl_fact_orders AS SELECT * FROM df LIMIT 0")
            con.execute("BEGIN")
            if path.name == "fact_batch_0.pkl":
                # the full orders export: replace everything that came from it (rows that now fail disappear),
                # but never overwrite an order that a later increment file corrected
                con.execute("DELETE FROM etl_fact_orders WHERE _source_file = 'orders.csv'")
                con.execute("""INSERT INTO etl_fact_orders BY NAME SELECT * FROM df
                               WHERE order_id NOT IN (SELECT order_id FROM etl_fact_orders)""")
            else:
                # increment file: upsert on order_id
                con.execute("DELETE FROM etl_fact_orders WHERE order_id IN (SELECT order_id FROM df)")
                con.execute("INSERT INTO etl_fact_orders BY NAME SELECT * FROM df")
            con.execute("COMMIT")
            con.unregister("df")
            loaded += len(df)
            print(f"[load] upserted {len(df)} rows from {df['_source_file'].iloc[0] if len(df) else path.name}")
        total = con.execute("SELECT count(*) FROM etl_fact_orders").fetchone()[0]
    finally:
        con.close()
    record_metric(run_id, dag_id, "rows_loaded", loaded)
    print(f"[load] etl_fact_orders now holds {total} rows")
    return loaded


# ── Reconcile ────────────────────────────────────────────────────────────────

RECONCILE_SQL = """
CREATE OR REPLACE TABLE {prefix}payment_reconciliation AS
WITH pay AS (
    SELECT order_id,
           count(*) FILTER (WHERE payment_status = 'SUCCESS')  AS n_success,
           sum(amount_paid) FILTER (WHERE payment_status = 'SUCCESS') AS amount_success,
           bool_or(payment_status = 'FAILED')   AS any_failed,
           bool_or(payment_status = 'REFUNDED') AS any_refunded,
           string_agg(payment_id, ',' ORDER BY payment_id) AS payment_ids
    FROM {payments} GROUP BY order_id
),
o AS (
    SELECT f.order_id, f.order_ts, f.order_status, f.order_amount, p.payment_ids, p.n_success, p.amount_success,
           p.any_failed, p.any_refunded
    FROM {orders} f LEFT JOIN pay p USING (order_id)
),
mismatches AS (
    SELECT order_id, payment_ids AS payment_id, order_status, order_amount, amount_success AS amount_paid,
        CASE
            WHEN payment_ids IS NULL AND order_ts > (SELECT max(payment_ts) FROM {payments})
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
           CASE WHEN order_id IN (SELECT order_id FROM {quarantined_orders})
                THEN 'payment_for_quarantined_order' ELSE 'payment_without_order' END AS reason
    FROM {all_payments}
    WHERE payment_status = 'SUCCESS' AND order_id NOT IN (SELECT order_id FROM {orders})
)
SELECT *, round(coalesce(amount_paid, 0) - coalesce(CASE WHEN order_status = 'CANCELLED' THEN 0 ELSE order_amount END, 0), 2)
          AS difference
FROM (SELECT * FROM mismatches WHERE reason IS NOT NULL UNION ALL SELECT * FROM orphan)
ORDER BY reason, order_id
"""


def reconcile(run_id, dag_id):
    d = run_dir(run_id, dag_id)
    clean = pd.read_pickle(d / "payments_clean.pkl")
    raw = pd.read_pickle(d / "extract_payments.pkl").drop_duplicates("payment_id")
    raw = raw.assign(amount_paid=num(raw["amount_paid"]),
                     payment_status=raw["payment_status"].str.strip().str.upper(),
                     order_id=raw["order_id"].str.strip())
    quarantined_ids = set()
    for f in d.glob("extract_*.pkl"):
        if "orders" in f.stem or "increment" in f.stem:
            quarantined_ids |= set(pd.read_pickle(f)["order_id"].str.strip())
    con = connect()
    try:
        con.register("payments_clean", clean)
        con.register("payments_all", raw)
        con.register("order_ids_seen", pd.DataFrame({"order_id": sorted(quarantined_ids)}))
        con.execute(RECONCILE_SQL.format(prefix="etl_", payments="payments_clean", orders="etl_fact_orders",
                                         all_payments="payments_all", quarantined_orders="order_ids_seen"))
        summary = con.execute("""SELECT reason, count(*) n, round(sum(abs(difference)), 2) amount
                                 FROM etl_payment_reconciliation GROUP BY reason ORDER BY n DESC""").fetchall()
    finally:
        con.close()
    print("[reconcile] etl_payment_reconciliation:")
    for reason, n, amount in summary:
        print(f"  {reason:32s} {n:4d}  ₹{amount:,.2f}")
    return len(summary)


# ── Report ───────────────────────────────────────────────────────────────────

def report(run_id, dag_id):
    con = connect()
    try:
        con.execute("""
            CREATE OR REPLACE TABLE etl_daily_zone_revenue AS
            SELECT f.order_date, s.zone, s.store_id, s.store_name,
                   count(*) FILTER (WHERE f.order_status = 'DELIVERED') AS delivered_orders,
                   round(sum(f.net_revenue), 2) AS net_revenue
            FROM etl_fact_orders f JOIN etl_dim_store s USING (store_id)
            GROUP BY ALL ORDER BY f.order_date, s.zone, s.store_id""")
        con.execute("""
            CREATE OR REPLACE TABLE etl_category_margin AS
            SELECT p.category, round(sum(f.net_revenue), 2) AS revenue, round(sum(f.cost_amount), 2) AS cost,
                   round(sum(f.gross_margin), 2) AS gross_margin,
                   round(100 * sum(f.gross_margin) / nullif(sum(f.net_revenue), 0), 1) AS margin_pct
            FROM etl_fact_orders f JOIN etl_dim_product p USING (product_id)
            GROUP BY ALL ORDER BY revenue DESC""")
        zone = con.execute("""SELECT zone, round(sum(net_revenue), 2) FROM etl_daily_zone_revenue
                              GROUP BY zone ORDER BY 2 DESC""").fetchall()
        cat = con.execute("SELECT * FROM etl_category_margin").fetchall()
    finally:
        con.close()
    print("[report] net revenue by zone:", zone)
    print("[report] category margin:")
    for row in cat:
        print("  ", row)
