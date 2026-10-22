-- rows rejected by the latest run of each DAG, by file and check (one row can fail several checks)
SELECT dag_id, split_part(check_name, '.', 1) AS file, split_part(check_name, '.', 2) AS reason, rows_failed
FROM dq_results
WHERE severity = 'Critical' AND rows_failed > 0
  AND run_id IN (SELECT arg_max(run_id, end_time) FROM pipeline_runs GROUP BY dag_id)
ORDER BY dag_id, file, rows_failed DESC;
