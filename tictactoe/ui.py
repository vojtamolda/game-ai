from PySide2.QtWidgets import QApplication, QWidget, QPushButton, QGridLayout, QComboBox, QMessageBox, QDialog, \
                              QSizePolicy, QVBoxLayout, QHBoxLayout
from PySide2.QtWebEngineWidgets import QWebEngineView
from PySide2.QtGui import QResizeEvent
from PySide2.QtCore import Qt, QSize

from ai import RandomAI, MinimaxAI, MonteCarloSearchAI, ValueFunctionAI
from tictactoe import TicTacToe


class QTicTacToe(QWidget):
    AIs = {
        "Random AI": RandomAI,
        "Minimax AI": MinimaxAI,
        "Monte Carlo Search AI": MonteCarloSearchAI,
        "Value Function AI": ValueFunctionAI
    }

    class QTileButton(QPushButton):
        SymbolMap = {'-': " ", 'X': "☓", 'O': "◯"}

        def __init__(self, parent):
            super().__init__(parent)
            self.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)

        def setPlayer(self, player: TicTacToe.Player):
            if player is None:
                self.setEnabled(True)
                self.setText(self.SymbolMap['-'])
            else:
                self.setEnabled(False)
                self.setText(self.SymbolMap[player.symbol])
            self.update()

        def resizeEvent(self, resizeEvent: QResizeEvent):
            font = self.font()
            font.setBold(True)
            font.setPixelSize(round(0.50 * min(self.width(), self.height())))
            self.setFont(font)

        def sizeHint(self) -> QSize:
            return QSize(80, 80)

    class QHumanAI(TicTacToe.Player):
        tile = None

        def play(self, gameboard: TicTacToe.Gameboard):
            return self.tile

    def __init__(self):
        super().__init__()
        self.ticTacToe = None
        self.player, self.ai = None, None
        self.gridLayout = None
        self.initGame()
        self.initUI()
        self.show()

    def initGame(self):
        self.ai = QTicTacToe.QHumanAI('O')
        self.player = QTicTacToe.QHumanAI('X')
        self.ticTacToe = TicTacToe(x=self.player, o=self.ai)
        self.ticTacToe.delegate = self

    def initUI(self):
        self.setWindowTitle(self.tr("Tic-Tac-Toe"))
        widgetLayout = QVBoxLayout()
        aiSelectLayout = QHBoxLayout()
        self.gridLayout = QGridLayout()
        self.gridLayout.setSpacing(0)

        aiComboBox = QComboBox(self)
        aiComboBox.addItems([self.tr(ai) for ai in self.AIs])
        aiComboBox.currentTextChanged.connect(self.selectAI)
        aiComboBox.setCurrentText("Value Function AI")

        aiVisualizationButton = QPushButton(self)
        aiVisualizationButton.setFixedWidth(30)
        aiVisualizationButton.setText(self.tr("?"))
        aiVisualizationButton.clicked.connect(self.visualizeAI)

        aiSelectLayout.addWidget(aiComboBox)
        aiSelectLayout.addWidget(aiVisualizationButton)
        widgetLayout.addLayout(aiSelectLayout)
        widgetLayout.addLayout(self.gridLayout)
        self.setLayout(widgetLayout)
        self.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        self.setFixedSize(240, 280)

        for tile in self.ticTacToe.gameboard.tiles():
            tileButton = QTicTacToe.QTileButton(self)
            tileButton.clicked.connect(lambda chk=False, tl=tile: self.round(tl))
            self.gridLayout.addWidget(tileButton, tile.row, tile.column)

    def notify(self, player: TicTacToe.Player, tile: TicTacToe.Tile):
        tileButton = self.gridLayout.itemAtPosition(tile.row, tile.column).widget()
        tileButton.setPlayer(player)

    def round(self, tile: TicTacToe.Tile):
        QApplication.setOverrideCursor(Qt.WaitCursor)
        self.player.tile = tile
        outcome = self.ticTacToe.round(notify=True)
        QApplication.restoreOverrideCursor()
        if outcome is not None:
            if outcome == +1:
                QMessageBox.information(self, self.tr("Victory!"), self.tr("You won :)"), QMessageBox.Ok)
            if outcome == 0:
                QMessageBox.warning(self, self.tr("Tie!"), self.tr("You tied :|"), QMessageBox.Ok)
            if outcome == -1:
                QMessageBox.critical(self, self.tr("Defeat!"), self.tr("You lost :("), QMessageBox.Ok)
            self.ticTacToe.reset(notify=True)

    def selectAI(self, name: str):
        ArtificialIntelligence = QTicTacToe.AIs[name]
        self.ai = ArtificialIntelligence(self.ai.symbol, self.ai.index)
        self.ticTacToe.o = self.ai

    def visualizeAI(self):
        dialog = QDialog(self)
        dialog.setWindowTitle("AI Algorithm Visualization")
        dialog.setMinimumSize(800, 600)

        layout = QHBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        dialog.setLayout(layout)

        QApplication.setOverrideCursor(Qt.WaitCursor)
        browser = QWebEngineView(dialog)
        browser.setContextMenuPolicy(Qt.PreventContextMenu)
        svg = self.ai.visualize(self.ticTacToe.gameboard)
        browser.setContent(svg, 'image/svg+xml')
        layout.addWidget(browser)
        QApplication.restoreOverrideCursor()

        dialog.show()
