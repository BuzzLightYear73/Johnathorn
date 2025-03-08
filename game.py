import pygame
import sys
from Enemy.dragon import Dragon
from Environment.environment import Environment, Window
from Character.character_defaults import CharacterDefault
from powerUp import PowerUp
import random

R2BUTTON = 5
L2BUTTON = 4
SQUAREBUTTON = 2
XBUTTON = 0

def play_game():
    pygame.init()
    my_win = pygame.display.set_mode()
    char = start_screen(my_win)
    win = run_game(char, my_win)
    end_screen(win, my_win)
    
    
#TODO: Change this function to use new environment class for main menu screen
#TODO: Use GameClock Class instead of directly using pygame clock()
def start_screen(my_win):
    pygame.mixer.music.load("Sounds/opening_sound.ogg")
    pygame.mixer.music.play()
    pygame.mixer.music.set_volume(.1)
    
    width = my_win.get_width()
    height = my_win.get_height()
    
    # Load background image once
    background = pygame.image.load("images/JOHNATHORN.png")
    new_background = pygame.transform.scale(background, (width, height))
    
    clock = pygame.time.Clock()
    keymap = {}
    
    while True:
        # Blit the background once per frame
        my_win.blit(new_background, (0, 0))
        pygame.display.flip()
        
        clock.tick(30)  # Limit frame rate to 30 FPS
        
        for event in pygame.event.get():
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

#TODO: Change function to use new environment class for end screen
#TODO: Use GameClock Class instead of directly using pygame clock()
def end_screen(win, my_win):
    keepGoing = True
    width = my_win.get_width()
    height = my_win.get_height()
    clock = pygame.time.Clock()
    if win:
        background = pygame.image.load("images/END_SCREEN.png")
        new_background = pygame.transform.scale(background, (width, height))
        my_win.blit(new_background, (0, 0))
    else:
        background = pygame.image.load("images/END_SCREEN.png")
        new_background = pygame.transform.scale(background, (width, height))
        my_win.blit(new_background, (0, 0))
    while keepGoing:
        clock.tick(30)  # Limit frame rate to 30 FPS

        keymap = {}
        pygame.display.update()

        for event in pygame.event.get():
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


    pygame.quit()

#TODO: Use GameClock Class instead of directly using pygame clock()
def initalizePygame(char, my_win):

    environment: Environment = Environment(my_win.get_width(), my_win.get_height())

    clock = pygame.time.Clock()
    keymap = {}

    joystick = None
    if pygame.joystick.get_count() > 0:
        joystick = pygame.joystick.Joystick(0)
        joystick.init()

    char = CharacterDefault.handleSelection(char)

    my_win.blit(environment.skybox, (0, 0))
    environment.playAmbientSound()

    return my_win, clock, keymap, joystick, char, environment 


#TODO: Use GameClock Class instead of directly using pygame clock()
def run_game(char, my_win):
    my_win, clock, keymap, joystick, char, environment = initalizePygame(char, my_win)
    width = my_win.get_width()
    height = my_win.get_height()

    dragon_sheet = pygame.image.load("images/thats_our_dragon.png")
    dragon = Dragon(dragon_sheet, 800, 500, 200, 200, 500, char)

    dt = 0
    keepGoing = True
    power = False
    while keepGoing:
        dt = clock.tick(60)
        #clock.tick(30)  # Limit frame rate to 30 FPS
        # if dt > 500:
        #     continue

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                keepGoing = False
                pygame.quit()
                sys.exit() 
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
        ptemp_img = pygame.image.load("images/p_up.png")
        p_img = pygame.transform.scale(ptemp_img, (25, 25))
        
        p_up = None
        if chance == 25:
            p_up = PowerUp(p_img, random.randint(100, width), height - 25, "health")
            power = True
        elif chance == 50:
            p_up = PowerUp(p_img, random.randint(100, width), height - 25, "damage")
            power = True
        elif chance == 75:
            p_up = PowerUp(p_img, random.randint(100, width), height - 25, "speed")
            power = True

        my_win.blit(environment.skybox, (0, 0))
        
        dragon.draw(my_win)
        dragon.draw_health(my_win)

        dragon.arrive(char, 1.0/10)
        dragon.apply_steering()
        dragon.move(dt, width, height)

        char.handle_input(keymap, dragon, joystick)        

        char.draw(my_win)
        char.draw_health(my_win)
        char.simulate(dt, width, height)

        if power and p_up != None:
            p_up.draw(my_win)
            power = p_up.collide(char)
            
        pygame.display.update()

        if char.health == 0:
            keepGoing = False
            return False
        if dragon.health == 0:
            return True

    pygame.quit()

play_game()
