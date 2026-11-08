# ==========================================
# 우주 방어 게임 (Space Defender) - 게임 오브젝트(스프라이트) 파일
# 플레이어 우주선, 줄별 외계인(1~3열), 레이저 총알, 폭발 이펙트를 정의합니다.
# ==========================================

import os
import sys
import math
import random
import pygame
from settings import (
    SCREEN_WIDTH,
    SCREEN_HEIGHT,
    COLOR_GREEN,
    COLOR_RED,
    PLAYER_WIDTH,
    PLAYER_HEIGHT,
    PLAYER_SPEED,
    PLAYER_COOLDOWN,
    PLAYER_INVINCIBLE_MS,
    ENEMY_ROW_SCORES,
    ENEMY_WIDTH,
    ENEMY_HEIGHT,
    BULLET_WIDTH,
    BULLET_HEIGHT,
    PLAYER_BULLET_SPEED,
    COLOR_YELLOW,
)

# 프로젝트 내 assets 폴더 경로 (PyInstaller EXE 번들 환경 지원)
BASE_DIR = getattr(sys, "_MEIPASS", os.path.dirname(os.path.abspath(__file__)))
ASSETS_DIR = os.path.join(BASE_DIR, "assets")

# 캐시된 스프라이트 이미지 (매번 디스크에서 다시 읽지 않도록 메모리에 보관)
_SPRITE_CACHE = {}


def load_sprite_image(relative_path, target_size):
    """assets 하위 폴더(player, enemy, background)에서 투명 PNG 스프라이트 이미지를 불러와 크기를 맞춥니다."""
    cache_key = (relative_path, target_size)
    if cache_key in _SPRITE_CACHE:
        return _SPRITE_CACHE[cache_key]

    img_path = os.path.join(ASSETS_DIR, relative_path)
    try:
        if os.path.exists(img_path):
            img = pygame.image.load(img_path).convert_alpha()
            scaled = pygame.transform.smoothscale(img, target_size)
            _SPRITE_CACHE[cache_key] = scaled
            return scaled
    except Exception as e:
        print(f"스프라이트 이미지 로드 오류 ({relative_path}): {e}", flush=True)

    return None


class Bullet(pygame.sprite.Sprite):
    """플레이어의 미사일 및 적의 총알을 나타내는 클래스"""

    def __init__(self, x, y, speed_y, color, is_player=True):
        super().__init__()
        bullet_file = (
            os.path.join("player", "bullet_player.png")
            if is_player
            else os.path.join("enemy", "bullet_enemy.png")
        )
        sprite_img = load_sprite_image(
            bullet_file, (BULLET_WIDTH + 4, BULLET_HEIGHT + 4)
        )

        if sprite_img is not None:
            self.image = sprite_img
        else:
            # 이미지가 없을 경우 기본 레이저 사각형 사용
            self.image = pygame.Surface(
                (BULLET_WIDTH, BULLET_HEIGHT), pygame.SRCALPHA
            )
            self.image.fill(color)
            inner_rect = pygame.Rect(
                1, 2, max(1, BULLET_WIDTH - 2), max(1, BULLET_HEIGHT - 4)
            )
            pygame.draw.rect(self.image, (255, 255, 255), inner_rect)

        self.rect = self.image.get_rect(center=(x, y))
        self.speed_y = speed_y

    def update(self):
        """매 프레임마다 총알을 위 또는 아래로 이동시킵니다."""
        self.rect.y += self.speed_y

        # 화면 위쪽이나 아래쪽 밖으로 벗어나면 메모리에서 자동 삭제
        if self.rect.bottom < 0 or self.rect.top > SCREEN_HEIGHT:
            self.kill()


