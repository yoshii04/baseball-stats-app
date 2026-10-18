# CLAUDE.md

このファイルは Claude Code (claude.ai/code) がこのリポジトリで作業する際の指針を提供します。

## プロジェクト概要

**Baseball Score v2** は以下の機能を提供する Python MVC アプリケーションです：
- Excelファイルから打撃記録を読み込み、集計・コンソール表示
- Excelファイル（相手攻撃シート）から投手成績を読み込み、集計・コンソール表示
- データをデータベース（PostgreSQL）に保存（打撃・投手両対応）
- 試合入力ファイルの自動生成、スコアのExcel書き込み
- DB登録済み成績から分析Excelを出力
- DB登録済み成績をブラウザで確認できる Web アプリ（FastAPI + Vue 3）

関心の分離が明確な層構造と包括的なテストを備えています。

## アーキテクチャ

**MVC パターンに明示的な層構造**を採用：

```
generate.py / import_db.py (エントリーポイント)
  ↓
BattingController (ワークフロー統合)
  ├─→ BattingRepository (Excel I/O)
  ├─→ BattingService (ビジネスロジック & DB 統合)
  │   └─→ DBRepository (データベース I/O)
  └─→ BattingView (コンソール出力)
```

### 各層の責務

- **Model** (`model/batting_record.py`): 打撃記録を表すデータクラス（検証機能付き）
- **Repository** (`repository/`):
  - `batting_repository.py`: Excelファイルを読み込み、BattingRecord オブジェクトに変換
  - `db_repository.py`: データベース操作（選手挿入、試合データ挿入、接続管理）
- **Service** (`service/batting_service.py`):
  - ヒット数を多段階辞書に集計（日付 → 対戦相手 → 回数 → 打種 → 選手 → 本数）
  - DB インポート処理を統合（先に選手、その次に試合データ）
  - 遅延 DB 接続 + コンテキストマネージャで接続を確実にクローズ
- **View** (`view/batting_view.py`): コンソール出力フォーマット
- **Controller** (`controller/batting_controller.py`): ワークフロー統合
- **Utils** (`utils/`):
  - `number_util.py`: Unicode 丸数字（①②③）と整数の相互変換
  - `excel_util.py`: Excel データの安全な型変換（None、NaN 対応）

### Web アプリ構成（`webapp/`）

```
webapp/
├── backend/                        # FastAPI REST API
│   ├── main.py                     # エントリーポイント・CORS設定
│   ├── database.py                 # get_cursor() コンテキストマネージャ（psycopg2）
│   └── routers/
│       ├── players.py              # GET /api/players, /api/players/{id}, /api/players/{id}/stats
│       ├── games.py                # GET /api/games, /api/games/{id}
│       ├── stats.py                # GET /api/stats/season, /api/stats/ranking
│       ├── analytics.py            # GET /api/analytics/hit-direction, /api/analytics/batting-trend
│       ├── pitchers.py             # GET /api/pitchers, /api/pitchers/{id}/stats
│       ├── history.py              # GET /api/history（実行履歴、date/step/last クエリパラメーター対応）
│       └── (各ルーター)            # APIRouter(dependencies=[Depends(verify_token)]) で全エンドポイントを保護
├── auth.py                         # Google OAuth id_token 検証 + ALLOWED_EMAILS 認可
└── frontend/                       # Vue 3 + Vite + Tailwind CSS
    ├── .env.production.example     # 本番ビルド用環境変数テンプレート
    └── src/
        ├── api/index.js            # axios ベースの API レイヤー（Authorization ヘッダー自動付与・401 時ログアウト）
        ├── config.js               # 表示用設定（VITE_TEAM_NAME からチーム名を取得）
        ├── composables/useYear.js  # 全画面共有の年度選択状態
        ├── components/             # NavBar / YearSelector / LoadingSpinner / ErrorAlert
        └── views/
            ├── LoginView.vue        # Google Sign-In ログイン画面
            ├── DashboardView.vue    # チーム成績3セクション（試合成績・打撃成績・投手成績のスコアカード）
            ├── PlayersView.vue      # 選手一覧テーブル + 選手名テキスト絞り込み（行クリックで詳細へ）
            ├── PlayerDetailView.vue # 選手詳細（サマリー・累積推移グラフ・打球方向グラフ・試合別成績）
            ├── GamesView.vue        # 試合一覧（月フィルター）+ 詳細モーダル
            ├── AnalyticsView.vue    # タブ切り替え：打球方向グラフ / 累積打率・OPS推移グラフ
            ├── PitchersView.vue     # 投手成績一覧テーブル + 試合別成績モーダル
            └── HistoryView.vue      # 実行履歴一覧（日付・ステップ・件数フィルター、run_id グループ表示）
```

