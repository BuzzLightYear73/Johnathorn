"""
powerUp.py — Collectible power-ups with bob animation and buff effects.
"""
import pygame
import random
import math
from settings import (POWERUP_SIZE, POWERUP_BOB_SPEED, POWERUP_BOB_AMPLITUDE,
                       POWERUP_DROP_CHANCE, HEALTH_RESTORE, PLAYER_HEALTH,
                       SPEED_BOOST_DURATION, ATTACK_BOOST_DURATION,
                       GREEN, BLUE, RED, IMAGES_DIR)

# Map power-up types to their display colour
_TYPE_COLORS = {
    'health': GREEN,
    'speed': BLUE,
    'attack': RED,
}


class PowerUp(pygame.sprite.Sprite):
    """A collectible power-up that bobs in the air and applies a buff."""

    def __init__(self, x, y, power_type):
        super().__init__()
        self.power_type = power_type
        color = _TYPE_COLORS.get(power_type, GREEN)
        try:
            raw = pygame.image.load(str(IMAGES_DIR / 'p_up.png')).convert_alpha()
            self.image = pygame.transform.scale(raw, (POWERUP_SIZE, POWERUP_SIZE))
            # Tint overlay by type
            tint = pygame.Surface((POWERUP_SIZE, POWERUP_SIZE), pygame.SRCALPHA)
            tint.fill((*color, 80))
            self.image.blit(tint, (0, 0))
        except (pygame.error, FileNotFoundError):
            self.image = pygame.Surface((POWERUP_SIZE, POWERUP_SIZE))
            self.image.fill(color)
        self.rect = self.image.get_rect()
        self.rect.x = x
        self.rect.y = y
        self.base_y = y
        self.bob_timer = 0.0

    def update(self):
        """Animate a gentle up-and-down bob."""
        self.bob_timer += POWERUP_BOB_SPEED
        self.rect.y = self.base_y + int(math.sin(self.bob_timer) * POWERUP_BOB_AMPLITUDE)

    def apply(self, player):
        """Apply the buff to *player* and remove this power-up from all groups."""
        if self.power_type == 'health':
            player.health = min(PLAYER_HEALTH, player.health + HEALTH_RESTORE)
        elif self.power_type == 'speed':
            player.speed_boosted = True
            player.speed_boost_timer = SPEED_BOOST_DURATION
        elif self.power_type == 'attack':
            player.attack_boosted = True
            player.attack_boost_timer = ATTACK_BOOST_DURATION
        self.kill()


def try_spawn_powerup(x, y):
    """Roll for a power-up drop. Returns a PowerUp or None."""
    if random.random() < POWERUP_DROP_CHANCE:
        power_type = random.choice(['health', 'speed', 'attack'])
        return PowerUp(x, y, power_type)
    return None
