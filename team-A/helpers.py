# CMSC 447 - Shared-State Wordle
import random
from postgrest.types import CountMethod
from postgrest.exceptions import APIError

import random
from db import admin, rows, auth_client
from postgrest.types import CountMethod
from postgrest.exceptions import APIError

OPEN_STATUS = ["waiting", "started"] # anything but finished

""" ERRORS """

class GameNotFound(Exception):
    """No game with that ID"""

class GameConflict(Exception):
    """Your request could not be completed"""

class GameForbidden(Exception):
    """Caller isn't a player in requested game."""

class PlayerNotFound(Exception):
    """No player found with for that ID"""

class NoWordsAvailable(Exception):
    """No words exist in the word table for that language"""

""" WORD HELPERS """

def pick_answer_word(language: str) -> str:
    """ Returns a randomly selected for from the word table for language """

    # Total number of words in a language
    count_res = (admin().table("word").select("word", count=CountMethod.exact).eq("language", language).limit(1).execute())
    total = count_res.count or 0
    if total == 0:
        raise NoWordsAvailable(f"There are no words available in '{language}'")

    # Fetch a word at a random position using bounds from total
    offset = random.randrange(total)
    res = (admin().table("word")
           .select("word")
           .eq("language", language)
           .order("word")
           .range(offset, offset)
           .execute())
    data = rows(res)
    if not data:
        raise NoWordsAvailable(f"There are no words available in '{language}'")
    return data[0]["word"]

""" PLAYER HELPERS """

def get_player_language(player_id: str) -> str | None:
    """ Returns a players preferred language and none if no player is found """

    res = (admin()
           .table("player")
           .select("language")
           .eq("player_id", player_id)
           .execute())
    data = rows(res)
    return data[0]["language"] if data else None

def get_open_game(player_id: str) -> dict | None:
    """ Returns that game_id and status if a player is in an unfinished game and
        return None if player has no unfinished games (games_status in OPEN_STATUS)"""

    res = (admin().table("plays")                   # SELECT g.game_id, g.status
           .select("game!inner(game_id, status)")   # FROM plays AS p JOIN game AS g ON g.game_id = p.game_id
           .eq("player_id", player_id)              # WHERE p.player_id = player_id
           .in_("game.status", OPEN_STATUS)         #   AND g.status IN ('waiting', 'started')
           .limit(1)                                # LIMIT 1
           .execute())
    data = rows(res)
    return data[0]["game"] if data else None

def release_player (player_id: str, join: str | None = None) -> None:
    """ Frees the player to start a different action. This function drops whatever
        the player was waiting on, so that they can join a different game """

    game = get_open_game(player_id)                             # 1. Find the players unfinished games. If the player
    if game is not None:                                        #    has no unfinished games. Then game = None 
        if game["game_id"] == join:                             # 2. If the game they want to leave is same game they
            raise GameConflict("You are already in this game")  #    want to join refuse the request
        if game["status"] != "waiting":                         # 3. If the game they want to leave has a status of
            raise GameConflict("You are already in a game")     #    'started' refuse the request
        try:                                                    # 4. If the game they want to leave hasn't started
            cancel_game(game["game_id"], player_id)             #    and isn't the same game they want to join
        except GameNotFound:                                    #    then cancel the game
            pass
    leave_queue(player_id)

""" MATCHMAKING QUEUE HELPERS """

def in_queue(player_id: str) -> bool:
    """ Returns true is the player is currently listed in the queue """

    res = (admin().table("matchmaking_queue")   # SELECT player_id
           .select("player_id")                 # FROM matchmaking_queue
           .eq("player_id", player_id)          # WHERE player_id = player_id
           .execute())
    return len(rows(res)) > 0

