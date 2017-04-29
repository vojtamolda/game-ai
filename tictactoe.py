from PyQt5.QtWidgets import QApplication, QWidget, QPushButton, QGridLayout, QMessageBox, QSizePolicy
from PyQt5.QtCore import Qt, QSize
import unittest
import sys


class TicTacToe:
    class Tile:
        def __init__(self, row, column, player=None):
            self.row, self.column = row, column
            self.player = player
            self.delegate = None

        def __str__(self):
            return str(self.player) if self.player is not None else "☐"

        def set(self, player, notify=False):
            self.player = player
            if notify is True:
                self.notify()

        def clear(self, notify=False):
            self.player = None
            if notify is True:
                self.notify()

        def notify(self):
            if self.delegate is not None:
                self.delegate.updateEvent(self)

        def score(self, board, player):
            def completeRow(board, player, row):
                return player == board[row, 0].player == board[row, 1].player == board[row, 2].player

            def completeColumn(board, player, column):
                return player == board[0, column].player == board[1, column].player == board[2, column].player

            def completeDiagonal(board, player, row, column):
                if column - row == 0:
                    return player == board[0, 0].player == board[1, 1].player == board[2, 2].player
                if column + row == 2:
                    return player == board[0, 2].player == board[1, 1].player == board[2, 0].player

            def completeBoard(board):
                for tile in board:
                    if tile.player is None:
                        return False
                return True

            row, column = self.row, self.column
            if completeRow(board, player, row):
                return 1
            if completeColumn(board, player, column):
                return 1
            if completeDiagonal(board, player, row, column):
                return 1
            if completeBoard(board):
                return 0
            return None

    class Player:
        def __init__(self, symbol):
            self.symbol = symbol

        def __str__(self):
            return self.symbol

    class AI(Player):
        def play(self, board, opponent, recursionLevel=1):
            bestScore, bestTile = -2, None

            for tile in board.emptyTiles():
                tile.set(self)
                score = tile.score(board, self)
                if score is None:
                    opponentScore, opponentTile = TicTacToe.AI.play(opponent, board, self, recursionLevel + 1)
                    score = -opponentScore
                else:
                    score /= recursionLevel
                if score > bestScore:
                    bestScore, bestTile = score, tile
                tile.clear()

            return bestScore, bestTile

    def __init__(self):
        self.size = 3
        self.ai = TicTacToe.AI("☓")
        self.player = TicTacToe.Player("◯")
        self.board = {}
        for row in range(self.size):
            for column in range(self.size):
                self.board[row, column] = TicTacToe.Tile(row, column)

    def __contains__(self, row_column):
        return row_column in self.board

    def __getitem__(self, row_column):
        return self.board[row_column]

    def __iter__(self):
        return self.board.values().__iter__()

    def __str__(self):
        string = ""
        for row in range(self.size):
            for column in range(self.size):
                string += str(self[row, column])
            string += "\n"
        return string

    @classmethod
    def create(TicTacToe, symbols):
        ticTacToe = TicTacToe()
        for row, symbols_row in enumerate(symbols):
            for column, symbol in enumerate(symbols_row):
                tile = ticTacToe[row, column]
                if symbol == ticTacToe.ai.symbol:
                    tile.player = ticTacToe.ai
                if symbol == ticTacToe.player.symbol:
                    tile.player = ticTacToe.player
        return ticTacToe

    def emptyTiles(self):
        for tile in self:
            if tile.player is None:
                yield tile

    def playRound(self, playerTile):
        playerTile.set(self.player, True)
        playerScore = playerTile.score(self, self.player)
        if playerScore is not None:
            return playerScore

        _, aiTile = self.ai.play(self, self.player)
        aiTile.set(self.ai, True)
        aiScore = aiTile.score(self, self.ai)
        if aiScore is not None:
            return -aiScore
        return None

    def reset(self):
        for tile in self:
            tile.clear(True)


