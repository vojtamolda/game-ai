from PyQt5.QtWidgets import QApplication, QWidget, QComboBox, QGraphicsScene, QGraphicsView, QVBoxLayout, QFrame, QSizePolicy
from PyQt5.QtCore import Qt, QSize, QTimer
from PyQt5.QtGui import QImage, QPixmap
import numpy as np
import random
import sys


class GameOfLife:
    def __init__(self, size=(400, 400), timeout=50, fill_rate=0.50):
        self.world = (np.random.random(size=size) < fill_rate).astype(np.uint8)
        self.visualization = 255 * np.ones(shape=size, dtype=np.uint8)
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

        if self.delegate is not None:
            image = self.visualize()
            self.delegate.tickEvent(image)

    def visualize(self):
        self.visualization += (self.visualization < 255).astype(np.uint8)
        self.visualization = self.visualization.clip(128, 255)
        self.visualization[(self.world == 1)] = 0
        return QImage(self.visualization.data, self.visualization.shape[1], self.visualization.shape[0],
                      QImage.Format_Grayscale8)

    def stop(self):
        self.timer.stop()


class GrayScottDiffusion:
    def __init__(self, size=(400, 400), timeout=0, coeffs=None):
        self.u = np.ones(shape=size, dtype=np.double)
        self.v = np.zeros(shape=size, dtype=np.double)
        box_xrange = int(size[0] * 0.45), int(size[0] * 0.55)
        box_yrange = int(size[1] * 0.45), int(size[1] * 0.55)
        self.u[box_xrange[0]:box_xrange[1], box_yrange[0]:box_yrange[1]] = 0.50
        self.v[box_xrange[0]:box_xrange[1], box_yrange[0]:box_yrange[1]] = 0.25
        self.u += 0.05 * np.random.uniform(-1, +1, size)
        self.v += 0.05 * np.random.uniform(-1, +1, size)
        if coeffs is None:
            self.cu, self.cv, self.f, self.k = 0.10, 0.10, 0.018, 0.050
        else:
            self.cu, self.cv, self.f, self.k = coeffs
        self.delegate = None
        self.timer = QTimer()
        self.timer.setInterval(timeout)
        self.timer.timeout.connect(self.tick)

    def start(self):
        self.timer.start()

    def tick(self):
        laplace_u = np.zeros(shape=self.u.shape)
        laplace_u[+1:-1, +1:-1] += self.u[+1:-1, +2:] + \
            self.u[:-2, +1:-1] - 4*self.u[+1:-1, +1:-1] + self.u[+2:, +1:-1] + \
                                   self.u[+1:-1, :-2]
        laplace_v = np.zeros(shape=self.v.shape)
        laplace_v[+1:-1, +1:-1] += self.v[+1:-1, +2:] + \
            self.v[:-2, +1:-1] - 4*self.v[+1:-1, +1:-1] + self.v[+2:, +1:-1] + \
                                   self.v[+1:-1, :-2]
        uvv = self.u * self.v * self.v
        self.u += self.cu * laplace_u - uvv + self.f * (1 - self.u)
        self.v += self.cv * laplace_v + uvv - (self.f + self.k) * self.v

        if self.delegate is not None:
            image = self.visualize()
            self.delegate.tickEvent(image)

    def visualize(self):
        min, max = self.v.min(), self.v.max()
        self.visualization = (255 * ((self.v - min) / (max - min))).astype(np.uint8)
        return QImage(self.visualization.data, self.visualization.shape[1], self.visualization.shape[0],
                      QImage.Format_Grayscale8)

    def stop(self):
        self.timer.stop()


class QGameOfLife(QWidget):
    games = {
        "Game of Life": lambda size: GameOfLife(size=size),
        "Bacteria": lambda size: GrayScottDiffusion(size=size, coeffs=(0.16, 0.08, 0.035, 0.065)),
        "Coral": lambda size: GrayScottDiffusion(size=size, coeffs=(0.16, 0.08, 0.062, 0.062)),
        "Fingerprint": lambda size: GrayScottDiffusion(size=size, coeffs=(0.19, 0.05, 0.060, 0.062)),
        "Spirals": lambda size: GrayScottDiffusion(size=size, coeffs=(0.10, 0.10, 0.018, 0.050)),
        "Unstable": lambda size: GrayScottDiffusion(size=size, coeffs=(0.16, 0.08, 0.020, 0.055)),
        "Worms": lambda size: GrayScottDiffusion(size=size, coeffs=(0.16, 0.08, 0.050, 0.065)),
        "Zebrafish": lambda size: GrayScottDiffusion(size=size, coeffs=(0.16, 0.08, 0.035, 0.060)),
    }

    def __init__(self, size=(400, 400)):
        super(QGameOfLife, self).__init__()
        self.game = None
        self.size = size
        self.initUI()
        self.show()

    def initUI(self):
        self.setWindowTitle(self.tr("Game of Life"))
        self.setLayout(QVBoxLayout())
        self.layout().setSpacing(0)
        self.layout().setContentsMargins(0, 0, 0, 0)

        self.comboBox = QComboBox()
        self.comboBox.addItems(self.games.keys())
        self.comboBox.currentTextChanged.connect(self.gameEvent)
        self.layout().addWidget(self.comboBox)

        self.scene = QGraphicsScene()
        self.item = None
        self.view = QGraphicsView(self.scene)
        self.view.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.view.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.view.setSizePolicy(QSizePolicy(QSizePolicy.Preferred, QSizePolicy.Preferred));
        self.view.setFrameShape(QFrame.NoFrame)
        self.layout().addWidget(self.view)

        self.tickEvent(QImage())
        self.view.fitInView(self.item, Qt.KeepAspectRatioByExpanding)
        self.comboBox.setCurrentText(random.choice(list(self.games.keys())))

    def gameEvent(self, name):
        if self.game is not None: self.game.stop()
        constructor = self.games[name]
        self.game = constructor(self.size)
        self.game.delegate = self
        self.game.start()

    def tickEvent(self, image):
        self.scene.removeItem(self.item)
        pixmap = QPixmap.fromImage(image)
        self.item = self.scene.addPixmap(pixmap)

    def resizeEvent(self, QResizeEvent):
        self.view.fitInView(self.item, Qt.KeepAspectRatioByExpanding)

    def sizeHint(self):
        return QSize(self.size[0], self.size[1])


if __name__ == "__main__":
    application = QApplication(sys.argv)
    qGameOfLife = QGameOfLife(size=(400, 400))
    sys.exit(application.exec_())
