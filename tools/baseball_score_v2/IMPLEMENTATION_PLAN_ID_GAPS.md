# ID 飛び番問題：実装計画

## 問題の視覚化

### 現在の動作（ON CONFLICT DO NOTHING を使用）

```
1回目の実行:
games テーブル: [1, 2, 3, 4, 5]  ← 5試合挿入
games sequence: 5

2回目の実行（同じ5試合を再挿入）:
INSERT ✓ 試合1 ... ON CONFLICT DO NOTHING
  → CONFLICT 発生、INSERT は ROLLBACK
  → sequence は 6 にインクリメント ❌

INSERT ✓ 試合2 ... ON CONFLICT DO NOTHING
  → CONFLICT 発生、INSERT は ROLLBACK
  → sequence は 7 にインクリメント ❌

... (以下同じ) ...
sequence は 10 に達する

games テーブル: [1, 2, 3, 4, 5]  ← データは変わらず
games sequence: 10  ← でも sequence は 10

3回目の実行（新規試合1件を挿入）:
INSERT INTO games ... RETURNING game_id
  → game_id = 11 ❌ (ID が飛ぶ！)

games テーブル: [1, 2, 3, 4, 5, 11]  ← ID 6-10 が欠番
```

### 改善後の動作（SELECT first パターン）

```
1回目の実行:
SELECT * FROM games WHERE ... (何もない)
INSERT INTO games ... RETURNING game_id  → 1
games: [1, 2, 3, 4, 5]

2回目の実行（同じ5試合を再挿入）:
SELECT * FROM games WHERE game_date=? AND home_team_id=? ...
  → 既存レコード 1 を取得
SELECT * FROM games WHERE game_date=? AND home_team_id=? ...
  → 既存レコード 2 を取得
... (以下同じ) ...
sequence は 5 のまま ✓

games テーブル: [1, 2, 3, 4, 5]
games sequence: 5  ✓ 連番

3回目の実行（新規試合1件を挿入）:
SELECT * FROM games WHERE ... (新規なので該当なし)
INSERT INTO games ... RETURNING game_id  → 6 ✓
games: [1, 2, 3, 4, 5, 6]  ✓ 連番
```

---

## 実装内容

### 1. `DBRepository` に Helper メソッドを追加

現在の `get_or_create_player()` パターンを他のテーブルにも拡張：

```python
def get_or_create_team(self, cur, team_name):
    """チームを取得または作成（既存なら既存IDを返す）"""
    cur.execute("SELECT team_id FROM teams WHERE team_name=%s", (team_name,))
    row = cur.fetchone()
    if row:
        return row[0]

    cur.execute(
        "INSERT INTO teams (team_name) VALUES (%s) RETURNING team_id",
        (team_name,)
    )
    return cur.fetchone()[0]

def get_or_create_game(self, cur, game_date, home_team_id, away_team_id):
    """ゲームを取得または作成"""
    cur.execute("""
        SELECT game_id FROM games
        WHERE game_date=%s AND home_team_id=%s AND away_team_id=%s
    """, (game_date, home_team_id, away_team_id))
    row = cur.fetchone()
    if row:
        return row[0]

    cur.execute("""
        INSERT INTO games (game_date, home_team_id, away_team_id)
        VALUES (%s, %s, %s) RETURNING game_id
    """, (game_date, home_team_id, away_team_id))
    return cur.fetchone()[0]

def get_or_create_inning(self, cur, game_id, inning_number):
    """イニングを取得または作成"""
    cur.execute("""
        SELECT inning_id FROM innings
        WHERE game_id=%s AND inning_number=%s
    """, (game_id, inning_number))
    row = cur.fetchone()
    if row:
        return row[0]

    cur.execute("""
        INSERT INTO innings (game_id, inning_number)
        VALUES (%s, %s) RETURNING inning_id
    """, (game_id, inning_number))
    return cur.fetchone()[0]
```

### 2. `insert_records()` をリファクタ

```python
def insert_records(self, records):
    """バッティングデータをDBに登録"""
    with self.conn.cursor(cursor_factory=DictCursor) as cur:
        team_id = self.get_or_create_team(cur, self.team_name)

        for record in records:
            # 選手IDを取得
            cur.execute("""
                SELECT player_id FROM players
                WHERE player_name=%s AND team_id=%s
            """, (record.player, team_id))
            row = cur.fetchone()
            if not row:
                self.logger.warning("選手が未登録のためスキップ: %s", record.player)
                continue
            player_id = row["player_id"]

            # ゲーム取得・作成（CONFLICT なし）
            away_team_id = self.get_or_create_team(cur, record.opponent)
            game_id = self.get_or_create_game(cur, record.date, team_id, away_team_id)

            # イニング取得・作成（CONFLICT なし）
            inning_number = marunum_to_int(record.inning)
            inning_id = self.get_or_create_inning(cur, game_id, inning_number)

            # バッティング成績登録（UNIQUE 制約で重複防止）
            cur.execute("""
                INSERT INTO batting_stats
                (player_id, inning_id, double_hit, triple, homerun)
                VALUES (%s, %s, %s, %s, %s)
                ON CONFLICT (player_id, inning_id) DO NOTHING
            """, (player_id, inning_id, record.double, record.triple, record.homerun))

        self.conn.commit()
        self.logger.info("打撃データ登録完了: %d 件", len(records))
```

