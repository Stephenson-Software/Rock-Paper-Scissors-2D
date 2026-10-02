import asyncio
import os
import random
import sys
import unittest
from contextlib import ExitStack
from unittest.mock import AsyncMock, Mock, patch

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
            patcher = patch("rockpaperscissors." + name, new_callable=AsyncMock)
            self.outcomes[name] = patcher.start()
            self.addCleanup(patcher.stop)

    def assertOutcome(self, playerChoice, computerChoice, expected):
        asyncio.run(rockpaperscissors.whoWon(playerChoice, computerChoice))
        for name, outcome in self.outcomes.items():
            if name == expected:
                outcome.assert_awaited_once_with(playerChoice, computerChoice)
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

class PlayerChoiceTest(unittest.TestCase):
    def setUp(self):
        self.addCleanup(setattr, rockpaperscissors, "chosenMove", None)

    def assertRecordsMove(self, playerChose, playerChoice):
        rockpaperscissors.chosenMove = None
        playerChose()
        self.assertEqual(rockpaperscissors.chosenMove, playerChoice)

    def test_rockButtonRecordsRock(self):
        self.assertRecordsMove(rockpaperscissors.playerChoseRock, "rock")

    def test_paperButtonRecordsPaper(self):
        self.assertRecordsMove(rockpaperscissors.playerChosePaper, "paper")

    def test_scissorsButtonRecordsScissors(self):
        self.assertRecordsMove(rockpaperscissors.playerChoseScissors, "scissors")

    def assertPlaysRound(self, playerChoice):
        with patch("rockpaperscissors.getComputerChoice", return_value="paper"), \
             patch("rockpaperscissors.whoWon", new_callable=AsyncMock) as whoWon:
            asyncio.run(rockpaperscissors.playRound(playerChoice))
        whoWon.assert_awaited_once_with(playerChoice, "paper")

    def test_playRoundPlaysRockAgainstTheComputer(self):
        self.assertPlaysRound("rock")

    def test_playRoundPlaysPaperAgainstTheComputer(self):
        self.assertPlaysRound("paper")

    def test_playRoundPlaysScissorsAgainstTheComputer(self):
        self.assertPlaysRound("scissors")

