import unittest
from typing import Tuple, List, Optional

from fourplay import FourPlay


class DepthFirstSearchAI(FourPlay.Player):

    recursion_limit = 8

    def play(self) -> FourPlay.Disc:
        def recursive_best(fourplay: FourPlay, myself: FourPlay.Player, opponent: FourPlay.Player,
                           myself_best_result: Tuple[int, Optional[FourPlay.Disc]]=(-2, None),
                           opponent_best_result: Tuple[int, Optional[FourPlay.Disc]]=(+2, None),
                           recursion_level: int=1):
            for disc in fourplay.frontier.choices(shuffle=True):
                fourplay.set(disc, myself)
                myself_result = (fourplay.score(disc), disc)
                if myself_result[0] is None:
                    if recursion_level < self.recursion_limit:
                        subtree_myself_best_result = (-myself_best_result[0], myself_best_result[1])
                        subtree_opponent_best_result = (-opponent_best_result[0], opponent_best_result[1])
                        opponent_result = recursive_best(fourplay, opponent, myself,
                                                         subtree_opponent_best_result,
                                                         subtree_myself_best_result,
                                                         recursion_level + 1)
                        myself_result = (-opponent_result[0], myself_result[1])
                    else:
                        myself_result = (-1 / self.recursion_limit, myself_result[1])
                else:
                    myself_result = (myself_result[0] / recursion_level, myself_result[1])
                fourplay.unset(disc)

                if myself_result[0] > myself_best_result[0]:
                    myself_best_result = myself_result
                if opponent_best_result[0] <= myself_best_result[0]:
                    break

            return myself_best_result

        opponent = self.fourplay.x if self == self.fourplay.o else self.fourplay.o
        best_result, best_disc = recursive_best(self.fourplay, self, opponent)
        return best_disc


# region Unit Tests


class TestDepthFirstSearchAI(unittest.TestCase):

    Situations = {
        'Finish': [
            'XXXOXX#',
            'OOOXOOO',
            'XXXOXXX',
            'OOOXOOO',
            'XXXOXXX',
            'OOOXOOO'],
        'EasyWin': [
            '-------',
            '-------',
            '-------',
            '-------',
            '-------',
            'OOO#XXX'],
        'DontScrewUp': [
            '-------',
            '-------',
            '-------',
            'X------',
            'X------',
            'OOO#---'],
        'DontMessUp': [
            '-------',
            '-------',
            '#------',
            'O------',
            'O---X--',
            'O--XX--'],
        'DontF__kUp': [
            '-------',
            '-------',
            '#------',
            'OO-----',
            'OXO----',
            'OXXOXXX']
    }

    @staticmethod
    def find(scenario: List[str], char: str) -> tuple:
        row_line_with_char = [(row, line) for row, line in enumerate(scenario) if char in line]
        assert len(row_line_with_char) == 1
        row, line = row_line_with_char[0]
        return row, line.find(char)

    def play(self, scenario: List[str], o: FourPlay.Player, x: FourPlay.Player):
        fourplay = FourPlay.build(scenario, o=o, x=x)
        disc = x.play()
        correct = self.find(scenario, '#')
        self.assertEqual((disc.row, disc.column), correct)

    def test_basics(self):
        dummy = FourPlay.Player('O')
        ai = DepthFirstSearchAI('X')
        self.play(self.Situations['Finish'], o=dummy, x=ai)
        self.play(self.Situations['EasyWin'], o=dummy, x=ai)
        self.play(self.Situations['DontScrewUp'], o=dummy, x=ai)
        self.play(self.Situations['DontMessUp'], o=dummy, x=ai)
        self.play(self.Situations['DontF__kUp'], o=dummy, x=ai)

    def test_ai_vs_ai(self):
        o, x = DepthFirstSearchAI('O'), DepthFirstSearchAI('X')
        fourplay = FourPlay(o, x)
        while True:
            score = fourplay.round()
            if score is not None:
                break
        self.assertEqual(score, +1, "AI vs AI game must be always won by the starting player:\n" + str(fourplay))


# endregion
