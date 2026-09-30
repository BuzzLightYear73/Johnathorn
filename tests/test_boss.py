"""
Unit and integration tests for Boss fight: Dragon and Fireball.
Headless tests using Pygame dummy drivers.
"""
import os
import sys
import math
import pytest

# Force headless SDL drivers
os.environ["SDL_VIDEODRIVER"] = "dummy"
os.environ["SDL_AUDIODRIVER"] = "dummy"

# Ensure project root is in sys.path
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

import pygame

from Boss.dragon import Dragon
from Boss.fireball import Fireball
from settings import (
    BOSS_HEALTH,
    BOSS_HOVER_Y,
    BOSS_HOVER_SPEED,
    BOSS_HOVER_AMPLITUDE,
    BOSS_FIREBALL_DAMAGE,
    BOSS_FIREBALL_SPEED,
    BOSS_DEATH_FRAMES,
    SCREEN_WIDTH,
    SCREEN_HEIGHT,
)


@pytest.fixture(autouse=True)
def pygame_setup():
    """Initialize pygame display and audio in headless mode."""
    pygame.init()
    pygame.display.set_mode((1, 1))
    yield
    pygame.quit()


class TestDragon:
    """Test suite for the Dragon boss."""

    def test_dragon_init(self):
        """Verify initial health=500, phase=1, and state='hovering'."""
        dragon = Dragon()
        assert dragon.health == 500
        assert dragon.max_health == 500
        assert dragon.phase == 1
        assert dragon.state == "hovering"
        assert dragon.rect.y == BOSS_HOVER_Y

    def test_phase_transitions(self):
        """Verify phase transitions: at 60% health -> phase 2, at 30% -> phase 3."""
        dragon = Dragon()
        player_rect = pygame.Rect(100, 400, 50, 50)
        assert dragon.phase == 1

        # Above 60% health (e.g. 301 / 500 = 60.2%) -> still Phase 1
        dragon.health = 301
        dragon.update(player_rect)
        assert dragon.phase == 1

        # At exactly 60% health (300 / 500 = 60.0%) -> Phase 2
        dragon.health = 300
        dragon.update(player_rect)
        assert dragon.phase == 2

        # Between 30% and 60% (e.g. 151 / 500 = 30.2%) -> still Phase 2
        dragon.health = 151
        dragon.update(player_rect)
        assert dragon.phase == 2

        # At exactly 30% health (150 / 500 = 30.0%) -> Phase 3
        dragon.health = 150
        dragon.update(player_rect)
        assert dragon.phase == 3

        # Below 30% health -> Phase 3
        dragon.health = 50
        dragon.update(player_rect)
        assert dragon.phase == 3

    def test_take_damage(self):
        """Verify take_damage reduces health and returns True when lethal."""
        dragon = Dragon()
        initial_health = dragon.health

        # Non-lethal damage
        is_lethal = dragon.take_damage(100)
        assert dragon.health == initial_health - 100
        assert is_lethal is False
        assert dragon.state == "hovering"

        # Additional non-lethal damage
        is_lethal = dragon.take_damage(150)
        assert dragon.health == initial_health - 250
        assert is_lethal is False

        # Lethal damage (remaining 250 health)
        is_lethal = dragon.take_damage(250)
        assert dragon.health == 0
        assert is_lethal is True

        # Further damage while dying/dead should return False and not reduce below 0
        is_lethal_post = dragon.take_damage(50)
        assert dragon.health == 0
        assert is_lethal_post is False

    def test_death_sequence(self):
        """Verify taking lethal damage sets state='dying'."""
        dragon = Dragon()
        player_rect = pygame.Rect(100, 400, 50, 50)

        # Apply lethal damage
        lethal = dragon.take_damage(dragon.health)
        assert lethal is True
        assert dragon.health == 0
        assert dragon.state == "dying"
        assert dragon.state_timer == BOSS_DEATH_FRAMES

        # Update through the death sequence frames until state becomes 'dead'
        for _ in range(BOSS_DEATH_FRAMES):
            assert dragon.state == "dying"
            dragon.update(player_rect)

        assert dragon.state == "dead"

    def test_fireball_attack(self):
        """Verify that after cooldown expires, dragon can launch fireball targeting player."""
        dragon = Dragon()
        player_rect = pygame.Rect(100, 400, 50, 50)

        # Before cooldown expires, no fireballs are active
        assert len(dragon.fireballs) == 0

        # Expire cooldowns to allow fireball attack
        dragon.attack_cooldown = 0
        dragon.fireball_cooldown = 0

        dragon.update(player_rect)

        # Dragon should enter fireball attack state and spawn a projectile
        assert dragon.state == "fireball"
        assert len(dragon.fireballs) == 1

        fireball = list(dragon.fireballs)[0]
        # Target is player to the left: fireball vx should be negative
        assert fireball.vx < 0
        assert fireball.damage == BOSS_FIREBALL_DAMAGE
        # Fireball cooldown should have reset
        assert dragon.fireball_cooldown > 0

    def test_hover_bob(self):
        """Verify dragon y oscillates around BOSS_HOVER_Y."""
        dragon = Dragon()
        player_rect = pygame.Rect(100, 400, 50, 50)

        # Keep attack cooldown high so dragon stays in hovering state
        dragon.attack_cooldown = 10000

        y_positions = []
        # Sample over one full sine wave cycle (~315 frames at speed=0.02)
        total_frames = int(2 * math.pi / BOSS_HOVER_SPEED) + 10
        for _ in range(total_frames):
            dragon.update(player_rect)
            y_positions.append(dragon.rect.y)

        # Check oscillation above and below BOSS_HOVER_Y
        min_y = min(y_positions)
        max_y = max(y_positions)

        assert min_y < BOSS_HOVER_Y, f"Expected min_y < {BOSS_HOVER_Y}, got {min_y}"
        assert max_y > BOSS_HOVER_Y, f"Expected max_y > {BOSS_HOVER_Y}, got {max_y}"

        # Check bounds: within hover amplitude
        assert min_y >= BOSS_HOVER_Y - BOSS_HOVER_AMPLITUDE
        assert max_y <= BOSS_HOVER_Y + BOSS_HOVER_AMPLITUDE