def join_queue(player_id: str, language: str, joined_at: str | None = None) -> None:
    """ Insert the player and their language into the matchmaking queue """

    # Opponents that are removed from the queue but are not successfully placed into a
    # game keep their original joined_at timestamp. If joined_at is none the column's
    # default now() is applied
    ticket = {"player_id": player_id, "language": language}
    if joined_at is not None:
        ticket["joined_at"] = joined_at

    try:
        (admin().table("matchmaking_queue") # INSERT INTO matchmaking_queue
         .insert(ticket)                    # (player_id, language)
         .execute())
    except APIError as e:
        if e.code != "23505": # unique_violation: Insertion failed because player is already in queue
            raise

def leave_queue(player_id: str) -> None:
    """ Removes the player from the matchmaking queue. Their row is deleted from 
        matchmaking_queue table. If no player_id is found in this table nothing
        happens. This function is safe to call even if player_id is not it table """

    (admin().table("matchmaking_queue")     
     .delete()                              # DELETE FROM matchmaking_queue
     .eq("player_id", player_id)            # WHERE player_id = player_id
     .execute())

""" MATCHMAKING GAME HELPERS """

def start_mm_match(player_a: str, player_b: str, language: str) -> dict:
    """ Starts a match between two paired players from matchmaking. The turn order 
        is randomly assined. Eventually, starts game once second player is seated """

    p1, p2 = random.sample([player_a, player_b], 2)
    game = insert_game(p1, language)

    try:
        return join_second_player(game["game_id"], p2)
    except Exception: # If joining a second player fails 
        (admin().table("game")              # DELETE
         .delete()                          # FROM game
         .eq("game_id", game["game_id"])    # WHERE game_id = game_id
         .execute())
        raise

def find_opponent(player_id: str, language: str) -> dict | None:
    """ Finds and assigns an opponet, decided by who has been waiting the the queue 
        the longest """

    db = admin()
    waitlist = rows(db.table("matchmaking_queue")   # SELECT player_id
                    .select("player_id")            # FROM matchmaking_queue
                    .eq("language", language)       # WHERE language = language
                    .neq("player_id", player_id)    #   AND player_id != player_id
                    .order("joined_at")             # ORDER BY joined_at
                    .limit(5)                       # LIMIT 5
                    .execute())
    # Removing the to-be-opponent from the waitlist
    for w in waitlist:
        opponent = rows(db.table("matchmaking_queue")       # DELETE
                        .delete()                           # FROM matchmaking_queue
                        .eq("player_id", w["player_id"])    # WHERE player_id = w.player_id
                        .execute())                         # RETURNING *
        if opponent:
            return opponent[0]
    return None

def match_player(player_id: str) -> dict | None:
    """ Pairs player with the player with with longest waiting time in their language
        if no player is avaible to be matched with the player is placed into the
        queue. If a match is found the started games row is reutrned, otherwise none """

    language = get_player_language(player_id) # returns none if no result if found for player_id
    if language is None:
        raise PlayerNotFound(player_id)
    
    if in_queue(player_id):     # If this player is already in the queue? Return none the player
        return None             # keeps waiting, and their time of remains the same. Otherwise, 
    release_player(player_id)   # release the player first so they can join the queue.

    opponent = find_opponent(player_id, language)   # Look for an opponent if none
    if opponent is None:                            # is found add player_id to queue
        join_queue(player_id, language)
        return None

    try:
        return start_mm_match(player_id, opponent["player_id"], language)
    except Exception:
        join_queue(opponent["player_id"], opponent["language"], opponent["joined_at"]) 
        raise

def matchmaking_status(player_id: str) -> dict:
    """ Players in queue wait for a match to be found. If a player is still in the
        queue, they comtinue to wait. """

    if in_queue(player_id):
        return {"queued": True, "game_id": None}
    
    game = get_open_game(player_id)
    if game is not None and game["status"] == "started":
        return {"queued": False, "game_id": game["game_id"]}
    return {"queued": False, "game_id": None}

""" INVITE GAME HELPERS """

