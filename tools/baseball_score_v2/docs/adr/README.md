# Architecture Decision Records（ADR）

設計上の判断と、その理由・結果を残す記録です。

| 番号 | タイトル | ステータス |
|------|----------|------------|
| [0001](0001-vue3-spa-frontend.md) | フロントエンドに Vue 3（SPA）を採用する | 採用済み |
| [0002](0002-plain-sql-without-orm.md) | ORM を使わず psycopg2 で SQL を直接書く | 採用済み |
| [0003](0003-google-oauth-allowed-emails.md) | Google OAuth と許可メールリストで認証する | 採用済み |
| [0004](0004-defer-alembic-migrations.md) | DB マイグレーション（Alembic）の導入を見送る | 提案（要承認） |
| [0005](0005-stop-aws-public-hosting.md) | AWS 上の常時公開を止め、ローカル利用と必要時の起動にする | 採用済み（遡及記録） |

## 書き方

- ファイル名は `NNNN-短い英語のタイトル.md`。番号は連番で、欠番を作らない。
- ステータスは「提案」「採用済み」「置き換え済み（ADR-NNNN）」のいずれか。
- 当時の記録が残っていない理由は、推測で書かず「記録なし」と明記する。
