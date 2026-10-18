# 公開対応 改修計画 — Baseball Score v2

作成日: 2026-03-27
対象ブランチ: feature-func-score_v50

## 前提条件

- **公開範囲**: チーム内限定（ログイン必須）
- **インフラ**: クラウドマネージド（GCP / AWS / Azure）

---

## 調査で判明した問題点

| 重大度 | 問題点 | 該当箇所 |
|---|---|---|
| 🔴 Critical | 認証ゼロ — 全APIが誰でもアクセス可能 | `webapp/backend/routers/*.py` 全エンドポイント |
| 🔴 Critical | シークレット管理が `secrets.json` ファイル依存 | `config/config.py:8-20` |
| 🔴 Critical | HTTPS 未対応（TLS終端なし） | `docker/docker-compose.yml` |
| 🟠 High | CORS が `localhost:5173` のみ | `webapp/backend/main.py:22-30` |
| 🟠 High | DB パスワードがデフォルト値（`postgres`） | `docker/docker-compose.yml:7` |
| 🟠 High | DB SSL 無効（`sslmode="disable"`） | `webapp/backend/database.py:23` |
| 🟠 High | フロントエンドの本番配信未整備（Nginx なし） | `webapp/frontend/` |
| 🟠 Medium | セキュリティヘッダーなし | `webapp/backend/main.py` |
| 🟠 Medium | レートリミットなし | 全エンドポイント |
| 🟠 Medium | Dockerfile が root ユーザーで起動 | `webapp/backend/Dockerfile:20` |
| 🟡 Low | ヘルスチェックが DB 接続確認なし | `docker/docker-compose.yml:39-43` |
| 🟡 Low | 依存ライブラリのバージョン上限未指定 | `webapp/backend/requirements.txt` |

> SQL インジェクション対策（パラメータ化クエリ）は全エンドポイントで実装済み。問題なし。

---

## クラウド費用比較（月額目安）

> **前提条件**: チーム内 20名以下、リクエスト数 100〜500件/日 程度の軽量トラフィック。東京リージョン基準。2026年3月時点の公開料金。

### サービス別費用内訳

| サービス種別 | GCP | AWS（標準） | AWS（最小構成） | Azure | Render.com |
|---|---|---|---|---|---|
| **フロントエンド配信** | Cloud Storage<br>~$0/月 | S3<br>~$0/月 | S3<br>~$0/月 | Static Web Apps (Free)<br>$0/月 | Static Site (Free)<br>$0/月 |
| **CDN** | Cloud CDN<br>~$1/月 | CloudFront<br>**$0/月** ※A | CloudFront<br>**$0/月** ※A | Azure CDN<br>~$1/月 | 込み |
| **バックエンド** | Cloud Run<br>**~$0/月** ※1 | App Runner<br>~$3.30/月 ※2 | EC2 t3.micro<br>**$0/月**（初年度）<br>$7.75/月（2年目〜）※B | Container Apps<br>**~$0/月** ※3 | Web Service (Starter)<br>$7/月 |
| **データベース** | Cloud SQL<br>(db-f1-micro, 10GB)<br>~$10/月 | RDS PostgreSQL<br>(db.t4g.micro, 20GB)<br>~$12/月 ※C | RDS PostgreSQL<br>(db.t4g.micro)<br>**$0/月**（初年度）<br>$12/月（2年目〜）※D | Azure DB for PostgreSQL<br>(Flexible B1ms, 32GB)<br>~$16/月 | PostgreSQL (Starter)<br>$7/月 |
| **HTTPS / ロードバランサー** | Cloud Run に自動含む<br>$0/月 | ACM 無料<br>(ALB 不要 ※2) | ACM 無料 | 自動マネージド証明書<br>$0/月 | 自動含む<br>$0/月 |
| **シークレット管理** | Secret Manager<br>~$0/月 ※4 | SSM Parameter Store<br>+ KMS<br>~$1/月 ※E | SSM Parameter Store<br>+ KMS<br>~$1/月 ※E | Key Vault<br>~$0/月 | 環境変数のみ<br>$0/月 |
| **コンテナレジストリ** | Artifact Registry<br>~$0/月 ※6 | ECR<br>~$0.04/月 | ECR<br>**$0/月**（初年度）<br>~$0.04/月（2年目〜） | Container Registry (Basic)<br>~$5/月 | 不要 (Git 連携) |
| **DNS** | Cloud DNS<br>~$0.50/月 | Route 53<br>~$0.50/月 | Route 53<br>~$0.50/月 | Azure DNS<br>~$0.50/月 | 込み |
| **月額合計（目安）** | **$11〜15/月** | **$17〜18/月** ※F | **初年度: $1〜2/月**<br>**2年目〜: $21〜22/月** | **$22〜27/月** | **$14/月** |
| **円換算（1USD=150円）** | **約1,650〜2,250円** | **約2,550〜2,700円** | **初年度: 約150〜300円**<br>**2年目〜: 約3,150〜3,300円** | **約3,300〜4,050円** | **約2,100円** |

