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

## Dependencies
- pygame
- Graphik

### pygame
This project uses [pygame](https://www.pygame.org/) for windowing, drawing, and input. It is the only third party dependency and is declared in `requirements.txt`.

### Graphik
This project utilizes the free and open source [Graphik](https://github.com/Preponderous-Software/Graphik) library. The copy loaded at runtime is the vendored `src/Graphik.py`, because Python places the script's own directory on `sys.path`. The `Graphik` submodule registered in `.gitmodules` is not initialized and is not imported by the game.
