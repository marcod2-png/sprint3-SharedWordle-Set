# Shared State Wordle

Shared State Wordle takes the classic single player game and adds a multiplayer component of going head-to-head against another player, either locally or via matchmaking. Instead of a player getting six turns it is split among two players who take turns making guesses using both their knowledge and whatever information they can gleam from the other player's guess.

## Description

Our website first starts you off on the intro/start screen where you're able to either sign in/sign up or directly play a game without doing either of those options. Signing in sends a request to the backend to check if the desired account already exists, and if it does it then logs them into that account and going forward, until they sign out, all data will be stored with that account. Signing up sends a request to the backend to check if any account with that information already exists, and if it doesn't it then automatically signs them into it. After that when a user hits play their preferred language that they select will be stored in the backend so games played after the initial one are done with that previously picked language, with the only way this being able to be changed is by going back to the start screen. A user can then select to play against the CPU or another player, regardless of what they pick they'll be put into a match where they have three chances to not only figure out the word, but also attempt to beat their opponent. The statistics surrounding the game they play will be stored to their account and when they select the statistics tab the frontend should make a GET request to retrieve all the required information. The user can also go to the history tab which will allow them to select any day and that will make a GET request from the backend so they can grab all games played that day and the information associated with it to display to the user. Besides this the user has access to a host of accessibility features such as dark mode and high contrast mode that will allow them to customize their game experience. If a user wants to play against someone they know they can generate a game code and have that sent to another player so they're guaranteed to be matchmade against them.

## Integration Table

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