def create_invite_game(player_id: str) -> dict:
    """ Creates an invite game in the host's langauge. The host is removed from
        matchmaking. Returns the game row with langauge attached """

    language = get_player_language(player_id) # None if no player found
    if language is None:
        raise PlayerNotFound(player_id)

    if get_open_game(player_id) is not None:
        raise GameConflict("You are already in a game")
    leave_queue(player_id) # Removes hosts from queue. Safe to call even if host isn't in queue

    game = insert_game(player_id, language)
    game["language"] = language
    return game

def join_invite_game(game_id: str, player_id: str) -> dict:
    """ Join and invite game as P2. If the player who is accepting this invite was
        in the matchmaking queue they are removed from it. """

    game = get_game_row(game_id)
    if game is None:
        raise GameNotFound(game_id) # Match was cancelled
    if game["status"] != "waiting":
        raise GameConflict("This game is already in progress")  # The game has already been set to 'started'
                                                                # another player has already joined the game
    release_player(player_id, join=game_id)         # Once checks pass release the to-be-p2 so they can join the invite game
    return join_second_player(game_id, player_id)   # Seat the second player

def cancel_game(game_id: str, player_id: str) -> None:
    """ Deletes a game that has status 'waiting' only the owner can cancel """
    db = admin()

    game = get_game_row(game_id)
    if game is None:
        raise GameNotFound(game_id)

    # Find the host of the game (player with turn = 1 for invite games)
    host = rows(db.table("plays")       # SELECT player_id
                .select("player_id")    # FROM plays
                .eq("game_id", game_id) # WHERE game_id = game_id
                .eq("turn_order", 1)    #   AND turn_order = 1
                .execute())

    if not host or host[0]["player_id"] != player_id:           # If the player_id does not match the host
        raise GameForbidden(game_id)                            # then they do not have permission to cancel
    if game["status"] != "waiting":                             # the game. Similarly, if the game has status
        raise GameConflict("Unable to cancel an active game")   # 'started' nobody has permission to cancel

    deleted = rows(db.table("game")         # DELETE
                   .delete()                # FROM game
                   .eq("game_id", game_id)  # WHERE game_id = game_id
                   .eq("status", "waiting") #   AND status = 'waiting'
                   .execute())

    if not deleted:                                             # If the game status is updated to 'started' between when we
        raise GameConflict("Unable to cancel an active game")   # checked permissions and took action then deletion will fail

""" PLAYER TWO HELPERS """

def join_second_player(game_id: str, player_id: str) -> dict:
    """ Writes the second player into the game. Once a game has two player then
        the game status is upgraded to 'started'. """

    db = admin()
    try:
        (db.table("plays")                                                      # INSERT INTO plays
         .insert({"game_id": game_id, "player_id": player_id, "turn_order": 2}) # (game_id, player_id, turn_order)
         .execute())
    except APIError as e: # Insertions failed 
        if e.code == "23505": # unique_violation
            raise GameConflict("This game is full") # Race case: Since game has not yet been set to 'started'. When two players
        raise                                       # join an invite at the same time, one of the insertions will fail.

    updated = rows(db.table("game")                 # UPDATE game
                   .update({"status": "started"})   # SET status 'started'
                   .eq("game_id", game_id)          # WHERE game_id = game_id
                   .eq("status", "waiting")         #   AND status = 'waiting'
                   .execute())
    if not updated: # This happens when the match is cancelled while P2 is joinging
        if get_game_row(game_id) is None:
            raise GameNotFound(game_id) # Match was cancelled
    return updated[0]

""" GAME HELPERS """ 

def get_game_row(game_id: str) -> dict | None:
    """ Returns the game row data (game_id, status, created_at, ended_at), returns
        none if no game row is found """

    res = (admin().table("game")    # SELECT *
           .select("*")             # FROM game
           .eq("game_id", game_id)  # WHERE game_id = game_id
           .execute())
    data = rows(res)
    return data[0] if data else None

