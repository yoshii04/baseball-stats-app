# 運用手順（CLI の使い方）

試合後のワークフロー（検証 → 入力ファイル生成 → DB 登録 → 分析 Excel 出力）と、スコアの Excel 書き込みの手順です。セットアップは [README](../README.md) を参照してください。

## 0. 開発環境 一括起動（dev_start.py）【推奨】

DB初期化から Web アプリ起動まで1コマンドで実行します。

```bash
python dev_start.py                          # DB初期化 → run_all → backend → frontend を一括起動
python dev_start.py --skip-init-db           # DB初期化をスキップ（既存データ保持）
python dev_start.py --skip-run-all           # run_all をスキップ
python dev_start.py --skip-init-db --skip-run-all  # backend + frontend のみ起動
```

実行順序: DB初期化（`down -v` → `up db`）→ `run_all.py --skip-analytics` → `docker compose up backend` → `npm run dev`（フォアグラウンド）

---

## 0-a. ワークフロー一括実行（run_all.py）

試合後の一連の手順を1コマンドで実行します。

```bash
# 基本（当年で全ステップ実行）
python run_all.py

# 年度を指定
python run_all.py --year 2026

# validate をスキップ
python run_all.py --skip-validate

# analytics をスキップ（DB登録のみ）
python run_all.py --skip-analytics
```

実行内容：`validate.py` → `generate.py` → `import_db.py` → `analytics.py` を順次実行し、各ステップの成否を `[OK]` / `[NG]` で表示します。エラー発生時は途中停止して原因を案内します。

| オプション | 説明 |
|-----------|------|
| `--year` | analytics の対象年度（省略時: 当年） |
| `--skip-validate` | validate ステップをスキップする |
| `--skip-analytics` | analytics ステップをスキップする |

---

## 0-b. 実行履歴の確認（show_log.py）

`run_all.py` の実行履歴を確認します。実行結果は `logs/run_history.jsonl` に自動保存されます。

```bash
# 全履歴を表示
python show_log.py

# 指定日付のみ表示
python show_log.py --date 2026-03-26

# ステップ名で絞り込み
python show_log.py --step import_db

# 最新10件のみ表示
python show_log.py --last 10
```

| オプション | 説明 |
|-----------|------|
| `--date` | `YYYY-MM-DD` 形式で日付絞り込み |
| `--step` | `validate` / `generate` / `import_db` / `analytics` でステップ絞り込み |
| `--last` | 最新 N 件のみ表示 |

Web UI の `/history` ページでも同様の履歴を確認できます。

---

## 0-c. データ入力バリデーション（validate.py）

Excelデータを読み込み、DB登録前に入力ミスを検出します。

```bash
# 基本実行（WARNING / ERROR を表示）
python validate.py

# WARNING も ERROR として扱う
python validate.py --strict
```

| チェック | レベル | 内容 |
|---|---|---|
| 打撃内訳の整合性 | ERROR | 長打計 > 安打 / 安打 > 打数 / 三振 > 打数 / 出塁 > 出塁機会 |
| 日付フォーマット | WARNING | 日付として解析できない値 |
| 対戦相手名の揺れ | WARNING | 全角スペースを含むスペース正規化後に同一視できる名前が複数存在 |
| 投手名 | WARNING | 相手攻撃シートの投手名がチーム単位シートに存在しない |

ERROR がある場合は終了コード 1 を返し、`run_all.py` がその時点で中断します。

---

## 1. Excel読み込み・集計・入力ファイル生成（generate.py）

```bash
python generate.py
```

実行内容：
1. `excel_file` から打撃記録を読み込む
2. 打撃成績を集計してコンソールに表示
3. 試合ごとの入力ファイルを `data/game_inputs/` に自動生成
4. 投手成績シートを読み込み、投手別・試合別に集計してコンソールに表示

**自動生成される試合入力ファイルの例** (`data/game_inputs/2026-03-07_相手A高校_1.txt`):