class Explosion(pygame.sprite.Sprite):
    """
    적이나 플레이어가 피격되었을 때 자연스러운 다단계 애니메이션으로 터지는 폭발 이펙트 클래스
    - 1단계 (0~30%): 중심부 섬광과 함께 폭발 이미지가 작게 시작해 빠르게 팽창
    - 2단계 (30~70%): 폭발 충격파 원형 링과 도트 불꽃 파편(파티클)이 사방으로 확산
    - 3단계 (70~100%): 폭발 화염과 파편이 서서히 투명해지며(페이드 아웃) 소멸
    """

    def __init__(self, center_pos, size=(52, 52), duration_ms=420):
        super().__init__()
        self.center_pos = center_pos
        self.base_size = size
        self.duration_ms = duration_ms
        self.spawn_time = pygame.time.get_ticks()

        # 원본 폭발 스프라이트 이미지 불러오기
        self.base_sprite = load_sprite_image(
            os.path.join("player", "explosion.png"), size
        )

        # 사방으로 튀는 도트 파편(파티클) 14개 무작위 생성
        self.particles = []
        for _ in range(14):
            angle = random.uniform(0, 2 * math.pi)
            speed = random.uniform(12.0, size[0] * 0.65)
            p_size = random.choice([3, 4, 5])
            color = random.choice(
                [
                    (255, 255, 180),  # 밝은 노랑
                    (255, 200, 50),   # 황금빛 주황
                    (255, 110, 20),   # 화염 주황
                    (255, 50, 30),    # 진한 빨강
                ]
            )
            self.particles.append((angle, speed, p_size, color))

        # 파편과 충격파가 잘리지 않도록 넉넉한 캔버스 크기 확보
        canvas_w = int(size[0] * 1.8)
        canvas_h = int(size[1] * 1.8)
        self.canvas_size = (canvas_w, canvas_h)
        self.image = pygame.Surface(self.canvas_size, pygame.SRCALPHA)
        self.rect = self.image.get_rect(center=center_pos)

        # 첫 프레임 즉시 렌더링
        self._render_frame(0.0)

    def _render_frame(self, progress):
        """진행도(0.0 ~ 1.0)에 맞춰 현재 폭발 애니메이션 프레임을 그립니다."""
        self.image.fill((0, 0, 0, 0))
        cx = self.canvas_size[0] // 2
        cy = self.canvas_size[1] // 2

        # 1. 폭발 본체 크기 및 투명도 계산
        if progress < 0.25:
            # 초반 25%: 0.35배 크기에서 1.1배 크기로 급격히 팽창
            scale = 0.35 + (progress / 0.25) * 0.75
            alpha = 255
        else:
            # 이후 75%: 서서히 퍼지며 투명도가 255 -> 0으로 감소
            fade_t = (progress - 0.25) / 0.75
            scale = 1.1 + fade_t * 0.15
            alpha = max(0, int(255 * ((1.0 - fade_t) ** 1.3)))

        if self.base_sprite is not None and alpha > 0:
            cur_w = max(4, int(self.base_size[0] * scale))
            cur_h = max(4, int(self.base_size[1] * scale))
            scaled_img = pygame.transform.smoothscale(
                self.base_sprite, (cur_w, cur_h)
            )
            # 자연스러운 역동감을 위해 시간에 따라 미세하게 회전
            rotated_img = pygame.transform.rotate(scaled_img, progress * 35.0)
            rotated_img.set_alpha(alpha)
            img_rect = rotated_img.get_rect(center=(cx, cy))
            self.image.blit(rotated_img, img_rect)

        # 2. 초기 중심부 백색/황색 섬광 (0 ~ 30% 구간)
        if progress < 0.30:
            flash_ratio = 1.0 - (progress / 0.30)
            flash_radius = max(2, int(self.base_size[0] * 0.35 * flash_ratio))
            flash_surf = pygame.Surface(self.canvas_size, pygame.SRCALPHA)
            pygame.draw.circle(
                flash_surf,
                (255, 255, 220, int(220 * flash_ratio)),
                (cx, cy),
                flash_radius,
            )
            self.image.blit(flash_surf, (0, 0))

        # 3. 퍼져나가는 충격파 링 (10% ~ 85% 구간)
        if 0.10 <= progress <= 0.85:
            ring_t = (progress - 0.10) / 0.75
            ring_radius = int(self.base_size[0] * (0.25 + ring_t * 0.55))
            ring_alpha = max(0, int(190 * (1.0 - ring_t)))
            if ring_radius > 3 and ring_alpha > 0:
                pygame.draw.circle(
                    self.image,
                    (255, 180, 50, ring_alpha),
                    (cx, cy),
                    ring_radius,
                    width=2,
                )

        # 4. 사방으로 튀는 도트 불꽃 파편 (전체 구간)
        p_alpha = max(0, int(255 * (1.0 - progress ** 1.4)))
        if p_alpha > 0:
            # 감속 곡선 적용 (초반에 빠르게 튀어나가고 후반에 느려짐)
            dist_factor = 1.0 - ((1.0 - progress) ** 2.2)
            for angle, speed, p_size, color in self.particles:
                px = int(cx + math.cos(angle) * speed * dist_factor)
                py = int(cy + math.sin(angle) * speed * dist_factor)
                cur_p_size = max(1, int(p_size * (1.0 - progress * 0.5)))
                pygame.draw.rect(
                    self.image,
                    (*color, p_alpha),
                    (px - cur_p_size // 2, py - cur_p_size // 2, cur_p_size, cur_p_size),
                )

    def update(self):
        """매 프레임마다 폭발 진행도를 계산하여 애니메이션을 갱신하고 끝나면 삭제합니다."""
        elapsed = pygame.time.get_ticks() - self.spawn_time
        if elapsed >= self.duration_ms:
            self.kill()
            return

        progress = elapsed / self.duration_ms
        self._render_frame(progress)
        self.rect = self.image.get_rect(center=self.center_pos)


class Player(pygame.sprite.Sprite):
    """플레이어가 조종하는 초록색 우주선 클래스"""

    def __init__(self):
        super().__init__()
        sprite_img = load_sprite_image(
            os.path.join("player", "player.png"), (PLAYER_WIDTH, PLAYER_HEIGHT)
        )

        if sprite_img is not None:
            self.base_image = sprite_img.copy()
        else:
            # 이미지가 없을 경우 기본 초록색 사각형 사용
            self.base_image = pygame.Surface((PLAYER_WIDTH, PLAYER_HEIGHT))
            self.base_image.fill(COLOR_GREEN)

        self.image = self.base_image.copy()

        # 초기 위치: 화면 하단 중앙
        self.rect = self.image.get_rect(
            midbottom=(SCREEN_WIDTH // 2, SCREEN_HEIGHT - 25)
        )
        self.speed = PLAYER_SPEED

        # 미사일 쿨타임 및 피격 후 무적 시간 기록
        self.last_shot_time = 0
        self.invincible_until = 0

    def is_invincible(self):
        """현재 피격 후 일시 무적 상태인지 반환합니다."""
        return pygame.time.get_ticks() < self.invincible_until

    def trigger_hit_invincibility(self):
        """생명이 깎였을 때 일정 시간(1.2초) 동안 무적 및 깜빡임 상태를 부여합니다."""
        self.invincible_until = pygame.time.get_ticks() + PLAYER_INVINCIBLE_MS

    def update(self, keys):
        """키보드 입력을 받아 플레이어를 좌우로 이동시키고 무적 깜빡임 효과를 적용합니다."""
        if keys[pygame.K_LEFT] or keys[pygame.K_a]:
            self.rect.x -= self.speed
        if keys[pygame.K_RIGHT] or keys[pygame.K_d]:
            self.rect.x += self.speed

        # 화면 왼쪽/오른쪽 끝을 벗어나지 않도록 위치 고정
        if self.rect.left < 0:
            self.rect.left = 0
        if self.rect.right > SCREEN_WIDTH:
            self.rect.right = SCREEN_WIDTH

        # 무적 시간 동안에는 빠르게 깜빡이도록 투명도(Alpha) 조절
        self.image = self.base_image.copy()
        if self.is_invincible():
            if (pygame.time.get_ticks() // 90) % 2 == 0:
                self.image.set_alpha(70)
            else:
                self.image.set_alpha(255)
        else:
            self.image.set_alpha(255)

    def can_shoot(self):
        """현재 미사일 발사 쿨타임이 지났는지 확인합니다."""
        current_time = pygame.time.get_ticks()
        return current_time - self.last_shot_time >= PLAYER_COOLDOWN

    def shoot(self):
        """쿨타임이 지났다면 플레이어 위치에서 위로 날아가는 미사일을 생성합니다."""
        if self.can_shoot():
            self.last_shot_time = pygame.time.get_ticks()
            return Bullet(
                self.rect.centerx,
                self.rect.top,
                PLAYER_BULLET_SPEED,
                COLOR_YELLOW,
                is_player=True,
            )
        return None


class Enemy(pygame.sprite.Sprite):
    """
    3x8 대형으로 움직이는 적(외계인) 클래스 (총 5종의 적군 이미지 활용)
    - 0번째 줄(맨 위): 대장 외계인 (enemy_row1.png) & 외계 UFO 전함 (enemy_ufo.png)
    - 1번째 줄(가운데): 전투 외계인 (enemy.png) & 중장갑 외계인 (enemy_heavy.png)
    - 2번째 줄(맨 아래): 정찰 외계인 (enemy_row3.png)
    """

    def __init__(self, x, y, row=1, col=0):
        super().__init__()
        self.row = row
        self.score_value = ENEMY_ROW_SCORES.get(row, 100)
        if row == 0:
            filename = "enemy_ufo.png" if col % 2 == 1 else "enemy_row1.png"
        elif row == 1:
            filename = "enemy_heavy.png" if col % 2 == 1 else "enemy.png"
        else:
            filename = "enemy_row3.png"

        img_file = os.path.join("enemy", filename)
        sprite_img = load_sprite_image(img_file, (ENEMY_WIDTH, ENEMY_HEIGHT))

        if sprite_img is not None:
            self.image = sprite_img
        else:
            # 이미지가 없을 경우 기본 빨간색 사각형 사용
            self.image = pygame.Surface((ENEMY_WIDTH, ENEMY_HEIGHT))
            self.image.fill(COLOR_RED)

        self.rect = self.image.get_rect(topleft=(x, y))

    def move_horizontal(self, dx):
        """적을 좌우로 이동시킵니다."""
        self.rect.x += dx

    def move_down(self, dy):
        """적을 아래로 한 칸 내려오게 합니다."""
        self.rect.y += dy
