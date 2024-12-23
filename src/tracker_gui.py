import tkinter as tk
from tkinter import messagebox, ttk

from tracker_utils import Player, Tournament


def main():
    tournament_gui = TournamentGUI()
    tournament_gui.mainloop()


class TournamentGUI(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Tournament Tracker")

        self.tournament = Tournament()

        self.columnconfigure(0, weight=3)
        self.columnconfigure(1, weight=1)
        self.rowconfigure(0, weight=1)

        playerSetup = PlayerForm(self, self.tournament)
        playerSetup.grid(row=0, column=0, sticky="nsew", padx=5, pady=5)

        pairingSetup = PairingForm(self, playerSetup, self.tournament)
        pairingSetup.grid(row=0, column=1, sticky="nsew", padx=5, pady=5)

        # self.label = ttk.Label(self, text="Player Name:")
        # self.label.pack()

        # self.playerNameEntry = ttk.Entry(self)
        # self.playerNameEntry.insert(0, "Player Name")
        # self.playerNameEntry.bind("<FocusIn>", self.onPlayerEntryIn)
        # self.playerNameEntry.bind("<FocusOut>", self.onPlayerEntryOut)
        # self.playerNameEntry.config(foreground="grey")
        # self.playerNameEntry.pack()

        # self.playerNameEntry.bind("<Return>", self.addPlayer)

        # self.addButton = ttk.Button(self, text="Add Player", command=self.addPlayer)
        # self.addButton.pack()

        # self.checkButton = ttk.Button(self, text="Check Player", command=self.checkPlayer)
        # self.checkButton.pack()

        # self.rmvButton = ttk.Button(self, text="Remove Player", command=self.removePlayer)
        # self.rmvButton.pack()

        # self.listButton = ttk.Button(self, text="List Players", command=self.listPlayers)
        # self.listButton.pack()

        # self.tree = ttk.Treeview(self, columns=("Name", "Score", "Differential"), show="headings")
        # self.tree.heading("Name", text="Player Name")
        # self.tree.heading("Score", text="Game Score")
        # self.tree.heading("Differential", text="LS Differential")
        # self.tree.pack()

        # self.resultText = tk.Text(self, height=10, width=40)
        # self.resultText.pack()

    # def onPlayerEntryIn(self, _event=None):
    #     if str(self.playerNameEntry.cget("foreground")) == "grey":
    #         self.playerNameEntry.delete(0, tk.END)
    #         self.playerNameEntry.insert(0, "")
    #         self.playerNameEntry.config(foreground="black")

    # def onPlayerEntryOut(self, _event=None):
    #     if len(self.playerNameEntry.get()) - self.playerNameEntry.get().count(" ") < 1:
    #         self.playerNameEntry.insert(0, "Player Name")
    #         self.playerNameEntry.config(foreground="grey")

    # def addPlayer(self, _event=None):
    #     name = self.playerNameEntry.get()
    #     if name and not self.tournament.checkForPlayer(name):
    #         newPlayer = Player(name)
    #         self.tournament.addPlayer(newPlayer)
    #         self.tree.insert("", "end", values=(newPlayer.name, newPlayer.score, newPlayer.differential))
    #         self.playerNameEntry.delete(0, tk.END)
    #     else:
    #         messagebox.showwarning("Warning", "Player already exists or name is empty.")

    # def removePlayer(self):
    #     try:
    #         selectedItem = self.tree.selection()[0]
    #     except IndexError:
    #         messagebox.showwarning("Warning", "No player selected.")
    #     else:
    #         # Get name of player being removed and remove from tournament
    #         name = self.tree.item(selectedItem)["values"][0]
    #         if self.tournament.checkForPlayer(name):
    #             self.tournament.removePlayer(name)

    #         # Remove player from Player Table
    #         self.tree.delete(selectedItem)
    #         self.resultText.delete(1.0, tk.END) # Clear previous text
    #         self.resultText.insert(tk.END, f"{name} was removed.")

    # def checkPlayer(self):
    #     name = self.playerNameEntry.get()
    #     if self.tournament.checkForPlayer(name):
    #         messagebox.showinfo("Info", f"{name} is in the tournament.")
    #     else:
    #         messagebox.showinfo("Info", f"{name} is not in the tournament.")

    # def listPlayers(self):
    #     players = str(self.tournament)
    #     self.resultText.delete(1.0, tk.END) # Clear previous text
    #     self.resultText.insert(tk.END, players or "No players in tournament.")


class PlayerForm(ttk.Frame):
    def __init__(self, parent, tournament):
        super().__init__(parent)
        self.tournament = tournament

        self.columnconfigure(0, weight=1)
        self.rowconfigure(1, weight=1)

        # self.label = ttk.Label(self, text="Player Name:")
        # self.label.grid()

        self.playerNameEntry = ttk.Entry(self)
        self.playerNameEntry.insert(0, "Player Name")
        self.playerNameEntry.bind("<Return>", self.addPlayer)
        self.playerNameEntry.bind("<FocusIn>", self.onPlayerEntryIn)
        self.playerNameEntry.bind("<FocusOut>", self.onPlayerEntryOut)
        self.playerNameEntry.config(foreground="grey")
        self.playerNameEntry.grid(row=0, column=0, sticky="ew")

        self.addPlayerBtn = ttk.Button(self, text="Add Player", command=self.addPlayer)
        self.addPlayerBtn.grid(row=0, column=1)

        self.rmvPlayerBtn = ttk.Button(
            self, text="Remove Player", command=self.removePlayer
        )
        self.rmvPlayerBtn.grid(row=0, column=2)

        self.playerTable = ttk.Treeview(
            self, columns=("Name", "Score", "Differential"), show="headings"
        )
        self.playerTable.heading("Name", text="Player Name")
        self.playerTable.heading("Score", text="Game Score")
        self.playerTable.heading("Differential", text="LS Differential")
        self.playerTable.grid(row=1, columnspan=3)

        self.resultText = tk.Text(self, height=10, width=40)
        self.resultText.grid(row=2)

    def onPlayerEntryIn(self, _event=None):
        if str(self.playerNameEntry.cget("foreground")) == "grey":
            self.playerNameEntry.delete(0, tk.END)
            self.playerNameEntry.insert(0, "")
            self.playerNameEntry.config(foreground="black")

    def onPlayerEntryOut(self, _event=None):
        if len(self.playerNameEntry.get()) - self.playerNameEntry.get().count(" ") < 1:
            self.playerNameEntry.insert(0, "Player Name")
            self.playerNameEntry.config(foreground="grey")

    def addPlayer(self, _event=None):
        name = self.playerNameEntry.get()
        if name and not self.tournament.checkForPlayer(name):
            newPlayer = Player(name)
            self.tournament.addPlayer(newPlayer)
            self.playerTable.insert(
                "",
                "end",
                values=(newPlayer.name, newPlayer.score, newPlayer.differential),
            )
            self.playerNameEntry.delete(0, tk.END)
        else:
            messagebox.showwarning("Warning", "Player already exists or name is empty.")

    def removePlayer(self):
        try:
            selectedItem = self.playerTable.selection()[0]
        except IndexError:
            messagebox.showwarning("Warning", "No player selected.")
        else:
            # Get name of player being removed and remove from tournament
            name = self.playerTable.item(selectedItem)["values"][0]
            if self.tournament.checkForPlayer(name):
                self.tournament.removePlayer(name)

            # Remove player from Player Table
            self.playerTable.delete(selectedItem)
            self.resultText.delete(1.0, tk.END)  # Clear previous text
            self.resultText.insert(tk.END, f"{name} was removed.")

    def refreshPlayerTable(self):
        self.playerTable.delete(*self.playerTable.get_children())
        self.tournament.rankPlayers(False)
        for player in self.tournament.players:
            self.playerTable.insert(
                "", "end", values=(player.name, player.score, player.differential)
            )


class PairingForm(ttk.Frame):
    def __init__(self, parent, playerSetup, tournament):
        super().__init__(parent)
        self.playerSetup = playerSetup
        self.tournament = tournament
        self.pairLines = []

        self.calcPairsBtn = ttk.Button(self, text="Begin", command=self.nextRound)
        self.calcPairsBtn.grid(row=0, column=0)

        self.roundLabel = ttk.Label(self, text=f"Round: {self.tournament.round}")
        # self.roundLabel.grid(row=0, column=1)

        self.finishTourneyBtn = ttk.Button(
            self,
            text="Finish Tournament",
            state=tk.DISABLED,
            command=self.finishTournament,
        )
        self.finishTourneyBtn.grid(row=0, column=2)

        # self.pairingsTable = ttk.Treeview(self, columns=("Player1", "vs", "Player2"))

        # pairing = PairingLine(self, self.tournament)
        # pairing.grid(row=1, column=0, sticky="nsew", padx=5, pady=5)

    def nextRound(self):
        # TO DO: If first round, check to see if tournament has any players.
        # If not, break out and give pop-up saying to add players.

        # Tabulate scores
        if self.tournament.round > 0:
            for pair in self.pairLines:
                p1Name = pair.pairing[0].name
                p1Score = int(pair.player1ScoreCB.get())
                p2Name = pair.pairing[1].name
                p2Score = int(pair.player2ScoreCB.get())
                self.tournament.enterGameResult_T12P(p1Name, p1Score, p2Name, p2Score)
                # TO DO: Break out if invalid game scores

        ## TO DO: Update player scores and rankings in PlayerTable treeview
        self.playerSetup.refreshPlayerTable()

        # New Pairings
        newPairings = self.tournament.calcPairings()
        currentRound = self.tournament.round
        self.roundLabel.config(text=f"Round: {currentRound}")
        self.roundLabel.grid(row=0, column=1)

        if currentRound == 1:
            self.calcPairsBtn.config(text="Next Round")
            for pair in newPairings:
                pairLine = PairingLine(self, pair)
                self.pairLines.append(pairLine)
        else:
            for i in range(len(self.pairLines)):
                self.pairLines[i] = PairingLine(self, newPairings[i])
        rowCount = 1
        for pairLine in self.pairLines:
            pairLine.grid(row=rowCount, column=0, sticky="nsew", padx=5, pady=5)
            rowCount += 1

    def finishTournament(self):
        pass  # TO DO: Print out final tournament rankings including head-to-head


class PairingLine(ttk.Frame):
    def __init__(self, parent, pairing):
        super().__init__(parent)
        self.pairing = pairing

        self.player1Label = ttk.Label(self, text=str(self.pairing[0]))
        self.player1Label.grid(row=1, column=0)

        self.player1ScoreCB = ttk.Combobox(self, values=["0", "1", "2", "3", "4", "5"])
        self.player1ScoreCB.grid(row=1, column=1)
        self.player1ScoreCB.set("0")

        self.vsLabel = ttk.Label(self, text="vs")
        self.vsLabel.grid(row=1, column=2)

        self.player2Label = ttk.Label(self, text=str(self.pairing[1]))
        self.player2Label.grid(row=1, column=3)

        self.player2ScoreCB = ttk.Combobox(self, values=["0", "1", "2", "3", "4", "5"])
        self.player2ScoreCB.grid(row=1, column=4)
        self.player2ScoreCB.set("0")


if __name__ == "__main__":
    main()