### 注釈

- ※1 **Cloud Run**: 月200万リクエスト・36万vCPU秒・18万GB秒が無料枠。100〜500件/日では無料枠内に収まる
- ※2 **App Runner (東京)**: バックエンドの最安マネージドコンテナ。アイドル時 $0.009/GB-時のみ課金。0.5GB × $0.009 × 730時間 = $3.29/月。リクエスト処理時間はごくわずかで事実上アイドル代のみ
- ※3 **Container Apps**: 月18万vCPU秒・36万GB秒が無料枠。軽量トラフィックでは無料枠内
- ※4 **Secret Manager**: 最初の6シークレットは無料
- ※6 **Artifact Registry**: 0.5GB/月まで無料。Dockerイメージ1本なら概ね無料枠内
- ※A **CloudFront**: 月1TB + 1,000万リクエストまで**常時無料**（12ヶ月制限なし。2021年12月以降の変更）。20名規模では超過しない
- ※B **EC2 t3.micro**: 初回サインアップから**12ヶ月間・750時間/月**が無料。2年目以降は $0.0106/時 × 730時間 = $7.75/月
- ※C **RDS db.t4g.micro**: db.t3.micro ($0.022/時) より安い Graviton2 世代。$0.016/時 × 730時間 = $11.68/月 + ストレージ
- ※D **RDS 無料枠**: 初回サインアップから**12ヶ月間・750時間/月**が無料（db.t3.micro / db.t4g.micro 対象、20GB ストレージ込み）
- ※E **SSM Parameter Store + KMS**: Secrets Manager ($0.40/シークレット × 6 = $2.40/月) の代替。KMS キー $1.00/月 + Parameter Store SecureString $0.05/パラメータ × 6 = $0.30 → 合計 $1.30/月。Secrets Manager より $1.10/月安い
- ※F **AWS 標準**: 当初見積もり ($24〜28/月) から以下の最適化で削減: ① db.t4g.micro 採用 (-$6)、② CloudFront 常時無料枠確認 (-$1)、③ Secrets Manager → SSM Parameter Store 変更 (-$1.10)

### AWS 最小構成の詳細（無料枠終了後・常時稼働）

| サービス | 月額 | 備考 |
|---|---|---|
| EC2 t3.micro（バックエンド） | $7.75/月 | $0.0116/時 × 730時間 |
| EBS 20GB gp3（EC2 ストレージ） | $1.92/月 | 停止中も常時課金 |
| RDS db.t4g.micro（DB） | $11.68/月 | $0.016/時 × 730時間 |
| RDS ストレージ 20GB（DB） | $2.30/月 | 停止中も常時課金 |
| S3（フロントエンド） | ~$0/月 | |
| CloudFront（CDN） | $0/月 | 常時無料 1TB/月 |
| ECR（コンテナ） | ~$0.04/月 | |
| SSM Parameter Store + KMS | $1.30/月 | |
| Route 53（DNS） | $0.50/月 | |
| **合計** | **$25〜26/月** | |

