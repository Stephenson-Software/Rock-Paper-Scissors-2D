# Entry point for the browser build: pygbag (https://pygame-web.github.io) packages this
# folder and runs main.py. The desktop entry point stays src/rockpaperscissors.py.
import asyncio

# pygbag decides which packages to load into the browser from main.py's own imports, so
# pygame must be imported here even though only rockpaperscissors.py uses it directly.
import pygame  # noqa: F401

from rockpaperscissors import main

# rockpaperscissors.main() skips usage reporting under pygbag: the trace client sends from
# a background thread, which the browser cannot start.
asyncio.run(main(reportUsage=True))
