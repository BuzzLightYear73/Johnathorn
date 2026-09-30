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
    SCROLL_SPEED, CAMERA_LERP_SPEED, GROUND_Y,
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
    ENEMY_SPRITE_SIZE,
)
from Pygame.engine import initPygame, Background
from Character.mainCharacter import MainCharacter
from Enemy.enemy import Enemy
from Boss.dragon import Dragon
from Boss.fireball import Fireball
from Environment.platform import Platform, generate_platform
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

        # Scroll / camera
        self.scroll = 0
        self.target_scroll = 0

        # Sounds (loaded lazily in run())
        self.sounds_loaded = False
        self.bg_music = None
        self.sword_swing = None
        self.sword_hit = None
        self.enemy_death = None
        self.game_over_sound = None

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

        # Setup wave
        self._start_wave()

        # Start spawn timer
        pygame.time.set_timer(self.ENEMY_SPAWN, self.get_spawn_interval())

        # Music
        if self.bg_music:
            self.bg_music.play(-1)

    def game_over(self):
        """Transition to game over state."""
        self.state = "game_over"
        pygame.time.set_timer(self.ENEMY_SPAWN, 0)  # stop spawning
        if self.bg_music:
            self.bg_music.stop()
        if self.game_over_sound:
            self.game_over_sound.play()

    def toggle_pause(self):
        """Toggle between playing and paused."""
        if self.state == "playing":
            self.state = "paused"
        elif self.state == "paused":
            self.state = "playing"

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

    def _victory(self):
        """Player defeated the boss."""
        self.state = "victory"
        self.victory_timer = 0
        if self.bg_music:
            self.bg_music.stop()

    def _spawn_enemy(self):
        """Spawn a single enemy for the current wave."""
        total_for_wave = (
            ENEMIES_PER_WAVE_BASE + (self.wave - 1) * ENEMIES_PER_WAVE_INCREMENT
        )
        if self.enemies_spawned >= total_for_wave:
            return

        speed_mult = 1.0 + (self.wave - 1) * ENEMY_SPEED_INCREASE_PER_WAVE
        new_enemy = Enemy(
            random.randint(SCREEN_WIDTH, SCREEN_WIDTH + 400),
            int(GROUND_Y - ENEMY_SPRITE_SIZE),
            speed_multiplier=speed_mult,
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
        try:
            # Only opening_sound.ogg is actual BGM; sound.ogg/sound1/sound2 are
            # full music tracks from the original project, not SFX.
            self.bg_music = pygame.mixer.Sound(str(SOUNDS_DIR / "opening_sound.ogg"))
            self.bg_music.set_volume(0.4)
            self.sounds_loaded = True
        except (FileNotFoundError, pygame.error):
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

        # Enemy health bars
        for e in self.enemy_list:
            bar_w = 50
            bar_h = 4
            from settings import ENEMY_BASE_HEALTH
            self._draw_health_bar(
                e.rect.x + (e.rect.width - bar_w) // 2,
                e.rect.y - 8,
                bar_w, bar_h,
                e.health, ENEMY_BASE_HEALTH,
                DARK_RED, RED,
            )

        # Active buffs
        buff_y = 40
        if self.player.speed_boosted:
            buff_text = self.small_font.render("⚡ SPEED", True, (100, 200, 255))
            self.screen.blit(buff_text, (10, buff_y))
            buff_y += 22
        if self.player.attack_boosted:
            buff_text = self.small_font.render("⚔ POWER", True, (255, 100, 100))
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

        self.screen = initPygame(SCREEN_WIDTH, SCREEN_HEIGHT, TITLE)
        self.clock = pygame.time.Clock()

        # Fonts
        self.font = pygame.font.SysFont("Arial", 32)
        self.small_font = pygame.font.SysFont("Arial", 20)
        self.combo_font = pygame.font.SysFont("Arial", 28, bold=True)
        self.title_font = pygame.font.SysFont("Arial", 56, bold=True)

        # Screen images
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

        # Initial platforms
        self.all_sprites.add(self.player)
        for px, py in [(300, 450), (550, 370), (200, 280), (700, 300)]:
            plat = Platform(px, py)
            self.all_sprites.add(plat)
            self.platform_list.add(plat)

        # Game loop
        running = True
        while running:
            dt = self.clock.tick(FPS)

            # ── Event handling ──
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False

                if event.type == pygame.KEYDOWN:
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

                # Camera scroll (smooth lerp toward player offset)
                target = -(self.player.rect.x - SCREEN_WIDTH // 3)
                self.scroll += (target - self.scroll) * CAMERA_LERP_SPEED

                # Update sprites
                self.player.update(self.platform_list)
                self.enemy_list.update(player_rect=self.player.rect)
                self.platform_list.update(self.scroll * 0.1)

                # Powerup update & collection
                self.powerup_list.update()
                for pu in pygame.sprite.spritecollide(self.player, self.powerup_list, False):
                    pu.apply(self.player)

                # Enemy damage to player
                if not self.player.invincible:
                    for e in self.enemy_list:
                        if pygame.sprite.collide_rect(self.player, e):
                            self.player.take_damage(ENEMY_ATTACK_DAMAGE)
                            self.effects.screen_shake()
                            self.effects.spawn_particles(
                                self.player.rect.centerx,
                                self.player.rect.centery,
                                RED, PARTICLE_COUNT_HIT,
                            )
                            if self.player.health <= 0:
                                self.game_over()
                            break

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
                        self._start_wave()
                else:
                    self.check_wave_complete()

                # Wave announcement timer
                if self.wave_announce_timer > 0:
                    self.wave_announce_timer -= 1

                # Procedural platform generation
                rightmost = max(
                    (p.rect.right for p in self.platform_list),
                    default=0,
                )
                if rightmost < SCREEN_WIDTH + 200:
                    new_plat = generate_platform(SCREEN_WIDTH)
                    self.all_sprites.add(new_plat)
                    self.platform_list.add(new_plat)

                # Remove off-screen platforms
                for p in list(self.platform_list):
                    if p.rect.right < -100:
                        p.kill()

            # ── Boss update ──
            if self.state == "boss" and not self.effects.is_paused:
                keys = pygame.key.get_pressed()
                if keys[pygame.K_LEFT] or keys[pygame.K_a]:
                    self.player.move(-1)
                if keys[pygame.K_RIGHT] or keys[pygame.K_d]:
                    self.player.move(1)

                # Camera stays fixed during boss fight
                self.scroll = 0

                self.player.update(self.platform_list)
                self.platform_list.update(0)

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

                # Background
                self.background.draw(self.screen, self.scroll + shake[0])

                # Ground
                ground_y = int(GROUND_Y + shake[1])
                pygame.draw.rect(self.screen, (45, 30, 15),
                                 (0, ground_y, SCREEN_WIDTH, SCREEN_HEIGHT - ground_y))
                pygame.draw.rect(self.screen, (35, 100, 30),
                                 (0, ground_y, SCREEN_WIDTH, 6))

                # Platforms
                for p in self.platform_list:
                    self.screen.blit(
                        p.image,
                        (p.rect.x + shake[0], p.rect.y + shake[1]),
                    )

                # Enemies
                for e in self.enemy_list:
                    self.screen.blit(
                        e.image,
                        (e.rect.x + shake[0], e.rect.y + shake[1]),
                    )

                # Boss
                if self.boss and self.boss.state != 'dead':
                    self.screen.blit(
                        self.boss.image,
                        (self.boss.rect.x + shake[0], self.boss.rect.y + shake[1]),
                    )
                    # Draw fireballs
                    for fb in self.boss.fireballs:
                        self.screen.blit(
                            fb.image,
                            (fb.rect.x + shake[0], fb.rect.y + shake[1]),
                        )
                    # Draw breath visual
                    if self.boss.state == 'breathing' and self.boss.breath_rect:
                        breath_surf = pygame.Surface(
                            (self.boss.breath_rect.width, self.boss.breath_rect.height),
                            pygame.SRCALPHA,
                        )
                        breath_surf.fill((255, 120, 0, 100))
                        self.screen.blit(breath_surf, (
                            self.boss.breath_rect.x + shake[0],
                            self.boss.breath_rect.y + shake[1],
                        ))

                # Power-ups
                for pu in self.powerup_list:
                    self.screen.blit(
                        pu.image,
                        (pu.rect.x + shake[0], pu.rect.y + shake[1]),
                    )

                # Player (blink during i-frames)
                if not self.player.invincible or (
                    self.player.iframes_timer % 4 < 2
                ):
                    self.screen.blit(
                        self.player.image,
                        (self.player.rect.x + shake[0],
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
        """Handle attack input — hits enemies and/or boss."""
        hits = self.player.attack(self.enemy_list)
        if self.sword_swing:
            self.sword_swing.play()
        if hits:
            if self.sword_hit:
                self.sword_hit.play()
            self.effects.hit_pause()
            self.effects.screen_shake(SCREEN_SHAKE_INTENSITY // 2)
            for enemy in hits:
                self.effects.spawn_particles(
                    enemy.rect.centerx, enemy.rect.centery,
                    WHITE, PARTICLE_COUNT_HIT,
                )
                self.effects.spawn_damage_number(
                    enemy.rect.centerx, enemy.rect.top,
                    self.player.attack_power if not self.player.attack_boosted
                    else int(self.player.attack_power * ATTACK_BOOST_MULTIPLIER),
                )
                enemy.apply_knockback(
                    1 if self.player.facing_right else -1
                )

        # Boss melee hit
        if self.state == "boss" and self.boss and self.boss.state not in ('dying', 'dead'):
            attack_rect = self.player.rect.inflate(
                PLAYER_ATTACK_POWER, 0
            )
            if self.player.facing_right:
                attack_rect.x += 25
            else:
                attack_rect.x -= 25
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

        card_w, card_h = 160, 280
        total_w = len(self._class_keys) * card_w + (len(self._class_keys) - 1) * 20
        start_x = (SCREEN_WIDTH - total_w) // 2

        for i, cls_key in enumerate(self._class_keys):
            cfg = CHARACTER_CLASSES[cls_key]
            x = start_x + i * (card_w + 20)
            y = 130
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

            # Stats
            stats = [
                f"HP: {int(PLAYER_HEALTH * cfg['health_mult'])}",
                f"ATK: {int(PLAYER_ATTACK_POWER * cfg['attack_mult'])}",
                f"SPD: {'★' * max(1, int(cfg['speed_mult'] * 3))}",
            ]
            if cfg.get('regen_rate', 0) > 0:
                stats.append("REGEN: ✓")

            for j, stat in enumerate(stats):
                stat_text = self.small_font.render(stat, True, (200, 200, 200))
                self.screen.blit(stat_text, (x + 15, y + 55 + j * 28))

            # Description
            desc_text = self.small_font.render(cfg['description'], True, (160, 160, 180))
            self.screen.blit(desc_text, (x + card_w // 2 - desc_text.get_width() // 2, y + card_h - 40))

            # Selection indicator
            if selected:
                arrow = self.font.render("▼", True, YELLOW)
                self.screen.blit(arrow, (x + card_w // 2 - arrow.get_width() // 2, y - 30))

        # Instructions
        hint = self.small_font.render("← →  Select  |  ENTER  Confirm", True, (120, 120, 150))
        self.screen.blit(hint, (SCREEN_WIDTH // 2 - hint.get_width() // 2, SCREEN_HEIGHT - 60))

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
