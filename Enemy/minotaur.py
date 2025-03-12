from vector import Vector
from Enemy.enemy import Enemy
import pygame
import os
class Minotaur(Enemy):
    steering = []

    def __init__(self, x_pos, y_pos, x_vel, y_vel, health, target):
        sprite_folder='images/minotaur'
        available_actions = ["walk", "attack", "die", "default"]  
        super().__init__(x_pos, y_pos, x_vel, y_vel, health,target,sprite_folder, available_actions)
    
    def attack(self):
        if "melee" in self.sprites["attack"]:
            self.set_action("attack", "melee")
        else:
            print("Melee attack animation not found.")
        return super().attack()