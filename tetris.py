from PyQt5.QtCore import Qt, QTimer, QSize, QPointF, QRectF, QPropertyAnimation, QEasingCurve, \
                         QSequentialAnimationGroup, QAbstractAnimation
from PyQt5.QtWidgets import QApplication, QWidget, QFrame, QMessageBox, QGraphicsScene, \
                            QGraphicsView, QGraphicsObject, QGridLayout
from PyQt5.QtGui import QPainter, QPen, QBrush, QColor, QTransform
import random
import sys


class Tetris:
    class Tetritile:
        def __init__(self, tetris, tetrimino, row, column, rotation):
            self.tetris = tetris
            self.delegate = None
            self.tetrimino = tetrimino
            self.rotation = rotation
            self.row, self.column = row, column
            if self.tetris[self.row, self.column] is None:
                self.tetris[self.row, self.column] = self
            else:
                raise IndexError("Game Over")

        def move(self, tetrimino, row, column, rotation):
            try:
                destination = self.tetris[row, column]
            except KeyError:
                return False
            if destination in tetrimino or destination is None:
                if self.tetris[self.row, self.column] == self:
                    self.tetris[self.row, self.column] = None
                self.row, self.column = row, column
                self.rotation = rotation
                self.tetris[self.row, self.column] = self
                return True
            else:
                return False

        def collapse(self):
            if self.tetris[self.row, self.column] == self:
                self.tetris[self.row, self.column] = None
            self.collapsed()

        def shift(self, delta):
            if self.tetris[self.row, self.column] == self:
                self.tetris[self.row, self.column] = None
            self.row, self.column = self.row + delta, self.column
            self.tetris[self.row, self.column] = self
            self.shifted()

        def moved(self, notify=True):
            if notify is True:
                self.delegate.moveEvent(self)

        def dropped(self):
            self.delegate.dropEvent(self)

        def collapsed(self):
            self.delegate.collapseEvent(self)

        def shifted(self):
            self.delegate.shiftEvent(self)

    class Tetrimino:
        shape = []
        center = (0, 0)

        def __init__(self, tetris, row, column):
            self.row, self.column = row, column
            self.rotation = 0

            self.tetritiles = {}
            for row, line in enumerate(self.shape):
                for column, symbol in filter(lambda tpl: tpl[1] == "☒", enumerate(line)):
                    local = row - self.center[0], column - self.center[1]
                    tetritile = Tetris.Tetritile(tetris, self, self.row + local[0], self.column + local[1], self.rotation)
                    self.tetritiles[tetritile] = local

        def __contains__(self, item):
            return item in self.tetritiles.keys()

        def __iter__(self):
            return self.tetritiles.keys().__iter__()

        def moveLeft(self):
            return self.move(self.row, self.column - 1, self.rotation)

        def moveRight(self):
            return self.move(self.row, self.column + 1, self.rotation)

        def moveUp(self):
            return self.move(self.row - 1, self.column, self.rotation)

        def moveDown(self):
            return self.move(self.row + 1, self.column, self.rotation)

        def rotateLeft(self):
            return self.move(self.row, self.column, self.rotation - 90)

        def rotateRight(self):
            return self.move(self.row, self.column, self.rotation + 90)

        def drop(self):
            while self.move(self.row + 1, self.column, self.rotation, False) is True:
                pass
            for tetritile in self:
                tetritile.dropped()
            return False

        def move(self, row, column, rotation, notify=True):
            for tetritile, local in self.tetritiles.items():
                rotated = self.rotate(rotation, local)
                if tetritile.move(self, row + rotated[0], column + rotated[1], rotation) is False:
                    break
            else:
                for tetritile in self:
                    tetritile.moved()
                self.row, self.column = row, column
                self.rotation = rotation
                return True
            for tetritile, local in self.tetritiles.items():
                rotated = self.rotate(self.rotation, local)
                tetritile.move(self, self.row + rotated[0], self.column + rotated[1], self.rotation)
            return False

        def rotate(self, rotation, row_column):
            from math import sin, cos, radians
            alpha = radians(rotation)
            row    = cos(alpha) * row_column[0] - sin(alpha) * row_column[1]
            columm = sin(alpha) * row_column[0] + cos(alpha) * row_column[1]
            return round(row), round(columm)


    class I(Tetrimino):
        shape = ["☒☒☒☒"]
        center = (0, 1)

    class J(Tetrimino):
        shape = ["☒☒☒",
                 "☐☐☒"]
        center = (0, 1)

    class L(Tetrimino):
        shape = ["☒☒☒",
                 "☒☐☐"]
        center = (0, 1)

    class O(Tetrimino):
        shape = ["☒☒",
                 "☒☒"]
        center = (0, 0)

    class S(Tetrimino):
        shape = ["☐☒☒",
                 "☒☒☐"]
        center = (0, 1)

    class T(Tetrimino):
        shape = ["☒☒☒",
                 "☐☒☐"]
        center = (0, 1)

    class Z(Tetrimino):
        shape = ["☒☒☐",
                 "☐☒☒"]
        center = (0, 1)

    def __init__(self):
        self.rows, self.columns = (20, 10)
        self.spawnRow, self.spawnColumn = (0, 4)
        self.delegate = None
        self.score = 0

        self.timer = QTimer()
        self.timer.setInterval(350)
        self.timer.timeout.connect(self.moveDown)
        self.timer.stop()

        self.tiles = {}
        for row in range(self.rows):
            for column in range(self.columns):
                self[row, column] = None

    def __getitem__(self, row_column):
        return self.tiles[row_column]

    def __setitem__(self, row_column, tetritile):
        self.tiles[row_column] = tetritile

    def __iter__(self):
        return self.tiles.values().__iter__()

    def __str__(self):
        string = ""
        for row in range(self.rows):
            for column in range(self.columns):
                string += "☒" if self[row, column] is not None else "☐"
            string +="\n"
        return string

    def spawn(self):
        randomTetrimino = random.choice([Tetris.I, Tetris.J, Tetris.L, Tetris.O, Tetris.S, Tetris.T, Tetris.Z])
        try:
            self.falling = randomTetrimino(self, self.spawnRow, self.spawnColumn)
            self.delegate.appearEvent(self.falling)
            self.timer.start()
        except IndexError:
            self.delegate.gameOverEvent(self.score)

    def moveLeft(self):
        if self.falling.moveLeft() is False:
            self.check()

    def moveRight(self):
        if self.falling.moveRight() is False:
            self.check()

    def moveDown(self):
        if self.falling.moveDown() is False:
            self.timer.stop()
            self.check()
            self.spawn()

    def rotate(self):
        if self.falling.rotateRight() is True:
            self.check()

    def drop(self):
        self.falling.drop()
        self.timer.stop()
        self.check()
        self.spawn()

    def check(self):
        countColumns = [0] * self.rows
        for row, column in self.tiles.keys():
            if self[row, column] is not None:
                countColumns[row] += 1
        collapsedRows = []
        for row, count in enumerate(countColumns):
            if count == self.columns:
                collapsedRows.append(row)

        if len(collapsedRows) > 0:
            self.collapse(collapsedRows)
            self.shift(collapsedRows)
            self.score += len(collapsedRows)
            self.delegate.scoreEvent(self.score)

    def collapse(self, collapsedRows):
        for collapseRow in reversed(sorted(collapsedRows)):
            for column in range(self.columns):
                self[collapseRow, column].collapse()

    def shift(self, collapsedRows):
        for collapseRow in reversed(range(min(collapsedRows))):
            for column in range(self.columns):
                if self[collapseRow, column] is not None:
                    self[collapseRow, column].shift(len(collapsedRows))

    def restart(self):
        self.timer.stop()
        for row, column in self.tiles.keys():
            if self[row, column] is not None:
                self.delegate.disappearEvent(self[row, column])
                self[row, column] = None
        self.score = 0
        self.delegate.scoreEvent(self.score)
        self.spawn()


