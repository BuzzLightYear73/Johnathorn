"""
Dragon boss — multi-phase boss fight with hovering, fireballs,
fire breath, and ground-slam attacks.
"""
import math
import random

import pygame

from settings import (
    IMAGES_DIR,
    SCREEN_WIDTH,
    SCREEN_HEIGHT,
    GROUND_Y,
    BOSS_HEALTH,
    BOSS_SPRITE_SCALE,
    BOSS_HOVER_Y,
    BOSS_HOVER_SPEED,
    BOSS_HOVER_AMPLITUDE,
    BOSS_FIREBALL_COOLDOWN,
    BOSS_BREATH_COOLDOWN,
    BOSS_BREATH_DAMAGE,
    BOSS_BREATH_DURATION,
    BOSS_SLAM_COOLDOWN,
    BOSS_SLAM_DAMAGE,
    BOSS_SLAM_SPEED,
    BOSS_PHASE2_THRESHOLD,
    BOSS_PHASE3_THRESHOLD,
    BOSS_DEATH_FRAMES,
    RED,
    DARK_RED,
    ORANGE,
    YELLOW,
)
from Boss.fireball import Fireball


# ═══════════════════════════════════════════════════════════════════════
#  Helpers
# ═══════════════════════════════════════════════════════════════════════

def _load_and_scale(filename, scale=BOSS_SPRITE_SCALE, flip_x=True):
    """Load a dragon sprite, scale it, and optionally flip horizontally.

    Returns a fallback surface if the file is missing.
    """
    try:
        raw = pygame.image.load(
            str(IMAGES_DIR / "dragon" / filename)
        ).convert_alpha()
        w = int(raw.get_width() * scale)
        h = int(raw.get_height() * scale)
        scaled = pygame.transform.scale(raw, (w, h))
        if flip_x:
            scaled = pygame.transform.flip(scaled, True, False)
        return scaled
    except (pygame.error, FileNotFoundError):
        # Fallback: solid coloured rectangle at approximate size
        fallback_w = int(72 * scale)
        fallback_h = int(97 * scale)
        surf = pygame.Surface((fallback_w, fallback_h), pygame.SRCALPHA)
        surf.fill(DARK_RED)
        return surf


# ═══════════════════════════════════════════════════════════════════════
#  Dragon
# ═══════════════════════════════════════════════════════════════════════

