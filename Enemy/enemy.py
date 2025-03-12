from vector import Vector
import pygame
import random
import os

#Controller button constants



class Enemy(pygame.sprite.Sprite):

    
    def __init__(self, x_pos, y_pos, x_vel, y_vel, health, target, sprite_folder, available_actions):
        """
        Initialize the enemy with position, velocity, health, and target.
        """
        self.health = health
        self.pos = Vector(0.0, 0.0)
        self.pos.x = x_pos
        self.pos.y = y_pos
        self.velocity = Vector(0.0, 0.0)
        self.velocity.x = x_vel
        self.velocity.y = y_vel
        self.speedlimit = self.velocity
        self.target = target
        

        super().__init__()
        self.sprites = {action: [] for action in available_actions}
        self.sprites["attack"] = {}  # Attack sub-actions handled separately
        
        # Load images from subfolders
        for action in available_actions:
            if action == "attack":
                attack_folder = os.path.join(sprite_folder, "attack")
                if os.path.exists(attack_folder):
                    for sub_action in os.listdir(attack_folder):
                        sub_action_path = os.path.join(attack_folder, sub_action)
                        if os.path.isdir(sub_action_path):
                            self.sprites["attack"][sub_action] = []
                            for filename in sorted(os.listdir(sub_action_path)):
                                if filename.endswith(".png"):
                                    image_path = os.path.join(sub_action_path, filename)
                                    image = pygame.transform.scale_by(pygame.image.load(image_path), 3.0)
                                    self.sprites["attack"][sub_action].append(image)
            else:
                action_folder = os.path.join(sprite_folder, action)
                if os.path.exists(action_folder):
                    for filename in sorted(os.listdir(action_folder)):
                        if filename.endswith(".png"):
                            image_path = os.path.join(action_folder, filename)
                            image = pygame.transform.scale_by(pygame.image.load(image_path), 3.0)
                            self.sprites[action].append(image)
        
        self.current_action = "walk" if "walk" in self.sprites else list(self.sprites.keys())[0]
        self.current_sub_action = None
        self.current_frame = 0
        self.facing_right = True  # Default facing direction
        self.image = self.sprites[self.current_action][self.current_frame]
        self.rect = self.image.get_rect()
        self.bbox = self.rect  # Initialize bounding box with the image rect
        

    
    def update(self):
        self.current_frame += 1
        frames = self.sprites[self.current_action]
        
        if isinstance(frames, dict):  # Handling attack sub-actions
            if self.current_sub_action and self.current_sub_action in frames:
                frames = frames[self.current_sub_action]
            else:
                return
        
        if self.current_frame >= len(frames):
            self.current_frame = 0
        
        # Flip the image based on direction
        self.image = frames[self.current_frame]
        if not self.facing_right:
            self.image = pygame.transform.flip(self.image, True, False)
    
    def set_action(self, action, sub_action=None):
        if action == "attack" and "attack" in self.sprites:
            if not sub_action and self.sprites["attack"]:  # Pick a random attack type
                sub_action = random.choice(list(self.sprites["attack"].keys()))
            if sub_action in self.sprites["attack"]:
                self.current_action = "attack"
                self.current_sub_action = sub_action
                self.current_frame = 0
        elif action in self.sprites and isinstance(self.sprites[action], list):
            self.current_action = action
            self.current_sub_action = None
            self.current_frame = 0
    
    def set_direction(self, right=True):
        """Set the direction the enemy is facing."""
        self.facing_right = right

    def set_vel(self, new_x ,new_y):
        self.velocity = (new_x, new_y)

    def get_vel(self):
        return self.velocity

    def remove_health(self, health):
        self.health -= health

    def set_pos(self, new_x, new_y):
        self.pos = (new_x, new_y)

    def get_pos(self):
        return self.pos
    
    def attack(self):
        self.set_action("attack")
        #self.expressions["attack"]
        self.target.remove_health(1)

    def draw(self, window):
        img = self.image
        window.blit (img, (round(self.pos.x), round(self.pos.y)))
        self.update()



    def simulate(self, millisecs, width, height):
        self.move(millisecs)
        self.bounce(width, height)
        self.simulateGravity()


    def bounce (self, width, height):

        img = self.image
        print("bounce")
        
        if (self.pos.x + img.get_width()) > width:
            self.pos.x = width - img.get_width()
            
        elif (self.pos.x) < 0:
            self.pos.x = 0 
            
            
        if (self.pos.y + img.get_height()) > height:
            self.pos.y = height - img.get_height()
            
            
        elif (self.pos.y) < 0:
            self.pos.y = 0
            self.attack()
            self.velocity.y = (-1)*self.velocity.y

    def simulateGravity(self):
        if (self.pos.y + 105 <  960 ):
            self.velocity.y = self.velocity.y + 10

    def draw_health(self, window):
            top = int(window.get_width()*0.05)
            right = int(window.get_width()) - (self.health)
            height = int(window.get_height()*0.02)
            width = max(int(window.get_width() - (right + 20)),0)
            enemy_health = window.subsurface((right, top, width, height))
            enemy_health.fill(pygame.color.Color("green"))
            enemy_health.blit(window,(right,top))


    def apply_steering (self):
        for s in self.steering:
            self.velocity = self.velocity.plus(s)
            
    def seek (self, target, weight):
        desired_direction = target.pos.minus(self.pos).normalize()
        max_speed = self.speedlimit.length()
        desired_velocity = desired_direction.times(max_speed)

        self.steering += [desired_velocity.minus(self.velocity).times(weight)]


    def arrive (self, target, weight):

        target_distance = target.pos.minus(self.pos).length()
        max_speed = self.speedlimit.length()
        slow_radius = 50

        if target_distance > slow_radius:

            self.seek(target, weight)
            

        else:

            desired_speed = max_speed * (target_distance / slow_radius)
            if desired_speed > max_speed:
                desired_speed = max_speed
            
            desired_direction = target.pos.minus(self.pos).normalize()
            desired_velocity = desired_direction.times(desired_speed/target_distance)

            self.steering += [desired_velocity.minus(self.velocity).times(weight)]

    def move (self, dt, width, height):
        print("move")
        self.bounce(width, height)
        self.clamp_v ()
        self.stop_v ()
        self.pos = self.pos.plus(self.velocity.times(float(dt)/1000))

    def apply_impulse (self, j, n):
        """ j is the impulse; n the collision normal, i.e. the
        direction along which the impact happens."""
        self.v = self.v.plus(n.times(j / self.m))


    def repair_position (self, rel_pos, other):
        """ If two objects overlap, move them apart so that they are
        touching but not overlapping. How much each of the objects
        gets moved depends on its mass, so that objects with an
        infinite mass do not get moved."""
        # dividing by 10, because the length of our normal vector is 10 pixels
        repair = float(self.r + other.r - rel_pos.length())#/10
        rel_pos.normalize()
        
        if math.isinf (self.m):
            other.pos = other.pos.plus(rel_pos.times(-1).times(repair))
        elif math.isinf (other.m):
            self.pos = self.pos.plus(rel_pos.times(repair))
        else:
            self.pos = self.pos.plus(rel_pos.times(repair*other.m/(self.m+other.m)))
            other.p = other.pos.plus(rel_pos.times(-1).times(repair*self.m/(self.m+other.m)))


    def clamp_v (self):
        """ Reset the velocity in either dimension to the speed limit
        if it should be faster than the speed limit."""
        if self.velocity.length() > self.speedlimit.length():
            self.velocity = self.velocity.normalize().times(self.speedlimit.length())


    def stop_v (self):
        """ Reset the velocity to 0 if it gets very close. """

        if self.velocity.length() < 5:
            self.velocity = Vector (0,0)
            print("stop_v")
            self.attack()

    def get_bbox (self):
        """
        Calculates the screen coordinate of the bounding box.
        """
        return pygame.Rect(self.pos.x, self.pos.y, self.bbox[2], self.bbox[3])
        

    
