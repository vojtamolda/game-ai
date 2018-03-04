from PyQt5.QtWidgets import QApplication, QWidget, QPushButton, QComboBox, QGridLayout, QMessageBox, \
                            QSizePolicy, QVBoxLayout
from PyQt5.QtGui import QPainter, QBrush, QPen, QPalette, QPaintEvent
from PyQt5.QtCore import Qt, QPoint, QSize, QEvent

from fourplay import FourPlay
from ai import DepthFirstSearchAI


class QFourPlay(QWidget):

    class QDiscButton(QPushButton):
        ColorMap = {'-': (QPalette.Dark, QPalette.Background),
                    'O': (QPalette.Highlight, QPalette.Highlight),
                    'X': (QPalette.Dark, QPalette.Dark)}

        def __init__(self, qFourPlay: 'QFourPlay'):
            super(QFourPlay.QDiscButton, self).__init__(qFourPlay)
            self.qFourPlay = qFourPlay
            self.highlight = False
            self.playable = False
            self.checked = False
            self.color = None
            self.setSizePolicy(QSizePolicy.MinimumExpanding, QSizePolicy.MinimumExpanding)
            self.setFocusPolicy(Qt.NoFocus)
            self.setMouseTracking(True)

        def marked(self, disc: FourPlay.Disc):
            self.checked = disc.marked
            self.color = self.ColorMap[str(disc)]
            self.playable = disc in self.qFourPlay.fourPlay.frontier
            self.update()

        def clickEvent(self, disc: FourPlay.Disc):
            self.leaveEvent(QEvent.None_)
            self.qFourPlay.round(disc)
            self.enterEvent(QEvent.None_)

        def enterEvent(self, event: QEvent):
            if self.playable is True:
                self.highlight = True
                self.update()

        def leaveEvent(self, event: QEvent):
            if self.playable is True:
                self.highlight = False
                self.update()

        def paintEvent(self, paintEvent: QPaintEvent):
            painter = QPainter(self)
            painter.setBackgroundMode(Qt.TransparentMode)
            painter.setRenderHint(QPainter.Antialiasing)
            brush = QBrush()
            brush.setStyle(Qt.SolidPattern)
            pen = QPen()
            pen.setJoinStyle(Qt.RoundJoin)
            pen.setCapStyle(Qt.RoundCap)

            center = QPoint(self.width() // 2, self.height() // 2)
            radius = 0.45 * min(self.width(), self.height())

            pen.setColor(self.palette().color(self.color[0]))
            brush.setColor(self.palette().color(self.color[1]))
            if self.highlight is True:
                pen.setColor(self.palette().color(QPalette.Highlight))
            pen.setWidth(round(0.15 * radius))
            painter.setBrush(brush)
            painter.setPen(pen)
            painter.drawEllipse(center, radius, radius)

            if self.checked is True:
                brush.setColor(self.palette().color(QPalette.Background))
                pen.setColor(self.palette().color(QPalette.Background))
                painter.setPen(pen)
                painter.setBrush(brush)
                painter.drawEllipse(center, 0.40 * radius, 0.40 * radius)
            del painter, brush, pen

        def sizeHint(self) -> QSize:
            return QSize(40, 40)

    class QPlayer(FourPlay.Player):
        disc = None

        def play(self) -> FourPlay.Disc:
            return self.fourplay.frontier[self.disc.column]

    AIs = {"Depth First Search AI": DepthFirstSearchAI}

    def __init__(self):
        super(QFourPlay, self).__init__()
        self.fourPlay = None
        self.player, self.ai = None, None
        self.initGame()
        self.initUI()
        self.show()

    def initGame(self):
        self.player = QFourPlay.QPlayer('O')
        ArtificialIntelligence = QFourPlay.AIs["Depth First Search AI"]
        self.ai = ArtificialIntelligence('X')
        self.fourPlay = FourPlay(o=self.player, x=self.ai)

    def initUI(self):
        self.setWindowTitle(self.tr("Fourplay"))
        layout = QVBoxLayout()
        self.setLayout(layout)
        discGridLayout = QGridLayout()
        discGridLayout.setSpacing(4)
        aiComboBox = QComboBox(self)
        aiComboBox.addItems([self.tr(ai) for ai in self.AIs])
        aiComboBox.currentTextChanged.connect(self.selectAI)
        layout.addWidget(aiComboBox)
        layout.addLayout(discGridLayout)

        for disc in self.fourPlay:
            qDisc = QFourPlay.QDiscButton(self)
            discGridLayout.addWidget(qDisc, disc.row, disc.column)
            qDisc.clicked.connect(lambda _, qDisc=qDisc, disc=disc: qDisc.clickEvent(disc))
            qDisc.marked(disc)
            disc.delegate = qDisc

    def round(self, disc: FourPlay.Disc):
        QApplication.setOverrideCursor(Qt.WaitCursor)
        self.player.disc = disc
        score = self.fourPlay.round(True)
        QApplication.restoreOverrideCursor()
        if score is not None:
            if score == +1:
                QMessageBox.information(self, self.tr("Victory!"), self.tr("You won :)"), QMessageBox.Ok)
            if score == 0:
                QMessageBox.warning(self, self.tr("Tie!"), self.tr("You tied :|"), QMessageBox.Ok)
            if score == -1:
                QMessageBox.critical(self, self.tr("Defeat!"), self.tr("You lost :("), QMessageBox.Ok)
            self.fourPlay.reset(True)

    def selectAI(self, name: str):
        ArtificialIntelligence = QFourPlay.AIs[name]
        self.ai = ArtificialIntelligence(self.fourPlay, self.ai.symbol)
        self.fourPlay.x = self.ai

    def sizeHint(self) -> QSize:
        return QSize(300, 300)
