"""Shared config and helpers for the NammaMart ETL and ELT DAGs."""

import hashlib
import json
import os
import re
import time
from datetime import date, datetime
from pathlib import Path

import duckdb
import pandas as pd

NAME = "yourname"  # also in the two DAG file names

INCLUDE = Path(__file__).resolve().parents[1]
DATA_DIR = INCLUDE / "data" / "nammamart"
SQL_DIR = INCLUDE / "sql"
WAREHOUSE = INCLUDE / f"warehouse_{NAME}.duckdb"
QUARANTINE_DIR = INCLUDE / "quarantine" / NAME
WORK_DIR = INCLUDE / "tmp" / NAME

FILES = {
    "stores": "stores.csv",
    "products": "products.csv",
    "customers": "customers.csv",
    "orders": "orders.csv",
    "payments": "payments.csv",
}
INCREMENT_GLOB = "orders_*_increment.csv"

REQUIRED_COLUMNS = {
    "orders": ["order_id", "order_ts", "customer_id", "store_id", "product_id", "quantity", "unit_price",
               "discount_pct", "order_amount", "payment_mode", "order_status", "channel", "delivery_minutes"],
    "payments": ["payment_id", "order_id", "payment_ts", "payment_mode", "amount_paid", "payment_status",
                 "gateway_ref"],
    "customers": ["customer_id", "full_name", "email", "phone", "city", "area", "pincode", "signup_date",
                  "loyalty_tier", "is_active"],
    "products": ["product_id", "product_name", "category", "sub_category", "brand", "mrp", "cost_price", "unit",
                 "is_perishable", "launch_date"],
    "stores": ["store_id", "store_name", "zone", "area", "pincode", "open_date", "manager_name",
               "capacity_orders_per_day"],
}

VALID_STATUS = {"DELIVERED", "CANCELLED", "RETURNED"}
VALID_PAYMENT_STATUS = {"SUCCESS", "FAILED", "REFUNDED"}
PAYMENT_MODE_MAP = {
    "upi": "UPI", "card": "Card", "wallet": "Wallet",
    "cash on delivery": "Cash on Delivery", "cod": "Cash on Delivery", "cashh": "Cash on Delivery",
}
LOYALTY_TIERS = {"bronze": "Bronze", "silver": "Silver", "gold": "Gold", "platinum": "Platinum"}
NULL_TOKENS = {"", "n/a", "na", "null", "none", "nan"}

DQ_DDL = """CREATE TABLE IF NOT EXISTS dq_results (
    run_id VARCHAR, dag_id VARCHAR, check_name VARCHAR, dimension VARCHAR, severity VARCHAR,
    rows_checked BIGINT, rows_failed BIGINT, status VARCHAR, checked_at TIMESTAMP)"""
RUNS_DDL = """CREATE TABLE IF NOT EXISTS pipeline_runs (
    run_id VARCHAR, dag_id VARCHAR, start_time TIMESTAMP, end_time TIMESTAMP, rows_extracted BIGINT,
    rows_loaded BIGINT, rows_quarantined BIGINT, status VARCHAR)"""


def as_of_date():
    """Business date the run reports on.

    In production this is the run's own date. The assignment files are frozen in Sept/Oct 2026, so it defaults
    to 1 Oct 2026; override with the Airflow Variable or env var NAMMAMART_AS_OF (YYYY-MM-DD).
    """
    value = os.environ.get("NAMMAMART_AS_OF")
    try:
        from airflow.models import Variable
        value = Variable.get("NAMMAMART_AS_OF", default_var=value)
    except Exception:
        pass
    return date.fromisoformat(value or "2026-10-01")


def connect(read_only=False, attempts=90):
    """DuckDB allows one writer process; parallel tasks wait for the lock instead of failing."""
    for _ in range(attempts):
        try:
            return duckdb.connect(str(WAREHOUSE), read_only=read_only)
        except duckdb.IOException:
            time.sleep(2)
    return duckdb.connect(str(WAREHOUSE), read_only=read_only)


def safe_run_id(run_id):
    return re.sub(r"[^A-Za-z0-9_.-]", "_", run_id)


