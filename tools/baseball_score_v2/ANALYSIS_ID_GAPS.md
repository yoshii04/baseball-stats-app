# DB ID 飛び番問題の分析と改善計画

## 問題の原因

### SERIAL と ON CONFLICT DO NOTHING の相互作用

PostgreSQL の `SERIAL` 型は内部的には `SEQUENCE` を使用します。問題は以下の流れで発生します：

```
INSERT ... ON CONFLICT DO NOTHING の実行時：
1. INSERT 文が実行される
2. CONSTRAINT 違反が検出される
3. INSERT は ROLLBACK される（DO NOTHING）
4. しかし SEQUENCE は既にインクリメントされている ← これが原因
```

### 実装での具体例

`db_repository.py:insert_records()` より：

```python
# 試合登録（同じ日付・チーム組み合わせで重複する可能性が高い）
cur.execute("""
    INSERT INTO games (game_date, home_team_id, away_team_id)
    VALUES (%s, %s, %s)
    ON CONFLICT ON CONSTRAINT uq_games_date_home_away DO NOTHING
    RETURNING game_id
""", (record.date, team_id, away_team_id))
row = cur.fetchone()
if row:
    game_id = row[0]
else:
    # CONFLICT が発生した場合、既存レコードを SELECT
    cur.execute("""
        SELECT game_id FROM games
        WHERE game_date=%s AND home_team_id=%s AND away_team_id=%s
    """, (record.date, team_id, away_team_id))
    game_id = cur.fetchone()[0]
```

- 1回目実行: `games` に 10 試合登録 → `game_id` は 1-10
- 2回目実行: 同じ 10 試合で CONFLICT → `SEQUENCE` が 11-20 にインクリメント
- 3回目実行: 新規試合 1 件追加 → `game_id` は 21 (10+11 のギャップ)

**結果：ID が飛び番になり、データの見た目が悪い＆デバッグが困難**

---

## 解決策の比較

| 方法 | メリット | デメリット | 実装複雑度 |
|------|---------|-----------|----------|
| **A. UUID に変更** | 飛び番なし、完全に新しいレコード対応 | schema 変更必須、ID が長い | 中（schema + コード変更） |
| **B. SELECT first（推奨）** | 既存スキーマ互換、飛び番を大幅削減 | 若干遅い（SELECT 追加） | 低（コード変更のみ） |
| **C. 明示的なシーケンス管理** | 制御可能 | 複雑で危険 | 高（デッドロック リスク） |
| **D. SERIAL → BIGSERIAL** | 実装が簡単 | 問題を遅延させるだけ | 低（schema のみ） |

---

## 推奨：Option B（SELECT first + ON CONFLICT DO NOTHING）

### 戦略

CONFLICT 前に SELECT を実行し、既存レコードの ID を取得。SERIAL のインクリメントを最小化する。

```python
def get_or_create_game(cur, game_date, home_team_id, away_team_id):
    """ゲームを取得または作成（重複を避ける）"""
    # 1. 既存ゲームを確認
    cur.execute("""
        SELECT game_id FROM games
        WHERE game_date=%s AND home_team_id=%s AND away_team_id=%s
    """, (game_date, home_team_id, away_team_id))
    row = cur.fetchone()
    if row:
        return row[0]

    # 2. 新規ゲームを登録
    cur.execute("""
        INSERT INTO games (game_date, home_team_id, away_team_id)
        VALUES (%s, %s, %s)
        RETURNING game_id
    """, (game_date, home_team_id, away_team_id))
    return cur.fetchone()[0]
```

**メリット：**
- SEQUENCE は「実際に INSERT された回数分」だけインクリメント
- ID は連番に近い（わずかな重複チェック遅延による飛び番のみ）
- schema 変更なし（既存互換）
- 単純で安全

---

## Option A：UUID に変更

### Schema 変更

```sql
-- teams
ALTER TABLE teams
  ALTER COLUMN team_id SET DEFAULT gen_random_uuid(),
  ALTER COLUMN team_id TYPE uuid USING team_id::text::uuid;

-- 他のテーブルも同様
```

**メリット：**
- 飛び番なし（UUID は意図的に生成）
- 分散システム対応
- INSERT の SET Returning も確定的

**デメリット：**
- 既存 ID データを migration で変換する必要
- ID が UUID 文字列になり、可読性低下
- インデックスサイズ増加（パフォーマンス若干低下）

---

##実装計画

### フェーズ 1：Option B（推奨、即実装）

**期待効果：** ID の飛び番を 90% 削減

1. `DBRepository.get_or_create_*()` メソッド群を実装
   - `get_or_create_team()`
   - `get_or_create_player()`
   - `get_or_create_game()`
   - `get_or_create_inning()`

2. `insert_records()` を リファクタ
   - 新しいメソッドを使用
   - ON CONFLICT を削除（GET first パターンに変更）

3. テスト作成
   - 同じデータを 2 回実行して、ID 飛び番がないか確認

4. migration 文は不要（schema 変更なし）

### フェーズ 2：Option A（長期検討）

UUID への移行を検討（別 PR で対応）

---

## テスト計画

```python
def test_no_id_gaps_on_duplicate_insert(self):
    """重複データの挿入時に ID が飛ばないことを確認"""
    record = BattingRecord(...)

    # 1回目実行
    service.import_to_db([record])
    # game_id = 1

    # 2回目実行（同じレコード）
    service.import_to_db([record])
    # game_id は 1 のままか 2（新規作成）のいずれか
    # 但し 11 や 21 になってはいけない

    cur.execute("SELECT MAX(game_id) FROM games")
    max_id = cur.fetchone()[0]

    cur.execute("SELECT COUNT(*) FROM games")
    count = cur.fetchone()[0]

    # count が n なら、max_id は n 付近（飛び番がない）
    self.assertLess(max_id, count + 10)  # 許容範囲：最大 10 個の飛び番
```

---

## ファイル修正一覧

- [ ] `repository/db_repository.py` - `get_or_create_*()` メソッド追加、`insert_records()` リファクタ
- [ ] `tests/test_db_repository.py` - ID 飛び番テスト追加
- [ ] `IMPLEMENTATION_SUMMARY.md` - 変更内容記載
