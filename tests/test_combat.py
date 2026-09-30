"""
Tests for Phase 3 — Combat & Hitbox Refinement.

TDD Gate 1: Tests written before implementation.

Covers:
- Attack phase progression (startup → active → recovery)
- Per-class hitbox dimensions
- Stagger on hit (interrupts attack)
- Enemy attack phases (damage only during active)
"""
import os
os.environ.setdefault('SDL_VIDEODRIVER', 'dummy')
os.environ.setdefault('SDL_AUDIODRIVER', 'dummy')

import unittest
import pygame

pygame.init()
pygame.display.set_mode((1, 1))

from Character.mainCharacter import MainCharacter
from Enemy.enemy import Enemy
import settings


class TestAttackPhases(unittest.TestCase):
    """Player attack must progress through startup → active → recovery."""

    def setUp(self):
        self.player = MainCharacter(100, 100, 'warrior')
        self.enemies = pygame.sprite.Group()

    def test_attack_starts_in_startup_phase(self):
        """Pressing attack should enter startup phase, not immediately active."""
        self.player.attack(self.enemies)
        self.assertEqual(self.player.attack_phase, 'startup')

    def test_attack_transitions_to_active(self):
        """After startup frames elapse, phase transitions to active."""
        fd = self.player.class_config['frame_data']
        self.player.attack(self.enemies)
        # Tick through startup
        for _ in range(fd['startup']):
            self.player.update_attack_phase()
        self.assertEqual(self.player.attack_phase, 'active')

    def test_attack_transitions_to_recovery(self):
        """After active frames elapse, phase transitions to recovery."""
        fd = self.player.class_config['frame_data']
        self.player.attack(self.enemies)
        for _ in range(fd['startup'] + fd['active']):
            self.player.update_attack_phase()
        self.assertEqual(self.player.attack_phase, 'recovery')

    def test_attack_ends_after_recovery(self):
        """After all phases complete, attacking is False and phase is None."""
        fd = self.player.class_config['frame_data']
        self.player.attack(self.enemies)
        total = fd['startup'] + fd['active'] + fd['recovery']
        for _ in range(total):
            self.player.update_attack_phase()
        self.assertFalse(self.player.attacking)
        self.assertIsNone(self.player.attack_phase)

    def test_no_damage_during_startup(self):
        """Enemies in range during startup phase should NOT take damage."""
        e = Enemy(130, 100, enemy_type='skeleton_warrior')
        self.enemies.add(e)
        initial_hp = e.health
        self.player.attack(self.enemies)
        # Still in startup — no damage dealt
        self.assertEqual(e.health, initial_hp)

    def test_damage_dealt_during_active_phase(self):
        """Melee hit check during active phase should deal damage."""
        fd = self.player.class_config['frame_data']
        e = Enemy(130, 100, enemy_type='skeleton_warrior')
        self.enemies.add(e)
        initial_hp = e.health
        self.player.attack(self.enemies)
        # Advance to active phase
        for _ in range(fd['startup']):
            self.player.update_attack_phase()
        # Now perform the hit check
        hits = self.player.check_melee_hits(self.enemies)
        self.assertGreater(len(hits), 0, "Should hit enemy during active phase")


class TestPerClassHitbox(unittest.TestCase):
    """Each class should have different hitbox dimensions from frame_data."""

    def test_all_classes_have_frame_data(self):
        """Every CHARACTER_CLASS must have a frame_data dict."""
        for cls_key, cfg in settings.CHARACTER_CLASSES.items():
            self.assertIn('frame_data', cfg, f"{cls_key} missing frame_data")
            fd = cfg['frame_data']
            for key in ('startup', 'active', 'recovery', 'hitbox_w', 'hitbox_h',
                        'hitbox_offset_x', 'knockback_force'):
                self.assertIn(key, fd, f"{cls_key} frame_data missing '{key}'")

    def test_warrior_has_widest_hitbox(self):
        """Warrior should have the widest melee hitbox."""
        warrior_w = settings.CHARACTER_CLASSES['warrior']['frame_data']['hitbox_w']
        archer_w = settings.CHARACTER_CLASSES['archer']['frame_data']['hitbox_w']
        self.assertGreater(warrior_w, archer_w)

    def test_warrior_has_highest_knockback(self):
        """Warrior should have the highest knockback force."""
        warrior_kb = settings.CHARACTER_CLASSES['warrior']['frame_data']['knockback_force']
        for cls_key in ('mage', 'archer', 'druid'):
            other_kb = settings.CHARACTER_CLASSES[cls_key]['frame_data']['knockback_force']
            self.assertGreaterEqual(warrior_kb, other_kb,
                f"Warrior knockback ({warrior_kb}) should be >= {cls_key} ({other_kb})")


class TestStagger(unittest.TestCase):
    """Taking damage should stagger the player and interrupt attacks."""

    def setUp(self):
        self.player = MainCharacter(100, 100, 'warrior')
        self.enemies = pygame.sprite.Group()

    def test_take_damage_sets_stagger(self):
        """Taking damage should set _staggered = True."""
        self.player.take_damage(10)
        self.assertTrue(self.player._staggered)

    def test_stagger_interrupts_attack(self):
        """Taking damage mid-attack should cancel the attack."""
        self.player.attack(self.enemies)
        self.assertTrue(self.player.attacking)
        self.player.take_damage(10)
        self.assertFalse(self.player.attacking)
        self.assertIsNone(self.player.attack_phase)

    def test_stagger_timer_counts_down(self):
        """Stagger timer should decrement each update."""
        self.player.take_damage(10)
        initial_timer = self.player._stagger_timer
        self.assertGreater(initial_timer, 0)
        # Simulate one update tick
        self.player._update_stagger()
        self.assertEqual(self.player._stagger_timer, initial_timer - 1)

    def test_stagger_clears_after_timer(self):
        """After stagger timer expires, _staggered should be False."""
        self.player.take_damage(10)
        timer = self.player._stagger_timer
        for _ in range(timer):
            self.player._update_stagger()
        self.assertFalse(self.player._staggered)


class TestEnemyAttackPhase(unittest.TestCase):
    """Enemies should only deal damage during their active attack frames."""

    def setUp(self):
        self.enemy = Enemy(100, 100, enemy_type='skeleton_warrior')

    def test_enemy_has_attack_phase_fields(self):
        """Enemy should have attack_phase tracking."""
        self.assertIsNone(self.enemy.attack_phase)

    def test_enemy_types_have_combat_config(self):
        """All ENEMY_TYPES must have attack phase configs."""
        for et_key, cfg in settings.ENEMY_TYPES.items():
            for key in ('stagger_frames', 'attack_startup', 'attack_active', 'attack_recovery'):
                self.assertIn(key, cfg, f"{et_key} missing '{key}'")

    def test_enemy_attack_enters_startup(self):
        """When enemy starts attack, phase should be startup."""
        self.enemy._start_attack()
        if self.enemy.attacking:
            self.assertEqual(self.enemy.attack_phase, 'startup')

    def test_enemy_in_active_phase_property(self):
        """Enemy should expose in_active_attack property."""
        self.assertFalse(self.enemy.in_active_attack)


if __name__ == "__main__":
    unittest.main()
