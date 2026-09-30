"""Frame-based animation controller with named clips."""

import pygame


class AnimationController:
    """Frame-based animation controller with named clips."""

    ONE_SHOT_CLIPS = {'attack', 'die', 'stagger', 'dash', 'breath', 'fireball', 'slam', 'dive'}

    def __init__(self, clips: dict, default_clip: str = 'idle', frame_duration: int = 8):
        """
        clips: {name: {"frames": [Surface, ...], "speed": int, "loop": bool}}
        OR clips: {name: [Surface, ...]}  (uses frame_duration and auto-detects loop)
        default_clip: clip to return to after one-shot completes
        frame_duration: default ticks per animation frame
        """
        self._clips: dict = {}
        self._default_clip = default_clip
        self._current_clip = default_clip
        self._tick = 0
        self._frame_idx = 0
        self._finished = False

        # Build the fallback surface once
        self._fallback = pygame.Surface((80, 80), pygame.SRCALPHA)
        self._fallback.fill((255, 0, 255, 255))

        # Normalize each clip into internal format
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

            frames_r = list(frames)
            frames_l = [pygame.transform.flip(f, True, False) for f in frames_r]

            self._clips[name] = {
                'frames_r': frames_r,
                'frames_l': frames_l,
                'speed': speed,
                'loop': loop,
            }

        # If default clip isn't in clips, pick the first available (or leave as-is)
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
        self._tick = 0
        self._frame_idx = 0
        self._finished = False

    def update(self):
        """Advance frame counter by 1 tick. Handle looping and one-shot completion."""
        clip = self._clips.get(self._current_clip)
        if not clip or not clip['frames_r']:
            return

        num_frames = len(clip['frames_r'])

        if self._finished:
            # One-shot already done — return to default clip
            self._current_clip = self._default_clip
            self._tick = 0
            self._frame_idx = 0
            self._finished = False
            return

        self._tick += 1
        if self._tick >= clip['speed']:
            self._tick = 0
            self._frame_idx += 1

            if self._frame_idx >= num_frames:
                if clip['loop']:
                    self._frame_idx = 0
                else:
                    # Stay on last frame and mark finished
                    self._frame_idx = num_frames - 1
                    self._finished = True

    def get_frame(self, facing_right: bool = True) -> pygame.Surface:
        """Return the current frame surface, flipped for direction."""
        clip = self._clips.get(self._current_clip)
        if not clip or not clip['frames_r']:
            return self._fallback

        if facing_right:
            return clip['frames_r'][self._frame_idx]
        return clip['frames_l'][self._frame_idx]

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
        """Current frame index within the active clip."""
        return self._frame_idx