**設計上の注意**:
- `database.py` は既存の `config/config.py` を `sys.path` 操作で再利用（DB設定の二重管理を避ける）
- Vite の dev proxy（`/api → localhost:8000`）を使用するため、フロント側の `baseURL` は空（開発時）
- 年度選択状態は `composables/useYear.js` でモジュールスコープの `ref` として管理（全画面共有）
- `analytics.py` の `hit-direction` エンドポイントは `player_id` クエリパラメーターで選手単体フィルタリング可能
- 全 API エンドポイントは `verify_token` で Google OAuth 認証必須。`ALLOWED_EMAILS` 未設定時はメール認可チェックをスキップ

## よく使うコマンド

### 開発環境 一括起動（推奨）
```bash
python dev_start.py                          # DB初期化 → run_all → backend → frontend を一括起動
python dev_start.py --skip-init-db           # DB初期化をスキップ（既存データ保持）
python dev_start.py --skip-run-all           # run_all をスキップ
python dev_start.py --skip-init-db --skip-run-all  # backend + frontend のみ起動
```
実行順序: DB初期化（`down -v` → `up db`）→ `run_all.py --skip-analytics` → `docker compose up backend` → `npm run dev`（フォアグラウンド）

### CLI ツール実行
```bash
python run_all.py [--year 2026] [--skip-validate] [--skip-analytics]  # validate → generate → import_db → analytics を一括実行（推奨）
python validate.py              # データ入力バリデーション（DB登録前に入力ミスを検出）
python generate.py              # Excel読み込み・打撃/投手成績の集計表示・試合入力ファイル生成
python import_db.py             # Docker起動 + 打撃・投手・チーム成績を一括DB登録
python analytics.py --year 2026 # 分析Excelの出力
python write_score.py --game data/game_inputs/xxx.txt  # スコアをExcelに書き込む
python show_log.py [--date 2026-03-26] [--step import_db] [--last 20]  # 実行履歴をCLIで確認
```
`config.json`（Excel パス/シート名）と `docker/.env`（DB 認証情報・OAuth 設定）が必要。
`dev_start.py` は起動時に `docker/.env` を読み込んで環境変数を自動セットする。

### Docker Compose 起動（DB + バックエンド）
```bash
cd docker
docker compose up -d          # DB + バックエンドを一括起動
docker compose down           # 停止（データ保持）
docker compose down -v        # 停止 + データ完全削除（DB初期化）
docker compose logs -f backend  # バックエンドログ確認
```

### デモ（合成データ・認証なし）
```bash
(cd demo && docker compose up --build)   # → http://localhost:8090（架空のチーム・選手・試合）
python demo/generate_demo_data.py        # seed.sql と logs/run_history.jsonl を再生成
```
バックエンドの `DEMO_MODE=true` は認証を省略する。`ENV=production` では起動しない。詳細は `demo/README.md`。

### Web アプリ起動
```bash
# バックエンド（FastAPI）をローカルで直接起動する場合（開発時）
cd webapp/backend
uvicorn main:app --reload --port 8000
# → http://localhost:8000/docs で Swagger UI を確認可能

# フロントエンド（Vue 3）— バックエンド起動後に実行
cd webapp/frontend
npm run dev
# → http://localhost:5173 でブラウザ確認
```

### テスト実行
```bash
pip install -r requirements.txt -r webapp/backend/requirements.txt
python -m unittest discover -s tests -t . -p "test_*.py" -v
```
標準的な `unittest` フレームワークを使用（DB・実データの Excel は不要）。主要なテスト：
- `tests/test_batting_service.py`: 打撃成績の集計ロジック
- `tests/test_db_repository.py`: 数値変換関数
- `tests/test_validate.py`: 入力バリデーション（各チェック関数・`run_validation` の終了コード）
- `tests/test_pitcher_service.py`: 投手成績の集計・DB 登録（DB リポジトリは差し替え）
- `tests/test_analytics_service.py`: 累積打率・OPS、打球方向の割合
- `tests/test_score_excel_writer.py`: スコアの Excel 書き込み（一時ファイルを使用）
- `tests/test_app_util.py`: 自チーム名・シート名の取得
- `tests/test_demo_data.py`: デモ用の合成データ生成（決定性、`seed.sql` との一致、成績の整合性）
- `tests/test_auth_demo_mode.py`: 認証のデモモード（本番で拒否、既定は無効）