---

### AWS 学習用構成（1日2時間稼働・無料枠なし）

> 学習目的で使うときだけ起動し、1日2時間程度のみ稼働させる場合の費用。
> **稼働: 2時間/日 × 30日 = 60時間/月　停止: 670時間/月**

#### 構成A — EC2 + RDS を別々に使う（現状アーキテクチャに近い）

| サービス | 計算内訳 | 月額 |
|---|---|---|
| EC2 t3.micro（実行中のみ） | 60時間 × $0.0116/時 | $0.70 |
| EBS 20GB gp3（EC2 ストレージ） | **停止中も課金** $0.096 × 20GB | **$1.92** |
| RDS db.t4g.micro（実行中のみ） | 60時間 × $0.016/時 | $0.96 |
| RDS ストレージ 20GB | **停止中も課金** $0.115 × 20GB | **$2.30** |
| CloudFront（CDN） | 常時無料 | $0 |
| S3（フロントエンド） | 100MB 程度 | ~$0 |
| ECR（コンテナ） | 無料枠超過分 | ~$0.04 |
| SSM Parameter Store + KMS | KMS キーは**常時課金** | $1.00 |
| Route 53 | ホストゾーン | $0.50 |
| **月額合計** | | **~$7.42/月（約1,110円）** |

> ⚠️ **RDS の注意点**: AWS は停止中の RDS を **7日後に自動再起動**する。学習のため止めていても週1回手動で再停止が必要。

#### 構成B — EC2 のみ（PostgreSQL を EC2 内で動かす、学習用に最もシンプル）

| サービス | 計算内訳 | 月額 |
|---|---|---|
| EC2 t3.micro（実行中のみ） | 60時間 × $0.0116/時 | $0.70 |
| EBS 30GB gp3（OS + DB 込み） | **停止中も課金** $0.096 × 30GB | **$2.88** |
| CloudFront（CDN） | 常時無料 | $0 |
| S3（フロントエンド） | 100MB 程度 | ~$0 |
| ECR（コンテナ） | ~$0.04 | ~$0.04 |
| **月額合計** | | **~$3.62/月（約543円）** |

> - RDS を使わず PostgreSQL を EC2 内で Docker Compose で起動するため RDS 費用ゼロ
> - KMS・Route 53 も学習目的なら不要（EC2 のパブリック IP で直接アクセス可）
> - 停止時は EC2 を止めるだけで済み、管理がシンプル
> - **学習目的にはこの構成を推奨**

#### 停止・起動のポイント

| サービス | 停止操作 | 停止中の課金 |
|---|---|---|
| EC2 | コンソール or CLI で停止 | EBS ストレージのみ課金 |
| RDS | コンソール or CLI で停止 | ストレージのみ課金（7日後自動再起動に注意） |
| CloudFront | 停止不要（常時無料） | — |
| S3 | 停止不要（ファイルが存在しない限りほぼ $0） | — |

**学習効率を上げるワンライナー（EC2 起動/停止）:**

```bash
# 起動
aws ec2 start-instances --instance-ids i-xxxxxxxxxxxxxxxxx

# 停止
aws ec2 stop-instances --instance-ids i-xxxxxxxxxxxxxxxxx

# RDS も止める場合
aws rds stop-db-instance --db-instance-identifier baseball-db
```

### スケール時の費用変化（参考）

| 想定ユーザー数 | GCP | AWS（標準） | Azure |
|---|---|---|---|
| 〜20名（現状） | $11〜15/月 | $17〜18/月 | $22〜27/月 |
| 〜100名 | $15〜25/月 | $25〜35/月 | $25〜35/月 |
| 〜500名 | $30〜50/月 | $50〜80/月 | $45〜70/月 |

