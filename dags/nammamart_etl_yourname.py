"""
NammaMart ETL: Extract -> Validate -> Transform -> Load (pandas, then DuckDB star schema)

  extract_stores ────┐
  extract_products ──┤
  extract_customers ─┼─► validate ─► transform ─► load ─► reconcile ─► report ─► run_audit (all_done)
  extract_orders ────┤      │
  extract_payments ──┤      └─ failed rows -> include/quarantine/<name>/<file>_failed_<run_id>.csv
  extract_increment ─┘

Logic lives in include/nammamart/etl.py so it can be tested without Airflow (include/nammamart/run_local.py).
"""

import sys
from datetime import timedelta
from pathlib import Path

import pendulum
from airflow.decorators import dag, task

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "include"))

from nammamart import common, etl  # noqa: E402

DAG_ID = f"nammamart_etl_{common.NAME}"

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
    tags=["nammamart", "etl", common.NAME],
)
def nammamart_etl():

    def make_extract(name):
        @task(task_id=f"extract_{name}")
        def _extract(run_id=None):
            return etl.extract(name, run_id, DAG_ID)
        return _extract()

    @task
    def extract_increment(run_id=None):
        return etl.extract_increments(run_id, DAG_ID)

    @task
    def validate(run_id=None):
        return etl.validate(run_id, DAG_ID)

    @task
    def transform(run_id=None):
        etl.transform(run_id, DAG_ID)

    @task
    def load(run_id=None):
        return etl.load(run_id, DAG_ID)

    @task
    def reconcile(run_id=None):
        etl.reconcile(run_id, DAG_ID)

    @task
    def report(run_id=None):
        etl.report(run_id, DAG_ID)

    @task(trigger_rule="all_done", retries=0)
    def run_audit(run_id=None, dag_run=None):
        metrics = common.read_metrics(run_id, DAG_ID)
        status = "success" if "report_done" in metrics else "failed"
        start = getattr(dag_run, "start_date", None) or pendulum.now("Asia/Kolkata")
        common.write_pipeline_run(run_id, DAG_ID, start, status)

    @task
    def mark_done(run_id=None):
        common.record_metric(run_id, DAG_ID, "report_done", True)

    extracts = [make_extract(n) for n in common.FILES] + [extract_increment()]
    done = mark_done()
    extracts >> validate() >> transform() >> load() >> reconcile() >> report() >> done >> run_audit()


nammamart_etl()