def run_dir(run_id, dag_id):
    d = WORK_DIR / dag_id / safe_run_id(run_id)
    d.mkdir(parents=True, exist_ok=True)
    return d


def increment_files():
    return sorted(DATA_DIR.glob(INCREMENT_GLOB))


def check_schema(name, path, columns):
    """Fail loudly on schema drift instead of loading wrong data silently."""
    expected = REQUIRED_COLUMNS[name]
    missing = [c for c in expected if c not in columns]
    extra = [c for c in columns if c not in expected]
    if missing or extra:
        raise ValueError(f"Schema drift in {path.name}: missing columns {missing}, unexpected columns {extra}")


def file_hash(path):
    return hashlib.md5(Path(path).read_bytes()).hexdigest()


def record_metric(run_id, dag_id, key, value):
    """Small per-run metrics file that the all_done audit task reads, even when upstream tasks failed."""
    path = run_dir(run_id, dag_id) / "metrics.json"
    metrics = json.loads(path.read_text()) if path.exists() else {}
    metrics[key] = value
    path.write_text(json.dumps(metrics, default=str))


def read_metrics(run_id, dag_id):
    path = run_dir(run_id, dag_id) / "metrics.json"
    return json.loads(path.read_text()) if path.exists() else {}


def dq_status(severity, rows_failed):
    if rows_failed == 0:
        return "PASS"
    return "FAIL" if severity == "Critical" else "WARN"


def write_dq_results(con, run_id, dag_id, results):
    """results: list of dicts with check_name, dimension, severity, rows_checked, rows_failed."""
    con.execute(DQ_DDL)
    names = [r["check_name"] for r in results]
    if names:
        con.execute("DELETE FROM dq_results WHERE run_id = ? AND dag_id = ? AND list_contains(?, check_name)",
                    [run_id, dag_id, names])
    now = datetime.now()
    rows = [(run_id, dag_id, r["check_name"], r["dimension"], r["severity"], int(r["rows_checked"]),
             int(r["rows_failed"]), dq_status(r["severity"], r["rows_failed"]), now) for r in results]
    con.executemany("INSERT INTO dq_results VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)", rows)


def previous_volume(con, dag_id, check_name, run_id):
    """rows_checked for the same check on the most recent earlier run (None on the first run)."""
    con.execute(DQ_DDL)
    row = con.execute("""SELECT rows_checked FROM dq_results WHERE dag_id = ? AND check_name = ? AND run_id <> ?
                         ORDER BY checked_at DESC LIMIT 1""", [dag_id, check_name, run_id]).fetchone()
    return row[0] if row else None


def write_pipeline_run(run_id, dag_id, start_time, status):
    m = read_metrics(run_id, dag_id)
    con = connect()
    try:
        con.execute(RUNS_DDL)
        con.execute("DELETE FROM pipeline_runs WHERE run_id = ? AND dag_id = ?", [run_id, dag_id])
        con.execute("INSERT INTO pipeline_runs VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                    [run_id, dag_id, start_time, datetime.now(), m.get("rows_extracted", 0),
                     m.get("rows_loaded", 0), m.get("rows_quarantined", 0), status])
    finally:
        con.close()
    print(f"[audit] {dag_id} {run_id}: {status} {m}")
    return m


# ── PII masking ──────────────────────────────────────────────────────────────

def mask_email(value):
    if not isinstance(value, str) or value.strip().lower() in NULL_TOKENS:
        return None
    local, _, domain = value.strip().partition("@")
    return f"{local[:2]}***@{domain}" if domain else f"{local[:2]}***"


def mask_phone(value):
    digits = re.sub(r"\D", "", value or "")
    if len(digits) < 4:
        return None
    return digits[:2] + "*" * (len(digits) - 4) + digits[-2:]


def mask_name(value):
    parts = (value or "").split()
    if not parts:
        return None
    return parts[0] if len(parts) == 1 else f"{parts[0]} {parts[-1][0]}."


def is_blank(series):
    return series.isna() | series.astype(str).str.strip().str.lower().isin(NULL_TOKENS)


def read_csv_text(path):
    """Read every column as text, exactly as received."""
    return pd.read_csv(path, dtype=str, keep_default_na=False)
