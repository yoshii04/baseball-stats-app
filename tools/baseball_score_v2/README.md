# Baseball Score v2

野球試合の打撃成績・投手成績・スコアを管理するPythonアプリケーション。
Excelから打撃・投手記録を読み込んでDBに登録する機能と、試合スコアをExcelへ書き込む機能、DB登録済みの成績を分析Excelとして出力する機能、ブラウザから成績を確認できるWebアプリ（FastAPI + Vue 3）を提供します。

---

## 機能一覧

| 機能 | 説明 |
|------|------|
| 打撃成績の読み込み・集計 | ExcelファイルからBattingRecordを読み込み、選手別・試合別に集計 |
| DB登録（打撃） | 打撃成績をPostgreSQLに登録 |
| **投手成績の読み込み・集計** | **「データ入力シート(相手攻撃)」からPitcherRecordを読み込み、投手別・試合別に集計** |
| **DB登録（投手）** | **投手成績をPostgreSQLに登録** |
| 試合入力ファイルの自動生成 | 集計結果から `data/game_inputs/{date}_{opponent}_{game_number}.txt` を生成 |
| スコアのExcel書き込み | 試合入力ファイル＋スコアCSVを読み込み、スコアシートに書き込む |
| **分析Excelの出力** | **DB登録済み打撃成績から選手別成績・打球方向・成績推移を集計しExcelに出力** |
| **成績確認 Web API** | **DB登録済み成績をブラウザから確認するための REST API（FastAPI）** |
| **成績確認 Web UI** | **Vue 3 製フロントエンド（ダッシュボード・選手一覧・投手成績・試合一覧・分析画面）** |
| **実行履歴の確認** | **`show_log.py`（CLI）および Web UI `/history` で過去のワークフロー実行履歴を確認** |

---

## ディレクトリ構造

