from PyQt5.QtCore import Qt, QSize, QPoint, QPropertyAnimation, QEasingCurve, pyqtProperty
from PyQt5.QtGui import QPainter, QPen, QPalette, QPaintEvent, QMouseEvent, QResizeEvent
from PyQt5.QtWidgets import QWidget, QMessageBox
import random


class QMaze(QWidget):

    class QNode:
        def __init__(self, maze: 'QMaze', row: int, column: int):
            self.row, self.column = row, column
            self.maze = maze
            self.neighbors = []
            self.links = []

        @property
        def point(self) -> QPoint:
            return QPoint(self.column * self.maze.paintStep, self.row * self.maze.paintStep)

        def closest(self, point: QPoint) -> 'QMaze.QNode':
            closestNode, closestDistance = None, float("inf")
            for node in self.links:
                delta = point - node.point
                distance = delta.manhattanLength()
                if distance < closestDistance:
                    closestNode, closestDistance = node, distance
            return closestNode

        def crawl(self, direction: tuple, distance: int=1) -> 'QMaze.QNode':
            if len(self.links) > 2 and distance > 1:
                return self
            for link in self.links:
                if direction == (link.row - self.row, link.column - self.column):
                    return link.crawl(direction, distance + 1)
            else:
                return self

    def __init__(self, size: int):
        super(QMaze, self).__init__()
        self.size = size
        self.nodes = None
        self.animation = None
        self.startNode = None
        self.finishNode = None
        self.playerNode = None
        self.paintStep = 0
        self.paintOffset = 0

        self.initMaze()
        self.initUI()
        self.show()

    @pyqtProperty(QPoint)
    def player(self) -> QPoint:
        return self._player

    @player.setter
    def player(self, point: QPoint):
        self._player = point
        self.update()

    def initMaze(self):
        self.nodes = {}
        for row in range(self.size):
            for column in range(self.size):
                self.nodes[row, column] = QMaze.QNode(self, row, column)

        for (row, column), node in self.nodes.items():
            if 0 < row:
                node.neighbors.append(self.nodes[row - 1, column])
            if row < self.size - 1:
                node.neighbors.append(self.nodes[row + 1, column])
            if 0 < column:
                node.neighbors.append(self.nodes[row, column - 1])
            if column < self.size - 1:
                node.neighbors.append(self.nodes[row, column + 1])

        self.startNode = self.nodes[0, 0]
        self.finishNode = self.generateMaze(self.startNode)
        self.playerNode = self.startNode
        self.player = self.playerNode.point

    def generateMaze(self, start: 'QMaze.QNode') -> 'QMaze.QNode':
        generated = set()
        deepestNode, deepestRecursion = start, -1

        def generateNode(node, recursion=0):
            nonlocal generated, deepestNode, deepestRecursion
            if node in generated:
                return
            generated.add(node)
            for neighbor in random.sample(node.neighbors, len(node.neighbors)):
                if neighbor not in generated:
                    node.links.append(neighbor)
                    neighbor.links.append(node)
                    generateNode(neighbor, recursion + 1)
            if recursion > deepestRecursion:
                deepestNode, deepestRecursion = node, recursion

        generateNode(start)
        return deepestNode

    def initUI(self):
        self.setWindowTitle(self.tr("Maze"))

    def mousePressEvent(self, mouseEvent: QMouseEvent):
        closestNode = self.playerNode.closest(mouseEvent.pos() - self.paintOffset)
        direction = closestNode.row - self.playerNode.row, closestNode.column - self.playerNode.column
        crawlNode = self.playerNode.crawl(direction)

        self.animation = QPropertyAnimation(self, b'player')
        if len(crawlNode.links) > 2:
            self.animation.setEasingCurve(QEasingCurve.OutBack);
        else:
            self.animation.setEasingCurve(QEasingCurve.OutBounce);
        self.animation.setStartValue(self.player)
        self.animation.setEndValue(crawlNode.point)
        self.animation.setDuration(400)
        self.animation.start()

        self.playerNode = crawlNode
        if self.playerNode == self.finishNode:
            QMessageBox.information(self, self.tr("Victory!"), self.tr("You won :)"), QMessageBox.Ok)
            self.initMaze()

    def paintEvent(self, paintEvent: QPaintEvent):
        pen = QPen()
        pen.setJoinStyle(Qt.RoundJoin)
        pen.setCapStyle(Qt.RoundCap)
        painter = QPainter(self)
        painter.translate(self.paintOffset)
        painter.setBackgroundMode(Qt.TransparentMode)
        painter.setRenderHint(QPainter.Antialiasing)

        if self.nodes is not None:
            painted = set()

            def paintNode(node):
                nonlocal painter, painted
                if node in painted:
                    return
                painted.add(node)
                for link in node.links:
                    if link not in painted:
                        painter.drawLine(node.point, link.point)
                        paintNode(link)

            color = self.palette().color(QPalette.Dark)
            pen.setColor(color)
            pen.setWidth(0.50 * self.paintStep)
            painter.setPen(pen)
            for node in self.nodes.values():
                if paintEvent.region().contains(node.point):
                    paintNode(node)

        if self.startNode is not None:
            color = self.palette().color(QPalette.Dark)
            pen.setColor(color)
            pen.setWidth(0.75 * self.paintStep)
            painter.setPen(pen)
            if paintEvent.region().contains(self.startNode.point):
                painter.drawPoint(self.startNode.point)

        if self.finishNode is not None and paintEvent.region().contains(self.finishNode.point):
            color = self.palette().color(QPalette.Dark).darker(120)
            pen.setColor(color)
            pen.setWidth(0.75 * self.paintStep)
            painter.setPen(pen)
            painter.drawPoint(self.finishNode.point)

        if self.player is not None:
            color = self.palette().color(QPalette.Highlight)
            color.setAlpha(196)
            pen.setColor(color)
            pen.setWidth(0.90 * self.paintStep)
            painter.setPen(pen)
            painter.drawPoint(self.player)

        del painter, pen

    def resizeEvent(self, resizeEvent: QResizeEvent):
        self.paintStep = min(self.width() / self.size, self.height() / self.size)
        self.paintOffset = QPoint((self.paintStep + (self.width() - self.paintStep * self.size)) / 2,
                                  (self.paintStep + (self.height() - self.paintStep * self.size)) / 2)
        self.player = self.playerNode.point

    def sizeHint(self) -> QSize:
        paintStepHint = 40
        return QSize(self.size * paintStepHint, self.size * paintStepHint)


if __name__ == "__main__":
    from PyQt5.QtWidgets import QApplication
    import sys

    application = QApplication(sys.argv)
    qMaze = QMaze(10)
    sys.exit(application.exec())
