# Baseball Score v2 - システム設計書

> **目的**: 学習用として、本プロジェクトの全ファイルの機能概要を1つのドキュメントにまとめた設計書です。

---

## 目次

1. [システム概要](#1-システム概要)
2. [ディレクトリ構成](#2-ディレクトリ構成)
3. [アーキテクチャ](#3-アーキテクチャ)
4. [各ファイルの機能概要](#4-各ファイルの機能概要)
   - 4.1 [エントリーポイント（CLIスクリプト）](#41-エントリーポイントcliスクリプト)
   - 4.2 [Model層](#42-model層)
   - 4.3 [Repository層](#43-repository層)
   - 4.4 [Service層](#44-service層)
   - 4.5 [Controller層](#45-controller層)
   - 4.6 [View層](#46-view層)
   - 4.7 [Utils層](#47-utils層)
   - 4.8 [Config層](#48-config層)
   - 4.9 [Tests](#49-tests)
   - 4.10 [Docker](#410-docker)
   - 4.11 [Webアプリ - バックエンド（FastAPI）](#411-webアプリ---バックエンドfastapi)
   - 4.12 [Webアプリ - フロントエンド（Vue 3）](#412-webアプリ---フロントエンドvue-3)
5. [データベーススキーマ](#5-データベーススキーマ)
6. [データフロー](#6-データフロー)
7. [主要な設計パターン](#7-主要な設計パターン)
8. [技術スタック](#8-技術スタック)
9. [実行コマンド集](#9-実行コマンド集)

---

## 1. システム概要

**Baseball Score v2** は高校野球チームの試合成績を管理するシステムです。

### 主な機能

| 機能 | 説明 |
|------|------|
| 打撃成績管理 | Excelから打撃データを読み込み・集計・DB登録 |
| 投手成績管理 | Excelから投手データを読み込み・集計・DB登録 |
| スコア記録 | 回別得点をExcelに書き込み |
| 分析出力 | 年度別の累積成績・打球方向分析をExcelに出力 |
| Web UI | ブラウザから成績をグラフ付きで閲覧（Google認証付き） |

### 操作の流れ（CLIワークフロー）

```
試合後
  → Excelに打撃・投手データを記録
  → python run_all.py  （バリデーション → 集計 → DB登録 → 分析）
  → ブラウザで成績を確認
```

---

## 2. ディレクトリ構成

```
baseball_score_v2/
│
├── README.md                        # プロジェクト概要・セットアップ手順
├── CLAUDE.md                        # Claude Code向け開発ガイド
├── requirements.txt                 # CLI・DB用Pythonライブラリ一覧
├── config.json                      # Excelファイルパス・シート名などの設定
│
│  ─── CLIエントリーポイント ───
├── run_all.py                       # ワークフロー統合（4ステップを一括実行）
├── validate.py                      # 入力バリデーション
├── generate.py                      # 成績集計・コンソール表示・試合入力ファイル生成
├── import_db.py                     # DB一括登録
├── write_score.py                   # スコアExcel書き込み
├── analytics.py                     # 分析Excel出力
├── show_log.py                      # 実行履歴CLIビューア
├── migrate.py                       # DBマイグレーション
├── app_util.py                      # 共通ヘルパー（logging・config・Docker起動）
├── dev_start.py                     # 開発環境一括起動スクリプト
│
│  ─── 層別ディレクトリ ───
├── model/                           # データモデル定義（dataclass）
├── repository/                      # データI/O（Excel読み込み・DB操作）
├── service/                         # ビジネスロジック（集計・計算）
├── controller/                      # ワークフロー統合（各層の呼び出し順制御）
├── view/                            # コンソール出力
├── utils/                           # 汎用ユーティリティ
├── config/                          # 環境設定・ロギング設定
├── tests/                           # ユニットテスト
│
│  ─── データ・ログ ───
├── data/
│   ├── game_inputs/                 # 試合入力ファイル（自動生成 + 手動補完）
│   └── scores/                      # スコアCSVファイル
├── logs/
│   ├── app.log                      # 実行ログ
│   └── run_history.jsonl            # ワークフロー実行履歴（JSON Lines形式）
│
│  ─── インフラ・Web ───
├── docker/                          # Docker Compose設定・DB初期化SQL
├── docs/                            # 設計ドキュメント（このファイル含む）
└── webapp/
    ├── backend/                     # FastAPI REST APIサーバー
    └── frontend/                    # Vue 3 + Vite + Tailwind CSS ブラウザUI
```

---

## 3. アーキテクチャ

本プロジェクトは **レイヤードアーキテクチャ（層分離設計）** を採用しています。

```
┌──────────────────────────────────────────────────────────┐
│                 CLIエントリーポイント                      │
│    run_all.py / generate.py / import_db.py / ...        │
└───────────────────────┬──────────────────────────────────┘
                        ↓
┌──────────────────────────────────────────────────────────┐
│                    Controller層                          │
│    batting_controller / score_controller / ...          │
│  （各層を呼び出す順序を制御するワークフロー層）             │
└───────────────────────┬──────────────────────────────────┘
                        ↓
┌──────────────────────────────────────────────────────────┐
│                    Service層                             │
│    batting_service / pitcher_service / analytics_service │
│  （集計・計算・DB登録のビジネスロジック）                   │
└────────────┬──────────────────────────────┬─────────────┘
             ↓                              ↓
┌────────────────────────┐   ┌─────────────────────────────┐
│     Repository層       │   │        View層               │
│  batting_repository    │   │  batting_view / pitcher_view │
│  pitcher_repository    │   │  （コンソール出力）           │
│  db_repository         │   └─────────────────────────────┘
│  analytics_repository  │
│  excel_writer類        │
└────────────┬───────────┘
             ↓
┌──────────────────────────────────────────────────────────┐
│                    Model層                               │
│  BattingRecord / PitcherRecord / GameRecord / ...       │
│  （データ構造の定義・型検証）                              │
└──────────────────────────────────────────────────────────┘
             ↕（データ授受）
┌──────────────────────────────────────────────────────────┐
│              外部データソース                             │
│    Excelファイル          PostgreSQL DB                  │
└──────────────────────────────────────────────────────────┘
```

---

## 4. 各ファイルの機能概要

### 4.1 エントリーポイント（CLIスクリプト）

これらはターミナルから直接実行するスクリプトです。各スクリプトは内部で Controller・Service 層を呼び出します。

---

#### `run_all.py` — ワークフロー統合スクリプト

**役割**: 4つのステップを順番に実行し、試合後の一括処理を行う。

**処理フロー**:
```
1. validate （入力バリデーション）
2. generate （集計・試合入力ファイル生成）
3. import_db （DB登録）
4. analytics （分析Excel出力）
```

**オプション**:
- `--year 2026` — 年度指定（analytics で使用）
- `--skip-validate` / `--skip-analytics` — ステップをスキップ

**学習ポイント**: サブプロセス呼び出し（`subprocess.run()`）でPythonスクリプトを順次実行するパターン。

---

#### `validate.py` — 入力バリデーション

**役割**: DB登録前にExcelデータの整合性チェックを行い、エラーがあればメッセージを出力して処理を止める。

**チェック内容**:
- 打撃内訳の合計が一致するか（単打＋二塁打＋三塁打＋本塁打 ≤ 安打数）
- 日付フォーマットが正しいか
- 対戦相手名の表記揺れがないか
- 投手名が正しく記録されているか

**学習ポイント**: 「入力値の検証をビジネスロジック実行前に行う」原則を示す実例。

---

#### `generate.py` — 成績集計・試合入力ファイル生成

**役割**: Excelから打撃・投手データを読み込み、コンソールに集計結果を表示する。また後続のDB登録に必要な試合入力ファイルを `data/game_inputs/` に生成する。

**実行結果**:
- コンソール: 打撃成績・投手成績の一覧表示
- ファイル出力: `data/game_inputs/{date}_{opponent}_{game_number}.txt`

---

#### `import_db.py` — DB一括登録

**役割**: 試合入力ファイル・スコアCSV・Excelデータを読み込み、PostgreSQLの各テーブルに登録する。Docker未起動の場合は自動起動する。

**登録テーブル**: `teams`, `players`, `games`, `batting_stats`, `pitcher_stats`

---

#### `write_score.py` — スコアExcel書き込み

**役割**: 試合入力ファイルとスコアCSVを組み合わせ、スコア・打撃成績をExcelの指定シートに書き込む。

**引数**:
- `--game` — 試合入力ファイルパス
- `--csv` — スコアCSVファイルパス

---

#### `analytics.py` — 分析Excel出力

**役割**: DBから年度別の成績データを取得し、分析Excelを3シート構成で生成する。

**出力シート**:
1. 選手別打撃成績（打率・OPS・長打別集計）
2. 打球方向分析（5方向の割合）
3. 成績推移グラフ（試合順の累積推移）

**引数**: `--year 2026`

---

#### `show_log.py` — 実行履歴CLIビューア

**役割**: `logs/run_history.jsonl` に記録された実行履歴を条件でフィルタリングして表示する。

**オプション**:
- `--date 2026-03-27` — 日付で絞り込み
- `--step import_db` — ステップ名で絞り込み
- `--last 20` — 直近N件を表示

---

#### `app_util.py` — 共通ヘルパー

**役割**: 複数のCLIスクリプトから共通利用されるユーティリティ関数を提供する。

**提供機能**:
- `setup_logging()` — `config/logging.conf` を読み込んでロガーを設定
- `load_config()` — `config.json` を読み込んで辞書として返す
- `ensure_docker_running()` — DockerコンテナのDB起動確認・未起動時の自動起動

---

#### `dev_start.py` — 開発環境一括起動

**役割**: 開発環境のセットアップを自動化する。DB初期化 → run_all → バックエンド起動 → フロントエンド起動を順番に実行する。

**オプション**:
- `--skip-init-db` — DB初期化をスキップ（既にデータがある場合）
- `--skip-run-all` — run_all をスキップ（データ登録不要な場合）

---

#### `migrate.py` — DBマイグレーション

**役割**: DBスキーマの変更（列追加・型変更など）を管理する。`docker/init.sql` の変更をDBに適用する。

---

### 4.2 Model層

`model/` ディレクトリ。**データ構造の定義** を担当します。Python の `@dataclass` デコレーターを使い、フィールド定義と型検証を一元管理します。

**学習ポイント**: `@dataclass` は `__init__()` を自動生成するPythonの機能。`__post_init__()` に追加の検証ロジックを書ける。

---

#### `model/batting_record.py` — 打撃記録データクラス

**クラス**: `BattingRecord`

**フィールド**:

| フィールド名 | 型 | 説明 |
|------------|-----|------|
| `game_date` | `date` | 試合日 |
| `opponent` | `str` | 対戦相手チーム名 |
| `player_name` | `str` | 選手名 |
| `game_number` | `int` | ゲーム番号（同日複数試合対応） |
| `at_bat_count` | `int` | 打数 |
| `hit_count` | `int` | 安打数 |
| `double_hit` | `int` | 2塁打数 |
| `triple` | `int` | 3塁打数 |
| `homerun` | `int` | 本塁打数 |
| `walk_count` | `int` | 四死球数 |
| `strike_out` | `int` | 三振数 |
| `stolen_base` | `int` | 盗塁数 |
| `right_9` | `int` | 打球方向: ライト |
| `right_center` | `int` | 打球方向: ライト中間 |
| `center` | `int` | 打球方向: センター |
| `left_center` | `int` | 打球方向: レフト中間 |
| `left_7` | `int` | 打球方向: レフト |
| `on_base` | `int` | 出塁数 |
| `on_base_opportunity` | `int` | 出塁機会数 |

**`__post_init__()`**: 型変換（文字列→整数）・必須項目チェックを実行。

---

#### `model/pitcher_record.py` — 投手成績データクラス（1打席分）

**クラス**: `PitcherRecord`

**フィールド**: 日付・対戦相手・投手名・ゲーム番号・投球数・被本塁打・与四死球・奪三振・被安打・失点・打球方向5方向

**補足**: 投手成績は打席単位で記録され、Service層で試合単位に集計される。

---

#### `model/game_record.py` — 試合スコアデータクラス

**クラス**: `GameRecord`

**フィールド**: 日付・対戦相手・ゲーム番号・会場・投手・回別得点リスト・合計得点・長打リスト・サヨナラフラグ

---

#### `model/team_pitcher_record.py` — チーム投手データクラス

**クラス**: `TeamPitcherRecord`

**フィールド**: 日付・対戦相手・ゲーム番号・投手名・投球回（整数部）・アウト数（0/1/2）

**補足**: Excelの「チーム投手」シートから読み込み、投手の投球回を管理する。

---

### 4.3 Repository層

`repository/` ディレクトリ。**データの読み書き（I/O）** を担当します。ExcelファイルとPostgreSQLの操作を集約し、上位層はデータソースを意識しなくて済む構造にします。

---

#### `repository/batting_repository.py` — 打撃記録Excelリーダー

**クラス**: `BattingRepository`

**主要メソッド**:
- `load_records(excel_file, sheet_name) → list[BattingRecord]`

**処理内容**:
1. `pandas.read_excel()` でExcelを読み込む
2. `_flatten_columns()` で2段ヘッダー（日付行＋項目行）を1つの列名に統合
3. ゲーム番号列を自動検出
4. 各行を `safe_str()` / `safe_int()` で安全に型変換
5. `BattingRecord` インスタンスのリストを返す

**学習ポイント**: 2段ヘッダーの処理と `pandas` のデータ操作パターン。

---

#### `repository/pitcher_repository.py` — 投手成績Excelリーダー

**クラス**: `PitcherRepository`

**主要メソッド**:
- `load_records(excel_file, sheet_name) → list[PitcherRecord]`

**処理内容**: 「相手攻撃」シートから投手別の1打席分データを読み込み、`PitcherRecord` リストを返す。

---

#### `repository/team_pitcher_repository.py` — チーム投手Excelリーダー

**クラス**: `TeamPitcherRepository`

**主要メソッド**:
- `load_records(excel_file, sheet_name) → list[TeamPitcherRecord]`

**処理内容**: 「チーム投手」シートから投手の投球回・アウト数を読み込む。

---

#### `repository/db_repository.py` — PostgreSQL操作

**クラス**: `DBRepository`

**主要メソッド**:

| メソッド | 説明 |
|---------|------|
| `get_or_create_team(team_name)` | チームが存在しなければ INSERT、存在すれば team_id を返す |
| `get_or_create_player(player_name, team_id)` | 選手が存在しなければ INSERT、存在すれば player_id を返す |
| `get_or_create_game(game_date, ...)` | 試合が存在しなければ INSERT、存在すれば game_id を返す |
| `insert_players(records)` | 選手を一括登録（重複スキップ） |
| `insert_records(records)` | 打撃成績を一括登録（`UNIQUE` 制約でスキップ） |
| `insert_pitcher_records(records)` | 投手成績を一括登録 |

**設計の特徴**:
- **SELECT-first パターン**: INSERT前に SELECT で存在確認し、IDの飛び番を防止
- **コンテキストマネージャ**: `with DBRepository() as repo:` の形で使用し、`__exit__()` でDB接続を確実にクローズ
- **トランザクション管理**: `conn.commit()` / `conn.rollback()` でデータ整合性を保証

**学習ポイント**: `psycopg2` によるPostgreSQL操作、コンテキストマネージャプロトコル（`__enter__`/`__exit__`）。

---

#### `repository/score_excel_writer.py` — スコアExcel書き込み

**クラス**: `ScoreExcelWriter`

**主要メソッド**:
- `write_game_to_excel(excel_path, sheet_name, row_data)` — 指定シートの指定行にスコアデータを書き込む

**使用ライブラリ**: `openpyxl`（Excelの読み書き専用ライブラリ）

---

#### `repository/analytics_repository.py` — 分析用DBクエリ

**クラス**: `AnalyticsRepository`

**主要メソッド**:

| メソッド | 説明 |
|---------|------|
| `fetch_player_batting_stats(year)` | 年度別・選手別の打撃集計データを取得 |
| `fetch_hit_direction_stats(year)` | 年度別・選手別の打球方向5分類データを取得 |
| `fetch_batting_trend(year, player_id)` | 試合順の累積成績データを取得 |

**特徴**: `year` が `None` の場合は全年度（通算）を取得。SQL の `WHERE` 句で年度フィルタリング。

---

#### `repository/analytics_excel_writer.py` — 分析結果Excel書き込み

**クラス**: `AnalyticsExcelWriter`

**主要メソッド**:

| メソッド | 説明 |
|---------|------|
| `write_player_batting_stats(df)` | 選手別打撃成績シートを作成（OPS順ソート） |
| `write_hit_direction(df)` | 打球方向分析シートを作成（割合計算・グラフ埋め込み） |
| `write_batting_trend(df)` | 成績推移シートを作成（折れ線グラフ） |

**使用ライブラリ**: `openpyxl` + `openpyxl.chart`（グラフ作成）

---

### 4.4 Service層

`service/` ディレクトリ。**ビジネスロジック（集計・計算・DB登録の統合）** を担当します。Repository層を呼び出してデータを取得・加工し、必要に応じてDBに登録します。

---

#### `service/batting_service.py` — 打撃集計・DB登録

**クラス**: `BattingService`

**主要メソッド**:

| メソッド | 説明 |
|---------|------|
| `summarize_hits(records)` | 打撃データを多段階辞書に集計 |
| `import_to_db(records)` | DB登録処理（選手登録→試合登録→成績登録） |
| `get_batting_stats_list()` | DBから選手別打撃成績を取得 |

**`summarize_hits()` の集計構造**:
```python
{
  "2026-03-27": {         # 日付
    "相手チーム": {         # 対戦相手
      1: {               # ゲーム番号
        "本塁打": {        # 打種
          "田中": 1,      # 選手: 本数
          "鈴木": 2,
        }
      }
    }
  }
}
```

**設計の特徴**:
- **遅延初期化**: `_db_repo = None` で初期化。`import_to_db()` が呼ばれた時点で初めてDB接続
- **コンテキストマネージャ**: `with BattingService() as svc:` で必ずDB接続をクローズ

**学習ポイント**: `collections.defaultdict` による多段階辞書の集計パターン。

---

#### `service/pitcher_service.py` — 投手集計・DB登録

**クラス**: `PitcherService`

**主要メソッド**:

| メソッド | 説明 |
|---------|------|
| `summarize(records, team_records)` | 打席単位の記録を試合・投手単位に集計し、チーム情報（投球回・自責点）をマージ |
| `import_to_db(records)` | `pitcher_stats` テーブルに登録 |

---

#### `service/analytics_service.py` — 分析計算

**クラス**: `AnalyticsService`

**主要メソッド**:

| メソッド | 説明 |
|---------|------|
| `calculate_direction_pct(direction_raw)` | 打球方向5方向の打球数を割合（%）に変換 |
| `calculate_batting_trend(stats_list)` | 試合順に並べた累積打率・OPS推移データを生成 |

**学習ポイント**: 純粋な計算ロジックのみを持つ層。DB・ファイルI/Oを一切行わないため、テストが書きやすい。

---

### 4.5 Controller層

`controller/` ディレクトリ。**各層の呼び出し順を制御するワークフロー層** です。CLIスクリプトからの呼び出しを受け取り、Repository → Service → View を適切な順番で呼び出します。

---

#### `controller/batting_controller.py` — 打撃ワークフロー制御

**クラス**: `BattingController`

**主要メソッド**:

| メソッド | 説明 |
|---------|------|
| `load_records()` | `BattingRepository.load_records()` を呼び出し、結果をキャッシュ（1度だけ読み込む） |
| `show_summary()` | `BattingService.summarize_hits()` → `BattingView.display_summary()` の順で呼び出す |
| `import_to_db()` | `BattingService.import_to_db()` を呼び出す |
| `export_game_inputs()` | 集計結果から試合入力ファイル（.txt）を `data/game_inputs/` に生成 |

**試合入力ファイルの命名規則**: `{YYYY-MM-DD}_{対戦相手}_{ゲーム番号}.txt`

---

#### `controller/score_controller.py` — スコア書き込みワークフロー制御

**クラス**: `ScoreController`

**主要メソッド**:
- `write_game(game_file, csv_file)` — 試合入力ファイル＋スコアCSVを読み込み、`ScoreExcelWriter` でExcelに書き込む

---

#### `controller/analytics_controller.py` — 分析ワークフロー制御

**クラス**: `AnalyticsController`

**主要メソッド**:
- `generate_analytics(year, output_path)` — `AnalyticsRepository` → `AnalyticsService` → `AnalyticsExcelWriter` を順番に呼び出し、分析Excelを生成

---

### 4.6 View層

`view/` ディレクトリ。**コンソール出力** を担当します。Serviceから受け取ったデータを、人が読みやすい形式でターミナルに表示します。

---

#### `view/batting_view.py` — 打撃成績コンソール出力

**クラス**: `BattingView`

**主要メソッド**:

| メソッド | 説明 |
|---------|------|
| `display_summary(summary)` | 日付/対戦相手/ゲーム番号ごとに打種別の選手リストを表示。複数ヒット時は丸数字（①②③）付きで表示 |
| `display_batting_stats(stats)` | 選手別打撃成績テーブル（OPS順）をコンソールに表示 |

**学習ポイント**: データ（Service）と表示（View）を分離することで、出力フォーマットを変えてもビジネスロジックに影響しない設計。

---

#### `view/pitcher_view.py` — 投手成績コンソール出力

**クラス**: `PitcherView`

**主要メソッド**:
- `display_summary(summary)` — 試合別・投手別の成績（投球回・失点・被安打など）をコンソールに表示

---

### 4.7 Utils層

`utils/` ディレクトリ。**汎用ユーティリティ関数** を提供します。特定のビジネスロジックに依存しない、再利用可能な関数を集めます。

---

#### `utils/number_util.py` — 数値変換ユーティリティ

**役割**: Unicode丸数字（①②③...⑨）と整数の相互変換。Excelの回番号や本数表記に対応するために使用。

**主要関数**:

| 関数 | 引数 | 戻り値 | 例 |
|-----|------|--------|-----|
| `to_marunum(value)` | `int \| str` | `str` | `1 → "①"`, `9 → "⑨"` |
| `marunum_to_int(inning_str)` | `str` | `int` | `"①" → 1`, `"①回" → 1`, `"10回" → 10` |

**学習ポイント**: Unicode文字コードを使った文字変換（`chr(0x2460 + n - 1)` で①を生成）。

---

#### `utils/excel_util.py` — Excel型安全変換ユーティリティ

**役割**: Excelから読み込んだ値を安全に型変換する関数群。Excelのセルは `None`・`NaN`・`datetime`・数値・文字列など様々な型になるため、一元的に処理する。

**主要関数**:

| 関数 | 説明 | None/NaN時の動作 |
|-----|------|----------------|
| `safe_str(value)` | 安全な文字列変換 | `""` を返す |
| `safe_int(value, default=0)` | 安全な整数変換 | `default` を返す |
| `safe_float(value, default=0.0)` | 安全な浮動小数点変換 | `default` を返す |
| `safe_game_number(value)` | ゲーム番号ラベルを整数変換 | `1` を返す |

**`safe_game_number()` の変換例**: `"1試合目" → 1`, `"2試合目" → 2`, `1 → 1`

**学習ポイント**: `pandas` の `NaN`（`float('nan')`）は `None` と別物なので `pd.isna()` でまとめてチェックする必要がある。

---

#### `utils/game_input_parser.py` — 試合入力ファイルパーサー

**役割**: `generate.py` が生成する試合入力ファイル（.txt）とスコアCSVを解析し、構造化データとして返す。

**主要関数**:

| 関数 | 入力 | 出力 |
|-----|------|------|
| `parse_game_file(file_path)` | 試合入力ファイルパス | 試合情報の辞書 |
| `parse_score_csv(csv_path)` | スコアCSVファイルパス | 回別得点のリスト |

**試合入力ファイルの形式** (例):
```
date: 2026-03-27
opponent: 相手高校
game_number: 1
venue: 甲子園
pitcher: 田中
```

---

#### `utils/run_logger.py` — 実行履歴ロガー

**役割**: `run_all.py` の各ステップ実行結果を `logs/run_history.jsonl` に記録する。

**主要関数**:
- `log_run(run_id, step, label, status, year, returncode)` — 1行のJSON（JSON Lines形式）として履歴ファイルに追記

**記録内容** (1行あたり):
```json
{"run_id": "20260327_143022", "step": "import_db", "label": "DB登録", "status": "success", "year": 2026, "returncode": 0, "timestamp": "2026-03-27T14:31:05"}
```

**学習ポイント**: JSON Lines（`.jsonl`）形式は、1行＝1JSONオブジェクトで追記しやすい。大きなログファイルでも行単位で読み込めるため、メモリ効率が良い。

---

### 4.8 Config層

`config/` ディレクトリ。**設定管理** を担当します。

---

#### `config/config.py` — DB接続設定

**役割**: 環境変数からDB接続情報を読み込み、接続用の辞書を返す。

**読み込む環境変数**:
```
DB_HOST, DB_PORT, DB_USER, DB_PASSWORD, DB_NAME, DB_SSLMODE
```

**学習ポイント**: 機密情報（パスワード等）をコードに直接書かず、環境変数から読み込む「12-Factor App」の原則。

---

#### `config/config.json` — 静的設定

**役割**: Excelファイルのパス・シート名・チーム名など、環境変数には馴染まない設定値を管理。`.gitignore` に追加して Git管理外にする（パスは環境ごとに異なるため）。

**設定例**:
```json
{
  "team_name": "サンプル高校",
  "excel_path": "/path/to/成績.xlsx",
  "batting_sheet": "打撃内訳",
  "pitcher_sheet": "相手攻撃"
}
```

---

#### `config/logging.conf` — ロギング設定

**役割**: Pythonの `logging.config.fileConfig()` で読み込まれる設定ファイル。ログのフォーマット・出力先（コンソール/ファイル）・ログレベルを定義。

**出力先**: `logs/app.log`

---

### 4.9 Tests

`tests/` ディレクトリ。**ユニットテスト** を格納します。Python標準の `unittest` フレームワークを使用。

---

#### `tests/test_batting_service.py` — 打撃集計ロジックのテスト

**テスト対象**: `BattingService.summarize_hits()`

**テスト内容**: 複数の `BattingRecord` を渡したとき、集計辞書が期待通りの構造・値になるかを検証。

---

#### `tests/test_batting_view.py` — ビュー層のテスト

**テスト対象**: `BattingView.display_summary()`

**テスト内容**: 集計結果を渡したとき、コンソール出力が期待通りの形式になるかを検証（`io.StringIO` でキャプチャ）。

---

#### `tests/test_db_repository.py` — 数値変換関数のテスト

**テスト対象**: `safe_int()` / `safe_str()` などのユーティリティ関数

**テスト内容**: None・NaN・文字列・数値など様々な入力パターンに対して正しく変換されるかを検証。

---

### 4.10 Docker

`docker/` ディレクトリ。**インフラ定義** を管理します。

---

#### `docker/docker-compose.yml` — コンテナ定義

**役割**: PostgreSQL（DB）とFastAPI（バックエンド）のコンテナ構成を定義する。

**サービス**:
- `db` — PostgreSQL 15。ポート5432。`init.sql` で初期化
- `backend` — FastAPI + uvicorn。ポート8000。`webapp/backend/` をマウント

---

#### `docker/init.sql` — DB初期化スクリプト

**役割**: DBコンテナ起動時に実行され、全テーブルと制約を作成する。

**作成テーブル**: `teams`, `players`, `games`, `batting_stats`, `pitcher_stats`

**学習ポイント**: `UNIQUE` 制約でデータの重複を防ぎ、`FOREIGN KEY` でテーブル間の参照整合性を保証する。

---

#### `docker/.env.example` — 環境変数テンプレート

**役割**: 実際の `.env` ファイルを作成する際の雛形。Git に含め、機密値は `changeme` などのプレースホルダーにしておく。

---

### 4.11 Webアプリ - バックエンド（FastAPI）

`webapp/backend/` ディレクトリ。**REST APIサーバー** を実装します。Dockerコンテナで動作し、ブラウザからのリクエストに応答します。

---

#### `webapp/backend/main.py` — FastAPIエントリーポイント

**役割**: FastAPIアプリの初期設定・ルーター登録・セキュリティ設定を行うメインファイル。

**設定内容**:
- CORS設定（`ALLOWED_ORIGINS` 環境変数から読み込み）
- セキュリティヘッダー（CSP・X-Frame-Options・HSTS・X-Content-Type-Options）
- Rate Limiting（`slowapi` で 60リクエスト/分）
- 各ルーターの登録（`players`, `games`, `stats`, `analytics`, `pitchers`, `history`）

**学習ポイント**: `FastAPI()` のインスタンスに `app.include_router()` でルーターを追加する構成。ミドルウェアでセキュリティヘッダーを一括設定。

---

#### `webapp/backend/database.py` — DB接続ヘルパー

**役割**: FastAPIのエンドポイントからDBを操作するための接続ヘルパーを提供する。

**提供機能**:
- `get_cursor()` — コンテキストマネージャ。`with get_cursor() as cur:` の形で使用し、処理後に自動でコミット/ロールバック・接続クローズ

---

#### `webapp/backend/auth.py` — Google OAuth認証

**役割**: リクエストの `Authorization` ヘッダーにある Google の id_token を検証し、許可されたユーザーかを確認する。

**処理フロー**:
1. `Authorization: Bearer {id_token}` ヘッダーを取得
2. `google-auth` ライブラリで id_token を検証（署名・有効期限・audience確認）
3. `ALLOWED_EMAILS` 環境変数が設定されている場合、メールアドレスで絞り込み
4. 検証失敗時は `HTTP 401` を返す

**FastAPIとの連携**: `Depends(verify_token)` で全エンドポイントに認証を適用。

---

#### `webapp/backend/routers/players.py` — 選手APIルーター

**エンドポイント**:

| エンドポイント | 説明 |
|------------|------|
| `GET /api/players` | 選手一覧（年度別シーズン成績付き） |
| `GET /api/players/{id}` | 選手詳細（基本情報） |
| `GET /api/players/{id}/stats` | 選手の試合別成績一覧 |

**SQLの特徴**: `batting_stats` を `GROUP BY player_id` で集計し、打率（`hit_count / at_bat_count`）・OPS（出塁率＋長打率）を計算。

---

#### `webapp/backend/routers/games.py` — 試合APIルーター

**エンドポイント**:

| エンドポイント | 説明 |
|------------|------|
| `GET /api/games` | 試合一覧（年度・月でフィルタリング可） |
| `GET /api/games/{id}` | 試合詳細（スコア・出場選手） |

---

#### `webapp/backend/routers/stats.py` — 統計APIルーター

**エンドポイント**:

| エンドポイント | 説明 |
|------------|------|
| `GET /api/stats/season` | シーズン統計（試合数・勝敗・チーム打率） |
| `GET /api/stats/ranking` | 個人ランキング（OPS順） |
| `GET /api/stats/team-batting` | チーム打撃成績 |
| `GET /api/stats/team-pitching` | チーム投手成績 |
| `GET /api/stats/team-record` | チーム試合成績（勝敗表） |

---

#### `webapp/backend/routers/analytics.py` — 分析APIルーター

**エンドポイント**:

| エンドポイント | 説明 |
|------------|------|
| `GET /api/analytics/hit-direction` | 打球方向分析（5方向の割合） |
| `GET /api/analytics/batting-trend` | 累積推移グラフデータ（試合順） |

**SQLの特徴**: `right_9`, `right_center`, `center`, `left_center`, `left_7` 列を `SUM()` して集計。

---

#### `webapp/backend/routers/pitchers.py` — 投手APIルーター

**エンドポイント**:

| エンドポイント | 説明 |
|------------|------|
| `GET /api/pitchers` | 投手一覧（年度別成績付き） |
| `GET /api/pitchers/{id}/stats` | 投手の試合別成績一覧 |

---

#### `webapp/backend/routers/history.py` — 実行履歴APIルーター

**エンドポイント**: `GET /api/history`

**動作**: `logs/run_history.jsonl` を読み込み、`date`・`step`・`last` クエリパラメーターでフィルタリングして返す。

**学習ポイント**: DBを使わずファイルを直接APIで返すパターン。

---

### 4.12 Webアプリ - フロントエンド（Vue 3）

`webapp/frontend/src/` ディレクトリ。**ブラウザUI** を実装します。Vue 3 の Composition API（`<script setup>`）を使い、Chart.js でグラフを表示します。

---

#### `src/main.js` — アプリケーションエントリーポイント

**役割**: Vueアプリの起動。`app.use(router)` でVue Routerを組み込み、`#app` にマウント。

---

#### `src/App.vue` — ルートコンポーネント

**役割**: 全ページ共通のレイアウト（`NavBar` + `RouterView`）。

---

#### `src/api/index.js` — API通信レイヤー

**役割**: バックエンドAPIとの通信を一元管理する。全エンドポイントのURLと、認証ヘッダーの自動付与を担当。

**設計の特徴**:
- `axios.create()` でベースURLと共通ヘッダーを設定した axios インスタンスを作成
- `interceptors.request` で全リクエストに `Authorization: Bearer {id_token}` を自動付与
- `interceptors.response` で `401` エラー時に自動ログアウト（sessionStorageクリア → `/login` へリダイレクト）

**エクスポート**: `playersApi`, `gamesApi`, `statsApi`, `analyticsApi`, `pitchersApi`, `historyApi`

**学習ポイント**: axios のインターセプターパターン。DRYに認証処理を共通化。

---

#### `src/composables/useYear.js` — 年度選択Composable

**役割**: 全ページから共有される「選択中の年度」の状態管理。`useYear()` を import することで、どのコンポーネントからも同じ `year` ref を参照・変更できる。

**実装**:
```js
// モジュールレベルで1つだけ定義（シングルトン）
const year = ref(null);  // null = 通算

export function useYear() {
  return { year };
}
```

**学習ポイント**: Vuex/Piniaを使わずに、シンプルなシングルトンComposableでグローバル状態を共有するパターン。

---

#### `src/router/index.js` — ルーター定義

**役割**: URLと表示するコンポーネントの対応（ルーティング）を定義する。

**ルート一覧**:

| パス | コンポーネント | 説明 |
|-----|-------------|------|
| `/login` | `LoginView` | ログイン画面（認証不要） |
| `/` | `DashboardView` | ダッシュボード（要認証） |
| `/players` | `PlayersView` | 選手一覧（要認証） |
| `/players/:id` | `PlayerDetailView` | 選手詳細（要認証） |
| `/games` | `GamesView` | 試合一覧（要認証） |
| `/analytics` | `AnalyticsView` | 分析（要認証） |
| `/pitchers` | `PitchersView` | 投手成績（要認証） |
| `/history` | `HistoryView` | 実行履歴（要認証） |

**認証ガード**: `router.beforeEach()` で `requiresAuth: true` のルートにアクセス時、sessionStorage に id_token がなければ `/login` にリダイレクト。

---

#### `src/components/NavBar.vue` — ナビゲーションバー

**役割**: 全ページ上部に表示されるナビゲーション。チーム名・ページリンク・ログアウトボタンを表示。

---

#### `src/components/YearSelector.vue` — 年度選択ドロップダウン

**役割**: `useYear()` の `year` を操作するUI部品。選択変更で全ページの成績表示が切り替わる。

---

#### `src/components/LoadingSpinner.vue` — ローディング表示

**役割**: API通信中に表示するスピナーアニメーション。`v-if="loading"` で制御。

---

#### `src/components/ErrorAlert.vue` — エラーアラート

**役割**: API通信エラー時にエラーメッセージを表示するアラートコンポーネント。

---

#### `src/views/LoginView.vue` — ログイン画面

**役割**: Google Sign-In ボタンを表示し、認証成功時に id_token を `sessionStorage` に保存してダッシュボードへリダイレクト。

**Google認証フロー**:
1. ページ読み込み時に Google Identity Services の JS SDK を初期化
2. ボタンクリックでGoogleの認証ポップアップを表示
3. 認証成功のコールバックで `credential`（id_token）を取得
4. `sessionStorage.setItem("id_token", credential)` で保存
5. `router.push("/")` でダッシュボードへ

---

#### `src/views/DashboardView.vue` — ダッシュボード

**役割**: チームの成績サマリーをカード形式で表示するトップページ。

**表示セクション**:
- チーム試合成績（勝敗数・勝率）
- チーム打撃成績（チーム打率・本塁打・盗塁）
- チーム投手成績（チーム防御率・奪三振）
- 累積打率推移グラフ（Chart.js Line グラフ）

---

#### `src/views/PlayersView.vue` — 選手一覧

**役割**: 全選手の成績テーブル。テキスト検索と行クリックによる詳細画面への遷移。

**機能**:
- テキスト入力で選手名をリアルタイムフィルタリング（`computed` プロパティ使用）
- 行クリックで `/players/:id` に遷移

---

#### `src/views/PlayerDetailView.vue` — 選手詳細

**役割**: 特定選手の詳細成績を複数の視点で表示する。

**表示内容**:
- 基本情報（選手名・通算成績サマリー）
- 試合別成績テーブル
- 累積推移折れ線グラフ（Chart.js Line）
- 打球方向横棒グラフ（Chart.js Bar, 5方向の割合）

---

#### `src/views/GamesView.vue` — 試合一覧

**役割**: 試合一覧を月フィルター付きで表示し、クリックで詳細モーダルを開く。

**機能**:
- 月のセレクトボックスでフィルタリング
- 試合行クリックでモーダル表示（スコア・打撃成績）

---

#### `src/views/AnalyticsView.vue` — 分析

**役割**: 分析データを2タブで表示する。

**タブ**:
1. 打球方向グラフ（選手別の5方向分布、横棒グラフ）
2. 累積打率・OPS推移（複数選手の試合順推移、折れ線グラフ）

---

#### `src/views/PitchersView.vue` — 投手成績

**役割**: 投手の通算成績テーブルと、クリックで試合別成績モーダルを表示。

---

#### `src/views/HistoryView.vue` — 実行履歴

**役割**: `run_all.py` の実行履歴を一覧表示し、run_id でグループ化して表示する。

**フィルター機能**: 日付・ステップ名・件数のクエリパラメーターを組み合わせてAPIに送信。

---

## 5. データベーススキーマ

### テーブル構成とリレーション

```
teams (チーム)
  ├─ team_id   SERIAL PRIMARY KEY
  └─ team_name TEXT UNIQUE

players (選手)
  ├─ player_id   SERIAL PRIMARY KEY
  ├─ player_name TEXT
  └─ team_id     INT → teams(team_id)
  └─ UNIQUE (player_name, team_id)

games (試合)
  ├─ game_id      SERIAL PRIMARY KEY
  ├─ game_date    DATE
  ├─ home_team_id INT → teams(team_id)
  ├─ away_team_id INT → teams(team_id)
  ├─ game_number  INT
  ├─ home_score   INT
  ├─ away_score   INT
  ├─ result       VARCHAR(1)  ... "W" / "L" / "D"
  └─ UNIQUE (game_date, home_team_id, away_team_id, game_number)

batting_stats (打撃成績)
  ├─ batting_id          SERIAL PRIMARY KEY
  ├─ player_id           INT → players(player_id)
  ├─ game_id             INT → games(game_id)
  ├─ at_bat_count        INT  ... 打数
  ├─ hit_count           INT  ... 安打
  ├─ double_hit          INT  ... 2塁打
  ├─ triple              INT  ... 3塁打
  ├─ homerun             INT  ... 本塁打
  ├─ walk_count          INT  ... 四死球
  ├─ strike_out          INT  ... 三振
  ├─ stolen_base         INT  ... 盗塁
  ├─ right_9             INT  ... 打球方向: ライト
  ├─ right_center        INT  ... 打球方向: ライト中間
  ├─ center              INT  ... 打球方向: センター
  ├─ left_center         INT  ... 打球方向: レフト中間
  ├─ left_7              INT  ... 打球方向: レフト
  ├─ on_base             INT  ... 出塁数
  ├─ on_base_opportunity INT  ... 出塁機会数
  └─ UNIQUE (player_id, game_id)

pitcher_stats (投手成績)
  ├─ pitcher_stat_id  SERIAL PRIMARY KEY
  ├─ pitcher_id       INT → players(player_id)
  ├─ game_id          INT → games(game_id)
  ├─ batters_faced    INT  ... 対戦打者数
  ├─ pitch_count      INT  ... 投球数
  ├─ hits_allowed     INT  ... 被安打
  ├─ homerun_allowed  INT  ... 被本塁打
  ├─ walks_allowed    INT  ... 与四死球
  ├─ strikeouts       INT  ... 奪三振
  ├─ runs_allowed     INT  ... 失点
  ├─ right_9          INT  ... 打球方向: ライト
  ├─ right_center     INT  ... 打球方向: ライト中間
  ├─ center           INT  ... 打球方向: センター
  ├─ left_center      INT  ... 打球方向: レフト中間
  ├─ left_7           INT  ... 打球方向: レフト
  ├─ innings_pitched  INT  ... 投球回（整数部）
  ├─ outs             INT  ... アウト数（0 / 1 / 2）
  ├─ earned_runs      INT  ... 自責点
  └─ UNIQUE (pitcher_id, game_id)
```

### 重複防止の設計

| 対策 | 場所 | 説明 |
|-----|------|------|
| `UNIQUE` 制約 | `batting_stats`, `pitcher_stats` | 1選手×1試合で1行のみ |
| `SELECT-first` パターン | `db_repository.py` | INSERT前にSELECTで確認し、IDの自動採番を無駄にしない |
| `UNIQUE` 制約 | `teams`, `players`, `games` | マスターデータの重複を防止 |

---

## 6. データフロー

### CLIワークフロー全体図

```
Excelファイル（打撃内訳・相手攻撃・チーム投手シート）
      │
      ▼
validate.py ──── 検証エラー ──→ 処理中断・エラーメッセージ表示
      │ (正常)
      ▼
generate.py
  ├─→ BattingRepository.load_records()
  │       ↓ [BattingRecord リスト]
  │   BattingService.summarize_hits()
  │       ↓ [多段階辞書]
  │   BattingView.display_summary()  → コンソール出力
  │
  ├─→ PitcherRepository.load_records()
  │       ↓ [PitcherRecord リスト]
  │   PitcherService.summarize()
  │       ↓ [集計辞書]
  │   PitcherView.display_summary()  → コンソール出力
  │
  └─→ BattingController.export_game_inputs()
          ↓
      data/game_inputs/{date}_{opponent}_{game}.txt  （生成）
      │
      ▼
import_db.py
  ├─→ BattingService.import_to_db()
  │       ↓
  │   DBRepository.insert_players()
  │   DBRepository.insert_records()
  │       ↓
  │   PostgreSQL: teams / players / batting_stats テーブル更新
  │
  ├─→ PitcherService.import_to_db()
  │       ↓
  │   DBRepository.insert_pitcher_records()
  │       ↓
  │   PostgreSQL: pitcher_stats テーブル更新
  │
  └─→ ScoreController.write_game()（write_score.py で実行）
          ↓
      ScoreExcelWriter → スコアExcelファイル更新
      │
      ▼
analytics.py --year 2026
  ├─→ AnalyticsRepository.fetch_player_batting_stats()
  │       ↓ [DataFrame]
  │   AnalyticsService.calculate_*()
  │       ↓ [加工済みデータ]
  │   AnalyticsExcelWriter.write_*()
  │       ↓
  │   analytics_2026.xlsx（3シート: 選手別成績・打球方向・推移グラフ）
  │
  └─→ logs/run_history.jsonl ← 各ステップの実行履歴を追記
```

### Webアプリのデータフロー

```
ブラウザ（Vue 3）
  │
  ├─→ LoginView ── Google Sign-In ──→ id_token を sessionStorage 保存
  │
  ├─→ API通信（src/api/index.js）
  │       │ Authorization: Bearer {id_token}  ← 全リクエストに自動付与
  │       ▼
  │   FastAPI（webapp/backend/main.py）
  │       │ auth.verify_token()  ← id_token を Google API で検証
  │       ▼
  │   Routers（players / games / stats / analytics / pitchers / history）
  │       │ SQL クエリ
  │       ▼
  │   PostgreSQL  ←─── batting_stats, pitcher_stats, games, players, teams
  │       │
  │       ▼
  │   JSONレスポンス
  │       │
  │       ▼
  │   Vue コンポーネント（ref / computed でリアクティブ表示）
  │       │
  │       ├─ Chart.js でグラフレンダリング
  │       └─ Tailwind CSS でスタイリング
  │
  └─→ YearSelector ── year変更 ──→ useYear() の ref 更新 ──→ 全ページ再取得
```

---

## 7. 主要な設計パターン

学習観点から、本プロジェクトで使われている主要な設計パターンをまとめます。

### バックエンド（Python）

| パターン | 実装場所 | 説明 |
|---------|---------|------|
| **レイヤードアーキテクチャ** | プロジェクト全体 | Model → Repository → Service → Controller → View の層分離。各層は隣接する層のみに依存 |
| **SELECT-first パターン** | `db_repository.py` | `INSERT` 前に `SELECT` で存在確認。`SERIAL` 採番の無駄を防ぎ、IDの飛び番を抑制 |
| **コンテキストマネージャ** | `db_repository.py`, `batting_service.py` | `__enter__` / `__exit__` で `with` 文に対応。リソース（DB接続）の確実な解放を保証 |
| **遅延初期化（Lazy Init）** | `service/batting_service.py` | `_db_repo = None` で宣言し、実際に必要になったときだけDB接続。コスト節約 |
| **Dataclass + 型検証** | `model/*.py` | `@dataclass` で定型コードを自動生成。`__post_init__()` に検証ロジックを集約 |
| **多段階 defaultdict** | `service/batting_service.py` | `defaultdict(lambda: defaultdict(...))` で多次元の集計辞書を構築 |
| **安全型変換関数** | `utils/excel_util.py` | `None`/`NaN`/`datetime` を一括処理する `safe_*()` 関数群でデータ読み込みを堅牢化 |
| **JSON Lines ログ** | `utils/run_logger.py` | 1行1JSONで追記する軽量ログ形式。大量データでも行単位で読み込め、メモリ効率が良い |
| **12-Factor App 設定** | `config/config.py` | 機密情報を環境変数から読み込み、コードに直接書かない |
| **Depends による認証** | `webapp/backend/auth.py` | FastAPI の `Depends(verify_token)` で全エンドポイントに認証を透過的に適用 |

### フロントエンド（Vue 3）

| パターン | 実装場所 | 説明 |
|---------|---------|------|
| **Composition API** | 全 Vue ファイル | `<script setup>` + `ref` / `computed` / `watch` でロジックを関数として整理 |
| **Composable（シングルトン状態）** | `composables/useYear.js` | モジュールスコープで1つだけ `ref` を定義し、全コンポーネントから import して共有 |
| **axios インターセプター** | `api/index.js` | リクエスト前後に処理を挟み、認証ヘッダーの付与と401エラー処理を共通化 |
| **Navigation Guard** | `router/index.js` | `router.beforeEach()` で認証不要ページ以外へのアクセスを制御 |
| **コンポーネント分割** | `components/*.vue` | `NavBar`・`YearSelector`・`LoadingSpinner`・`ErrorAlert` を共通部品として抽出 |

---

## 8. 技術スタック

### バックエンド

| 分類 | ライブラリ / ツール | 用途 |
|-----|-----------------|------|
| 言語 | Python 3.10+ | — |
| Excelデータ読み込み | `pandas`, `openpyxl` | Excel読み込み・書き込み・グラフ作成 |
| DB接続 | `psycopg2` | PostgreSQL接続ドライバ |
| REST API | `fastapi`, `uvicorn` | APIサーバー（ASGI） |
| 認証 | `google-auth` | Google OAuth id_token 検証 |
| Rate Limiting | `slowapi` | APIのリクエスト数制限 |
| RDBMS | PostgreSQL 15 | 成績データの永続化 |
| コンテナ | Docker / Docker Compose | DB・バックエンドのコンテナ化 |

### フロントエンド

| 分類 | ライブラリ / ツール | 用途 |
|-----|-----------------|------|
| UIフレームワーク | Vue 3 | Composition API によるリアクティブUI |
| ルーティング | Vue Router 4 | クライアントサイドルーティング |
| HTTP通信 | axios | REST API通信・インターセプター |
| グラフ | Chart.js + vue-chartjs | Line・Bar グラフの描画 |
| CSS | Tailwind CSS | ユーティリティファーストCSS |
| バンドラー | Vite | 高速開発サーバー・本番ビルド |

---

## 9. 実行コマンド集

### CLIワークフロー

```bash
# ── 推奨: 一括実行 ──
python run_all.py                          # 全ステップ実行
python run_all.py --year 2026              # 年度指定
python run_all.py --skip-validate          # バリデーションスキップ
python run_all.py --skip-analytics         # 分析出力スキップ

# ── 個別実行 ──
python validate.py                         # 入力検証のみ
python generate.py                         # 集計・試合入力ファイル生成
python import_db.py                        # DB登録
python write_score.py \
  --game data/game_inputs/2026-03-27_xxx_1.txt \
  --csv  data/scores/2026-03-27_xxx.csv    # スコアExcel書き込み
python analytics.py --year 2026            # 分析Excel出力
python show_log.py --last 20               # 最新20件の実行履歴
python show_log.py --date 2026-03-27       # 日付でフィルタ
python show_log.py --step import_db        # ステップでフィルタ
```

### 開発環境起動

```bash
# 開発環境を一括起動（DB初期化 → run_all → backend → frontend）
python dev_start.py
python dev_start.py --skip-init-db         # DB初期化をスキップ
python dev_start.py --skip-run-all         # run_all をスキップ
```

### Docker操作

```bash
cd docker
docker compose up -d db                    # DBのみ起動
docker compose up -d                       # DB + バックエンド起動
docker compose down                        # 停止（データ保持）
docker compose down -v                     # 停止 + データ削除（初期化）
docker compose logs -f backend             # バックエンドのログを追跡
```

### バックエンド・フロントエンド単独起動

```bash
# バックエンド（FastAPI）
cd webapp/backend
uvicorn main:app --reload --port 8000
# → http://localhost:8000/docs  （Swagger UI）

# フロントエンド（Vue 3）
cd webapp/frontend
npm install
npm run dev
# → http://localhost:5173

# フロントエンド本番ビルド
npm run build
# → dist/ に出力
```

### テスト実行

```bash
python -m unittest discover -s tests -p "test_*.py" -v
```
