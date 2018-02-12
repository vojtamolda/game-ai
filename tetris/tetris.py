import random
import math


class Tetris(dict):

    class Tile:
        def __init__(self, tetris: 'Tetris', row: int, column: int, rotation: int):
            self.tetris = tetris
            self.row, self.column = row, column
            self.rotation = rotation
            self.delegate = None
            if self.tetris[self.row, self.column] is not None:
                raise RuntimeError("Game Over")
            self.tetris[self.row, self.column] = self

        def move(self, row: int, column: int, rotation: int):
            if self.tetris[self.row, self.column] == self:
                self.tetris[self.row, self.column] = None
            self.row, self.column = row, column
            self.rotation = rotation
            self.tetris[self.row, self.column] = self
            if self.delegate is not None:
                self.delegate.moved(self)

        def drop(self, distance: int):
            if self.tetris[self.row, self.column] == self:
                self.tetris[self.row, self.column] = None
            self.row += distance
            self.tetris[self.row, self.column] = self
            if self.delegate is not None:
                self.delegate.dropped(self)

        def collapse(self):
            if self.tetris[self.row, self.column] == self:
                self.tetris[self.row, self.column] = None
            if self.delegate is not None:
                self.delegate.collapsed(self)

        def shift(self, delta: int):
            if self.tetris[self.row, self.column] == self:
                self.tetris[self.row, self.column] = None
            self.row, self.column = self.row + delta, self.column
            self.tetris[self.row, self.column] = self
            if self.delegate is not None:
                self.delegate.shifted(self)

        def disappear(self):
            if self.delegate is not None:
                self.delegate.disappeared(self)

    class Tetrimino(set):
        shape = None
        central_row, central_column = None, None

        def __init__(self, tetris: 'Tetris', row: int, column: int):
            super(Tetris.Tetrimino, self).__init__()
            self.row, self.column, self.rotation = row, column, 0
            self.tetris = tetris
            for row, line in enumerate(self.shape):
                for column, symbol in filter(lambda tpl: tpl[1] == '☒', enumerate(line)):
                    local_row, local_column = row - self.central_row, column - self.central_column
                    tile = Tetris.Tile(tetris, self.row + local_row, self.column + local_column, self.rotation)
                    self.add(tile)

        def move(self, row: int, column: int, rotation: int) -> bool:

            def rotate(row: int, column: int, rotation: int) -> tuple:
                alpha = math.radians(rotation)
                rotated_row = math.cos(alpha) * row - math.sin(alpha) * column
                rotated_columm = math.sin(alpha) * row + math.cos(alpha) * column
                return round(rotated_row), round(rotated_columm)

            for tile in self:
                local_row, local_column = tile.row - self.row, tile.column - self.column
                local_rotation = rotation - self.rotation
                rotated_row, rotated_column = rotate(local_row, local_column, local_rotation)
                destination_row, destination_column = row + rotated_row, column + rotated_column
                row_inside = (0 <= destination_row < self.tetris.num_rows)
                column_inside = (0 <= destination_column < self.tetris.num_columns)
                if not row_inside or not column_inside:
                    return False
                self_intersect = (self.tetris[destination_row, destination_column] in self)
                if not self_intersect and self.tetris[destination_row, destination_column] is not None:
                    return False

            for tile in self:
                local_row, local_column = tile.row - self.row, tile.column - self.column
                local_rotation = rotation - self.rotation
                rotated_row, rotated_column = rotate(local_row, local_column, local_rotation)
                destination_row, destination_column = row + rotated_row, column + rotated_column
                tile.move(destination_row, destination_column, rotation)
            self.row, self.column = row, column
            self.rotation = rotation
            return True

        def drop(self):
            collision, distance = False, 0
            while collision is False:
                distance += 1
                for tile in self:
                    destination_row, destination_column = tile.row + distance, tile.column
                    row_inside = (0 <= destination_row < self.tetris.num_rows)
                    if not row_inside:
                        collision, distance = True, distance - 1
                        break
                    self_intersect = (self.tetris[destination_row, destination_column] in self)
                    if not self_intersect and self.tetris[destination_row, destination_column] is not None:
                        collision, distance = True, distance - 1
                        break

            for tile in self:
                tile.drop(distance)
            self.row += distance

    class I(Tetrimino):
        shape = ['☒☒☒☒']
        central_row, central_column = 0, 1

    class J(Tetrimino):
        shape = ['☒☒☒',
                 '☐☐☒']
        central_row, central_column = 0, 1

    class L(Tetrimino):
        shape = ['☒☒☒',
                 '☒☐☐']
        central_row, central_column = 0, 1

    class O(Tetrimino):
        shape = ['☒☒',
                 '☒☒']
        central_row, central_column = 0, 0

    class S(Tetrimino):
        shape = ['☐☒☒',
                 '☒☒☐']
        central_row, central_column = 0, 1

    class T(Tetrimino):
        shape = ['☒☒☒',
                 '☐☒☐']
        central_row, central_column = 0, 1

    class Z(Tetrimino):
        shape = ['☒☒☐',
                 '☐☒☒']
        central_row, central_column = 0, 1

    num_rows, num_columns = (20, 10)
    spawn_row, spawn_column = (0, 4)

    def __init__(self):
        super(Tetris, self).__init__()
        self.falling_tetrimino = None
        self.delegate = None
        self.score = 0
        self.update({(row, column): None for row in range(self.num_rows) for column in range(self.num_columns)})

    def __iter__(self):
        return iter(self.values())

    def __str__(self) -> str:
        string = ''
        for row in range(self.num_rows):
            for column in range(self.num_columns):
                string += '☒' if self[row, column] is not None else '☐'
            string += '\n'
        return string

    def spawn(self):
        RandomTetrimino = random.choice([Tetris.I, Tetris.J, Tetris.L, Tetris.O, Tetris.S, Tetris.T, Tetris.Z])
        try:
            self.falling_tetrimino = RandomTetrimino(self, self.spawn_row, self.spawn_column)
            self.delegate.appeared(self.falling_tetrimino)
        except RuntimeError:
            self.delegate.terminated()

    def move_left(self):
        row, column = self.falling_tetrimino.row, self.falling_tetrimino.column - 1
        rotation = self.falling_tetrimino.rotation
        if self.falling_tetrimino.move(row, column, rotation) is False:
            self.check()

    def move_right(self):
        row, column = self.falling_tetrimino.row, self.falling_tetrimino.column + 1
        rotation = self.falling_tetrimino.rotation
        if self.falling_tetrimino.move(row, column, rotation) is False:
            self.check()

    def rotate(self):
        row, column = self.falling_tetrimino.row, self.falling_tetrimino.column
        rotation = self.falling_tetrimino.rotation + 90
        if self.falling_tetrimino.move(row, column, rotation) is False:
            self.check()

    def move_down(self):
        row, column = self.falling_tetrimino.row + 1, self.falling_tetrimino.column
        rotation = self.falling_tetrimino.rotation
        if self.falling_tetrimino.move(row, column, rotation) is False:
            self.check()
            self.spawn()

    def tick(self):
        self.move_down()

    def drop(self):
        self.falling_tetrimino.drop()
        self.check()
        self.spawn()

    def check(self):
        full_rows = []
        for row in range(self.num_rows):
            for column in range(self.num_columns):
                if self[row, column] is None:
                    break
            else:
                full_rows.append(row)

        if len(full_rows) > 0:
            self.collapse(full_rows)
            self.shift(full_rows)
            self.score += len(full_rows)
            self.delegate.scored(self.score)

    def collapse(self, full_rows: list):
        for row in reversed(sorted(full_rows)):
            for column in range(self.num_columns):
                self[row, column].collapse()

    def shift(self, full_rows: list):
        for row in reversed(range(min(full_rows))):
            for column in range(self.num_columns):
                if self[row, column] is not None:
                    self[row, column].shift(len(full_rows))

    def restart(self):
        for tile in filter(lambda tl: tl is not None, self):
            tile.disappear()
        self.clear()
        self.update({(row, column): None for row in range(self.num_rows) for column in range(self.num_columns)})
        self.score = 0
        self.delegate.scored(self.score)
        self.spawn()


if __name__ == '__main__':
    from PyQt5.QtWidgets import QApplication
    import sys
    import ui

    application = QApplication(sys.argv)
    qTetris = ui.QTetris()
    sys.exit(application.exec())
