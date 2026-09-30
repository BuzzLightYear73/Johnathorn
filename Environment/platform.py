"""
Environment/platform.py — Platform sprite and layout loading.
"""
import pygame
from settings import (IMAGES_DIR, PLATFORM_WIDTH, PLATFORM_HEIGHT,
                       WAVE_PLATFORMS, BOSS_PLATFORMS)


class Platform(pygame.sprite.Sprite):
    """A static platform the player can land on.

    Platforms use world-space coordinates.  The camera offset is applied
    at render time by the game loop, so ``rect.x / rect.y`` always
    represent the platform's true world position.
    """

    def __init__(self, x, y):
        super().__init__()
        try:
            raw = pygame.image.load(str(IMAGES_DIR / 'platform.png'))
            self.image = pygame.transform.scale(raw, (PLATFORM_WIDTH, PLATFORM_HEIGHT))
        except (pygame.error, FileNotFoundError):
            # Stone platform with grass top — semi-transparent
            self.image = pygame.Surface((PLATFORM_WIDTH, PLATFORM_HEIGHT), pygame.SRCALPHA)
            # Stone body (semi-transparent)
            self.image.fill((80, 65, 45, 180))
            # Grass top strip
            pygame.draw.rect(self.image, (45, 100, 35, 200), (0, 0, PLATFORM_WIDTH, 4))
            # Subtle highlight below grass
            pygame.draw.rect(self.image, (90, 75, 50, 160), (0, 4, PLATFORM_WIDTH, 2))
            # Bottom shadow
            pygame.draw.rect(self.image, (40, 30, 20, 120), (0, PLATFORM_HEIGHT - 2, PLATFORM_WIDTH, 2))
        self.rect = self.image.get_rect()
        self.rect.x = x
        self.rect.y = y

    def update(self, *_args):
        """Platforms are static in world-space; camera handles rendering offset."""
        pass


def load_wave_platforms(wave_num):
    """Return a list of Platform instances for the given wave.

    Falls back to wave 1 layout if wave_num has no explicit entry.
    """
    layout = WAVE_PLATFORMS.get(wave_num, WAVE_PLATFORMS.get(1, []))
    return [Platform(x, y) for x, y in layout]


def load_boss_platforms():
    """Return the curated boss arena platforms."""
    return [Platform(x, y) for x, y in BOSS_PLATFORMS]
