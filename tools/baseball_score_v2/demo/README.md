# デモ（合成データ）

架空のチーム・選手・試合による合成データで、**画面まで一括で起動**します。実データは使いません。
Excel も Google アカウントも不要です。

## 起動

```bash
cd tools/baseball_score_v2/demo
docker compose up --build
```

http://localhost:8090 を開くと、ダッシュボードが表示されます（初回はイメージのビルドに数分かかります）。

止めるとき:

```bash
docker compose down        # コンテナを止める（データは残る）
docker compose down -v     # データも消す。次回の起動で合成データを入れ直す
```

## 内容

| 項目 | 内容 |
|---|---|
| チーム | サンプル高校（架空）。対戦相手 8 校も架空 |
| 選手 | 15 名（デモ・テスト・サンプル・ダミー・仮名 × 太郎・次郎・三郎）。投手 4 名を含む |
| 試合 | 23 試合（2026-03-07〜2026-07-11 の土曜、ダブルヘッダー 4 回）。13 勝 9 敗 1 分 |
| 打撃・投手成績 | 乱数（種を固定）で生成。同じ手順で必ず同じ結果になる |
| 実行履歴 | `run_all.py` を試合日の翌日に実行した、という体の記録（直近 6 回分） |

DB には本番と同じスキーマ（[docker/init.sql](../docker/init.sql)）を使い、その後に [seed.sql](seed.sql) を流し込みます。
画面と API のコードは本番と同じです。違いは次の 3 点だけです。

- 認証を行いません（バックエンドの `DEMO_MODE=true`、フロントの `VITE_DEMO_MODE=true`）。
  `ENV=production` と同時に指定するとバックエンドは起動しません。
- 画面の上部に、合成データであることの注記を出します。
- 打点（`rbi`）は 0 です。実際の取込処理（`import_db.py`）も打点を登録しないため、合わせています。

## 構成

```text
ブラウザ → frontend（nginx、:8090）─ /api/* ─→ backend（FastAPI）→ db（PostgreSQL 15）
```

- ホスト側に公開するのは画面の 8090 番だけです（`127.0.0.1` のみ）。API と DB はコンテナ内に閉じています。
- 現行の構成（[docker/docker-compose.yml](../docker/docker-compose.yml)）とは、プロジェクト名もボリュームも別です。
  同時に起動しても、既存のデータには触りません。

## データの再生成

```bash
cd tools/baseball_score_v2
python demo/generate_demo_data.py     # demo/seed.sql と demo/logs/run_history.jsonl を更新する
```

[generate_demo_data.py](generate_demo_data.py) の `SEED` を変えると、別の成績になります。
`tests/test_demo_data.py` が、生成結果と `seed.sql` の一致、および成績の整合性（安打 ≤ 打数、失点の合計 = 相手の得点、など）を確認します。

## スクリーンショットと画面録画

```bash
pip install playwright && playwright install chromium
python demo/capture_demo.py ../../docs/images    # PNG 5 枚と demo.webm
```

リポジトリの [docs/images/](../../../docs/images/) には PNG だけを置いています。録画（webm）は容量が大きいため、リポジトリには含めていません。

## 注意

- **認証がありません。** ローカルの確認専用です。インターネットに公開するホストでは起動しないでください。
- 8090 番が使用中の場合は、`docker-compose.yml` の `ports` を変更してください。
