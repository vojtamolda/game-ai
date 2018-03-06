import copy
import math
import pickle
import random
import pathlib
import unittest
from typing import Tuple, List, Optional

from tictactoe import TicTacToe


class MinimaxAI(TicTacToe.Player):

    class Graph(TicTacToe.Player.Graph):
        def __init__(self, gameboard: TicTacToe.Gameboard, player: 'MinimaxAI'):
            self.transpositions = TicTacToe.Transpositions()
            super().__init__(gameboard, player)

        def add_node(self, gameboard: TicTacToe.Gameboard, **attrs) -> TicTacToe.Gameboard:
            equivalent = self.transpositions.equivalent(gameboard)
            if equivalent is None:
                equivalent = gameboard
                self.transpositions[equivalent] = None

            label = f"{str(equivalent)}"
            super().add_node(equivalent, label=label)
            return equivalent

    def play(self, gameboard: TicTacToe.Gameboard) -> TicTacToe.Tile:
        best_score, best_tile = self.minimax(gameboard)
        return best_tile

    def minimax(self, gameboard: TicTacToe.Gameboard, recursion_level: int = 1) -> Tuple[int, TicTacToe.Tile]:
        if gameboard.next == self:
            maximize, best_score = True, -math.inf
        else:
            maximize, best_score = False, +math.inf
        best_tile = None

        for tile in gameboard.tiles():
            following = gameboard.following(tile)
            score = following.score(self)
            if score is None:
                score, opponent_tile = self.minimax(following, recursion_level + 1)
            else:
                score /= recursion_level

            if maximize is True and score > best_score:
                best_score, best_tile = score, tile
            if maximize is False and score < best_score:
                best_score, best_tile = score, tile
        return best_score, best_tile


class MonteCarloSearchAI(TicTacToe.Player):

    class Graph(TicTacToe.Player.Graph):
        def add_node(self, gameboard: TicTacToe.Gameboard, **attrs) -> TicTacToe.Gameboard:
            equivalent = self.player.storage.equivalent(gameboard)
            if equivalent is None:
                equivalent = gameboard
                (visits, wins) = (0, '?')
            else:
                (visits, wins) = self.player.storage[equivalent]

            label = f"{str(equivalent)}\n{visits}|{wins}"
            tooltip = f"visits={visits} wins={wins}"
            super().add_node(equivalent, label=label, tooltip=tooltip)
            return equivalent

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.transpositions = TicTacToe.Transpositions()

    def ucb(self, gameboard: TicTacToe.Gameboard, following: TicTacToe.Gameboard) -> float:
        (gb_visits, gb_wins) = self.transpositions[gameboard]
        (fo_visits, fo_wins) = self.transpositions[following]
        fo_wins = +fo_wins if gameboard.next == self else -fo_wins
        ucb = fo_wins / fo_visits + 1.0 * math.sqrt(math.log(gb_visits) / fo_visits)
        return ucb

    def select(self, gameboard: TicTacToe.Gameboard) -> List[TicTacToe.Gameboard]:
        if gameboard.outcome is not None:
            return [gameboard]

        ucbs_followings = []
        for following in (gameboard.following(tile) for tile in gameboard.tiles()):
            if following not in self.transpositions:
                return [gameboard]
            ucbs_followings += [(self.ucb(gameboard, following), following)]
        _, max_ucb_following = max(ucbs_followings, key=lambda ug: ug[0])

        max_ucb_followings = self.select(max_ucb_following)
        return [gameboard] + max_ucb_followings

    def expand(self, gameboard: TicTacToe.Gameboard) -> int:
        if gameboard.outcome is not None:
            return gameboard.score(self)

        score = 0
        for following in (gameboard.following(tile) for tile in gameboard.tiles()):
            (visits, wins) = self.transpositions[following] if following in self.transpositions else (0, 0)
            score = self.playout(following)
            self.transpositions[following] = (visits + 1, wins + score)
        return score

    def playout(self, gameboard: TicTacToe.Gameboard) -> int:
        if gameboard.outcome is not None:
            return gameboard.score(self)

        random_move = random.choice(gameboard.tiles())
        random_following = gameboard.following(random_move)
        score = self.playout(random_following)
        return score

    def backpropagate(self, gameboards: List[TicTacToe.Gameboard], score: int):
        for gameboard in gameboards:
            (visits, wins) = self.transpositions[gameboard]
            self.transpositions[gameboard] = (visits + 1, wins + score)

    def play(self, gameboard: TicTacToe.Gameboard) -> TicTacToe.Tile:
        if gameboard not in self.transpositions:
            self.transpositions[gameboard] = (0, 0)

        for repeat in range(500):
            selected_gameboards = self.select(gameboard)
            score = self.expand(selected_gameboards[-1])
            self.backpropagate(selected_gameboards, score)

        visits_tiles = []
        for tile in gameboard.tiles():
            following = gameboard.following(tile)
            (visits, wins) = self.transpositions[following]
            visits_tiles += [(visits, tile)]
        _, max_visit_tile = max(visits_tiles, key=lambda vt: vt[0])
        return max_visit_tile

    def reset(self):
        self.transpositions.clear()


