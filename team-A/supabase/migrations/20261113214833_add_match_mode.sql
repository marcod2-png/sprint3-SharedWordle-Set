-- Author:      Miguel Leon
-- Reviewer:    

-- Games are joined either by and invite (shared with game_id) or matchmaking
-- (players joined from waiting pool). Existing games were all invite only.
alter table game
    add column mode text not null default 'invite'
    check (mode in ('invite', 'match'));

-- Matchmaking will find the oldest waiting 'match' games. This will speed
-- up data retrieval
create index game_waiting_match_idx
    on game (created_at)
    where status = 'waiting' and mode = 'match';