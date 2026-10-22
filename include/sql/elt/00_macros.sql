-- Current version of each source file: the content most recently loaded into raw.
-- Raw keeps every version; staging reads only the current one. Increment files loaded on earlier
-- days stay current, so their corrections survive a run that has no new increment file.
CREATE OR REPLACE MACRO current_hashes(file_pattern) AS TABLE
    SELECT arg_max(file_hash, loaded_at) FROM raw_load_log
    WHERE source_file LIKE file_pattern
    GROUP BY source_file;
