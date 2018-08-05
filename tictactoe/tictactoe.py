from typing import Optional, List


class TicTacToe(dict):

    class Tile:
        def __init__(self, tictactoe: 'TicTacToe', row: int, column: int):
            self.tictactoe = tictactoe
            self.row, self.column = row, column
            self.delegate = None
            self.player = None

        def __str__(self):
            return '-' if self.player is None else str(self.player)

        def complete_row(self) -> bool:
            tictactoe, row, player = self.tictactoe, self.row, self.player
            return player == tictactoe[row, 0].player == tictactoe[row, 1].player == tictactoe[row, 2].player

        def complete_column(self) -> bool:
            tictactoe, column, player = self.tictactoe, self.column, self.player
            return player == tictactoe[0, column].player == tictactoe[1, column].player == tictactoe[2, column].player

        def complete_diagonal(self) -> bool:
            tictactoe, row, column, player = self.tictactoe, self.row, self.column, self.player
            if column - row == 0:
                return player == tictactoe[0, 0].player == tictactoe[1, 1].player == tictactoe[2, 2].player
            if column + row == 2:
                return player == tictactoe[0, 2].player == tictactoe[1, 1].player == tictactoe[2, 0].player

        def notify(self):
            if self.delegate is not None:
                self.delegate.marked()

    class Player:
        def __init__(self, symbol: str, tictactoe: 'TicTacToe'=None):
            self.tictactoe = tictactoe
            self.symbol = symbol

        def __str__(self):
            return self.symbol

        def play(self) -> 'TicTacToe.Tile':
            raise NotImplementedError()

        def reset(self):
            pass

    size = 3

    def __init__(self, o: 'TicTacToe.Player'=None, x: 'TicTacToe.Player'=None):
        super(TicTacToe, self).__init__()
        if o is None:
            o = TicTacToe.Player('O', self)
        if x is None:
            x = TicTacToe.Player('X', self)
        self.o, self.x = o, x
        self.o.tictactoe, self.x.tictactoe = self, self
        self.size = 3
        self.next = o
        for row in range(self.size):
            for column in range(self.size):
                self[row, column] = TicTacToe.Tile(self, row, column)

    def __iter__(self):
        return iter(self.values())

    def __str__(self):
        string = ""
        for row in range(self.size):
            for column in range(self.size):
                string += str(self[row, column])
            string += "\n"
        return string

    @classmethod
    def build(cls, scenario: List[str], o: 'TicTacToe.Player', x: 'TicTacToe.Player') -> 'TicTacToe':
        tictactoe = cls(o=o, x=x)
        symbol_map = {tictactoe.o.symbol: tictactoe.o, tictactoe.x.symbol: tictactoe.x}
        for row, scenario_row in enumerate(scenario):
            for column, symbol in enumerate(scenario_row):
                disc = tictactoe[row, column]
                disc.player = symbol_map.get(symbol, None)
        return tictactoe

    def set(self, tile, notify=False):
        assert tile.player is None
        tile.player = self.next
        self.next = self.o if self.next == self.x else self.x
        if notify is True:
            tile.notify()

    def unset(self, tile: 'TicTacToe.Tile', notify: bool=False):
        assert tile.player is not None
        tile.player = None
        self.next = self.o if self.next == self.x else self.x
        if notify is True:
            tile.notify()

    def score(self, tile: 'TicTacToe.Tile') -> Optional[int]:
        def complete(tictactoe):
            for tile in tictactoe:
                if tile.player is None:
                    return False
            return True

        player = tile.player
        if player is None:
            return None
        if tile.complete_row() is True:
            return +1 if tile.player == player else -1
        if tile.complete_column() is True:
            return +1 if tile.player == player else -1
        if tile.complete_diagonal() is True:
            return +1 if tile.player == player else -1
        if complete(self):
            return 0
        return None

    def choices(self) -> List['TicTacToe.Tile']:
        return [tile for tile in self if tile.player is None]

    def round(self, notify: bool=False):
        o_tile = self.o.play()
        assert o_tile in self.choices()
        self.set(o_tile, notify)
        o_score = self.score(o_tile)
        if o_score is not None:
            return +o_score

        x_tile = self.x.play()
        assert x_tile in self.choices()
        self.set(x_tile, notify)
        x_score = self.score(x_tile)
        if x_score is not None:
            return -x_score
        return None

    def reset(self, notify: bool=False):
        for tile in self:
            tile.player = None
            if notify is True:
                tile.notify()
        self.o.reset()
        self.x.reset()
        self.next = self.o


if __name__ == "__main__":
    from PySide2.QtWidgets import QApplication
    import sys
    import ui

    application = QApplication(sys.argv)
    qTicTacToe = ui.QTicTacToe()
    sys.exit(application.exec_())