FastAPI のルーター、Vue 側（フロントエンド）、`generate.py` / `import_db.py` の結線にはテストが無い。

## 設定

### config.json
プロジェクトルートにあります。以下を定義：
```json
{
  "excel_file": "/path/to/data.xlsx",
  "sheet_name": "シート1",
  "pitcher_sheet_name": "データ入力シート(相手攻撃)",
  "team_data_sheet_name": "チーム単位のデータ",
  "game_list_sheet_name": "2025年度　試合の一覧",
  "our_team_name": "チーム名"
}
```
`pitcher_sheet_name` / `team_data_sheet_name` / `game_list_sheet_name` は省略可能（各デフォルト値を使用）。
`our_team_name` は自チーム名で、省略時は環境変数 `TEAM_NAME` を使う（どちらも無い場合 `write_score.py` はエラー終了）。
チーム名・シート名をコードに直接書かないこと。

### docker/.env （Git に追加しないこと）
データベース認証情報・Google OAuth 設定・CORS 設定：
```env
DB_HOST=db
DB_PORT=5432
DB_USER=postgres
DB_PASSWORD=changeme
DB_NAME=baseball
DB_SSLMODE=disable
TEAM_NAME=チーム名
GOOGLE_CLIENT_ID=xxx.apps.googleusercontent.com
ALLOWED_EMAILS=member@example.com
ALLOWED_ORIGINS=https://xxxx.cloudfront.net
```
テンプレートは `docker/.env.example` を参照。

DB 接続情報は環境変数（`docker/.env`）で渡す。

### ログ設定
`config/logging.conf` で設定。ログは `logs/app.log` に出力（初回実行時にディレクトリ自動作成）。

`run_all.py` を実行すると `logs/run_history.jsonl` にワークフロー実行履歴が JSON Lines 形式で追記される。`show_log.py` または Web UI `/history` で確認可能。

## 重要な設計判断

### 1. **遅延 DB 接続**
`BattingService` は `import_to_db()` が呼ばれるまで `DBRepository` を生成しません。これにより、DB 接続なしに集計のみを行うワークフローが可能になります。

### 2. **コンテキストマネージャ パターン**
`BattingService` と `DBRepository` は `__enter__/__exit__` を実装し、リソースを確実にクリーンアップします。`main.py` は `finally` ブロックで service を close し、エラー時も接続をクローズします。

### 3. **データフロー：1度読み込み、複数回使用**
早期バージョンとは異なり、`main.py` は Excel を 1 度だけ読み込み、同じ `records` リストを以下に渡します：
- `controller.show_summary()`
- `controller.import_to_db()`

これにより冗長なファイル I/O を避けます。

### 4. **重複レコード防止**
データベース スキーマは `batting_stats` テーブルの `(player_id, game_id)` に一意制約を含みます。INSERT 文は `ON CONFLICT DO NOTHING`（PostgreSQL）またはそれに相当する処理を使用し、アプリ再実行時のデータ破損を防止します。

### 5. **回数フォーマット**
- Excel 入力: 数字（1, 2, 3, ...）
- メモリ内表現: Unicode 丸数字（①②③...）
- データベース保存: 整数（1, 2, 3, ...）
- 変換は `utils/number_util.py` で処理: `to_marunum()`（整数→丸）、`marunum_to_int()`（丸/文字→整数）

### 6. **安全な Excel データ変換**
Excel セルは None、NaN、datetime オブジェクト、文字列を含む可能性があります。`utils/excel_util.py` は以下を提供：
- `safe_str(value)`: 全型に対応、None/NaN は "" を返す
- `safe_int(value)`: 全型に対応、None/空文字/NaN は 0 を返す

### 7. **SELECT-first パターンで ID の飛び番を防止**
`get_or_create_*()`ヘルパーメソッドは `ON CONFLICT` の代わりに **SELECT → INSERT** の順で実行します。
これにより PostgreSQL の SERIAL SEQUENCE が不必要にインクリメントされるのを避け、ID を連番に近く保つ。
- `get_or_create_team(cur, team_name=None)`: チーム名から team_id を取得または作成
- `get_or_create_game(cur, game_date, home_team_id, away_team_id)`: ゲームを取得または作成
- `get_or_create_player(cur, player_name, team_id)`: 選手を取得または作成

`batting_stats` テーブルの INSERT のみ `ON CONFLICT DO NOTHING` を使用（実データ重複防止用、再挿入頻度が低い）。

