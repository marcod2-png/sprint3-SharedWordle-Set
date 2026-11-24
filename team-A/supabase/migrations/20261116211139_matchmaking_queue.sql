-- Author:  Miguel Leon
-- Reviwer: TODO

-- Matchmaking is a queue now instead of a flag 'match'. This approach will
-- only create a game once two players are matched. The previous apprach opened
-- half a game and had players wait with a 'match' flag. That was done because
-- the schema was not designed with matchmaking in mind. With this new table
-- the use of the flag is no longer needed and joining/leaving the queue is
-- as easy as deleting a single row.

-- Players who wish to play matchmaking are added as a row to this queue
-- using player_id as PK means that player can only join the queue once.
-- language is used to match players with same language preference.
-- joined_at is how we find the players who have been waiting the the queue
-- the longest.
create table matchmaking_queue (
    player_id   uuid        primary key references player (player_id) on delete cascade,
    language    text        not null references language (language_code),
    joined_at   TIMESTAMPTZ not null default now()
);

-- RLS
alter table matchmaking_queue enable row level security;

-- For look up of longest waiting player in a language
create index matchmaking_queue_lang_idx on matchmaking_queue(language, joined_at);

delete from game where status = 'waiting' and mode = 'match';   -- deprecated
drop index game_waiting_match_idx;                              -- deprecated
alter table game drop column mode;                              -- deprecated