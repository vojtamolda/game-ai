from PySide2.QtCore import Qt, QTimer, QSize, QPointF, QRectF, QPropertyAnimation, QEasingCurve, \
                           QParallelAnimationGroup, QAbstractAnimation
from PySide2.QtWidgets import QWidget, QFrame, QMessageBox, QGraphicsScene, QGraphicsView, \
                            QGraphicsObject, QGridLayout, QStyleOptionGraphicsItem, \
                            QGraphicsSceneMouseEvent, QGraphicsSceneWheelEvent
from PySide2.QtGui import QPainter, QPen, QBrush, QColor, QTransform, QResizeEvent, QKeyEvent
from typing import Union

from tetris import Tetris


class QTetris(QWidget):

    class QTile(QGraphicsObject):
        colorMap = {Tetris.I: QColor("#53bbf4"), Tetris.J: QColor("#e25fb8"),
                    Tetris.L: QColor("#ffac00"), Tetris.O: QColor("#ecff2e"),
                    Tetris.S: QColor("#97eb00"), Tetris.T: QColor("#ff85cb"),
                    Tetris.Z: QColor("#ff5a48")}

        def __init__(self, qTetris: 'QTetris', tetrimino: Tetris.Tetrimino, tile: Tetris.Tile):
            super(QTetris.QTile, self).__init__()
            tile.delegate = self
            self.color = self.colorMap[type(tetrimino)]
            self.qTetris = qTetris
            self.moveAnimation = QParallelAnimationGroup()
            self.dropAnimation = QPropertyAnimation(self, b'pos')
            self.collapseAnimation = QPropertyAnimation(self, b'pos')
            self.shiftAnimation = QPropertyAnimation(self, b'pos')
            self.collapseAnimation.finished.connect(lambda tl=tile: tile.delegate.disappeared(tl))
            self.qTetris.scene.addItem(self)
            self.setPos(QPointF(0, 4))
            self.moved(tile)

        def moved(self, tile: Tetris.Tile):
            translation = QPropertyAnimation(self, b'pos')
            start, end = self.pos(), QPointF(tile.row, tile.column)
            curve, speed, delay = QEasingCurve.OutBack, 1 / 50, -1
            self.animate(translation, start, end, curve, speed, delay)

            rotation = QPropertyAnimation(self, b'rotation')
            start, end = self.rotation(), tile.rotation
            curve, speed, delay = QEasingCurve.OutBack, 1, -1
            self.animate(rotation, start, end, curve, speed, delay)
            rotation.setDuration(translation.duration())

            self.moveAnimation.clear()
            self.moveAnimation.addAnimation(translation)
            self.moveAnimation.addAnimation(rotation)
            self.moveAnimation.start()

        def dropped(self, tile: Tetris.Tile):
            start, end = self.pos(), QPointF(tile.row, tile.column)
            curve, speed, delay = QEasingCurve.OutBounce, 1 / 50, 0
            self.animate(self.dropAnimation, start, end, curve, speed, delay)

        def collapsed(self, tile: Tetris.Tile):
            start, end = self.pos(), QPointF(tile.row, tile.column + 2 * tile.tetris.num_columns)
            curve, speed, delay = QEasingCurve.InOutExpo, 1 / 50, 800
            if self.dropAnimation.state() == QAbstractAnimation.Running:
                start = self.dropAnimation.endValue()
            self.animate(self.collapseAnimation, start, end, curve, speed, delay)

        def shifted(self, tile: Tetris.Tile):
            start, end = self.pos(), QPointF(tile.row, tile.column)
            curve, speed, delay = QEasingCurve.OutBounce, 1 / 100, 1200
            if self.dropAnimation.state() == QAbstractAnimation.Running:
                start = self.dropAnimation.endValue()
            self.animate(self.shiftAnimation, start, end, curve, speed, delay)

        def disappeared(self, tile: Tetris.Tile):
            self.qTetris.scene.removeItem(self)

        def paint(self, painter: QPainter, styleOption: QStyleOptionGraphicsItem, widget: QWidget=None):
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

        @staticmethod
        def animate(animation: QPropertyAnimation, start: Union[QPointF, int, float], end: Union[QPointF, int, float],
                    curve: QEasingCurve=QEasingCurve.Linear, speed: float=1 / 50, delay: int=-1):
            animation.setStartValue(start)
            animation.setEndValue(end)
            animation.setEasingCurve(curve)
            if type(start) == type(end) == QPointF:
                distance = (end - start).manhattanLength()
            else:
                distance = abs(end - start)
            animation.setDuration(round(distance / speed))
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

    class QScene(QGraphicsScene):
        def __init__(self, tetris: Tetris):
            super(QTetris.QScene, self).__init__()
            self.tetris = tetris

            pen = QPen()
            pen.setWidthF(0.05)
            pen.setColor(Qt.lightGray)
            brush = QBrush(Qt.NoBrush)
            rect = QRectF(0, 0, tetris.num_rows, tetris.num_columns)
            rect.translate(-0.5, -0.5)
            self.setSceneRect(rect)
            self.addRect(rect, pen, brush)
            self.setBackgroundBrush(self.palette().window())

            for column in range(0, tetris.num_columns, 2):
                pen = QPen(Qt.NoPen)
                brush = QBrush(Qt.SolidPattern)
                brush.setColor(Qt.lightGray)
                topLeft = QPointF(0, column)
                bottomRight = QPointF(tetris.num_rows, column + 1)
                rectangle = QRectF(topLeft, bottomRight)
                rectangle.translate(-0.5, -0.5)
                self.addRect(rectangle, pen, brush)

        def mouseMoveEvent(self, sceneMouseEvent: QGraphicsSceneMouseEvent):
            mousePoint = sceneMouseEvent.scenePos()
            mouseRow, mouseColumn = round(mousePoint.x()), round(mousePoint.y())
            row, column = self.tetris.falling_tetrimino.row, self.tetris.falling_tetrimino.column
            if mouseColumn - column > 0:
                self.tetris.move_right()
            if mouseColumn - column < 0:
                self.tetris.move_left()

        def mouseReleaseEvent(self, sceneMouseEvent: QGraphicsSceneMouseEvent):
            if sceneMouseEvent.button() == Qt.LeftButton:
                self.tetris.drop()
            if sceneMouseEvent.button() == Qt.RightButton:
                self.tetris.rotate()

        def wheelEvent(self, sceneWheelEvent: QGraphicsSceneWheelEvent):
            if sceneWheelEvent.delta() > 10:
                self.tetris.move_down()

        def keyReleaseEvent(self, sceneKeyEvent: QKeyEvent):
            if sceneKeyEvent.key() == Qt.Key_Left:
                self.tetris.move_left()
            if sceneKeyEvent.key() == Qt.Key_Right:
                self.tetris.move_right()
            if sceneKeyEvent.key() == Qt.Key_Down:
                self.tetris.move_down()
            if sceneKeyEvent.key() == Qt.Key_Up:
                self.tetris.rotate()

    class QView(QGraphicsView):
        def __init__(self, scene: 'QTetris.QScene'):
            super(QTetris.QView, self).__init__()
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
        self.tetris = None
        self.timer = None
        self.initGame()

        self.view = None
        self.scene = None
        self.initUI()

        self.show()
        self.tetris.spawn()
        self.timer.start()

    def initGame(self):
        self.tetris = Tetris()
        self.tetris.delegate = self
        self.timer = QTimer(self)
        self.timer.setInterval(350)
        self.timer.timeout.connect(lambda: self.tetris.tick())

    def initUI(self):
        self.setLayout(QGridLayout())
        self.layout().setSpacing(0)
        self.layout().setContentsMargins(0, 0, 0, 0)
        self.scene = QTetris.QScene(self.tetris)
        self.view = QTetris.QView(self.scene)
        self.layout().addWidget(self.view)
        self.scored(0)

    def appeared(self, tetrimino: Tetris.Tetrimino):
        for tile in tetrimino:
            QTetris.QTile(self, tetrimino, tile)

    def scored(self, score: int):
        self.setWindowTitle(self.tr("Tetris - {score}").format(score=score))

    def terminated(self):
        QMessageBox.critical(self, self.tr("Game Over!"), self.tr("You toppped out."), QMessageBox.Ok)
        self.tetris.restart()

    def resizeEvent(self, resizeEvent: QResizeEvent):
        boundingRect = self.scene.itemsBoundingRect()
        self.view.fitInView(boundingRect, Qt.KeepAspectRatio)
        self.view.centerOn(boundingRect.center())

    def sizeHint(self) -> QSize:
        return QSize(self.tetris.num_columns * 22, self.tetris.num_rows * 22)
