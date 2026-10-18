# 個人開発 3 本の紹介

業務外の個人開発 3 本です。どれも、Excel や家計簿ソフトで手作業していた記録・集計を、Web アプリに移したものです。**3 本で、同じ進め方（ADR → 仕様書 → テスト → 実装 → レビュー）を、題材と技術を変えて繰り返しています。**

| | [baseball-stats-app](../../README.md)（このリポジトリ） | householdAccountBook | performanceRecords |
|---|---|---|---|
| 題材 | 高校野球チームの成績管理 | 家計簿の集計 | 日別の行動記録・ポイント管理 |
| **主に示すこと** | データの取り込みから画面までの流れ、**CI/CD と運用の判断（AWS を構築し、費用で止めた）** | **仕様駆動の開発プロセス**（ADR・仕様書・テスト方針・レビューの履歴） | **テスト先行（Red / Green）の実践**、作った機能を**取り込まない判断** |
| 構成 | Python CLI + FastAPI + Vue 3 + PostgreSQL | FastAPI + SQLAlchemy 2.0 + Alembic + Jinja2 + PostgreSQL 16 | FastAPI + SQLAlchemy 2.0 + Alembic + 素の JavaScript + PostgreSQL 16 |
| 認証 | Google ログイン + 許可メール | なし（ローカル稼働。ADR-0006 に判断を記録） | Google ログイン + 許可メール 1 件 |
| テストと CI | 102 件の単体テスト。push・PR で自動実行 | pytest（PostgreSQL 16）、`pip-audit` | pytest（SQLite / PostgreSQL）、alembic、vitest、ruff、`pip-audit`（週 1 回の定期実行あり） |
| 設計判断の記録 | ADR 4 本（遡及 3 + 提案 1） | ADR 6 本、機能仕様書 19 本、テスト方針 | ADR 5 本（却下 1 を含む）、機能仕様書 13 本 |
| 入口 | [README](../../README.md) | 非公開（必要なときに招待） | 非公開（必要なときに招待） |

## どこから見るか

| 知りたいこと | 見る場所 |
|---|---|
| 何を作ったか、どう動くか | 各リポジトリの README |
| 判断の仕方、AI との進め方 | [設計判断と AI の使い方](design-decisions-and-ai.md) |
| 設計判断の記録 | このリポジトリの [ADR](../../tools/baseball_score_v2/docs/adr/README.md) |
| 仕様書の書き方 | householdAccountBook の機能仕様書（非公開。必要なときに招待） |
| 運用の判断（コスト・停止・再開） | このリポジトリの [AWS 手順](../../tools/baseball_score_v2/docs/aws-deploy.md)、[deploy.yml](../../.github/workflows/deploy.yml) |

## 補足

- 3 本とも、**個人が自分の環境で使う**ことを前提にしています。常時稼働の外部公開は行っていません。
- このリポジトリの画面のスクリーンショット（`docs/images/`）は、すべて合成データです。実データは含みません。
- householdAccountBook と performanceRecords は、現時点では非公開です。
