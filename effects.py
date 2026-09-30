"""
Johnathorn — Effects system
Screen shake, hit pause, particles, and floating damage numbers.
"""
import random

import pygame

from settings import (
    DAMAGE_NUMBER_FONT_SIZE,
    DAMAGE_NUMBER_LIFETIME,
    DAMAGE_NUMBER_SPEED,
    HIT_PAUSE_FRAMES,
    PARTICLE_GRAVITY,
    PARTICLE_LIFETIME_MAX,
    PARTICLE_LIFETIME_MIN,
    SCREEN_SHAKE_DECAY,
    SCREEN_SHAKE_INTENSITY,
)


class EffectsManager:
    """Centralised manager for screen shake, hit pause, particles, and
    floating damage numbers."""

    def __init__(self):
        # Screen shake
        self.shake_intensity = 0.0
        self.shake_offset = (0, 0)

        # Hit pause (freeze-frame on impact)
        self.hit_pause_timer = 0

        # Visual effects lists
        self.particles = []       # list[dict]
        self.damage_numbers = []  # list[dict]

        # Font for damage numbers (lazy-init to avoid pygame.font not-initialized errors)
        self._font = None

    @property
    def font(self):
        if self._font is None:
            self._font = pygame.font.SysFont("Arial", DAMAGE_NUMBER_FONT_SIZE)
        return self._font

    # ── Screen shake ──────────────────────────────────────────────────

    def screen_shake(self, intensity=None):
        """Start a screen-shake effect.

        Parameters
        ----------
        intensity : float | None
            Shake magnitude in pixels.  Defaults to
            ``SCREEN_SHAKE_INTENSITY`` from settings.
        """
        if intensity is None:
            intensity = SCREEN_SHAKE_INTENSITY
        self.shake_intensity = float(intensity)
        # Compute initial offset immediately
        self.shake_offset = (
            random.uniform(-self.shake_intensity, self.shake_intensity),
            random.uniform(-self.shake_intensity, self.shake_intensity),
        )

    def get_shake_offset(self):
        """Return the current shake offset as ``(dx, dy)``."""
        return self.shake_offset

    # ── Hit pause ─────────────────────────────────────────────────────

    def hit_pause(self, frames=None):
        """Freeze the game for *frames* update ticks.

        Parameters
        ----------
        frames : int | None
            Number of frozen frames.  Defaults to ``HIT_PAUSE_FRAMES``.
        """
        if frames is None:
            frames = HIT_PAUSE_FRAMES
        self.hit_pause_timer = frames

    @property
    def is_paused(self):
        """``True`` while the hit-pause freeze is active."""
        return self.hit_pause_timer > 0

    # ── Particles ─────────────────────────────────────────────────────

    def spawn_particles(self, x, y, color, count, spread=5.0):
        """Create *count* particles at ``(x, y)`` with random velocities.

        Parameters
        ----------
        x, y : float
            Spawn position.
        color : tuple
            RGB colour tuple.
        count : int
            Number of particles to create.
        spread : float
            Maximum magnitude of initial velocity in each axis.
        """
        for _ in range(count):
            lifetime = random.randint(PARTICLE_LIFETIME_MIN, PARTICLE_LIFETIME_MAX)
            self.particles.append(
                {
                    "x": float(x),
                    "y": float(y),
                    "vx": random.uniform(-spread, spread),
                    "vy": random.uniform(-spread, spread),
                    "color": color,
                    "lifetime": lifetime,
                    "max_lifetime": lifetime,
                    "size": random.randint(2, 5),
                }
            )

    # ── Damage numbers ────────────────────────────────────────────────

    def spawn_damage_number(self, x, y, damage):
        """Create a floating damage number at ``(x, y)``.

        Parameters
        ----------
        x, y : float
            Position (world coordinates).
        damage : int | float
            Damage value to display.
        """
        self.damage_numbers.append(
            {
                "x": float(x),
                "y": float(y),
                "text": str(int(damage)),
                "lifetime": DAMAGE_NUMBER_LIFETIME,
                "max_lifetime": DAMAGE_NUMBER_LIFETIME,
                "alpha": 255,
            }
        )

    # ── Per-frame update ──────────────────────────────────────────────

    def update(self):
        """Advance all effects by one frame."""
        # 1. Hit pause: decrement and skip everything else while frozen
        if self.hit_pause_timer > 0:
            self.hit_pause_timer -= 1
            return

        # 2. Screen shake — decay then recompute offset
        if self.shake_intensity > 0:
            self.shake_intensity *= SCREEN_SHAKE_DECAY
            if self.shake_intensity < 0.5:
                self.shake_intensity = 0.0
                self.shake_offset = (0, 0)
            else:
                self.shake_offset = (
                    random.uniform(-self.shake_intensity, self.shake_intensity),
                    random.uniform(-self.shake_intensity, self.shake_intensity),
                )

        # 3. Particles — physics + lifetime
        alive_particles = []
        for p in self.particles:
            p["vy"] += PARTICLE_GRAVITY
            p["x"] += p["vx"]
            p["y"] += p["vy"]
            p["lifetime"] -= 1
            if p["lifetime"] > 0:
                alive_particles.append(p)
        self.particles = alive_particles

        # 4. Damage numbers — float upward + lifetime
        alive_numbers = []
        for dn in self.damage_numbers:
            dn["y"] -= DAMAGE_NUMBER_SPEED
            dn["lifetime"] -= 1
            # Fade alpha proportionally
            if dn["max_lifetime"] > 0:
                dn["alpha"] = max(
                    0, int(255 * dn["lifetime"] / dn["max_lifetime"])
                )
            if dn["lifetime"] > 0:
                alive_numbers.append(dn)
        self.damage_numbers = alive_numbers

    # ── Drawing ───────────────────────────────────────────────────────

    def draw(self, screen, camera_offset=(0, 0)):
        """Render all active effects onto *screen*.

        Parameters
        ----------
        screen : pygame.Surface
            The display surface.
        camera_offset : tuple[int, int]
            ``(ox, oy)`` world-to-screen offset for scrolling.
        """
        ox, oy = camera_offset

        # Particles — small filled circles
        for p in self.particles:
            alpha_ratio = p["lifetime"] / p["max_lifetime"] if p["max_lifetime"] else 1
            radius = max(1, int(p["size"] * alpha_ratio))
            pos = (int(p["x"] + ox), int(p["y"] + oy))
            pygame.draw.circle(screen, p["color"], pos, radius)

        # Damage numbers — text with alpha fade
        for dn in self.damage_numbers:
            if dn["alpha"] <= 0:
                continue
            text_surf = self.font.render(dn["text"], True, (255, 255, 255))
            alpha_surf = pygame.Surface(text_surf.get_size(), pygame.SRCALPHA)
            alpha_surf.fill((255, 255, 255, dn["alpha"]))
            text_surf = text_surf.convert_alpha()
            text_surf.blit(alpha_surf, (0, 0), special_flags=pygame.BLEND_RGBA_MULT)
            pos = (int(dn["x"] + ox), int(dn["y"] + oy))
            screen.blit(text_surf, pos)
