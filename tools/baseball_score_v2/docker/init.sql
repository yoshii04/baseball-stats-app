-- teams
CREATE TABLE teams (
    team_id SERIAL PRIMARY KEY,
    team_name TEXT NOT NULL
);
COMMENT ON COLUMN teams.team_id IS 'チームID';
COMMENT ON COLUMN teams.team_name IS 'チーム名';

-- players
CREATE TABLE players (
    player_id SERIAL PRIMARY KEY,
    player_name TEXT NOT NULL,
    team_id INT NOT NULL REFERENCES teams(team_id)
);
COMMENT ON COLUMN players.player_id IS '選手ID';
COMMENT ON COLUMN players.player_name IS '選手名';
COMMENT ON COLUMN players.team_id IS 'チームID';

-- games
CREATE TABLE games (
    game_id SERIAL PRIMARY KEY,
    game_date DATE NOT NULL,
    home_team_id INT NOT NULL REFERENCES teams(team_id),
    away_team_id INT NOT NULL REFERENCES teams(team_id),
    game_number INT NOT NULL DEFAULT 1,
    home_score INTEGER,
    away_score INTEGER,
    result VARCHAR(1)
);
COMMENT ON COLUMN games.game_id IS '試合ID';
COMMENT ON COLUMN games.game_date IS '日付';
COMMENT ON COLUMN games.home_team_id IS 'ホームチームID';
COMMENT ON COLUMN games.away_team_id IS 'アウェイチームID';
COMMENT ON COLUMN games.game_number IS '試合番号（ダブルヘッダー対応: 1試合目=1, 2試合目=2）';
COMMENT ON COLUMN games.home_score IS 'ホームチーム得点';
COMMENT ON COLUMN games.away_score IS 'アウェイチーム得点';
COMMENT ON COLUMN games.result IS '試合結果（W/L/D）';

-- batting_stats
CREATE TABLE batting_stats (
    batting_id SERIAL PRIMARY KEY,
    player_id INT NOT NULL REFERENCES players(player_id),
    game_id INT NOT NULL REFERENCES games(game_id),
    at_bat INT,
    pitch_count INT,
    first_pitch INT,
    total INT,
    homerun INT,
    triple INT,
    double_hit INT,
    single INT,
    walk INT,
    hit_by_pitch INT,
    error INT,
    strike INT,
    strike_out_with_runner INT,
    sacrifice_hit INT,
    sacrifice_fly INT,
    fc INT,
    obstruction INT,
    ground_ball INT,
    liner INT,
    infield_fly INT,
    outfield_fly INT,
    direction TEXT,
    rbi INT,
    run INT,
    failure INT,
    steal_2 INT,
    steal_3 INT,
    steal_home INT,
    wk INT,
    at_bat_count INT,
    walk_count INT,
    two_strike_walk INT,
    strike_out INT,
    hit_count INT,
    on_base_opportunity INT,
    on_base INT,
    stolen_base INT,
    total_bases INT,
    right_9 INT,
    right_center INT,
    center INT,
    left_center INT,
    left_7 INT
);

