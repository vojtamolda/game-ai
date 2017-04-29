from PyQt5.QtWidgets import QApplication, QWidget, QGraphicsScene, QGraphicsView, QGridLayout, QFrame
from PyQt5.QtCore import Qt, QSize, QTimer
from PyQt5.QtGui import QImage, QPixmap
import numpy as np
import sys


class GameOfLife:
    def __init__(self, size=(400, 400), timeout=50, fill_rate=0.25):
        self.world = (np.random.random(size=size) < fill_rate).astype(np.uint8)
        self.neighbors = np.zeros(shape=size, dtype=np.uint8)
        self.delegate = None
        self.timer = QTimer()
        self.timer.setInterval(timeout)
        self.timer.timeout.connect(self.tick)

    def start(self):
        self.timer.start()

    def tick(self):
        self.neighbors[:, :] = 0
        self.neighbors[+1:-1, +1:-1] += \
                self.world[  :-2, :-2] + self.world[  :-2, +1:-1] + self.world[  :-2, +2:] + \
                self.world[+1:-1, :-2]                            + self.world[+1:-1, +2:] + \
                self.world[+2:,   :-2] + self.world[+2:  , +1:-1] + self.world[+2:  , +2:]
        birth = ((self.neighbors == 3) & (self.world == 0))
        survive = (((self.neighbors == 2) | (self.neighbors == 3)) & (self.world == 1))
        self.world[:, :] = 0
        self.world[birth | survive] = 1
        if self.delegate is not None: self.delegate.tickEvent(self.world)

    def stop(self):
        self.timer.stop()


class QGameOfLife(QWidget):
    def __init__(self, size=(400, 400)):
        super(QGameOfLife, self).__init__()
        self.gameOfLife = GameOfLife(size=size, timeout=10, fill_rate=0.50)
        self.gameOfLife.delegate = self
        self.gameOfLife.start()
        self.size = size
        self.initUI()
        self.show()

    def initUI(self):
        self.setWindowTitle(self.tr("Game of Life"))
        self.setLayout(QGridLayout())
        self.layout().setSpacing(0)
        self.layout().setContentsMargins(0, 0, 0, 0)

        self.scene = QGraphicsScene()
        self.item = None
        self.view = QGraphicsView(self.scene)
        self.view.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.view.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.view.setFrameShape(QFrame.NoFrame)
        self.layout().addWidget(self.view)
        self.world = np.ones(shape=self.size, dtype=np.uint8) * 255
        self.tickEvent(self.world)

    def tickEvent(self, world):
        self.world += (self.world < np.iinfo(self.world.dtype).max)
        self.world = self.world.clip(128, np.iinfo(self.world.dtype).max)
        self.world[(world == 1)] = 0
        self.scene.removeItem(self.item)
        image = QImage(self.world.data, self.size[1], self.size[0], QImage.Format_Grayscale8)
        pixmap = QPixmap.fromImage(image)
        self.item = self.scene.addPixmap(pixmap)

    def resizeEvent(self, QResizeEvent):
        self.view.fitInView(self.item, Qt.KeepAspectRatioByExpanding)

    def sizeHint(self):
        return self.layout().sizeHint()


if __name__ == "__main__":
    application = QApplication(sys.argv)
    qGameOfLife = QGameOfLife(size=(400, 400))
    sys.exit(application.exec_())