class DecisionScreenTest(CounterResettingTestCase):
    def runDecisionScreen(self):
        with ExitStack() as stack:
            graphik, _ = enterScreenPatches(stack, [])
            with self.assertRaises(LoopDidNotExit):
                asyncio.run(rockpaperscissors.decisionScreen())
        return graphik

    def pressButtonOnFirstFrame(self, label):
        def drawButtonStub(*args):
            if args[7] == label and not state["pressed"]:
                state["pressed"] = True
                args[8]()
        state = {"pressed": False}
        with ExitStack() as stack:
            graphik, _ = enterScreenPatches(stack, [])
            graphik.drawButton.side_effect = drawButtonStub
            stack.enter_context(patch("rockpaperscissors.getComputerChoice", return_value="paper"))
            whoWon = stack.enter_context(patch("rockpaperscissors.whoWon", new_callable=AsyncMock))
            with self.assertRaises(LoopDidNotExit):
                asyncio.run(rockpaperscissors.decisionScreen())
        return whoWon

    def test_buttonsAreLabelledAndWiredLeftToRight(self):
        graphik = self.runDecisionScreen()
        firstFrame = graphik.drawButton.call_args_list[:3]
        labels = [call.args[7] for call in firstFrame]
        callbacks = [call.args[8] for call in firstFrame]
        xPositions = [call.args[0] for call in firstFrame]
        self.assertEqual(labels, ["Rock", "Paper", "Scissors"])
        self.assertEqual(callbacks, [
            rockpaperscissors.playerChoseRock,
            rockpaperscissors.playerChosePaper,
            rockpaperscissors.playerChoseScissors,
        ])
        self.assertEqual(xPositions, sorted(xPositions))

    def test_pressingAButtonPlaysExactlyOneRoundWithThatMove(self):
        for label, move in (("Rock", "rock"), ("Paper", "paper"), ("Scissors", "scissors")):
            with self.subTest(label=label):
                whoWon = self.pressButtonOnFirstFrame(label)
                whoWon.assert_awaited_once_with(move, "paper")

    def runWithEvents(self, events):
        with ExitStack() as stack:
            enterScreenPatches(stack, events)
            stack.enter_context(patch("pygame.mouse.get_pressed", return_value=(False, False, False)))
            stack.enter_context(patch("rockpaperscissors.getComputerChoice", return_value="paper"))
            whoWon = stack.enter_context(patch("rockpaperscissors.whoWon", new_callable=AsyncMock))
            with self.assertRaises(LoopDidNotExit):
                asyncio.run(rockpaperscissors.decisionScreen())
        return whoWon

    def pressEvent(self, pos, button=1):
        event = Mock()
        event.type = pygame.MOUSEBUTTONDOWN
        event.button = button
        event.pos = pos
        return event

    def test_aTapOrQuickClickOnAButtonPlaysThatMove(self):
        # press and release in the same frame: the button is no longer held when drawn
        middle = rockpaperscissors.displayWidth // 2 - 50
        for xpos, move in ((middle - 200, "rock"), (middle, "paper"), (middle + 200, "scissors")):
            with self.subTest(move=move):
                whoWon = self.runWithEvents([self.pressEvent((xpos + 50, 350))])
                whoWon.assert_awaited_once_with(move, "paper")

    def test_aPressOutsideEveryButtonPlaysNothing(self):
        whoWon = self.runWithEvents([self.pressEvent((50, 350)), self.pressEvent((450, 250))])
        whoWon.assert_not_called()

    def test_aRightButtonPressPlaysNothing(self):
        middle = rockpaperscissors.displayWidth // 2 - 50
        whoWon = self.runWithEvents([self.pressEvent((middle - 150, 350), button=3)])
        whoWon.assert_not_called()

    def test_noPressMeansNoRound(self):
        with ExitStack() as stack:
            enterScreenPatches(stack, [])
            whoWon = stack.enter_context(patch("rockpaperscissors.whoWon", new_callable=AsyncMock))
            with self.assertRaises(LoopDidNotExit):
                asyncio.run(rockpaperscissors.decisionScreen())
        whoWon.assert_not_called()

    def test_tallyShowsTheCurrentCounters(self):
        rockpaperscissors.wins = 2
        rockpaperscissors.losses = 1
        rockpaperscissors.ties = 3
        graphik = self.runDecisionScreen()
        text = drawnText(graphik)
        self.assertIn("Wins: 2", text)
        self.assertIn("Losses: 1", text)
        self.assertIn("Ties: 3", text)

class MainTest(unittest.TestCase):
    def setUp(self):
        # The dummy drivers keep main() from opening a real window or touching the audio device.
        self.addCleanup(self.resetDisplayGlobals)
        self.addCleanup(pygame.display.quit)
        patcher = patch.dict(os.environ, {"SDL_VIDEODRIVER": "dummy", "SDL_AUDIODRIVER": "dummy"})
        patcher.start()
        self.addCleanup(patcher.stop)

    def resetDisplayGlobals(self):
        rockpaperscissors.gameDisplay = None
        rockpaperscissors.graphik = None
        rockpaperscissors.clock = None

    def test_opensTheWindowThenEntersTheDecisionScreen(self):
        with patch("rockpaperscissors.decisionScreen", new_callable=AsyncMock) as decisionScreen:
            asyncio.run(rockpaperscissors.main())
        self.assertEqual(rockpaperscissors.gameDisplay.get_size(), (rockpaperscissors.displayWidth, rockpaperscissors.displayHeight))
        self.assertEqual(pygame.display.get_caption()[0], "Rock Paper Scissors")
        self.assertIs(rockpaperscissors.graphik.gameDisplay, rockpaperscissors.gameDisplay)
        # pygame.time.Clock is a factory function on older pygame releases, not a type.
        self.assertIsInstance(rockpaperscissors.clock, type(pygame.time.Clock()))
        decisionScreen.assert_awaited_once_with()

    def test_directCallDoesNotStartUsageReporting(self):
        with patch("rockpaperscissors.decisionScreen", new_callable=AsyncMock), \
                patch("rockpaperscissors.startUsageReporting") as startUsageReporting:
            asyncio.run(rockpaperscissors.main())
        startUsageReporting.assert_not_called()
        self.assertIsNone(rockpaperscissors.usage)

    def test_launchStartsUsageReportingBeforeTheWindowOpens(self):
        self.addCleanup(setattr, rockpaperscissors, "usage", None)
        with patch("rockpaperscissors.decisionScreen", new_callable=AsyncMock), \
                patch("rockpaperscissors.startUsageReporting") as startUsageReporting:
            asyncio.run(rockpaperscissors.main(reportUsage=True))
        startUsageReporting.assert_called_once_with()
        self.assertIs(rockpaperscissors.usage, startUsageReporting.return_value)

    def test_browserLaunchDoesNotStartUsageReporting(self):
        # the trace client sends from a thread, which the pygbag build cannot start
        self.addCleanup(setattr, rockpaperscissors, "usage", None)
        with patch("rockpaperscissors.decisionScreen", new_callable=AsyncMock), \
                patch("rockpaperscissors.sys.platform", "emscripten"), \
                patch("rockpaperscissors.startUsageReporting") as startUsageReporting:
            asyncio.run(rockpaperscissors.main(reportUsage=True))
        startUsageReporting.assert_not_called()
        self.assertIsNone(rockpaperscissors.usage)

