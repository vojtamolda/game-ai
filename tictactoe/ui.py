from PySide2.QtWidgets import QApplication, QWidget, QPushButton, QGridLayout, QMessageBox, QSizePolicy, QVBoxLayout, \
                              QComboBox
from PySide2.QtCore import Qt, QSize
from PySide2.QtGui import QResizeEvent

from tictactoe import TicTacToe
from ai import DepthFirstSearchAI


class QTicTacToe(QWidget):

    class QTileButton(QPushButton):
        SymbolMap = {'-': " ", 'O': "◯", 'X': "☓"}

        def __init__(self, parent, tile):
            super(QTicTacToe.QTileButton, self).__init__(parent)
            self.tile = tile
            self.setFocusPolicy(Qt.NoFocus)
            self.setSizePolicy(QSizePolicy.MinimumExpanding, QSizePolicy.MinimumExpanding)
            self.setContextMenuPolicy(Qt.CustomContextMenu)

        def clickEvent(self):
            self.parent().round(self.tile)
            self.repaint()

        def marked(self):
            self.setEnabled(self.tile.player is None)
            self.setText(self.SymbolMap[str(self.tile)])
            self.update()

        def resizeEvent(self, resizeEvent: QResizeEvent):
            font = self.font()
            font.setBold(True)
            font.setPixelSize(round(0.50 * min(self.width(), self.height())))
            self.setFont(font)

        def sizeHint(self) -> QSize:
            return QSize(40, 40)

    class QPlayer(TicTacToe.Player):
        tile = None

        def play(self):
            return self.tile

    AIs = {"Depth First Search AI": DepthFirstSearchAI}

    def __init__(self):
        super(QTicTacToe, self).__init__()
        self.ticTacToe = None
        self.player, self.ai = None, None
        self.initGame()
        self.initUI()
        self.show()

    def initGame(self):
        self.player = QTicTacToe.QPlayer('O')
        ArtificialIntelligence = QTicTacToe.AIs["Depth First Search AI"]
        self.ai = ArtificialIntelligence('X')
        self.ticTacToe = TicTacToe(o=self.player, x=self.ai)

    def initUI(self):
        self.setWindowTitle(self.tr("Tic-Tac-Toe"))
        layout = QVBoxLayout()
        self.setLayout(layout)
        gridLayout = QGridLayout()
        gridLayout.setSpacing(3)
        aiComboBox = QComboBox(self)
        aiComboBox.addItems([self.tr(ai) for ai in self.AIs])
        aiComboBox.currentTextChanged.connect(self.selectAI)
        layout.addWidget(aiComboBox)
        layout.addLayout(gridLayout)

        for tile in self.ticTacToe:
            button = QTicTacToe.QTileButton(self, tile)
            gridLayout.addWidget(button, tile.row, tile.column)
            button.clicked.connect(button.clickEvent)
            tile.delegate = button

    def round(self, tile: TicTacToe.Tile):
        QApplication.setOverrideCursor(Qt.WaitCursor)
        self.player.tile = tile
        score = self.ticTacToe.round(True)
        QApplication.restoreOverrideCursor()
        if score is not None:
            if score == +1:
                QMessageBox.information(self, self.tr("Victory!"), self.tr("You won :)"), QMessageBox.Ok)
            if score == 0:
                QMessageBox.warning(self, self.tr("Tie!"), self.tr("You tied :|"), QMessageBox.Ok)
            if score == -1:
                QMessageBox.critical(self, self.tr("Defeat!"), self.tr("You lost :("), QMessageBox.Ok)
            self.ticTacToe.reset(True)

    def selectAI(self, name: str):
        ArtificialIntelligence = QTicTacToe.AIs[name]
        self.ai = ArtificialIntelligence(self.ticTacToe, self.ai.symbol)
        self.ticTacToe.x = self.ai

    def sizeHint(self) -> QSize:
        return QSize(180, 220)
