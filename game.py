"""
Johnathorn: Quest of Riefel — Main Game Module
A 2D side-scrolling boss fight game built with Pygame.
"""
import pygame
import sys
import random
import math

from settings import (
    SCREEN_WIDTH, SCREEN_HEIGHT, FPS, TITLE, BLACK, WHITE, RED, GREEN,
    YELLOW, ORANGE, DARK_RED, HEALTH_GREEN, HEALTH_BG, IMAGES_DIR,
    CAMERA_LERP_SPEED, CAMERA_LEFT_MARGIN, GROUND_Y,
    ARENA_WIDTH, ARENA_LEFT_BOUND, ARENA_RIGHT_BOUND,
    SCALED, RESIZABLE, START_FULLSCREEN,
    PLAYER_START_X, PLAYER_START_Y, PLAYER_HEALTH, PLAYER_ATTACK_POWER,
    ATTACK_BOOST_MULTIPLIER,
    INITIAL_SPAWN_INTERVAL, SPAWN_INTERVAL_DECREASE, MIN_SPAWN_INTERVAL,
    ENEMIES_PER_WAVE_BASE, ENEMIES_PER_WAVE_INCREMENT, WAVE_PAUSE_DURATION,
    ENEMY_SPEED_INCREASE_PER_WAVE, ENEMY_ATTACK_DAMAGE,
    KILL_SCORE, COMBO_BONUS, COMBO_WINDOW,
    SCREEN_SHAKE_INTENSITY, PARTICLE_COUNT_DEATH, PARTICLE_COUNT_HIT,
    PARTICLE_COUNT_LAND,
    SOUNDS_DIR, CHARACTER_CLASSES, DEFAULT_CHARACTER_CLASS,
    MAX_WAVES_BEFORE_BOSS, BOSS_FIREBALL_DAMAGE, BOSS_HEALTH,
    ENEMY_SPRITE_SIZE, get_enemy_types_for_wave,
)
from Pygame.engine import initPygame, Background
from Character.mainCharacter import MainCharacter
from Enemy.enemy import Enemy
from Boss.dragon import Dragon
from Boss.fireball import Fireball
from Environment.platform import Platform, load_wave_platforms, load_boss_platforms
from powerUp import PowerUp, try_spawn_powerup
from effects import EffectsManager