def insert_game(player_id: str, language: str) -> dict:
    """ Inserts a game into games table. Adds the player with turn order 1 to the
        plays table. Player two needs to get added with join_second_player() """

    db = admin()

    game = rows(db.table("game")
                .insert({"status": "waiting"})
                .execute())[0]
    game_id = game["game_id"] # game_id is generated randomly by Postgres with gen_random_uuid()

    try:
        word = pick_answer_word(language)
        (db.table("answer")                                                         # INSERT INTO answer
         .insert({"game_id": game_id, "word": word, "language": language})          # (game_id, word, langauge)
         .execute())
        (db.table("plays")                                                          # INSERT INTO plays
         .insert({"game_id": game_id, "player_id": player_id, "turn_order": 1})     # (game_id, player_id, turn_order)
         .execute())
    except Exception:
        # Since these inserts happen sequentially and not in a
        # single transaction upon failure we must undo the game
        (db.table("game")           # DELETE
         .delete()                  # FROM game
         .eq("game_id", game_id)    # WHERE game_id = game_id
         .execute())
        raise
    return game

def whose_turn(players: list[dict], guesses: list[dict]) -> str | None:
    """ P1 will always go first, then turns will alternate. """
    next_order = len(guesses) % 2 + 1
    for p in players:
        if p["turn_order"] == next_order:
            return p["player_id"]
    return None # Player 2 hasn't joined yet

def get_game_state(game_id: str, player_id: str) -> dict:
    """ Returns the game state. The answer word is not returned until the game status 
        as been set the 'finished'. """
    db = admin()

    game = get_game_row(game_id)
    if game is None:
        raise GameNotFound(game_id)

    # players, with username pulled from the player table via FK
    plays = rows(db.table("plays")                                              # SELECT player_id, turn_order, results, player(username)
                 .select("player_id, turn_order, results, player(username)")    # FROM plays
                 .eq("game_id", game_id)                                        # WHERE game_id == game_id
                 .order("turn_order")                                           # ORDER BY turn_order
                 .execute())
    if player_id not in {p["player_id"] for p in plays}:
        raise GameForbidden(game_id)

    players = [{"player_id": p["player_id"],
                "username": (p.get("player") or {}).get("username"),
                "turn_order": p["turn_order"],
                "result": p["results"]}
                for p in plays]

    finished = game["status"] == "finished"

    answer = rows(db.table("answer")
                  .select("language, word" if finished else "language")
                  .eq("game_id", game_id)
                  .execute())

    guesses = rows(db.table("guess")
                   .select("attempt_num, player_id, word, feedback, made_at")
                   .eq("game_id", game_id)
                   .order("made_at")
                   .execute())

    state = {
        "game_id": game["game_id"],
        "status": game["status"],
        "created_at": game["created_at"],
        "ended_at": game["ended_at"],
        "language": answer[0]["language"],
        "players": players,
        "guesses": guesses,
        "current_turn" : whose_turn(players, guesses) if game["status"] == "started" else None,
    }
    if finished:
        state["answer"] = answer[0]["word"]
    return state

def verify_user(username: str, password: str) -> dict | None:
    """ Verifies a user's username and password using Supabase Auth.
        Returns user information and session tokens if authentication succeeds.
        Returns None if verification fails.
    """

    db = admin()
    # Find the user's email using their username
    response = (
        db.table("player")
        .select("player_id, username")
        .eq("username", username)
        .maybe_single()
        .execute()
    )
    
    if response is None or not isinstance(response.data, dict):
        return None

    row = response.data
    player_id = str(row["player_id"])
    db_username = str(row["username"])

    # Retrieve the user's email from Supabase Auth
    auth_user = admin().auth.admin.get_user_by_id(player_id)
    email = auth_user.user.email
    if not email:
        return None

    # Authenticate with Supabase Auth
    try:
        auth_response = auth_client().auth.sign_in_with_password({
            "email": email,
            "password": password,
        })
    except Exception:
        return None
    if auth_response.user is None or auth_response.session is None:
        return None
    
    return {
        "user_id": auth_response.user.id,
        "username": db_username,
        "access_token": auth_response.session.access_token,
        "refresh_token": auth_response.session.refresh_token,
        "expires_at": auth_response.session.expires_at
    }
