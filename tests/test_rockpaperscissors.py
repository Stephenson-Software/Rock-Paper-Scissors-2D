import os
import random
import sys
import unittest
from contextlib import ExitStack
from unittest.mock import Mock, patch

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "src"))

import pygame

import rockpaperscissors

validChoices = ["rock", "paper", "scissors"]

frameLimit = 400
millisecondsPerFrame = 16

class LoopDidNotExit(Exception):
    pass

def makeEventGetStub(events):
    state = {"framesLeft": frameLimit, "delivered": False}

    def eventGetStub():
        state["framesLeft"] -= 1
        if state["framesLeft"] <= 0:
            raise LoopDidNotExit()
        if state["delivered"]:
            return []
        state["delivered"] = True
        return list(events)

    return eventGetStub

def makeGetTicksStub():
    state = {"ticks": 0}

    def getTicksStub():
        current = state["ticks"]
        state["ticks"] += millisecondsPerFrame
        return current

    return getTicksStub

def enterScreenPatches(stack, events):
    stack.enter_context(patch.object(rockpaperscissors, "gameDisplay", Mock()))
    graphik = stack.enter_context(patch.object(rockpaperscissors, "graphik", Mock()))
    stack.enter_context(patch.object(rockpaperscissors, "clock", Mock()))
    eventGet = stack.enter_context(patch("pygame.event.get", side_effect=makeEventGetStub(events)))
    stack.enter_context(patch("pygame.time.get_ticks", side_effect=makeGetTicksStub()))
    stack.enter_context(patch("pygame.display.update"))
    return graphik, eventGet

def drawnText(graphik):
    return [call.args[0] for call in graphik.drawText.call_args_list]

class CounterResettingTestCase(unittest.TestCase):
    def setUp(self):
        self.resetCounters()
        self.addCleanup(self.resetCounters)

    def resetCounters(self):
        rockpaperscissors.wins = 0
        rockpaperscissors.losses = 0
        rockpaperscissors.ties = 0

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
        self.addCleanup(random.setstate, random.getstate())
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

class ScoreCounterTest(CounterResettingTestCase):
    def runResultScreen(self, resultScreen, playerChoice, computerChoice):
        with ExitStack() as stack:
            enterScreenPatches(stack, [])
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

class RenderLoopTest(CounterResettingTestCase):
    def test_decisionScreenDrawsWhenTheEventQueueIsEmpty(self):
        with ExitStack() as stack:
            graphik, _ = enterScreenPatches(stack, [])
            with self.assertRaises(LoopDidNotExit):
                rockpaperscissors.decisionScreen()
            self.assertIn("Rock, Paper, or Scissors?", drawnText(graphik))
            self.assertEqual(graphik.drawButton.call_count, 3 * (frameLimit - 1))

    def test_resultScreenDrawsWhenTheEventQueueIsEmpty(self):
        with ExitStack() as stack:
            graphik, _ = enterScreenPatches(stack, [])
            rockpaperscissors.win("rock", "scissors")
            self.assertIn("You win!", drawnText(graphik))

    def test_resultScreenPumpsEventsInsteadOfSleeping(self):
        with ExitStack() as stack:
            _, eventGet = enterScreenPatches(stack, [])
            sleep = stack.enter_context(patch("time.sleep"))
            rockpaperscissors.lose("rock", "paper")
            sleep.assert_not_called()
            self.assertGreater(eventGet.call_count, 10)

    def test_resultScreenEndsAfterItsConfiguredDuration(self):
        expectedFrames = rockpaperscissors.resultScreenDuration // millisecondsPerFrame
        with ExitStack() as stack:
            _, eventGet = enterScreenPatches(stack, [])
            rockpaperscissors.tie("rock", "rock")
            self.assertEqual(eventGet.call_count, expectedFrames)

    def test_quitDuringAResultScreenIsHonoured(self):
        quitEvent = Mock()
        quitEvent.type = pygame.QUIT
        with ExitStack() as stack:
            enterScreenPatches(stack, [quitEvent])
            stack.enter_context(patch("pygame.quit"))
            with self.assertRaises(SystemExit):
                rockpaperscissors.win("rock", "scissors")

if __name__ == "__main__":
    unittest.main()
