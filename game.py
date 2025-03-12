import pygame
import sys
from Enemy.dragon import Dragon
from Enemy.minotaur import Minotaur
from Environment.environment import Environment, Window
from Character.character_defaults import CharacterDefault
from Pygame.pygame_wrapper import PygameWrapper
from powerUp import PowerUp
import random

R2BUTTON = 5
L2BUTTON = 4
SQUAREBUTTON = 2
XBUTTON = 0

pygameWrapper: PygameWrapper = PygameWrapper()

def play_game():
    char = startScreen(pygameWrapper.window)
    hasPlayerWon = runGame(char, pygameWrapper.window)
    endScreen(pygameWrapper.window)
    
    
#TODO: Change this function to use new environment class for main menu screen
def startScreen(myWindow):
    width = myWindow.get_width()
    height = myWindow.get_height()

    clock = pygameWrapper.clock
    
    background = PygameWrapper.createSurfaceFromImage("images/JOHNATHORN.png")
    new_background = PygameWrapper.transformSurfaceScale(background, width, height)

    PygameWrapper.loadMusic("Sounds/opening_sound.ogg")
    PygameWrapper.setVolume(0)
    PygameWrapper.playMusic()

    keymap = {}
    
    while True:
        # Blit the background once per frame
        myWindow.blit(new_background, (0, 0))
        PygameWrapper.flipDisplay()
        
        clock.tick(30)  # Limit frame rate to 30 FPS
        
        for event in PygameWrapper.getEvents():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            elif event.type == pygame.KEYDOWN:
                keymap[event.key] = True
            elif event.type == pygame.KEYUP:
                keymap[event.key] = False

        # Check keys only once per frame after events are processed
        if keymap.get(pygame.K_w, False):
            return "Warrior"
        if keymap.get(pygame.K_m, False):
            return "Mage"
        if keymap.get(pygame.K_a, False):
            return "Archer"
        if keymap.get(pygame.K_d, False):
            return "Druid"
        if keymap.get(pygame.K_t, False):
            return "Titan"

#TODO: Change function to use new environment class for end screen
def endScreen(myWindow):
    keepGoing = True
    
    width = myWindow.get_width()
    height = myWindow.get_height()

    clock = pygameWrapper.clock

    background = PygameWrapper.createSurfaceFromImage("images/END_SCREEN.png")
    newBackground = PygameWrapper.transformSurfaceScale(background, width, height)
    myWindow.blit(newBackground, (0, 0))

    while keepGoing:
        clock.tick(30)  # Limit frame rate to 30 FPS

        keymap = {}
        PygameWrapper.updateDisplay()

        for event in PygameWrapper.getEvents():
            if event.type == pygame.QUIT:
                keepGoing = False
            elif event.type == pygame.KEYDOWN:
                key = event.key
                keymap[key] = True
            elif event.type == pygame.KEYUP:
                key = event.key
                keymap[key] = False
            elif event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            if keymap.get(pygame.K_r, False):
                play_game()
                keepGoing = False
            if keymap.get(pygame.K_q, False):
                keepGoing = False


    PygameWrapper.quit()

def initalizeEnvironment(char, myWindow):

    environment: Environment = Environment(myWindow.get_width(), myWindow.get_height())

    keymap = {}

    joystick = None
    if PygameWrapper.getJoystickCount() > 0:
        joystick = PygameWrapper.createJoystick()
        joystick.init()

    char = CharacterDefault.handleSelection(char)

    myWindow.blit(environment.skybox, (0, 0))
    environment.playAmbientSound()

    return keymap, joystick, char, environment 
    
def enemy_builder(x, y, width, height, health, char):
    """Randomly selects an enemy type and returns an instance."""
    enemy_classes = [Minotaur, Dragon]  # Add more enemy types if needed
    EnemyClass = random.choice(enemy_classes)
    return EnemyClass(x, y, width, height, health, char)  # `char` is the sprite folder

def runGame(char, myWindow):
    keymap, joystick, char, environment = initalizeEnvironment(char, myWindow)
    clock = pygameWrapper.clock
    width = myWindow.get_width()
    height = myWindow.get_height()

    #dragon_sheet = pygame.image.load("images/thats_our_dragon.png")
    #enemy = Dragon(800, 500, 200, 200, 500, char) #Minotaur(800, 500, 200, 200, 500, char)#Dragon(800, 500, 200, 200, 500, char)
    enemy = enemy_builder(800, 500, 200, 200, 500, char)
    #Second enemy spawn for testing purposes
    enemy2 = enemy_builder(800, 500, 200, 200, 500, char)

# Example usage:

    dt = 0
    keepGoing = True
    power = False
    p_up = None
    while keepGoing:
        dt = clock.tick(60)
        #clock.tick(30)  # Limit frame rate to 30 FPS
        # if dt > 500:
        #     continue

        for event in PygameWrapper.getEvents():
            if event.type == pygame.QUIT:
                keepGoing = False
                PygameWrapper.quit()
            elif event.type == pygame.KEYDOWN:
                key = event.key
                keymap[key] = True
            elif event.type == pygame.KEYUP:
                key = event.key
                keymap[key] = False
            elif event.type == pygame.JOYBUTTONDOWN:
                key = event.button
                keymap[key] = True
            elif event.type == pygame.JOYBUTTONUP:
                key = event.button
                keymap[key] = False

        chance = random.randint(0, 200)

        ptemp_img = PygameWrapper.createSurfaceFromImage("images/p_up.png")
        p_img = PygameWrapper.transformSurfaceScale(ptemp_img, 25, 25)
        
        
        if not power and p_up == None:
            if chance == 25:
                p_up = PowerUp(p_img, random.randint(100, width), height - 25, "health")
                power = True
            elif chance == 50:
                p_up = PowerUp(p_img, random.randint(100, width), height - 25, "damage")
                power = True
            elif chance == 75:
                p_up = PowerUp(p_img, random.randint(100, width), height - 25, "speed")
                power = True

        myWindow.blit(environment.skybox, (0, 0))
        
        enemy.draw(myWindow)
        enemy.draw_health(myWindow)

        enemy.arrive(char, 1.0/10)
        enemy.apply_steering()
        enemy.move(dt, width, height)

        char.handle_input(keymap, enemy, joystick)        

        char.draw(myWindow)
        char.draw_health(myWindow)
        char.simulate(dt, width, height)
        
        #Second enemy spawn for testing purposes
        enemy2.draw(myWindow)
        enemy2.draw_health(myWindow)

        enemy2.arrive(char, 2.0/10)
        enemy2.apply_steering()
        enemy2.move(dt*2, width*2, height*2)

        if power and p_up != None:
            p_up.draw(myWindow)
            power = p_up.collide(char)
            if not power:
                p_up = None
            
        PygameWrapper.updateDisplay()

        if char.health == 0:
            keepGoing = False
            return False
        if enemy.health == 0 and enemy2.health == 0:
            return True

    PygameWrapper.quit()

play_game()
