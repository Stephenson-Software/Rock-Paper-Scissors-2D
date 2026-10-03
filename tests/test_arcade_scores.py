import os
import sys
import types
import unittest
from unittest.mock import Mock, patch

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "src"))

import arcade_scores

class BridgeTest(unittest.TestCase):
    def setUp(self):
        self.evaluate = Mock()
        self.bridge = arcade_scores.ArcadeScores(self.evaluate)

    def test_submitCallsTheClientWithANumber(self):
        self.bridge.submit("best-streak", 7)
        self.evaluate.assert_called_once_with(
            'void (window.ArcadeScores && window.ArcadeScores.submit("best-streak", 7))')

    def test_unlockCallsTheClient(self):
        self.bridge.unlock("first-win")
        self.evaluate.assert_called_once_with(
            'void (window.ArcadeScores && window.ArcadeScores.unlock("first-win"))')

    def test_argumentsAreQuotedAsJson(self):
        self.bridge.unlock('x"); alert(1); ("')
        expression = self.evaluate.call_args.args[0]
        self.assertIn('unlock("x\\"); alert(1); (\\"")', expression)

    def test_aFailingCallNeverReachesTheGame(self):
        self.evaluate.side_effect = RuntimeError("no page")
        self.bridge.submit("best-streak", 1)
        self.bridge.unlock("first-win")

class StartTest(unittest.TestCase):
    def test_desktopGetsNoBridge(self):
        with patch("arcade_scores.sys.platform", "linux"):
            self.assertIsNone(arcade_scores.start())

    def test_browserLoadsTheVendoredClientIntoThePage(self):
        window = Mock()
        fakePlatform = types.SimpleNamespace(window=window)
        with patch("arcade_scores.sys.platform", "emscripten"), \
                patch.dict(sys.modules, {"platform": fakePlatform}):
            bridge = arcade_scores.start()
        with open(arcade_scores.CLIENT_SCRIPT, encoding="utf-8") as source:
            window.eval.assert_called_once_with(source.read())
        self.assertIs(bridge.evaluate, window.eval)

    def test_aPageThatCannotLoadTheClientGetsNoBridge(self):
        window = Mock()
        window.eval.side_effect = RuntimeError("blocked")
        with patch("arcade_scores.sys.platform", "emscripten"), \
                patch.dict(sys.modules, {"platform": types.SimpleNamespace(window=window)}):
            self.assertIsNone(arcade_scores.start())

    def test_theVendoredClientIsTheArcadeSocialOne(self):
        with open(arcade_scores.CLIENT_SCRIPT, encoding="utf-8") as source:
            self.assertTrue(source.readline().startswith("/* arcade-scores.js 0.1.0 (arcade-social, RFC 0014)"))

if __name__ == "__main__":
    unittest.main()
