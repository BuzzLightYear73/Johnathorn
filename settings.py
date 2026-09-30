"""
Johnathorn — Central Settings & Constants
All game tuning knobs in one place. No magic numbers elsewhere.
"""
from pathlib import Path

# ── Paths ──────────────────────────────────────────────────────────────
BASE_DIR = Path(__file__).resolve().parent
IMAGES_DIR = BASE_DIR / "images"
SOUNDS_DIR = BASE_DIR / "Sounds"

# ── Display ────────────────────────────────────────────────────────────
SCREEN_WIDTH = 800
SCREEN_HEIGHT = 600
FPS = 60
TITLE = "Johnathorn: Quest of Riefel"
SCALED = True                   # Hardware-accelerated GPU scaling (pygame 2.0+)
RESIZABLE = True                # Allow window resizing with aspect preservation
START_FULLSCREEN = False        # Start in windowed mode

# ── Colors ─────────────────────────────────────────────────────────────
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
RED = (255, 0, 0)
GREEN = (0, 255, 0)
BLUE = (0, 0, 255)
YELLOW = (255, 255, 0)
ORANGE = (255, 165, 0)
DARK_RED = (139, 0, 0)
HEALTH_GREEN = (50, 205, 50)
HEALTH_BG = (60, 60, 60)

# ── Physics ────────────────────────────────────────────────────────────
GRAVITY = 0.8
GROUND_Y = 550

# ── Player ─────────────────────────────────────────────────────────────
PLAYER_START_X = 100
PLAYER_START_Y = 400
PLAYER_HEALTH = 100
PLAYER_ATTACK_POWER = 25
PLAYER_SPRITE_SIZE = 80
PLAYER_FRAME_COUNT = 4

# Movement (acceleration-based)
PLAYER_ACCEL = 0.9
PLAYER_FRICTION = 0.82
PLAYER_MAX_SPEED = 6.0

# Jump
JUMP_SPEED = -13.5
COYOTE_TIME = 6        # frames after walking off edge where jump still works
JUMP_BUFFER = 6        # frames before landing where jump press is queued
VARIABLE_JUMP_CUT = 0.4  # multiply velocity_y by this when releasing jump early

# I-frames
IFRAMES_DURATION = 60   # frames of invincibility after taking a hit
IFRAMES_BLINK_RATE = 4   # blink every N frames during i-frames

# Dash
DASH_SPEED = 15.0
DASH_DURATION = 8       # frames
DASH_COOLDOWN = 60      # frames

# Attack (legacy globals — used as fallbacks)
ATTACK_DURATION = 20    # frames
ATTACK_LUNGE = 3.0      # forward pixels on attack
ATTACK_HITBOX_INFLATE = 30  # extra width for attack rect
ATTACK_HITBOX_OFFSET = 25   # offset in facing direction

# Stagger
PLAYER_STAGGER_FRAMES = 12  # flinch duration on hit

# ── Enemy ──────────────────────────────────────────────────────────────
ENEMY_BASE_HEALTH = 50
ENEMY_SPEED_MIN = 1.0
ENEMY_SPEED_MAX = 3.0
ENEMY_DETECTION_RANGE = 250  # pixels — start chasing player
ENEMY_ATTACK_RANGE = 60      # pixels — stop and attack
ENEMY_CHASE_ACCEL = 0.15
ENEMY_KNOCKBACK_SPEED = 10
ENEMY_KNOCKBACK_FRAMES = 12
ENEMY_ATTACK_COOLDOWN = 60   # frames between attacks
ENEMY_ATTACK_DAMAGE = 15
ENEMY_SPRITE_SIZE = 80
ENEMY_FRAME_COUNT = 4

# ── Waves ──────────────────────────────────────────────────────────────
INITIAL_SPAWN_INTERVAL = 3000   # ms
SPAWN_INTERVAL_DECREASE = 200   # ms per wave
MIN_SPAWN_INTERVAL = 1000       # ms
ENEMIES_PER_WAVE_BASE = 3
ENEMIES_PER_WAVE_INCREMENT = 1
WAVE_PAUSE_DURATION = 120       # frames between waves
ENEMY_SPEED_INCREASE_PER_WAVE = 0.3

# ── Scoring ────────────────────────────────────────────────────────────
KILL_SCORE = 100
COMBO_BONUS = 50
COMBO_WINDOW = 90  # frames (1.5 seconds at 60fps)

