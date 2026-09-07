import pygame
import random
from Graphik import *

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

def getComputerChoice():
    randomInt = random.randint(1,3)
    if randomInt == 1:
        return "rock"

    if randomInt == 2:
        return "paper"

    return "scissors"

def playerChoseRock():
    computerChoice = getComputerChoice()
    whoWon("rock", computerChoice)

def playerChosePaper():
    computerChoice = getComputerChoice()
    whoWon("paper", computerChoice)

def playerChoseScissors():
    computerChoice = getComputerChoice()
    whoWon("scissors", computerChoice)
        
def whoWon(playerChoice, computerChoice):
    if playerChoice == computerChoice:
        tie(playerChoice, computerChoice)
    
    if playerChoice == "rock" and computerChoice == "paper":
        lose(playerChoice, computerChoice)
    
    if playerChoice == "rock" and computerChoice == "scissors":
        win(playerChoice, computerChoice)
    
    if playerChoice == "paper" and computerChoice == "rock":
        win(playerChoice, computerChoice)
    
    if playerChoice == "paper" and computerChoice == "scissors":
        lose(playerChoice, computerChoice)
    
    if playerChoice == "scissors" and computerChoice == "rock":
        lose(playerChoice, computerChoice)
    
    if playerChoice == "scissors" and computerChoice == "paper":
        win(playerChoice, computerChoice)

def decisionScreen():
    running = True

    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                quit()

        gameDisplay.fill(white)
        graphik.drawText("Rock, Paper, or Scissors?", displayWidth//2, displayHeight//4, 36, black)
        middleButtonXPos = displayWidth//2 - 50
        graphik.drawButton(middleButtonXPos - 200, 300, 100, 100, black, white, 15, "Rock", playerChoseRock)
        graphik.drawButton(middleButtonXPos, 300, 100, 100, black, white, 15, "Paper", playerChosePaper)
        graphik.drawButton(middleButtonXPos + 200, 300, 100, 100, black, white, 15, "Scissors", playerChoseScissors)

        graphik.drawText("Wins: " + str(wins), 50, 25, 15, black)
        graphik.drawText("Losses: " + str(losses), 50, 50, 15, black)
        graphik.drawText("Ties: " + str(ties), 50, 75, 15, black)
        pygame.display.update()
        clock.tick(framesPerSecond)


def tie(p, c):
    global ties
    ties += 1
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
        pygame.display.update()
        clock.tick(framesPerSecond)

        if pygame.time.get_ticks() - startTime >= resultScreenDuration:
            running = False

def win(p, c):
    global wins
    wins += 1
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
        pygame.display.update()
        clock.tick(framesPerSecond)

        if pygame.time.get_ticks() - startTime >= resultScreenDuration:
            running = False
            
def lose(p, c):
    global losses
    losses += 1
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
        pygame.display.update()
        clock.tick(framesPerSecond)

        if pygame.time.get_ticks() - startTime >= resultScreenDuration:
            running = False

def main():
    global gameDisplay, graphik, clock
    pygame.init()
    gameDisplay = pygame.display.set_mode((displayWidth, displayHeight))
    graphik = Graphik(gameDisplay)
    pygame.display.set_caption("Rock Paper Scissors")
    clock = pygame.time.Clock()
    decisionScreen()

if __name__ == "__main__":
    main()