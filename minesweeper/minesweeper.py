import random


class MineSweeper(dict):

    class Tile:
        def __init__(self, minesweeper: 'MineSweeper', row: int, column: int):
            self.row, self.column = row, column
            self.minesweeper = minesweeper
            self.explosive = False
            self.delegate = None
            self.revealed = False
            self.bombs = None

        def __str__(self):
            if self.revealed and self.explosive:
                return "☀"
            if self.revealed and self.bombs > 0:
                return str(self.bombs)
            return " "

        def reveal(self, ignore_recursive: bool=False):
            self.revealed = True
            self.notify()
            if self.explosive:
                return
            if self.bombs == 0 and not ignore_recursive:
                for neighbor in self.neighbors():
                    if not neighbor.explosive and not neighbor.revealed:
                        neighbor.reveal()

        def notify(self):
            if self.delegate is not None:
                self.delegate.refresh()

        def neighbors(self):
            for diff_row, diff_col in [(+1, -1), (+1, 0), (+1, +1),
                                        (0, -1),           (0, +1),
                                       (-1, -1), (-1, 0), (-1, +1)]:
                neighbor_row, neighbor_col = self.row + diff_row, self.column + diff_col
                if (neighbor_row, neighbor_col) in self.minesweeper:
                    yield self.minesweeper[neighbor_row, neighbor_col]

        def reset(self):
            self.explosive = False
            self.revealed = False
            self.bombs = None
            self.notify()

        def count(self):
            self.bombs = 0
            for neighbor in self.neighbors():
                self.bombs += int(neighbor.explosive)

    def __init__(self, size: int, explosiveness: float=0.10):
        super(MineSweeper, self).__init__()
        self.explosiveness = explosiveness
        self.size = size
        for row in range(self.size):
            for column in range(self.size):
                tile = MineSweeper.Tile(self, row, column)
                tile.explosive = (random.random() <= self.explosiveness)
                self[row, column] = tile
        for tile in self:
            tile.count()

    def __iter__(self):
        return iter(self.values())

    def __str__(self):
        string = ""
        for row in range(self.size):
            for column in range(self.size):
                string += str(self[row, column])
            string += "\n"
        return string

    def score(self):
        not_revealed_count = 0
        for tile in self:
            if not tile.revealed and not tile.explosive:
                not_revealed_count += 1
            if tile.revealed and tile.explosive:
                return -1
        if not_revealed_count == 0:
            return +1
        return None

    def reveal(self):
        for tile in self:
            if tile.explosive:
                tile.reveal(True)

    def reset(self):
        for tile in self:
            tile.reset()
            tile.explosive = (random.random() <= self.explosiveness)
        for tile in self:
            tile.count()


if __name__ == "__main__":
    from PySide2.QtWidgets import QApplication
    import sys
    import ui

    application = QApplication(sys.argv)
    qMineSweeper = ui.QMineSweeper(10)
    sys.exit(application.exec_())
