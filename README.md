# Rock-Paper-Scissors
This application allows the user to play a simple graphical version of Rock Paper Scissors against the computer.

## Play in your browser
The game is also built for the browser with [pygbag](https://pygame-web.github.io) and served at https://rock-paper-scissors.play.danielstephenson.dev, alongside the other games at https://danielstephenson.dev/play. Nothing needs to be installed: the page loads Python and pygame compiled to WebAssembly, then asks for a click or tap to start. The buttons work with a mouse or a tap on a phone. Usage reporting is off in the browser build (see below).

To build and serve it locally:
```
python3 -m pip install pygbag==0.9.3
python3 -m pygbag --build src
python3 -m http.server 8000 --directory src/build/web
```
then open http://localhost:8000. `src/main.py` is the browser entry point; `src/rockpaperscissors.py` stays the desktop one. The build output in `src/build/` is not committed.

## High scores
In the browser build, a signed-in player's longest run of consecutive wins in a session is reported to the "Best win streak" leaderboard (`best-streak`) of [arcade-social](https://github.com/Stephenson-Software/arcade-social) at `https://api.play.danielstephenson.dev`, and two achievements are unlocked: `first-win` (the first win) and `streak-5` (five wins in a row). A loss or a tie ends the streak, which is shown under the tally as `Streak: n`. Only a new best of the session is sent. Sign-in happens on arcade-social's own page; the game never sees a password, and nothing is sent while signed out, from any address other than https://rock-paper-scissors.play.danielstephenson.dev, or from the desktop game. Scores are reported by the player's browser and can be forged, so the board is labelled "not verified".

The client is `src/arcade-scores.js`, vendored unchanged from arcade-social's `clients/js`; pygbag packs it into the game's archive, and `src/arcade_scores.py` loads it into the page and calls it through pygbag's `platform.window`. Its calls never throw: a refused or lost score is dropped and the game carries on.

## Prerequisites
- Python 3
- A display (the game opens a 900x600 window)

## Installation
```
python3 -m pip install -r requirements.txt
```

## Usage
```
python3 src/rockpaperscissors.py
```
A window titled "Rock Paper Scissors" opens with Rock, Paper, and Scissors buttons, and a running Wins / Losses / Ties tally in the top left. A round is played by clicking a button; the result is shown for two seconds and the tally updates. The game is exited by closing the window.

## Tests
```
python3 -m unittest discover -s tests
```
The suite covers `getComputerChoice` and all nine `whoWon` outcome pairs, the Wins / Losses / Ties counters, the render loops — that a frame is drawn even when the event queue is empty, that a result screen ends after its configured duration without blocking, and that a quit request during the decision screen or a result screen is honoured — that each result screen shows its heading ("You win!", "You lost!" or "It was a tie!") with the player's and the computer's choices, that every frame of every screen yields to the event loop (the browser build freezes otherwise), and the decision screen's wiring: that the Rock, Paper, and Scissors buttons are labelled and laid out left to right, each records the matching choice, a click plays exactly one round with the button it landed on even when the mouse button is held down afterwards, a tap or quick click whose press and release land in the same frame still plays it (while a press outside every button, or with the right button, plays nothing), and the tally shows the current counters. The browser-only behaviour is covered too: under pygbag (`sys.platform == "emscripten"`) `main()` starts no usage reporting, seeds the computer's choices from the clock and starts the high-score bridge (the desktop launch does not). `StreakTest` covers the win streak: a loss or a tie ends it, only a new best of the session is submitted to `best-streak`, `first-win` is unlocked on the first win and `streak-5` on the fifth in a row, and nothing is reported without the bridge; `tests/test_arcade_scores.py` checks the bridge itself (the calls it makes into the page, JSON-quoted arguments, that a failing call never reaches the game, that the desktop gets no bridge, and that the vendored client is arcade-social's). `tests/test_graphik.py` characterises the vendored `src/Graphik.py`: `drawRectangle` fills exactly the requested area, `drawText` is centred on the given point, and `drawButton` fires its callback only while the cursor is inside the box with the left button down. The usage reporting described below is covered too: `tests/test_usage_reporting.py` checks the `settings.json` block, the first-launch notice, the opt-outs and the startup event, `tests/test_trace_client.py` checks the vendored client, and `tests/test_rockpaperscissors.py` checks that each round reports its result and that only `main(reportUsage=True)` starts reporting. Only the standard library `unittest` module is used, so no additional dependency is required. No window is opened by the tests: `src/rockpaperscissors.py` creates its window in `main()`, which runs only when the file is executed directly, and the tests that call `main()` do so under the dummy SDL video and audio drivers.

## Continuous integration
`.github/workflows/ci.yml` runs on every push to `master` and on every pull request. It installs the dependencies, runs the suite above, and launches the game under the dummy SDL video and audio drivers to confirm it starts and keeps running. Clicking a button still requires a display, so the desktop play-through remains a manual check.

`.github/workflows/browser.yml` runs on the same events and builds the browser version with pygbag, checking that `src/build/web/index.html` was produced. On a manual run (`workflow_dispatch`), or on a push to `master` once the repository variable `ARCADE_ENABLED` is `true`, it deploys the build to [arcade](https://github.com/Stephenson-Software/arcade) with [arcade-deploy](https://github.com/Stephenson-Software/arcade-deploy), as version `<version.txt>+g<short commit>`; the upload token is the `ARCADE_TOKEN` secret.

## Usage reporting
Usage reporting is on by default: the game sends its name (`Rock-Paper-Scissors-2D`), its version and the events `startup` (when the game is launched) and `round-played` (after each round, tagged with its `result`: `win`, `lose` or `tie`) to [trace](https://github.com/Stephenson-Software/trace) at `https://trace.danielstephenson.dev`. Nothing about you, your machine, your IP address or your choices is sent. The report is made from a background thread, never blocks the game, and is dropped silently if the service is unreachable.

The first launch writes a `settings.json` at the repository root and prints a one-line notice. To turn reporting off, any one of these is enough:

- `"usage_reporting": {"enabled": false}` in `settings.json`:

  ```json
  {
    "usage_reporting": {
      "enabled": false
    }
  }
  ```

- the environment variable `TRACE_USAGE_REPORTING=off` (also `false`, `0`, `no`), which turns off every program that reports to trace
- the environment variable `DO_NOT_TRACK=1` (also `true`, `yes`; see [consoledonottrack.com](https://consoledonottrack.com))

The environment variables win over `settings.json`. If `settings.json` exists but cannot be read as a JSON object, nothing is reported, a message says so, and the file is left untouched. The `endpoint` and `key` entries in the same block select where reports go and the key they are sent with. The client is `src/trace_client.py`, vendored from [trace-client-python](https://github.com/Stephenson-Software/trace-client-python); the settings handling is in `src/usage_reporting.py`. Only a launch of `src/rockpaperscissors.py` reports to the real service: `main()` called directly reports nothing, the one test that calls `main(reportUsage=True)` replaces `startUsageReporting` with a mock, the reporting tests send only to a stub server on `127.0.0.1` (and `tests/test_usage_reporting.py` keeps its `settings.json` in a temporary directory), and the CI smoke launch sets `TRACE_USAGE_REPORTING=off`. The browser build never reports: the client sends from a background thread, which the browser cannot start, so `main()` skips reporting when running under pygbag.

Details: https://github.com/Stephenson-Software/trace#usage-reporting

## Dependencies
- pygame
- Graphik

### pygame
This project uses [pygame](https://www.pygame.org/) for windowing, drawing, and input. It is the only third party dependency and is declared in `requirements.txt`; the usage-reporting client in `src/trace_client.py` uses only the standard library.

### Graphik
This project utilizes the free and open source [Graphik](https://github.com/Preponderous-Software/Graphik) library. The copy loaded at runtime is the vendored `src/Graphik.py`, because Python places the script's own directory on `sys.path`. The `Graphik` submodule registered in `.gitmodules` is not initialized and is not imported by the game.
