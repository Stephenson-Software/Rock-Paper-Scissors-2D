import os
import runpy
import sys
import unittest
from unittest.mock import AsyncMock, patch

srcDir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "src")
sys.path.insert(0, srcDir)

import pygame

import rockpaperscissors

browserEntryPoint = os.path.join(srcDir, "main.py")
desktopEntryPoint = os.path.join(srcDir, "rockpaperscissors.py")

class BrowserEntryPointTest(unittest.TestCase):
    # src/main.py is what pygbag runs; running it here with rockpaperscissors.main replaced
    # by a mock opens no window and starts no loop
    def runEntryPoint(self):
        with patch.object(rockpaperscissors, "main", new_callable=AsyncMock) as main:
            namespace = runpy.run_path(browserEntryPoint)
        return main, namespace

    def test_runsTheGameOnceAsALaunch(self):
        main, namespace = self.runEntryPoint()
        main.assert_awaited_once_with(reportUsage=True)

    def test_importsPygameForPygbag(self):
        # pygbag loads only the packages main.py itself imports into the browser
        main, namespace = self.runEntryPoint()
        self.assertIs(namespace["pygame"], pygame)

class DesktopEntryPointTest(unittest.TestCase):
    def test_runsTheGameOnceAsALaunch(self):
        # the script defines its own main(), so asyncio.run is replaced instead: the coroutine
        # it is handed never starts, which opens no window and reports nothing
        with patch("asyncio.run") as run:
            runpy.run_path(desktopEntryPoint, run_name="__main__")
        run.assert_called_once()
        coroutine = run.call_args.args[0]
        self.addCleanup(coroutine.close)
        self.assertEqual(coroutine.cr_code.co_name, "main")
        self.assertIs(coroutine.cr_frame.f_locals["reportUsage"], True)

    def test_theTallyAndTheStreakStartAtZero(self):
        # a fresh copy of the module: the other test modules reset the imported one's counters
        namespace = runpy.run_path(desktopEntryPoint)
        for counter in ("wins", "losses", "ties", "streak", "bestStreak"):
            self.assertEqual(namespace[counter], 0, counter)

if __name__ == "__main__":
    unittest.main()
