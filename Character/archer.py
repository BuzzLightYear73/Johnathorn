from vector import Vector
from Character.character import Character
import pygame
import os

DEFAULT = 0
WALKING_RIGHT = 1
WALKING_LEFT=3
ATTACKING = 2
JUMP = 4

class Archer(Character):
    def __init__(self, x_pos, y_pos, x_vel, y_vel, health, arrows, xs, ys):
        sprite_folder='images/archer'
        available_actions = ["default", "walk", "attack", "die"]  
        super().__init__(x_pos, y_pos, x_vel, y_vel, health, arrows, xs, ys, sprite_folder, available_actions)
        

    def sprint(self):
        self.velocity = self.velocity.times(2)
