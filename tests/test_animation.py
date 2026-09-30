"""Comprehensive tests for the Animation package (TDD Gate 1)."""

import os
import sys
import unittest
from pathlib import Path

os.environ.setdefault('SDL_VIDEODRIVER', 'dummy')
os.environ.setdefault('SDL_AUDIODRIVER', 'dummy')

import pygame

pygame.init()
pygame.display.set_mode((1, 1))

# Ensure project root is on sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from Animation.controller import AnimationController
from Animation.loader import load_clip, load_clips_from_config, load_tinted_clips


def _make_surface(color=(255, 0, 0, 255), size=(80, 80)):
    """Create a solid-color SRCALPHA surface for testing."""
    surf = pygame.Surface(size, pygame.SRCALPHA)
    surf.fill(color)
    return surf


class TestAnimationController(unittest.TestCase):
    """Tests for AnimationController."""

    def setUp(self):
        """Create dummy clips for each test."""
        self.idle_frames = [_make_surface((0, 255, 0, 255)) for _ in range(4)]
        self.walk_frames = [_make_surface((0, 0, 255, 255)) for _ in range(6)]
        self.attack_frames = [_make_surface((255, 0, 0, 255)) for _ in range(3)]

        self.clips = {
            'idle': self.idle_frames,
            'walk': self.walk_frames,
            'attack': self.attack_frames,
        }

    def test_default_clip_plays_on_init(self):
        """Controller should start playing the default clip."""
        ac = AnimationController(self.clips, default_clip='idle')
        self.assertEqual(ac.current_clip, 'idle')
        self.assertEqual(ac.frame_index, 0)

    def test_switch_clip(self):
        """play() should switch to a different looping clip."""
        ac = AnimationController(self.clips, default_clip='idle')
        ac.play('walk')
        self.assertEqual(ac.current_clip, 'walk')
        self.assertEqual(ac.frame_index, 0)

    def test_frame_advances_after_speed_ticks(self):
        """Frame index should advance after 'speed' ticks."""
        ac = AnimationController(self.clips, default_clip='idle', frame_duration=4)
        self.assertEqual(ac.frame_index, 0)
        # 3 ticks — not enough
        for _ in range(3):
            ac.update()
        self.assertEqual(ac.frame_index, 0)
        # 4th tick advances to frame 1
        ac.update()
        self.assertEqual(ac.frame_index, 1)

    def test_looping_clip_wraps_around(self):
        """A looping clip should wrap back to frame 0."""
        ac = AnimationController(self.clips, default_clip='idle', frame_duration=1)
        # idle has 4 frames, speed=1 → each tick advances frame
        for _ in range(4):
            ac.update()
        self.assertEqual(ac.frame_index, 0)  # wrapped
        self.assertFalse(ac.finished)

    def test_one_shot_clip_signals_finished(self):
        """A one-shot clip should signal finished after all frames."""
        ac = AnimationController(self.clips, default_clip='idle', frame_duration=1)
        ac.play('attack')
        self.assertFalse(ac.finished)
        # attack has 3 frames, speed=1
        # tick 1 → frame 1
        ac.update()
        self.assertFalse(ac.finished)
        # tick 2 → frame 2
        ac.update()
        self.assertFalse(ac.finished)
        # tick 3 → would be frame 3 (out of bounds) → stays on 2, finished=True
        ac.update()
        self.assertTrue(ac.finished)
        self.assertEqual(ac.current_clip, 'attack')

    def test_one_shot_returns_to_default(self):
        """After a finished one-shot, the next update() returns to default clip."""
        ac = AnimationController(self.clips, default_clip='idle', frame_duration=1)
        ac.play('attack')
        # Play through all 3 frames
        for _ in range(3):
            ac.update()
        self.assertTrue(ac.finished)
        # Next update should return to idle
        ac.update()
        self.assertEqual(ac.current_clip, 'idle')
        self.assertEqual(ac.frame_index, 0)
        self.assertFalse(ac.finished)

    def test_get_frame_flips_for_left(self):
        """get_frame(facing_right=False) should return horizontally flipped surface."""
        # Use a surface with an asymmetric pattern to verify flip
        surf = pygame.Surface((80, 80), pygame.SRCALPHA)
        surf.fill((0, 0, 0, 0))
        # Draw a red rectangle on the left side only
        pygame.draw.rect(surf, (255, 0, 0, 255), (0, 0, 40, 80))

        clips = {'idle': [surf]}
        ac = AnimationController(clips, default_clip='idle')

        frame_r = ac.get_frame(facing_right=True)
        frame_l = ac.get_frame(facing_right=False)

        # The right-facing frame should have red on the left (pixel 0,0)
        self.assertEqual(frame_r.get_at((0, 0)), pygame.Color(255, 0, 0, 255))
        self.assertEqual(frame_r.get_at((79, 0)), pygame.Color(0, 0, 0, 0))

        # The left-facing (flipped) frame should have red on the right
        self.assertEqual(frame_l.get_at((79, 0)), pygame.Color(255, 0, 0, 255))
        self.assertEqual(frame_l.get_at((0, 0)), pygame.Color(0, 0, 0, 0))

    def test_empty_clips_returns_fallback(self):
        """An empty clips dict should return a magenta 80x80 fallback surface."""
        ac = AnimationController({})
        frame = ac.get_frame()
        self.assertEqual(frame.get_size(), (80, 80))
        self.assertEqual(frame.get_at((0, 0)), pygame.Color(255, 0, 255, 255))

    def test_play_same_clip_does_not_restart(self):
        """Playing the same clip again should not restart the animation."""
        ac = AnimationController(self.clips, default_clip='idle', frame_duration=1)
        ac.update()  # advance to frame 1
        self.assertEqual(ac.frame_index, 1)
        ac.play('idle')  # play same clip
        self.assertEqual(ac.frame_index, 1)  # should NOT reset

    def test_force_restart_resets_frame(self):
        """force_restart=True should reset the clip even if already playing."""
        ac = AnimationController(self.clips, default_clip='idle', frame_duration=1)
        ac.update()  # advance to frame 1
        self.assertEqual(ac.frame_index, 1)
        ac.play('idle', force_restart=True)
        self.assertEqual(ac.frame_index, 0)