class QTetris(QWidget):
    class QTetritile(QGraphicsObject):
        colorMap = {Tetris.I: QColor("#53bbf4"), Tetris.J: QColor("#e25fb8"), Tetris.L: QColor("#ffac00"),
                    Tetris.O: QColor("#ecff2e"), Tetris.S: QColor("#97eb00"), Tetris.T: QColor("#ff85cb"),
                    Tetris.Z: QColor("#ff5a48")}
        def __init__(self, tetris, tetritile):
            super(QTetris.QTetritile, self).__init__()
            tetritile.delegate = self
            self.color = self.colorMap[type(tetritile.tetrimino)]
            self.tetris = tetris
            self.moveAnimation = QSequentialAnimationGroup()
            self.dropAnimation = QPropertyAnimation(self, b"pos")
            self.collapseAnimation = QPropertyAnimation(self, b"pos")
            self.shiftAnimation = QPropertyAnimation(self, b"pos")
            self.collapseAnimation.finished.connect(lambda tetritile=tetritile: self.tetris.disappearEvent(tetritile))
            self.tetris.scene.addItem(self)
            self.setPos(QPointF(0, 4))
            self.moveEvent(tetritile)

        def moveEvent(self, tetritile):
            translation = QPropertyAnimation(self, b"pos")
            start, end = self.pos(), QPointF(tetritile.row, tetritile.column)
            curve, speed, delay = QEasingCurve.OutBack, 1 / 50, -1
            self.animate(translation, start, end, curve, speed, delay)

            rotation = QPropertyAnimation(self, b"rotation")
            start, end = self.rotation(), tetritile.rotation
            curve, speed, delay = QEasingCurve.OutBack, 1, -1
            self.animate(rotation, start, end, curve, speed, delay)
            rotation.setDuration(translation.duration())

            self.moveAnimation.clear()
            self.moveAnimation.addAnimation(translation)
            self.moveAnimation.addAnimation(rotation)
            self.moveAnimation.start()

        def dropEvent(self, tetritile):
            start, end = self.pos(), QPointF(tetritile.row, tetritile.column)
            curve, speed, delay = QEasingCurve.OutBounce, 1 / 50, 0
            self.animate(self.dropAnimation, start, end, curve, speed, delay)

        def collapseEvent(self, tetritile):
            start, end = self.pos(), QPointF(tetritile.row, tetritile.column + self.tetris.tetris.columns + 5)
            curve, speed, delay = QEasingCurve.InOutExpo, 1 / 50, 800
            if self.dropAnimation.state() == QAbstractAnimation.Running:
                start = self.dropAnimation.endValue()
            self.animate(self.collapseAnimation, start, end, curve, speed, delay)

        def shiftEvent(self, tetritile):
            start, end = self.pos(), QPointF(tetritile.row, tetritile.column)
            curve, speed, delay = QEasingCurve.OutBounce, 1 / 100, 1200
            if self.dropAnimation.state() == QAbstractAnimation.Running:
                start = self.dropAnimation.endValue()
            self.animate(self.shiftAnimation, start, end, curve, speed, delay)

        def paint(self, painter, styleOption, widget=None):
            pen = QPen()
            pen.setWidthF(0.05)
            pen.setColor(Qt.darkGray)
            painter.setPen(pen)
            brush = QBrush()
            brush.setColor(self.color)
            brush.setStyle(Qt.SolidPattern)
            painter.setBrush(brush)
            topLeft = QPointF(0, 0)
            bottomRight = QPointF(1, 1)
            rectangle = QRectF(topLeft, bottomRight)
            rectangle.translate(-0.5, -0.5)
            painter.drawRect(rectangle)

        def animate(self, animation, start, end, curve=QEasingCurve.Linear, speed=1/50, delay=-1):
            animation.setStartValue(start)
            animation.setEndValue(end)
            animation.setEasingCurve(curve)
            try:
                animation.setDuration((end - start).manhattanLength() / speed)
            except AttributeError:
                animation.setDuration(abs(end - start) / speed)
            if delay == 0:
                animation.start()
            if delay > 0:
                QTimer.singleShot(delay, animation.start)

        def boundingRect(self):
            topLeft = QPointF(0, 0)
            bottomRight = QPointF(1, 1)
            rectangle = QRectF(topLeft, bottomRight)
            rectangle.translate(-0.5, -0.5)
            return rectangle

    class QTetriscene(QGraphicsScene):
        def __init__(self, tetris):
            super(QTetris.QTetriscene, self).__init__()
            self.tetris = tetris

            pen = QPen()
            pen.setWidthF(0.05)
            pen.setColor(Qt.lightGray)
            brush = QBrush(Qt.NoBrush)
            rect = QRectF(0, 0, tetris.rows, tetris.columns)
            rect.translate(-0.5, -0.5)
            self.setSceneRect(rect)
            self.addRect(rect, pen, brush)
            self.setBackgroundBrush(self.palette().window())

            for column in range(0, tetris.columns, 2):
                pen = QPen(Qt.NoPen)
                brush = QBrush(Qt.SolidPattern)
                brush.setColor(Qt.lightGray)
                topLeft = QPointF(0, column)
                bottomRight = QPointF(tetris.rows, column + 1)
                rectangle = QRectF(topLeft, bottomRight)
                rectangle.translate(-0.5, -0.5)
                self.addRect(rectangle, pen, brush)

        def mouseMoveEvent(self, sceneMouseEvent):
            mousePoint = sceneMouseEvent.scenePos()
            mouseRow, mouseColumn = round(mousePoint.x()), round(mousePoint.y())
            row, column = self.tetris.falling.row, self.tetris.falling.column
            if mouseColumn - column > 0:
                self.tetris.moveRight()
            if mouseColumn - column < 0:
                self.tetris.moveLeft()

        def mouseReleaseEvent(self, sceneMouseEvent):
            if sceneMouseEvent.button() == Qt.LeftButton:
                self.tetris.drop()
            if sceneMouseEvent.button() == Qt.RightButton:
                self.tetris.rotate()

        def wheelEvent(self, sceneWheelEvent):
            if sceneWheelEvent.delta() > 10:
                self.tetris.moveDown()

        def keyReleaseEvent(self, sceneKeyEvent):
            if sceneKeyEvent.key() == Qt.Key_Left:
                self.tetris.moveLeft()
            if sceneKeyEvent.key() == Qt.Key_Right:
                self.tetris.moveRight()
            if sceneKeyEvent.key() == Qt.Key_Down:
                self.tetris.moveDown()
            if sceneKeyEvent.key() == Qt.Key_Up:
                self.tetris.rotate()

    class QTetriview(QGraphicsView):
        def __init__(self, scene):
            super(QTetris.QTetriview, self).__init__()
            self.setTransform(QTransform().rotate(+90).scale(+1, -1))
            self.setMinimumSize(100, 200)
            self.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
            self.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
            self.setRenderHints(QPainter.Antialiasing)
            self.setFrameStyle(QFrame.NoFrame)
            self.setMouseTracking(True)
            self.setScene(scene)

    def __init__(self):
        super(QTetris, self).__init__()
        self.tetris = Tetris()
        self.tetris.delegate = self
        self.initUI()
        self.tetris.spawn()
        self.adjustSize()
        self.resizeEvent(None)
        self.show()

    def initUI(self):
        self.setLayout(QGridLayout())
        self.layout().setSpacing(0)
        self.layout().setContentsMargins(0, 0, 0, 0)
        self.scene = QTetris.QTetriscene(self.tetris)
        self.view = QTetris.QTetriview(self.scene)
        self.layout().addWidget(self.view)
        self.scoreEvent(0)

    def appearEvent(self, tetrimino):
        for tetritile in tetrimino:
            QTetris.QTetritile(self, tetritile)

    def scoreEvent(self, score):
        self.setWindowTitle(self.tr("Tetris - {score}").format(score=score))

    def disappearEvent(self, tetritile):
        self.scene.removeItem(tetritile.delegate)

    def gameOverEvent(self, score):
        QMessageBox.critical(self, self.tr("Game Over!"), self.tr("You toppped out."), QMessageBox.Ok)
        self.tetris.restart()

    def resizeEvent(self, resizeEvent):
        boundingRect = self.scene.itemsBoundingRect()
        self.view.fitInView(boundingRect, Qt.KeepAspectRatio)
        self.view.centerOn(boundingRect.center())

    def sizeHint(self):
        return QSize(self.tetris.columns * 22, self.tetris.rows * 22)


if __name__ == "__main__":
    application = QApplication(sys.argv)
    qTetris = QTetris()
    sys.exit(application.exec_())
