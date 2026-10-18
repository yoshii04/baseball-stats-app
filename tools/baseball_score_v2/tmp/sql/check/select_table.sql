SELECT
    relname AS 物理名,
    obj_description(c.oid, 'pg_class') AS 論理名
FROM
    pg_class c
JOIN
    pg_namespace n ON n.oid = c.relnamespace
WHERE
    n.nspname = 'public'  -- スキーマ名がpublicのもの
    AND c.relkind = 'r'   -- 通常のテーブル(Ordinary Table)のみ
ORDER BY
    relname;