class TestAnimationLoader(unittest.TestCase):
    """Tests for animation loading utilities."""

    def test_load_clip_from_directory(self):
        """load_clip should load numbered PNGs from a real directory."""
        walk_dir = PROJECT_ROOT / 'images' / 'warrior' / 'generated' / 'walk'
        frames = load_clip(walk_dir, size=(80, 80))
        self.assertEqual(len(frames), 8)
        for f in frames:
            self.assertIsInstance(f, pygame.Surface)
            self.assertEqual(f.get_size(), (80, 80))

    def test_load_clip_missing_directory_returns_empty(self):
        """load_clip on a non-existent path should return []."""
        frames = load_clip(Path('/tmp/no_such_directory_xyz'), size=(80, 80))
        self.assertEqual(frames, [])

    def test_load_clips_from_config(self):
        """load_clips_from_config should load clips per config dict."""
        config = {
            'walk': {
                'dir': 'generated/walk',
                'frames': 8,
                'speed': 6,
                'loop': True,
            },
        }
        base = PROJECT_ROOT / 'images' / 'warrior'
        result = load_clips_from_config(config, base, size=(64, 64))
        self.assertIn('walk', result)
        self.assertEqual(len(result['walk']['frames']), 8)
        self.assertEqual(result['walk']['speed'], 6)
        self.assertTrue(result['walk']['loop'])
        for f in result['walk']['frames']:
            self.assertEqual(f.get_size(), (64, 64))

    def test_load_tinted_clips(self):
        """load_tinted_clips should return new clips with tinted frames."""
        original_surf = _make_surface((255, 255, 255, 255))
        clips = {
            'idle': {
                'frames': [original_surf],
                'speed': 8,
                'loop': True,
            },
        }
        tinted = load_tinted_clips(clips, (255, 0, 0, 255))
        self.assertIn('idle', tinted)
        self.assertEqual(len(tinted['idle']['frames']), 1)

        tinted_frame = tinted['idle']['frames'][0]
        # White * (255,0,0,255) via BLEND_RGBA_MULT → should produce red
        pixel = tinted_frame.get_at((40, 40))
        self.assertEqual(pixel.r, 255)
        self.assertEqual(pixel.g, 0)
        self.assertEqual(pixel.b, 0)

        # Original should be unchanged
        orig_pixel = original_surf.get_at((40, 40))
        self.assertEqual(orig_pixel, pygame.Color(255, 255, 255, 255))


if __name__ == '__main__':
    unittest.main()
