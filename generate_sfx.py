"""
generate_sfx.py — Synthesize retro 8-bit/16-bit game sound effects.

Generates .wav files in Sounds/sfx/ for:
  - sword_swing.wav   (melee attack)
  - hit.wav           (enemy takes damage)
  - enemy_death.wav   (enemy killed)
  - player_hurt.wav   (player takes damage)
  - jump.wav          (player jumps)
  - dash.wav          (player dashes)
  - pickup.wav        (powerup collected)
  - arrow_fire.wav    (archer fires arrow)
  - magic_fire.wav    (mage fires spell)
  - boss_roar.wav     (boss intro / phase change)
  - fireball.wav      (boss fireball)
  - victory.wav       (boss defeated fanfare)
"""
import numpy as np
import wave
import os
import struct

SAMPLE_RATE = 22050
OUTPUT_DIR = os.path.join(os.path.dirname(__file__), "Sounds", "sfx")


def save_wav(filename, samples, sample_rate=SAMPLE_RATE):
    """Save a numpy float array [-1,1] as a 16-bit mono WAV."""
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    path = os.path.join(OUTPUT_DIR, filename)
    # Clip and convert to int16
    samples = np.clip(samples, -1.0, 1.0)
    int_samples = (samples * 32767).astype(np.int16)
    with wave.open(path, "wb") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(sample_rate)
        wf.writeframes(int_samples.tobytes())
    print(f"  ✓ {filename} ({len(samples)/sample_rate:.2f}s)")


def envelope(length, attack=0.01, decay=0.0, sustain=1.0, release=0.1):
    """ADSR envelope. Length in seconds."""
    n = int(length * SAMPLE_RATE)
    env = np.ones(n)
    a = int(attack * SAMPLE_RATE)
    r = int(release * SAMPLE_RATE)
    # Attack ramp
    if a > 0:
        env[:a] = np.linspace(0, 1, a)
    # Release ramp
    if r > 0:
        env[-r:] = np.linspace(sustain, 0, r)
    return env


def noise(length):
    """White noise."""
    return np.random.uniform(-1, 1, int(length * SAMPLE_RATE))


def sine(freq, length):
    """Sine wave."""
    t = np.linspace(0, length, int(length * SAMPLE_RATE), False)
    return np.sin(2 * np.pi * freq * t)


def square(freq, length):
    """Square wave (classic 8-bit)."""
    return np.sign(sine(freq, length))


def saw(freq, length):
    """Sawtooth wave."""
    t = np.linspace(0, length, int(length * SAMPLE_RATE), False)
    return 2 * (t * freq - np.floor(0.5 + t * freq))


def freq_sweep(f_start, f_end, length):
    """Linear frequency sweep."""
    t = np.linspace(0, length, int(length * SAMPLE_RATE), False)
    freqs = np.linspace(f_start, f_end, len(t))
    phase = np.cumsum(freqs / SAMPLE_RATE) * 2 * np.pi
    return np.sin(phase)


# ── Sound Effect Generators ──────────────────────────────────────────

def gen_sword_swing():
    """Whooshy slash sound."""
    n = noise(0.15) * envelope(0.15, attack=0.005, release=0.1)
    sweep = freq_sweep(800, 200, 0.15) * 0.3 * envelope(0.15, attack=0.005, release=0.1)
    return (n * 0.6 + sweep) * 0.8


def gen_hit():
    """Impact thud when enemy is hit."""
    thud = sine(120, 0.08) * envelope(0.08, attack=0.002, release=0.06)
    crack = noise(0.04) * envelope(0.04, attack=0.001, release=0.03)
    result = np.zeros(int(0.12 * SAMPLE_RATE))
    result[:len(thud)] += thud * 0.7
    result[:len(crack)] += crack * 0.5
    return result


def gen_enemy_death():
    """Descending pitch + noise burst."""
    sweep = freq_sweep(600, 80, 0.3) * envelope(0.3, attack=0.005, release=0.2)
    n = noise(0.15) * envelope(0.15, attack=0.002, release=0.12)
    result = np.zeros(int(0.35 * SAMPLE_RATE))
    result[:len(sweep)] += sweep * 0.6
    result[:len(n)] += n * 0.3
    return result


def gen_player_hurt():
    """Quick descending buzz."""
    buzz = square(300, 0.05) * 0.4
    buzz2 = square(200, 0.05) * 0.3
    combined = np.concatenate([buzz, buzz2])
    env = envelope(len(combined) / SAMPLE_RATE, attack=0.002, release=0.06)
    # Trim to match
    n = min(len(combined), len(env))
    return combined[:n] * env[:n]


def gen_jump():
    """Quick ascending chirp."""
    sweep = freq_sweep(200, 600, 0.12) * envelope(0.12, attack=0.005, release=0.08)
    return sweep * 0.5


