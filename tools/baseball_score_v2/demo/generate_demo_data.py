"""デモ用の合成データ（架空のチーム・選手・試合）を生成する。

実データは一切使わない。乱数の種を固定しているため、何度実行しても同じ結果になる。

出力:
    demo/seed.sql                  DB の初期データ（teams / players / games / batting_stats / pitcher_stats）
    demo/logs/run_history.jsonl    「実行履歴」画面用のログ

使い方:
    cd tools/baseball_score_v2
    python demo/generate_demo_data.py
"""
import datetime
import json
import os
import random
from dataclasses import dataclass, field

SEED = 8
SEASON_START = datetime.date(2026, 3, 7)
SEASON_END = datetime.date(2026, 7, 12)

TEAM_NAME = "サンプル高校"
OPPONENTS = [
    "テスト高校", "デモ学園", "サンプル商業", "ダミー工業",
    "仮名高校", "例題学院", "試作高校", "模擬大付属",
]

# 姓（デモ・テスト・サンプル・ダミー・仮名）× 名（太郎・次郎・三郎）の 15 名。実在の人物とは無関係。
PLAYERS = [f"{family} {given}" for family in ("デモ", "テスト", "サンプル", "ダミー", "仮名")
           for given in ("太郎", "次郎", "三郎")]

# 打撃力（打席あたりの安打率の目安）。先頭 9 名が主力、後ろ 6 名は控え。
_HIT_RATE = [0.34, 0.31, 0.29, 0.33, 0.27, 0.26, 0.24, 0.22, 0.21,
             0.25, 0.23, 0.20, 0.22, 0.19, 0.18]
_LONG_HIT_SHARE = [0.30, 0.25, 0.20, 0.45, 0.35, 0.20, 0.15, 0.20, 0.10,
                   0.25, 0.20, 0.15, 0.10, 0.10, 0.05]
_WALK_RATE = [0.12, 0.10, 0.08, 0.11, 0.07, 0.06, 0.07, 0.05, 0.06,
              0.08, 0.06, 0.05, 0.05, 0.04, 0.04]
_SO_RATE = [0.14, 0.16, 0.18, 0.20, 0.22, 0.20, 0.24, 0.26, 0.27,
            0.20, 0.22, 0.25, 0.26, 0.28, 0.30]
_STEAL_RATE = [0.30, 0.20, 0.05, 0.02, 0.05, 0.10, 0.15, 0.10, 0.05,
               0.15, 0.10, 0.02, 0.05, 0.02, 0.02]

# 投手（PLAYERS のインデックス）。先発の順に回す。
_PITCHERS = [5, 8, 11, 14]
_PITCHER_STRENGTH = {5: 0.9, 8: 1.0, 11: 1.2, 14: 1.4}  # 小さいほど良い


@dataclass
class Game:
    game_id: int
    date: datetime.date
    game_number: int
    opponent: str
    batting: list = field(default_factory=list)
    pitching: list = field(default_factory=list)
    runs_for: int = 0
    runs_against: int = 0
    result: str = ""


def _build_schedule(rng: random.Random) -> list[Game]:
    """土曜に 1 試合、4 週に 1 回は同日 2 試合目（ダブルヘッダー）を入れる。"""
    games = []
    date = SEASON_START
    week = 0
    while date <= SEASON_END:
        opp_index = (week * 3) % len(OPPONENTS)
        games.append(Game(len(games) + 1, date, 1, OPPONENTS[opp_index]))
        if week % 4 == 3:
            games.append(Game(len(games) + 1, date, 2, OPPONENTS[(opp_index + 1) % len(OPPONENTS)]))
        date += datetime.timedelta(days=7)
        week += 1
    return games


def _batting_line(rng: random.Random, idx: int, plate_appearances: int) -> dict:
    hit_rate, long_share = _HIT_RATE[idx], _LONG_HIT_SHARE[idx]
    walk_rate, so_rate = _WALK_RATE[idx], _SO_RATE[idx]
    line = dict(at_bat_count=0, hit_count=0, double_hit=0, triple=0, homerun=0,
                walk_count=0, strike_out=0, stolen_base=0,
                on_base_opportunity=plate_appearances, on_base=0,
                right_9=0, right_center=0, center=0, left_center=0, left_7=0)
    # 打球方向の偏り（右打ち・引っ張りなど）を選手ごとに固定する
    direction_weights = [
        [3, 2, 2, 1, 1], [1, 2, 2, 2, 3], [1, 1, 3, 2, 1], [2, 3, 2, 2, 1], [1, 2, 3, 2, 2],
    ][idx % 5]
    for _ in range(plate_appearances):
        r = rng.random()
        if r < walk_rate:
            line["walk_count"] += 1
            line["on_base"] += 1
            continue
        line["at_bat_count"] += 1
        r = rng.random()
        if r < hit_rate:
            line["hit_count"] += 1
            line["on_base"] += 1
            if rng.random() < long_share:
                kind = rng.random()
                if kind < 0.08 + long_share * 0.2:
                    line["homerun"] += 1
                elif kind < 0.2:
                    line["triple"] += 1
                else:
                    line["double_hit"] += 1
            direction = rng.choices(["right_9", "right_center", "center", "left_center", "left_7"],
                                    weights=direction_weights)[0]
            line[direction] += 1
        elif r < hit_rate + so_rate:
            line["strike_out"] += 1
        else:
            direction = rng.choices(["right_9", "right_center", "center", "left_center", "left_7"],
                                    weights=direction_weights)[0]
            line[direction] += 1
    if line["on_base"] > 0 and rng.random() < _STEAL_RATE[idx] * 1.5:
        line["stolen_base"] = 1
    return line


