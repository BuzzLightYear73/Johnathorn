#!/usr/bin/env python3
"""
Sprite Sheet Slicer for Johnathorn: Quest of Riefel

Converts generated JPG sprite sheets to PNG, slices them into
individual frames, and saves them to the appropriate directories.
"""

import os
import sys
from pathlib import Path

try:
    from PIL import Image
except ImportError:
    print("Pillow not found. Trying venv...")
    venv_path = Path(__file__).parent.parent / ".venv" / "lib"
    for p in venv_path.glob("python*/site-packages"):
        sys.path.insert(0, str(p))
    from PIL import Image


# Base paths
PROJECT_ROOT = Path(__file__).parent.parent
IMAGES_DIR = PROJECT_ROOT / "images"
ARTIFACT_DIR = Path("/home/nseney/.gemini/antigravity/brain/b4a4dc42-ba6d-4541-9990-4a7a2d42e4ce")
PREV_ARTIFACT_DIR = Path("/home/nseney/.gemini/antigravity/brain/2f1aa9b3-33f2-4a47-b501-d1de3f3b5737")

# Manifest: (source_jpg_filename, output_subdir, num_frames)
# Format: output_subdir is relative to IMAGES_DIR
SPRITE_SHEETS = [
    # === WARRIOR (previously generated sheets from prior artifact dir) ===
    ("warrior_walk_sheet_1790733365462.jpg", "warrior/generated/walk", 8, PREV_ARTIFACT_DIR),
    ("warrior_idle_sheet_1790734001898.jpg", "warrior/generated/idle", 4, PREV_ARTIFACT_DIR),
    ("warrior_attack_sheet_1790734018517.jpg", "warrior/generated/attack", 6, PREV_ARTIFACT_DIR),
    ("warrior_die_sheet_1790734039278.jpg", "warrior/generated/die", 4, PREV_ARTIFACT_DIR),
    ("warrior_jump_sheet_1790734069216.jpg", "warrior/generated/jump", 2, PREV_ARTIFACT_DIR),
    # Warrior new sheets
    ("warrior_dash_sheet_1790734166581.jpg", "warrior/generated/dash", 3, ARTIFACT_DIR),
    ("warrior_stagger_sheet_1790734175529.jpg", "warrior/generated/stagger", 2, ARTIFACT_DIR),

    # === MAGE ===
    ("mage_walk_sheet_1790734090473.jpg", "mage/generated/walk", 8, PREV_ARTIFACT_DIR),
    ("mage_idle_sheet_1790734185704.jpg", "mage/generated/idle", 4, ARTIFACT_DIR),
    ("mage_attack_sheet_1790734194598.jpg", "mage/generated/attack", 6, ARTIFACT_DIR),
    ("mage_jump_sheet_1790734203421.jpg", "mage/generated/jump", 2, ARTIFACT_DIR),
    ("mage_dash_sheet_1790734223904.jpg", "mage/generated/dash", 3, ARTIFACT_DIR),
    ("mage_die_sheet_1790734232579.jpg", "mage/generated/die", 4, ARTIFACT_DIR),
    ("mage_stagger_sheet_1790734241548.jpg", "mage/generated/stagger", 2, ARTIFACT_DIR),

    # === ARCHER ===
    ("archer_idle_sheet_1790734263556.jpg", "archer/generated/idle", 4, ARTIFACT_DIR),
    ("archer_walk_sheet_1790734271756.jpg", "archer/generated/walk", 8, ARTIFACT_DIR),
    ("archer_attack_sheet_1790734281143.jpg", "archer/generated/attack", 6, ARTIFACT_DIR),
    ("archer_jump_sheet_1790734289262.jpg", "archer/generated/jump", 2, ARTIFACT_DIR),
    ("archer_dash_sheet_1790734296990.jpg", "archer/generated/dash", 3, ARTIFACT_DIR),
    ("archer_die_sheet_1790734317995.jpg", "archer/generated/die", 4, ARTIFACT_DIR),
    ("archer_stagger_sheet_1790734327389.jpg", "archer/generated/stagger", 2, ARTIFACT_DIR),

    # === DRUID ===
    ("druid_idle_sheet_1790734375121.jpg", "druid/generated/idle", 4, ARTIFACT_DIR),
    ("druid_walk_sheet_1790734385707.jpg", "druid/generated/walk", 8, ARTIFACT_DIR),
    ("druid_attack_sheet_1790734398312.jpg", "druid/generated/attack", 6, ARTIFACT_DIR),
    ("druid_jump_sheet_1790734419878.jpg", "druid/generated/jump", 2, ARTIFACT_DIR),
    ("druid_dash_sheet_1790734598212.jpg", "druid/generated/dash", 3, ARTIFACT_DIR),
    ("druid_die_sheet_1790734608082.jpg", "druid/generated/die", 4, ARTIFACT_DIR),
    ("druid_stagger_sheet_1790734617403.jpg", "druid/generated/stagger", 2, ARTIFACT_DIR),

    # === SKELETON WARRIOR ===
    ("skeleton_warrior_idle_sheet_1790734640985.jpg", "skeleton_warrior/idle", 4, ARTIFACT_DIR),
    ("skeleton_warrior_walk_sheet_1790734654229.jpg", "skeleton_warrior/walk", 8, ARTIFACT_DIR),
    ("skeleton_warrior_attack_sheet_1790734665432.jpg", "skeleton_warrior/attack", 4, ARTIFACT_DIR),
    ("skeleton_warrior_die_sheet_1790734674354.jpg", "skeleton_warrior/die", 4, ARTIFACT_DIR),
    ("skeleton_warrior_stagger_sheet_1790734684137.jpg", "skeleton_warrior/stagger", 3, ARTIFACT_DIR),

    # === SKELETON ARCHER ===
    ("skeleton_archer_idle_sheet_1790734713605.jpg", "skeleton_archer/idle", 4, ARTIFACT_DIR),
    ("skeleton_archer_walk_sheet_1790734721780.jpg", "skeleton_archer/walk", 8, ARTIFACT_DIR),
    ("skeleton_archer_attack_sheet_1790734730452.jpg", "skeleton_archer/attack", 4, ARTIFACT_DIR),
    ("skeleton_archer_die_sheet_1790734738887.jpg", "skeleton_archer/die", 4, ARTIFACT_DIR),
    ("skeleton_archer_stagger_sheet_1790734748453.jpg", "skeleton_archer/stagger", 3, ARTIFACT_DIR),

    # === SHADOW BAT ===
    ("shadow_bat_hover_sheet_1790734771482.jpg", "shadow_bat/hover", 4, ARTIFACT_DIR),
    ("shadow_bat_fly_sheet_1790734780068.jpg", "shadow_bat/fly", 8, ARTIFACT_DIR),
    ("shadow_bat_dive_sheet_1790734789275.jpg", "shadow_bat/dive", 4, ARTIFACT_DIR),
    ("shadow_bat_die_sheet_1790734798065.jpg", "shadow_bat/die", 4, ARTIFACT_DIR),

    # === DRAGON ===
    ("dragon_hover_sheet_1790734828039.jpg", "dragon/generated/hover", 6, ARTIFACT_DIR),
    ("dragon_breath_sheet_1790734837082.jpg", "dragon/generated/breath", 6, ARTIFACT_DIR),
    ("dragon_fireball_sheet_1790734846419.jpg", "dragon/generated/fireball", 4, ARTIFACT_DIR),
    ("dragon_slam_sheet_1790734855810.jpg", "dragon/generated/slam", 4, ARTIFACT_DIR),
    ("dragon_die_sheet_1790734865269.jpg", "dragon/generated/die", 5, ARTIFACT_DIR),
    ("dragon_stagger_sheet_1790734891021.jpg", "dragon/generated/stagger", 4, ARTIFACT_DIR),
]


