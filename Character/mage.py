from vector import Vector
from Character.character import Character
import pygame
import os

DEFAULT = 0
WALKING_RIGHT = 1
WALKING_LEFT=3
ATTACKING = 2
JUMP = 4

class Mage(Character):

    expressions = []
    expression = DEFAULT
    
    def __init__(self, x_pos, y_pos, x_vel, y_vel, health, mana, xs, ys):
            sprite_folder='images/mage'
            available_actions = ["walk", "attack", "die", "default"]  
            super().__init__(x_pos, y_pos, x_vel, y_vel, health, mana, xs, ys, sprite_folder, available_actions)

    def heal(self, health, mana):
        if self.special < mana:
            print("NOT ENOUGH MANA")
        else:
            self.health += health
            self.special -= mana

    def attack(self, target):
        #self.expression = ATTACKING
        super().attack(target)
        
