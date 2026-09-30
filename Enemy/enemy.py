"""
Johnathorn — Enemy module
Enemy types with patrol, chase, attack AI and knockback support.
Supports skeleton_warrior, skeleton_archer, and shadow_bat via ENEMY_TYPES config.
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
    ENEMY_KNOCKBACK_FRAMES,
    ENEMY_KNOCKBACK_SPEED,
    ENEMY_SPEED_MAX,
    ENEMY_SPEED_MIN,
    ENEMY_SPRITE_SIZE,
    ENEMY_TYPES,
    IMAGES_DIR,
)
from Animation.controller import AnimationController
from Animation.loader import load_clips_from_config


class Enemy(pygame.sprite.Sprite):
    """An enemy that patrols, chases, attacks, and can be knocked back."""

    def __init__(self, x, y, speed_multiplier=1.0, enemy_type='skeleton_warrior'):
        super().__init__()
        self.enemy_type = enemy_type
        type_config = ENEMY_TYPES.get(enemy_type, {})

        # ── Load animation clips ──────────────────────────────────────
        self._load_sprites(type_config)
        self.image = self.animator.get_frame(True)
        self.rect = self.image.get_rect(topleft=(x, y))

        # ── Stats ─────────────────────────────────────────────────────
        health_mult = type_config.get('health_mult', 1.0)
        self.max_health = int(ENEMY_BASE_HEALTH * health_mult)
        self.health = self.max_health
        speed_mult = type_config.get('speed_mult', 1.0)
        self.speed = (
            random.uniform(ENEMY_SPEED_MIN, ENEMY_SPEED_MAX)
            * speed_multiplier * speed_mult
        )
        self.velocity_x = 0.0

        # ── Knockback ─────────────────────────────────────────────────
        self.knockback_timer = 0
        self.knockback_dir = 0

        # ── Attack ────────────────────────────────────────────────────
        self.attack_cooldown = 0
        self.attacking = False
        self.facing_right = False
        self.attack_phase = None       # None | 'startup' | 'active' | 'recovery'
        self.attack_phase_timer = 0
        self._attack_hit_this_swing = False

        # Combat config from enemy type
        self._stagger_frames = type_config.get('stagger_frames', 15)
        self._attack_startup = type_config.get('attack_startup', 8)
        self._attack_active = type_config.get('attack_active', 4)
        self._attack_recovery = type_config.get('attack_recovery', 10)
        self._damage_mult = type_config.get('damage_mult', 1.0)

    def _load_sprites(self, type_config):
        """Load enemy animation clips via AnimationController."""
        size = (ENEMY_SPRITE_SIZE, ENEMY_SPRITE_SIZE)

        if 'animations' in type_config:
            sprite_dir = IMAGES_DIR / type_config['sprite_dir']
            clips = load_clips_from_config(type_config['animations'], sprite_dir, size)
            if clips:
                self.animator = AnimationController(clips, default_clip='idle')
                # Legacy references
                walk_clip = clips.get('walk', {})
                attack_clip = clips.get('attack', {})
                self.walk_frames = walk_clip.get('frames', [])
                self.attack_frames = attack_clip.get('frames', self.walk_frames)
                self.current_frames = self.walk_frames
                return

        # Fallback: green placeholder sprites
        placeholder = []
        for _ in range(4):
            surf = pygame.Surface(size, pygame.SRCALPHA)
            surf.fill((0, 180, 0, 200))
            pygame.draw.rect(surf, (0, 100, 0), surf.get_rect(), 2)
            placeholder.append(surf)
        clips = {'idle': placeholder, 'walk': placeholder, 'attack': placeholder}
        self.animator = AnimationController(clips, default_clip='idle')
        self.walk_frames = placeholder
        self.attack_frames = placeholder
        self.current_frames = placeholder

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

        # 5. Attack phase progression
        self._update_attack_phase()

        # 6. Animate
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

    def apply_knockback(self, direction, force=None):
        """Push the enemy in *direction* (1 = right, -1 = left)."""
        self.knockback_timer = ENEMY_KNOCKBACK_FRAMES
        self.knockback_dir = direction
        if force is not None:
            self._knockback_force = force
        # Interrupt attack on knockback
        self.attacking = False
        self.attack_phase = None
        self.attack_phase_timer = 0

    @property
    def in_active_attack(self):
        """True if the enemy is in the active damage-dealing phase of an attack."""
        return self.attacking and self.attack_phase == 'active'

    # ── private helpers ───────────────────────────────────────────────

    def _patrol(self):
        """Move leftward at base speed."""
        self.velocity_x = -self.speed
        self.facing_right = False
        self.attacking = False

    def _start_attack(self):
        """Switch to attack animation and reset cooldown."""
        if self.attack_cooldown <= 0 and self.attack_phase is None:
            self.attacking = True
            self.attack_cooldown = ENEMY_ATTACK_COOLDOWN
            self.attack_phase = 'startup'
            self.attack_phase_timer = 0
            self._attack_hit_this_swing = False

    def _update_attack_phase(self):
        """Progress enemy attack through startup → active → recovery."""
        if self.attack_phase is None:
            return

        self.attack_phase_timer += 1

        if self.attack_phase == 'startup':
            if self.attack_phase_timer >= self._attack_startup:
                self.attack_phase = 'active'
                self.attack_phase_timer = 0
        elif self.attack_phase == 'active':
            if self.attack_phase_timer >= self._attack_active:
                self.attack_phase = 'recovery'
                self.attack_phase_timer = 0
        elif self.attack_phase == 'recovery':
            if self.attack_phase_timer >= self._attack_recovery:
                self.attack_phase = None
                self.attacking = False

    def _resolve_animation_state(self):
        """Determine which animation clip should play.

        Priority: die → stagger → attack → walk → idle
        """
        if self.health <= 0:
            return 'die'
        if self.knockback_timer > 0:
            return 'stagger'
        if self.attacking:
            return 'attack'
        if abs(self.velocity_x) > 0.1:
            return 'walk'
        return 'idle'

    def _animate(self):
        """Drive the animation controller based on current state."""
        state = self._resolve_animation_state()
        self.animator.play(state)
        self.animator.update()
        self.image = self.animator.get_frame(self.facing_right)

        # Auto-end attack when animation finishes
        if self.attacking and self.animator.finished:
            self.attacking = False