# ── Power-ups ──────────────────────────────────────────────────────────
POWERUP_DROP_CHANCE = 0.20
POWERUP_SIZE = 30
POWERUP_BOB_SPEED = 0.05
POWERUP_BOB_AMPLITUDE = 5
HEALTH_RESTORE = 25
SPEED_BOOST_AMOUNT = 3.0
SPEED_BOOST_DURATION = 300      # frames (5s)
ATTACK_BOOST_MULTIPLIER = 2.0
ATTACK_BOOST_DURATION = 300     # frames (5s)

# ── Platform ───────────────────────────────────────────────────────────
PLATFORM_WIDTH = 200
PLATFORM_HEIGHT = 30
PLATFORM_MIN_Y = 250            # highest platform
PLATFORM_MAX_Y = 480            # lowest platform

# ── Arena ──────────────────────────────────────────────────────────────
ARENA_WIDTH = 1200              # total playable world width
ARENA_LEFT_BOUND = 30           # player can't walk past (world-space)
ARENA_RIGHT_BOUND = ARENA_WIDTH - 30

# Curated platform layouts per wave (world-space coordinates)
WAVE_PLATFORMS = {
    1: [(250, 460), (550, 380), (850, 460)],
    2: [(150, 460), (400, 370), (700, 370), (1000, 460), (550, 260)],
    3: [(100, 450), (350, 350), (600, 450), (850, 350), (1100, 450), (475, 230)],
}

# Boss arena — safe platforms for dodging slam shockwave + breath
BOSS_PLATFORMS = [
    (150, 430), (450, 430), (750, 430),   # three ground-level safe zones
    (300, 280), (600, 280),               # two high platforms for breath dodging
]

# ── Effects ────────────────────────────────────────────────────────────
SCREEN_SHAKE_INTENSITY = 8
SCREEN_SHAKE_DECAY = 0.82
HIT_PAUSE_FRAMES = 3
PARTICLE_COUNT_DEATH = 15
PARTICLE_COUNT_HIT = 8
PARTICLE_COUNT_LAND = 6
PARTICLE_COUNT_DASH = 3
PARTICLE_GRAVITY = 0.15
PARTICLE_LIFETIME_MIN = 15
PARTICLE_LIFETIME_MAX = 35
DAMAGE_NUMBER_SPEED = 1.5
DAMAGE_NUMBER_LIFETIME = 45     # frames
DAMAGE_NUMBER_FONT_SIZE = 20

# ── Camera ─────────────────────────────────────────────────────────────
CAMERA_LERP_SPEED = 0.08
CAMERA_LEFT_MARGIN = SCREEN_WIDTH // 3    # player kept in left third

# ── Waves / Boss Gate ──────────────────────────────────────────────────
MAX_WAVES_BEFORE_BOSS = 3

# ── Boss (Dragon) ──────────────────────────────────────────────────────
BOSS_HEALTH = 500
BOSS_SPRITE_SCALE = 3.0       # Scale factor for dragon sprites
BOSS_HOVER_Y = 120            # Y position when hovering
BOSS_HOVER_SPEED = 0.02       # Sinusoidal hover bob speed
BOSS_HOVER_AMPLITUDE = 15     # Hover bob pixels

# Fireball attack
BOSS_FIREBALL_SPEED = 5
BOSS_FIREBALL_DAMAGE = 20
BOSS_FIREBALL_SIZE = 50       # Scaled fireball sprite size
BOSS_FIREBALL_COOLDOWN = 120  # Frames between fireballs (phase 1)

# Fire breath attack
BOSS_BREATH_DAMAGE = 3        # Damage per frame of overlap
BOSS_BREATH_DURATION = 60     # Frames breath stays active
BOSS_BREATH_COOLDOWN = 180    # Frames between breaths

# Ground slam
BOSS_SLAM_DAMAGE = 30
BOSS_SLAM_SPEED = 12          # Descent speed
BOSS_SLAM_COOLDOWN = 240      # Frames between slams

# Phase thresholds (fraction of max health)
BOSS_PHASE2_THRESHOLD = 0.6
BOSS_PHASE3_THRESHOLD = 0.3

# Death
BOSS_DEATH_FRAMES = 90        # Frames for death sequence

