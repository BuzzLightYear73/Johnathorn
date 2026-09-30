"""Frame-based animation controller with named clips and procedural micro-animation."""

import math
import pygame


class AnimationController:
    """Animation controller using paper-puppet technique.

    Uses a single key frame per clip and applies procedural transforms
    (bob, lean, squash-stretch) to create smooth animation from static art.
    """

    ONE_SHOT_CLIPS = {'attack', 'die', 'stagger', 'dash', 'breath', 'fireball', 'slam', 'dive'}

    # Procedural animation profiles per clip type
    # phase_speed: how fast the animation oscillates (radians per tick)
    # bob_y: vertical bounce amplitude in pixels
    # lean_deg: side-to-side lean in degrees
    # squash_x / squash_y: scale oscillation amplitude (1.0 = no change)
    # one_shot_curve: if True, use a linear 0→1 progress instead of sin wave
    ANIM_PROFILES = {
        'idle': {
            'phase_speed': 0.06,
            'bob_y': 2.0,
            'lean_deg': 0.0,
            'squash_x': 0.0,
            'squash_y': 0.02,
        },
        'walk': {
            'phase_speed': 0.18,
            'bob_y': 3.0,
            'lean_deg': 3.0,
            'squash_x': 0.0,
            'squash_y': 0.03,
        },
        'attack': {
            'phase_speed': 0.0,  # uses one-shot curve
            'bob_y': 0.0,
            'lean_deg': 0.0,
            'squash_x': 0.15,
            'squash_y': -0.1,
            'one_shot_curve': True,
        },
        'jump': {
            'phase_speed': 0.0,
            'bob_y': 0.0,
            'lean_deg': 0.0,
            'squash_x': -0.05,
            'squash_y': 0.08,
        },
        'dash': {
            'phase_speed': 0.0,
            'bob_y': 0.0,
            'lean_deg': 0.0,
            'squash_x': 0.2,
            'squash_y': -0.15,
            'one_shot_curve': True,
        },
        'die': {
            'phase_speed': 0.0,
            'bob_y': 0.0,
            'lean_deg': 0.0,
            'squash_x': 0.0,
            'squash_y': -0.3,
            'one_shot_curve': True,
        },
        'stagger': {
            'phase_speed': 0.25,
            'bob_y': 0.0,
            'lean_deg': 8.0,
            'squash_x': 0.0,
            'squash_y': 0.0,
        },
    }

    DEFAULT_PROFILE = {
        'phase_speed': 0.06,
        'bob_y': 1.0,
        'lean_deg': 0.0,
        'squash_x': 0.0,
        'squash_y': 0.0,
    }

    def __init__(self, clips: dict, default_clip: str = 'idle', frame_duration: int = 8):
        """
        clips: {name: {"frames": [Surface, ...], "speed": int, "loop": bool}}
        OR clips: {name: [Surface, ...]}  (uses frame_duration and auto-detects loop)
        default_clip: clip to return to after one-shot completes
        frame_duration: default ticks per animation frame (used for one-shot duration)
        """
        self._clips: dict = {}
        self._default_clip = default_clip
        self._current_clip = default_clip
        self._phase = 0.0        # Procedural animation phase (radians for loop, 0-1 for one-shot)
        self._tick = 0
        self._frame_idx = 0
        self._finished = False
        self._frame_duration = frame_duration

        # Build the fallback surface once
        self._fallback = pygame.Surface((80, 80), pygame.SRCALPHA)
        self._fallback.fill((255, 0, 255, 255))

        # Normalize each clip into internal format — keep only the FIRST frame
        for name, data in clips.items():
            if isinstance(data, list):
                frames = data
                speed = frame_duration
                loop = name not in self.ONE_SHOT_CLIPS
            elif isinstance(data, dict):
                frames = data.get('frames', [])
                speed = data.get('speed', frame_duration)
                loop = data.get('loop', name not in self.ONE_SHOT_CLIPS)
            else:
                continue

            if not frames:
                continue

            # Use only the first (key) frame
            key_frame = frames[0]
            key_frame_l = pygame.transform.flip(key_frame, True, False)

            self._clips[name] = {
                'key_frame_r': key_frame,
                'key_frame_l': key_frame_l,
                'speed': speed,
                'loop': loop,
                'total_ticks': speed * max(len(frames), 1),  # duration for one-shot timing
            }

        # If default clip isn't in clips, pick the first available
        if self._default_clip not in self._clips and self._clips:
            self._default_clip = next(iter(self._clips))
            self._current_clip = self._default_clip

    def play(self, clip_name: str, force_restart: bool = False):
        """Switch to clip. If already playing and not force_restart, do nothing.
        If current clip is one-shot and not finished, don't interrupt (unless force_restart).
        """
        if clip_name not in self._clips:
            return

        # Already playing this clip — only restart if forced
        if clip_name == self._current_clip and not force_restart:
            return

        # Current clip is a one-shot still in progress — don't interrupt unless forced
        if not force_restart and not self._finished:
            cur = self._clips.get(self._current_clip)
            if cur and not cur['loop']:
                return

        self._current_clip = clip_name
        self._phase = 0.0
        self._tick = 0
        self._frame_idx = 0
        self._finished = False

    def update(self):
        """Advance procedural animation phase by 1 tick."""
        clip = self._clips.get(self._current_clip)
        if not clip:
            return

        if self._finished:
            # One-shot already done — return to default clip
            self._current_clip = self._default_clip
            self._phase = 0.0
            self._tick = 0
            self._frame_idx = 0
            self._finished = False
            return

        self._tick += 1

        profile = self.ANIM_PROFILES.get(self._current_clip, self.DEFAULT_PROFILE)

        if profile.get('one_shot_curve'):
            # Linear progress 0→1 over the clip's total duration
            total = clip['total_ticks']
            self._phase = min(self._tick / max(total, 1), 1.0)
            if self._tick >= total:
                if clip['loop']:
                    self._tick = 0
                    self._phase = 0.0
                else:
                    self._finished = True
        else:
            # Continuous sin-wave phase
            self._phase += profile.get('phase_speed', 0.06)
            # For non-looping clips, check duration
            if not clip['loop']:
                total = clip['total_ticks']
                if self._tick >= total:
                    self._finished = True

    def get_frame(self, facing_right: bool = True) -> pygame.Surface:
        """Return the current frame with procedural transforms applied."""
        clip = self._clips.get(self._current_clip)
        if not clip:
            return self._fallback

        base = clip['key_frame_r'] if facing_right else clip['key_frame_l']
        profile = self.ANIM_PROFILES.get(self._current_clip, self.DEFAULT_PROFILE)

        return self._apply_procedural(base, profile, facing_right)

    def _apply_procedural(self, base: pygame.Surface, profile: dict,
                          facing_right: bool) -> pygame.Surface:
        """Apply procedural bob, lean, and squash-stretch to base frame."""
        is_one_shot = profile.get('one_shot_curve', False)

        if is_one_shot:
            # Use attack/dash curve: wind up then snap
            t = self._phase  # 0→1
            # Bell curve: peaks at t=0.4 for attack feel
            curve = math.sin(t * math.pi)
        else:
            curve = math.sin(self._phase)

        # Calculate transforms
        bob_y = profile.get('bob_y', 0.0) * curve
        lean = profile.get('lean_deg', 0.0) * curve
        sq_x = 1.0 + profile.get('squash_x', 0.0) * curve
        sq_y = 1.0 + profile.get('squash_y', 0.0) * curve

        w, h = base.get_size()

        # Skip transform if everything is negligible
        if abs(bob_y) < 0.5 and abs(lean) < 0.5 and abs(sq_x - 1.0) < 0.01 and abs(sq_y - 1.0) < 0.01:
            return base

        # Apply squash-stretch by scaling
        new_w = max(1, int(w * sq_x))
        new_h = max(1, int(h * sq_y))

        if abs(lean) >= 0.5:
            # Rotate (lean) then scale
            rotated = pygame.transform.rotate(base, lean if facing_right else -lean)
            result = pygame.transform.scale(rotated, (new_w, new_h))
        elif new_w != w or new_h != h:
            result = pygame.transform.scale(base, (new_w, new_h))
        else:
            result = base

        # Apply bob by blitting onto an offset surface
        if abs(bob_y) >= 0.5:
            canvas = pygame.Surface((new_w, new_h + int(abs(bob_y)) + 1), pygame.SRCALPHA)
            canvas.blit(result, (0, max(0, -int(bob_y))))
            return canvas

        return result

    @property
    def finished(self) -> bool:
        """True if current one-shot clip has played all frames."""
        return self._finished

    @property
    def current_clip(self) -> str:
        """Name of the currently playing clip."""
        return self._current_clip

    @property
    def frame_index(self) -> int:
        """Current frame index within the active clip (always 0 in puppet mode)."""
        return self._frame_idx
