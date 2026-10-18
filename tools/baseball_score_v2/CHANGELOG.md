# Changelog

## [v72] - 2026-04-01

### Fixed
- **EC2 ビルドのアーキテクチャ不一致エラーを修正**: `DOCKER_BUILDKIT=0` を設定し buildx の arm64/amd64 不一致問題を回避

## [v71] - 2026-04-01

### Fixed
- **EC2 デプロイの `git pull` 認証エラーを修正**: `x-access-token:$GITHUB_TOKEN` を使った HTTPS URL に一時変更してから元に戻すフローに変更
- **docker compose のパスを修正**: `cd tools/baseball_score_v2/docker` で正しいディレクトリに移動してから `docker compose up` を実行するよう修正

## [v70] - 2026-04-01

### Fixed
- **`test_batting_view` の期待値を修正**: 選手名フィールドキー（`選手名` → `名前`）および出塁率 → OPS カラムに実装に合わせて修正

## [v69] - 2026-04-01

### Fixed
- **`test_batting_view` のテストデータに `ops` キーを追加**: CI テストでの `KeyError` を解消

## [v68] - 2026-04-01

### Fixed
- **`.gitignore` から `utils/` を削除**: `number_util.py` / `excel_util.py` 等が git 追跡対象から外れていたのを修正し、CI でのモジュール不在エラーを解消

## [v67] - 2026-04-01

### Fixed
- **`unittest discover` に `-t` オプションを追加**: トップレベルディレクトリを明示し `utils` モジュールの import パスを正しく解決

## [v66] - 2026-04-01

### Fixed
- **PYTHONPATH を絶対パスで指定**: CI 環境での `utils` モジュール解決エラーを修正（相対パス指定では動作しないケースに対応）

## [v65] - 2026-04-01

### Fixed
- **CI テスト用 PYTHONPATH と DB ダミー環境変数を追加**: テスト実行時の `ModuleNotFoundError` と `KeyError`（DB 環境変数未設定）を解消

## [v64] - 2026-04-01

### Fixed
- **CI/CD の `paths` フィルターを削除**: `paths` 指定により特定ファイル変更時しか CI が起動しない問題を解消し、`main` push で常に CI/CD が起動するよう変更

## [v63] - 2026-04-01

### Added
- **GitHub Actions CI/CD パイプライン追加**（STEP 2-7）: `.github/workflows/deploy.yml` を新規作成
  - **Job 1 (test)**: Python 3.11 + `unittest discover` でユニットテストを自動実行。DB ダミー環境変数を注入してモジュール解決を保証
  - **Job 2 (deploy)**: テスト成功時のみ SSH 経由で EC2 に自動デプロイ（`git pull origin main` → `DOCKER_BUILDKIT=0 docker compose up --build -d`）

## [v55] - 2026-03-30

### Added
- **公開対応 STEP 1 完了**: チーム内限定公開に必要なセキュリティ対応を実施
- **`webapp/backend/auth.py` を新規追加**: Google OAuth の `id_token` 検証 + `ALLOWED_EMAILS` による認可
- **`webapp/frontend/src/views/LoginView.vue` を新規追加**: Google Sign-In ボタン画面
- **`docker/.env.example` を新規追加**: 環境変数の雛形ファイル
- **`webapp/frontend/.env.production.example` を新規追加**: フロントエンド本番ビルド用環境変数の雛形
- **AWS 本番環境を構築**: EC2（t3.micro + Amazon Linux 2023）+ Nginx（HTTPS / Let's Encrypt）+ Docker Compose + S3 + CloudFront

