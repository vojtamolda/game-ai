import io
import copy
import math
import numpy
import pygraphviz
import dataclasses
from typing import List, Optional, Any, Iterator


class TicTacToe(dict):
    """ TicTacToe class represents the game rules. It decided who moves first, when the
    game, and when to notify the UI delegate. During every round Tile where to make the
    move is solicited from each Player. Solicited Tile objects are then used to evolve
    the Gameboard state forward to the next round.
    """
    class Gameboard(numpy.ndarray):
        """ Gameboard represents a Tic-Tac-Toe game situation. It stores a grid of Os and Xs
        as well as the outcome and the player that will move next. It can also return 90 deg
        rotated and mirrored symmetrically equivalent views of itself.
        """
        Empty, X, O = 0, 1, 2

        def __new__(cls, tictactoe: 'TicTacToe'):
            gameboard = numpy.zeros(shape=[3, 3], dtype=numpy.uint8).view(cls)
            gameboard.tictactoe = tictactoe
            gameboard.outcome = None
            gameboard.next = None
            return gameboard

        def __array_finalize__(self, template: 'TicTacToe'):
            self.tictactoe = getattr(template, 'tictactoe', None)
            self.outcome = getattr(template, 'outcome', None)
            self.next = getattr(template, 'next', None)

        def __str__(self):
            x, o = self.tictactoe.x, self.tictactoe.o
            symbol_map = {self.Empty: '-', x.index: x.symbol, o.index: o.symbol}
            lines = [[symbol_map.get(self[row, column], '?') for column in range(3)] for row in range(3)]
            lines = [''.join(line) for line in lines]
            return '\n'.join(lines)

        def __eq__(self, other: 'TicTacToe.Gameboard'):
            return self.tobytes() == other.tobytes()

        def __hash__(self):
            return hash(self.tobytes())

        def tiles(self) -> List['TicTacToe.Tile']:
            equal_zero = numpy.equal(self, 0)
            equal_indices = numpy.where(equal_zero)
            return [TicTacToe.Tile(row, column) for row, column in zip(*equal_indices)]

        def following(self, tile: 'TicTacToe.Tile') -> 'TicTacToe.Gameboard':
            return self.tictactoe.following(self, tile)

        def rotated(self) -> 'TicTacToe.Gameboard':
            return numpy.rot90(self)

        def mirrored(self) -> 'TicTacToe.Gameboard':
            return numpy.fliplr(self)

        def score(self, player: 'TicTacToe.Player') -> Optional[int]:
            if self.outcome is None:
                return None
            if player.index == 1:
                return +self.outcome
            else:
                return -self.outcome

    class Transpositions(dict):
        """ Transpositions is a symmetry aware dictionary that uses Gameboard objects as keys. It
        treats all 8 symmetric (four 90 deg rotated + mirrored) variants of a Gameboard as a single
        object with one associated value.
        """
        @classmethod
        def symmetric_variants(cls, gameboard: 'TicTacToe.Gameboard') -> Iterator['TicTacToe.Gameboard']:
            yield gameboard
            yield gameboard.mirrored()
            for i in range(3):
                gameboard = gameboard.rotated()
                yield gameboard
                yield gameboard.mirrored()

        def equivalent(self, gameboard: 'TicTacToe.Gameboard') -> Optional['TicTacToe.Gameboard']:
            for variant in self.symmetric_variants(gameboard):
                if super().__contains__(variant):
                    return variant
            return None

        def __setitem__(self, gameboard: 'TicTacToe.Gameboard', value: Any):
            equivalent = self.equivalent(gameboard)
            if equivalent is None:
                super().__setitem__(gameboard, value)
            else:
                super().__setitem__(equivalent, value)

        def __contains__(self, gameboard: 'TicTacToe.Gameboard') -> bool:
            equivalent = self.equivalent(gameboard)
            return equivalent is not None

        def __getitem__(self, gameboard: 'TicTacToe.Gameboard') -> Any:
            equivalent = self.equivalent(gameboard)
            if equivalent is None:
                raise KeyError()
            else:
                return super().__getitem__(equivalent)

    class Player:
        """ Player is an abstraction of an AI agent that selects tbe best action based on the
        provided Gameboard state. Actions are represented as a Tile object (a tuple of row
        and column).
        """
        class Graph(pygraphviz.AGraph):
            ScoreColormap = {
                None: 'white',
                +1: 'green',
                0: 'gray',
                -1: 'red'
            }

            def __init__(self, gameboard: 'TicTacToe.Gameboard', player: 'TicTacToe.Player'):
                super().__init__()
                self.player = player
                self.max_depth = math.inf
                self.add_node(gameboard)
                self.expand(gameboard)

            def expand(self, gameboard: 'TicTacToe.Gameboard', depth=1):
                if depth > self.max_depth:
                    return
                for tile in gameboard.tiles():
                    following = gameboard.following(tile)
                    self.add_edge(gameboard, following, tile)
                    if following.outcome is None:
                        self.expand(following, depth + 1)

            def add_node(self, gameboard: 'TicTacToe.Gameboard', **attrs) -> 'TicTacToe.Gameboard':
                attrs['fillcolor'] = self.ScoreColormap[gameboard.score(self.player)]
                super().add_node(gameboard, **attrs)
                return gameboard

            def add_edge(self, start: 'TicTacToe.Gameboard', end: 'TicTacToe.Gameboard', tile: 'TicTacToe.Tile'):
                start_node = self.add_node(start)
                end_node = self.add_node(end)
                super().add_edge(start_node, end_node, label=str(tile))

            def to_svg(self) -> bytes:
                buffer = io.BytesIO()
                self.draw(buffer, prog='dot', format='svg', args='-Nstyle=filled -Edir=forward')
                return buffer.getvalue()

        def __init__(self, symbol: str, index: int = None):
            self.symbol = symbol
            self.index = index

        def __str__(self):
            return self.symbol

        def play(self, gameboard: 'TicTacToe.Gameboard') -> 'TicTacToe.Tile':
            raise NotImplementedError()

        def visualize(self, gameboard: 'TicTacToe.Gameboard') -> bytes:
            tree = self.Graph(gameboard, self)
            svg_bytes = tree.to_svg()
            return svg_bytes

        def reset(self):
            pass

    @dataclasses.dataclass
    class Tile:
        """ Tile is lightweight data class that represents a Player's move in the
        Gameboard object.
        """
        row: int
        column: int
        SymbolMap = {
            (0, 0): "↖", (0, 1): "↑", (0, 2): "↗",
            (1, 0): "←", (1, 1): "□", (1, 2): "→",
            (2, 0): "↙", (2, 1): "↓", (2, 2): "↘",
        }

        def __str__(self):
            return self.SymbolMap[(self.row, self.column)]

    def __init__(self, x: 'TicTacToe.Player' = None, o: 'TicTacToe.Player' = None,
                 gameboard: 'TicTacToe.Gameboard' = None):
        super().__init__()
        if x is None:
            x = TicTacToe.Player('X')
        if o is None:
            o = TicTacToe.Player('O')
        x.index, o.index = self.Gameboard.X, self.Gameboard.O
        self.x, self.o = x, o

        if gameboard is None:
            self.gameboard = self.Gameboard(self)
            self.gameboard.next = x
        else:
            gameboard.tictactoe = self
            self.gameboard = gameboard
        self.delegate = None

    def __str__(self):
        return str(self.gameboard)

    @classmethod
    def from_scenario(cls, scenario: List[str], x: 'TicTacToe.Player', o: 'TicTacToe.Player') -> 'TicTacToe':
        x.index, o.index = cls.Gameboard.X, cls.Gameboard.O
        index_map = {'-': 0, x.symbol: x.index, o.symbol: o.index}

        gameboard = cls.Gameboard(None)
        for row, scenario_row in enumerate(scenario):
            for column, symbol in enumerate(scenario_row):
                gameboard[row, column] = index_map.get(symbol, 0)
        gameboard.next = x

        tictactoe = cls(x=x, o=o, gameboard=gameboard)
        return tictactoe

    def move(self, gameboard: 'TicTacToe.Gameboard', tile: 'TicTacToe.Tile', notify=False):
        player = gameboard.next
        gameboard[tile.row, tile.column] = player.index
        gameboard.next = self.o if player == self.x else self.x

        outcome = self.outcome(gameboard, tile)
        if outcome is not None:
            gameboard.outcome = +outcome if player == self.x else -outcome
        else:
            gameboard.outcome = None

        if notify is True:
            self.delegate.notify(player, tile)

    def following(self, gameboard: 'TicTacToe.Gameboard', tile: 'TicTacToe.Tile') -> 'TicTacToe.Gameboard':
        following = copy.copy(gameboard)
        self.move(following, tile, False)
        return following

    @staticmethod
    def outcome(gameboard: 'TicTacToe.Gameboard', tile: 'TicTacToe.Tile') -> Optional[int]:
        if gameboard[tile.row, 0] == gameboard[tile.row, 1] == gameboard[tile.row, 2]:
            return 1
        if gameboard[0, tile.column] == gameboard[1, tile.column] == gameboard[2, tile.column]:
            return 1
        if tile.column - tile.row == 0 and gameboard[0, 0] == gameboard[1, 1] == gameboard[2, 2]:
            return 1
        if tile.column + tile.row == 2 and gameboard[0, 2] == gameboard[1, 1] == gameboard[2, 0]:
            return 1
        if not gameboard.tiles():
            return 0
        return None

    def play(self, notify=False) -> Optional[int]:
        tile = self.gameboard.next.play(self.gameboard)
        assert tile in self.gameboard.tiles()

        self.move(self.gameboard, tile, notify)
        return self.gameboard.outcome

    def round(self, notify=False) -> Optional[int]:
        outcome = self.play(notify)
        if outcome is not None:
            return outcome

        outcome = self.play(notify)
        if outcome is not None:
            return outcome

        return None

    def reset(self, notify=False):
        self.gameboard = self.Gameboard(self)
        self.gameboard.next = self.x

        if notify is True:
            for tile in self.gameboard.tiles():
                self.delegate.notify(None, tile)

        self.x.reset()
        self.o.reset()


if __name__ == "__main__":
    from PySide2.QtWidgets import QApplication
    import sys
    import ui

    application = QApplication(sys.argv)
    qTicTacToe = ui.QTicTacToe()
    sys.exit(application.exec_())