def _lineup(rng: random.Random, game_index: int) -> list[int]:
    """主力 9 名を基本に、数試合に 1 回は控えが入れ替わりで先発する。"""
    lineup = list(range(9))
    if game_index % 3 == 2:
        lineup[rng.randrange(3, 9)] = 9 + (game_index // 3) % 6
    if game_index % 7 == 5:
        lineup[rng.randrange(6, 9)] = 9 + (game_index // 2) % 6
    return lineup


def _simulate(rng: random.Random, games: list[Game]) -> None:
    for game_index, game in enumerate(games):
        team_hits = team_walks = team_hr = 0
        for idx in _lineup(rng, game_index):
            pa = rng.choice([3, 4, 4, 4, 5])
            line = _batting_line(rng, idx, pa)
            game.batting.append((idx, line))
            team_hits += line["hit_count"]
            team_walks += line["walk_count"]
            team_hr += line["homerun"]
        # 得点は出塁（安打・四死球）が多いほど増える
        runners = team_hits + team_walks
        game.runs_for = sum(rng.random() < 0.40 for _ in range(runners)) + team_hr

        starter = _PITCHERS[game_index % len(_PITCHERS)]
        strength = _PITCHER_STRENGTH[starter]
        # 9 回制（27 アウト）。先発が 16〜27 アウトを投げ、残りは別の投手が継投する。
        starter_outs = rng.choice([16, 18, 19, 21, 21, 22, 24, 27])
        innings = [(starter, starter_outs)]
        if starter_outs < 27:
            reliever = _PITCHERS[(game_index + 1 + rng.randrange(3)) % len(_PITCHERS)]
            if reliever == starter:
                reliever = _PITCHERS[(game_index + 1) % len(_PITCHERS)]
            innings.append((reliever, 27 - starter_outs))
        total_runs_against = 0
        for pitcher, outs in innings:
            hits_allowed = max(0, round(outs * rng.uniform(0.12, 0.38) * strength))
            walks_allowed = rng.randint(0, 1 + round(strength * outs / 9))
            batters_faced = outs + hits_allowed + walks_allowed
            strikeouts = rng.randint(max(0, outs // 6), max(1, outs // 2 - 1))
            homerun_allowed = 1 if hits_allowed > 0 and rng.random() < 0.12 * strength else 0
            runs_allowed = sum(rng.random() < 0.38 * strength for _ in range(hits_allowed + walks_allowed)) \
                + homerun_allowed
            earned_runs = max(0, runs_allowed - (1 if runs_allowed >= 3 and rng.random() < 0.3 else 0))
            directions = [0, 0, 0, 0, 0]
            for _ in range(max(0, hits_allowed - homerun_allowed)):
                directions[rng.randrange(5)] += 1
            game.pitching.append((pitcher, dict(
                batters_faced=batters_faced,
                pitch_count=round(batters_faced * rng.uniform(3.6, 4.4)),
                hits_allowed=hits_allowed, homerun_allowed=homerun_allowed,
                walks_allowed=walks_allowed, strikeouts=strikeouts, runs_allowed=runs_allowed,
                right_9=directions[0], right_center=directions[1], center=directions[2],
                left_center=directions[3], left_7=directions[4],
                innings_pitched=outs // 3, outs=outs % 3, earned_runs=earned_runs,
            )))
            total_runs_against += runs_allowed
        game.runs_against = total_runs_against
        if game.runs_for > game.runs_against:
            game.result = "〇"
        elif game.runs_for < game.runs_against:
            game.result = "×"
        else:
            game.result = "△"


def _q(value) -> str:
    if value is None:
        return "NULL"
    if isinstance(value, str):
        return "'" + value.replace("'", "''") + "'"
    return str(value)


def build_sql(games: list[Game]) -> str:
    lines = [
        "-- デモ用の合成データ（架空のチーム・選手・試合）。",
        "-- demo/generate_demo_data.py が生成する。直接編集しない。",
        "BEGIN;",
        "",
    ]
    team_ids = {TEAM_NAME: 1}
    for opponent in OPPONENTS:
        team_ids[opponent] = len(team_ids) + 1
    for name, team_id in team_ids.items():
        lines.append(f"INSERT INTO teams (team_id, team_name) VALUES ({team_id}, {_q(name)});")
    lines.append("")
    for i, name in enumerate(PLAYERS, start=1):
        lines.append(
            f"INSERT INTO players (player_id, player_name, team_id) VALUES ({i}, {_q(name)}, 1);"
        )
    lines.append("")
    for g in games:
        lines.append(
            "INSERT INTO games (game_id, game_date, home_team_id, away_team_id, game_number, "
            "home_score, away_score, result) VALUES "
            f"({g.game_id}, '{g.date.isoformat()}', 1, {team_ids[g.opponent]}, {g.game_number}, "
            f"{g.runs_for}, {g.runs_against}, {_q(g.result)});"
        )
    lines.append("")
    bat_cols = ["double_hit", "triple", "homerun", "at_bat_count", "hit_count", "walk_count",
                "strike_out", "stolen_base", "on_base_opportunity", "on_base",
                "right_9", "right_center", "center", "left_center", "left_7"]
    for g in games:
        for idx, line in g.batting:
            values = ", ".join(str(line[c]) for c in bat_cols)
            lines.append(
                f"INSERT INTO batting_stats (player_id, game_id, {', '.join(bat_cols)}) "
                f"VALUES ({idx + 1}, {g.game_id}, {values});"
            )
    lines.append("")
    pit_cols = ["batters_faced", "pitch_count", "hits_allowed", "homerun_allowed", "walks_allowed",
                "strikeouts", "runs_allowed", "right_9", "right_center", "center", "left_center",
                "left_7", "innings_pitched", "outs", "earned_runs"]
    for g in games:
        for pitcher, line in g.pitching:
            values = ", ".join(str(line[c]) for c in pit_cols)
            lines.append(
                f"INSERT INTO pitcher_stats (pitcher_id, game_id, {', '.join(pit_cols)}) "
                f"VALUES ({pitcher + 1}, {g.game_id}, {values});"
            )
    lines += [
        "",
        "-- 明示した ID の次から採番されるようにシーケンスを進める",
        "SELECT setval(pg_get_serial_sequence('teams', 'team_id'), (SELECT MAX(team_id) FROM teams));",
        "SELECT setval(pg_get_serial_sequence('players', 'player_id'), (SELECT MAX(player_id) FROM players));",
        "SELECT setval(pg_get_serial_sequence('games', 'game_id'), (SELECT MAX(game_id) FROM games));",
        "",
        "COMMIT;",
        "",
    ]
    return "\n".join(lines)


def build_run_history(games: list[Game]) -> str:
    """試合日の翌日に run_all.py を実行した、という体の実行履歴を作る。"""
    steps = [
        ("validate", "STEP 1: validate    — データ入力バリデーション"),
        ("generate", "STEP 2: generate    — 集計表示・試合入力ファイル生成"),
        ("import_db", "STEP 3: import_db   — DB登録"),
        ("analytics", "STEP 4: analytics   — 分析Excel出力 (year=2026)"),
    ]
    records = []
    for game in games[-6:]:
        run_time = datetime.datetime.combine(game.date + datetime.timedelta(days=1), datetime.time(21, 5))
        run_id = f"run_{run_time:%Y%m%d_%H%M%S}"
        for offset, (step, label) in enumerate(steps):
            ts = run_time + datetime.timedelta(seconds=offset * 3 + 1)
            records.append({
                "timestamp": ts.isoformat(), "run_id": run_id, "step": step, "label": label,
                "status": "OK", "year": 2026, "returncode": 0, "error": None,
            })
    return "".join(json.dumps(r, ensure_ascii=False) + "\n" for r in records)


def generate() -> tuple[list[Game], str, str]:
    rng = random.Random(SEED)
    games = _build_schedule(rng)
    _simulate(rng, games)
    return games, build_sql(games), build_run_history(games)


def main() -> None:
    here = os.path.dirname(os.path.abspath(__file__))
    games, sql, history = generate()
    with open(os.path.join(here, "seed.sql"), "w", encoding="utf-8") as f:
        f.write(sql)
    os.makedirs(os.path.join(here, "logs"), exist_ok=True)
    with open(os.path.join(here, "logs", "run_history.jsonl"), "w", encoding="utf-8") as f:
        f.write(history)
    wins = sum(g.result == "〇" for g in games)
    losses = sum(g.result == "×" for g in games)
    draws = sum(g.result == "△" for g in games)
    print(f"{len(games)} 試合（{wins}勝 {losses}敗 {draws}分）を生成しました。")


if __name__ == "__main__":
    main()