```
baseball_score_v2/
├── run_all.py                       # ワークフロー統合コマンド（validate → generate → import_db → analytics を一括実行）
├── validate.py                      # データ入力バリデーション（DB登録前に入力ミスを検出）
├── show_log.py                      # 実行履歴 CLI ビューア（--date / --step / --last オプション対応）
├── generate.py                      # ステップ1: 打撃/投手成績の集計表示・試合入力ファイル生成エントリーポイント
├── import_db.py                     # ステップ2: 打撃・投手・チーム成績を一括DB登録エントリーポイント
├── write_score.py                   # ステップ3: スコア・打撃成績のExcel書き込みエントリーポイント
├── analytics.py                     # ステップ4: 分析Excelの出力エントリーポイント
├── app_util.py                      # 共通ヘルパー（logging設定・config読み込み・Docker起動）
├── config.json                      # 設定ファイル
│
├── config/
│   ├── config.py                    # DB設定の読み込み（環境変数から取得）
│   └── logging.conf                 # ロギング設定
│
├── model/
│   ├── batting_record.py            # 打撃記録データクラス
│   ├── pitcher_record.py            # 投手成績データクラス（1打席分）
│   └── game_record.py               # 試合スコアデータクラス
│
├── repository/
│   ├── batting_repository.py        # Excelから打撃記録を読み込む
│   ├── pitcher_repository.py        # Excelから投手成績を読み込む（相手攻撃シート）
│   ├── db_repository.py             # DB操作（選手・試合・打撃・投手データの挿入）
│   ├── score_excel_writer.py        # スコアをExcelに書き込む
│   ├── analytics_repository.py      # 分析用DBクエリ集（年度フィルタ付き）
│   └── analytics_excel_writer.py    # 分析結果をExcelに書き込む（グラフ付き）
│
├── service/
│   ├── batting_service.py           # 打撃集計ロジック・DB登録処理
│   ├── pitcher_service.py           # 投手集計ロジック・DB登録処理
│   └── analytics_service.py         # 累積成績・打球方向%の計算ロジック
│
├── view/
│   ├── batting_view.py              # 打撃成績コンソール出力
│   └── pitcher_view.py              # 投手成績コンソール出力
│
├── controller/
│   ├── batting_controller.py        # 打撃成績フロー制御・試合入力ファイル生成
│   ├── score_controller.py          # スコア書き込みフロー制御
│   └── analytics_controller.py      # 分析Excel出力フロー制御
│
├── utils/
│   ├── number_util.py               # Unicode丸数字と整数の相互変換
│   ├── excel_util.py                # Excelデータの安全な型変換
│   ├── game_input_parser.py         # 試合入力ファイル・スコアCSVのパーサー
│   └── run_logger.py                # 実行履歴を logs/run_history.jsonl に JSON Lines 形式で記録
│
├── data/
│   ├── game_inputs/                 # 試合入力ファイル（自動生成 + 手動補完）
│   └── scores/                      # スコアCSVファイル
│
├── logs/
│   ├── app.log                      # 実行ログ（自動生成）
│   └── run_history.jsonl            # ワークフロー実行履歴（JSON Lines 形式、自動生成）
│
├── tmp/sql/                         # 過去のDBマイグレーション履歴（内容は docker/init.sql に統合済み）
│
└── webapp/
    ├── backend/                     # 成績確認 Web API（FastAPI）
    │   ├── main.py                  # エントリーポイント・CORS設定
    │   ├── database.py              # DB接続ヘルパー
    │   ├── requirements.txt         # Web API用依存ライブラリ
    │   └── routers/
    │       ├── players.py           # 選手エンドポイント
    │       ├── games.py             # 試合エンドポイント
    │       ├── stats.py             # 成績統計エンドポイント
    │       ├── analytics.py         # 分析データエンドポイント
    │       ├── pitchers.py          # 投手成績エンドポイント
    │       └── history.py           # 実行履歴エンドポイント
    └── frontend/                    # 成績確認 Web UI（Vue 3 + Vite + Tailwind CSS）
        ├── index.html
        ├── vite.config.js           # Vite設定（/api → localhost:8000 プロキシ）
        ├── package.json
        ├── tailwind.config.js       # カスタム navy カラー定義
        ├── .env.production.example  # 本番ビルド用環境変数テンプレート
        └── src/
            ├── main.js              # Vueアプリ起動・ルーター登録
            ├── App.vue              # 共通レイアウト（NavBar + RouterView）
            ├── router/
            │   └── index.js         # 7画面のルーティング定義（requiresAuth ガード付き）
            ├── api/
            │   └── index.js         # axiosベースのAPIレイヤー（認証ヘッダー自動付与）
            ├── composables/
            │   └── useYear.js       # アプリ全体で共有する年度選択 composable
            ├── components/
            │   ├── NavBar.vue        # ナビゲーションバー（アクティブ状態対応）
            │   ├── YearSelector.vue  # 年度セレクタ
            │   ├── LoadingSpinner.vue
            │   └── ErrorAlert.vue
            └── views/
                ├── LoginView.vue       # Google Sign-In ログイン画面
                ├── DashboardView.vue   # チーム成績3セクション（試合成績・打撃成績・投手成績）
                ├── PlayersView.vue     # 選手一覧・全成績テーブル（行クリックで選手詳細へ）
                ├── PlayerDetailView.vue # 選手詳細（サマリー・推移グラフ・打球方向・試合別成績）
                ├── GamesView.vue       # 試合一覧 + 詳細モーダル
                ├── AnalyticsView.vue   # 打球方向・累積成績推移グラフ＋テーブル
                ├── PitchersView.vue    # 投手成績一覧 + 試合別成績モーダル
                └── HistoryView.vue     # 実行履歴一覧（日付・ステップ・件数フィルター）
```

---

## セットアップ

### 1. 環境変数ファイルを作成

```bash
cp docker/.env.example docker/.env
# docker/.env を編集して実際の値を入力
```