### Changed
- **`config/config.py`**: `secrets.json` 読み込みを廃止 → `os.environ` から DB 設定をフェイルファストで取得
- **`webapp/backend/database.py`**: `sslmode` を `DB_SSLMODE` 環境変数から取得（デフォルト: `disable`）
- **`webapp/backend/main.py`**: `ALLOWED_ORIGINS` を環境変数（カンマ区切り）から取得。未設定時のデフォルトは `http://localhost:5173`
- **`webapp/backend/routers/*.py`（全6ファイル）**: `APIRouter(dependencies=[Depends(verify_token)])` で全エンドポイントを一括保護
- **`webapp/backend/requirements.txt`**: `google-auth` / `requests` を追加
- **`webapp/frontend/src/router/index.js`**: 全ルートに `requiresAuth` ガード追加。`/login` ルートを追加
- **`webapp/frontend/src/api/index.js`**: `Authorization: Bearer` ヘッダー自動付与 + 401 時の自動ログアウトを追加
- **`docker/docker-compose.yml`**: DB 認証情報・Google OAuth・CORS 設定を環境変数化。`secrets.json` マウントを削除
- **`dev_start.py`**: `docker/.env` を読み込みローカル実行用に注入する `load_dotenv()` を追加。`DB_HOST/PORT` 上書きを `run_all` subprocess 専用 env に限定
- **`.gitignore`**: `docker/.env` / `webapp/frontend/.env.local` / `webapp/frontend/.env.production` を追加

## [v49] - 2026-03-27

### Added
- **`dev_start.py` を新規追加**: 開発環境を1コマンドで一括起動するスクリプト
  - 実行順序: DB初期化（`docker compose down -v` → `up db --wait`）→ `run_all.py --skip-analytics` → `docker compose up backend --wait` → `npm run dev`（フォアグラウンド）
  - `--skip-init-db`: DB初期化をスキップし既存データを保持したまま起動
  - `--skip-run-all`: validate / generate / import_db をスキップ

## [v48] - 2026-03-26

### Added
- **`docker/docker-compose.yml` を新規追加**（STEP 6: Docker Compose による環境統一）
  - `db` サービス: PostgreSQL 15（ポート 5433、healthcheck 付き）
  - `backend` サービス: FastAPI バックエンド（Dockerfile ビルド、`docker compose up -d` で一括起動）
  - `config/secrets.json` と `logs/` をボリュームマウントで提供
- **`docker/init.sql` を新規追加**: `baseball_score_v2/docker/` にテーブル定義・制約を集約
- **`webapp/backend/Dockerfile` を新規追加**: Python 3.11 slim ベースの FastAPI バックエンドイメージ

### Changed
- **`config/config.py`**: `DB_HOST` / `DB_PORT` 環境変数で接続先をオーバーライド可能に変更。Docker Compose 環境では `DB_HOST=db` が自動設定される
- **`app_util.py` の `setup_docker_and_db()`**:
  - Docker ディレクトリを `./docker`（`baseball_score_v2/docker/`）に変更
  - `docker compose down -v`（データ削除）を廃止 → `docker compose up -d --wait`（起動済みなら何もしない）に変更

## [v47] - 2026-03-26

### Added
- **`utils/run_logger.py` を新規追加**: `logs/run_history.jsonl` に JSON Lines 形式でステップ実行履歴を記録するモジュール（STEP 3: 実行ログの可視化・履歴確認）
  - 記録項目: タイムスタンプ・`run_id`（ワークフロー単位の識別子）・ステップ名・ラベル・成否・対象年度・終了コード
- **`show_log.py` を新規追加**: CLI 実行履歴ビューア
  - `--date YYYY-MM-DD` で日付絞り込み
  - `--step validate|generate|import_db|analytics` でステップ絞り込み
  - `--last N` で最新 N 件のみ表示
  - `run_id` 単位でグループ表示し、ステータス（成功 / 失敗 / スキップ）を明示
- **`webapp/backend/routers/history.py` を新規追加**: `GET /api/history` エンドポイント
  - クエリパラメーター `date` / `step` / `last` によるフィルタリングに対応
- **`webapp/frontend/src/views/HistoryView.vue` を新規追加**: Web UI 実行履歴画面（`/history`）
  - 日付・ステップ・件数フィルター
  - `run_id` 単位のグループ表示でワークフロー実行ごとに整理

### Changed
- **`run_all.py`**: 各ステップ実行後に `run_logger` でログを記録。ワークフロー単位の `run_id`（`run_YYYYMMDD_HHMMSS`）を付与し、スキップしたステップも `SKIP` として記録
- **`webapp/backend/main.py`**: `history` ルーターを追加（`/api/history`）
- **`webapp/frontend/src/api/index.js`**: `historyApi.list()` を追加
- **`webapp/frontend/src/router/index.js`**: `/history` ルートを追加
- **`webapp/frontend/src/components/NavBar.vue`**: ナビバーに「実行履歴」タブを追加

