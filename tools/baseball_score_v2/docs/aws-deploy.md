# AWS へのデータ登録（EC2 停止状態からの手順）

> **現状（2026-10-12 時点）**: 費用の関係で AWS 上の公開は停止中です。GitHub Actions の deploy も手動実行（`workflow_dispatch`）にしており、`main` への push では EC2 へデプロイしません。

## 前提

- EC2にはSSH接続できるキーペア（`.pem`ファイル）がある
- EC2上の `/srv/baseball/` にアプリが配置されている
- EC2上の `docker-compose.yml` にPostgreSQL + FastAPIが定義されている

---

## STEP 1: EC2を起動する

### AWSコンソールから起動する場合

1. AWSコンソール → EC2 → インスタンス
2. 対象インスタンスを選択 → 「インスタンスの状態」→「開始」

### AWS CLIから起動する場合

```bash
aws ec2 start-instances --instance-ids i-xxxxxxxxxxxxxxxxx
```

起動完了まで1〜2分かかります。

---

## STEP 2: SSH接続を確認する

```bash
ssh -i ~/.ssh/your-key.pem ec2-user@<EC2のElastic IP>
```

接続できたらEC2上でDockerが動いているか確認します。

```bash
cd /srv/baseball/docker
docker compose ps
```

`db` と `backend` の State が `running` になっていればOKです。
停止していた場合は起動します。

```bash
docker compose up -d
```

---

## STEP 3: ExcelファイルをEC2へ転送する

ローカルPCのターミナルで実行します（EC2ではなくローカルで実行）。

```bash
# ローカルPCで実行
scp -i ~/.ssh/your-key.pem \
  "/path/to/実績データ.xlsx" \
  ec2-user@<EC2のElastic IP>:/srv/baseball/
```

> ファイルパスにスペースが含まれる場合はダブルクォートで囲んでください。

---

## STEP 4: EC2上のconfig.jsonを確認する

SSH接続したEC2上で確認します。

```bash
cat /srv/baseball/tools/baseball_score_v2/config.json
```

`excel_file` のパスがSTEP 3で転送したファイルのパスになっているか確認します。
異なる場合は修正します。

```bash
# viエディタで編集する場合
vi /srv/baseball/tools/baseball_score_v2/config.json
```

```json
{
  "excel_file": "/srv/baseball/実績データ.xlsx",
  "sheet_name": "データ入力シート(自チーム攻撃)",
  "pitcher_sheet_name": "データ入力シート(相手攻撃)"
}
```

---

## STEP 5: import_db.py を実行してデータを登録する

EC2上で実行します。

```bash
cd /srv/baseball/tools/baseball_score_v2
export $(grep -v '^#' /srv/baseball/docker/.env | xargs)
export DB_HOST=localhost
export DB_PORT=5433
python3.11 import_db.py
```

> **`DB_HOST` と `DB_PORT` を上書きする理由**:
> `docker/.env` の `DB_HOST=db` はDocker Compose内部のホスト名です。
> EC2上で直接スクリプトを実行する場合、Dockerの外からDBに接続するため
> `DB_HOST=localhost`（同じEC2内）・`DB_PORT=5433`（ホスト側のマッピングポート）に上書きする必要があります。

実行すると以下の順番でデータが登録されます。

1. 打撃成績をDBに登録
2. 投手成績をDBに登録
3. チーム成績（試合一覧）をDBに登録

成功すると `チーム成績取込完了: 更新 X 件、新規挿入 X 件` のようなメッセージが表示されます。

---

## STEP 6: 動作確認（任意）

バックエンドAPIにリクエストして、データが入っているか確認します。

```bash
# EC2上で実行（localhost経由でAPIを確認）
curl http://localhost:8000/api/stats/season?year=2025
```

---

## STEP 7: EC2を停止する

作業が終わったらEC2を停止してコストを抑えます。

### AWSコンソールから停止する場合

EC2 → インスタンス → 「インスタンスの状態」→「停止」

### AWS CLIから停止する場合

```bash
aws ec2 stop-instances --instance-ids i-xxxxxxxxxxxxxxxxx
```

> **注意**: EBSストレージは停止中も課金されます（約$2.88/月）。データを完全に削除したい場合のみ「終了（削除）」を選択してください。

---

## まとめ

| STEP | 作業場所 | 内容 |
|------|---------|------|
| STEP 1 | AWSコンソール or CLI | EC2を起動 |
| STEP 2 | ローカルPCのターミナル | SSH接続・Docker起動確認 |
| STEP 3 | ローカルPCのターミナル | ExcelファイルをSCPで転送 |
| STEP 4 | EC2上（SSH接続中） | config.jsonのパスを確認・修正 |
| STEP 5 | EC2上（SSH接続中） | `python import_db.py` を実行 |
| STEP 6 | EC2上（SSH接続中） | API動作確認（任意） |
| STEP 7 | AWSコンソール or CLI | EC2を停止 |
