# CHANGELOG

Webアプリ改修の完了履歴を記録します。

---

## [投手成績] Phase 1〜4 投手成績機能追加 - 2026-03-21

### 追加
- `model/pitcher_record.py`: 1打席分の投手成績データクラス（`PitcherRecord`）
- `repository/pitcher_repository.py`: 「データ入力シート(相手攻撃)」を読み込み `PitcherRecord` リストに変換
- `service/pitcher_service.py`: 試合・投手単位に集計（`summarize()`）＋ DB登録（`import_to_db()`）
- `view/pitcher_view.py`: 投手別成績サマリーのコンソール表示
- `generate_pitcher.py`: Phase 1 エントリーポイント（Excel読み込み・集計・コンソール表示）
- `import_pitcher_db.py`: Phase 2 エントリーポイント（Excel読み込み → DB登録）
- `tmp/sql/007_add_pitcher_stats_table.sql`: `pitcher_stats` テーブル追加マイグレーション
- `webapp/backend/routers/pitchers.py`: `GET /api/pitchers`, `GET /api/pitchers/{id}/stats` エンドポイント
- `webapp/frontend/src/views/PitchersView.vue`: 投手成績一覧テーブル＋試合別成績モーダル
- `docs/plan/pitcher_stats.md`: 投手成績機能の実装計画ドキュメント

### 変更
- `repository/db_repository.py`: `insert_pitcher_stats()` メソッドを追加
- `webapp/backend/main.py`: `pitchers` ルーターを登録
- `webapp/frontend/src/api/index.js`: `pitchersApi`（`list`, `stats`）を追加
- `webapp/frontend/src/router/index.js`: `/pitchers` ルートを追加
- `webapp/frontend/src/components/NavBar.vue`: 「投手成績」ナビリンクを追加

---

## [Phase 5] 選手詳細ページ - 2026-03-19

### 追加
- 選手詳細ページ（`PlayerDetailView.vue`）を新規作成（ルート: `/players/:id`）
  - シーズンサマリーカード（試合数・打数・安打・本塁打・打率・OPS）
  - 累積打率・OPS推移折れ線グラフ
  - 打球方向横棒グラフ（選手単体）
  - 試合別成績テーブル（累積打率・OPS付き）
- `PlayersView.vue`: 選手行クリックで `/players/:id` へ遷移するよう更新
- `router/index.js`: `/players/:id` ルートを追加

### 変更
- `analytics.py`（バックエンド）: `hit-direction` エンドポイントに `player_id` フィルターを追加
- `api/index.js`: `analyticsApi.hitDirection()` に `playerId` パラメーターを追加対応

---

## [Phase 4] グラフ・ビジュアライゼーション追加 - 2026-03-19

### 追加
- `AnalyticsView.vue`: 累積打率・OPS推移折れ線グラフを追加（vue-chartjs + Chart.js）
- `AnalyticsView.vue`: 打球方向横棒グラフを追加（選手ごとの方向割合をカラー区別）
- `DashboardView.vue`: チームトレンドグラフを追加

---

## [Phase 3] フロントエンド画面実装 - 2026-03-18

### 追加
- `DashboardView.vue`: サマリーカード（試合数・打率・OPS・本塁打）＋OPSランキング Top10
- `PlayersView.vue`: 全選手成績テーブル（年度フィルタ・選手名テキスト絞り込み・OPS降順ソート）
- `GamesView.vue`: 試合一覧（月フィルター）＋試合行クリックで詳細モーダル（選手別打撃成績）
- `AnalyticsView.vue`: タブ切り替え（打球方向テーブル／累積打率・OPS推移テーブル）

---

## [Phase 2] フロントエンド基盤構築 - 2026-03-18

### 追加
- Vue 3 + Vite + Tailwind CSS プロジェクト初期化
- Vue Router 設定（4画面: ダッシュボード・選手成績・試合一覧・分析）
- 共通コンポーネント
  - `NavBar.vue`: ナビゲーションバー
  - `YearSelector.vue`: 年度切り替えセレクター（全画面共通状態）
  - `LoadingSpinner.vue`: ローディング表示
  - `ErrorAlert.vue`: エラー表示
- APIクライアント（`src/api/index.js`）
- 年度共有composable（`src/composables/useYear.js`）

---

## [Phase 1] バックエンドAPI構築 - 2026-03-xx

### 追加
- FastAPI エントリーポイント（`webapp/backend/main.py`）
- CORS設定（フロントエンド開発サーバー対応）
- ルーター
  - `routers/players.py`: 選手一覧・詳細・試合別成績
  - `routers/games.py`: 試合一覧・試合詳細
  - `routers/stats.py`: シーズン集計・OPSランキング
  - `routers/analytics.py`: 打球方向・累積打率OPS推移
- DB接続モジュール（`webapp/backend/database.py`）
- 依存パッケージ定義（`requirements.txt`）