## テストパターン

- **ユニット テスト**: 純粋関数（集計、数値変換）に焦点
- **データ層のモック化なし**: テストは実際のデータクラス オブジェクトを使用；DB テストはモックではなくヘルパー関数を使用
- **setUp/tearDown**: テストは `service.close()` を呼び出して DB 接続をクリーンアップ
- **テスト ユーティリティ**: インラインのデータクラス構築で可読性向上

テスト パターン例：
```python
def test_something(self):
    records = [BattingRecord(...), BattingRecord(...)]
    result = self.service.summarize_hits(records)
    self.assertIn(expected_key, result)
```

## よくある問題と解決策

### Excel 読み込み失敗
`config.json` のパスを確認し、列が「日」「回数」「対戦相手」「選手名」「2塁打」「3塁打」「本塁打」（B〜H 列、1 行目スキップ）であることを確認。

### DB 接続拒否
環境変数 `DB_HOST` / `DB_PORT` / `DB_USER` / `DB_PASSWORD` / `DB_NAME` が正しいことを確認（`docker/.env`、`config/config.py` を参照）。
ローカルからホスト経由で接続する場合、ポートは `5433`。

### DB に重複データが登録される
`docker/` ディレクトリで `docker compose down -v && docker compose up -d` でコンテナを完全初期化してから `python import_db.py` を再実行してください。一意制約は `docker/init.sql` に含まれており、コンテナ起動時に自動で有効化されます。

### 回数でクラッシュ（③以降で ValueError）
Phase 1 で修正済み。再発時は `utils/number_util.py` の `marunum_to_int()` が①-⑨ の全丸数字を処理していることを確認。

## ファイル整理の注意

