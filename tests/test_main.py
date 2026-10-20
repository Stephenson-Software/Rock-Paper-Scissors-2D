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

if __name__ == "__main__":
    unittest.main()
