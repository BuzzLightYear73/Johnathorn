"""
Pygame/engine.py — Display initialisation and parallax background.
"""
import pygame
from settings import IMAGES_DIR, SCREEN_WIDTH, SCREEN_HEIGHT


def initPygame(width, height, title):
    """Create and return a display surface with the given dimensions and title."""
    screen = pygame.display.set_mode((width, height))
    pygame.display.set_caption(title)
    return screen


class Background(pygame.sprite.Sprite):
    """Parallax-scrolling background that wraps seamlessly."""

    def __init__(self):
        super().__init__()
        try:
            # Try new generated background first
            raw = pygame.image.load(str(IMAGES_DIR / 'background.png'))
            self.image = pygame.transform.scale(
                raw, (SCREEN_WIDTH * 2, SCREEN_HEIGHT)
            )
        except (pygame.error, FileNotFoundError):
            try:
                raw = pygame.image.load(str(IMAGES_DIR / 'castle.jpg'))
                self.image = pygame.transform.scale(
                    raw, (SCREEN_WIDTH * 2, SCREEN_HEIGHT)
                )
            except (pygame.error, FileNotFoundError):
                self.image = pygame.Surface((SCREEN_WIDTH * 2, SCREEN_HEIGHT))
                self.image.fill((20, 20, 40))
        self.rect = self.image.get_rect()

    def draw(self, screen, scroll):
        """Draw the background with parallax effect and seamless wrapping."""
        # Scroll at a fraction of the main scroll for parallax depth
        parallax_speed = 0.3
        width = self.image.get_width()
        offset = int(scroll * parallax_speed) % width
        # Blit twice for seamless wrapping
        screen.blit(self.image, (-offset, 0))
        screen.blit(self.image, (-offset + width, 0))
