"""Part F data experiments, run against both pipelines without Airflow.

Each experiment swaps a modified copy of a source file into include/data/nammamart/, runs both pipelines
with run_local, records what happened, then restores the original files.

    .venv/bin/python include/nammamart/experiments.py > include/nammamart/experiments_output.txt
"""

import shutil
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import pandas as pd  # noqa: E402

from nammamart import common, run_local  # noqa: E402

D = common.DATA_DIR
INC = D / "orders_2026-10-01_increment.csv"


def counts():
    con = common.connect(read_only=True)
    try:
        q = lambda sql: con.execute(sql).fetchone()[0]  # noqa: E731
        return {
            "etl_fact_orders": q("SELECT count(*) FROM etl_fact_orders"),
            "etl_returned": q("SELECT count(*) FROM etl_fact_orders WHERE order_status = 'RETURNED'"),
            "etl_revenue": q("SELECT round(sum(net_revenue), 2) FROM etl_fact_orders"),
            "raw_orders": q("SELECT count(*) FROM raw_orders"),
            "stg_orders_pass": q("SELECT count(*) FROM stg_orders WHERE dq_status = 'PASS'"),
            "elt_returned": q("SELECT count(*) FROM stg_orders WHERE dq_status = 'PASS' AND order_status = 'RETURNED'"),
            "elt_revenue": q("SELECT round(sum(net_revenue), 2) FROM mart_daily_store_kpis"),
        }
    finally:
        con.close()


def dq(run_ids, like):
    con = common.connect(read_only=True)
    try:
        return con.execute(f"""SELECT dag_id, check_name, severity, rows_failed, status FROM dq_results
                               WHERE run_id IN ({', '.join('?' * len(run_ids))}) AND check_name LIKE ? AND rows_failed > 0
                               ORDER BY dag_id, check_name""", [*run_ids, like]).fetchall()
    finally:
        con.close()


def both():
    etl_run, etl_status = run_local.run_etl()
    elt_run, elt_status = run_local.run_elt()
    print(f"  -> ETL {etl_status}, ELT {elt_status}")
    return [etl_run, elt_run]


def experiment(title):
    print(f"\n\n######## {title} ########")


def main():
    backup = Path(tempfile.mkdtemp())
    for f in D.glob("*.csv"):
        shutil.copy(f, backup / f.name)
    orders = pd.read_csv(backup / "orders.csv", dtype=str, keep_default_na=False)

    def restore():
        for f in D.glob("*.csv"):
            f.unlink()
        for f in backup.glob("*.csv"):
            shutil.copy(f, D / f.name)

    try:
        experiment("1 + 3a. Happy path WITHOUT the increment file")
        INC.unlink()
        both()
        before = counts()
        print("  counts:", before)

        experiment("2. Re-run the same files (idempotency)")
        both()
        print("  counts:", counts())

        experiment("3b. Incremental load: add orders_2026-10-01_increment.csv")
        shutil.copy(backup / INC.name, INC)
        both()
        after = counts()
        print("  counts:", after)
        print("  change:", {k: round(after[k] - before[k], 2) for k in after})

        experiment("5. New bad data: 5 bad rows appended to orders.csv")
        bad = orders.iloc[:5].copy()
        bad["order_id"] = [f"ORD9000{i}" for i in range(1, 6)]
        bad.loc[bad.index[0], "customer_id"] = ""
        bad.loc[bad.index[1], "quantity"] = "-2"
        bad.loc[bad.index[2], "store_id"] = "S42"
        bad.loc[bad.index[3], "order_status"] = "SHIPPED"
        bad.loc[bad.index[4], "order_ts"] = "2027-03-15 10:00:00"
        pd.concat([orders, bad]).to_csv(D / "orders.csv", index=False)
        runs = both()
        for q in sorted((common.QUARANTINE_DIR).glob("orders_failed_*.csv"))[-1:]:
            qdf = pd.read_csv(q, dtype=str)
            print("  ETL quarantine rows for the 5 new orders:")
            print(qdf[qdf["order_id"].str.startswith("ORD9000")][["order_id", "failure_reason"]].to_string(index=False))
        con = common.connect(read_only=True)
        print("  ELT stg_orders rows:")
        print(con.execute("""SELECT order_id, dq_status, failure_reason FROM stg_orders
                             WHERE order_id LIKE 'ORD9000%' ORDER BY order_id""").df().to_string(index=False))
        con.close()
        restore()

        experiment("6. Schema change: order_amount renamed to total")
        orders.rename(columns={"order_amount": "total"}).to_csv(D / "orders.csv", index=False)
        both()
        restore()

        experiment("7. Volume anomaly: only 50 orders")
        orders.head(50).to_csv(D / "orders.csv", index=False)
        runs = both()
        print("  volume checks:", dq(runs, "%row_count_vs_previous_run"))
        restore()

        experiment("8. Distribution drift: unit_price x100 for store S05")
        drift = orders.copy()
        m = drift["store_id"] == "S05"
        drift.loc[m, "unit_price"] = (pd.to_numeric(drift.loc[m, "unit_price"]) * 100).astype(str)
        drift.to_csv(D / "orders.csv", index=False)
        runs = both()
        print("  checks that fired:", dq(runs, "orders.%price%") + dq(runs, "orders.order_amount%"))
        print("  counts:", counts())
        restore()

        experiment("9. Freshness: every order_ts shifted 30 days back")
        old = orders.copy()
        ts = pd.to_datetime(old["order_ts"], format="%Y-%m-%d %H:%M:%S", errors="coerce")
        old.loc[ts.notna(), "order_ts"] = (ts[ts.notna()] - pd.Timedelta(days=30)).dt.strftime("%Y-%m-%d %H:%M:%S")
        old.to_csv(D / "orders.csv", index=False)
        runs = both()
        print("  freshness checks:", dq(runs, "%latest_order_within_1_day"))
        restore()

        experiment("Back to the original files")
        both()
        print("  counts:", counts())
    finally:
        restore()
        shutil.rmtree(backup)


if __name__ == "__main__":
    main()
