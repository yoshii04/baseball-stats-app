# ADR-0001: フロントエンドに Vue 3（SPA）を採用する

- ステータス: 採用済み
- 決定時期: 2026-03-17 ごろ（Phase 2 フロントエンド基盤構築。`docs/plan/overview.md`）
- 関連: [ADR-0003](0003-google-oauth-allowed-emails.md)

## 背景

試合後に Excel から DB へ登録した成績を、チームメンバーがブラウザで確認できるようにする必要があった。
当初の利用形態は CLI と Excel 出力のみで、一覧・グラフ・選手別の詳細を見るには Excel を開く必要があった。

## 決定

フロントエンドは **Vue 3（Composition API / `<script setup>`）+ Vite + Tailwind CSS** の SPA とし、
バックエンド（FastAPI）とは REST API（JSON）だけで接続する。

- ルーティング: Vue Router 4
- グラフ: Chart.js（vue-chartjs）
- 通信: axios（`src/api/index.js` に集約。認証ヘッダーの付与と 401 時のログアウトもここ）
- 状態管理: Pinia / Vuex は使わない。全画面で共有する年度選択だけを
  `composables/useYear.js` のモジュールスコープの `ref` で持つ

## 理由

当時の選定理由（他フレームワークとの比較など）を書いた記録は残っていない。
以下は、この構成が現在成立させていることである。

- ビルド成果物が静的ファイルだけなので、S3 + CloudFront で配信でき、サーバーを増やさずに済む（AWS 構成）。
- フロントとバックエンドが REST API だけで分離されており、同じ API を CLI や別クライアントからも使える。
- 共有状態が年度選択だけなので、状態管理ライブラリなしで足りている。

## 結果

- 画面数はログインを除いて 7（ダッシュボード・打撃成績・選手詳細・投手成績・試合一覧・分析・実行履歴）。
- 表示用の設定（チーム名など）はビルド時の環境変数（`VITE_*`）で埋め込む。変更するには再ビルドが必要。
- フロントエンドの自動テストはまだ無い。導入する場合は Vitest + Vue Test Utils を想定している
  （`docs/plan/public_release_plan.md` STEP 3）。