def slice_sprite_sheet(src_path: Path, output_dir: Path, num_frames: int) -> list[Path]:
    """
    Slice a horizontal sprite sheet into individual frames.
    
    Args:
        src_path: Path to the source JPG sprite sheet
        output_dir: Directory to save individual frame PNGs
        num_frames: Number of frames to slice into
        
    Returns:
        List of paths to created frame files
    """
    output_dir.mkdir(parents=True, exist_ok=True)
    
    img = Image.open(src_path)
    width, height = img.size
    frame_width = width // num_frames
    
    created_files = []
    for i in range(num_frames):
        left = i * frame_width
        right = (i + 1) * frame_width
        frame = img.crop((left, 0, right, height))
        
        # Convert to RGBA for transparency support
        if frame.mode != "RGBA":
            frame = frame.convert("RGBA")
        
        frame_path = output_dir / f"{i}.png"
        frame.save(frame_path, "PNG")
        created_files.append(frame_path)
    
    # Also save the full sheet as PNG
    sheet_png_path = output_dir / "sheet.png"
    if img.mode != "RGBA":
        img = img.convert("RGBA")
    img.save(sheet_png_path, "PNG")
    created_files.append(sheet_png_path)
    
    return created_files


def main():
    total_files = 0
    total_sheets = 0
    errors = []
    
    print(f"Sprite Sheet Slicer - Processing {len(SPRITE_SHEETS)} sheets")
    print(f"Output directory: {IMAGES_DIR}")
    print("=" * 60)
    
    for filename, output_subdir, num_frames, source_dir in SPRITE_SHEETS:
        src_path = source_dir / filename
        output_dir = IMAGES_DIR / output_subdir
        
        if not src_path.exists():
            errors.append(f"NOT FOUND: {src_path}")
            print(f"  ✗ {filename} - FILE NOT FOUND")
            continue
        
        try:
            created = slice_sprite_sheet(src_path, output_dir, num_frames)
            total_files += len(created)
            total_sheets += 1
            print(f"  ✓ {output_subdir}: {num_frames} frames + sheet.png")
        except Exception as e:
            errors.append(f"ERROR processing {filename}: {e}")
            print(f"  ✗ {filename} - {e}")
    
    print("=" * 60)
    print(f"Done! Processed {total_sheets}/{len(SPRITE_SHEETS)} sheets")
    print(f"Total files created: {total_files}")
    
    if errors:
        print(f"\n{len(errors)} errors:")
        for err in errors:
            print(f"  - {err}")
    
    return 0 if not errors else 1


if __name__ == "__main__":
    sys.exit(main())
