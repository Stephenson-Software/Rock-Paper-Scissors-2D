import os
import random
import sys
import unittest
from unittest.mock import Mock, patch

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "src"))

import pygame

import rockpaperscissors

validChoices = ["rock", "paper", "scissors"]

class GetComputerChoiceTest(unittest.TestCase):
    def test_rollOfOneIsRock(self):
        with patch("rockpaperscissors.random.randint", return_value=1):
            self.assertEqual(rockpaperscissors.getComputerChoice(), "rock")

    def test_rollOfTwoIsPaper(self):
        with patch("rockpaperscissors.random.randint", return_value=2):
            self.assertEqual(rockpaperscissors.getComputerChoice(), "paper")

    def test_rollOfThreeIsScissors(self):
        with patch("rockpaperscissors.random.randint", return_value=3):
            self.assertEqual(rockpaperscissors.getComputerChoice(), "scissors")

    def test_everyDrawIsAValidChoice(self):
        random.seed(1)
        observed = set()
        for _ in range(200):
            choice = rockpaperscissors.getComputerChoice()
            self.assertIn(choice, validChoices)
            observed.add(choice)
        self.assertEqual(observed, set(validChoices))

class WhoWonTest(unittest.TestCase):
    def setUp(self):
        self.outcomes = {}
        for name in ("win", "lose", "tie"):
            patcher = patch("rockpaperscissors." + name)
            self.outcomes[name] = patcher.start()
            self.addCleanup(patcher.stop)

    def assertOutcome(self, playerChoice, computerChoice, expected):
        rockpaperscissors.whoWon(playerChoice, computerChoice)
        for name, outcome in self.outcomes.items():
            if name == expected:
                outcome.assert_called_once_with(playerChoice, computerChoice)
            else:
                outcome.assert_not_called()

    def test_rockTiesRock(self):
        self.assertOutcome("rock", "rock", "tie")

    def test_rockLosesToPaper(self):
        self.assertOutcome("rock", "paper", "lose")

    def test_rockBeatsScissors(self):
        self.assertOutcome("rock", "scissors", "win")

    def test_paperBeatsRock(self):
        self.assertOutcome("paper", "rock", "win")

    def test_paperTiesPaper(self):
        self.assertOutcome("paper", "paper", "tie")

    def test_paperLosesToScissors(self):
        self.assertOutcome("paper", "scissors", "lose")

    def test_scissorsLosesToRock(self):
        self.assertOutcome("scissors", "rock", "lose")

    def test_scissorsBeatsPaper(self):
        self.assertOutcome("scissors", "paper", "win")

    def test_scissorsTiesScissors(self):
        self.assertOutcome("scissors", "scissors", "tie")

class ScoreCounterTest(unittest.TestCase):
    def setUp(self):
        self.resetCounters()
        self.addCleanup(self.resetCounters)

    def resetCounters(self):
        rockpaperscissors.wins = 0
        rockpaperscissors.losses = 0
        rockpaperscissors.ties = 0

    def runResultScreen(self, resultScreen, playerChoice, computerChoice):
        event = Mock()
        event.type = pygame.USEREVENT
        with patch.object(rockpaperscissors, "gameDisplay", Mock()), \
             patch.object(rockpaperscissors, "graphik", Mock()), \
             patch("pygame.event.get", return_value=[event]), \
             patch("pygame.display.update"), \
             patch("rockpaperscissors.time.sleep"):
            resultScreen(playerChoice, computerChoice)

    def assertCounters(self, wins, losses, ties):
        self.assertEqual(rockpaperscissors.wins, wins)
        self.assertEqual(rockpaperscissors.losses, losses)
        self.assertEqual(rockpaperscissors.ties, ties)

    def test_winIncrementsWinsOnly(self):
        self.runResultScreen(rockpaperscissors.win, "rock", "scissors")
        self.assertCounters(1, 0, 0)

    def test_loseIncrementsLossesOnly(self):
        self.runResultScreen(rockpaperscissors.lose, "rock", "paper")
        self.assertCounters(0, 1, 0)

    def test_tieIncrementsTiesOnly(self):
        self.runResultScreen(rockpaperscissors.tie, "rock", "rock")
        self.assertCounters(0, 0, 1)

if __name__ == "__main__":
    unittest.main()
