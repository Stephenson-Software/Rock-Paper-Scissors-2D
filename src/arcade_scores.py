# Reports high scores and achievements to arcade-social (https://api.play.danielstephenson.dev)
# from the browser build, through arcade-scores.js: the one-file JavaScript client vendored
# unchanged from https://github.com/Stephenson-Software/arcade-social (clients/js). pygbag packs
# the file into the game's archive with this module, so it is loaded from the game's own origin.
#
# The desktop build never reports: start() returns None anywhere but pygbag. In the browser the
# client itself sends nothing unless the page is served from rock-paper-scissors.play.danielstephenson.dev
# and the player is signed in, and none of its calls can throw. Scores come from the player's
# browser and can be forged, so the board is labelled "not verified".
import json
import os
import sys

CLIENT_SCRIPT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "arcade-scores.js")

class ArcadeScores:
    def __init__(self, evaluate):
        # evaluate runs one JavaScript expression in the page (window.eval in the browser)
        self.evaluate = evaluate

    def submit(self, board, value):
        self.call("submit", board, value)

    def unlock(self, achievement):
        self.call("unlock", achievement)

    def call(self, name, *args):
        # the arguments go through JSON so a number arrives as a JavaScript number; the
        # promise the client returns is discarded (the calls are fire-and-forget)
        expression = "void (window.ArcadeScores && window.ArcadeScores.%s(%s))" % (
            name, ", ".join(json.dumps(arg) for arg in args))
        try:
            self.evaluate(expression)
        except Exception:
            # a lost score is acceptable; a stalled game is not
            pass

def start():
    # Loads the vendored client into the page and returns the bridge, or None off the browser
    # or when the client cannot be loaded.
    if sys.platform != "emscripten":
        return None
    try:
        import platform
        with open(CLIENT_SCRIPT, encoding="utf-8") as source:
            platform.window.eval(source.read())
        return ArcadeScores(platform.window.eval)
    except Exception:
        return None
