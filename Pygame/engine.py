"""
Pygame/engine.py — Display initialisation and parallax background.
"""
import pygame
from settings import IMAGES_DIR, SCREEN_WIDTH, SCREEN_HEIGHT, ARENA_WIDTH


def initPygame(width, height, title):
    """Create and return a display surface with the given dimensions and title."""
    screen = pygame.display.set_mode((width, height))
    pygame.display.set_caption(title)
    return screen


class Background(pygame.sprite.Sprite):
    """Parallax-scrolling background that wraps seamlessly."""

    def __init__(self):
        super().__init__()
        # Scale background to cover the full arena width (with wrapping room)
        bg_width = max(ARENA_WIDTH, SCREEN_WIDTH * 2)
        try:
            # Try new generated background first
            raw = pygame.image.load(str(IMAGES_DIR / 'background.png'))
            self.image = pygame.transform.scale(
                raw, (bg_width, SCREEN_HEIGHT)
            )
        except (pygame.error, FileNotFoundError):
            try:
                raw = pygame.image.load(str(IMAGES_DIR / 'castle.jpg'))
                self.image = pygame.transform.scale(
                    raw, (bg_width, SCREEN_HEIGHT)
                )
            except (pygame.error, FileNotFoundError):
                self.image = pygame.Surface((bg_width, SCREEN_HEIGHT))
                self.image.fill((20, 20, 40))
        self.rect = self.image.get_rect()

    def draw(self, screen, camera_x):
        """Draw the background with parallax effect and seamless wrapping.

        *camera_x* is the world-space camera offset (pixels).
        """
        parallax_speed = 0.3
        width = self.image.get_width()
        offset = int(camera_x * parallax_speed) % width
        # Blit twice for seamless wrapping
        screen.blit(self.image, (-offset, 0))
        screen.blit(self.image, (-offset + width, 0))
