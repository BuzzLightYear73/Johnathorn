"""Sprite frame loading utilities for the Animation system."""

from pathlib import Path

import pygame


def load_clip(directory: Path, size: tuple = (80, 80), count: int = None) -> list:
    """Load numbered PNG frames (0.png, 1.png, ...) from directory.

    Scale each to *size*. If *count* is given, load exactly that many.
    If directory doesn't exist or has no frames, return an empty list.
    """
    directory = Path(directory)
    if not directory.is_dir():
        return []

    frames: list[pygame.Surface] = []
    idx = 0
    while True:
        if count is not None and idx >= count:
            break
        path = directory / f"{idx}.png"
        if not path.is_file():
            break
        try:
            surf = pygame.image.load(str(path)).convert_alpha()
            surf = pygame.transform.scale(surf, size)
            frames.append(surf)
        except pygame.error:
            break
        idx += 1

    return frames


def load_clips_from_config(
    animations_config: dict,
    base_dir: Path,
    size: tuple = (80, 80),
) -> dict:
    """Load all clips defined in an animations config dict.

    animations_config format::

        {
            "idle": {"dir": "generated/idle", "frames": 4, "speed": 10, "loop": True},
            "walk": {"dir": "generated/walk", "frames": 8, "speed": 8, "loop": True},
            ...
        }

    Returns: ``{name: {"frames": [Surface, ...], "speed": int, "loop": bool}}``
    """
    base_dir = Path(base_dir)
    result: dict = {}

    for name, cfg in animations_config.items():
        clip_dir = base_dir / cfg.get('dir', f'generated/{name}')
        count = cfg.get('frames', None)
        speed = cfg.get('speed', 8)
        loop = cfg.get('loop', True)

        frames = load_clip(clip_dir, size=size, count=count)
        result[name] = {
            'frames': frames,
            'speed': speed,
            'loop': loop,
        }

    return result


def load_tinted_clips(clips: dict, tint_color: tuple) -> dict:
    """Apply a color tint overlay to all frames in all clips.

    Used for enemy variants. Returns a new clips dict.

    *tint_color*: ``(R, G, B, A)`` tuple.
    """
    tinted: dict = {}

    for name, data in clips.items():
        frames = data.get('frames', [])
        tinted_frames: list[pygame.Surface] = []

        for frame in frames:
            # Copy the original frame
            new_frame = frame.copy()
            # Create a tint overlay the same size
            overlay = pygame.Surface(new_frame.get_size(), pygame.SRCALPHA)
            overlay.fill(tint_color)
            # Blend the tint onto the copy
            new_frame.blit(overlay, (0, 0), special_flags=pygame.BLEND_RGBA_MULT)
            tinted_frames.append(new_frame)

        tinted[name] = {
            'frames': tinted_frames,
            'speed': data.get('speed', 8),
            'loop': data.get('loop', True),
        }

    return tinted
