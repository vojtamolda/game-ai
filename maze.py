from PyQt5.QtCore import Qt, QSize, QPoint, QPropertyAnimation, QEasingCurve, pyqtProperty
from PyQt5.QtWidgets import QApplication, QWidget, QMessageBox
from PyQt5.QtGui import QPainter, QPen, QPalette
import random
import sys


class QMaze(QWidget):
    class Node:
        def __init__(self, row, column):
            self.row, self.column = row, column
            self.neighbors = []
            self.links = []

        def point(self, maze):
            return QPoint(self.column * maze.paintStep, self.row * maze.paintStep)

        def closest(self, maze, point):
            closestNode, closestDistance = None, float("inf")
            for node in self.links:
                delta = point - node.point(maze)
                distance = delta.manhattanLength()
                if distance < closestDistance:
                    closestNode, closestDistance = node, distance
            return closestNode

        def crawl(self, direction, distance = 1):
            if len(self.links) > 2 and distance > 1:
                return self
            for link in self.links:
                if direction == (link.row - self.row, link.column - self.column):
                    return link.crawl(direction, distance + 1)
            else:
                return self

    def __init__(self, size):
        super(QMaze, self).__init__()
        self.size = size
        self.nodes = None
        self.startNode = None
        self.finishNode = None
        self.playerNode = None
        self.paintStep = 0
        self.paintOffset = 0

        self.initMaze()
        self.initUI()
        self.show()

    @pyqtProperty(QPoint)
    def player(self):
        return self._player

    @player.setter
    def player(self, point):
        self._player = point
        self.update()

    def initMaze(self):
        self.nodes = {}
        for row in range(self.size):
            for column in range(self.size):
                self.nodes[row, column] = QMaze.Node(row, column)

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
        self.player = self.playerNode.point(self)

    def generateMaze(self, start):
        generated = set()
        deepest_node, deepest_recursion = None, -1

        def generateNode(node, recursion=0):
            nonlocal generated, deepest_node, deepest_recursion
            if node in generated:
                return
            generated.add(node)
            for neighbor in random.sample(node.neighbors, len(node.neighbors)):
                if neighbor not in generated:
                    node.links.append(neighbor)
                    neighbor.links.append(node)
                    generateNode(neighbor, recursion + 1)
            if recursion > deepest_recursion:
                deepest_node, deepest_recursion = node, recursion

        generateNode(start)
        return deepest_node

    def initUI(self):
        self.setWindowTitle(self.tr("Maze"))

    def mousePressEvent(self, mouseEvent):
        closestNode = self.playerNode.closest(self, mouseEvent.pos() - self.paintOffset)
        direction = closestNode.row - self.playerNode.row, closestNode.column - self.playerNode.column
        crawlNode = self.playerNode.crawl(direction)

        self.animation = QPropertyAnimation(self, b"player")
        if len(crawlNode.links) > 2:
            self.animation.setEasingCurve(QEasingCurve.OutBack);
        else:
            self.animation.setEasingCurve(QEasingCurve.OutBounce);
        self.animation.setStartValue(self.player)
        self.animation.setEndValue(crawlNode.point(self))
        self.animation.setDuration(400)
        self.animation.start()

        self.playerNode = crawlNode
        if self.playerNode == self.finishNode:
            QMessageBox.information(self, self.tr("Victory!"), self.tr("You won :)"), QMessageBox.Ok)
            self.initMaze()

    def paintEvent(self, paintEvent):
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
                        painter.drawLine(node.point(self), link.point(self))
                        paintNode(link)

            color = self.palette().color(QPalette.Dark)
            pen.setColor(color)
            pen.setWidth(0.50 * self.paintStep)
            painter.setPen(pen)
            for node in self.nodes.values():
                if paintEvent.region().contains(node.point(self)):
                    paintNode(node)

        if self.startNode is not None:
            color = self.palette().color(QPalette.Dark)
            pen.setColor(color)
            pen.setWidth(0.75 * self.paintStep)
            painter.setPen(pen)
            if paintEvent.region().contains(self.startNode.point(self)):
                painter.drawPoint(self.startNode.point(self))

        if self.finishNode is not None and paintEvent.region().contains(self.finishNode.point(self)):
            color = self.palette().color(QPalette.Dark).darker(120)
            pen.setColor(color)
            pen.setWidth(0.75 * self.paintStep)
            painter.setPen(pen)
            painter.drawPoint(self.finishNode.point(self))

        if self.player is not None:
            color = self.palette().color(QPalette.Highlight)
            color.setAlpha(196)
            pen.setColor(color)
            pen.setWidth(0.90 * self.paintStep)
            painter.setPen(pen)
            painter.drawPoint(self.player)

        del painter, pen

    def resizeEvent(self, resizeEvent):
        self.paintStep = min(self.width() / self.size, self.height() / self.size)
        self.paintOffset = QPoint((self.paintStep + (self.width() - self.paintStep * self.size)) / 2,
                                  (self.paintStep + (self.height() - self.paintStep * self.size)) / 2)
        self.player = self.playerNode.point(self)

    def sizeHint(self):
        paintStepHint = 40
        return QSize(self.size * paintStepHint, self.size * paintStepHint)


if __name__ == "__main__":
    application = QApplication(sys.argv)
    qMaze = QMaze(10)
    sys.exit(application.exec_())
