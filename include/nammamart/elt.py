"""ELT pipeline logic: Extract -> Load raw (all text, untouched) -> Transform in DuckDB with the SQL in include/sql/elt.

Quality checks in the staging SQL are boolean columns named c__<Severity>__<Dimension>__<check_name>.
finalize_stage() turns them into dq_status / failure_reason and writes one dq_results row per check.
"""

from datetime import datetime, timedelta

from nammamart.common import (
    DATA_DIR, FILES, SQL_DIR, as_of_date, check_schema, connect, file_hash, increment_files, previous_volume,
    record_metric, write_dq_results,
)

ELT_SQL = SQL_DIR / "elt"
LOG_DDL = """CREATE TABLE IF NOT EXISTS raw_load_log (run_id VARCHAR, dag_id VARCHAR, raw_table VARCHAR,
    source_file VARCHAR, file_hash VARCHAR, rows_in_file BIGINT, rows_appended BIGINT, loaded_at TIMESTAMP)"""


def session(run_id):
    con = connect()
    con.execute("SET VARIABLE run_id = ?", [run_id])
    con.execute("SET VARIABLE as_of = ?::DATE", [as_of_date().isoformat()])
    return con


def run_sql(con, filename):
    print(f"[sql] {filename}")
    con.execute((ELT_SQL / filename).read_text())


# ── Load raw ─────────────────────────────────────────────────────────────────