class ValueFunctionAI(TicTacToe.Player):

    class Graph(TicTacToe.Player.Graph):
        def add_node(self, gameboard: TicTacToe.Gameboard, **attrs) -> TicTacToe.Gameboard:
            equivalent = self.player.value.equivalent(gameboard)
            if equivalent is None:
                equivalent, value = gameboard, math.inf
            else:
                value = self.player.value[equivalent]

            label = f"{equivalent}\n{value:+.3f}"
            tooltip = f"value={value:+.3f}"
            super().add_node(equivalent, label=label, tooltip=tooltip)
            return equivalent

    class ValueFunction(TicTacToe.Transpositions):
        File = pathlib.Path(__file__).parent / 'value.pkl'
        Alpha = 1 / 2

        def __getitem__(self, gameboard: TicTacToe.Gameboard) -> float:
            if super().__contains__(gameboard):
                return super().__getitem__(gameboard)
            else:
                return 0.0

        def transition(self, before: TicTacToe.Gameboard, after: TicTacToe.Gameboard, score: Optional[int]):
            if score is not None:
                self[after] = score
            value_before = self[before] if before in self else 0.0
            value_after = self[after] if after in self else 0.0
            self[before] = (1 - self.Alpha) * value_before + self.Alpha * value_after

        def save(self, file: pathlib.Path = None):
            if file is None:
                file = self.File
            with file.open('wb') as f:
                pickle.dump(self, f)

        @classmethod
        def load(cls, file: pathlib.Path = None) -> 'ValueFunctionAI.ValueFunction':
            if file is None:
                file = cls.File
            if file.exists():
                with file.open('rb') as f:
                    value_function = pickle.load(f)
            else:
                value_function = cls()
            return value_function

    Epsilon = 1 / 5

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.epsilon = 0.0
        try:
            self.value = self.ValueFunction.load()
        except FileExistsError:
            self.value = self.ValueFunction()

    def play(self, gameboard: TicTacToe.Gameboard) -> TicTacToe.Tile:
        if random.random() < self.epsilon:
            return random.choice(gameboard.tiles())

        values_tiles = []
        for tile in gameboard.tiles():
            following = gameboard.following(tile)
            value = self.value[following]
            values_tiles += [(value, tile)]

        max_value_tile = max(values_tiles, key=lambda vt: vt[0])
        optimal = [value_tile for value_tile in values_tiles if value_tile[0] == max_value_tile[0]]
        return random.choice(optimal)[1]

    def train(self, start: TicTacToe, num_games: int = 1):
        self.epsilon = self.Epsilon

        wins, ties = 0, 0
        for game in range(num_games):
            tictactoe = TicTacToe(x=start.x, o=start.o, gameboard=copy.copy(start.gameboard))

            score = None
            while score is None:
                before = copy.copy(tictactoe.gameboard)
                tictactoe.play()
                after = tictactoe.gameboard
                score = after.score(self)
                self.value.transition(before, after, score)

            wins = wins + 1 if score > 0 else wins
            ties = ties + 1 if score == 0 else ties

        self.epsilon = 0.0
        return wins, ties


class RandomAI(TicTacToe.Player):
    def play(self, gameboard: TicTacToe.Gameboard) -> TicTacToe.Tile:
        return random.choice(gameboard.tiles())

    def visualize(self, gameboard: 'TicTacToe.Gameboard') -> bytes:
        return b'''
        <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 54 40">
            <path d="M29.898 26.5722l-4.3921 0c-0.0118,-0.635 -0.0177,-1.0172 -0.0177,-1.1583 0,-1.4229
             0.2352,-2.5929 0.7056,-3.5102 0.4704,-0.9231 1.417,-1.952 2.8281,-3.1044 1.4111,-1.1465
             2.2578,-1.8991 2.5282,-2.2578 0.4292,-0.5585 0.6409,-1.1818 0.6409,-1.8579 0,-0.9408
             -0.3763,-1.7463 -1.1289,-2.4224 -0.7526,-0.6703 -1.7639,-1.0054 -3.0397,-1.0054 -1.2289,0
             -2.2578,0.3527 -3.0868,1.0524 -0.8232,0.6997 -1.3935,1.7698 -1.7051,3.2044l-4.4391
             -0.5527c0.1234,-2.0578 0.9995,-3.8041 2.6223,-5.2387 1.6286,-1.4346 3.757,-2.152
             6.4029,-2.152 2.7752,0 4.9859,0.7291 6.6322,2.1814 1.6404,1.4522 2.4635,3.1397 2.4635,5.0741
             0,1.0642 -0.3057,2.0755 -0.9054,3.028 -0.6056,0.9525 -1.8933,2.2519 -3.8688,3.8923 -1.0231,0.8525
             -1.6581,1.5346 -1.905,2.052 -0.2469,0.5174 -0.3587,1.4405 -0.3351,2.7752zm-4.3921 6.5087l0
             -4.8389 4.8389 0 0 4.8389 -4.8389 0z"/>
        </svg>
        '''


