"""
Johnathorn — Enemy module
Orc enemy with patrol, chase, attack AI and knockback support.
"""
import random

import pygame

import settings
from settings import (
    ENEMY_ATTACK_COOLDOWN,
    ENEMY_ATTACK_RANGE,
    ENEMY_BASE_HEALTH,
    ENEMY_CHASE_ACCEL,
    ENEMY_DETECTION_RANGE,
    ENEMY_FRAME_COUNT,
    ENEMY_KNOCKBACK_FRAMES,
    ENEMY_KNOCKBACK_SPEED,
    ENEMY_SPEED_MAX,
    ENEMY_SPEED_MIN,
    ENEMY_SPRITE_SIZE,
    IMAGES_DIR,
)


def _load_frames(directory, names, size):
    """Load individual frame PNGs from a directory and scale them.

    Falls back to coloured placeholder surfaces when files are missing.
    """
    try:
        frames = []
        for name in names:
            img = pygame.image.load(str(directory / name)).convert_alpha()
            frames.append(pygame.transform.scale(img, (size, size)))
        return frames
    except (FileNotFoundError, pygame.error):
        frames = []
        for _ in range(max(len(names), 1)):
            surf = pygame.Surface((size, size), pygame.SRCALPHA)
            surf.fill((0, 180, 0, 200))
            pygame.draw.rect(surf, (0, 100, 0), surf.get_rect(), 2)
            frames.append(surf)
        return frames


class Enemy(pygame.sprite.Sprite):
    """An enemy that patrols, chases, attacks, and can be knocked back."""

    def __init__(self, x, y, speed_multiplier=1.0):
        super().__init__()

        # ── Sprite frames ─────────────────────────────────────────────
        archer_dir = IMAGES_DIR / "archer"
        walk_names = [f"aWalk{i}.png" for i in range(1, 9)]
        attack_names = ["aAttack.png"]

        self.walk_frames = _load_frames(
            archer_dir, walk_names, ENEMY_SPRITE_SIZE
        )
        self.attack_frames = _load_frames(
            archer_dir, attack_names, ENEMY_SPRITE_SIZE
        )

        # Tint enemy frames red to differentiate from player
        self.walk_frames = [self._tint(f, (180, 0, 0, 60)) for f in self.walk_frames]
        self.attack_frames = [self._tint(f, (180, 0, 0, 60)) for f in self.attack_frames]

        self.current_frames = self.walk_frames
        self.frame_index = 0
        self.animation_speed = 0.15
        self.image = self.current_frames[self.frame_index]
        self.rect = self.image.get_rect(topleft=(x, y))

        # ── Stats ─────────────────────────────────────────────────────
        self.health = ENEMY_BASE_HEALTH
        self.speed = (
            random.uniform(ENEMY_SPEED_MIN, ENEMY_SPEED_MAX) * speed_multiplier
        )
        self.velocity_x = 0.0

        # ── Knockback ─────────────────────────────────────────────────
        self.knockback_timer = 0
        self.knockback_dir = 0

        # ── Attack ────────────────────────────────────────────────────
        self.attack_cooldown = 0
        self.attacking = False
        self.facing_right = False

    @staticmethod
    def _tint(surface, color):
        """Return a copy of surface with a color overlay applied."""
        tinted = surface.copy()
        overlay = pygame.Surface(surface.get_size(), pygame.SRCALPHA)
        overlay.fill(color)
        tinted.blit(overlay, (0, 0))
        return tinted

    # ── public API ────────────────────────────────────────────────────

    def update(self, player_rect=None):
        """Advance enemy AI by one frame.

        Parameters
        ----------
        player_rect : pygame.Rect | None
            The player's rect used for detection / chasing / attacking.
        """
        # Tick cooldown
        if self.attack_cooldown > 0:
            self.attack_cooldown -= 1

        # 1. Knockback overrides everything
        if self.knockback_timer > 0:
            self.rect.x += self.knockback_dir * ENEMY_KNOCKBACK_SPEED
            self.knockback_timer -= 1
            self._animate()
            return

        # 2. Player interaction
        if player_rect is not None:
            dist = abs(self.rect.centerx - player_rect.centerx)

            if dist <= ENEMY_ATTACK_RANGE:
                # In attack range — stop and attack
                self.velocity_x = 0.0
                self._start_attack()
            elif dist <= ENEMY_DETECTION_RANGE:
                # Chase the player
                direction = 1 if player_rect.centerx > self.rect.centerx else -1
                self.facing_right = direction == 1
                self.velocity_x += direction * ENEMY_CHASE_ACCEL
                # Clamp chase speed
                if abs(self.velocity_x) > self.speed:
                    self.velocity_x = self.speed * (
                        1 if self.velocity_x > 0 else -1
                    )
                self.current_frames = self.walk_frames
                self.attacking = False
            else:
                # Out of range — patrol
                self._patrol()
        else:
            # No player info — patrol
            self._patrol()

        self.rect.x += int(self.velocity_x)

        # 4. Remove if off-screen left
        if self.rect.right < 0:
            self.kill()

        # 5. Animate
        self._animate()

    def take_damage(self, damage):
        """Subtract *damage* from health.

        Returns
        -------
        bool
            ``True`` if the enemy died (health <= 0), ``False`` otherwise.
        """
        self.health -= damage
        return self.health <= 0

    def apply_knockback(self, direction):
        """Push the enemy in *direction* (1 = right, -1 = left)."""
        self.knockback_timer = ENEMY_KNOCKBACK_FRAMES
        self.knockback_dir = direction

    # ── private helpers ───────────────────────────────────────────────

    def _patrol(self):
        """Move leftward at base speed."""
        self.velocity_x = -self.speed
        self.facing_right = False
        self.current_frames = self.walk_frames
        self.attacking = False

    def _start_attack(self):
        """Switch to attack animation and reset cooldown."""
        if self.attack_cooldown <= 0:
            self.current_frames = self.attack_frames
            self.attacking = True
            self.attack_cooldown = ENEMY_ATTACK_COOLDOWN

    def _animate(self):
        """Advance frame index and update self.image."""
        self.frame_index += self.animation_speed
        if self.frame_index >= len(self.current_frames):
            self.frame_index = 0
            if self.attacking:
                self.attacking = False
                self.current_frames = self.walk_frames
        frame = self.current_frames[int(self.frame_index)]
        if self.facing_right:
            self.image = frame
        else:
            self.image = pygame.transform.flip(frame, True, False)
