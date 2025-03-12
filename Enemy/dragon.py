from vector import Vector
from Enemy.enemy import Enemy
import pygame



class Dragon(Enemy):

    steering = []

    def __init__(self, x_pos, y_pos, x_vel, y_vel, health, target):
        sprite_folder='images/dragon'
        available_actions = ["flying", "attack", "die", "default"]  
        super().__init__(x_pos, y_pos, x_vel, y_vel, health,target,sprite_folder, available_actions)

        
        #self.target = target

        ##Setting Expressions


        # def attack(self):
        #     return

        def fireball(self):
            return

        def deepBreath(self):
            return