# region Unit Tests


class TestMinimaxAI(unittest.TestCase):
    Scenarios = {
        'Finish': [
             '#OX',
             'OXX',
             'OXO'],
        'EasyWin': [
            '#X-',
            'XOO',
            'XOO'],
        'DontScrewUp': [
            'OX-',
            'OX-',
            '#OX'],
        'DontMessUp1': [
            '#-X',
            'O--',
            'OX-'],
        'DontMessUp2': [
            '-#X',
            'OX-',
            'OXO'],
        'DontF__kUp1': [
            'XXO',
            '-O-',
            '#OX'],
        'DontF__kUp2': [
            '-#-',
            '-O-',
            '-OX']
    }

    @staticmethod
    def find(scenario: List[str], char: str) -> TicTacToe.Tile:
        row_line_with_char = [(row, line) for row, line in enumerate(scenario) if char in line]
        assert len(row_line_with_char) == 1
        row, line = row_line_with_char[0]
        return TicTacToe.Tile(row, line.find(char))

    def play(self, scenario: List[str], x: TicTacToe.Player, o: TicTacToe.Player):
        tictactoe = TicTacToe.from_scenario(scenario, x=x, o=o)
        tile = x.play(tictactoe.gameboard)
        correct = self.find(scenario, '#')
        self.assertEqual(tile, correct)

    def scenarios(self, x: TicTacToe.Player):
        dummy = TicTacToe.Player('O')
        self.play(self.Scenarios['Finish'], x=x, o=dummy)
        x.reset()
        self.play(self.Scenarios['EasyWin'], x=x, o=dummy)
        x.reset()
        self.play(self.Scenarios['DontScrewUp'], x=x, o=dummy)
        x.reset()
        self.play(self.Scenarios['DontMessUp1'], x=x, o=dummy)
        x.reset()
        self.play(self.Scenarios['DontMessUp2'], x=x, o=dummy)
        x.reset()
        self.play(self.Scenarios['DontF__kUp1'], x=x, o=dummy)
        x.reset()
        self.play(self.Scenarios['DontF__kUp2'], x=x, o=dummy)
        x.reset()

    def ai_vs_ai(self, x: TicTacToe.Player, o: TicTacToe.Player):
        tictactoe = TicTacToe(x=x, o=o)
        outcome = None

        while outcome is None:
            outcome = tictactoe.round()
        self.assertEqual(outcome, 0, "AI vs AI game must always end up in a tie:\n" + str(tictactoe))

    def test_scenarios(self):
        self.scenarios(x=MinimaxAI('X'))

    def test_ai_vs_ai(self):
        self.ai_vs_ai(x=MinimaxAI('X'), o=MinimaxAI('O'))


class TestMonteCarloSearchAI(TestMinimaxAI):

    def test_scenarios(self):
        self.scenarios(x=MonteCarloSearchAI('X'))

    def test_ai_vs_ai(self):
        self.ai_vs_ai(x=MonteCarloSearchAI('X'), o=MonteCarloSearchAI('O'))


class TestValueFunctionAI(TestMinimaxAI):

    def test_scenarios(self):
        x = ValueFunctionAI('X')
        o = RandomAI('O')

        x.value.clear()
        for scenario in self.Scenarios.values():
            tictactoe = TicTacToe.from_scenario(scenario, x=x, o=o)
            x.train(tictactoe, 100)

        self.scenarios(x=x)

    def test_ai_vs_ai(self):
        x = ValueFunctionAI('X')
        o = ValueFunctionAI('O')
        tictactoe = TicTacToe(x=x, o=o)

        x.value.clear()
        o.value.clear()
        num_batches, batch_size = 1_000, 10
        for batch in range(num_batches // batch_size):
            wins, ties = x.train(tictactoe, batch_size)
            print(f"X ({batch}/{num_batches}): Wins={wins}, Ties={ties}")
            wins, ties = o.train(tictactoe, batch_size)
            print(f"O ({batch}/{num_batches}): Wins={wins}, Ties={ties}")

        self.ai_vs_ai(x=x, o=o)
        self.ai_vs_ai(x=x, o=MinimaxAI('O'))
        self.ai_vs_ai(x=MinimaxAI('X'), o=o)

        o.value.save()


class TestRandomAI(unittest.TestCase):

    def test_ai_vs_ai(self):
        tictactoe = TicTacToe(x=RandomAI('X'), o=RandomAI('O'))
        outcome = None

        while outcome is None:
            outcome = tictactoe.round()


# endregion