> 500名規模では Cloud SQL や RDS のスペックアップが主な費用増加要因となる

### 選定ポイントまとめ

| 観点 | 推奨 | 理由 |
|---|---|---|
| **コスト最小（通常）** | GCP | Cloud Run の無料枠が大きく、小規模では DB 費用のみ |
| **コスト最小（初年度のみ）** | AWS | 無料枠を活用すれば初年度はほぼ $0 |
| **シンプルさ** | Render.com | Git push で自動デプロイ、設定最小。ただし高度な制御は不可 |
| **Google Workspace との連携** | GCP | Google OAuth / IAP との親和性が高く、認証設定が容易 |
| **既存 AWS 環境がある場合** | AWS | 既存 VPC / IAM と統合しやすい |
| **既存 Microsoft 環境がある場合** | Azure | Azure AD (Entra ID) と OAuth を容易に連携可能 |

---

## 推奨インフラ構成（AWS 学習用構成B）

> **方針**: EC2 t3.micro 1台に PostgreSQL + FastAPI を Docker Compose でまとめて起動。
> RDS・SSM・Route 53 は使用せず、学習目的に最もシンプルな構成を採用。

```
Internet (HTTPS)
    │
    ├── S3 + CloudFront  ← フロントエンド (dist/ 静的配信 / HTTPS自動)
    │
    └── EC2 t3.micro (Elastic IP + Nginx + Let's Encrypt)
            │
            ├── Nginx (SSL終端 / リバースプロキシ → port 8000)
            └── Docker Compose
                    ├── FastAPI コンテナ (port 8000)
                    └── PostgreSQL コンテナ (port 5432)

シークレット: EC2 上の /srv/baseball/.env ファイル（chmod 600）
```

### サービスと費用（60時間/月稼働）

| サービス | 月額 | 備考 |
|---|---|---|
| EC2 t3.micro | $0.70/月 | 停止時は EBS のみ課金 |
| EBS 30GB gp3 | $2.88/月 | OS + DB 込み、停止中も課金 |
| S3 + CloudFront | ~$0/月 | CloudFront は常時無料枠内 |
| ECR | ~$0.04/月 | 任意（EC2 直接 build でも可） |
| **合計** | **~$3.62/月（約543円）** | |

### 各 AWS サービスの役割

| サービス | 用途 |
|---|---|
| EC2 t3.micro | バックエンド (FastAPI) + DB (PostgreSQL) を Docker Compose で起動 |
| Elastic IP | 固定パブリック IP（無料。EC2 停止中のみ課金: $0.005/時） |
| S3 | フロントエンド静的ファイル配信 |
| CloudFront | S3 への HTTPS CDN（常時無料枠：1TB/月・1000万req） |
| ECR | Docker イメージ保存（任意。EC2 で直接 build する場合は不要） |
| Let's Encrypt + Certbot | バックエンドの無料 HTTPS 証明書（Nginx 経由） |

> **GCP との対応表（参考）**
> Cloud Run → EC2 + Nginx、Cloud SQL → Docker Compose PostgreSQL、
> Secret Manager → `.env` ファイル、Cloud Load Balancing → Nginx + Let's Encrypt、
> Cloud Storage + CDN → S3 + CloudFront

---

## STEP 1 — 公開最低条件（必須）✅ 完了（2026-03-30）

### 1-1. 認証機構の実装（Google OAuth）✅ 完了

チームメンバーは Google アカウントを持つ前提が成立しやすく、パスワード管理不要で実装コストが低い。

#### バックエンド

**新規作成: `webapp/backend/auth.py`**

- `google-auth` ライブラリで Google 発行の `id_token` を検証
- 環境変数 `ALLOWED_EMAILS`（カンマ区切り）と照合して認可
- `verify_token()` を FastAPI の `Depends()` として提供