| 変数名 | 説明 |
|--------|------|
| `DB_HOST` | DB ホスト（Docker Compose 内では `db`、ローカル直接実行では `localhost`） |
| `DB_PORT` | DB ポート（Docker Compose 内では `5432`、ホストからは `5433`） |
| `DB_USER` | PostgreSQL ユーザー名 |
| `DB_PASSWORD` | PostgreSQL パスワード |
| `DB_NAME` | データベース名 |
| `TEAM_NAME` | チーム名（DB のチーム名、`config.json` に `our_team_name` が無い場合の自チーム名、API の説明文に使用） |
| `GOOGLE_CLIENT_ID` | Google OAuth クライアント ID |
| `ALLOWED_EMAILS` | ログインを許可するメールアドレス（カンマ区切り） |
| `ALLOWED_ORIGINS` | CORS 許可オリジン（例: `https://xxxx.cloudfront.net`、ローカルは `http://localhost:5173`） |

### 2. Docker Compose で DB + バックエンドを起動

```bash
cd docker
docker compose up -d
```

`db`（PostgreSQL）と `backend`（FastAPI）の2サービスが起動します。
初回起動時は `init.sql` が自動実行されてテーブルが作成されます。

| コマンド | 説明 |
|---------|------|
| `docker compose up -d` | DB + バックエンドを起動（初回 or 停止後の再開） |
| `docker compose down` | コンテナを停止（データは保持） |
| `docker compose down -v` | コンテナを停止してデータも完全削除（DB初期化） |
| `docker compose logs -f backend` | バックエンドのログを確認 |

### 3. 必要なライブラリをインストール

```bash
# CLI ツール（generate / import_db / write_score / analytics）
# バージョンは requirements.txt で固定している
pip install -r requirements.txt

# フロントエンド（webapp/frontend）
cd webapp/frontend
npm install
```

### 4. config.json を設定

```json
{
  "excel_file": "/path/to/batting_data.xlsx",
  "sheet_name": "データ入力シート(自チーム攻撃)",
  "pitcher_sheet_name": "データ入力シート(相手攻撃)",
  "score_excel_file": "/path/to/試合記録.xlsx",
  "score_sheet_name": "2026.3.7から2026.mm.dd",
  "team_data_sheet_name": "チーム単位のデータ",
  "our_team_name": "チーム名"
}
```

| キー | 説明 |
|------|------|
| `excel_file` | 打撃成績が記載されたExcelファイルのパス |
| `sheet_name` | 打撃成績のシート名 |
| `pitcher_sheet_name` | 投手成績（相手攻撃）のシート名（省略時: `"データ入力シート(相手攻撃)"` ） |
| `score_excel_file` | スコアを書き込む先のExcelファイルのパス |
| `score_sheet_name` | スコアを書き込む先のシート名 |
| `team_data_sheet_name` | チーム単位のデータ（投手のイニング数・自責点）のシート名（省略時: `"チーム単位のデータ"`） |
| `our_team_name` | 自チーム名（スコアの書き込み・スコアCSVの行特定に使用。省略時は環境変数 `TEAM_NAME`） |

---

## 使用方法

試合後の運用手順の詳細は [docs/operations.md](docs/operations.md) を参照してください。

```bash
python run_all.py   # validate → generate → import_db → analytics を一括実行
```

| コマンド | 内容 |
|---|---|
| `dev_start.py` | 開発環境（DB・バックエンド・フロントエンド）を一括起動 |
| `run_all.py` | 試合後ワークフローを一括実行 |
| `validate.py` | 入力ミスの検出（DB 登録前） |
| `generate.py` | 集計表示・試合入力ファイルの生成 |
| `import_db.py` | 打撃・投手・チーム成績の DB 登録 |
| `analytics.py` | 分析 Excel の出力 |
| `write_score.py` | スコアの Excel 書き込み |
| `show_log.py` | 実行履歴の確認 |

---

## ファイルフォーマット

### 試合入力ファイル（`data/game_inputs/*.txt`）

```
date: 2026-07-21
opponent: 相手A高校
game_number: 1
venue: サンプルグラウンド
pitcher: 投手A（6回）、投手B（3回）
doubles: 選手A、選手B、選手C
triples: 選手D
homeruns:
```

