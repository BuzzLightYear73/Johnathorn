"""
Character/projectile.py — Player projectiles (arrows, fireballs).
"""
import pygame
import math
from settings import IMAGES_DIR, SCREEN_WIDTH, SCREEN_HEIGHT


class PlayerProjectile(pygame.sprite.Sprite):
    """A projectile fired by the player (arrow or magic bolt)."""

    def __init__(self, x, y, direction, proj_type='arrow', damage=25):
        """
        Parameters
        ----------
        x, y : int
            Spawn position.
        direction : int
            1 = right, -1 = left.
        proj_type : str
            'arrow' or 'magic' — determines sprite and speed.
        damage : int
            Damage dealt on hit.
        """
        super().__init__()
        self.damage = damage
        self.direction = direction

        if proj_type == 'arrow':
            speed = 10
            sprite_path = IMAGES_DIR / 'archer' / 'arrows' / 'arrow_flat.png'
            fallback_color = (180, 140, 60)
            fallback_size = (30, 6)
        else:  # magic
            speed = 8
            sprite_path = IMAGES_DIR / 'mage' / 'fireball.png'
            fallback_color = (100, 60, 220)
            fallback_size = (20, 20)

        try:
            raw = pygame.image.load(str(sprite_path)).convert_alpha()
            self.image = pygame.transform.scale(raw, (30, 12) if proj_type == 'arrow' else (24, 24))
        except (pygame.error, FileNotFoundError):
            self.image = pygame.Surface(fallback_size, pygame.SRCALPHA)
            self.image.fill(fallback_color)

        # Flip if going left
        if direction < 0:
            self.image = pygame.transform.flip(self.image, True, False)

        self.rect = self.image.get_rect(center=(x, y))
        self.vx = speed * direction
        self.lifetime = 120  # frames before auto-kill

        # Magic bolt glow effect
        if proj_type == 'magic':
            glow = pygame.Surface((self.rect.width + 8, self.rect.height + 8), pygame.SRCALPHA)
            pygame.draw.ellipse(glow, (120, 80, 255, 60), glow.get_rect())
            self._glow = glow
        else:
            self._glow = None

    def update(self):
        self.rect.x += self.vx
        self.lifetime -= 1

        # Kill if off-screen or expired
        if (self.rect.right < -20 or self.rect.left > SCREEN_WIDTH + 20
                or self.lifetime <= 0):
            self.kill()

    def draw(self, surface, offset=(0, 0)):
        """Draw with optional glow effect."""
        if self._glow:
            surface.blit(self._glow, (
                self.rect.x - 4 + offset[0],
                self.rect.y - 4 + offset[1],
            ))
        surface.blit(self.image, (
            self.rect.x + offset[0],
            self.rect.y + offset[1],
        ))