```python
# 設計イメージ
from fastapi import Depends, HTTPException
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from google.oauth2 import id_token
from google.auth.transport import requests as grequests
import os

security = HTTPBearer()
ALLOWED_EMAILS = set(os.environ.get("ALLOWED_EMAILS", "").split(","))
GOOGLE_CLIENT_ID = os.environ["GOOGLE_CLIENT_ID"]

def verify_token(credentials: HTTPAuthorizationCredentials = Depends(security)):
    try:
        idinfo = id_token.verify_oauth2_token(
            credentials.credentials, grequests.Request(), GOOGLE_CLIENT_ID
        )
        email = idinfo.get("email")
        if ALLOWED_EMAILS and email not in ALLOWED_EMAILS:
            raise HTTPException(status_code=403, detail="アクセス権限がありません")
        return idinfo
    except ValueError:
        raise HTTPException(status_code=401, detail="無効なトークンです")
```

**変更: `webapp/backend/routers/*.py`（全6ファイル）**

- `APIRouter(dependencies=[Depends(verify_token)])` でルーター全体を一括保護
- `/health` エンドポイントのみ認証対象外

**変更: `webapp/backend/requirements.txt`**

- `google-auth` を追加

#### フロントエンド

**新規作成: `webapp/frontend/src/views/LoginView.vue`**

- Google Sign-In（`gsi/client`）で `id_token` を取得
- 取得した `id_token` を `sessionStorage` に保存してダッシュボードへリダイレクト

**変更: `webapp/frontend/src/router/index.js`**

- 全既存ルートに `meta: { requiresAuth: true }` を追加
- `/login` ルートを追加
- `router.beforeEach` で未認証なら `/login` へリダイレクト

**変更: `webapp/frontend/src/api/index.js`**

- request インターセプター: `sessionStorage` の `id_token` を `Authorization: Bearer` に自動付与
- response インターセプター: 401 応答時に `sessionStorage` をクリアして `/login` へリダイレクト

---

### 1-2. シークレット管理の環境変数化 ✅ 完了

> **AWS 学習用構成B の方針**: SSM Parameter Store / Secrets Manager は使用しない。
> EC2 上の `/srv/baseball/.env` ファイル（`chmod 600`）で管理する。
> ローカル開発時は `docker/.env` ファイルを使用（Git に含めない）。

**変更: `config/config.py`**

- `secrets.json` の読み込み処理（1〜20行）を完全削除
- 全 DB 設定を `os.environ` から取得（未設定なら `KeyError` で起動失敗 = フェイルファスト）

```python
DB_CONFIG = {
    "host":     os.environ["DB_HOST"],
    "port":     int(os.environ.get("DB_PORT", "5432")),
    "user":     os.environ["DB_USER"],
    "password": os.environ["DB_PASSWORD"],
    "dbname":   os.environ["DB_NAME"],
}
TEAM_NAME = os.environ.get("TEAM_NAME", "Default Team")
```

**変更: `webapp/backend/database.py:23`**

- `sslmode="disable"` → `sslmode=os.environ.get("DB_SSLMODE", "disable")`
- EC2 内の Docker Compose では同一ホスト内通信のため `disable` のままで OK
- 外部 RDS を使う場合は `require` に変更

**変更: `docker/docker-compose.yml`**

- `POSTGRES_PASSWORD: postgres` → `${DB_PASSWORD}` 等に変更
- `secrets.json` のボリュームマウント（行33）を削除
- backend コンテナに DB 関連環境変数を追加

**新規作成: `docker/.env.example`**（`.env` 本体は `.gitignore` 対象）

```env
DB_HOST=db
DB_PORT=5432
DB_USER=postgres
DB_PASSWORD=changeme
DB_NAME=baseball
DB_SSLMODE=disable
TEAM_NAME=チーム名
GOOGLE_CLIENT_ID=xxx.apps.googleusercontent.com
ALLOWED_EMAILS=member1@example.com,member2@example.com
ALLOWED_ORIGINS=https://xxxxxxxx.cloudfront.net
```

