DROP TABLE IF EXISTS kafka_cricket_fixtures;
CREATE TABLE IF NOT EXISTS kafka_cricket_fixtures (
    fixture_id UInt64,
    league_id UInt64,
    season_id UInt64,
    stage_id UInt64,
    round String,   
    localteam_id UInt64,
    visitorteam_id UInt64,
    starting_at String,
    type String,
    live UInt8,
    status String,
    note String,
    venue_id UInt64,
    toss_won_team_id UInt64,
    winner_team_id UInt64,
    man_of_match_id UInt64,
    total_overs_played UInt32,
    elected String,
    super_over UInt8,
    follow_on UInt8,
    updated_at UInt64
) ENGINE = Kafka
SETTINGS kafka_broker_list = 'redpanda:9092',
         kafka_topic_list = 'cricket_fixtures_v2',
         kafka_group_name = 'clickhouse_group',
         kafka_format = 'JSONEachRow';

DROP TABLE IF EXISTS kafka_teams;

CREATE TABLE IF NOT EXISTS kafka_teams (
    team_id UInt64,
    name String,
    code String,
    image_path String,
    country_id UInt64,
    national_team UInt8,
    updated_at UInt64
) ENGINE = Kafka
SETTINGS kafka_broker_list = 'redpanda:9092',
         kafka_topic_list = 'cricket_teams_v2',
         kafka_group_name = 'clickhouse-consumer-group',
         kafka_format = 'JSONEachRow',
         kafka_num_consumers = 1;

DROP TABLE IF EXISTS cricket_fixtures;

CREATE TABLE IF NOT EXISTS cricket_fixtures (
    fixture_id UInt64,
    league_id UInt64,
    season_id UInt64,
    stage_id UInt64,
    round String,
    localteam_id UInt64,
    visitorteam_id UInt64,
    starting_at String,
    type String,
    live UInt8,
    status String,
    note String,
    venue_id UInt64,
    toss_won_team_id UInt64,
    winner_team_id UInt64,
    man_of_match_id UInt64,
    total_overs_played UInt32,
    elected String,
    super_over UInt8,
    follow_on UInt8,
    updated_at UInt64
) ENGINE = ReplacingMergeTree(fixture_id)
ORDER BY fixture_id;

DROP TABLE IF EXISTS cricket_teams;

CREATE TABLE IF NOT EXISTS cricket_teams (
    team_id UInt64,
    name String,
    code String,
    image_path String,
    country_id UInt64,
    national_team UInt8,
    updated_at UInt64
) ENGINE = ReplacingMergeTree(updated_at)
ORDER BY team_id;

DROP TABLE IF EXISTS mv_fixtures_v2;
CREATE MATERIALIZED VIEW mv_fixtures_v2 TO cricket_fixtures AS
SELECT * FROM kafka_cricket_fixtures;

DROP TABLE IF EXISTS mv_teams_v2;
CREATE MATERIALIZED VIEW mv_teams_v2 TO cricket_teams AS
SELECT * FROM kafka_teams;

CREATE MATERIALIZED VIEW fixtures_with_team_names_mv
ENGINE = ReplacingMergeTree(fixture_id)
ORDER BY (fixture_id)
AS
SELECT
    f.*,
    t1.name AS localteam_name,
    t2.name AS visiting_team_name,
    t3.name AS toss_won_team,
    t4.name AS winner_team
FROM cricket_fixtures f
LEFT JOIN cricket_teams t1 ON f.localteam_id = t1.team_id
LEFT JOIN cricket_teams t2 ON f.visitorteam_id = t2.team_id
LEFT JOIN cricket_teams t3 ON f.toss_won_team_id = t3.team_id
LEFT JOIN cricket_teams t4 ON f.winner_team_id = t4.team_id;

