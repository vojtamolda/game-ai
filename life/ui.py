from PySide2.QtWidgets import QWidget, QComboBox, QGraphicsScene, QGraphicsView, QVBoxLayout, QFrame, QSizePolicy
from PySide2.QtCore import Qt, QSize, QTimer
from PySide2.QtGui import QImage, QPixmap, QResizeEvent
import random

from life import GameOfLife, GrayScottDiffusion


class QGameOfLife(QWidget):

    Games = {
        "Game of Life": (GameOfLife, {'fill_rate': 0.50}),
        "Bacteria": (GrayScottDiffusion, {'coeffs': (0.16, 0.08, 0.035, 0.065)}),
        "Coral": (GrayScottDiffusion, {'coeffs': (0.16, 0.08, 0.062, 0.062)}),
        "Fingerprint": (GrayScottDiffusion, {'coeffs': (0.19, 0.05, 0.060, 0.062)}),
        "Spirals": (GrayScottDiffusion, {'coeffs': (0.10, 0.10, 0.018, 0.050)}),
        "Unstable": (GrayScottDiffusion, {'coeffs': (0.16, 0.08, 0.020, 0.055)}),
        "Worms": (GrayScottDiffusion, {'coeffs': (0.16, 0.08, 0.050, 0.065)}),
        "Zebrafish": (GrayScottDiffusion, {'coeffs': (0.16, 0.08, 0.035, 0.060)}),
    }

    def __init__(self, size=(400, 400)):
        super(QGameOfLife, self).__init__()
        self.size = size
        self.game = None
        self.initUI()
        self.show()

    def initUI(self):
        self.setWindowTitle(self.tr("Game of Life"))
        self.setLayout(QVBoxLayout())
        self.layout().setSpacing(0)
        self.layout().setContentsMargins(0, 0, 0, 0)

        self.comboBox = QComboBox()
        self.comboBox.addItems([*QGameOfLife.Games.keys()])
        self.comboBox.currentTextChanged.connect(self.select)
        self.layout().addWidget(self.comboBox)

        self.scene = QGraphicsScene()
        self.view = QGraphicsView(self.scene)
        self.view.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.view.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.view.setSizePolicy(QSizePolicy(QSizePolicy.Preferred, QSizePolicy.Preferred))
        self.view.setFrameShape(QFrame.NoFrame)
        self.layout().addWidget(self.view)

        self.item = None
        self.timer = QTimer()
        self.timer.setInterval(10)
        self.timer.timeout.connect(self.tick)
        initialGame = random.choice([*QGameOfLife.Games.keys()])
        self.select(initialGame)
        self.view.fitInView(self.item, Qt.KeepAspectRatioByExpanding)
        self.comboBox.setCurrentText(initialGame)

    def select(self, name: str):
        self.timer.stop()
        Game, args = QGameOfLife.Games[name]
        self.game = Game(self.size, **args)
        self.tick()
        self.timer.start()

    def tick(self):
        self.game.tick()
        bitmap = self.game.visualize()
        image = QImage(bitmap.data, bitmap.shape[1], bitmap.shape[0], QImage.Format_Grayscale8)
        self.scene.removeItem(self.item)
        pixmap = QPixmap.fromImage(image)
        self.item = self.scene.addPixmap(pixmap)

    def resizeEvent(self, event: QResizeEvent):
        self.view.fitInView(self.item, Qt.KeepAspectRatioByExpanding)

    def sizeHint(self) -> QSize:
        return QSize(self.size[0], self.size[1])
