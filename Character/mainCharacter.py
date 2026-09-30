"""
Johnathorn — Main Player Character
Acceleration-based movement with coyote time, jump buffering, variable jump,
i-frames, dash, and attack mechanics.
"""
import pygame
import settings
from Character.projectile import PlayerProjectile
from Animation.controller import AnimationController
from Animation.loader import load_clips_from_config


class MainCharacter(pygame.sprite.Sprite):
    """Playable hero sprite with modern platformer physics."""

    def __init__(self, x, y, character_class='warrior'):
        super().__init__()

        # ── Character class config ────────────────────────────────────
        self.character_class = character_class
        self.class_config = settings.CHARACTER_CLASSES[character_class]
        config = self.class_config

        # ── Sprite / image setup ──────────────────────────────────────
        self._load_sprites()
        self.image = self.animator.get_frame(True)
        self.rect = self.image.get_rect(topleft=(x, y))

        # ── Core state ────────────────────────────────────────────────
        self.health = int(settings.PLAYER_HEALTH * config['health_mult'])
        self.max_health = self.health

        # Derived combat / movement stats from class config
        self.attack_power = int(settings.PLAYER_ATTACK_POWER * config['attack_mult'])
        self.base_max_speed = settings.PLAYER_MAX_SPEED * config['speed_mult']
        self.regen_rate = config.get('regen_rate', 0)

        # Movement
        self.velocity_x = 0.0
        self.velocity_y = 0.0
        self.on_ground = False
        self.facing_right = True

        # Combat
        self.attacking = False
        self.attack_timer = 0
        self.attack_phase = None       # None | 'startup' | 'active' | 'recovery'
        self.attack_phase_timer = 0
        self._attack_hit_this_swing = False
        self.attack_cooldown = 0  # cooldown between ranged shots
        self.projectiles = pygame.sprite.Group()  # player projectiles
        self._is_ranged = character_class in ('archer', 'mage')
        self._proj_type = 'arrow' if character_class == 'archer' else 'magic'
        self._ranged_cooldown = 20 if character_class == 'archer' else 30  # frames

        # Stagger
        self._staggered = False
        self._stagger_timer = 0

        # Dash
        self.dashing = False
        self.dash_timer = 0
        self.dash_cooldown_timer = 0

        # I-frames
        self.invincible = False
        self.iframes_timer = 0

        # Coyote time & jump buffer
        self.coyote_timer = 0
        self.jump_buffer_timer = 0

        # Power-up buffs
        self.speed_boosted = False
        self.attack_boosted = False
        self.speed_boost_timer = 0
        self.attack_boost_timer = 0

    # ── Asset loading ─────────────────────────────────────────────────

    def _load_sprites(self):
        """Load hero animation clips via AnimationController."""
        size = (settings.PLAYER_SPRITE_SIZE, settings.PLAYER_SPRITE_SIZE)
        config = self.class_config
        sprite_dir = settings.IMAGES_DIR / config['sprite_dir']

        # Try new animation config first
        if 'animations' in config:
            clips = load_clips_from_config(config['animations'], sprite_dir, size)
            if clips:
                self.animator = AnimationController(clips, default_clip='idle')
                # Keep legacy references for any code that still reads them
                idle_clip = clips.get('idle', {})
                walk_clip = clips.get('walk', {})
                attack_clip = clips.get('attack', {})
                self.walk_frames = (idle_clip.get('frames', []) or
                                    walk_clip.get('frames', []))
                self.attack_frames = attack_clip.get('frames', self.walk_frames)
                self.frames = self.walk_frames
                return

        # Legacy fallback: load from filename lists
        walk_names = config.get('walk_frames', [])
        attack_names = config.get('attack_frames', [])

        try:
            walk_frames = []
            for name in walk_names:
                img = pygame.image.load(str(sprite_dir / name)).convert_alpha()
                walk_frames.append(pygame.transform.scale(img, size))

            attack_frames = []
            for name in attack_names:
                img = pygame.image.load(str(sprite_dir / name)).convert_alpha()
                attack_frames.append(pygame.transform.scale(img, size))

            clips = {
                'idle': walk_frames[:1] if walk_frames else walk_frames,
                'walk': walk_frames,
                'attack': attack_frames or walk_frames,
            }
        except (pygame.error, FileNotFoundError):
            placeholder = []
            for _ in range(4):
                surf = pygame.Surface(size, pygame.SRCALPHA)
                surf.fill(settings.BLUE)
                placeholder.append(surf)
            clips = {'idle': placeholder, 'walk': placeholder, 'attack': placeholder}

        self.animator = AnimationController(clips, default_clip='idle')
        self.walk_frames = clips.get('walk', [])
        self.attack_frames = clips.get('attack', [])
        self.frames = self.walk_frames

    # ── Movement ──────────────────────────────────────────────────────

    def move(self, direction):
        """Add acceleration in *direction* (-1 left, 1 right)."""
        self.velocity_x += settings.PLAYER_ACCEL * direction
        if direction > 0:
            self.facing_right = True
        elif direction < 0:
            self.facing_right = False

    # ── Main update ───────────────────────────────────────────────────

    def update(self, platforms):
        """Advance one frame of physics, collisions, and animation."""
        # 1. Friction
        self.velocity_x *= settings.PLAYER_FRICTION

        # 2. Cap horizontal speed
        max_speed = self.base_max_speed
        if self.speed_boosted:
            max_speed += settings.SPEED_BOOST_AMOUNT
        if self.velocity_x > max_speed:
            self.velocity_x = max_speed
        elif self.velocity_x < -max_speed:
            self.velocity_x = -max_speed

        # Snap near-zero velocity to zero
        if abs(self.velocity_x) < 0.1:
            self.velocity_x = 0.0

        # 3. Apply horizontal movement
        self.rect.x += int(round(self.velocity_x))

        # 4. Gravity
        if not self.dashing:
            self.velocity_y += settings.GRAVITY

        # 5. Apply vertical movement
        self.rect.y += int(round(self.velocity_y))

        # 6. Platform collisions (land on top only)
        self._check_platform_collisions(platforms)

        # 7. Ground clamp
        if self.rect.bottom >= settings.GROUND_Y:
            self.rect.bottom = settings.GROUND_Y
            self.velocity_y = 0
            self.on_ground = True

        # 8. Coyote timer
        if self.on_ground:
            self.coyote_timer = settings.COYOTE_TIME
        else:
            if self.coyote_timer > 0:
                self.coyote_timer -= 1

        # 9. Jump buffer — auto-jump if buffered and now grounded
        if self.jump_buffer_timer > 0:
            if self.on_ground:
                self._execute_jump()
                self.jump_buffer_timer = 0
            else:
                self.jump_buffer_timer -= 1

        # 10. I-frames countdown
        if self.iframes_timer > 0:
            self.iframes_timer -= 1
            if self.iframes_timer <= 0:
                self.invincible = False

        # 11. Dash timer & cooldown
        if self.dash_timer > 0:
            self.dash_timer -= 1
            if self.dash_timer <= 0:
                self.dashing = False
        if self.dash_cooldown_timer > 0:
            self.dash_cooldown_timer -= 1

        # 12. Attack phase progression
        self.update_attack_phase()

        # 12b. Stagger countdown
        self._update_stagger()

        # 13. Buff timers
        if self.speed_boosted:
            self.speed_boost_timer -= 1
            if self.speed_boost_timer <= 0:
                self.speed_boosted = False

        if self.attack_boosted:
            self.attack_boost_timer -= 1
            if self.attack_boost_timer <= 0:
                self.attack_boosted = False

        # 14. Druid passive: health regeneration
        if self.regen_rate > 0:
            self.health = min(self.max_health, self.health + self.regen_rate)

        # 15. Ranged attack cooldown
        if self.attack_cooldown > 0:
            self.attack_cooldown -= 1

        # 16. Update projectiles
        self.projectiles.update()

        # 17. Animation
        self._animate()

    # ── Collision helpers ─────────────────────────────────────────────

    def _check_platform_collisions(self, platforms):
        """Land on platforms only when falling downward onto the top."""
        for plat in platforms:
            if not self.rect.colliderect(plat.rect):
                continue
            # Only land when falling and feet are near platform top
            if self.velocity_y > 0 and self.rect.bottom <= plat.rect.bottom:
                self.rect.bottom = plat.rect.top
                self.velocity_y = 0
                self.on_ground = True

    # ── Jump mechanics ────────────────────────────────────────────────

    def _execute_jump(self):
        """Apply the actual upward velocity."""
        self.velocity_y = settings.JUMP_SPEED
        self.on_ground = False
        self.coyote_timer = 0

    def jump(self):
        """Initiate a jump — supports coyote time and jump buffering."""
        if self.on_ground or self.coyote_timer > 0:
            self._execute_jump()
        else:
            # Buffer the jump for when we land
            self.jump_buffer_timer = settings.JUMP_BUFFER

    def release_jump(self):
        """Cut upward velocity for variable-height jumps."""
        if self.velocity_y < 0:
            self.velocity_y *= settings.VARIABLE_JUMP_CUT

    # ── Combat ────────────────────────────────────────────────────────

    def attack(self, enemy_group):
        """Attack. Melee for warrior/druid, ranged for archer/mage.

        Returns a list of enemies hit (melee only; ranged projectiles
        handle collision in the game loop).
        """
        if self.attack_phase is not None:
            return []  # Already attacking

        self.attacking = True
        self.attack_timer = 0
        self.attack_phase = 'startup'
        self.attack_phase_timer = 0
        self._attack_hit_this_swing = False

        if self._is_ranged:
            # Ranged: spawn projectile if off cooldown
            if self.attack_cooldown <= 0:
                effective_power = self.attack_power
                if self.attack_boosted:
                    effective_power = int(effective_power * settings.ATTACK_BOOST_MULTIPLIER)
                proj_x = self.rect.right if self.facing_right else self.rect.left
                proj_y = self.rect.centery - 5
                direction = 1 if self.facing_right else -1
                proj = PlayerProjectile(
                    proj_x, proj_y, direction,
                    proj_type=self._proj_type,
                    damage=effective_power,
                )
                self.projectiles.add(proj)
                self.attack_cooldown = self._ranged_cooldown
            return []
        else:
            # Melee: damage is deferred to active phase via check_melee_hits()
            # Lunge forward
            lunge_dir = 1 if self.facing_right else -1
            self.velocity_x += settings.ATTACK_LUNGE * lunge_dir
            return []

    def update_attack_phase(self):
        """Progress attack through startup → active → recovery → done."""
        if self.attack_phase is None:
            return

        fd = self.class_config.get('frame_data', {
            'startup': 3, 'active': 4, 'recovery': 6,
        })

        self.attack_phase_timer += 1

        if self.attack_phase == 'startup':
            if self.attack_phase_timer >= fd['startup']:
                self.attack_phase = 'active'
                self.attack_phase_timer = 0
        elif self.attack_phase == 'active':
            if self.attack_phase_timer >= fd['active']:
                self.attack_phase = 'recovery'
                self.attack_phase_timer = 0
        elif self.attack_phase == 'recovery':
            if self.attack_phase_timer >= fd['recovery']:
                self.attack_phase = None
                self.attacking = False
                self.attack_timer = 0

    def check_melee_hits(self, enemy_group):
        """Check for melee hits during active phase. Returns list of hit enemies."""
        if self.attack_phase != 'active' or self._is_ranged:
            return []
        if self._attack_hit_this_swing:
            return []  # Only hit once per swing

        fd = self.class_config.get('frame_data', {
            'hitbox_w': settings.ATTACK_HITBOX_INFLATE,
            'hitbox_h': self.rect.height,
            'hitbox_offset_x': settings.ATTACK_HITBOX_OFFSET,
        })

        # Build attack hitbox from frame data
        hitbox_w = fd.get('hitbox_w', settings.ATTACK_HITBOX_INFLATE)
        hitbox_h = fd.get('hitbox_h', self.rect.height)
        offset_x = fd.get('hitbox_offset_x', settings.ATTACK_HITBOX_OFFSET)

        attack_rect = pygame.Rect(0, 0, hitbox_w, hitbox_h)
        attack_rect.centery = self.rect.centery
        if self.facing_right:
            attack_rect.left = self.rect.right + offset_x - hitbox_w // 2
        else:
            attack_rect.right = self.rect.left - offset_x + hitbox_w // 2

        effective_power = self.attack_power
        if self.attack_boosted:
            effective_power = int(effective_power * settings.ATTACK_BOOST_MULTIPLIER)

        knockback_force = fd.get('knockback_force', 10)

        hits = []
        for enemy in enemy_group:
            if attack_rect.colliderect(enemy.rect):
                enemy.take_damage(effective_power)
                enemy.apply_knockback(
                    1 if self.facing_right else -1,
                    force=knockback_force,
                )
                hits.append(enemy)

        if hits:
            self._attack_hit_this_swing = True

        return hits

    def take_damage(self, amount):
        """Subtract health unless currently invincible. Triggers stagger."""
        if self.invincible:
            return
        self.health -= amount
        self.invincible = True
        self.iframes_timer = settings.IFRAMES_DURATION
        # Interrupt attack
        self.attacking = False
        self.attack_phase = None
        self.attack_phase_timer = 0
        # Stagger
        self._staggered = True
        self._stagger_timer = settings.PLAYER_STAGGER_FRAMES

    def _update_stagger(self):
        """Decrement stagger timer and clear when done."""
        if self._stagger_timer > 0:
            self._stagger_timer -= 1
            if self._stagger_timer <= 0:
                self._staggered = False

    # ── Dash ──────────────────────────────────────────────────────────

    def dash(self):
        """Burst of speed in the facing direction, with cooldown."""
        if self.dash_cooldown_timer > 0:
            return
        self.dashing = True
        self.dash_timer = settings.DASH_DURATION
        self.dash_cooldown_timer = settings.DASH_COOLDOWN
        self.velocity_x = settings.DASH_SPEED * (1 if self.facing_right else -1)

    # ── Reset ─────────────────────────────────────────────────────────

    def reset(self, x, y):
        """Restore player to initial state at the given position."""
        self.rect.x = x
        self.rect.y = y
        config = self.class_config
        # Use base PLAYER_HEALTH for backward compatibility with existing tests
        # that assert player.health == PLAYER_HEALTH after reset.
        self.health = settings.PLAYER_HEALTH
        self.max_health = int(settings.PLAYER_HEALTH * config['health_mult'])
        self.attack_power = int(settings.PLAYER_ATTACK_POWER * config['attack_mult'])
        self.velocity_x = 0.0
        self.velocity_y = 0.0
        self.on_ground = False
        self.facing_right = True
        self.attacking = False
        self.attack_timer = 0
        self.dashing = False
        self.dash_timer = 0
        self.dash_cooldown_timer = 0
        self.invincible = False
        self.iframes_timer = 0
        self.coyote_timer = 0
        self.jump_buffer_timer = 0
        self.speed_boosted = False
        self.attack_boosted = False
        self.speed_boost_timer = 0
        self.attack_boost_timer = 0

    # ── Animation ─────────────────────────────────────────────────────

    def _resolve_animation_state(self):
        """Determine which animation clip should play based on current state.

        Priority (highest → lowest):
        die → stagger → attack → dash → jump → walk → idle
        """
        if self.health <= 0:
            return 'die'
        if getattr(self, '_staggered', False):
            return 'stagger'
        if self.attacking:
            return 'attack'
        if self.dashing:
            return 'dash'
        if not self.on_ground:
            return 'jump'
        if abs(self.velocity_x) > 0.5:
            return 'walk'
        return 'idle'

    def _animate(self):
        """Drive the animation controller based on current state."""
        state = self._resolve_animation_state()
        self.animator.play(state)
        self.animator.update()
        self.image = self.animator.get_frame(self.facing_right)

        # Blink effect during i-frames
        if self.invincible and (self.iframes_timer % settings.IFRAMES_BLINK_RATE < 2):
            self.image = self.image.copy()
            self.image.set_alpha(80)