**EC2 上での `.env` ファイル配置手順（デプロイ時）:**

```bash
# EC2 上で作成（一度だけ）
sudo mkdir -p /srv/baseball
sudo cp docker/.env.example /srv/baseball/.env
sudo chmod 600 /srv/baseball/.env
# vim 等で実際の値を編集
sudo vim /srv/baseball/.env

# docker compose 起動時に参照
cd /srv/baseball
docker compose --env-file /srv/baseball/.env up -d
```

---

### 1-3. CORS の本番対応 ✅ 完了

**変更: `webapp/backend/main.py:22-30`**

- `allow_origins` を環境変数 `ALLOWED_ORIGINS`（カンマ区切り）から取得
- デフォルト値を `http://localhost:5173` に設定（開発環境との後方互換性を維持）
- 本番では CloudFront の URL を設定（例: `https://xxxxxxxx.cloudfront.net`）

---

### 1-4. フロントエンド本番ビルド設定 ✅ 完了

**新規作成: `webapp/frontend/.env.production`**

```env
VITE_API_BASE_URL=https://<EC2のElasticIP or ドメイン>
```

> **AWS 学習用構成B の注意点**: バックエンドへのアクセスは EC2 の Elastic IP（または取得したドメイン）を直接指定。
> CloudFront は S3（フロントエンド）にのみ使用し、バックエンド API は EC2 の Nginx が HTTPS 終端する。

`src/api/index.js` はすでに `import.meta.env.VITE_API_BASE_URL ?? ''` を参照しているため、このファイル追加のみで対応完了。

---

### 1-5. クラウドインフラ構築（AWS 学習用構成B 手順）✅ 完了

#### フェーズ 1: EC2 セットアップ

```bash
# 1. EC2 t3.micro 起動（AMI: Amazon Linux 2023 推奨）
#    セキュリティグループ: SSH(22), HTTP(80), HTTPS(443), API(8000) を開放

# 2. Elastic IP を割り当て・関連付け（EC2 停止時もIPが変わらない）

# 3. EC2 に SSH 接続後、Docker + Docker Compose をインストール
sudo dnf update -y
sudo dnf install -y docker git
sudo systemctl enable --now docker
sudo usermod -aG docker ec2-user
# Docker Compose v2 は docker plugin として利用可能
docker compose version
```

#### フェーズ 2: Nginx + Let's Encrypt（HTTPS）

> ドメインがない場合は HTTP のみで学習開始も可。Google OAuth は HTTPS 必須のため、
> 本番運用にはドメイン取得（Route 53 or お名前.com）または Elastic IP でも設定可能。

```bash
# Nginx + Certbot インストール
sudo dnf install -y nginx python3-certbot-nginx

# Nginx リバースプロキシ設定（/etc/nginx/conf.d/baseball.conf）
# ドメインがある場合: certbot --nginx -d your-domain.example.com
# ドメインなし (自己署名): openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
#   -keyout /etc/ssl/private/baseball.key -out /etc/ssl/certs/baseball.crt

sudo systemctl enable --now nginx
```

**Nginx 設定例** (`/etc/nginx/conf.d/baseball.conf`):
```nginx
server {
    listen 443 ssl;
    server_name your-domain.example.com;  # または _ (IP直接アクセス)
    ssl_certificate /etc/ssl/certs/baseball.crt;  # Let's Encrypt または自己署名
    ssl_certificate_key /etc/ssl/private/baseball.key;

    location / {
        proxy_pass http://localhost:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
server {
    listen 80;
    return 301 https://$host$request_uri;
}
```

#### フェーズ 3: アプリのデプロイ

```bash
# EC2 上でリポジトリをクローン
cd /srv
sudo git clone <repo-url> baseball
sudo chown -R ec2-user:ec2-user baseball

# .env ファイルを配置
cp /srv/baseball/docker/.env.example /srv/baseball/docker/.env
chmod 600 /srv/baseball/docker/.env
# 実際の値を編集
vim /srv/baseball/docker/.env

# Docker Compose で起動（DB + バックエンド）
cd /srv/baseball/docker
docker compose up -d --build
```

