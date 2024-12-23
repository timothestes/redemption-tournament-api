class Player:
    def __init__(self, name):
        self.name = name
        self.deckChecked = False
        self.score = 0
        self.differential = 0
        self.opponents = set()

    def __repr__(self):
        return f"{self.name} ({self.score}, {self.differential})"

    # TO DO: Implement way to mark that their deck has been checked and confirm
    # that deckChecked is True for all players before starting Round 1.
    def checkDeck(self):
        self.deckChecked = True

    def addOpponent(self, opponent):
        self.opponents.add(opponent)

    def addScore(self, score):
        self.score += score

    def addLSDifferential(self, differential):
        self.differential += differential


# TO DO: Implement a means of saving the Tournament state (including Player scores)
#   at the end of each round so that the host can revert to a previous round if
#   there was a mistake, someone has to leave, etc.
class Tournament:
    def __init__(self):
        self.players = []
        self.round = 0

    def __repr__(self):
        return "\n".join(str(player) for player in self.players)

    def addPlayer(self, player):
        self.players.append(player)

    def removePlayer(self, playerName):
        self.players = [player for player in self.players if player.name != playerName]

    def updatePlayerScore(self, name, score, differential):
        for player in self.players:
            if player.name == name:
                player.addScore(score)
                player.addLSDifferential(differential)
                return

    # Returns True if a player by a certain name is in the tournament
    # Probably not necessary once tournament is controlled by GUI
    def checkForPlayer(self, playerName) -> bool:
        return any(player.name == playerName for player in self.players)

    # Returns True if both scores are between 0 and 5 inclusive and
    # at most one score is equal to 5
    def validGameResult_T12P(self, score1, score2):
        return (
            (0 <= score1 <= 5)
            and (0 <= score2 <= 5)
            and not (score1 == 5 and score2 == 5)
        )

    def enterGameResult_T12P(self, p1Name, p1Redeemed, p2Name, p2Redeemed):

        # Confirm both players are still in the tournament
        # TO DO: Cleanly handle cases when players aren't found in tournament.
        # Maybe not needed at this point if entries can only be made from legit pairings.
        if not self.checkForPlayer(p1Name):
            print(f"Player {p1Name} not found in tournament.")
            return
        if not self.checkForPlayer(p2Name):
            print(f"Player {p2Name} not found in tournament.")
            return

        # Check validity of game result
        if not self.validGameResult_T12P(p1Redeemed, p2Redeemed):
            print(f"{p1Redeemed} and {p2Redeemed} are not valid game scores.")
            return

        # Calculate Lost Soul Differential for each player
        p1Diff = p1Redeemed - p2Redeemed
        p2Diff = -p1Diff

        # Calculate Game Score for each player
        if p1Redeemed == 5:
            p1Score = 3
            p2Score = 0
        elif p2Redeemed == 5:
            p1Score = 0
            p2Score = 3
        elif p1Redeemed == p2Redeemed:
            p1Score = p2Score = 1.5
        elif p1Redeemed > p2Redeemed:
            p1Score = 2
            p2Score = 1
        else:
            p1Score = 1
            p2Score = 2

        # Update Game Score and Lost Soul Differential for each player
        self.updatePlayerScore(p1Name, p1Score, p1Diff)
        self.updatePlayerScore(p2Name, p2Score, p2Diff)

    # If this function is being used to determine the final
    # results of the tournament then finalScoring = True and
    # head-to-head will be taken into account to determine
    # rankings. Otherwise rankings will be determined by Game
    # Score and Lost Soul Differential only.
    def rankPlayers(self, finalScoring: bool) -> list:
        if not finalScoring:
            self.players.sort(key=lambda player: (-player.score, -player.differential))
        else:
            pass  # TO DO: Sort players by rank using head-to-head as the first score tiebreaker

    # TO DO: Implement random pairings for players that are tied (should work for creating
    #   Round 1 pairings and determining who plays Player 1 if Players 2 and 3 are tied).
    # TO DO: Handle when it can't find pairings that haven't already played. Currently, the
    #   implementation is linear and can't backtrack, so if it gets to the end and the last
    #   two players have already played then it will break.
    def calcPairings(self):
        self.rankPlayers(False)
        self.round += 1

        pairings = []
        usedIndices = set()  # Keep track of players accounted for

        while len(usedIndices) < len(self.players):
            for i in range(len(self.players)):
                if i in usedIndices:
                    continue
                player1 = self.players[i]
                for j in range(i + 1, len(self.players)):
                    if j in usedIndices:
                        continue
                    player2 = self.players[j]

                    # Check if player1 and player2 have already played
                    if player2.name not in player1.opponents:
                        pairings.append((player1, player2))
                        player1.addOpponent(player2.name)
                        player2.addOpponent(player1.name)
                        usedIndices.add(i)
                        usedIndices.add(j)
                        break
                else:
                    continue  # Pairing created, break the outer loop
                break  # Exit outer loop after pairing

        return pairings
