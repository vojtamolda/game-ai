import numpy as np


class GameOfLife:

    def __init__(self, size: tuple=(400, 400), fill_rate: int=0.50):
        self.world = (np.random.random(size=size) < fill_rate).astype(np.uint8)
        self.visualization = 255 * np.ones(shape=size, dtype=np.uint8)
        self.neighbors = np.zeros(shape=size, dtype=np.uint8)

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

    def visualize(self) -> np.array:
        self.visualization += (self.visualization < 255).astype(np.uint8)
        self.visualization = self.visualization.clip(128, 255)
        self.visualization[(self.world == 1)] = 0
        return self.visualization


class GrayScottDiffusion:

    def __init__(self, size: tuple=(400, 400), coeffs: dict=None):
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

    def visualize(self) -> np.array:
        min, max = self.v.min(), self.v.max()
        self.visualization = (255 * ((self.v - min) / (max - min))).astype(np.uint8)
        return self.visualization


if __name__ == '__main__':
    from PySide2.QtWidgets import QApplication
    import sys
    import ui

    application = QApplication(sys.argv)
    qGameOfLife = ui.QGameOfLife(size=(400, 400))
    sys.exit(application.exec_())
