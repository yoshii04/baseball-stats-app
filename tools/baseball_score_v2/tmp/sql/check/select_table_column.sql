SELECT
    cols.table_schema AS スキーマ名,
    cols.table_name AS テーブル物理名,
    obj_description(c.oid, 'pg_class') AS テーブル論理名,
    cols.column_name AS 項目物理名,
    col_description(c.oid, cols.ordinal_position) AS 項目論理名,
    cols.data_type AS 項目型,
    CASE 
        WHEN cols.character_maximum_length IS NOT NULL THEN cols.character_maximum_length::text
        WHEN cols.datetime_precision IS NOT NULL THEN '精度:' || cols.datetime_precision
        WHEN cols.numeric_precision IS NOT NULL THEN cols.numeric_precision || ',' || cols.numeric_scale
        ELSE '無制限' 
    END AS サイズ_精度
FROM
    information_schema.columns cols
JOIN
    pg_class c ON c.relname = cols.table_name
JOIN
    pg_namespace n ON n.oid = c.relnamespace AND n.nspname = cols.table_schema
WHERE
    cols.table_schema NOT IN ('pg_catalog', 'information_schema')
ORDER BY
    cols.table_schema,
    cols.table_name,
    cols.ordinal_position;