### スコアCSV（`data/scores/*.csv`）

```csv
チーム名,1,2,3,4,5,6,7,8,9,合計
自チーム名,2,0,4,1,1,0,2,1,2,13
相手A,3,0,2,0,0,2,0,0,1,8
```

### Excelスコアシートの書き込みレイアウト（6行1ブロック）

| 行 | A列 | C〜K列 | M列 | その他 |
|----|-----|--------|-----|--------|
| N | 日付（例: 2026年7月21日（火）） | | | |
| N+1 | | 1〜9（回数ヘッダー） | 計 | |
| N+2 | 自チーム名 | 各回得点 | 合計 | |
| N+3 | 相手チーム名 | 各回得点 | 合計 | |
| N+4 | | | | D列: P➡ピッチャー名、H列: 打撃成績 |
| N+5 | （空行） | | | |

---

## 処理フロー

### generate.py

```
generate.py
  ↓
TeamPitcherRepository.load_records()  # チーム単位シートから投手情報を読み込み（pitcher_map 構築）
  ↓
BattingController
  ├─→ load_records()            # Excelから打撃記録を読み込み
  ├─→ show_summary()            # 集計結果をコンソール表示
  └─→ export_game_inputs()      # 試合入力ファイルを自動生成
  ↓
PitcherRepository.load_records()      # 投手成績シートを読み込み
PitcherService.summarize()            # 投手別・試合別に集計
PitcherView.display_summary()         # コンソール表示
```

### import_db.py

```
import_db.py
  ↓
setup_docker_and_db()                 # Docker起動・PostgreSQL待機
  ↓
BattingController                     # 1. 打撃成績
  ├─→ load_records()
  ├─→ import_to_db()
  └─→ show_batting_stats_list()
  ↓
PitcherService                        # 2. 投手成績
  ├─→ summarize()
  └─→ import_to_db()
  ↓
_read_game_list()                     # 3. チーム成績（試合一覧）
_import_game_list()
```

### write_score.py

```
write_score.py
  ↓
ScoreController
  ├─→ parse_game_file()         # 試合入力ファイルを読み込み
  ├─→ parse_score_csv()         # スコアCSVを読み込み（--csv 省略時はスキップ）
  └─→ ScoreExcelWriter.write_game()
        ├─→ find_next_row()     # 書き込み開始行を自動検出
        ├─→ _find_style_refs()  # 既存ブロックからスタイルをコピー
        └─→ セルに値を書き込み・保存
```

### analytics.py

```
analytics.py --year 2026
  ↓
AnalyticsController
  ├─→ AnalyticsRepository.fetch_player_batting_stats()  # Sheet 1 用: 選手別集計
  ├─→ AnalyticsRepository.fetch_hit_direction_stats()   # Sheet 2 用: 打球方向集計
  │     └─→ AnalyticsService.calculate_direction_pct()  # 方向%を計算
  ├─→ AnalyticsRepository.fetch_player_game_log()       # Sheet 3 用: 試合別ログ
  │     └─→ AnalyticsService.calculate_cumulative_stats() # 累積打率・OPSを計算
  └─→ AnalyticsExcelWriter
        ├─→ write_player_batting_stats()  # Sheet 1 書き込み + グラフ
        ├─→ write_hit_direction()         # Sheet 2 書き込み + グラフ
        ├─→ write_player_progress()       # Sheet 3 書き込み + グラフ
        └─→ save() → analytics_2026.xlsx
```

---

## 5. 成績確認 Web API（webapp/backend）

DB登録済みの打撃成績をブラウザや外部アプリから確認するための REST API です。

### 起動方法

```bash
# DBコンテナ・バックエンドコンテナを起動（未起動の場合）
cd docker && docker compose up -d

# ローカルで API サーバーを直接起動する場合（開発時）
cd webapp/backend
uvicorn main:app --reload --port 8000
```

起動後、以下にアクセスできます。

