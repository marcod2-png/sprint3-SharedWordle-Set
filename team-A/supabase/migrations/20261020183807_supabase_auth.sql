-- Author:      Miguel Leon
-- Co-author:   
-- Reviewer:    

-- IDs will come from Supabase Auth, remove default gen_random_id()
alter table player
    alter column player_id drop default;

-- Each row must be tied to an auth account
alter table player
    add constraint player_user_id_fkey
    foreign key (player_id) references auth.users (id)
    on delete cascade; -- When account is deleted delete entry in player table

-- Player will be automatically created on sign-up
create function handle_new_user()
returns trigger -- can't be called by a query
language plpgsql -- PL/psSQL
security definer set search_path = ''
as $$
    begin
        insert into public.player (player_id, username) 
        values (new.id, -- Supabase Auth generates a new random id
                new.raw_user_meta_data ->> 'username'); -- pull the raw string with ->> out of JSON {"username"}
        return new;
    end;
$$;

-- trigger to run automatically when auth user is created
create trigger on_auth_user_created
    after insert on auth.users
    for each row execute function handle_new_user();