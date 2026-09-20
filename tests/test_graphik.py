import os
import sys
import unittest
from unittest.mock import Mock, patch

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "src"))

import pygame

from Graphik import Graphik

black = (0,0,0)
white = (255,255,255)
red = (200,0,0)

surfaceWidth = 200
surfaceHeight = 100

def pixelsMatching(surface, color):
    matching = set()
    for x in range(surface.get_width()):
        for y in range(surface.get_height()):
            if surface.get_at((x, y))[:3] == color:
                matching.add((x, y))
    return matching

class GraphikTestCase(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        pygame.font.init()

    def setUp(self):
        self.surface = pygame.Surface((surfaceWidth, surfaceHeight))
        self.surface.fill(white)
        self.graphik = Graphik(self.surface)

class DrawRectangleTest(GraphikTestCase):
    def test_fillsExactlyTheRequestedRectangle(self):
        self.graphik.drawRectangle(20, 10, 30, 40, red)
        expected = {(x, y) for x in range(20, 50) for y in range(10, 50)}
        self.assertEqual(pixelsMatching(self.surface, red), expected)

class DrawTextTest(GraphikTestCase):
    def test_rendersTheTextCentredOnTheGivenPoint(self):
        self.graphik.drawText("Rock", 100, 50, 15, black)
        textWidth, textHeight = pygame.font.Font("freesansbold.ttf", 15).size("Rock")
        textRectangle = pygame.Rect(0, 0, textWidth, textHeight)
        textRectangle.center = (100, 50)
        painted = pixelsMatching(self.surface, black)
        self.assertTrue(painted)
        for pixel in painted:
            self.assertTrue(textRectangle.collidepoint(pixel))

class DrawButtonTest(GraphikTestCase):
    xpos = 20
    ypos = 10
    width = 100
    height = 40
    inside = (xpos + width // 2, ypos + height // 2)
    outside = (xpos + width + 10, ypos + height // 2)

    def drawButton(self, position, leftPressed):
        function = Mock()
        with patch("pygame.mouse.get_pos", return_value=position), \
             patch("pygame.mouse.get_pressed", return_value=(leftPressed, False, False)):
            self.graphik.drawButton(self.xpos, self.ypos, self.width, self.height, black, red, 15, "Rock", function)
        return function

    def test_drawsTheBoxAndTheLabel(self):
        self.drawButton(self.outside, False)
        box = pygame.Rect(self.xpos, self.ypos, self.width, self.height)
        self.assertEqual(self.surface.get_at((self.xpos, self.ypos))[:3], black)
        self.assertEqual(self.surface.get_at((self.xpos - 1, self.ypos - 1))[:3], white)
        label = pixelsMatching(self.surface, red)
        self.assertTrue(label)
        for pixel in label:
            self.assertTrue(box.collidepoint(pixel))

    def test_firesWhenTheCursorIsInsideAndTheLeftButtonIsPressed(self):
        function = self.drawButton(self.inside, True)
        function.assert_called_once_with()

    def test_doesNotFireWhenTheCursorIsInsideButNothingIsPressed(self):
        function = self.drawButton(self.inside, False)
        function.assert_not_called()

    def test_doesNotFireWhenTheCursorIsOutside(self):
        function = self.drawButton(self.outside, True)
        function.assert_not_called()

    def test_doesNotFireOnTheLeftEdge(self):
        function = self.drawButton((self.xpos, self.ypos + self.height // 2), True)
        function.assert_not_called()

    def test_doesNotFireOnTheTopEdge(self):
        function = self.drawButton((self.xpos + self.width // 2, self.ypos), True)
        function.assert_not_called()

    def test_heldButtonFiresOnEveryDraw(self):
        # Characterises the polled-state behaviour tracked by issue #3: a button that is
        # still held on the next frame fires its callback again.
        firstFrame = self.drawButton(self.inside, True)
        secondFrame = self.drawButton(self.inside, True)
        firstFrame.assert_called_once_with()
        secondFrame.assert_called_once_with()

if __name__ == "__main__":
    unittest.main()
