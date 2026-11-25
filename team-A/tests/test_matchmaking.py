# CMSC 447 - Shared-State Wordle
# Tests for the matchmaking games, invite games, and switching between actions
#
#   POST    /games/match            Enter matchmaking pool
#   DELETE  /games/match            Exit matchmaking pool

import pytest
import helpers
from datetime import datetime, timezone

FALSE_GAME_ID   = "00000000-0000-0000-0000-000000000000"
FALSE_PLAYER_ID = "00000000-0000-0000-0000-000000000000"

""" FIXTURES """

@pytest.fixture(autouse=True)
def clear_pool(db):
    (db.table("matchmaking_queue")      # DELETE
     .delete()                          # FROM matchmaking_queue
     .neq("player_id", FALSE_PLAYER_ID) # WHERE player_id != FALSE_PLAYER_ID
     .execute())

""" ROUTE CALLERS """
# Each of these is a caller for a route. Each one sends a single request and
# returns the correct response WITH NO CHECKING. This is so that intentional
# errors can be verified for consistency

def join_mm(client, player):
    return client.post("/games/match", headers=player["headers"])

def leave_mm(client, player):
    return client.delete("/games/match", headers=player["headers"])

def create_invite(client, player):
    return client.post("/games", headers=player["headers"])

def cancel_invite(client, player, game_id):
    return client.delete(f"/games/{game_id}", headers=player["headers"])

def join_invite(client, player, game_id):
    return client.post(f"/games/{game_id}/join", headers=player["headers"])

def get_state(client, player, game_id):
    return client.get(f"/games/{game_id}", headers=player["headers"])

""" INTIAL STATE HELPERS """
# Reach the database and pulls lines to verify that request worked
# as expected

def _tickets(player, db, db_rows):
    res = (db.table("matchmaking_queue")            # SELECT *
           .select("*")                             # FROM matchmaking_queue
           .eq("player_id", player["player_id"])    # WHERE player_id = player_id
           .execute())
    return db_rows(res)

def _joined_at(player, db, db_rows):
    return _tickets(player, db, db_rows)[0]["joined_at"]

def _get_queued(db, db_rows):
    return [r["player_id"] for r in
            db_rows(db.table("matchmaking_queue")   # SELECT player_id
                    .select("player_id")            # FROM matchmaking_queue
                    .order("joined_at")             # ORDER BY joined_at
                    .execute())]

def _open_game_id(player):
    game = helpers.get_open_game(player["player_id"])

    if game is not None:
        return game["game_id"]
    return FALSE_GAME_ID

def _in_same_game(player_a, player_b):
    game_a = helpers.get_open_game(player_a["player_id"])
    game_b = helpers.get_open_game(player_b["player_id"])

    if game_a is not None and game_b is not None:
        return game_a["game_id"] == game_b["game_id"]
    return False

def _game_exists(game_id):
    return helpers.get_game_row(game_id) is not None

""" SETUP HELPERS """
# These are used to set game variable before into a state that will impact the
# test. For example, simulating many players in queue. 

def _inject_into_queue(player, db):
    # Skips the route, so the player is queued without looking for a match
    language = helpers.get_player_language(player["player_id"])
    (db.table("matchmaking_queue")                                      # INSERT INTO matchmaking_queue
     .insert({"player_id": player["player_id"], "language": language})  # (player_id, language)
     .execute())

def _set_language(player, language, db):
    (db.table("player")                     # UPDATE player
     .update({"language": language})        # SET language = language
     .eq("player_id", player["player_id"])  # WHERE player_id = player_id
     .execute())

def _finish_game(game_id, db):
    ended_at = datetime.now(timezone.utc).isoformat()
    (db.table("game")                                       # UPDATE game
     .update({"status": "finished", "ended_at": ended_at})  # SET status = 'finished', ended_at = ended_at
     .eq("game_id", game_id)                                # WHERE game_id = game_id
     .execute())

def _host_invite(client, player):
    r = create_invite(client, player)
    assert r.status_code == 201, r.get_json()
    return r.get_json()["game_id"]

def _start_invite_game(client, host, guest):
    game_id = _host_invite(client, host)
    r = join_invite(client, guest, game_id)
    assert r.status_code == 200, r.get_json()
    assert _in_same_game(host, guest)
    return game_id

def _start_mm_game(client, player_a, player_b):
    assert join_mm(client, player_a).status_code == 202
    assert join_mm(client, player_b).status_code == 201
    assert _in_same_game(player_a, player_b)
    return _open_game_id(player_a)

""" MATCHMAKING ROUTES TEST """