## [v46] - 2026-03-25

### Added
- **`validate.py` を新規追加**: DB登録前にExcelデータの入力ミスを検出するバリデーションスクリプト（STEP 2: データ入力バリデーション強化）
  - 打撃内訳の整合性チェック（ERROR）: 長打計 > 安打 / 安打 > 打数 / 三振 > 打数 / 出塁 > 出塁機会
  - 日付フォーマット異常チェック（WARNING）
  - 対戦相手名の揺れチェック（WARNING）: 全角スペースを含むスペースを正規化して表記ゆれを検出
  - 投手名チェック（WARNING）: 相手攻撃シートの投手名がチーム単位シートに存在しない場合を検出
  - `--strict` オプションで WARNING も ERROR として扱い終了コード 1 を返す

### Changed
- **`run_all.py` にバリデーションステップを追加**: ワークフローが `validate → generate → import_db → analytics` の4ステップに変更
  - `--skip-validate` オプションで validate ステップをスキップ可能

## [v45] - 2026-03-25

### Added
- **`run_all.py` を新規追加**: 試合後のワークフロー（`generate` → `import_db` → `analytics`）を1コマンドで順次実行できる統合スクリプト
  - 各ステップの成否を `[OK]` / `[NG]` で表示
  - エラー発生時は途中停止し、`logs/app.log` を案内
  - `--year`（対象年度）・`--skip-analytics`（analytics スキップ）オプションに対応

## [v42] - 2026-03-25

### Changed
- **`import_db.py` を一括取込コマンドに統合**
  - `python import_db.py` 1コマンドで打撃成績・投手成績・チーム成績（試合一覧）をすべてDBに登録できるよう統合
  - `import_pitcher_db.py` を削除（`import_db.py` に統合）
  - `import_game_list.py` を削除（`import_db.py` に統合）
- **`generate.py` に投手成績の集計表示を統合**
  - `python generate.py` 1コマンドで打撃・投手両成績の集計表示と試合入力ファイル生成が完結
  - `generate_pitcher.py` を削除（`generate.py` に統合）
  - `team_records` の重複読み込みを解消

### Added
- **`docker/init.sql` を全テーブル対応に更新**
  - `pitcher_stats` テーブルを追加（`innings_pitched` / `outs` / `earned_runs` 含む）
  - `games` テーブルに `home_score` / `away_score` / `result` カラムを追加
  - `tmp/sql` の手動マイグレーション実行が不要に
- **`requirements.txt` を新規作成**（`pandas` / `openpyxl` / `psycopg2-binary` / `fastapi` / `uvicorn`）

## [v41] - 2026-03-25

### Added
- 各画面のチーム成績に第1試合/第2試合別の成績を追加表示

## [v40] - 2026-03-24

### Added
- CHANGELOG 新規作成

### Changed
- README / CLAUDE.md のダッシュボード説明を更新

## [v39] - 2026-03-24

### Changed
- **ダッシュボード画面を全面刷新** (`DashboardView.vue`)
  - 個人成績（OPSランキングテーブル・グラフ）を削除
  - チーム成績を「試合成績」「打撃成績」「投手成績」の3セクションで表示
  - 試合成績：勝・負・分を大きく表示し、試合数・得点・失点をサブ行に配置
  - 打撃成績：打率 / 本塁打 / OPS の3スコアカードで表示
  - 投手成績：防御率 / 奪三振 / WHIP の3スコアカードで表示
  - カードデザインを color-topped border + font-black スタイルに統一
  - Chart.js 依存を削除（グラフ不要のため）
  - API呼び出しを `teamRecord` / `teamBatting` / `teamPitching` の3本に整理

## [v38] - 2026-03-24

### Changed
- 打撃成績・投手成績・試合一覧画面のデフォルト表示を通算（年度未指定）に変更

## [v37] - 2026-03-23

### Changed
- 打撃成績・投手成績・試合一覧画面にチーム成績を上部表示

## [v36] - 2026-03-23

### Added
- 試合一覧・打撃成績・投手成績画面にチーム戦績サマリーを追加

## [v35] 以前

過去のリリース履歴は git log を参照してください。