def load_raw(name, run_id, dag_id, path=None):
    """Append the file to raw_<table> exactly as received (all VARCHAR). Raw is never cleaned or deleted.

    A file whose content was already loaded (same md5) is not appended again, so re-runs don't grow raw.
    """
    path = path or DATA_DIR / FILES[name]
    table = "raw_orders" if name.startswith("increment") else f"raw_{name}"
    if not path.exists():
        raise FileNotFoundError(f"Source file missing: {path}")
    h = file_hash(path)
    src = (f"SELECT *, '{path.name}' AS _source_file, '{h}' AS _file_hash, $run_id AS _run_id, "
           f"now()::TIMESTAMP AS _loaded_at, row_number() OVER () AS _row_num "
           f"FROM read_csv('{path}', all_varchar = true, header = true, nullstr = '\\N')")
    con = session(run_id)
    try:
        columns = [r[0] for r in con.execute(f"DESCRIBE SELECT * FROM read_csv('{path}', all_varchar = true)").fetchall()]
        check_schema("orders" if name.startswith("increment") else name, path, columns)
        con.execute(f"CREATE TABLE IF NOT EXISTS {table} AS {src} LIMIT 0", {"run_id": run_id})
        rows = con.execute(f"SELECT count(*) FROM read_csv('{path}', all_varchar = true)").fetchone()[0]
        already = con.execute(f"SELECT count(*) FROM {table} WHERE _file_hash = ?", [h]).fetchone()[0]
        appended = 0
        if not already:
            con.execute(f"INSERT INTO {table} BY NAME {src}", {"run_id": run_id})
            appended = rows
        con.execute(LOG_DDL)
        con.execute("DELETE FROM raw_load_log WHERE run_id = ? AND dag_id = ? AND source_file = ?",
                    [run_id, dag_id, path.name])
        con.execute("INSERT INTO raw_load_log VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                    [run_id, dag_id, table, path.name, h, rows, appended, datetime.now()])
        total = con.execute(f"SELECT count(*) FROM {table}").fetchone()[0]
    finally:
        con.close()
    record_metric(run_id, dag_id, f"extracted_{name}", rows)
    print(f"[raw] {path.name}: {rows} rows in file, {appended} appended "
          f"({'already loaded' if already else 'new content'}); {table} now {total} rows")
    return rows


def load_raw_increments(run_id, dag_id):
    files = increment_files()
    for i, path in enumerate(files):
        load_raw(f"increment_{i}", run_id, dag_id, path)
    return len(files)


# ── Staging ──────────────────────────────────────────────────────────────────

def finalize_stage(con, table, file_label, run_id, dag_id):
    """Add dq_status / failure_reason from the c__ check columns and record each check in dq_results."""
    checks = [c for c in con.table(table).columns if c.startswith("c__")]
    critical = [c for c in checks if c.split("__")[1] == "Critical"]
    reasons = ", ".join(f"CASE WHEN \"{c}\" THEN '{c.split('__')[3]}' END" for c in critical)
    con.execute(f"""
        CREATE OR REPLACE TABLE {table} AS
        SELECT *, CASE WHEN failure_reason = '' THEN 'PASS' ELSE 'FAIL' END AS dq_status
        FROM (SELECT * REPLACE ({", ".join(f'coalesce("{c}", true) AS "{c}"' for c in checks)}),
                     concat_ws('; ', {reasons}) AS failure_reason
              FROM {table})""")
    con.execute(f"UPDATE {table} SET failure_reason = NULL WHERE failure_reason = ''")
    counts = con.execute(f"SELECT count(*), {', '.join(f'count_if(\"{c}\")' for c in checks)} FROM {table}").fetchone()
    results = [dict(check_name=f"{file_label}.{c.split('__')[3]}", dimension=c.split("__")[2],
                    severity=c.split("__")[1], rows_checked=counts[0], rows_failed=counts[i + 1])
               for i, c in enumerate(checks)]
    # Volume pillar: warn when a file shrinks by more than 90% against the previous run
    prev = previous_volume(con, dag_id, f"{file_label}.row_count_vs_previous_run", run_id)
    dropped = prev is not None and counts[0] < 0.1 * prev
    results.append(dict(check_name=f"{file_label}.row_count_vs_previous_run", dimension="Completeness",
                        severity="Warning", rows_checked=counts[0], rows_failed=int(dropped)))
    if dropped:
        print(f"[volume] WARNING {file_label}: {counts[0]} rows vs {prev} on the previous run (>90% drop)")
    write_dq_results(con, run_id, dag_id, results)
    failed = con.execute(f"SELECT count(*) FROM {table} WHERE dq_status = 'FAIL'").fetchone()[0]
    print(f"[stage] {table}: {counts[0]} rows, {failed} FAIL")
    return failed


def freshness_check(con, table, file_label, run_id, dag_id):
    latest = con.execute(f"SELECT max(order_ts) FROM {table} WHERE dq_status = 'PASS'").fetchone()[0]
    stale = latest is None or latest < datetime.combine(as_of_date(), datetime.min.time()) - timedelta(days=1)
    write_dq_results(con, run_id, dag_id, [dict(check_name=f"{file_label}.latest_order_within_1_day",
                                                dimension="Timeliness", severity="Warning",
                                                rows_checked=1, rows_failed=int(stale))])
    if stale:
        print(f"[freshness] WARNING {file_label}: latest order_ts {latest} is more than 1 day before {as_of_date()}")


def build_staging(run_id, dag_id):
    con = session(run_id)
    quarantined = 0
    try:
        run_sql(con, "00_macros.sql")
        for sql, table, label in (("01_stg_stores.sql", "stg_stores", "stores"),
                                  ("02_stg_products.sql", "stg_products", "products"),
                                  ("03_stg_customers.sql", "stg_customers", "customers")):
            run_sql(con, sql)
            quarantined += finalize_stage(con, table, label, run_id, dag_id)
        run_sql(con, "04_orders_checked_macro.sql")
        run_sql(con, "05_stg_orders.sql")
        quarantined += finalize_stage(con, "stg_orders", "orders", run_id, dag_id)
        freshness_check(con, "stg_orders", "orders", run_id, dag_id)
    finally:
        con.close()
    record_metric(run_id, dag_id, "rows_quarantined_masters_orders", quarantined)


def merge_increments(run_id, dag_id):
    """Raw already has the increment rows appended; here they are validated and MERGEd into stg_orders."""
    con = session(run_id)
    try:
        has_increment = con.execute("""SELECT count(*) FROM raw_load_log
                                       WHERE source_file LIKE '%_increment.csv'""").fetchone()[0]
        if not has_increment:
            print("[merge] no increment file loaded yet")
            record_metric(run_id, dag_id, "rows_quarantined_increment", 0)
            return 0
        before = con.execute("SELECT count(*) FROM stg_orders").fetchone()[0]
        run_sql(con, "06_stg_orders_increment.sql")
        failed = finalize_stage(con, "stg_orders_increment", "orders_increment", run_id, dag_id)
        updated = con.execute("""SELECT count(*) FROM stg_orders_increment s JOIN stg_orders t USING (order_id)
                                 WHERE s.dq_status = 'PASS' AND t._dup_rank = 1""").fetchone()[0]
        run_sql(con, "07_merge_increment.sql")
        after = con.execute("SELECT count(*) FROM stg_orders").fetchone()[0]
    finally:
        con.close()
    print(f"[merge] stg_orders: {after - before} inserted, {updated} updated, {failed} increment rows FAIL")
    record_metric(run_id, dag_id, "rows_quarantined_increment", failed)
    return after - before


def build_marts(run_id, dag_id):
    con = session(run_id)
    try:
        run_sql(con, "08_stg_payments.sql")
        failed = finalize_stage(con, "stg_payments", "payments", run_id, dag_id)
        for sql in sorted(p.name for p in ELT_SQL.glob("1*_mart_*.sql")):
            run_sql(con, sql)
        loaded = con.execute("SELECT count(*) FROM stg_orders WHERE dq_status = 'PASS'").fetchone()[0]
        zone = con.execute("""SELECT zone, round(sum(net_revenue), 2) FROM mart_daily_store_kpis
                              GROUP BY zone ORDER BY 2 DESC""").fetchall()
        recon = con.execute("""SELECT reason, count(*), round(sum(abs(difference)), 2) FROM mart_payment_reconciliation
                               GROUP BY reason ORDER BY 2 DESC""").fetchall()
    finally:
        con.close()
    from nammamart.common import read_metrics
    m = read_metrics(run_id, dag_id)
    record_metric(run_id, dag_id, "rows_extracted", sum(v for k, v in m.items() if k.startswith("extracted_")))
    record_metric(run_id, dag_id, "rows_quarantined", failed + m.get("rows_quarantined_masters_orders", 0)
                  + m.get("rows_quarantined_increment", 0))
    record_metric(run_id, dag_id, "rows_loaded", loaded)
    record_metric(run_id, dag_id, "report_done", True)
    print("[marts] net revenue by zone:", zone)
    print("[marts] reconciliation:", recon)