# ── Character Classes ──────────────────────────────────────────────────
# Each class defines sprites directory, animation configs, and stat multipliers
CHARACTER_CLASSES = {
    "warrior": {
        "display_name": "Warrior",
        "description": "High health, powerful melee strikes",
        "sprite_dir": "warrior",
        "animations": {
            "idle":    {"dir": "generated/idle",    "frames": 4, "speed": 10, "loop": True},
            "walk":    {"dir": "generated/walk",    "frames": 8, "speed": 8,  "loop": True},
            "attack":  {"dir": "generated/attack",  "frames": 6, "speed": 5,  "loop": False},
            "jump":    {"dir": "generated/jump",    "frames": 2, "speed": 12, "loop": False},
            "dash":    {"dir": "generated/dash",    "frames": 3, "speed": 4,  "loop": False},
            "die":     {"dir": "generated/die",     "frames": 4, "speed": 8,  "loop": False},
            "stagger": {"dir": "generated/stagger", "frames": 2, "speed": 6,  "loop": False},
        },
        # Legacy frame lists (used until animation system fully migrated)
        "walk_frames": [f"wWalk{i}.png" for i in range(1, 9)],
        "attack_frames": [f"wAttack{i}.png" for i in range(1, 6)],
        "color": (200, 50, 50),
        "health_mult": 1.2,
        "attack_mult": 1.3,
        "speed_mult": 0.9,
        "frame_data": {
            "startup": 3,
            "active": 4,
            "recovery": 6,
            "hitbox_w": 50,
            "hitbox_h": 60,
            "hitbox_offset_x": 30,
            "knockback_force": 12,
        },
    },
    "mage": {
        "display_name": "Mage",
        "description": "Low health, devastating magic attacks",
        "sprite_dir": "mage",
        "animations": {
            "idle":    {"dir": "generated/idle",    "frames": 4, "speed": 10, "loop": True},
            "walk":    {"dir": "generated/walk",    "frames": 8, "speed": 8,  "loop": True},
            "attack":  {"dir": "generated/attack",  "frames": 6, "speed": 5,  "loop": False},
            "jump":    {"dir": "generated/jump",    "frames": 2, "speed": 12, "loop": False},
            "dash":    {"dir": "generated/dash",    "frames": 3, "speed": 4,  "loop": False},
            "die":     {"dir": "generated/die",     "frames": 4, "speed": 8,  "loop": False},
            "stagger": {"dir": "generated/stagger", "frames": 2, "speed": 6,  "loop": False},
        },
        "walk_frames": [f"mWalk{i}.png" for i in range(1, 8)],
        "attack_frames": ["mAttack.png"],
        "color": (80, 80, 220),
        "health_mult": 0.7,
        "attack_mult": 1.8,
        "speed_mult": 1.0,
        "frame_data": {
            "startup": 5,
            "active": 3,
            "recovery": 8,
            "hitbox_w": 40,
            "hitbox_h": 50,
            "hitbox_offset_x": 25,
            "knockback_force": 8,
        },
    },
    "archer": {
        "display_name": "Archer",
        "description": "Fast and agile, medium damage",
        "sprite_dir": "archer",
        "animations": {
            "idle":    {"dir": "generated/idle",    "frames": 4, "speed": 10, "loop": True},
            "walk":    {"dir": "generated/walk",    "frames": 8, "speed": 8,  "loop": True},
            "attack":  {"dir": "generated/attack",  "frames": 6, "speed": 5,  "loop": False},
            "jump":    {"dir": "generated/jump",    "frames": 2, "speed": 12, "loop": False},
            "dash":    {"dir": "generated/dash",    "frames": 3, "speed": 4,  "loop": False},
            "die":     {"dir": "generated/die",     "frames": 4, "speed": 8,  "loop": False},
            "stagger": {"dir": "generated/stagger", "frames": 2, "speed": 6,  "loop": False},
        },
        "walk_frames": [f"aWalk{i}.png" for i in range(1, 9)],
        "attack_frames": ["aAttack.png"],
        "color": (50, 180, 50),
        "health_mult": 0.9,
        "attack_mult": 1.0,
        "speed_mult": 1.3,
        "frame_data": {
            "startup": 2,
            "active": 2,
            "recovery": 4,
            "hitbox_w": 35,
            "hitbox_h": 40,
            "hitbox_offset_x": 20,
            "knockback_force": 6,
        },
    },
    "druid": {
        "display_name": "Druid",
        "description": "Balanced stats, regenerates health",
        "sprite_dir": "druid",
        "animations": {
            "idle":    {"dir": "generated/idle",    "frames": 4, "speed": 10, "loop": True},
            "walk":    {"dir": "generated/walk",    "frames": 8, "speed": 8,  "loop": True},
            "attack":  {"dir": "generated/attack",  "frames": 6, "speed": 5,  "loop": False},
            "jump":    {"dir": "generated/jump",    "frames": 2, "speed": 12, "loop": False},
            "dash":    {"dir": "generated/dash",    "frames": 3, "speed": 4,  "loop": False},
            "die":     {"dir": "generated/die",     "frames": 4, "speed": 8,  "loop": False},
            "stagger": {"dir": "generated/stagger", "frames": 2, "speed": 6,  "loop": False},
        },
        "walk_frames": [f"dWalk{i}.png" for i in range(1, 8)],
        "attack_frames": ["dAttack1.png", "dAttack2.png"],
        "color": (120, 200, 80),
        "health_mult": 1.0,
        "attack_mult": 1.0,
        "speed_mult": 1.0,
        "regen_rate": 0.05,
        "frame_data": {
            "startup": 4,
            "active": 5,
            "recovery": 5,
            "hitbox_w": 45,
            "hitbox_h": 55,
            "hitbox_offset_x": 28,
            "knockback_force": 10,
        },
    },
}
DEFAULT_CHARACTER_CLASS = "warrior"

