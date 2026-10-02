import asyncio
import sys
import time

import pygame
import random
from Graphik import *
from usage_reporting import startUsageReporting

black = (0,0,0)
white = (255,255,255)
red = (200,0,0)
green = (0,200,0)
blue = (0,0,200)

displayWidth = 900
displayHeight = 600

framesPerSecond = 60
resultScreenDuration = 2000

gameDisplay = None
graphik = None
clock = None

wins = 0
losses = 0
ties = 0

# the trace client once main() has started usage reporting; None until then, and for
# main() called directly (as the tests do), so only a real launch reports
usage = None

# the move a button press recorded during the current decision-screen frame; the screen
# plays the round once the frame is drawn. Callbacks only record, because the browser
# build (pygbag) needs every frame loop to yield, which a synchronous callback cannot do.
chosenMove = None

def runningInBrowser():
    # pygbag runs the game under CPython compiled to WebAssembly
    return sys.platform == "emscripten"

async def endFrame():
    pygame.display.update()
    clock.tick(framesPerSecond)
    # hands control back to the browser once per frame; a no-op pause on the desktop
    await asyncio.sleep(0)

def reportRound(result):
    if usage is not None:
        usage.report("round-played", tags={"result": result})

def getComputerChoice():
    randomInt = random.randint(1,3)
    if randomInt == 1:
        return "rock"

    if randomInt == 2:
        return "paper"

    return "scissors"

def chooseMove(move):
    global chosenMove
    chosenMove = move

def playerChoseRock():
    chooseMove("rock")

def playerChosePaper():
    chooseMove("paper")

def playerChoseScissors():
    chooseMove("scissors")

async def playRound(playerChoice):
    computerChoice = getComputerChoice()
    await whoWon(playerChoice, computerChoice)

async def whoWon(playerChoice, computerChoice):
    if playerChoice == computerChoice:
        await tie(playerChoice, computerChoice)
    
    if playerChoice == "rock" and computerChoice == "paper":
        await lose(playerChoice, computerChoice)
    
    if playerChoice == "rock" and computerChoice == "scissors":
        await win(playerChoice, computerChoice)
    
    if playerChoice == "paper" and computerChoice == "rock":
        await win(playerChoice, computerChoice)
    
    if playerChoice == "paper" and computerChoice == "scissors":
        await lose(playerChoice, computerChoice)
    
    if playerChoice == "scissors" and computerChoice == "rock":
        await lose(playerChoice, computerChoice)
    
    if playerChoice == "scissors" and computerChoice == "paper":
        await win(playerChoice, computerChoice)

def ignoreHeldButton():
    # Graphik.drawButton calls its function on every frame the left button is held over
    # the box, so one long press would play a round each time the result screen ended;
    # a round is played from the press event in decisionScreen instead
    pass

def pressLandedOn(pressPos, xpos, ypos, width, height):
    # the same bounds Graphik.drawButton uses for the cursor
    return pressPos is not None and xpos + width > pressPos[0] > xpos and ypos + height > pressPos[1] > ypos

async def decisionScreen():
    global chosenMove
    running = True
    buttonYPos = 300
    buttonSize = 100

    while running:
        chosenMove = None
        # A round is played only from a left-button press event, once per click or tap: a
        # press and release landing in the same frame (how a browser tap arrives) still
        # counts, and a button held down plays nothing further.
        pressPos = None
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                quit()
            elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                pressPos = event.pos

        gameDisplay.fill(white)
        graphik.drawText("Rock, Paper, or Scissors?", displayWidth//2, displayHeight//4, 36, black)
        middleButtonXPos = displayWidth//2 - 50
        buttons = [
            (middleButtonXPos - 200, "Rock", playerChoseRock),
            (middleButtonXPos, "Paper", playerChosePaper),
            (middleButtonXPos + 200, "Scissors", playerChoseScissors),
        ]
        for buttonXPos, label, chooseThis in buttons:
            graphik.drawButton(buttonXPos, buttonYPos, buttonSize, buttonSize, black, white, 15, label, ignoreHeldButton)
            if pressLandedOn(pressPos, buttonXPos, buttonYPos, buttonSize, buttonSize):
                chooseThis()

        graphik.drawText("Wins: " + str(wins), 50, 25, 15, black)
        graphik.drawText("Losses: " + str(losses), 50, 50, 15, black)
        graphik.drawText("Ties: " + str(ties), 50, 75, 15, black)
        await endFrame()

        if chosenMove is not None:
            move = chosenMove
            chosenMove = None
            await playRound(move)


async def tie(p, c):
    global ties
    ties += 1
    reportRound("tie")
    running = True
    startTime = pygame.time.get_ticks()

    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                quit()

        gameDisplay.fill(white)
        graphik.drawText("It was a tie!", displayWidth//2, displayHeight//4, 36, black)
        graphik.drawText("Player Choice: " + p, displayWidth//2, displayHeight//2, 36, black)
        graphik.drawText("Computer Choice: " + c, displayWidth//2, displayHeight - displayHeight//4, 36, black)
        await endFrame()

        if pygame.time.get_ticks() - startTime >= resultScreenDuration:
            running = False

async def win(p, c):
    global wins
    wins += 1
    reportRound("win")
    running = True
    startTime = pygame.time.get_ticks()

    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                quit()

        gameDisplay.fill(white)
        graphik.drawText("You win!", displayWidth//2, displayHeight//4, 36, black)
        graphik.drawText("Player Choice: " + p, displayWidth//2, displayHeight//2, 36, black)
        graphik.drawText("Computer Choice: " + c, displayWidth//2, displayHeight - displayHeight//4, 36, black)
        await endFrame()

        if pygame.time.get_ticks() - startTime >= resultScreenDuration:
            running = False

async def lose(p, c):
    global losses
    losses += 1
    reportRound("lose")
    running = True
    startTime = pygame.time.get_ticks()

    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                quit()

        gameDisplay.fill(white)
        graphik.drawText("You lost!", displayWidth//2, displayHeight//4, 36, black)
        graphik.drawText("Player Choice: " + p, displayWidth//2, displayHeight//2, 36, black)
        graphik.drawText("Computer Choice: " + c, displayWidth//2, displayHeight - displayHeight//4, 36, black)
        await endFrame()

        if pygame.time.get_ticks() - startTime >= resultScreenDuration:
            running = False

async def main(reportUsage=False):
    global gameDisplay, graphik, clock, usage
    # the trace client sends from a background thread, which the browser build cannot start
    if reportUsage and not runningInBrowser():
        usage = startUsageReporting()
    if runningInBrowser():
        # every page load would otherwise start from the same random state, so each
        # visitor would face the same sequence of computer moves
        random.seed(time.time_ns())
    pygame.init()
    gameDisplay = pygame.display.set_mode((displayWidth, displayHeight))
    graphik = Graphik(gameDisplay)
    pygame.display.set_caption("Rock Paper Scissors")
    clock = pygame.time.Clock()
    await decisionScreen()

if __name__ == "__main__":
    asyncio.run(main(reportUsage=True))