class Dragon(pygame.sprite.Sprite):
    """Multi-phase dragon boss positioned on the right side of the arena."""

    # ── Construction ──────────────────────────────────────────────────
    def __init__(self):
        super().__init__()

        # -- sprite sets (all flipped to face left) --------------------
        self.idle_image = _load_and_scale("dragStanding.png")

        self.breath_frames = [
            _load_and_scale(f"dragBreath{i}.png") for i in range(1, 5)
        ]

        self.fireball_launch_frames = [
            _load_and_scale(f"dragFBall{i}.png") for i in range(1, 4)
        ]

        self.death_frames = [
            _load_and_scale(f"dragDeath{i}.png") for i in range(1, 6)
        ]

        self.shadow_image = _load_and_scale("dragShadow.png", flip_x=False)

        # -- state machine ---------------------------------------------
        self.image = self.idle_image
        self.rect = self.image.get_rect()
        self.rect.x = SCREEN_WIDTH - self.rect.width - 30
        self.rect.y = BOSS_HOVER_Y

        self.health = BOSS_HEALTH
        self.max_health = BOSS_HEALTH
        self.phase = 1
        self.state = "hovering"  # hovering | fireball | breathing | slamming | dying | dead
        self.state_timer = 0

        self.hover_timer = 0.0
        self.base_y = BOSS_HOVER_Y

        # -- cooldowns (in frames) -------------------------------------
        self.fireball_cooldown = BOSS_FIREBALL_COOLDOWN
        self.breath_cooldown = BOSS_BREATH_COOLDOWN
        self.slam_cooldown = BOSS_SLAM_COOLDOWN
        self.attack_cooldown = 60  # initial grace period

        self.facing_left = True

        # -- active damage areas (None when inactive) ------------------
        self.breath_rect = None
        self.slam_shockwave_rect = None

        # -- projectiles -----------------------------------------------
        self.fireballs = pygame.sprite.Group()

        # -- slam bookkeeping ------------------------------------------
        self._slam_origin_y = self.rect.y
        self._slam_landed = False

        # -- animation bookkeeping -------------------------------------
        self._anim_index = 0
        self._anim_timer = 0

    # ── Per-frame update ──────────────────────────────────────────────
    def update(self, player_rect):
        if self.state == "dead":
            return

        self._update_phase()

        # -- dying animation -------------------------------------------
        if self.state == "dying":
            self._animate_death()
            self.fireballs.update()
            return

        # -- hover bob -------------------------------------------------
        if self.state == "hovering":
            self.hover_timer += BOSS_HOVER_SPEED
            self.rect.y = int(
                self.base_y + math.sin(self.hover_timer) * BOSS_HOVER_AMPLITUDE
            )

        # -- tick cooldowns --------------------------------------------
        self.fireball_cooldown = max(0, self.fireball_cooldown - 1)
        self.breath_cooldown = max(0, self.breath_cooldown - 1)
        self.slam_cooldown = max(0, self.slam_cooldown - 1)
        self.attack_cooldown = max(0, self.attack_cooldown - 1)

        # -- state execution -------------------------------------------
        if self.state == "hovering":
            self.image = self.idle_image
            self.breath_rect = None
            self.slam_shockwave_rect = None
            if self.attack_cooldown <= 0:
                self._choose_attack(player_rect)

        elif self.state == "fireball":
            self._run_fireball_state()

        elif self.state == "breathing":
            self._run_breath_state()

        elif self.state == "slamming":
            self._run_slam_state()

        # -- update fireballs ------------------------------------------
        self.fireballs.update()

    # ── Phase calculation ─────────────────────────────────────────────
    def _update_phase(self):
        ratio = self.health / self.max_health
        if ratio <= BOSS_PHASE3_THRESHOLD:
            self.phase = 3
        elif ratio <= BOSS_PHASE2_THRESHOLD:
            self.phase = 2
        else:
            self.phase = 1

    # ── Attack selection ──────────────────────────────────────────────
    def _choose_attack(self, player_rect):
        available = []

        if self.fireball_cooldown <= 0:
            available.append("fireball")

        if self.phase >= 2 and self.breath_cooldown <= 0:
            available.append("breath")

        if self.phase >= 3 and self.slam_cooldown <= 0:
            available.append("slam")

        if not available:
            return

        choice = random.choice(available)

        if choice == "fireball":
            self._start_fireball(player_rect)
        elif choice == "breath":
            self._start_breath()
        elif choice == "slam":
            self._start_slam()

    # ── Fireball attack ───────────────────────────────────────────────
    def _start_fireball(self, player_rect):
        self.state = "fireball"
        self.state_timer = 30
        self._anim_index = 0
        self._anim_timer = 0

        # Reset cooldown (Phase 3 = faster)
        cd = BOSS_FIREBALL_COOLDOWN
        if self.phase == 3:
            cd = int(cd * 0.6)
        self.fireball_cooldown = cd

        # Spawn fireball from the dragon's left-centre (mouth area)
        spawn_x = self.rect.left
        spawn_y = self.rect.centery
        fb = Fireball(spawn_x, spawn_y, player_rect.centerx, player_rect.centery)
        self.fireballs.add(fb)

    def _run_fireball_state(self):
        # Animate launch frames
        frame_dur = max(1, 30 // len(self.fireball_launch_frames))
        self._anim_timer += 1
        if self._anim_timer >= frame_dur:
            self._anim_timer = 0
            self._anim_index = min(
                self._anim_index + 1, len(self.fireball_launch_frames) - 1
            )
        self.image = self.fireball_launch_frames[self._anim_index]

        self.state_timer -= 1
        if self.state_timer <= 0:
            self._end_attack()

    # ── Fire breath attack ────────────────────────────────────────────
    def _start_breath(self):
        self.state = "breathing"
        self.state_timer = BOSS_BREATH_DURATION
        self._anim_index = 0
        self._anim_timer = 0

        cd = BOSS_BREATH_COOLDOWN
        if self.phase == 3:
            cd = int(cd * 0.6)
        self.breath_cooldown = cd

        # Breath hitbox: wide rect extending LEFT from dragon's mouth
        breath_w = 300
        breath_h = 60
        self.breath_rect = pygame.Rect(
            self.rect.left - breath_w,
            self.rect.centery - breath_h // 2,
            breath_w,
            breath_h,
        )

    def _run_breath_state(self):
        # Cycle through breath animation frames
        frame_dur = max(1, BOSS_BREATH_DURATION // (len(self.breath_frames) * 2))
        self._anim_timer += 1
        if self._anim_timer >= frame_dur:
            self._anim_timer = 0
            self._anim_index = (self._anim_index + 1) % len(self.breath_frames)
        self.image = self.breath_frames[self._anim_index]

        self.state_timer -= 1
        if self.state_timer <= 0:
            self.breath_rect = None
            self._end_attack()

    # ── Ground slam attack ────────────────────────────────────────────
    def _start_slam(self):
        self.state = "slamming"
        self.state_timer = 60
        self._slam_origin_y = self.rect.y
        self._slam_landed = False
        self.slam_shockwave_rect = None

        cd = BOSS_SLAM_COOLDOWN
        if self.phase == 3:
            cd = int(cd * 0.6)
        self.slam_cooldown = cd

    def _run_slam_state(self):
        if not self._slam_landed:
            # Descend rapidly
            self.rect.y += BOSS_SLAM_SPEED
            landing_y = GROUND_Y - self.rect.height
            if self.rect.y >= landing_y:
                self.rect.y = landing_y
                self._slam_landed = True

                # Create shockwave at ground level spanning most of the screen
                shockwave_h = 30
                self.slam_shockwave_rect = pygame.Rect(
                    0,
                    GROUND_Y - shockwave_h,
                    SCREEN_WIDTH,
                    shockwave_h,
                )
        else:
            # Hold at ground briefly, then rise back to hover
            self.state_timer -= 1
            # Remove shockwave after a short window
            if self.state_timer <= 45:
                self.slam_shockwave_rect = None
            if self.state_timer <= 0:
                self.rect.y = self._slam_origin_y
                self._end_attack()

    # ── Shared helpers ────────────────────────────────────────────────
    def _end_attack(self):
        """Return to hovering state after an attack concludes."""
        self.state = "hovering"
        self.image = self.idle_image
        self.breath_rect = None
        self.slam_shockwave_rect = None
        # Small gap before next attack so attacks don't chain instantly
        self.attack_cooldown = 30

    # ── Death animation ───────────────────────────────────────────────
    def _animate_death(self):
        frames_per_sprite = max(1, BOSS_DEATH_FRAMES // len(self.death_frames))
        idx = min(
            (BOSS_DEATH_FRAMES - self.state_timer) // frames_per_sprite,
            len(self.death_frames) - 1,
        )
        self.image = self.death_frames[idx]

        self.state_timer -= 1
        if self.state_timer <= 0:
            self.state = "dead"

    # ── Damage interface ──────────────────────────────────────────────
    def take_damage(self, amount):
        """Reduce health; returns True if the dragon just died."""
        if self.state in ("dying", "dead"):
            return False
        self.health -= amount
        if self.health <= 0:
            self.health = 0
            self.state = "dying"
            self.state_timer = BOSS_DEATH_FRAMES
            return True
        return False

    def get_damage_rect(self):
        """Return (rect, damage) for the active damage-dealing area, or None."""
        if self.state == "breathing" and self.breath_rect:
            return self.breath_rect, BOSS_BREATH_DAMAGE
        if self.state == "slamming" and self.slam_shockwave_rect:
            return self.slam_shockwave_rect, BOSS_SLAM_DAMAGE
        return None
