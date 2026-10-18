# 投手成績機能 段階的追加計画

## Context

「データ入力シート(相手攻撃)」Excelシートには、相手チームの打者1打席を1行として記録されており、
「選手名」列（[4]列）が**自チームの投手名**に対応している。
このシートを集計することで自チーム投手の投手成績（被安打・与四死球・奪三振・失点など）を導出できる。
現状はDBに投手成績テーブルがなく、Webアプリにも投手画面が存在しない。
段階的に機能を追加し、打撃成績と同様に投手成績を管理・可視化できる状態にする。

---

## Excelシート「データ入力シート(相手攻撃)」の構造

| インデックス | 列名（flatten後） | 意味 |
|---|---|---|
| 0 | (blank) | ゲームID（試合を一意識別） |
| 1 | 日 | 試合日 |
| 2 | 試合回数 | 試合番号（ダブルヘッダー: 1 or 2） |
| 3 | 対戦相手 | 相手チーム名 |
| 4 | 選手名 | **自チーム投手名** |
| 5 | 対戦相手_2 | 相手打者コード ('1-1', '1-2'...) |
| 7 | 投球 | 投球数 |
| 10 | 塁打本塁打 | 被本塁打 |
| 32 | 得点 | 失点 |
| 39 | 四死球 | 与四死球 |
| 41 | 三振 | 奪三振 |
| 42 | 安打 | 被安打 |
| 47-51 | 右/右中/中/左中/左 | 被打球方向 |

1行 = 1打席（per-at-bat）。同一ゲームに複数投手が登板する場合あり（実データで確認済み）。

---

## Phase 1: Excelデータ読み込み基盤

**目的**: 相手攻撃シートを読み込み、投手別・試合別に集計してコンソール表示する。

### 新規ファイル

**`model/pitcher_record.py`**
1打席分の投手成績データクラス。`BattingRecord`（`model/batting_record.py`）と同様のパターン。

```python
@dataclass
class PitcherRecord:
    date: str
    opponent: str
    pitcher_name: str
    game_number: int = 1
    pitch_count: int = 0
    homerun_allowed: int = 0
    walks_allowed: int = 0
    strikeouts: int = 0
    hits_allowed: int = 0
    runs_allowed: int = 0
    right_9: int = 0
    right_center: int = 0
    center: int = 0
    left_center: int = 0
    left_7: int = 0
```

**`repository/pitcher_repository.py`**
`BattingRepository`（`repository/batting_repository.py`）の`_flatten_columns`・`load_records`パターンを踏襲。
- `_flatten_columns()`: 同一ロジックを再利用
- `load_records(excel_file, sheet_name)`: "データ入力シート(相手攻撃)" を読み込み `PitcherRecord` リストを返す
- 注意: `試合回数` 列 = 試合番号（イニングではない）、`選手名` 列 = 投手名

**`service/pitcher_service.py`**
PitcherRecordリストを (date, opponent, game_number, pitcher_name) でグルーピング・集計。
集計後の構造: `{ (date, opponent, game_number) → { pitcher_name → stats_dict } }`

**`view/pitcher_view.py`**
コンソール表示（投手別成績サマリー）。

**`generate_pitcher.py`** (エントリーポイント)
読み込み・集計・コンソール表示を実行。

### 再利用する既存コード
- `utils/excel_util.py`: `safe_str()`, `safe_int()`, `safe_game_number()`
- `repository/batting_repository.py`: `_flatten_columns()` の実装パターン

### 設定（config.json）
シート名を `pitcher_sheet_name` キーで指定可能。省略時は `"データ入力シート(相手攻撃)"` を使用。

### 検証
```bash
python generate_pitcher.py
# 投手別・試合別の被安打・与四死球・奪三振・失点がコンソールに表示される
```

---

## Phase 2: DBへの投手成績登録

**目的**: 集計した投手成績をPostgreSQLに登録できるようにする。

### DBマイグレーション

**`tmp/sql/007_add_pitcher_stats_table.sql`**
```sql
CREATE TABLE pitcher_stats (
    pitcher_stat_id SERIAL PRIMARY KEY,
    pitcher_id INT NOT NULL REFERENCES players(player_id),
    game_id INT NOT NULL REFERENCES games(game_id),
    batters_faced INT,
    pitch_count INT,
    hits_allowed INT,
    homerun_allowed INT,
    walks_allowed INT,
    strikeouts INT,
    runs_allowed INT,
    right_9 INT,
    right_center INT,
    center INT,
    left_center INT,
    left_7 INT,
    CONSTRAINT uq_pitcher_stats_pitcher_game UNIQUE (pitcher_id, game_id)
);
```

### 変更ファイル

**`repository/db_repository.py`**
以下メソッドを追加:
- `insert_pitcher_stats(cur, pitcher_id, game_id, stats)`: ON CONFLICT DO UPDATE パターン