def gen_dash():
    """Fast whoosh."""
    n = noise(0.1) * envelope(0.1, attack=0.005, release=0.08)
    sweep = freq_sweep(400, 100, 0.1) * 0.2 * envelope(0.1, attack=0.005, release=0.08)
    return (n * 0.5 + sweep) * 0.7


def gen_pickup():
    """Ascending chime — coin/powerup collect."""
    note1 = sine(523, 0.06) * envelope(0.06, attack=0.002, release=0.04)  # C5
    note2 = sine(659, 0.06) * envelope(0.06, attack=0.002, release=0.04)  # E5
    note3 = sine(784, 0.1) * envelope(0.1, attack=0.002, release=0.08)    # G5
    gap = np.zeros(int(0.02 * SAMPLE_RATE))
    return np.concatenate([note1, gap, note2, gap, note3]) * 0.6


def gen_arrow_fire():
    """Twang + whoosh."""
    twang = sine(800, 0.04) * envelope(0.04, attack=0.001, release=0.03)
    whoosh = noise(0.1) * envelope(0.1, attack=0.01, release=0.08)
    result = np.zeros(int(0.14 * SAMPLE_RATE))
    result[:len(twang)] += twang * 0.5
    result[int(0.02 * SAMPLE_RATE):int(0.02 * SAMPLE_RATE) + len(whoosh)] += whoosh * 0.3
    return result


def gen_magic_fire():
    """Shimmery magic cast."""
    shimmer = sine(1200, 0.2) * envelope(0.2, attack=0.01, release=0.15)
    sweep = freq_sweep(600, 1500, 0.15) * 0.3 * envelope(0.15, attack=0.01, release=0.12)
    sparkle = noise(0.1) * 0.15 * envelope(0.1, attack=0.005, release=0.08)
    result = np.zeros(int(0.25 * SAMPLE_RATE))
    result[:len(shimmer)] += shimmer * 0.4
    result[:len(sweep)] += sweep
    result[:len(sparkle)] += sparkle
    return result


def gen_boss_roar():
    """Low rumbling roar with distortion."""
    low = saw(60, 0.6) * envelope(0.6, attack=0.05, release=0.4)
    mid = saw(90, 0.5) * envelope(0.5, attack=0.08, release=0.3) * 0.5
    rumble = noise(0.6) * 0.2 * envelope(0.6, attack=0.05, release=0.4)
    result = np.zeros(int(0.7 * SAMPLE_RATE))
    result[:len(low)] += low * 0.5
    result[:len(mid)] += mid * 0.4
    result[:len(rumble)] += rumble
    # Soft clip for distortion
    result = np.tanh(result * 2) * 0.7
    return result


def gen_fireball():
    """Whooshing fire projectile."""
    sweep = freq_sweep(300, 100, 0.2) * envelope(0.2, attack=0.01, release=0.15)
    crackle = noise(0.15) * 0.25 * envelope(0.15, attack=0.01, release=0.12)
    result = np.zeros(int(0.25 * SAMPLE_RATE))
    result[:len(sweep)] += sweep * 0.5
    result[:len(crackle)] += crackle
    return result


def gen_victory():
    """Short victory fanfare — ascending major arpeggio."""
    notes = [523, 659, 784, 1047]  # C5 E5 G5 C6
    parts = []
    for freq in notes:
        note = (sine(freq, 0.12) * 0.4 + square(freq, 0.12) * 0.2)
        note *= envelope(0.12, attack=0.005, release=0.08)
        parts.append(note)
        parts.append(np.zeros(int(0.03 * SAMPLE_RATE)))
    # Final sustained note
    final = (sine(1047, 0.4) * 0.4 + sine(1319, 0.4) * 0.2)
    final *= envelope(0.4, attack=0.01, release=0.3)
    parts.append(final)
    return np.concatenate(parts) * 0.7


if __name__ == "__main__":
    print("Generating retro SFX...")
    save_wav("sword_swing.wav", gen_sword_swing())
    save_wav("hit.wav", gen_hit())
    save_wav("enemy_death.wav", gen_enemy_death())
    save_wav("player_hurt.wav", gen_player_hurt())
    save_wav("jump.wav", gen_jump())
    save_wav("dash.wav", gen_dash())
    save_wav("pickup.wav", gen_pickup())
    save_wav("arrow_fire.wav", gen_arrow_fire())
    save_wav("magic_fire.wav", gen_magic_fire())
    save_wav("boss_roar.wav", gen_boss_roar())
    save_wav("fireball.wav", gen_fireball())
    save_wav("victory.wav", gen_victory())
    print(f"\nAll SFX saved to {OUTPUT_DIR}/")