def test_first_player_in_queue(client, sofia):
    r = join_mm(client, sofia)

    assert r.get_json() == {"queued": True, "game_id": None}
    assert helpers.in_queue(sofia["player_id"])

def test_second_player_in_queue(client, sofia, julia):
    first = join_mm(client, sofia)

    assert first.status_code == 202
    assert first.get_json() == {"queued": True, "game_id": None}

    second = join_mm(client, julia)

    julia_game = helpers.get_open_game(julia["player_id"])
    sofia_game = helpers.get_open_game(sofia["player_id"])

    assert julia_game is not None
    assert sofia_game is not None

    assert second.status_code == 201
    assert second.get_json() == {"queued": False, "game_id": julia_game["game_id"]}

    assert _in_same_game(sofia, julia)

def test_thrid_player_in_queue(client, sofia, julia, grace, db, db_rows):
    _inject_into_queue(sofia, db) # FIRST
    _inject_into_queue(julia, db) # SECOND

    assert _get_queued(db, db_rows) == [sofia["player_id"], julia["player_id"]]

    r = join_mm(client, grace)
    assert r.status_code == 201

    assert _get_queued(db, db_rows) == [julia["player_id"]] # Only Julia waits

    assert _in_same_game(sofia, grace)

def test_leave_queue_normal(client, sofia, db, db_rows):
    join_mm(client, sofia)
    leave_mm(client, sofia)

    assert _get_queued(db, db_rows) == []

def test_leave_queue_and_rejoin(client, sofia, db, db_rows):
    join_mm(client, sofia)
    leave_mm(client, sofia)
    join_mm(client, sofia)

    assert _get_queued(db, db_rows) == [sofia["player_id"]]

def test_leave_and_rejoin_still_pairable(client, sofia, julia, db, db_rows):
    _inject_into_queue(sofia, db)
    _inject_into_queue(julia, db)
    leave_mm(client, sofia)

    assert _get_queued(db, db_rows) == [julia["player_id"]]

    r = join_mm(client, sofia)
    assert r.status_code == 201

    assert _in_same_game(sofia, julia)

def test_leave_queue_resets_timestamp(client, sofia, db, db_rows):
    original = "2026-01-01T00:00:00+00:00"
    helpers.join_queue(sofia["player_id"], "eng", original)

    assert original == _joined_at(sofia, db, db_rows)

    leave_mm(client, sofia)
    join_mm(client, sofia)

    assert _tickets(sofia, db, db_rows)[0]["joined_at"] != original

def test_leave_mm_safe_to_call_on_unqueued_players(client, sofia, db, db_rows):
    assert _get_queued(db, db_rows) == []
    leave_mm(client, sofia) # 204 checked in leave_mm
    assert _get_queued(db, db_rows) == []

""" INVITE ROUTES TEST """

def test_create_invite_game(client, sofia):
    assert _open_game_id(sofia) == FALSE_GAME_ID
    create_invite(client, sofia)

    invite = _open_game_id(sofia)
    assert invite != FALSE_GAME_ID

def test_cancel_invite_game(client, sofia):
    create_invite(client, sofia)
    game_id = _open_game_id(sofia)
    cancel_invite(client, sofia, game_id)
    assert _open_game_id(sofia) == FALSE_GAME_ID

def test_join_invite_game(client, sofia, grace):
    create_invite(client, sofia)
    game_id = _open_game_id(sofia)
    join_invite(client, grace, game_id)

    assert _in_same_game(sofia, grace)

def test_create_two_invtes(client, sofia):
    first = create_invite(client, sofia)
    assert first.status_code == 201
    game_id = _open_game_id(sofia)

    second  = create_invite(client, sofia)
    assert second.status_code == 409

    assert game_id == _open_game_id(sofia)

def test_create_invite_leaves_mm(client, sofia, db, db_rows):
    join_mm(client, sofia)
    assert _get_queued(db, db_rows) == [sofia["player_id"]]

    r = create_invite(client, sofia)
    assert r.status_code == 201

    assert _get_queued(db, db_rows) == []

def test_create_invite_after_leaving_mm_is_joinable(client, sofia, julia):
    join_mm(client, sofia)
    create_invite(client, sofia)
    game_id = _open_game_id(sofia)
    join_invite(client, julia, game_id)

    assert _in_same_game(sofia, julia)

def test_invite_unjoinable_when_entering_mm(client, sofia, julia):
    create_invite(client, sofia)
    game_id = _open_game_id(sofia)
    join_mm(client, sofia)

    r = join_invite(client, julia, game_id)
    assert r.status_code == 404
    assert _in_same_game(sofia, julia) == False