class Game:
    """Main game class managing state, waves, scoring, and the game loop."""

    def __init__(self):
        # Core state
        self.state = "title"  # title | char_select | playing | boss | paused | game_over | victory
        self.score = 0
        self.wave = 1
        self.combo = 0
        self.combo_timer = 0
        self.kills = 0
        self.wave_pause_timer = 0
        self.enemies_remaining = 0
        self.enemies_spawned = 0

        # Character selection
        self.selected_class = DEFAULT_CHARACTER_CLASS
        self._class_keys = list(CHARACTER_CLASSES.keys())
        self._class_index = 0

        # Boss
        self.boss = None
        self.boss_intro_timer = 0
        self.victory_timer = 0

        # These are initialized when start_game() is called or during run()
        self.screen = None
        self.clock = None
        self.player = None
        self.background = None
        self.effects = EffectsManager()

        # Sprite groups
        self.all_sprites = pygame.sprite.Group()
        self.enemy_list = pygame.sprite.Group()
        self.platform_list = pygame.sprite.Group()
        self.powerup_list = pygame.sprite.Group()

        # Camera (world-space offset, NOT cumulative)
        self.camera_x = 0.0

        # Sounds (loaded lazily in run())
        self.sounds_loaded = False
        self._bgm_path = None
        self.sfx_sword_swing = None
        self.sfx_hit = None
        self.sfx_enemy_death = None
        self.sfx_player_hurt = None
        self.sfx_jump = None
        self.sfx_dash = None
        self.sfx_pickup = None
        self.sfx_arrow_fire = None
        self.sfx_magic_fire = None
        self.sfx_boss_roar = None
        self.sfx_fireball = None
        self.sfx_victory = None

        # Fonts
        self.font = None
        self.small_font = None
        self.combo_font = None
        self.title_font = None

        # Spawn timer event
        self.ENEMY_SPAWN = pygame.USEREVENT + 1

        # Wave announcement
        self.wave_announce_timer = 0
        self.wave_announce_text = ""

    # ── State transitions ──────────────────────────────────────────────

    def start_game(self):
        """Transition to playing state and reset everything."""
        self.state = "playing"
        self.score = 0
        self.wave = 1
        self.combo = 0
        self.combo_timer = 0
        self.kills = 0
        self.wave_pause_timer = 0
        self.enemies_spawned = 0
        self.boss = None

        # Create player with selected class
        if self.player:
            self.player.kill()
        self.player = MainCharacter(
            PLAYER_START_X, PLAYER_START_Y,
            character_class=self.selected_class,
        )
        self.all_sprites.add(self.player)

        # Clear enemies and powerups
        for e in self.enemy_list:
            e.kill()
        for p in self.powerup_list:
            p.kill()

        # Clear old platforms and load wave layout
        for p in self.platform_list:
            p.kill()
        self._load_platforms_for_wave(self.wave)

        # Setup wave
        self._start_wave()

        # Start spawn timer
        pygame.time.set_timer(self.ENEMY_SPAWN, self.get_spawn_interval())

        # Music — use pygame.mixer.music for BGM looping
        if self._bgm_path:
            try:
                pygame.mixer.music.load(self._bgm_path)
                pygame.mixer.music.set_volume(0.4)
                pygame.mixer.music.play(-1)
            except (pygame.error, FileNotFoundError):
                pass

    def game_over(self):
        """Transition to game over state."""
        self.state = "game_over"
        pygame.time.set_timer(self.ENEMY_SPAWN, 0)  # stop spawning
        pygame.mixer.music.stop()

    def toggle_pause(self):
        """Toggle between playing and paused."""
        if self.state == "playing":
            self.state = "paused"
        elif self.state == "paused":
            self.state = "playing"

    def _load_platforms_for_wave(self, wave_num):
        """Clear existing platforms and load the curated layout for a wave."""
        for p in list(self.platform_list):
            p.kill()
        for plat in load_wave_platforms(wave_num):
            self.all_sprites.add(plat)
            self.platform_list.add(plat)

    def _load_boss_platforms(self):
        """Clear existing platforms and load the boss arena layout."""
        for p in list(self.platform_list):
            p.kill()
        for plat in load_boss_platforms():
            self.all_sprites.add(plat)
            self.platform_list.add(plat)

    # ── Wave system ────────────────────────────────────────────────────

    def _start_wave(self):
        """Initialize a new wave."""
        self.enemies_remaining = (
            ENEMIES_PER_WAVE_BASE + (self.wave - 1) * ENEMIES_PER_WAVE_INCREMENT
        )
        self.enemies_spawned = 0
        pygame.time.set_timer(self.ENEMY_SPAWN, self.get_spawn_interval())
        self.wave_announce_timer = 90  # frames to display wave announcement
        self.wave_announce_text = f"WAVE {self.wave}"

    def get_spawn_interval(self):
        """Calculate spawn interval for current wave."""
        interval = INITIAL_SPAWN_INTERVAL - (self.wave - 1) * SPAWN_INTERVAL_DECREASE
        return max(interval, MIN_SPAWN_INTERVAL)

    def check_wave_complete(self):
        """Check if all enemies in the wave have been defeated."""
        if (self.enemies_remaining <= 0
                and len(self.enemy_list) == 0
                and self.enemies_spawned >= (
                    ENEMIES_PER_WAVE_BASE + (self.wave - 1) * ENEMIES_PER_WAVE_INCREMENT
                )):
            self.wave += 1
            pygame.time.set_timer(self.ENEMY_SPAWN, 0)  # pause spawning

            # Check if it's boss time
            if self.wave > MAX_WAVES_BEFORE_BOSS:
                self._start_boss()
            else:
                self.wave_pause_timer = WAVE_PAUSE_DURATION

    def _start_boss(self):
        """Transition to boss fight."""
        self.state = "boss"
        self.boss = Dragon()
        self.all_sprites.add(self.boss)
        self.boss_intro_timer = 120  # 2 seconds intro
        self.wave_announce_timer = 120
        self.wave_announce_text = "RIEFEL THE DRAGON"
        pygame.time.set_timer(self.ENEMY_SPAWN, 0)
        self._load_boss_platforms()
        if self.sfx_boss_roar:
            self.sfx_boss_roar.play()

    def _victory(self):
        """Player defeated the boss."""
        self.state = "victory"
        self.victory_timer = 0
        pygame.mixer.music.stop()
        if self.sfx_victory:
            self.sfx_victory.play()

    def _spawn_enemy(self):
        """Spawn a single enemy for the current wave."""
        total_for_wave = (
            ENEMIES_PER_WAVE_BASE + (self.wave - 1) * ENEMIES_PER_WAVE_INCREMENT
        )
        if self.enemies_spawned >= total_for_wave:
            return

        speed_mult = 1.0 + (self.wave - 1) * ENEMY_SPEED_INCREASE_PER_WAVE
        # Spawn from either edge of the arena for variety
        if random.random() < 0.5:
            spawn_x = random.randint(ARENA_WIDTH - 100, ARENA_WIDTH + 50)
        else:
            spawn_x = random.randint(-50, 0)
        # Select enemy type based on wave (progressive unlock)
        available_types = get_enemy_types_for_wave(self.wave)
        enemy_type = random.choice(available_types) if available_types else 'skeleton_warrior'
        new_enemy = Enemy(
            spawn_x,
            int(GROUND_Y - ENEMY_SPRITE_SIZE),
            speed_multiplier=speed_mult,
            enemy_type=enemy_type,
        )
        self.all_sprites.add(new_enemy)
        self.enemy_list.add(new_enemy)
        self.enemies_spawned += 1

    # ── Scoring & Combo ────────────────────────────────────────────────

    def on_enemy_killed(self):
        """Handle scoring when an enemy is killed."""
        self.kills += 1
        self.enemies_remaining -= 1

        # Combo logic
        if self.combo_timer > 0:
            self.combo += 1
        else:
            self.combo = 1

        self.combo_timer = COMBO_WINDOW

        # Score: base + combo bonus for streaks
        self.score += KILL_SCORE
        if self.combo > 1:
            self.score += COMBO_BONUS * (self.combo - 1)

    def update_combo(self):
        """Decrement combo timer each frame."""
        if self.combo_timer > 0:
            self.combo_timer -= 1
            if self.combo_timer <= 0:
                self.combo = 0

    # ── Sound loading ──────────────────────────────────────────────────

    def _load_sounds(self):
        """Load sound assets. Call once after pygame.mixer.init()."""
        if self.sounds_loaded:
            return

        sfx_dir = SOUNDS_DIR / "sfx"

        def _load_sfx(name):
            """Try loading a SFX .wav file, return Sound or None."""
            try:
                snd = pygame.mixer.Sound(str(sfx_dir / name))
                snd.set_volume(0.5)
                return snd
            except (FileNotFoundError, pygame.error):
                return None

        # SFX
        self.sfx_sword_swing = _load_sfx("sword_swing.wav")
        self.sfx_hit = _load_sfx("hit.wav")
        self.sfx_enemy_death = _load_sfx("enemy_death.wav")
        self.sfx_player_hurt = _load_sfx("player_hurt.wav")
        self.sfx_jump = _load_sfx("jump.wav")
        self.sfx_dash = _load_sfx("dash.wav")
        self.sfx_pickup = _load_sfx("pickup.wav")
        self.sfx_arrow_fire = _load_sfx("arrow_fire.wav")
        self.sfx_magic_fire = _load_sfx("magic_fire.wav")
        self.sfx_boss_roar = _load_sfx("boss_roar.wav")
        self.sfx_fireball = _load_sfx("fireball.wav")
        self.sfx_victory = _load_sfx("victory.wav")

        # BGM — use pygame.mixer.music for proper looping
        try:
            self._bgm_path = str(SOUNDS_DIR / "opening_sound.ogg")
            # We'll start music in start_game(), not here
        except Exception:
            self._bgm_path = None

        self.sounds_loaded = True

    # ── Drawing helpers ────────────────────────────────────────────────

    def _draw_health_bar(self, x, y, w, h, current, maximum, bg_color, fg_color):
        """Draw a health bar with background and foreground."""
        ratio = max(0, current / maximum)
        pygame.draw.rect(self.screen, bg_color, (x, y, w, h))
        pygame.draw.rect(self.screen, fg_color, (x, y, int(w * ratio), h))
        pygame.draw.rect(self.screen, WHITE, (x, y, w, h), 1)

    def _draw_hud(self):
        """Draw the player HUD: health, score, wave, combo."""
        # Health bar — use class-based max health
        self._draw_health_bar(
            10, 10, 200, 22,
            self.player.health, self.player.max_health,
            HEALTH_BG, HEALTH_GREEN,
        )
        hp_text = self.small_font.render(
            f"HP: {max(0, int(self.player.health))}/{int(self.player.max_health)}", True, WHITE
        )
        self.screen.blit(hp_text, (15, 12))

        # Score
        score_text = self.small_font.render(f"Score: {self.score}", True, YELLOW)
        self.screen.blit(score_text, (SCREEN_WIDTH - score_text.get_width() - 10, 10))

        # Wave
        wave_text = self.small_font.render(f"Wave: {self.wave}", True, WHITE)
        self.screen.blit(wave_text, (SCREEN_WIDTH - wave_text.get_width() - 10, 35))

        # Combo
        if self.combo > 1:
            combo_color = ORANGE if self.combo < 5 else RED
            combo_text = self.combo_font.render(
                f"{self.combo}x COMBO!", True, combo_color
            )
            # Pulse effect
            scale = 1.0 + (self.combo_timer / COMBO_WINDOW) * 0.3
            scaled = pygame.transform.scale(
                combo_text,
                (int(combo_text.get_width() * scale),
                 int(combo_text.get_height() * scale)),
            )
            self.screen.blit(
                scaled,
                (SCREEN_WIDTH // 2 - scaled.get_width() // 2, 50),
            )

        # Enemy health bars (world-space → screen-space with camera offset)
        cam = int(self.camera_x)
        for e in self.enemy_list:
            # Only show health bar when enemy has taken damage
            if e.health >= e.max_health:
                continue
            bar_w = 40
            bar_h = 3
            bar_x = e.rect.x - cam + (e.rect.width - bar_w) // 2
            bar_y = e.rect.y - 6
            self._draw_health_bar(
                bar_x, bar_y,
                bar_w, bar_h,
                e.health, e.max_health,
                DARK_RED, RED,
            )

        # Active buffs
        buff_y = 40
        if self.player.speed_boosted:
            buff_text = self.small_font.render(">> SPEED", True, (100, 200, 255))
            self.screen.blit(buff_text, (10, buff_y))
            buff_y += 22
        if self.player.attack_boosted:
            buff_text = self.small_font.render("** POWER", True, (255, 100, 100))
            self.screen.blit(buff_text, (10, buff_y))

    def _draw_title_screen(self):
        """Draw the title / start screen."""
        # Background image
        if self._title_bg:
            self.screen.blit(self._title_bg, (0, 0))
            # Darken overlay for readability
            overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
            overlay.fill((0, 0, 0, 140))
            self.screen.blit(overlay, (0, 0))
        else:
            self.screen.fill((15, 15, 30))

        # Title
        title_text = self.title_font.render("JOHNATHORN", True, (220, 180, 60))
        self.screen.blit(
            title_text,
            (SCREEN_WIDTH // 2 - title_text.get_width() // 2, 150),
        )

        # Subtitle
        sub_text = self.font.render("Quest of Riefel", True, (150, 150, 180))
        self.screen.blit(
            sub_text,
            (SCREEN_WIDTH // 2 - sub_text.get_width() // 2, 220),
        )

        # Controls
        controls = [
            "A / D : Move",
            "W / SPACE : Jump",
            "S : Attack",
            "SHIFT : Dash",
            "ESC : Pause",
        ]
        start_y = 320
        for i, line in enumerate(controls):
            ctrl_text = self.small_font.render(line, True, (180, 180, 200))
            self.screen.blit(
                ctrl_text,
                (SCREEN_WIDTH // 2 - ctrl_text.get_width() // 2, start_y + i * 30),
            )

        # Start prompt (blink)
        if (pygame.time.get_ticks() // 500) % 2 == 0:
            start_text = self.font.render("Press ENTER to Start", True, YELLOW)
            self.screen.blit(
                start_text,
                (SCREEN_WIDTH // 2 - start_text.get_width() // 2, 500),
            )

    def _draw_game_over_screen(self):
        """Draw the game over screen with stats."""
        if self._gameover_bg:
            self.screen.blit(self._gameover_bg, (0, 0))
            overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
            overlay.fill((0, 0, 0, 160))
            self.screen.blit(overlay, (0, 0))
        else:
            self.screen.fill((30, 10, 10))

        go_text = self.title_font.render("GAME OVER", True, RED)
        self.screen.blit(
            go_text,
            (SCREEN_WIDTH // 2 - go_text.get_width() // 2, 150),
        )

        stats = [
            f"Score: {self.score}",
            f"Wave Reached: {self.wave}",
            f"Enemies Defeated: {self.kills}",
        ]
        for i, line in enumerate(stats):
            stat_text = self.font.render(line, True, WHITE)
            self.screen.blit(
                stat_text,
                (SCREEN_WIDTH // 2 - stat_text.get_width() // 2, 260 + i * 45),
            )

        if (pygame.time.get_ticks() // 500) % 2 == 0:
            restart_text = self.small_font.render("Press R to Restart", True, YELLOW)
            self.screen.blit(
                restart_text,
                (SCREEN_WIDTH // 2 - restart_text.get_width() // 2, 450),
            )

    def _draw_pause_screen(self):
        """Draw pause overlay."""
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 128))
        self.screen.blit(overlay, (0, 0))

        pause_text = self.title_font.render("PAUSED", True, WHITE)
        self.screen.blit(
            pause_text,
            (SCREEN_WIDTH // 2 - pause_text.get_width() // 2,
             SCREEN_HEIGHT // 2 - pause_text.get_height() // 2),
        )

    def _draw_wave_announcement(self):
        """Draw wave announcement text."""
        if self.wave_announce_timer > 0:
            alpha = min(255, self.wave_announce_timer * 6)
            announce = self.title_font.render(self.wave_announce_text, True, YELLOW)
            # Center on screen
            self.screen.blit(
                announce,
                (SCREEN_WIDTH // 2 - announce.get_width() // 2,
                 SCREEN_HEIGHT // 2 - announce.get_height() // 2 - 50),
            )

    # ── Main game loop ─────────────────────────────────────────────────

    def run(self):
        """Initialize display and run the main game loop."""
        pygame.init()
        pygame.mixer.init()

        self.screen = initPygame(
            SCREEN_WIDTH, SCREEN_HEIGHT, TITLE,
            scaled=SCALED, resizable=RESIZABLE, fullscreen=START_FULLSCREEN,
        )
        self.clock = pygame.time.Clock()

        # Fonts
        self.font = pygame.font.SysFont("Arial", 32)
        self.small_font = pygame.font.SysFont("Arial", 20)
        self.combo_font = pygame.font.SysFont("Arial", 28, bold=True)
        self.title_font = pygame.font.SysFont("Arial", 56, bold=True)

        # Screen images — try new generated art first, fall back to originals
        try:
            raw = pygame.image.load(str(IMAGES_DIR / 'title_bg.png')).convert()
            self._title_bg = pygame.transform.scale(raw, (SCREEN_WIDTH, SCREEN_HEIGHT))
        except (pygame.error, FileNotFoundError):
            try:
                raw = pygame.image.load(str(IMAGES_DIR / 'JOHNATHORN.png')).convert()
                self._title_bg = pygame.transform.scale(raw, (SCREEN_WIDTH, SCREEN_HEIGHT))
            except (pygame.error, FileNotFoundError):
                self._title_bg = None
        try:
            raw = pygame.image.load(str(IMAGES_DIR / 'END_SCREEN.png')).convert()
            self._gameover_bg = pygame.transform.scale(raw, (SCREEN_WIDTH, SCREEN_HEIGHT))
        except (pygame.error, FileNotFoundError):
            self._gameover_bg = None

        # Load sounds
        self._load_sounds()

        # Create game objects
        self.player = MainCharacter(PLAYER_START_X, PLAYER_START_Y)
        self.background = Background()

        # Initial platforms (wave 1 layout)
        self.all_sprites.add(self.player)
        self._load_platforms_for_wave(1)

        # Game loop
        running = True
        while running:
            dt = self.clock.tick(FPS)

            # ── Event handling ──
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False

                if event.type == pygame.KEYDOWN:
                    # F11 fullscreen toggle (works in all states)
                    if event.key == pygame.K_F11:
                        pygame.display.toggle_fullscreen()
                    if self.state == "title":
                        if event.key == pygame.K_RETURN:
                            self.state = "char_select"

                    elif self.state == "char_select":
                        if event.key in (pygame.K_LEFT, pygame.K_a):
                            self._class_index = (self._class_index - 1) % len(self._class_keys)
                            self.selected_class = self._class_keys[self._class_index]
                        elif event.key in (pygame.K_RIGHT, pygame.K_d):
                            self._class_index = (self._class_index + 1) % len(self._class_keys)
                            self.selected_class = self._class_keys[self._class_index]
                        elif event.key == pygame.K_RETURN:
                            self.start_game()

                    elif self.state in ("playing", "boss"):
                        if event.key in (pygame.K_w, pygame.K_SPACE):
                            self.player.jump()
                        elif event.key == pygame.K_s:
                            self._handle_attack()
                        elif event.key in (pygame.K_LSHIFT, pygame.K_RSHIFT):
                            self.player.dash()
                        elif event.key == pygame.K_ESCAPE:
                            self.toggle_pause()

                    elif self.state == "paused":
                        if event.key == pygame.K_ESCAPE:
                            self.toggle_pause()

                    elif self.state == "game_over":
                        if event.key == pygame.K_r:
                            self.start_game()

                    elif self.state == "victory":
                        if event.key == pygame.K_RETURN:
                            self.state = "title"

                if event.type == pygame.KEYUP:
                    if event.key in (pygame.K_w, pygame.K_SPACE) and self.state in ("playing", "boss"):
                        self.player.release_jump()

                if event.type == self.ENEMY_SPAWN and self.state == "playing":
                    self._spawn_enemy()

            # ── Update ──
            if self.state == "playing" and not self.effects.is_paused:
                # Player input
                keys = pygame.key.get_pressed()
                if keys[pygame.K_LEFT] or keys[pygame.K_a]:
                    self.player.move(-1)
                if keys[pygame.K_RIGHT] or keys[pygame.K_d]:
                    self.player.move(1)

                # Camera (smooth lerp toward player in world-space)
                target_cam = self.player.rect.centerx - CAMERA_LEFT_MARGIN
                # Clamp camera to arena bounds
                target_cam = max(0, min(target_cam, ARENA_WIDTH - SCREEN_WIDTH))
                self.camera_x += (target_cam - self.camera_x) * CAMERA_LERP_SPEED

                # Player horizontal clamping (world-space)
                if self.player.rect.left < ARENA_LEFT_BOUND:
                    self.player.rect.left = ARENA_LEFT_BOUND
                if self.player.rect.right > ARENA_RIGHT_BOUND:
                    self.player.rect.right = ARENA_RIGHT_BOUND

                # Update sprites
                self.player.update(self.platform_list)
                self.enemy_list.update(player_rect=self.player.rect)
                self.platform_list.update()

                # Powerup update & collection
                self.powerup_list.update()
                for pu in pygame.sprite.spritecollide(self.player, self.powerup_list, False):
                    pu.apply(self.player)
                    if self.sfx_pickup:
                        self.sfx_pickup.play()

                # Enemy damage to player (only during enemy active attack phase)
                if not self.player.invincible:
                    for e in self.enemy_list:
                        if e.in_active_attack and pygame.sprite.collide_rect(self.player, e):
                            damage = int(ENEMY_ATTACK_DAMAGE * getattr(e, '_damage_mult', 1.0))
                            self.player.take_damage(damage)
                            if self.sfx_player_hurt:
                                self.sfx_player_hurt.play()
                            self.effects.screen_shake()
                            self.effects.spawn_particles(
                                self.player.rect.centerx,
                                self.player.rect.centery,
                                RED, PARTICLE_COUNT_HIT,
                            )
                            if self.player.health <= 0:
                                self.game_over()
                            break

                # Player melee hit check (active phase only)
                melee_hits = self.player.check_melee_hits(self.enemy_list)
                if melee_hits:
                    if self.sfx_hit:
                        self.sfx_hit.play()
                    self.effects.hit_pause()
                    self.effects.screen_shake(SCREEN_SHAKE_INTENSITY // 2)
                    for enemy in melee_hits:
                        self.effects.spawn_particles(
                            enemy.rect.centerx, enemy.rect.centery,
                            WHITE, PARTICLE_COUNT_HIT,
                        )
                        self.effects.spawn_damage_number(
                            enemy.rect.centerx, enemy.rect.top,
                            self.player.attack_power if not self.player.attack_boosted
                            else int(self.player.attack_power * ATTACK_BOOST_MULTIPLIER),
                        )

                # Player projectile → enemy collisions
                for proj in list(self.player.projectiles):
                    for e in list(self.enemy_list):
                        if proj.rect.colliderect(e.rect):
                            e.take_damage(proj.damage)
                            self.effects.spawn_particles(
                                e.rect.centerx, e.rect.centery,
                                WHITE, PARTICLE_COUNT_HIT,
                            )
                            self.effects.spawn_damage_number(
                                e.rect.centerx, e.rect.top, proj.damage,
                            )
                            e.apply_knockback(1 if proj.direction > 0 else -1)
                            proj.kill()
                            break

                # Check enemy deaths
                for e in list(self.enemy_list):
                    if e.health <= 0:
                        # Death effects
                        self.effects.screen_shake(SCREEN_SHAKE_INTENSITY)
                        self.effects.spawn_particles(
                            e.rect.centerx, e.rect.centery,
                            RED, PARTICLE_COUNT_DEATH,
                        )
                        if self.sfx_enemy_death:
                            self.sfx_enemy_death.play()

                        # Score
                        self.on_enemy_killed()

                        # Power-up drop
                        pu = try_spawn_powerup(e.rect.centerx, e.rect.centery)
                        if pu:
                            self.all_sprites.add(pu)
                            self.powerup_list.add(pu)

                        e.kill()

                # Combo timer
                self.update_combo()

                # Wave management
                if self.wave_pause_timer > 0:
                    self.wave_pause_timer -= 1
                    if self.wave_pause_timer <= 0:
                        self._load_platforms_for_wave(self.wave)
                        self._start_wave()
                else:
                    self.check_wave_complete()

                # Wave announcement timer
                if self.wave_announce_timer > 0:
                    self.wave_announce_timer -= 1



            # ── Boss update ──
            if self.state == "boss" and not self.effects.is_paused:
                keys = pygame.key.get_pressed()
                if keys[pygame.K_LEFT] or keys[pygame.K_a]:
                    self.player.move(-1)
                if keys[pygame.K_RIGHT] or keys[pygame.K_d]:
                    self.player.move(1)

                # Camera stays fixed during boss fight (centered on arena)
                boss_cam = max(0, (ARENA_WIDTH - SCREEN_WIDTH) / 2)
                self.camera_x += (boss_cam - self.camera_x) * CAMERA_LERP_SPEED

                # Player horizontal clamping
                if self.player.rect.left < ARENA_LEFT_BOUND:
                    self.player.rect.left = ARENA_LEFT_BOUND
                if self.player.rect.right > ARENA_RIGHT_BOUND:
                    self.player.rect.right = ARENA_RIGHT_BOUND

                self.player.update(self.platform_list)
                self.platform_list.update()

                # Boss intro countdown
                if self.boss_intro_timer > 0:
                    self.boss_intro_timer -= 1
                else:
                    self.boss.update(self.player.rect)

                # Boss fireball collisions with player
                if not self.player.invincible:
                    for fb in self.boss.fireballs:
                        if pygame.sprite.collide_rect(self.player, fb):
                            self.player.take_damage(fb.damage)
                            self.effects.screen_shake(SCREEN_SHAKE_INTENSITY)
                            self.effects.spawn_particles(
                                self.player.rect.centerx, self.player.rect.centery,
                                ORANGE, PARTICLE_COUNT_HIT,
                            )
                            fb.kill()
                            if self.player.health <= 0:
                                self.game_over()
                            break

                # Boss breath/slam damage to player
                if not self.player.invincible and self.boss:
                    dmg_info = self.boss.get_damage_rect()
                    if dmg_info:
                        dmg_rect, dmg_amount = dmg_info
                        if self.player.rect.colliderect(dmg_rect):
                            self.player.take_damage(dmg_amount)
                            self.effects.screen_shake(SCREEN_SHAKE_INTENSITY)
                            self.effects.spawn_particles(
                                self.player.rect.centerx, self.player.rect.centery,
                                ORANGE, PARTICLE_COUNT_HIT,
                            )
                            if self.player.health <= 0:
                                self.game_over()

                # Player projectiles → boss
                if self.boss and self.boss.state not in ('dying', 'dead'):
                    for proj in list(self.player.projectiles):
                        if proj.rect.colliderect(self.boss.rect):
                            self.boss.take_damage(proj.damage)
                            self.effects.spawn_particles(
                                self.boss.rect.centerx, self.boss.rect.centery,
                                ORANGE, PARTICLE_COUNT_HIT,
                            )
                            self.effects.spawn_damage_number(
                                self.boss.rect.centerx, self.boss.rect.top, proj.damage,
                            )
                            proj.kill()

                # Check boss death
                if self.boss and self.boss.state == 'dead':
                    self.effects.screen_shake(SCREEN_SHAKE_INTENSITY * 3)
                    self.effects.spawn_particles(
                        self.boss.rect.centerx, self.boss.rect.centery,
                        ORANGE, PARTICLE_COUNT_DEATH * 3,
                    )
                    self.score += 5000  # Boss kill bonus
                    self.boss.kill()
                    self._victory()

                # Powerup update & collection
                self.powerup_list.update()
                for pu in pygame.sprite.spritecollide(self.player, self.powerup_list, False):
                    pu.apply(self.player)
                    if self.sfx_pickup:
                        self.sfx_pickup.play()

                self.update_combo()
                if self.wave_announce_timer > 0:
                    self.wave_announce_timer -= 1

            # Effects always update (including during pause for visual continuity)
            self.effects.update()

            # ── Draw ──
            if self.state == "title":
                self._draw_title_screen()

            elif self.state == "char_select":
                self._draw_char_select()

            elif self.state in ("playing", "boss", "paused"):
                self.screen.fill(BLACK)
                shake = self.effects.get_shake_offset()
                cam = int(self.camera_x)

                # Background (parallax via camera offset)
                self.background.draw(self.screen, cam + shake[0])

                # Ground (extends full arena width, offset by camera)
                ground_y = int(GROUND_Y + shake[1])
                pygame.draw.rect(self.screen, (45, 30, 15),
                                 (-cam + shake[0], ground_y,
                                  ARENA_WIDTH, SCREEN_HEIGHT - ground_y))
                pygame.draw.rect(self.screen, (35, 100, 30),
                                 (-cam + shake[0], ground_y, ARENA_WIDTH, 6))

                # Platforms
                for p in self.platform_list:
                    self.screen.blit(
                        p.image,
                        (p.rect.x - cam + shake[0], p.rect.y + shake[1]),
                    )

                # Enemies
                for e in self.enemy_list:
                    self.screen.blit(
                        e.image,
                        (e.rect.x - cam + shake[0], e.rect.y + shake[1]),
                    )

                # Boss
                if self.boss and self.boss.state != 'dead':
                    self.screen.blit(
                        self.boss.image,
                        (self.boss.rect.x - cam + shake[0], self.boss.rect.y + shake[1]),
                    )
                    # Draw fireballs
                    for fb in self.boss.fireballs:
                        self.screen.blit(
                            fb.image,
                            (fb.rect.x - cam + shake[0], fb.rect.y + shake[1]),
                        )
                    # Draw breath visual
                    if self.boss.state == 'breathing' and self.boss.breath_rect:
                        breath_surf = pygame.Surface(
                            (self.boss.breath_rect.width, self.boss.breath_rect.height),
                            pygame.SRCALPHA,
                        )
                        breath_surf.fill((255, 120, 0, 100))
                        self.screen.blit(breath_surf, (
                            self.boss.breath_rect.x - cam + shake[0],
                            self.boss.breath_rect.y + shake[1],
                        ))

                # Power-ups
                for pu in self.powerup_list:
                    self.screen.blit(
                        pu.image,
                        (pu.rect.x - cam + shake[0], pu.rect.y + shake[1]),
                    )

                # Player (blink during i-frames)
                if not self.player.invincible or (
                    self.player.iframes_timer % 4 < 2
                ):
                    self.screen.blit(
                        self.player.image,
                        (self.player.rect.x - cam + shake[0],
                         self.player.rect.y + shake[1]),
                    )

                # Player projectiles
                for proj in self.player.projectiles:
                    proj.draw(self.screen, offset=shake)

                # Effects overlay
                self.effects.draw(self.screen, camera_offset=shake)

                # HUD (not affected by shake)
                self._draw_hud()

                # Boss HUD
                if self.state == "boss" and self.boss:
                    self._draw_boss_hud()

                # Wave announcement
                self._draw_wave_announcement()

                # Pause overlay
                if self.state == "paused":
                    self._draw_pause_screen()

            elif self.state == "game_over":
                self._draw_game_over_screen()

            elif self.state == "victory":
                self._draw_victory_screen()

            pygame.display.flip()

        pygame.quit()
        sys.exit()

    # ── Attack handler (shared between playing & boss states) ──────────

    def _handle_attack(self):
        """Handle attack input — initiates attack (hits resolved per-frame via check_melee_hits)."""
        self.player.attack(self.enemy_list)

        # Play class-appropriate attack SFX
        if self.player._is_ranged:
            sfx = self.sfx_arrow_fire if self.player._proj_type == 'arrow' else self.sfx_magic_fire
            if sfx and self.player.attack_cooldown == self.player._ranged_cooldown:
                sfx.play()
        else:
            if self.sfx_sword_swing:
                self.sfx_sword_swing.play()

        # Boss melee hit (still immediate for boss since boss has no attack phases yet)
        if self.state == "boss" and self.boss and self.boss.state not in ('dying', 'dead'):
            if self.player.attack_phase == 'active' and not self.player._is_ranged:
                fd = self.player.class_config.get('frame_data', {})
                hitbox_w = fd.get('hitbox_w', 30)
                hitbox_offset = fd.get('hitbox_offset_x', 25)
                attack_rect = pygame.Rect(0, 0, hitbox_w, self.player.rect.height)
                attack_rect.centery = self.player.rect.centery
                if self.player.facing_right:
                    attack_rect.left = self.player.rect.right + hitbox_offset - hitbox_w // 2
                else:
                    attack_rect.right = self.player.rect.left - hitbox_offset + hitbox_w // 2
                if attack_rect.colliderect(self.boss.rect) and self.player.attacking:
                    dmg = self.player.attack_power
                    if self.player.attack_boosted:
                        dmg = int(dmg * ATTACK_BOOST_MULTIPLIER)
                    self.boss.take_damage(dmg)
                    self.effects.hit_pause()
                    self.effects.screen_shake(SCREEN_SHAKE_INTENSITY)
                    self.effects.spawn_particles(
                        self.boss.rect.centerx, self.boss.rect.centery,
                        ORANGE, PARTICLE_COUNT_HIT,
                    )
                    self.effects.spawn_damage_number(
                        self.boss.rect.centerx, self.boss.rect.top, dmg,
                    )


    # ── Character select drawing ───────────────────────────────────────

    def _draw_char_select(self):
        """Draw the character selection screen."""
        self.screen.fill((15, 15, 30))

        title = self.title_font.render("Choose Your Hero", True, (220, 180, 60))
        self.screen.blit(title, (SCREEN_WIDTH // 2 - title.get_width() // 2, 40))

        card_w, card_h = 170, 300
        total_w = len(self._class_keys) * card_w + (len(self._class_keys) - 1) * 16
        start_x = (SCREEN_WIDTH - total_w) // 2

        for i, cls_key in enumerate(self._class_keys):
            cfg = CHARACTER_CLASSES[cls_key]
            x = start_x + i * (card_w + 16)
            y = 120
            selected = (i == self._class_index)

            # Card background
            color = cfg['color']
            border_color = YELLOW if selected else (80, 80, 80)
            border_width = 3 if selected else 1

            card_surf = pygame.Surface((card_w, card_h), pygame.SRCALPHA)
            card_surf.fill((*color, 40))
            self.screen.blit(card_surf, (x, y))
            pygame.draw.rect(self.screen, border_color, (x, y, card_w, card_h), border_width)

            # Class name
            name_text = self.font.render(cfg['display_name'], True, WHITE if selected else (150, 150, 150))
            self.screen.blit(name_text, (x + card_w // 2 - name_text.get_width() // 2, y + 10))

            # Class preview sprite — use generated idle frame
            sprite_map = {
                'warrior': 'warrior/generated/idle/0.png',
                'mage': 'mage/generated/idle/0.png',
                'archer': 'archer/generated/idle/0.png',
                'druid': 'druid/generated/idle/0.png',
            }
            sprite_path = IMAGES_DIR / sprite_map.get(cls_key, '')
            try:
                if not hasattr(self, '_class_sprites'):
                    self._class_sprites = {}
                if cls_key not in self._class_sprites:
                    raw = pygame.image.load(str(sprite_path)).convert_alpha()
                    self._class_sprites[cls_key] = pygame.transform.scale(raw, (80, 80))
                preview = self._class_sprites[cls_key]
                self.screen.blit(preview, (x + card_w // 2 - 40, y + 48))
            except (pygame.error, FileNotFoundError):
                pass  # No preview available

            # Stats — use ASCII-safe characters
            spd_val = max(1, int(cfg['speed_mult'] * 3))
            stats = [
                f"HP: {int(PLAYER_HEALTH * cfg['health_mult'])}",
                f"ATK: {int(PLAYER_ATTACK_POWER * cfg['attack_mult'])}",
                f"SPD: {'|' * spd_val}{'.' * (4 - spd_val)}",
            ]
            if cfg.get('regen_rate', 0) > 0:
                stats.append("REGEN: YES")

            for j, stat in enumerate(stats):
                stat_text = self.small_font.render(stat, True, (200, 200, 200))
                self.screen.blit(stat_text, (x + 15, y + 140 + j * 28))

            # Description — clip to card width
            desc = cfg['description']
            desc_text = self.small_font.render(desc, True, (160, 160, 180))
            # Truncate if wider than card
            if desc_text.get_width() > card_w - 10:
                # Render clipped
                clip_surf = pygame.Surface((card_w - 10, desc_text.get_height()), pygame.SRCALPHA)
                clip_surf.blit(desc_text, (0, 0))
                desc_text = clip_surf
            self.screen.blit(desc_text, (x + card_w // 2 - desc_text.get_width() // 2, y + card_h - 40))

            # Selection indicator
            if selected:
                arrow = self.font.render("v", True, YELLOW)
                self.screen.blit(arrow, (x + card_w // 2 - arrow.get_width() // 2, y - 30))

        # Instructions — ASCII-safe
        hint = self.small_font.render("< >  Select  |  ENTER  Confirm", True, (120, 120, 150))
        self.screen.blit(hint, (SCREEN_WIDTH // 2 - hint.get_width() // 2, SCREEN_HEIGHT - 50))

    # ── Boss HUD ───────────────────────────────────────────────────────

    def _draw_boss_hud(self):
        """Draw boss health bar at top of screen."""
        if not self.boss:
            return
        bar_w = SCREEN_WIDTH - 100
        bar_h = 16
        x = 50
        y = 20

        # Label
        label = self.font.render("RIEFEL THE DRAGON", True, (255, 100, 50))
        self.screen.blit(label, (SCREEN_WIDTH // 2 - label.get_width() // 2, y - 2))

        y += 30
        self._draw_health_bar(x, y, bar_w, bar_h,
                              self.boss.health, self.boss.max_health,
                              (60, 20, 20), (220, 50, 20))

        # Phase indicator
        phase_text = self.small_font.render(f"Phase {self.boss.phase}", True, ORANGE)
        self.screen.blit(phase_text, (SCREEN_WIDTH - 120, y + 20))

    # ── Victory screen ─────────────────────────────────────────────────

    def _draw_victory_screen(self):
        """Draw the victory screen."""
        self.victory_timer += 1
        self.screen.fill((10, 20, 40))

        # Pulsing gold title
        pulse = 1.0 + 0.1 * math.sin(self.victory_timer * 0.05)
        vic_text = self.title_font.render("VICTORY!", True, (255, 215, 0))
        scaled = pygame.transform.scale(
            vic_text,
            (int(vic_text.get_width() * pulse), int(vic_text.get_height() * pulse)),
        )
        self.screen.blit(scaled, (SCREEN_WIDTH // 2 - scaled.get_width() // 2, 100))

        subtitle = self.font.render("Riefel the Dragon has been slain!", True, (200, 180, 100))
        self.screen.blit(subtitle, (SCREEN_WIDTH // 2 - subtitle.get_width() // 2, 200))

        stats = [
            f"Final Score: {self.score}",
            f"Enemies Defeated: {self.kills}",
            f"Class: {CHARACTER_CLASSES[self.selected_class]['display_name']}",
        ]
        for i, line in enumerate(stats):
            t = self.font.render(line, True, WHITE)
            self.screen.blit(t, (SCREEN_WIDTH // 2 - t.get_width() // 2, 280 + i * 45))

        if (pygame.time.get_ticks() // 500) % 2 == 0:
            hint = self.small_font.render("Press ENTER to return", True, YELLOW)
            self.screen.blit(hint, (SCREEN_WIDTH // 2 - hint.get_width() // 2, 480))


if __name__ == "__main__":
    game = Game()
    game.run()