class TestFireball:
    """Test suite for the Fireball projectile."""

    def test_fireball_init(self):
        """Verify fireball spawns at correct position and has velocity toward target."""
        spawn_x = 600
        spawn_y = 200
        target_x = 100
        target_y = 200

        fb = Fireball(spawn_x, spawn_y, target_x, target_y)

        # Fireball should center at spawn coordinates
        assert fb.rect.center == (spawn_x, spawn_y)

        # Direct horizontal shot to the left
        assert fb.vx == pytest.approx(-BOSS_FIREBALL_SPEED)
        assert fb.vy == pytest.approx(0.0)

        # Angled shot: 3-4-5 triangle toward bottom-left
        fb_angled = Fireball(500, 100, 200, 500)
        # dx = -300, dy = 400, dist = 500
        expected_vx = (-300 / 500) * BOSS_FIREBALL_SPEED
        expected_vy = (400 / 500) * BOSS_FIREBALL_SPEED
        assert fb_angled.vx == pytest.approx(expected_vx)
        assert fb_angled.vy == pytest.approx(expected_vy)
        assert math.hypot(fb_angled.vx, fb_angled.vy) == pytest.approx(BOSS_FIREBALL_SPEED)

    def test_fireball_moves(self):
        """Verify update() changes position according to velocity."""
        fb = Fireball(400, 300, 100, 300)
        initial_x = fb.rect.x
        initial_y = fb.rect.y

        fb.update()

        assert fb.rect.x == initial_x + fb.vx
        assert fb.rect.y == initial_y + fb.vy
        assert fb.rect.x != initial_x

    def test_fireball_kills_offscreen(self):
        """Verify fireball auto-removes when off screen."""
        group = pygame.sprite.Group()

        # On-screen fireball stays alive
        fb = Fireball(400, 300, 100, 300)
        group.add(fb)
        fb.update()
        assert group.has(fb)
        assert fb.alive()

        # Off-screen left (rect.right < -50)
        fb_left = Fireball(400, 300, 100, 300)
        group.add(fb_left)
        fb_left.rect.right = -51
        fb_left.update()
        assert not group.has(fb_left)
        assert not fb_left.alive()

        # Off-screen right (rect.left > SCREEN_WIDTH + 50)
        fb_right = Fireball(400, 300, 500, 300)
        group.add(fb_right)
        fb_right.rect.left = SCREEN_WIDTH + 51
        fb_right.update()
        assert not group.has(fb_right)
        assert not fb_right.alive()

        # Off-screen top (rect.bottom < -50)
        fb_top = Fireball(400, 300, 400, 100)
        group.add(fb_top)
        fb_top.rect.bottom = -51
        fb_top.update()
        assert not group.has(fb_top)
        assert not fb_top.alive()

        # Off-screen bottom (rect.top > SCREEN_HEIGHT + 50)
        fb_bottom = Fireball(400, 300, 400, 500)
        group.add(fb_bottom)
        fb_bottom.rect.top = SCREEN_HEIGHT + 51
        fb_bottom.update()
        assert not group.has(fb_bottom)
        assert not fb_bottom.alive()

    def test_fireball_damage(self):
        """Verify fireball has correct damage value."""
        fb = Fireball(400, 300, 100, 300)
        assert fb.damage == BOSS_FIREBALL_DAMAGE
        assert fb.damage == 20
