# Shared State Wordle

Shared State Wordle takes the classic single player game and adds a multiplayer component of going head-to-head against another player, either locally or via matchmaking. Instead of a player getting six turns it is split among two players who take turns making guesses using both their knowledge and whatever information they can gleam from the other player's guess.

## Description

| Connection (A -> B) | What is passed? (Function or Endpoint) | Format and Example | Owner | Done By |
| ------------------- | -------------------------------------- | ------------------ | ----- | ------- |
| Frontend Client -> Backend Server | GET /games/{games_id} | Data               | TEAM A | DONE |
| Frontend Client -> Backend Server | Data                                   | Data               |       |         |
| Frontend Client -> Backend Server | Data                                   | Data               |       |         |
| Frontend Client -> Backend Server | Data                                   | Data               |       |         |
| Frontend Client -> Backend Server | Data                                   | Data               |       |         |
| Frontend Client -> Backend Server | Data                                   | Data               |       |         |


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
