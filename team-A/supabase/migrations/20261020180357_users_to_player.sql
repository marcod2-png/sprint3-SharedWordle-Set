begin; -- opens transaction

-- rename table
alter table users rename to player;

-- rename relevant columns
alter table player  rename column user_id to player_id;
alter table plays   rename column user_id to player_id;
alter table guess   rename column user_id to player_id;

-- rename auto generated constraints that were intialized with users
alter table player  rename constraint users_pkey           to player_pkey;
alter table player  rename constraint users_username_key   to player_username_key;
alter table plays   rename constraint plays_user_id_fkey           to plays_player_id_fkey;
alter table guess   rename constraint guess_user_id_game_id_fkey   to guess_player_id_game_id_fkey;

commit; -- closes transaction, ensures entire transaction is commited, not just partially  