# ADR-0003: Google OAuth と許可メールリストで認証する

- ステータス: 採用済み
- 決定時期: 2026-03-30（公開対応 STEP 1 完了）
- 関連: [ADR-0001](0001-vue3-spa-frontend.md)、`docs/plan/public_release_plan.md` 1-1

## 背景

成績は選手個人の記録なので、チームメンバー以外に公開できない。
AWS 上に Web アプリを公開するにあたり、API の全エンドポイントを保護する必要があった。

## 決定

**Google アカウントでログインし、許可したメールアドレスの利用者だけを通す。**

1. フロントエンドが Google Sign-In で `id_token` を取得し、`Authorization: Bearer` で API に送る。
2. バックエンドの `webapp/backend/auth.py` の `verify_token()` が、`google-auth` で署名・クライアント ID を検証する。
3. 環境変数 `ALLOWED_EMAILS`（カンマ区切り）に含まれるメールアドレスだけを許可し、含まれない場合は 403 を返す。
4. すべてのルーターに `APIRouter(dependencies=[Depends(verify_token)])` を付けて一括で保護する。

## 理由

`docs/plan/public_release_plan.md` に残っている理由は次のとおりである。

- チームメンバーは Google アカウントを持っている前提が成立しやすい。
- パスワードの保管・再設定を自前で持たなくてよい。
- 実装コストが低い。

## 結果

- 利用者の追加・削除は `ALLOWED_EMAILS` の変更とバックエンドの再起動で行う（ユーザー管理画面は無い）。
- **`ALLOWED_EMAILS` が未設定（空）のときはメールによる認可を行わず、Google アカウントを持つ全員が通る。**
  本番では必ず設定すること（`docker/.env.example` を参照）。未設定時に拒否へ倒す変更は未実施。
- 認証は「誰でもログインできる Google アカウント」+「許可リスト」の 2 段であり、
  ロール（閲覧のみ・編集可など）の区別は無い。すべての利用者が全データを閲覧できる。
- API は読み取り専用（GET のみ）で、書き込みは CLI から行う。そのため認可の粒度は現状の許可リストで足りている。
