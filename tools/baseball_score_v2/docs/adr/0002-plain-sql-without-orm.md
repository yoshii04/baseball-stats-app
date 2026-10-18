# ADR-0002: ORM を使わず psycopg2 で SQL を直接書く

- ステータス: 採用済み
- 関連: [ADR-0004](0004-defer-alembic-migrations.md)、`ANALYSIS_ID_GAPS.md`、`CLAUDE.md` の設計判断 7

## 背景

データの入口は Excel で、DB はそこから再生成できる集計・参照用のストアである。
登録処理は「重複を入れない」「再実行しても結果が変わらない」「ID が飛ばない」ことが求められる。

## 決定

DB アクセスには ORM（SQLAlchemy など）を使わず、`psycopg2` で SQL を直接書く。
CLI 側は `repository/db_repository.py`、Web API 側は `webapp/backend/database.py` の
`get_cursor()` に接続処理を集約する。

## 理由

記録として残っている理由は次の 1 点である。

- **ID の飛び番を避けるために、SQL の発行順を明示的に制御したい。**
  `INSERT ... ON CONFLICT DO NOTHING` は、衝突して挿入されなくても SERIAL のシーケンスが進むため、
  再実行のたびに ID が飛ぶ。そこで `get_or_create_*()` は SELECT → INSERT の順に実行している
  （`ANALYSIS_ID_GAPS.md`、`CLAUDE.md` の設計判断 7）。
  ORM の upsert 機能に任せると、この発行順を保証しにくい。

ORM を比較検討した記録は残っていない。

## 結果

- 良い点: 発行される SQL がコードに書いてあるとおりで、ID 連番の挙動を確認しやすい。依存が少ない。
- 悪い点: SQL 文字列が `repository/` と `webapp/backend/routers/` に分散する。
  パラメータの組み立てと列名の対応は人が保つ必要がある。
- スキーマの変更履歴は ORM のモデルから生成できない。扱いは [ADR-0004](0004-defer-alembic-migrations.md) に記す。
- 接続プールは無く、API のリクエストごとに接続する。負荷が増えた場合は SQLAlchemy への移行を検討する
  （`docs/plan/public_release_plan.md` STEP 3）。