class BrowserSeedingTest(unittest.TestCase):
    def setUp(self):
        self.addCleanup(MainTest.resetDisplayGlobals, self)
        self.addCleanup(pygame.display.quit)
        patcher = patch.dict(os.environ, {"SDL_VIDEODRIVER": "dummy", "SDL_AUDIODRIVER": "dummy"})
        patcher.start()
        self.addCleanup(patcher.stop)

    def runMain(self, platform):
        with patch("rockpaperscissors.decisionScreen", new_callable=AsyncMock), \
                patch("rockpaperscissors.sys.platform", platform), \
                patch("rockpaperscissors.time.time_ns", return_value=123456789), \
                patch("rockpaperscissors.random.seed") as seed:
            asyncio.run(rockpaperscissors.main())
        return seed

    def test_browserLaunchSeedsTheComputerFromTheClock(self):
        self.runMain("emscripten").assert_called_once_with(123456789)

    def test_desktopLaunchLeavesPythonsOwnSeeding(self):
        self.runMain("linux").assert_not_called()

class RoundReportingTest(CounterResettingTestCase):
    def setUp(self):
        super().setUp()
        self.usage = Mock()
        patcher = patch("rockpaperscissors.usage", self.usage)
        patcher.start()
        self.addCleanup(patcher.stop)

    def playRound(self, resultScreen, playerChoice, computerChoice):
        with ExitStack() as stack:
            enterScreenPatches(stack, [])
            asyncio.run(resultScreen(playerChoice, computerChoice))

    def test_eachResultReportsARoundWithItsResult(self):
        self.playRound(rockpaperscissors.win, "rock", "scissors")
        self.playRound(rockpaperscissors.lose, "rock", "paper")
        self.playRound(rockpaperscissors.tie, "rock", "rock")
        self.assertEqual([c.args for c in self.usage.report.call_args_list],
                         [("round-played",)] * 3)
        self.assertEqual([c.kwargs["tags"] for c in self.usage.report.call_args_list],
                         [{"result": "win"}, {"result": "lose"}, {"result": "tie"}])

    def test_noClientMeansNothingIsReported(self):
        with patch("rockpaperscissors.usage", None):
            self.playRound(rockpaperscissors.win, "rock", "scissors")
        self.usage.report.assert_not_called()