#### フェーズ 4: フロントエンドを S3 + CloudFront で配信

```bash
# ローカルでビルド（VITE_API_BASE_URL に EC2 の HTTPS URL を設定）
cd webapp/frontend
echo "VITE_API_BASE_URL=https://<EC2-IP-or-domain>" > .env.production
npm run build

# S3 バケット作成（Static website hosting 有効化）
aws s3 mb s3://baseball-score-frontend --region ap-northeast-1
aws s3 website s3://baseball-score-frontend --index-document index.html --error-document index.html

# dist/ を S3 にアップロード
aws s3 sync dist/ s3://baseball-score-frontend --delete

# CloudFront ディストリビューション作成（AWS コンソール推奨）
# Origin: S3 バケット、Default Root Object: index.html
# → https://xxxxxxxx.cloudfront.net でアクセス可能になる

# ALLOWED_ORIGINS を CloudFront URL に更新して docker compose 再起動
```

#### EC2 停止・起動のワンライナー

```bash
# 停止（EBS 課金のみ。PostgreSQL データは保持される）
aws ec2 stop-instances --instance-ids i-xxxxxxxxxxxxxxxxx

# 起動
aws ec2 start-instances --instance-ids i-xxxxxxxxxxxxxxxxx

# アプリの再起動（EC2 再起動後 Docker が自動起動しない場合）
cd /srv/baseball/docker && docker compose up -d
```

---

### STEP 1 変更ファイル一覧

```
新規作成:
  webapp/backend/auth.py
  webapp/frontend/src/views/LoginView.vue
  webapp/frontend/.env.production
  docker/.env.example

変更:
  config/config.py                     secrets.json 読み込みを廃止 → 環境変数化
  webapp/backend/database.py           sslmode を環境変数化
  webapp/backend/main.py               CORS allow_origins を環境変数化
  webapp/backend/routers/players.py    認証 Depends 追加
  webapp/backend/routers/games.py      認証 Depends 追加
  webapp/backend/routers/stats.py      認証 Depends 追加
  webapp/backend/routers/analytics.py  認証 Depends 追加
  webapp/backend/routers/pitchers.py   認証 Depends 追加
  webapp/backend/routers/history.py    認証 Depends 追加
  webapp/backend/requirements.txt      google-auth 追加
  webapp/frontend/src/router/index.js  requiresAuth + beforeEach ガード
  webapp/frontend/src/api/index.js     インターセプター追加
  docker/docker-compose.yml            env vars 化、secrets.json マウント削除
```

---

### STEP 1 推奨実装順序（AWS 学習用構成B）

```
1. アプリコード修正（ローカルで動作確認しながら進める）
   ├── config/config.py + database.py 修正（シークレット環境変数化）
   │   └── docker compose で動作確認（docker/.env ファイルで開発環境を維持）
   ├── webapp/backend/auth.py 新規作成
   │   └── webapp/backend/routers/*.py に認証追加
   └── フロントエンド
       └── LoginView.vue 作成
       └── router/index.js にルートガード追加
       └── api/index.js にインターセプター追加

2. AWS インフラ構築（EC2）
   ├── EC2 t3.micro 起動 + Elastic IP 設定
   ├── Docker + Nginx インストール
   └── Let's Encrypt or 自己署名証明書でHTTPS設定（Nginx）

3. EC2 にアプリをデプロイ
   ├── git clone → /srv/baseball/.env 配置
   ├── docker compose up -d --build（DB + バックエンド）
   └── Nginx 動作確認（curl https://<EC2-IP>/api/players）

4. フロントエンドを S3 + CloudFront にデプロイ
   ├── .env.production に EC2 の HTTPS URL を設定
   ├── npm run build → aws s3 sync dist/ s3://...
   ├── CloudFront ディストリビューション作成
   └── ALLOWED_ORIGINS を CloudFront URL に更新して EC2 side 再起動

5. Google OAuth コンソールで Authorized origins / redirect URI を本番 URL に追加
   └── ブラウザで動作確認（ログイン → ダッシュボード表示）
```

