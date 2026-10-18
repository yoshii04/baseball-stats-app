# Webアプリ改修計画 - 全体概要

## 目的

DB登録済みの野球成績データを、ブラウザから直感的に確認・分析できるWebアプリケーションを構築する。

---

## 技術スタック

| 層 | 技術 |
|---|---|
| バックエンド | FastAPI (Python) |
| データベース | PostgreSQL |
| フロントエンド | Vue 3 + Vite |
| スタイリング | Tailwind CSS |
| ルーティング | Vue Router |

---

## 画面構成

| パス | 画面名 | 概要 |
|---|---|---|
| `/` | ダッシュボード | チームサマリー・OPSランキング |
| `/players` | 選手成績 | 全選手のシーズン成績一覧 |
| `/games` | 試合一覧 | 試合リスト・試合詳細モーダル |
| `/analytics` | 分析 | 打球方向・累積成績推移 |

---

## Phaseサマリー

| Phase | 内容 | 状態 |
|---|---|---|
| Phase 1 | バックエンドAPI構築（FastAPI） | ✅ 完了 |
| Phase 2 | フロントエンド基盤構築（Vue 3） | ✅ 完了 |
| Phase 3 | フロントエンド画面実装（各View） | ✅ 完了 |
| Phase 4 | グラフ・ビジュアライゼーション追加 | ✅ 完了 |
| Phase 5 | 選手詳細ページ | ✅ 完了 |

---

## APIエンドポイント一覧

| メソッド | パス | 内容 |
|---|---|---|
| GET | `/api/players` | 選手一覧（シーズン成績付き） |
| GET | `/api/players/{id}` | 選手基本情報 |
| GET | `/api/players/{id}/stats` | 選手別試合ログ＋累積打率・OPS |
| GET | `/api/games` | 試合一覧（年・月フィルター） |
| GET | `/api/games/{id}` | 試合詳細（選手別成績） |
| GET | `/api/stats/season` | チームシーズン集計 |
| GET | `/api/stats/ranking` | OPSランキング |
| GET | `/api/analytics/hit-direction` | 打球方向集計 |
| GET | `/api/analytics/batting-trend` | 累積打率・OPS推移 |
