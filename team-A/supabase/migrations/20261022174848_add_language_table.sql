-- Author:      Miguel Leon
-- Co-author:   
-- Reviewer: 

-- new language table
create table language (
    language_code   TEXT    primary key,
    language_name   TEXT    not null unique
);

-- add English and Spanish
insert into language (language_code, language_name) values 
    ('eng', 'English'),
    ('esp', 'Spanish');

-- enable RLS
alter table language enable row level security;

-- add language column to player where English is set by default
alter table player
    add column language text not null default 'eng' references language (language_code);

-- drop foreign keys that reference words current primary key
-- the PK of answer and guess is being changed
alter table answer  drop constraint answer_word_fkey;
alter table guess   drop constraint guess_word_fkey;

-- add language column to word and update it's primary key
-- the PK of word is (language, word) i.e., ("eng", "pasta") is different from ("esp", "pasta")
alter table word
    add column language text not null references language (language_code);
alter table word drop constraint word_pkey;
alter table word add primary key (language, word);

-- update answer to reference the new primary key of word
-- answer words have an associated language
alter table answer
    add column language text not null;
alter table answer
    add constraint answer_word_fkey foreign key (language, word) references word (language, word);
alter table answer
    add constraint answer_game_language_key unique (game_id, language);
    
-- update guess to reference the new primary key of word
-- guesses have an associated langauge
alter table guess
    add column language text not null;
alter table guess
    add constraint guess_word_fkey foreign key (language, word) references word (language, word);
-- whenever a row is inserted into guess it's language must match the answers language
alter table guess
    add constraint guess_game_language_fkey
    foreign key (game_id, language) references answer (game_id, language);