**`service/pitcher_service.py`** に追記:
- `import_to_db()`: DBRepositoryを使い投手成績を登録
  - `get_or_create_player(pitcher_name, our_team_id)` で pitcher_id 取得
  - `get_or_create_game(game_date, home_team_id, away_team_id, game_number)` で game_id 取得

**`import_pitcher_db.py`** (新規エントリーポイント)
- Excel読み込み → 集計 → DB登録のフロー

### 検証
```bash
python import_pitcher_db.py
psql -h localhost -p 5433 -U ... -d baseball_db \
  -c "SELECT p.player_name, g.game_date, ps.hits_allowed, ps.strikeouts FROM pitcher_stats ps JOIN players p ON p.player_id=ps.pitcher_id JOIN games g ON g.game_id=ps.game_id;"
```

---

## Phase 3: Web API (FastAPI)

**目的**: DB登録済み投手成績をREST APIで取得できるようにする。

### 新規ファイル

**`webapp/backend/routers/pitchers.py`**
`webapp/backend/routers/players.py` のパターンを踏襲。

| エンドポイント | 説明 |
|---|---|
| `GET /api/pitchers?year=` | 投手一覧（シーズン集計: 試合数, 打者数, 被安打, 与四死球, 奪三振, 失点, WHIP） |
| `GET /api/pitchers/{id}/stats?year=` | 投手別 試合ごとの成績一覧 |

WHIP = (被安打 + 与四死球) / 対戦打者数 × 3（打者3人 = 1イニング換算）

### 変更ファイル

**`webapp/backend/main.py`**
`from routers import pitchers` を追加し、`app.include_router(pitchers.router)` を登録。

**`webapp/frontend/src/api/index.js`**
投手APIのaxios関数を追加:
```js
export const pitchersApi = {
  list:  (year)            => api.get('/api/pitchers', { params: { year } }),
  stats: (pitcherId, year) => api.get(`/api/pitchers/${pitcherId}/stats`, { params: { year } }),
}
```

### 検証
```bash
# バックエンド起動後
curl http://localhost:8000/api/pitchers?year=2025
# → 投手一覧JSON
```

---

## Phase 4: Web UI (Vue 3)

**目的**: ブラウザで投手成績を確認できるページを追加する。

### 新規ファイル

**`webapp/frontend/src/views/PitchersView.vue`**
`PlayersView.vue` のパターンを踏襲。
- 年度セレクター（`useYear` composable 再利用）
- 投手成績テーブル: 選手名 / 登板試合数 / 打者数 / 投球数 / 被安打 / 被本塁打 / 与四死球 / 奪三振 / 失点 / WHIP
- 行クリックで試合別成績モーダル（`GamesView.vue` のモーダルパターン再利用）

### 変更ファイル

**`webapp/frontend/src/router/index.js`**
`/pitchers` ルートを追加。

**`webapp/frontend/src/components/NavBar.vue`**
「投手成績」リンクを「選手成績」の隣に追加。

### 検証
```bash
cd webapp/frontend && npm run dev
# http://localhost:5173/pitchers で投手一覧が表示される
```

---

## Phase 5: 分析Excel出力への追加（将来）

**目的**: `analytics.py` の分析Excel出力に投手成績シートを追加する。

### 概要
- `repository/analytics_repository.py`: 投手成績集計クエリを追加
- `repository/analytics_excel_writer.py`: 投手成績シートを追加（WHIP・奪三振率グラフなど）
- `service/analytics_service.py`: 投手成績の累積推移計算を追加

---

## ファイル変更サマリー

| Phase | 新規ファイル | 変更ファイル |
|---|---|---|
| 1 | `model/pitcher_record.py`, `repository/pitcher_repository.py`, `service/pitcher_service.py`, `view/pitcher_view.py`, `generate_pitcher.py` | - |
| 2 | `tmp/sql/007_add_pitcher_stats_table.sql`, `import_pitcher_db.py` | `repository/db_repository.py`, `service/pitcher_service.py` |
| 3 | `webapp/backend/routers/pitchers.py` | `webapp/backend/main.py`, `webapp/frontend/src/api/index.js` |
| 4 | `webapp/frontend/src/views/PitchersView.vue` | `webapp/frontend/src/router/index.js`, `webapp/frontend/src/components/NavBar.vue` |
| 5 | - | `repository/analytics_repository.py`, `repository/analytics_excel_writer.py`, `service/analytics_service.py` |

---

## 実装状況

| Phase | 状態 |
|---|---|
| Phase 1 | 完了 |
| Phase 2 | 完了 |
| Phase 3 | 完了 |
| Phase 4 | 完了 |
| Phase 5 | 未着手 |