COMMENT ON COLUMN batting_stats.batting_id IS '打撃ID';
COMMENT ON COLUMN batting_stats.player_id IS '選手ID';
COMMENT ON COLUMN batting_stats.game_id IS '試合ID';
COMMENT ON COLUMN batting_stats.at_bat IS '打席';
COMMENT ON COLUMN batting_stats.pitch_count IS '投球';
COMMENT ON COLUMN batting_stats.first_pitch IS '初球';
COMMENT ON COLUMN batting_stats.total IS 'total';
COMMENT ON COLUMN batting_stats.homerun IS '本塁打';
COMMENT ON COLUMN batting_stats.triple IS '3塁打';
COMMENT ON COLUMN batting_stats.double_hit IS '2塁打';
COMMENT ON COLUMN batting_stats.single IS '1塁打';
COMMENT ON COLUMN batting_stats.walk IS '四球';
COMMENT ON COLUMN batting_stats.hit_by_pitch IS '死球';
COMMENT ON COLUMN batting_stats.error IS '失策';
COMMENT ON COLUMN batting_stats.strike IS '振';
COMMENT ON COLUMN batting_stats.strike_out_with_runner IS '振逃';
COMMENT ON COLUMN batting_stats.sacrifice_hit IS '犠打';
COMMENT ON COLUMN batting_stats.sacrifice_fly IS '犠飛';
COMMENT ON COLUMN batting_stats.fc IS 'FC';
COMMENT ON COLUMN batting_stats.obstruction IS '妨害';
COMMENT ON COLUMN batting_stats.ground_ball IS 'ゴロ';
COMMENT ON COLUMN batting_stats.liner IS 'ライナー';
COMMENT ON COLUMN batting_stats.infield_fly IS '内F';
COMMENT ON COLUMN batting_stats.outfield_fly IS '外F';
COMMENT ON COLUMN batting_stats.direction IS '方向';
COMMENT ON COLUMN batting_stats.rbi IS '打点';
COMMENT ON COLUMN batting_stats.run IS '得点';
COMMENT ON COLUMN batting_stats.failure IS '失敗';
COMMENT ON COLUMN batting_stats.steal_2 IS '2盗';
COMMENT ON COLUMN batting_stats.steal_3 IS '3盗';
COMMENT ON COLUMN batting_stats.steal_home IS '本盗';
COMMENT ON COLUMN batting_stats.wk IS 'WK';
COMMENT ON COLUMN batting_stats.at_bat_count IS '打数';
COMMENT ON COLUMN batting_stats.walk_count IS '四死球';
COMMENT ON COLUMN batting_stats.two_strike_walk IS '2S四死球';
COMMENT ON COLUMN batting_stats.strike_out IS '三振';
COMMENT ON COLUMN batting_stats.hit_count IS '安打';
COMMENT ON COLUMN batting_stats.on_base_opportunity IS '出塁機会';
COMMENT ON COLUMN batting_stats.on_base IS '出塁';
COMMENT ON COLUMN batting_stats.stolen_base IS '盗塁';
COMMENT ON COLUMN batting_stats.total_bases IS '塁打数';
COMMENT ON COLUMN batting_stats.right_9 IS '右';
COMMENT ON COLUMN batting_stats.right_center IS '右中';
COMMENT ON COLUMN batting_stats.center IS '中';
COMMENT ON COLUMN batting_stats.left_center IS '左中';
COMMENT ON COLUMN batting_stats.left_7 IS '左';

-- pitcher_stats
CREATE TABLE pitcher_stats (
    pitcher_stat_id SERIAL PRIMARY KEY,
    pitcher_id      INT NOT NULL REFERENCES players(player_id),
    game_id         INT NOT NULL REFERENCES games(game_id),
    batters_faced   INT,
    pitch_count     INT,
    hits_allowed    INT,
    homerun_allowed INT,
    walks_allowed   INT,
    strikeouts      INT,
    runs_allowed    INT,
    right_9         INT,
    right_center    INT,
    center          INT,
    left_center     INT,
    left_7          INT,
    innings_pitched INT,
    outs            INT,
    earned_runs     INT
);

COMMENT ON COLUMN pitcher_stats.pitcher_stat_id IS '投手成績ID';
COMMENT ON COLUMN pitcher_stats.pitcher_id IS '投手選手ID';
COMMENT ON COLUMN pitcher_stats.game_id IS '試合ID';
COMMENT ON COLUMN pitcher_stats.batters_faced IS '対戦打者数';
COMMENT ON COLUMN pitcher_stats.pitch_count IS '投球数';
COMMENT ON COLUMN pitcher_stats.hits_allowed IS '被安打';
COMMENT ON COLUMN pitcher_stats.homerun_allowed IS '被本塁打';
COMMENT ON COLUMN pitcher_stats.walks_allowed IS '与四死球';
COMMENT ON COLUMN pitcher_stats.strikeouts IS '奪三振';
COMMENT ON COLUMN pitcher_stats.runs_allowed IS '失点';
COMMENT ON COLUMN pitcher_stats.right_9 IS '右';
COMMENT ON COLUMN pitcher_stats.right_center IS '右中';
COMMENT ON COLUMN pitcher_stats.center IS '中';
COMMENT ON COLUMN pitcher_stats.left_center IS '左中';
COMMENT ON COLUMN pitcher_stats.left_7 IS '左';
COMMENT ON COLUMN pitcher_stats.innings_pitched IS '投球回（整数部）';
COMMENT ON COLUMN pitcher_stats.outs IS 'アウト数（余り: 0/1/2）';
COMMENT ON COLUMN pitcher_stats.earned_runs IS '自責点';

-- unique constraints
ALTER TABLE teams ADD CONSTRAINT uq_team_name UNIQUE (team_name);
ALTER TABLE players ADD CONSTRAINT uq_player UNIQUE (player_name, team_id);
ALTER TABLE games ADD CONSTRAINT uq_games_date_home_away_number UNIQUE (game_date, home_team_id, away_team_id, game_number);
ALTER TABLE batting_stats ADD CONSTRAINT uq_batting_stats_player_game UNIQUE (player_id, game_id);
ALTER TABLE pitcher_stats ADD CONSTRAINT uq_pitcher_stats_pitcher_game UNIQUE (pitcher_id, game_id);
