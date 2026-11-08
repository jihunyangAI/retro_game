# ==========================================
# 우주 방어 게임 (Space Defender) - 레트로 사운드 생성 및 재생 모듈
# 외부 음원 없이 파이썬 기본 라이브러리로 8비트 오락실 효과음(WAV)을
# assets/sounds/ 폴더에 자동 생성하고 재생합니다.
# ==========================================

import os
import sys
import math
import wave
import struct
import random
import pygame

BASE_DIR = getattr(sys, "_MEIPASS", os.path.dirname(os.path.abspath(__file__)))
SOUNDS_DIR = os.path.join(BASE_DIR, "assets", "sounds")
SAMPLE_RATE = 22050


def _save_wav(filepath, samples):
    """생성된 오디오 샘플 리스트(-1.0 ~ 1.0)를 16비트 모노 WAV 파일로 저장합니다."""
    os.makedirs(os.path.dirname(filepath), exist_ok=True)
    with wave.open(filepath, "w") as wav_file:
        wav_file.setnchannels(1)
        wav_file.setsampwidth(2)
        wav_file.setframerate(SAMPLE_RATE)
        frames = bytearray()
        for s in samples:
            clamped = max(-1.0, min(1.0, s))
            frames.extend(struct.pack("<h", int(clamped * 32767)))
        wav_file.writeframes(frames)


def _generate_laser_samples():
    """플레이어 미사일 발사음: 고음에서 저음으로 빠르게 떨어지는 레트로 레이저 '쓔웅!' 사운드"""
    duration = 0.14
    num_samples = int(SAMPLE_RATE * duration)
    samples = []
    phase = 0.0
    for i in range(num_samples):
        t = i / num_samples
        # 주파수가 1100Hz에서 220Hz로 빠르게 하강
        freq = 1100.0 * ((1.0 - t) ** 1.6) + 180.0
        phase += 2.0 * math.pi * freq / SAMPLE_RATE
        # 사각파(Square)와 사인파 혼합으로 8비트 질감 표현
        wave_val = 0.6 * (1.0 if math.sin(phase) >= 0 else -1.0) + 0.4 * math.sin(phase)
        envelope = (1.0 - t) ** 0.8
        samples.append(wave_val * envelope * 0.35)
    return samples


def _generate_explosion_samples(duration=0.32, pitch_scale=1.0):
    """적 격추 및 피격 폭발음: 묵직한 저음 진동과 노이즈가 섞인 오락실 '쾅!' 폭발 사운드"""
    num_samples = int(SAMPLE_RATE * duration)
    samples = []
    rng = random.Random(42)
    phase = 0.0
    last_noise = 0.0
    for i in range(num_samples):
        t = i / num_samples
        # 저음 럼블 주파수 (140Hz -> 35Hz)
        freq = (140.0 * ((1.0 - t) ** 1.4) + 35.0) * pitch_scale
        phase += 2.0 * math.pi * freq / SAMPLE_RATE
        rumble = math.sin(phase)

        # 레트로 크런치 노이즈 (일정 주기로 샘플 홀드)
        if i % max(1, int(4 / pitch_scale)) == 0:
            last_noise = rng.uniform(-1.0, 1.0)

        envelope = (1.0 - t) ** 1.5
        val = (0.55 * last_noise + 0.45 * rumble) * envelope * 0.5
        samples.append(val)
    return samples


def _generate_melody_samples(notes, note_duration=0.11, volume=0.35):
    """음계 주파수 리스트를 받아 8비트 아케이드 멜로디(승리/패배/시작음)를 생성합니다."""
    samples = []
    for freq, dur_mult in notes:
        num_samples = int(SAMPLE_RATE * note_duration * dur_mult)
        phase = 0.0
        for i in range(num_samples):
            t = i / num_samples
            if freq <= 0:
                samples.append(0.0)
                continue
            phase += 2.0 * math.pi * freq / SAMPLE_RATE
            square = 1.0 if math.sin(phase) >= 0 else -1.0
            tri = (2.0 / math.pi) * math.asin(math.sin(phase))
            envelope = min(1.0, (1.0 - t) * 4.0)
            samples.append((0.5 * square + 0.5 * tri) * envelope * volume)
    return samples


class SoundManager:
    """게임 내 모든 효과음을 생성, 로드 및 재생하는 사운드 매니저"""

    def __init__(self):
        self.enabled = False
        self.sounds = {}

        try:
            if not pygame.mixer.get_init():
                pygame.mixer.init(frequency=SAMPLE_RATE, size=-16, channels=1, buffer=512)
            self.enabled = True
            self._ensure_sound_files()
            self._load_sounds()
        except Exception as e:
            print(f"사운드 초기화 실패 (음소거 모드로 진행): {e}", flush=True)
            self.enabled = False

    def _ensure_sound_files(self):
        """assets/sounds 폴더에 효과음 WAV 파일이 없으면 자동 생성합니다."""
        os.makedirs(SOUNDS_DIR, exist_ok=True)

        sound_recipes = {
            "shoot.wav": lambda: _generate_laser_samples(),
            "explosion.wav": lambda: _generate_explosion_samples(0.28, 1.0),
            "player_explosion.wav": lambda: _generate_explosion_samples(0.55, 0.65),
            "start.wav": lambda: _generate_melody_samples(
                [(587.33, 0.8), (880.0, 1.5)], note_duration=0.09
            ),
            "victory.wav": lambda: _generate_melody_samples(
                [(523.25, 1.0), (659.25, 1.0), (783.99, 1.0), (1046.50, 2.5)],
                note_duration=0.12,
            ),
            "gameover.wav": lambda: _generate_melody_samples(
                [(392.00, 1.2), (369.99, 1.2), (349.23, 1.2), (329.63, 2.8)],
                note_duration=0.14,
            ),
        }

        for filename, generator in sound_recipes.items():
            path = os.path.join(SOUNDS_DIR, filename)
            if not os.path.exists(path):
                _save_wav(path, generator())

    def _load_sounds(self):
        """생성된 WAV 파일들을 메모리에 불러옵니다."""
        for key in ("shoot", "explosion", "player_explosion", "start", "victory", "gameover"):
            path = os.path.join(SOUNDS_DIR, f"{key}.wav")
            if os.path.exists(path):
                self.sounds[key] = pygame.mixer.Sound(path)

    def play(self, key):
        """지정한 이름의 효과음을 재생합니다."""
        if self.enabled and key in self.sounds:
            self.sounds[key].play()
