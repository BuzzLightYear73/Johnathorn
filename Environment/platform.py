"""
Environment/platform.py — Platform sprite and procedural generation.
"""
import pygame
import random
from settings import (IMAGES_DIR, PLATFORM_WIDTH, PLATFORM_HEIGHT,
                       PLATFORM_MIN_Y, PLATFORM_MAX_Y)


class Platform(pygame.sprite.Sprite):
    """A static platform the player can land on."""

    def __init__(self, x, y):
        super().__init__()
        try:
            raw = pygame.image.load(str(IMAGES_DIR / 'platform.png'))
            self.image = pygame.transform.scale(raw, (PLATFORM_WIDTH, PLATFORM_HEIGHT))
        except (pygame.error, FileNotFoundError):
            # Stone platform with grass top
            self.image = pygame.Surface((PLATFORM_WIDTH, PLATFORM_HEIGHT), pygame.SRCALPHA)
            # Stone body
            self.image.fill((100, 80, 60))
            # Highlight top edge
            pygame.draw.rect(self.image, (50, 120, 40), (0, 0, PLATFORM_WIDTH, 5))
            # Dark border
            pygame.draw.rect(self.image, (40, 30, 20), (0, 0, PLATFORM_WIDTH, PLATFORM_HEIGHT), 2)
        self.rect = self.image.get_rect()
        self.rect.x = x
        self.rect.y = y

    def update(self, scroll):
        """Shift platform horizontally by *scroll* pixels."""
        self.rect.x += scroll


def generate_platform(screen_width):
    """Create a platform just off the right edge at a random valid height."""
    x = screen_width + random.randint(50, 200)
    y = random.randint(PLATFORM_MIN_Y, PLATFORM_MAX_Y)
    return Platform(x, y)
