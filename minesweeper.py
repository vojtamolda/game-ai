from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtGui import *
import random
import sys


class MineSweeper:
    class Tile:
        def __init__(self, row, column):
            self.row, self.column = row, column
            self.explosive = False
            self.delegate = None
            self.revealed = False
            self.marked = False
            self.bombs = None

        def __str__(self):
            if self.revealed and self.explosive:
                return "☀"
            if self.revealed and self.bombs > 0:
                return str(self.bombs)
            if self.marked:
                return "★"
            return " "

        def mark(self):
            self.marked = not self.marked
            self.notify()

        def reveal(self, mineSweeper, ignoreRecursive=False, ignoreMarked=False):
            if self.marked and not ignoreMarked:
                return
            self.revealed = True
            self.notify()
            if self.explosive:
                return
            if self.bombs == 0 and not ignoreRecursive:
                for neighbor in self.neighbors(mineSweeper):
                    if not neighbor.explosive and not neighbor.revealed:
                        neighbor.reveal(mineSweeper)

        def notify(self):
            if self.delegate is not None:
                self.delegate.moveEvent(self)

        def neighbors(self, mineSweeper):
            for diffRow, diffCol in [(+1, -1), (+1, 0), (+1, +1),
                                      (0, -1),           (0, +1),
                                     (-1, -1), (-1, 0), (-1, +1)]:
                neighborRow, neighborCol = self.row + diffRow, self.column + diffCol
                if (neighborRow, neighborCol) in mineSweeper:
                    yield mineSweeper[(neighborRow, neighborCol)]

        def reset(self):
            self.explosive = False
            self.revealed = False
            self.marked = False
            self.bombs = None
            self.notify()

        def count(self, mineSweeper):
            self.bombs = 0
            for neighbor in self.neighbors(mineSweeper):
                self.bombs += int(neighbor.explosive)

    def __init__(self, size, explosiveness):
        self.explosiveness = explosiveness
        self.size = size
        self.field = {}
        for row in range(self.size):
            for column in range(self.size):
                tile = MineSweeper.Tile(row, column)
                tile.explosive = random.random() <= self.explosiveness
                self.field[row, column] = tile
        for tile in self:
            tile.count(self)

    def __contains__(self, row_column):
        return row_column in self.field

    def __getitem__(self, row_column):
        return self.field[row_column]

    def __iter__(self):
        return self.field.values().__iter__()

    def __str__(self):
        string = ""
        for row in range(self.size):
            for column in range(self.size):
                string += str(self[row, column])
            string += "\n"
        return string

    def score(self):
        notRevealedTilesCount = 0
        for tile in self:
            if not tile.revealed and not tile.explosive:
                notRevealedTilesCount += 1
            if tile.revealed and tile.explosive:
                return -1
        if notRevealedTilesCount == 0:
            return 1
        return None

    def reveal(self):
        for tile in self:
            if tile.explosive:
                tile.reveal(self, True, True)

    def reset(self):
        for tile in self:
            tile.reset()
            tile.explosive = random.random() <= self.explosiveness
        for tile in self:
            tile.count(self)


class QMineSweeper(QWidget):
    class QTileButton(QPushButton):
        def __init__(self):
            super(QMineSweeper.QTileButton, self).__init__()
            self.setFocusPolicy(Qt.NoFocus)
            self.setContextMenuPolicy(Qt.CustomContextMenu)
            self.setSizePolicy(QSizePolicy.MinimumExpanding, QSizePolicy.MinimumExpanding)

        def clickEvent(self, tile):
            self.parent().reveal(tile)

        def menuEvent(self, tile):
            tile.mark()

        def resizeEvent(self, resizeEvent):
            font = self.font()
            font.setBold(True)
            font.setPixelSize(0.50 * min(self.width(), self.height()))
            self.setFont(font)

        def updateEvent(self, tile):
            self.setEnabled(not tile.revealed)
            self.setText(str(tile))

        def sizeHint(self):
            return QSize(35, 35)

    def __init__(self, size):
        super(QMineSweeper, self).__init__()
        self.size = size
        self.mineSweeper = MineSweeper(self.size, 0.1)
        self.initUI()
        self.show()

    def initUI(self):
        self.setWindowTitle(self.tr("Minesweeper"))
        layout = QGridLayout()
        layout.setSpacing(11)
        self.setLayout(layout)

        for tile in self.mineSweeper:
            button = QMineSweeper.QTileButton()
            self.layout().addWidget(button, tile.row, tile.column)
            button.clicked.connect(lambda _, button=button, tile=tile: button.clickEvent(tile))
            button.customContextMenuRequested.connect(lambda _, button=button, tile=tile: button.menuEvent(tile))
            tile.delegate = button

    def reveal(self, tile):
        tile.reveal(self.mineSweeper)
        gameScore = self.mineSweeper.score()
        if gameScore is not None:
            self.mineSweeper.reveal()
            if gameScore == +1:
                QMessageBox.information(self, self.tr("Victory!"), self.tr("You won :)"), QMessageBox.Ok)
            if gameScore == -1:
                QMessageBox.critical(self, self.tr("Defeat!"), self.tr("You lost :("), QMessageBox.Ok)
            self.mineSweeper.reset()

    def sizeHint(self):
        return QSize(300, 300)


if __name__ == "__main__":
    application = QApplication(sys.argv)
    qMineSweeper = QMineSweeper(10)
    sys.exit(application.exec_())