class QTicTacToe(QWidget):
    class QTileButton(QPushButton):
        def __init__(self, playerSymbolMap):
            super(QTicTacToe.QTileButton, self).__init__()
            self.playerSymbolMap = playerSymbolMap
            self.setFocusPolicy(Qt.NoFocus)
            self.setSizePolicy(QSizePolicy.MinimumExpanding, QSizePolicy.MinimumExpanding)
            self.setContextMenuPolicy(Qt.CustomContextMenu)

        def clickEvent(self, tile):
            self.parent().playRound(tile)

        def updateEvent(self, tile):
            self.setEnabled(tile.player is None)
            self.setText(self.playerSymbolMap[tile.player])
            self.update()

        def resizeEvent(self, resizeEvent):
            font = self.font()
            font.setBold(True)
            font.setPixelSize(0.50 * min(self.width(), self.height()))
            self.setFont(font)

        def sizeHint(self):
            return QSize(40, 40)

    def __init__(self):
        super(QTicTacToe, self).__init__()
        self.ticTacToe = TicTacToe()
        self.initUI()
        self.show()

    def initUI(self):
        self.setWindowTitle(self.tr("Tic-Tac-Toe"))
        layout = QGridLayout()
        layout.setSpacing(3)
        self.setLayout(layout)
        playerSymbolMap = {None: "",
                           self.ticTacToe.ai: "☓",
                           self.ticTacToe.player: "◯"}

        for tile in self.ticTacToe:
            button = QTicTacToe.QTileButton(playerSymbolMap)
            self.layout().addWidget(button, tile.row, tile.column)
            button.clicked.connect(lambda _, button=button, tile=tile: button.clickEvent(tile))
            tile.delegate = button

    def playRound(self, tile):
        QApplication.setOverrideCursor(Qt.WaitCursor)
        gameScore = self.ticTacToe.playRound(tile)
        QApplication.restoreOverrideCursor()
        if gameScore is not None:
            if gameScore == +1:
                QMessageBox.information(self, self.tr("Victory!"), self.tr("You won :)"), QMessageBox.Ok)
            if gameScore == 0:
                QMessageBox.warning(self, self.tr("Tie!"), self.tr("You tied :|"), QMessageBox.Ok)
            if gameScore == -1:
                QMessageBox.critical(self, self.tr("Defeat!"), self.tr("You lost :("), QMessageBox.Ok)
            self.ticTacToe.reset()

    def sizeHint(self):
        return QSize(180, 180)


class TestTicTacToe(unittest.TestCase):
    def testBasicAI(self):
        ticTacToe = TicTacToe.create(["☐◯☓",
                                      "◯☓☓",
                                      "◯☓◯"])
        score, tile = ticTacToe.ai.play(ticTacToe, ticTacToe.player)
        self.assertEqual((tile.row, tile.column), (0, 0))
        self.assertEqual(score, 0.0)

        ticTacToe = TicTacToe.create(["◯☓☐",
                                      "◯☓☐",
                                      "☐◯☓"])
        score, tile = ticTacToe.ai.play(ticTacToe, ticTacToe.player)
        self.assertEqual((tile.row, tile.column), (2, 0))
        self.assertEqual(score, 0.0)

        ticTacToe = TicTacToe.create(["☐☐☓",
                                      "◯☓☐",
                                      "◯☓◯"])
        score, tile = ticTacToe.ai.play(ticTacToe, ticTacToe.player)
        self.assertEqual((tile.row, tile.column), (0, 1))
        self.assertEqual(score, 1.0)

        ticTacToe = TicTacToe.create(["☐☐☓",
                                      "◯☐☐",
                                      "◯☓☐"])
        score, tile = ticTacToe.ai.play(ticTacToe, ticTacToe.player)
        self.assertEqual((tile.row, tile.column), (0, 0))

        ticTacToe = TicTacToe.create(["☓☓◯",
                                      "☐◯☐",
                                      "☐◯☓"])
        score, tile = ticTacToe.ai.play(ticTacToe, ticTacToe.player)
        self.assertEqual((tile.row, tile.column), (2, 0))
        self.assertEqual(score, 0.0)

    def testAIvsAI(self):
        x = TicTacToe.AI("☓")
        o = TicTacToe.AI("◯")
        ticTacToe = TicTacToe()

        while True:
            _, tile = x.play(ticTacToe, o)
            tile.set(x)
            score = tile.score(ticTacToe, x)
            if score is not None:
                break
            _, tile = o.play(ticTacToe, x)
            tile.set(o)
            score = tile.score(ticTacToe, o)
            if score is not None:
                break
        self.assertEqual(0, score, "AI vs AI game must always end up in a tie:\n" + str(ticTacToe))


if __name__ == "__main__":
    application = QApplication(sys.argv)
    qTicTacToe = QTicTacToe()
    sys.exit(application.exec_())