| URL | 内容 |
|-----|------|
| `http://localhost:8000/docs` | Swagger UI（ブラウザでの動作確認） |
| `http://localhost:8000/redoc` | ReDoc（API リファレンス） |

### エンドポイント一覧

#### 選手 `/api/players`

| メソッド | パス | 説明 | 主なクエリパラメータ |
|---------|------|------|-------------------|
| GET | `/api/players` | 選手一覧（OPS順・シーズン成績付き） | `year` |
| GET | `/api/players/{player_id}` | 選手基本情報 | - |
| GET | `/api/players/{player_id}/stats` | 試合別成績 + 累積打率・OPS | `year` |

#### 試合 `/api/games`

| メソッド | パス | 説明 | 主なクエリパラメータ |
|---------|------|------|-------------------|
| GET | `/api/games` | 試合一覧 | `year`, `month` |
| GET | `/api/games/{game_id}` | 試合詳細（出場選手の打撃成績付き） | - |

#### 成績統計 `/api/stats`

| メソッド | パス | 説明 | 主なクエリパラメータ |
|---------|------|------|-------------------|
| GET | `/api/stats/season` | チームシーズン集計（試合数・打率・OPS等） | `year` |
| GET | `/api/stats/ranking` | OPSランキング | `year`, `limit` |

#### 分析 `/api/analytics`

| メソッド | パス | 説明 | 主なクエリパラメータ |
|---------|------|------|-------------------|
| GET | `/api/analytics/hit-direction` | 打球方向集計（選手別・方向%付き） | `year`, `player_id` |
| GET | `/api/analytics/batting-trend` | 累積打率・OPS推移 | `year`, `player_id` |

#### 投手 `/api/pitchers`

| メソッド | パス | 説明 | 主なクエリパラメータ |
|---------|------|------|-------------------|
| GET | `/api/pitchers` | 投手一覧（試合数・被安打・与四死球・奪三振・失点・WHIP） | `year` |
| GET | `/api/pitchers/{pitcher_id}/stats` | 投手別 試合ごとの成績一覧 | `year` |

#### 実行履歴 `/api/history`

| メソッド | パス | 説明 | 主なクエリパラメータ |
|---------|------|------|-------------------|
| GET | `/api/history` | ワークフロー実行履歴一覧 | `date`, `step`, `last` |

### 使用例

```bash
# 2025年 チームシーズン集計
curl http://localhost:8000/api/stats/season?year=2025

# 2025年 OPSランキング Top5
curl "http://localhost:8000/api/stats/ranking?year=2025&limit=5"

# 選手ID=8 の試合別成績（累積打率付き）
curl "http://localhost:8000/api/players/8/stats?year=2025"

# 2026年3月の試合一覧
curl "http://localhost:8000/api/games?year=2026&month=3"
```

---

## 6. 成績確認 Web UI（webapp/frontend）

Vue 3 製のフロントエンドアプリです。バックエンド API（`localhost:8000`）と連携し、打撃成績をブラウザで確認できます。

### 起動方法

```bash
# バックエンドを先に起動しておくこと（「5. 成績確認 Web API」参照）

cd webapp/frontend
npm run dev
```

起動後、`http://localhost:5173` にアクセスします。

画面に表示するチーム名は、ビルド時の環境変数 `VITE_TEAM_NAME`（`webapp/frontend/.env.local`、本番は `.env.production`）で指定します。未設定の場合は「自チーム」と表示されます。

> Vite の開発サーバーが `/api` へのリクエストを `localhost:8000` にプロキシするため、CORS設定不要で動作します。

### 画面構成