class ScoreCounterTest(CounterResettingTestCase):
    def runResultScreen(self, resultScreen, playerChoice, computerChoice):
        with ExitStack() as stack:
            enterScreenPatches(stack, [])
            asyncio.run(resultScreen(playerChoice, computerChoice))

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
                asyncio.run(rockpaperscissors.decisionScreen())
            self.assertIn("Rock, Paper, or Scissors?", drawnText(graphik))
            self.assertEqual(graphik.drawButton.call_count, 3 * (frameLimit - 1))

    def test_resultScreenDrawsWhenTheEventQueueIsEmpty(self):
        with ExitStack() as stack:
            graphik, _ = enterScreenPatches(stack, [])
            asyncio.run(rockpaperscissors.win("rock", "scissors"))
            self.assertIn("You win!", drawnText(graphik))

    def test_resultScreenPumpsEventsInsteadOfSleeping(self):
        with ExitStack() as stack:
            _, eventGet = enterScreenPatches(stack, [])
            sleep = stack.enter_context(patch("time.sleep"))
            asyncio.run(rockpaperscissors.lose("rock", "paper"))
            sleep.assert_not_called()
            self.assertGreater(eventGet.call_count, 10)

    def test_resultScreenEndsAfterItsConfiguredDuration(self):
        expectedFrames = rockpaperscissors.resultScreenDuration // millisecondsPerFrame
        with ExitStack() as stack:
            _, eventGet = enterScreenPatches(stack, [])
            asyncio.run(rockpaperscissors.tie("rock", "rock"))
            self.assertEqual(eventGet.call_count, expectedFrames)

    def test_everyResultScreenFrameYieldsToTheEventLoop(self):
        # the browser build (pygbag) freezes unless each frame awaits asyncio.sleep(0)
        with ExitStack() as stack:
            _, eventGet = enterScreenPatches(stack, [])
            sleep = stack.enter_context(patch("rockpaperscissors.asyncio.sleep", new_callable=AsyncMock))
            asyncio.run(rockpaperscissors.tie("rock", "rock"))
            self.assertEqual(sleep.await_count, eventGet.call_count)
            sleep.assert_awaited_with(0)

    def test_everyDecisionScreenFrameYieldsToTheEventLoop(self):
        with ExitStack() as stack:
            _, eventGet = enterScreenPatches(stack, [])
            sleep = stack.enter_context(patch("rockpaperscissors.asyncio.sleep", new_callable=AsyncMock))
            with self.assertRaises(LoopDidNotExit):
                asyncio.run(rockpaperscissors.decisionScreen())
            self.assertEqual(sleep.await_count, eventGet.call_count - 1)
            sleep.assert_awaited_with(0)

    def test_quitDuringAResultScreenIsHonoured(self):
        quitEvent = Mock()
        quitEvent.type = pygame.QUIT
        with ExitStack() as stack:
            enterScreenPatches(stack, [quitEvent])
            stack.enter_context(patch("pygame.quit"))
            with self.assertRaises(SystemExit):
                asyncio.run(rockpaperscissors.win("rock", "scissors"))

    def test_quitDuringTheDecisionScreenIsHonoured(self):
        quitEvent = Mock()
        quitEvent.type = pygame.QUIT
        with ExitStack() as stack:
            enterScreenPatches(stack, [quitEvent])
            pygameQuit = stack.enter_context(patch("pygame.quit"))
            with self.assertRaises(SystemExit):
                asyncio.run(rockpaperscissors.decisionScreen())
            pygameQuit.assert_called_once_with()

class ResultScreenTextTest(CounterResettingTestCase):
    def assertResultScreenShows(self, resultScreen, heading):
        with ExitStack() as stack:
            graphik, _ = enterScreenPatches(stack, [])
            asyncio.run(resultScreen("paper", "scissors"))
            firstFrame = drawnText(graphik)[:3]
        self.assertEqual(firstFrame, [heading, "Player Choice: paper", "Computer Choice: scissors"])

    def test_winScreenShowsTheHeadingAndBothChoices(self):
        self.assertResultScreenShows(rockpaperscissors.win, "You win!")

    def test_loseScreenShowsTheHeadingAndBothChoices(self):
        self.assertResultScreenShows(rockpaperscissors.lose, "You lost!")

    def test_tieScreenShowsTheHeadingAndBothChoices(self):
        self.assertResultScreenShows(rockpaperscissors.tie, "It was a tie!")

if __name__ == "__main__":
    unittest.main()
