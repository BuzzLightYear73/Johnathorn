from vector import Vector
from Character.character import Character
import pygame
import os

DEFAULT = 0
WALKING_RIGHT = 1
WALKING_LEFT=3
ATTACKING = 2
JUMP = 4


class Titan(Character):

    # expressions = []
    # expression = DEFAULT


    def __init__(self, x_pos, y_pos, x_vel, y_vel, health, armour, xs, ys):
            sprite_folder='images/titan'
            available_actions = ["default", "walk", "attack", "die"]  
            super().__init__(x_pos, y_pos, x_vel, y_vel, health, armour, xs, ys, sprite_folder, available_actions)

##        

    def attack(self, target):
        self.expression = ATTACKING
        if self.collide(target):
            target.remove_health(self.damage)

        

    def block(self):
        return

    def set_armour(self, new_armour):
        self.armour += new_armour

    def get_armour(self):
        return self.armour
