"""Run the ETL and/or ELT pipeline once without Airflow, in the same task order as the DAGs.

    .venv/bin/python include/nammamart/run_local.py etl
    .venv/bin/python include/nammamart/run_local.py elt
"""

import sys
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from nammamart import common, etl  # noqa: E402

ETL_DAG = f"nammamart_etl_{common.NAME}"
ELT_DAG = f"nammamart_elt_{common.NAME}"


def run(dag_id, steps):
    run_id = f"local__{datetime.now():%Y-%m-%dT%H:%M:%S.%f}"
    start, status = datetime.now(), "success"
    try:
        for step in steps:
            step(run_id, dag_id)
    except Exception as e:
        status = "failed"
        print(f"[{dag_id}] FAILED: {type(e).__name__}: {e}")
    common.write_pipeline_run(run_id, dag_id, start, status)
    return run_id, status


def run_etl():
    steps = [lambda r, d, n=n: etl.extract(n, r, d) for n in common.FILES]
    steps += [etl.extract_increments, etl.validate, etl.transform, etl.load, etl.reconcile, etl.report]
    return run(ETL_DAG, steps)


def run_elt():
    from nammamart import elt
    steps = [lambda r, d, n=n: elt.load_raw(n, r, d) for n in common.FILES]
    steps += [elt.load_raw_increments, elt.build_staging, elt.merge_increments, elt.build_marts]
    return run(ELT_DAG, steps)


if __name__ == "__main__":
    for which in sys.argv[1:] or ["etl", "elt"]:
        print(f"\n===== {which.upper()} =====")
        {"etl": run_etl, "elt": run_elt}[which]()