# ── Enemy Types ───────────────────────────────────────────────────────
# Progressive unlock: wave 1 = skeleton_warrior only, wave 2+ = mix
ENEMY_TYPES = {
    "skeleton_warrior": {
        "display_name": "Skeleton Warrior",
        "sprite_dir": "skeleton_warrior",
        "animations": {
            "idle":    {"dir": "idle",    "frames": 4, "speed": 10, "loop": True},
            "walk":    {"dir": "walk",    "frames": 8, "speed": 8,  "loop": True},
            "attack":  {"dir": "attack",  "frames": 4, "speed": 6,  "loop": False},
            "die":     {"dir": "die",     "frames": 4, "speed": 8,  "loop": False},
            "stagger": {"dir": "stagger", "frames": 3, "speed": 6,  "loop": False},
        },
        "health_mult": 1.0,
        "damage_mult": 1.0,
        "speed_mult": 1.0,
        "unlock_wave": 1,
        "stagger_frames": 15,
        "attack_startup": 8,
        "attack_active": 4,
        "attack_recovery": 10,
    },
    "skeleton_archer": {
        "display_name": "Skeleton Archer",
        "sprite_dir": "skeleton_archer",
        "animations": {
            "idle":    {"dir": "idle",    "frames": 4, "speed": 10, "loop": True},
            "walk":    {"dir": "walk",    "frames": 8, "speed": 8,  "loop": True},
            "attack":  {"dir": "attack",  "frames": 4, "speed": 6,  "loop": False},
            "die":     {"dir": "die",     "frames": 4, "speed": 8,  "loop": False},
            "stagger": {"dir": "stagger", "frames": 3, "speed": 6,  "loop": False},
        },
        "health_mult": 0.8,
        "damage_mult": 1.2,
        "speed_mult": 0.9,
        "unlock_wave": 2,
        "stagger_frames": 12,
        "attack_startup": 6,
        "attack_active": 3,
        "attack_recovery": 8,
    },
    "shadow_bat": {
        "display_name": "Shadow Bat",
        "sprite_dir": "shadow_bat",
        "animations": {
            "idle":    {"dir": "hover",   "frames": 4, "speed": 8,  "loop": True},
            "walk":    {"dir": "fly",     "frames": 8, "speed": 6,  "loop": True},
            "attack":  {"dir": "dive",    "frames": 4, "speed": 4,  "loop": False},
            "die":     {"dir": "die",     "frames": 4, "speed": 8,  "loop": False},
        },
        "health_mult": 0.5,
        "damage_mult": 0.8,
        "speed_mult": 1.5,
        "unlock_wave": 3,
        "stagger_frames": 8,
        "attack_startup": 4,
        "attack_active": 3,
        "attack_recovery": 6,
    },
}

# Wave → available enemy types (progressive unlock)
def get_enemy_types_for_wave(wave):
    """Return list of enemy type keys available at the given wave."""
    return [k for k, v in ENEMY_TYPES.items() if v.get('unlock_wave', 1) <= wave]