- **config.json** (Git に含まない): Excel パスとローカルシート名を保持
- **docker/.env** (Git に含まない): DB 認証情報・OAuth 設定—**絶対に commit しないこと**（テンプレート: `docker/.env.example`）
- **webapp/frontend/.env.local** (Git に含まない): フロントエンドのローカル開発用環境変数（表示するチーム名は `VITE_TEAM_NAME`）
- **webapp/frontend/.env.production** (Git に含まない): フロントエンドの本番ビルド用環境変数（テンプレート: `.env.production.example`）
- **tmp/sql/**: 過去のマイグレーション履歴（内容はすべて `docker/init.sql` に統合済み。新規環境では不要）
- **logs/**: 実行時に自動作成；.gitignore に追加して構わない
- **tests/**: スタンドアロン ユニット テスト；アプリ状態なしで実行可能

## これまでの主要な変更

詳細は `CHANGELOG.md` を参照。主要な改善：
1. 回数番号変換を修正（①-⑨ 対応）
2. DB 接続クリーンアップ + コンテキストマネージャ追加
3. ユーティリティ関数を抽出（`number_util.py`、`excel_util.py`）
4. BattingRecord に dataclass 検証を追加
5. 遅延 DB 接続を実装
6. 一意制約で重複レコード防止
7. テスト スイート追加（初期は 12 テスト。現在は 90 テスト、`validate` / 投手集計 / 分析 / Excel 書込を含む）
8. FastAPI バックエンド（全9エンドポイント）を実装
9. Vue 3 フロントエンド（4画面・共通コンポーネント）を実装
10. フロントエンド全4画面のUIと機能を実装（Phase 3）
11. グラフ・ビジュアライゼーション追加（累積推移折れ線・打球方向横棒・ダッシュボードトレンド）（Phase 4）
12. 選手詳細ページ追加（`/players/:id`）と `hit-direction` への `player_id` フィルター追加（Phase 5）
13. 投手成績機能追加（Phase 1〜4）: PitcherRecord・PitcherRepository・PitcherService・pitcher_stats テーブル・`/api/pitchers` エンドポイント・PitchersView（`/pitchers`）
14. 各画面のチーム成績に第1試合/第2試合別の成績を追加表示
15. `import_db.py` を統合：打撃・投手・チーム成績（試合一覧）を1コマンドで一括DB登録。`docker/init.sql` に全テーブル・制約を集約し手動マイグレーション不要に
16. `generate.py` に投手成績集計表示を統合：`generate_pitcher.py` / `import_game_list.py` を削除しエントリーポイントを `generate.py` / `import_db.py` の2本に集約
17. `run_all.py` を追加：試合後ワークフロー（generate → import_db → analytics）を1コマンドで一括実行。各ステップの成否を `[OK]` / `[NG]` で表示し、エラー時は途中停止
18. `validate.py` を追加：DB登録前にExcelデータの入力ミスを検出するバリデーション（打撃内訳整合性・日付フォーマット・対戦相手名揺れ・投手名チェック）。`run_all.py` の先頭ステップとして統合
19. `utils/run_logger.py` を追加・`run_all.py` を修正：`logs/run_history.jsonl` にJSON Lines形式でステップ実行履歴を記録（`run_id` でワークフロー単位にグループ化）
20. `show_log.py` を追加：CLI実行履歴ビューア（`--date` / `--step` / `--last` オプション対応）
21. `GET /api/history` エンドポイント・Web UI `/history` 画面を追加：実行履歴を日付・ステップ・件数でフィルタリング可能
22. Docker Compose 整備（STEP 6）: `baseball_score_v2/docker/docker-compose.yml` に PostgreSQL + FastAPI バックエンドを統合。`webapp/backend/Dockerfile` を追加。`config/config.py` に `DB_HOST`/`DB_PORT` 環境変数オーバーライドを追加。`app_util.py` の `setup_docker_and_db()` から `down -v` を廃止し `docker compose up -d --wait` に変更
23. `dev_start.py` を追加：開発環境を1コマンドで一括起動（DB初期化 → run_all → backend → frontend）。`--skip-init-db` / `--skip-run-all` オプションで柔軟なスキップが可能
24. 公開対応 STEP 1 完了（AWS は費用のため 2026-10-12 時点で停止中。デプロイは手動実行）：Google OAuth 認証・シークレット環境変数化・CORS 本番対応・AWS 本番環境（EC2 + Nginx + S3 + CloudFront）を整備。`auth.py` 追加・`config/config.py` 環境変数化・全ルーターに認証 Depends 追加・`LoginView.vue` 追加・`docker/.env` によるシークレット管理に移行
25. GitHub Actions を追加：`.github/workflows/deploy.yml`。`main` への push と PR で unittest を自動実行する。EC2 へのデプロイ（SSH で `git pull` → `DOCKER_BUILDKIT=0 docker compose up --build -d`）は、AWS 停止中のため Actions タブからの手動実行（`workflow_dispatch`）のみ。当初は push のたびに自動デプロイしていたが、EC2 停止後に失敗が続いたため手動実行へ変更した（2026-10-12）

## 開発ワークフロー

1. **ブランチ作成**: `main` から機能名のブランチを切る（下記「ブランチ名」）
2. **機能追加/修正**: 関連する層を更新（例：ロジック→service、I/O→repository）
3. **テスト作成**: `tests/test_*.py` に標準的な `unittest` で作成
4. **ローカル テスト実行**: `python -m unittest discover -s tests -t . -p "test_*.py" -v`
5. **エンドツーエンド実行**: テスト データを Excel に用意して `python run_all.py --skip-analytics`
6. **ログ確認**: `logs/app.log` で問題をレビュー
7. **PR 作成**: `main` 宛てに PR を出す（テストが自動実行される）

### ブランチ名

`<種別>/<内容を表す英語の短い名前>`（ケバブケース）。種別はコミットメッセージと同じ。

| 種別 | 用途 | 例 |
|------|------|----|
| `feat/` | 機能追加 | `feat/pitcher-stats` |
| `fix/` | 不具合修正 | `fix/duplicate-game-import` |
| `refactor/` | 動作を変えない整理 | `refactor/team-name-config` |
| `docs/` | ドキュメント | `docs/adr` |
| `test/` | テスト追加 | `test/validate` |
| `chore/` | CI・依存関係・設定 | `chore/pin-requirements` |

- 連番のブランチ名（`feature-func-score_vNN`）は使わない。PR のタイトルと履歴から内容が分からなくなるため。
- 1 ブランチ 1 目的にする。

### 設計判断の記録（ADR）

設計上の判断は `docs/adr/` に ADR として残す（一覧は `docs/adr/README.md`）。
このファイルの「重要な設計判断」はコード上の実装メモで、方針の選択とその理由は ADR に書く。

## 将来の改善予定

- SQLAlchemy への移行で DB 抽象化を強化（現状の方針は `docs/adr/0002-plain-sql-without-orm.md`）
- CLI フレームワーク（Click/Typer）で UX 向上
- Alembic によるデータベース マイグレーション管理（導入の判断は `docs/adr/0004-defer-alembic-migrations.md`）
- フロントエンドのテスト追加（Vitest / Vue Test Utils）
- 試合後レポートの自動生成（STEP 7）
