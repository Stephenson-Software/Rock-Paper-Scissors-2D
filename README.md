# Rock-Paper-Scissors
This application allows the user to play a simple graphical version of Rock Paper Scissors against the computer.

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
A window titled "Rock Paper Scissors" opens with Rock, Paper, and Scissors buttons, and a running Wins / Losses / Ties tally in the top left. The game is exited by closing the window.

## Tests
```
python3 -m unittest discover -s tests
```
The suite covers `getComputerChoice` and all nine `whoWon` outcome pairs, the Wins / Losses / Ties counters, the render loops — that a frame is drawn even when the event queue is empty, that a result screen ends after its configured duration without blocking, and that a quit request during a result screen is honoured — and the decision screen's wiring: that the Rock, Paper, and Scissors buttons are labelled and laid out left to right, each plays the matching choice, and the tally shows the current counters. `tests/test_graphik.py` characterises the vendored `src/Graphik.py`: `drawRectangle` fills exactly the requested area, `drawText` is centred on the given point, and `drawButton` fires its callback only while the cursor is inside the box with the left button down. The usage reporting described below is covered too: `tests/test_usage_reporting.py` checks the `settings.json` block, the first-launch notice, the opt-outs and the startup event, `tests/test_trace_client.py` checks the vendored client, and `tests/test_rockpaperscissors.py` checks that each round reports its result and that only `main(reportUsage=True)` starts reporting. Only the standard library `unittest` module is used, so no additional dependency is required. No window is opened by the tests: `src/rockpaperscissors.py` creates its window in `main()`, which runs only when the file is executed directly, and the tests that call `main()` do so under the dummy SDL video and audio drivers.

## Continuous integration
`.github/workflows/ci.yml` runs on every push to `master` and on every pull request. It installs the dependencies, runs the suite above, and launches the game under the dummy SDL video and audio drivers to confirm it starts and keeps running. Clicking a button still requires a display, so the play-through remains a manual check.

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

The environment variables win over `settings.json`. If `settings.json` exists but cannot be read as a JSON object, nothing is reported, a message says so, and the file is left untouched. The `endpoint` and `key` entries in the same block select where reports go and the key they are sent with. The client is `src/trace_client.py`, vendored from [trace-client-python](https://github.com/Stephenson-Software/trace-client-python); the settings handling is in `src/usage_reporting.py`. Only a launch of `src/rockpaperscissors.py` reports to the real service: `main()` called directly reports nothing, the one test that calls `main(reportUsage=True)` replaces `startUsageReporting` with a mock, the reporting tests send only to a stub server on `127.0.0.1` and keep their `settings.json` in a temporary directory, and the CI smoke launch sets `TRACE_USAGE_REPORTING=off`.

Details: https://github.com/Stephenson-Software/trace#usage-reporting

## Dependencies
- pygame
- Graphik

### pygame
This project uses [pygame](https://www.pygame.org/) for windowing, drawing, and input. It is the only third party dependency and is declared in `requirements.txt`; the usage-reporting client in `src/trace_client.py` uses only the standard library.

### Graphik
This project utilizes the free and open source [Graphik](https://github.com/Preponderous-Software/Graphik) library. The copy loaded at runtime is the vendored `src/Graphik.py`, because Python places the script's own directory on `sys.path`. The `Graphik` submodule registered in `.gitmodules` is not initialized and is not imported by the game.
