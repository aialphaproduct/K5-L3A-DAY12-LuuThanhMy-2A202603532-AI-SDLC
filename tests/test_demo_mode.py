import math
import unittest

from server_preview import DEMO_GAME_SECONDS, GameServer
from simulation import DURATIONS, LANTERNS, WIN_RATIO


class DemoModeTests(unittest.TestCase):
    def test_demo_nights_reach_a_real_dawn_win(self):
        for night in (1, 2, 3):
            server = GameServer(night=night)
            server.reset(night=night, demo=True)
            lit = sum(lantern['lit'] for lantern in server.game.lanterns)
            required = math.ceil(WIN_RATIO * len(LANTERNS[night]))

            self.assertEqual(server.game.time, DEMO_GAME_SECONDS * 60)
            self.assertEqual(lit, min(len(LANTERNS[night]), required + 1))

            for _ in range(server.game.time):
                server.game.step()
            self.assertEqual(server.game.state, 'won')
            self.assertEqual(server.game.events[-1]['data']['reason'], 'dawn_survived')

    def test_normal_reset_keeps_standard_night_durations(self):
        for night in (1, 2, 3):
            server = GameServer(night=night)
            server.reset(night=night)
            self.assertEqual(server.game.time, DURATIONS[night] * 60)
            self.assertFalse(any(lantern['lit'] for lantern in server.game.lanterns))


if __name__ == '__main__':
    unittest.main()