```
date: 2026-03-07
opponent: 相手A高校
game_number: 1
venue:
pitcher:
doubles: 選手A、選手B
triples: 選手D
homeruns:
```

> `venue`（会場）と `pitcher`（ピッチャー）は打撃成績Excelに含まれないため空欄です。必要に応じて手動で追記してください。

---

## 2. DBへの打撃成績登録（import_db.py）

```bash
python import_db.py
```

実行内容：
1. `docker compose up -d --wait db` で DB コンテナを起動（起動済みなら何もしない）
2. 打撃成績をDBに登録、DB登録済み成績をコンソールに表示
3. 投手成績をDBに登録
4. チーム成績（試合一覧）をDBに登録

---

## 3. DBへの打撃成績登録後に分析Excelを出力する（analytics.py）

```bash
python analytics.py --year 2026
```

実行内容：
1. 指定年度の打撃成績をDBから取得
2. 累積成績・打球方向%を計算
3. `analytics_{year}.xlsx` を出力（3シート構成）

**出力ファイル**: `analytics_2026.xlsx`

### 出力シート構成

| シート | 内容 | グラフ |
|--------|------|--------|
| 選手別打撃成績 | 17列（選手名〜OPS）、OPSカラースケール付き | OPSランキング横棒 ＋ 安打種別積み上げ |
| 打球方向分析 | 方向別本数・各方向%、データバー条件書式 | 打球方向分布100%積み上げ |
| 選手別成績推移 | 選手ごとのブロック＋累積打率・累積OPS | 主要選手の累積打率推移折れ線 |

### オプション

| オプション | 説明 |
|-----------|------|
| `--year` | 対象年度（必須、例: `2026`） |
| `--output` | 出力ファイルパス（省略時: `analytics_{year}.xlsx`） |

> **事前条件**: `python import_db.py` を実行してDBにデータを登録済みであること。

---

## 4. スコアをExcelに書き込む（write_score.py）

### 単一ファイル：スコアあり（CSVファイル指定）

```bash
python write_score.py \
  --game data/game_inputs/2026-03-07_相手A高校_1.txt \
  --csv  data/scores/sample.csv
```

### 単一ファイル：スコアなし（空欄で書き込む）

試合は確定しているがスコアがまだない場合、`--csv` を省略するとスコア欄が空欄になります。

```bash
python write_score.py --game data/game_inputs/2026-03-07_相手A高校_1.txt
```

### 一括処理：ディレクトリ指定

`--game` にディレクトリを指定すると、配下の全 `.txt` ファイルを処理します。
`--csv-dir` を指定すると、日付・試合番号でCSVを自動マッチングします。

```bash
# ゲームファイルのみ一括処理（スコア空欄）
python write_score.py --game data/game_inputs/

# CSVディレクトリも指定して自動マッチング
python write_score.py --game data/game_inputs/ --csv-dir /path/to/csv_dir/
python write_score.py --game data/game_inputs/ --csv-dir data/scores/

# DRY RUNで確認
python write_score.py --game data/game_inputs/ --csv-dir /path/to/csv_dir/ --dry-run
```

> **CSVの自動マッチング規則**: ゲームファイル `YYYY-MM-DD_相手チーム_N.txt` に対し、
> `*_YYYY-MM-DD_N.csv` というパターンでCSVを検索します（例: `baseball_score_2026-03-07_1.csv`）。

### オプション一覧

| オプション | 説明 |
|-----------|------|
| `--game` | 試合入力ファイルのパス、またはディレクトリ（必須） |
| `--csv` | スコアCSVファイルのパス（単一ファイル指定時のみ有効） |
| `--csv-dir` | CSVファイルのディレクトリ（日付・試合番号で自動マッチング） |
| `--start-row` | 書き込み開始行（省略時は自動検出） |
| `--dry-run` | 書き込まず内容のみ確認表示する |