| 画面 | URL | 内容 |
|------|-----|------|
| ダッシュボード | `/` | チーム成績3セクション（試合成績：勝・負・分・得点・失点 / 打撃成績：打率・本塁打・OPS / 投手成績：防御率・奪三振・WHIP） |
| 選手一覧 | `/players` | 全選手の打撃成績テーブル（年度フィルタ・選手名テキスト絞り込み）、行クリックで選手詳細へ遷移 |
| 選手詳細 | `/players/:id` | シーズンサマリー・累積推移グラフ・打球方向グラフ・試合別成績テーブル |
| 投手成績 | `/pitchers` | 全投手の成績テーブル（試合数・被安打・与四死球・奪三振・失点・WHIP）、行クリックで試合別成績モーダル |
| 試合一覧 | `/games` | 試合一覧（月フィルター）＋試合行クリックで詳細モーダル（選手別打撃成績） |
| 分析 | `/analytics` | タブ切り替え：打球方向グラフ＋集計テーブル（右/右中/中/左中/左）／累積打率・OPS推移グラフ＋テーブル |
| 実行履歴 | `/history` | ワークフロー実行履歴一覧（日付・ステップ・件数フィルター、`run_id` 単位でグループ表示） |

### 技術スタック

| ライブラリ | バージョン | 用途 |
|-----------|-----------|------|
| Vue 3 | Composition API | UIフレームワーク |
| Vue Router 4 | - | クライアントサイドルーティング |
| Vite 6 | - | ビルドツール・開発サーバー |
| Tailwind CSS 3 | - | スタイリング（カスタム navy カラー定義） |
| axios | - | API通信（レスポンスインターセプタでエラーハンドリング） |

### ビルド（本番用）

```bash
cd webapp/frontend
npm run build
# dist/ に静的ファイルが生成される
```

---

## テスト実行

```bash
pip install -r requirements.txt -r webapp/backend/requirements.txt
python -m unittest discover -s tests -t . -p "test_*.py" -v
```

DB・Excel ファイルが無くても実行できます（DB はテスト内で差し替え、Excel は一時ファイルを使用）。
GitHub Actions でも `main` への push と PR で同じコマンドを自動実行します。

| テスト | 対象 |
|--------|------|
| `test_batting_service.py` | 打撃成績の集計 |
| `test_batting_view.py` | 打撃成績のコンソール表示 |
| `test_db_repository.py` | DB リポジトリの変換処理 |
| `test_validate.py` | 入力バリデーション（チェック関数・終了コード） |
| `test_pitcher_service.py` | 投手成績の集計・DB 登録 |
| `test_analytics_service.py` | 累積打率・OPS、打球方向の割合 |
| `test_score_excel_writer.py` | スコアの Excel 書き込み |
| `test_app_util.py` | 設定値（自チーム名・シート名）の取得 |

---

## トラブルシューティング

### Excelファイルが見つからない
- `config.json` の `excel_file` / `score_excel_file` パスを確認

### DBに接続できない
- `docker/.env` の接続情報（`DB_HOST` / `DB_PASSWORD` 等）を確認
- DockerコンテナのPostgreSQLが起動しているか確認（`docker compose ps`）
- ローカルで CLI ツール直接実行の場合: `DB_HOST=localhost`, `DB_PORT=5433` を環境変数にセット（またはdev_start.py経由で起動）

### スコアのExcelシートが見つからない
- `config.json` の `score_sheet_name` とExcel上のシート名が一致しているか確認

### 重複データがDBに登録される
- `docker/` ディレクトリで `docker compose down -v && docker compose up -d` でコンテナを完全初期化してから `python import_db.py` を再実行

### フロントエンドでAPIエラーが表示される
- バックエンド（`uvicorn main:app --reload --port 8000`）が起動しているか確認
- `http://localhost:8000/docs` にアクセスしてAPIが動作しているか確認

### フロントエンドの依存ライブラリが見つからない
- `webapp/frontend` ディレクトリで `npm install` を実行

---

## 7. AWSへのデータ登録

EC2 を起動して Excel のデータを AWS 上の DB へ取り込む手順は [docs/aws-deploy.md](docs/aws-deploy.md) を参照してください。

> 費用の関係で AWS は停止中です（2026-10-12 時点）。GitHub Actions の deploy は手動実行（`workflow_dispatch`）です。

---

## ライセンス

プライベートプロジェクト
