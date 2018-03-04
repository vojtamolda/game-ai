import random
from typing import Optional, List


class FourPlay(dict):

    class Disc:
        def __init__(self, fourplay: 'FourPlay', row: int, column: int):
            self.fourplay = fourplay
            self.row, self.column = row, column
            self.delegate = None
            self.player = None
            self.marked = False
            self.rank = 0

        def __eq__(self, other: 'FourPlay.Disc'):
            if other is None:
                return False
            else:
                return (self.row, self.column) == (other.row, other.column)

        def __str__(self):
            return '-' if self.player is None else str(self.player)

        def mark(self, notify: bool=False):
            self.marked = True
            self.notify(notify)

        def notify(self, notify: bool=False):
            if self.delegate is not None and notify is True:
                self.delegate.marked(self)

        def neighbor(self, location: tuple=None) -> Optional['FourPlay.Disc']:
            diff_row, diff_col = location[0], location[1]
            neighbor_row, neighbor_col = self.row + diff_row, self.column + diff_col
            if (neighbor_row, neighbor_col) in self.fourplay:
                return self.fourplay[(neighbor_row, neighbor_col)]
            else:
                return None

        def crawl(self, direction: tuple, player: 'FourPlay.Player', mark: bool=False) -> int:
            if self.player == player:
                if mark is True:
                    self.mark(True)
                neighbor = self.neighbor(direction)
                if neighbor is not None:
                    return neighbor.crawl(direction, player, mark) + 1
                else:
                    return 1
            return 0

        def reset(self, notify: bool=False):
            self.player = None
            self.marked = False
            self.rank = 0
            self.notify(notify)

    class Frontier(list):
        def __init__(self, fourplay):
            super(FourPlay.Frontier, self).__init__()
            self.fourplay = fourplay

        def __str__(self):
            chars = ["-" if disc is None else str(disc.row) for disc in self]
            return "".join(chars)

        def increase(self, column: int, notify: bool=False):
            disc = self[column]
            if disc is None:
                return
            disc_above = disc.neighbor((-1, 0))
            self[column] = disc_above
            if disc_above is not None:
                disc_above.notify(notify)

        def decrease(self, column: int, notify: bool=False):
            disc = self[column]
            if disc is None:
                top_row_disc = self.fourplay[0, column]
                self[column] = top_row_disc
                top_row_disc.notify(notify)
                return
            disc_below = disc.neighbor((+1, 0))
            self[column] = disc_below
            if disc_below is not None:
                disc_below.notify(notify)

        def choices(self, shuffle: bool=True) -> List['FourPlay.Disc']:
            choices = [disc for disc in self if disc is not None]
            if shuffle is True:
                random.shuffle(choices)
            return choices

        def reset(self, fourplay: 'FourPlay'):
            self.fourplay = fourplay
            self[:] = [None] * fourplay.num_columns
            for column in range(fourplay.num_columns):
                for row in range(fourplay.num_rows):
                    disc = fourplay[row, column]
                    if disc.player is None or row == fourplay.num_rows:
                        self[column] = disc
                    else:
                        break

    class Player:
        def __init__(self, symbol: str, fourplay: 'FourPlay'=None):
            self.fourplay = fourplay
            self.symbol = symbol

        def __str__(self):
            return self.symbol

        def play(self) -> 'FourPlay.Disc':
            raise NotImplementedError()

        def reset(self):
            pass

    num_rows, num_columns = 6, 7

    def __init__(self, o: 'FourPlay.Player'=None, x: 'FourPlay.Player'=None):
        super(FourPlay, self).__init__()
        if o is None:
            o = FourPlay.Player('O', self)
        if x is None:
            x = FourPlay.Player('X', self)
        self.o, self.x = o, x
        self.o.fourplay, self.x.fourplay = self, self
        self.frontier = FourPlay.Frontier(self)
        for row in range(self.num_rows):
            for column in range(self.num_columns):
                self[row, column] = FourPlay.Disc(self, row, column)
        self.frontier.reset(self)

    def __iter__(self):
        return iter(self.values())

    def __str__(self):
        string = ""
        for row in range(self.num_rows):
            for column in range(self.num_columns):
                string += str(self[row, column])
            string += "\n"
        return string

    @classmethod
    def build(cls, scenario: List[str], o: 'FourPlay.Player', x: 'FourPlay.Player') -> 'FourPlay':
        fourplay = cls(o=o, x=x)
        symbol_map = {fourplay.o.symbol: fourplay.o, fourplay.x.symbol: fourplay.x}
        for row, scenario_row in enumerate(scenario):
            for column, symbol in enumerate(scenario_row):
                disc = fourplay[row, column]
                disc.player = symbol_map.get(symbol, None)
        fourplay.frontier.reset(fourplay)
        return fourplay

    def set(self, disc: 'FourPlay.Disc', player: 'FourPlay.Player', notify: bool=False):
        assert disc.player is None
        disc.player = player
        self.frontier.increase(disc.column, notify)
        disc.notify(notify)

    def unset(self, disc: 'FourPlay.Disc', notify: bool=False):
        assert disc.player is not None
        disc.player = None
        self.frontier.decrease(disc.column, notify)
        disc.notify(notify)

    def score(self, disc: 'FourPlay.Disc') -> Optional[int]:
        for forward in [(+1, 0), (0, +1), (+1, +1), (+1, -1)]:
            rearward = -forward[0], -forward[1]
            connected = disc.crawl(forward, disc.player) + disc.crawl(rearward, disc.player) - 1
            if connected >= 4:
                return 1
        if len(self.frontier.choices()) == 0:
            return 0
        return None

    def round(self, notify: bool=False) -> Optional[int]:
        o_disc = self.o.play()
        assert o_disc in self.frontier
        self.set(o_disc, self.o, notify)
        o_score = self.score(o_disc)
        if o_score is not None:
            if notify:
                self.highlight(o_disc)
            return +o_score

        x_disc = self.x.play()
        assert x_disc in self.frontier
        self.set(x_disc, self.x, notify)
        x_score = self.score(x_disc)
        if x_score is not None:
            if notify:
                self.highlight(x_disc)
            return -x_score
        return None

    def highlight(self, disc: 'FourPlay.Disc') -> bool:
        for forward in [(+1, 0), (0, +1), (+1, +1), (+1, -1)]:
            rearward = -forward[0], -forward[1]
            connected = disc.crawl(forward, disc.player) + disc.crawl(rearward, disc.player) - 1
            if connected >= 4:
                disc.crawl(forward, disc.player, True)
                disc.crawl(rearward, disc.player, True)
                return True
        return False

    def reset(self, notify: bool=True):
        for disc in self:
            disc.reset(False)
        self.frontier.reset(self)
        self.o.reset()
        self.x.reset()
        for disc in self:
            disc.notify(notify)


if __name__ == '__main__':
    from PyQt5.QtWidgets import QApplication
    import sys
    import ui

    application = QApplication(sys.argv)
    qFourPlay = ui.QFourPlay()
    sys.exit(application.exec())
