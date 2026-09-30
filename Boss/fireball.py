"""
Fireball projectile fired by the Dragon boss.
"""
import math
import pygame
from settings import (
    IMAGES_DIR,
    SCREEN_WIDTH,
    SCREEN_HEIGHT,
    BOSS_FIREBALL_SPEED,
    BOSS_FIREBALL_DAMAGE,
    BOSS_FIREBALL_SIZE,
    ORANGE,
    YELLOW,
)


class Fireball(pygame.sprite.Sprite):
    """A single fireball projectile that travels toward a target position."""

    def __init__(self, x, y, target_x, target_y):
        super().__init__()

        # ── Load / fallback sprite ────────────────────────────────────
        try:
            raw = pygame.image.load(
                str(IMAGES_DIR / "dragon" / "dragFireBall.png")
            ).convert_alpha()
            self.image = pygame.transform.scale(
                raw, (BOSS_FIREBALL_SIZE, BOSS_FIREBALL_SIZE)
            )
        except (pygame.error, FileNotFoundError):
            self.image = pygame.Surface(
                (BOSS_FIREBALL_SIZE, BOSS_FIREBALL_SIZE), pygame.SRCALPHA
            )
            pygame.draw.circle(
                self.image,
                ORANGE,
                (BOSS_FIREBALL_SIZE // 2, BOSS_FIREBALL_SIZE // 2),
                BOSS_FIREBALL_SIZE // 2,
            )
            pygame.draw.circle(
                self.image,
                YELLOW,
                (BOSS_FIREBALL_SIZE // 2, BOSS_FIREBALL_SIZE // 2),
                BOSS_FIREBALL_SIZE // 4,
            )

        self.rect = self.image.get_rect(center=(x, y))

        # ── Velocity toward target ────────────────────────────────────
        dx = target_x - x
        dy = target_y - y
        dist = math.hypot(dx, dy)
        if dist == 0:
            dist = 1  # avoid division by zero
        self.vx = (dx / dist) * BOSS_FIREBALL_SPEED
        self.vy = (dy / dist) * BOSS_FIREBALL_SPEED

        self.damage = BOSS_FIREBALL_DAMAGE

    # ── Per-frame update ──────────────────────────────────────────────
    def update(self):
        self.rect.x += self.vx
        self.rect.y += self.vy

        # Remove when well off-screen
        if (
            self.rect.right < -50
            or self.rect.left > SCREEN_WIDTH + 50
            or self.rect.bottom < -50
            or self.rect.top > SCREEN_HEIGHT + 50
        ):
            self.kill()