---

## STEP 2 — 本番品質（公開後 1〜2週以内に推奨）

| # | 対象ファイル | 変更内容 | 状態 |
|---|---|---|---|
| 2-1 | `webapp/backend/main.py` | セキュリティヘッダーミドルウェア追加（X-Frame-Options, HSTS, X-Content-Type-Options, CSP） | 未着手 |
| 2-2 | `webapp/backend/main.py` | `slowapi` によるレートリミット（60req/min/IP）追加 | 未着手 |
| 2-3 | `webapp/backend/main.py` | 本番環境（`ENV=production`）で Swagger UI / ReDoc を無効化 | 未着手 |
| 2-4 | `webapp/backend/main.py` | `/health` エンドポイントを DB 接続確認付きに強化 | 未着手 |
| 2-5 | `webapp/backend/Dockerfile` | non-root ユーザー（`appuser`）での実行 | 未着手 |
| 2-6 | `webapp/backend/requirements.txt` | `>=` を `==` に変更してバージョン完全固定、`slowapi` 追加 | 未着手 |
| 2-7 | `.github/workflows/deploy.yml`（新規） | CI/CD パイプライン（テスト → Docker build → SSH で EC2 に `docker compose up --build`） | ✅ 完了（2026-04-01） |

> **2-7 実装メモ**: `main` push → unittest 自動実行 → 成功時のみ SSH で EC2 へ自動デプロイ。`DOCKER_BUILDKIT=0` で arm64/amd64 の buildx 問題を回避。PYTHONPATH と DB ダミー環境変数を CI に注入して utils モジュール解決を保証（v63〜v72 で対応完了）。

---

## STEP 3 — 長期整備（将来）

| 対象 | 変更内容 |
|---|---|
| `webapp/backend/` 全体 | `psycopg2` → SQLAlchemy (async) 移行（接続プール・コネクションリーク防止） |
| `docker/` | Alembic によるスキーママイグレーション管理 |
| インフラ | IAP（Identity-Aware Proxy）によるアプリ前段での二重認証 |
| インフラ | Cloud Armor による WAF・DDoS 対策 |
| インフラ | Cloud Monitoring / Logging によるアラート設定 |
| `webapp/frontend/` | Vitest / Vue Test Utils によるフロントエンドテスト追加 |

---

## 検証方法

> `<EC2_URL>` は EC2 の `https://<Elastic-IP-or-domain>` に置き換える。

```bash
# 認証なしで拒否されることを確認
curl -X GET <EC2_URL>/api/players
# → 401 Unauthorized

# 正規 id_token でアクセス可能なことを確認
curl -H "Authorization: Bearer <id_token>" <EC2_URL>/api/players
# → 200 OK

# 許可外メールのトークンで拒否されることを確認
# → 403 Forbidden

# ヘルスチェック（認証不要）
curl <EC2_URL>/health
# → {"status": "ok", "db": "connected"}

# セキュリティヘッダー確認（STEP 2 実装後）
curl -I <EC2_URL>/api/players
# → Strict-Transport-Security, X-Frame-Options 等を確認

# フロントエンド（CloudFront）
curl https://xxxxxxxx.cloudfront.net
# → 200 OK（index.html が返る）

# EC2 内 Docker Compose の状態確認
ssh ec2-user@<Elastic-IP> "cd /srv/baseball/docker && docker compose ps"
# → db, backend が Up 状態であることを確認

# 既存テストがすべてパスすることを確認（ローカル）
python -m unittest discover -s tests -p "test_*.py" -v
```
