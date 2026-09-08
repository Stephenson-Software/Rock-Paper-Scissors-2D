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
The suite covers `getComputerChoice` and all nine `whoWon` outcome pairs, the Wins / Losses / Ties counters, and the render loops — that a frame is drawn even when the event queue is empty, that a result screen ends after its configured duration without blocking, and that a quit request during a result screen is honoured. Only the standard library `unittest` module is used, so no additional dependency is required. No display is opened by the tests: `src/rockpaperscissors.py` creates its window in `main()`, which runs only when the file is executed directly.

## Continuous integration
`.github/workflows/ci.yml` runs on every push to `master` and on every pull request. It installs the dependencies, runs the suite above, and launches the game under the dummy SDL video and audio drivers to confirm it starts and keeps running. Clicking a button still requires a display, so the play-through remains a manual check.

## Dependencies
- pygame
- Graphik

### pygame
This project uses [pygame](https://www.pygame.org/) for windowing, drawing, and input. It is the only third party dependency and is declared in `requirements.txt`.

### Graphik
This project utilizes the free and open source [Graphik](https://github.com/Preponderous-Software/Graphik) library. The copy loaded at runtime is the vendored `src/Graphik.py`, because Python places the script's own directory on `sys.path`. The `Graphik` submodule registered in `.gitmodules` is not initialized and is not imported by the game.
