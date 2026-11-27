# Shared State Wordle

Shared State Wordle takes the classic single player game and adds a multiplayer component of going head-to-head against another player, either locally or via matchmaking. Instead of a player getting six turns it is split among two players who take turns making guesses using both their knowledge and whatever information they can gleam from the other player's guess.

## Description

| Connection (A -> B) | What is passed? (Function or Endpoint) | Format and Example | Owner | Done By |
| ------------------- | -------------------------------------- | ------------------ | ----- | ------- |
| Frontend Client -> Backend Server | GET /games/{games_id} | Response: {"game_id":"<uuid>","status":"started","created_at":"<timestamp>","ended_at":"<timestamp>","language":"<language>","players":[{"player_id":"<uuid>","username":"<name>","turn_order":1,"result":null},{"player_id":"<uuid>","username":"<name>","turn_order":2,"result":null}],"guesses":[{"attempt_num":1,"player_id":"<uuid>","word":"<guess>","feedback":"","made_at":"<timestamp>"}],"current_turn":"<uuid>","answer":"<answer>"} | TEAM A | DONE |
| Frontend Client -> Backend Server | POST /games/match | Response 201:{"queued":false,"game_id":"<game_id>"} .Response 202:{"queued":true,"game_id":null} | TEAM A | DONE |
| Frontend Client -> Backend Server | DELETE /games/match | Response: HTTP 204 | TEAM A | DONE |
| Frontend Client -> Backend Server | POST /games | Response 201:{"game_id":"<game_id>","game_status":"waiting","language":"<language>"} | TEAM A | DONE |
| Frontend Client -> Backend Server | GET /games/match | Response 200:{"queued":true,"game_id":null} or{"queued":false,"game_id":"<game_id>"} or{"queued":false,"game_id":null} | TEAM A | DONE |
| Frontend Client -> Backend Server | DELETE /games/{games_id} | Response: HTTP 204 | TEAM A | DONE |
| Frontend Client -> Backend Server | POST /games/{game_id}/join | Response 201:{"game_id":"<game_id>","game_status":"started","turn_order":2} | TEAM A | DONE |
| Frontend Client -> Backend Server | POST /users/login | Response 201:{"user_id":"<user_id>","username":"<username>","access_token":"<access_token>","refresh_token":"<refresh_token>","expires_at":"<expiration_timestamp>"} | Team A | DONE |
| Frontend Client -> Backend Server | POST /users/edit/language | Request:{"lang_code":"es"} .Success (200):{"lang_code":"es"} .Errors: {"error":"Missing language code"} (400),{"error":"Invalidlanguage code"} (400),{"error":"Failed toupdate language"} (500). | TEAM A | 11/26/26 |
| Frontend Client -> Backend Server | POST /game/guess | Unknown | TEAM A | TBD |
| Frontend Client -> Backend Server | POST /users | Unknown | TEAM A | TBD |
| Frontend Client -> Backend Server | POST /users/history | Unknown | TEAM A | TBD |

## Getting Started

### Dependencies

* Nothing needs to be installed before running this, the only thing needed is a browser and the web address
* The server needs to be spun up with the database active for data to be stored and displayed
* (If any team needs to add more information please update accordingly)

### Executing program

* Running the program is as simple as visiting the link which should take you directly to the start screen and selecting play, which will lead you through a series of preferences
* Actual multiplayer isn't implemented yet and is only done locally, CPU is more supported at the moment
* (If any team needs to add more information please update accordingly)

## Help

If a user finds themselves stuck in a game or don't know how to restart, they can simply exit out and go back to the start screen to give them a new beginning.

Certain features, such a history and statistics host static data/information and aren't properly set up at the moment.

(If any team needs to add more information please update accordingly)

## Authors

Contributors names

(Team A)
Put Names Here

(Team B)
Put Names Here

(Team C)
Marco DeCesaris
Jacob Wingers
Isabelle Knight
Camila Ton


## License

This project is licensed under the MIT License - see the LICENSE.md file for details