def test_cancel_invite_as_non_host(client, sofia, julia):
    create_invite(client, sofia)
    game_id = _open_game_id(sofia)

    r = client.delete(f"/games/{game_id}", headers=julia["headers"])
    assert r.status_code == 403

def test_cannot_cancel_started_invite_game(client, sofia, julia):
    game_id = _start_invite_game(client, sofia, julia)

    s = client.delete(f"/games/{game_id}", headers=julia["headers"])
    assert s.status_code == 403

    j = client.delete(f"/games/{game_id}", headers=sofia["headers"])
    assert j.status_code == 409

    assert _open_game_id(sofia) == game_id

def test_two_players_accept_invite(client, sofia, julia, grace):
    create_invite(client, sofia)
    game_id = _open_game_id(sofia)

    first = join_invite(client, julia, game_id)
    assert first.status_code == 200

    second = join_invite(client, grace, game_id)
    assert second.status_code == 409

    assert _in_same_game(sofia, julia)
    assert _in_same_game(sofia, grace) == False

def test_cannot_join_mm_with_started_invite_game(client, sofia, julia):
    _start_invite_game(client, sofia, julia)

    assert _in_same_game(sofia, julia)

    s = client.post("/games/match", headers=sofia["headers"])
    assert s.status_code == 409
    j = client.post("/games/match", headers=julia["headers"])
    assert j.status_code == 409

def test_cannot_join_mm_with_started_mm_game(client, sofia, julia):
    _start_mm_game(client, sofia, julia)

    s = client.post("/games/match", headers=sofia["headers"])
    assert s.status_code == 409
    j = client.post("/games/match", headers=julia["headers"])
    assert j.status_code == 409

def test_cannot_accept_invite_with_started_invite_game(client, sofia, julia, grace):
    _start_invite_game(client, sofia, julia)
    create_invite(client, grace)
    game_id = _open_game_id(grace)

    s = client.post(f"/games/{game_id}/join", headers=sofia["headers"])
    assert s.status_code == 409
    j = client.post(f"/games/{game_id}/join", headers=julia["headers"])
    assert j.status_code == 409

def test_cannot_accept_invite_with_started_mm_game(client, sofia, julia, grace):
    _start_mm_game(client, sofia, julia)
    create_invite(client, grace)
    game_id = _open_game_id(grace)

    s = client.post(f"/games/{game_id}/join", headers=sofia["headers"])
    assert s.status_code == 409
    j = client.post(f"/games/{game_id}/join", headers=julia["headers"])
    assert j.status_code == 409

def test_cannot_create_invite_with_started_mm_game(client, sofia, julia):
    _start_mm_game(client, sofia, julia)

    s = client.post("/games", headers=sofia["headers"])
    j = client.post("/games", headers=julia["headers"])

    assert s.status_code == 409
    assert j.status_code == 409

def test_cannot_create_invite_with_started_invite_game(client, sofia, julia):
    _start_invite_game(client, sofia, julia)

    s = client.post("/games", headers=sofia["headers"])
    j = client.post("/games", headers=julia["headers"])

    assert s.status_code == 409
    assert j.status_code == 409

""" HELPER TESTS """
# Helpers aren't completly tested here. The tests in this program
# focus on testing the routes. Tests are preformed on the individual
# helpers when creating the behaviour on the routes is too challenging

def test_in_queue_helper(client, sofia):
    assert helpers.in_queue(sofia["player_id"]) == False
    join_mm(client, sofia)
    assert helpers.in_queue(sofia["player_id"]) == True

def test_join_queue_normal(sofia, db, db_rows):
    helpers.join_queue(sofia["player_id"], "eng")
    ticket = _tickets(sofia, db, db_rows)

    assert ticket[0]["player_id"] == sofia["player_id"]
    assert ticket[0]["language"]  == "eng"
    assert ticket[0]["joined_at"] is not None

def test_join_queue_double_join(sofia, db, db_rows):
    helpers.join_queue(sofia["player_id"], "eng")
    original = _tickets(sofia, db, db_rows)

    helpers.join_queue(sofia["player_id"], language="end")
    duplicate = _tickets(sofia, db, db_rows)

    assert len(_tickets(sofia, db, db_rows)) == 1
    assert original[0]["joined_at"] == duplicate[0]["joined_at"]

def test_join_preserves_timestamp(sofia, db, db_rows):
    original = "2026-01-01T00:00:00+00:00"
    helpers.join_queue(sofia["player_id"], "eng", joined_at=original)

    assert original == _tickets(sofia, db, db_rows)[0]["joined_at"]

    # TODO: RACE