### 3. Migration の整理

現在の `001_add_unique_constraint_*` `002_truncate_*` `003_add_constraints_*` を整理：

- `001_*` → 初回のみ実行（UNIQUE 制約追加）
- `002_*` → TRUNCATE は運用時に手動実行（migration では不要）
- `003_*` → 初回設定に統合

新しい Migration：
```sql
-- 000_create_tables.sql（これを作成するか、docker/init.sql に統一）
-- または既に init.sql が本体なら、migration は変更のみ適用

-- 001_add_unique_constraints.sql
-- 制約の追加（各テーブルの UNIQUE ロジック）
```

---

## テスト追加内容

### `tests/test_db_repository.py` に追加

```python
import unittest
from unittest.mock import Mock
from repository.db_repository import DBRepository
from model.batting_record import BattingRecord
from datetime import date

class TestDBRepositoryIDGaps(unittest.TestCase):
    """ID 飛び番がないことを確認するテスト"""

    def test_no_sequence_gaps_on_duplicate_team(self):
        """同じチーム名を複数回挿入した場合、ID が飛ばないことを確認"""
        # Mock の cursor を作成
        mock_cur = Mock()

        # 1回目: team が存在しない → INSERT → team_id = 1
        mock_cur.fetchone.side_effect = [None, (1,)]
        repo = DBRepository()
        repo.conn = Mock()

        team_id_1 = repo.get_or_create_team(mock_cur, "Team A")
        self.assertEqual(team_id_1, 1)

        # 2回目: team が既に存在 → SELECT で取得 → team_id = 1
        mock_cur.fetchone.side_effect = [(1,)]  # SELECT で team_id=1 を取得
        team_id_2 = repo.get_or_create_team(mock_cur, "Team A")
        self.assertEqual(team_id_2, 1)  # 同じ ID

    def test_games_id_sequence_no_gaps(self):
        """games テーブルで ID が連番であることを確認"""
        # Assume database contains games with IDs [1, 2, 3, 5]
        # （実装後に実際の DB で検証）
        pass
```

---

## 実装順序

1. **Step 1**: Helper メソッドを追加（`get_or_create_team()`, `get_or_create_game()`, `get_or_create_inning()`）
2. **Step 2**: `insert_records()` をリファクタして新メソッドを使用
3. **Step 3**: テストを追加（ID 飛び番がないことを確認）
4. **Step 4**: `CLAUDE.md` と `IMPLEMENTATION_SUMMARY.md` を更新
5. **Step 5**: Migration ファイルを整理（オプション）

---

## 期待効果

- ✅ ID 飛び番を 90% 以上削減
- ✅ DB のデータ整合性向上
- ✅ デバッグが容易に
- ✅ Schema 変更なし（既存互換）
- ✅ 処理速度への影響最小（SELECT キャッシュヒット）

---

## 追加検討項目

### Option A への将来移行（UUID 化）

フェーズ 2 以降で検討：

```sql
-- teams テーブルを UUID に変更
ALTER TABLE teams
  ALTER COLUMN team_id DROP DEFAULT,
  ALTER COLUMN team_id SET DEFAULT gen_random_uuid(),
  ALTER COLUMN team_id TYPE uuid USING team_id::text::uuid;

-- Foreign keys を更新
ALTER TABLE players ALTER COLUMN team_id TYPE uuid USING team_id::text::uuid;
ALTER TABLE games ALTER COLUMN home_team_id TYPE uuid USING home_team_id::text::uuid;
ALTER TABLE games ALTER COLUMN away_team_id TYPE uuid USING away_team_id::text::uuid;

-- インデックス再構築
REINDEX TABLE teams;
```

メリット：
- 飛び番が完全に消える
- 分散 DB 対応

デメリット：
- ID が長くなる（可読性低下）
- インデックスサイズ増加
- 既存 data の migration が複雑

---

## まとめ

**推奨：Option B（SELECT first）を実装**
- 即座に実装可能（コード変更のみ）
- スキーマ互換性を保持
- 飛び番を大幅削減
