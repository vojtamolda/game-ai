from PySide2.QtWidgets import QWidget, QPushButton, QMessageBox, QGridLayout, QSizePolicy
from PySide2.QtGui import QResizeEvent
from PySide2.QtCore import Qt, QSize

from minesweeper import MineSweeper


class QMineSweeper(QWidget):

    class QTile(QPushButton):
        def __init__(self, mineSweeper: 'QMineSweeper', tile: MineSweeper.Tile):
            super(QMineSweeper.QTile, self).__init__()
            self.setFocusPolicy(Qt.NoFocus)
            self.setContextMenuPolicy(Qt.CustomContextMenu)
            self.setSizePolicy(QSizePolicy.MinimumExpanding, QSizePolicy.MinimumExpanding)
            self.mineSweeper = mineSweeper
            self.marked = False
            self.tile = tile

        def leftClick(self):
            if self.marked:
                return
            self.tile.reveal()
            self.mineSweeper.score()
            self.repaint()

        def rightClick(self):
            self.marked = not self.marked
            self.refresh()

        def resizeEvent(self, resizeEvent: QResizeEvent):
            font = self.font()
            font.setBold(True)
            font.setPixelSize(round(0.50 * min(self.width(), self.height())))
            self.setFont(font)

        def refresh(self):
            self.setEnabled(not self.tile.revealed)
            text = "★" if self.marked else str(self.tile)
            self.setText(text)

        def sizeHint(self) -> QSize:
            return QSize(40, 40)

    def __init__(self, size: int):
        super(QMineSweeper, self).__init__()
        self.size = size
        self.mineSweeper = MineSweeper(self.size, 0.10)
        self.initUI()
        self.show()

    def initUI(self):
        self.setWindowTitle(self.tr("Minesweeper"))
        layout = QGridLayout()
        layout.setSpacing(5)
        self.setLayout(layout)

        for tile in self.mineSweeper:
            qTile = QMineSweeper.QTile(self, tile)
            layout.addWidget(qTile, tile.row, tile.column)
            qTile.clicked.connect(qTile.leftClick)
            qTile.customContextMenuRequested.connect(qTile.rightClick)
            tile.delegate = qTile

    def score(self):
        score = self.mineSweeper.score()
        if score is not None:
            self.mineSweeper.reveal()
            if score == +1:
                QMessageBox.information(self, self.tr("Victory!"), self.tr("You won :)"), QMessageBox.Ok)
            if score == -1:
                QMessageBox.critical(self, self.tr("Defeat!"), self.tr("You lost :("), QMessageBox.Ok)
            for tile in self.mineSweeper:
                tile.delegate.marked = False
            self.mineSweeper.reset()

    def sizeHint(self) -> QSize:
        return QSize(300, 300)
