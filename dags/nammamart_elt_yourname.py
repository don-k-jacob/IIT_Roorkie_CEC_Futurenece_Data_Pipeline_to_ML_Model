"""
NammaMart ELT: Extract -> Load raw (untouched text) -> Transform inside DuckDB with SQL (include/sql/elt/)

  load_raw_stores ────┐
  load_raw_products ──┤
  load_raw_customers ─┼─► build_staging ─► merge_increment ─► build_marts ─► run_audit (all_done)
  load_raw_orders ────┤   (stg_* + dq)     (MERGE on order_id)  (stg_payments + mart_*)
  load_raw_payments ──┤
  load_raw_increment ─┘

Layers: raw_* (every row as received, never deleted) -> stg_* (typed, deduped, PII masked, dq_status +
failure_reason) -> mart_* (business tables). Logic in include/nammamart/elt.py; SQL in include/sql/elt/.
"""

import sys
from datetime import timedelta
from pathlib import Path

import pendulum
from airflow.decorators import dag, task

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "include"))

from nammamart import common, elt  # noqa: E402

DAG_ID = f"nammamart_elt_{common.NAME}"

default_args = {
    "owner": common.NAME,
    "retries": 2,
    "retry_delay": timedelta(minutes=2),
    "execution_timeout": timedelta(minutes=15),
}


@dag(
    dag_id=DAG_ID,
    schedule="0 9 * * 1-6",  # 9:00 AM, Monday to Saturday, in the start_date's timezone (IST)
    start_date=pendulum.datetime(2026, 10, 1, tz="Asia/Kolkata"),
    catchup=False,
    default_args=default_args,
    tags=["nammamart", "elt", common.NAME],
)
def nammamart_elt():

    def make_load_raw(name):
        @task(task_id=f"load_raw_{name}")
        def _load(run_id=None):
            return elt.load_raw(name, run_id, DAG_ID)
        return _load()

    @task
    def load_raw_increment(run_id=None):
        return elt.load_raw_increments(run_id, DAG_ID)

    @task
    def build_staging(run_id=None):
        elt.build_staging(run_id, DAG_ID)

    @task
    def merge_increment(run_id=None):
        return elt.merge_increments(run_id, DAG_ID)

    @task
    def build_marts(run_id=None):
        elt.build_marts(run_id, DAG_ID)

    @task(trigger_rule="all_done", retries=0)
    def run_audit(run_id=None, dag_run=None):
        metrics = common.read_metrics(run_id, DAG_ID)
        status = "success" if metrics.get("report_done") else "failed"
        start = getattr(dag_run, "start_date", None) or pendulum.now("Asia/Kolkata")
        common.write_pipeline_run(run_id, DAG_ID, start, status)

    raw = [make_load_raw(n) for n in common.FILES] + [load_raw_increment()]
    raw >> build_staging() >> merge_increment() >> build_marts() >> run_audit()


nammamart_elt()
