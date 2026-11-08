# ==========================================
# 우주 방어 게임 (Space Defender) - 메인 실행 파일
# 생명(3개) 시스템, 점수 계산, 알파벳 3글자 이니셜 입력 및 영구 랭킹 보드,
# 3x8 적 군단 제어, 충돌/폭발 애니메이션 및 사운드를 총괄합니다.
# ==========================================

import os
import sys
import ctypes
import random
import pygame

from settings import (
    SCREEN_WIDTH,
    SCREEN_HEIGHT,
    FPS,
    GAME_TITLE,
    COLOR_BLACK,
    COLOR_WHITE,
    COLOR_GREEN,
    COLOR_RED,
    COLOR_YELLOW,
    COLOR_CYAN,
    COLOR_ORANGE,
    PLAYER_INITIAL_LIVES,
    LIFE_BONUS_SCORE,
    ENEMY_ROWS,
    ENEMY_COLS,
    ENEMY_H_SPACE,
    ENEMY_V_SPACE,
    ENEMY_START_X,
    ENEMY_START_Y,
    ENEMY_SPEED_X,
    ENEMY_DROP_Y,
    ENEMY_SHOOT_INTERVAL,
    ENEMY_BULLET_SPEED,
)
from sprites import Player, Enemy, Bullet, Explosion, load_sprite_image
from sounds import SoundManager
from ranking import load_rankings, save_ranking


def get_korean_font(size):
    """윈도우 기본 한글 폰트(맑은 고딕 등)를 빠르게 불러옵니다."""
    font_paths = [
        r"C:\Windows\Fonts\malgunbd.ttf",
        r"C:\Windows\Fonts\malgun.ttf",
        r"C:\Windows\Fonts\gulim.ttc",
    ]
    for path in font_paths:
        if os.path.exists(path):
            return pygame.font.Font(path, size)
    # 기본 경로에 없을 경우 시스템 폰트 사용
    return pygame.font.SysFont("malgungothic", size)


class SpaceDefenderGame:
    """우주 방어 게임의 전체 흐름을 관리하는 메인 클래스"""

    def __init__(self):
        pygame.init()
        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        pygame.display.set_caption(GAME_TITLE)
        self.clock = pygame.time.Clock()

        # 실행 시 게임 창을 화면 맨 앞으로 가져오기 (윈도우 환경)
        try:
            hwnd = pygame.display.get_wm_info().get("window")
            if hwnd:
                ctypes.windll.user32.ShowWindow(hwnd, 1)
                ctypes.windll.user32.SetForegroundWindow(hwnd)
        except Exception:
            pass

        # 화면 표시용 한글 폰트 설정
        self.title_font = get_korean_font(36)
        self.hud_font = get_korean_font(22)
        self.ui_font = get_korean_font(20)
        self.rank_font = get_korean_font(22)

        # 레트로 아케이드 사운드 매니저 초기화 (assets/sounds/ 폴더에 효과음 자동 생성)
        self.sound_manager = SoundManager()

        # assets/background 폴더에서 인트로 배경, 인게임 우주 배경, 승리/패배 배너 불러오기
        self.intro_image = self.load_background_image("intro_screen.jpg")
        self.game_bg_image = self.load_background_image("game_bg.jpg")
        self.victory_banner = load_sprite_image(
            os.path.join("background", "victory.png"), (340, 105)
        )
        self.gameover_banner = load_sprite_image(
            os.path.join("background", "gameover.png"), (340, 95)
        )

        # 저장된 영구 랭킹 리스트 불러오기
        self.rankings = load_rankings()

        # 게임 초기 상태 설정 (첫 시작 시에는 인트로 화면 표시)
        self.reset_game()
        self.game_state = "INTRO"
        print("게임 창이 성공적으로 열렸습니다!", flush=True)

    def load_background_image(self, filename):
        """assets/background 폴더에서 배경 이미지를 불러와 화면 크기(800x600)에 맞게 조절합니다."""
        base_dir = getattr(sys, "_MEIPASS", os.path.dirname(os.path.abspath(__file__)))
        local_img_path = os.path.join(base_dir, "assets", "background", filename)

        try:
            if os.path.exists(local_img_path):
                img = pygame.image.load(local_img_path).convert()
                return pygame.transform.smoothscale(
                    img, (SCREEN_WIDTH, SCREEN_HEIGHT)
                )
        except Exception as e:
            print(f"배경 이미지 로드 오류 ({filename}): {e}", flush=True)
        return None

    def reset_game(self):
        """게임을 처음 상태로 초기화합니다. (재시작 시 호출)"""
        # 스프라이트 그룹 생성
        self.all_sprites = pygame.sprite.Group()
        self.enemies = pygame.sprite.Group()
        self.player_bullets = pygame.sprite.Group()
        self.enemy_bullets = pygame.sprite.Group()
        self.explosions = pygame.sprite.Group()

        # 플레이어 생성 및 등록
        self.player = Player()
        self.all_sprites.add(self.player)

        # 3줄 x 8칸 적(외계인) 군단 생성 (5종 디자인 배치)
        self.create_enemy_fleet()

        # 플레이어 초기 생명(3개) 및 점수(0점) 설정
        self.lives = PLAYER_INITIAL_LIVES
        self.score = 0

        # 게임 종료 후 알파벳 3글자 이니셜 입력 상태 변수
        self.player_initials = ""
        self.name_input_done = False
        self.rankings = load_rankings()

        # 적 군단 이동 방향 (1: 오른쪽, -1: 왼쪽)
        self.enemy_direction = 1
        self.last_enemy_shot_time = pygame.time.get_ticks()

        # 게임 진행 상태 ("PLAYING": 진행 중, "VICTORY": 승리, "GAME_OVER": 패배)
        self.game_state = "PLAYING"

    def create_enemy_fleet(self):
        """화면 상단에 3줄 x 8칸 대형으로 총 24마리의 적을 5종 디자인으로 생성합니다."""
        for row in range(ENEMY_ROWS):
            for col in range(ENEMY_COLS):
                x = ENEMY_START_X + col * ENEMY_H_SPACE
                y = ENEMY_START_Y + row * ENEMY_V_SPACE
                enemy = Enemy(x, y, row=row, col=col)
                self.enemies.add(enemy)
                self.all_sprites.add(enemy)

    def handle_events(self):
        """키보드 입력 및 창 닫기 이벤트를 처리합니다."""
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()

            if event.type == pygame.KEYDOWN:
                # ESC 키를 누르면 즉시 게임 종료
                if event.key == pygame.K_ESCAPE:
                    pygame.quit()
                    sys.exit()

                # 1. 인트로 화면에서 스페이스바 또는 엔터를 누르면 게임 시작
                if self.game_state == "INTRO" and event.key in (
                    pygame.K_SPACE,
                    pygame.K_RETURN,
                ):
                    self.sound_manager.play("start")
                    self.game_state = "PLAYING"

                # 2. 게임 종료(승리/패배) 후 알파벳 3글자 이니셜 입력 단계
                elif self.game_state in ("VICTORY", "GAME_OVER") and not self.name_input_done:
                    if event.key == pygame.K_BACKSPACE:
                        self.player_initials = self.player_initials[:-1]
                    elif event.key in (pygame.K_RETURN, pygame.K_KP_ENTER):
                        # 3글자를 모두 입력했을 때 엔터를 누르면 랭킹 저장 완료
                        if len(self.player_initials) == 3:
                            self.sound_manager.play("start")
                            self.rankings = save_ranking(
                                self.player_initials, self.score
                            )
                            self.name_input_done = True
                    else:
                        # 알파벳(A~Z) 키 입력만 허용하여 최대 3글자까지 추가
                        char = event.unicode.upper()
                        if (
                            len(char) == 1
                            and "A" <= char <= "Z"
                            and len(self.player_initials) < 3
                        ):
                            self.player_initials += char
                            self.sound_manager.play("shoot")

                # 3. 이니셜 입력 및 랭킹 등록 완료 후 R 키를 누르면 게임 재시작
                elif (
                    self.game_state in ("VICTORY", "GAME_OVER")
                    and self.name_input_done
                    and event.key == pygame.K_r
                ):
                    self.sound_manager.play("start")
                    self.reset_game()

    def update_enemies(self):
        """적 군단 전체를 좌우로 움직이고, 화면 끝에 닿으면 한 칸 내리고 방향을 바꿉니다."""
        move_dx = ENEMY_SPEED_X * self.enemy_direction
        hit_wall = False

        # 1. 모든 적을 현재 방향으로 이동시키면서 벽에 닿았는지 검사
        for enemy in self.enemies:
            enemy.move_horizontal(move_dx)
            if enemy.rect.right >= SCREEN_WIDTH or enemy.rect.left <= 0:
                hit_wall = True

        # 2. 한 마리라도 화면 양 끝에 닿았다면, 전체 적을 한 칸 내리고 방향 반전
        if hit_wall:
            self.enemy_direction *= -1
            for enemy in self.enemies:
                enemy.move_down(ENEMY_DROP_Y)

        # 3. 일정 시간마다 살아있는 적 중 무작위 한 마리가 아래로 총알 발사
        current_time = pygame.time.get_ticks()
        if (
            self.enemies
            and current_time - self.last_enemy_shot_time >= ENEMY_SHOOT_INTERVAL
        ):
            self.last_enemy_shot_time = current_time
            shooter = random.choice(self.enemies.sprites())
            enemy_bullet = Bullet(
                shooter.rect.centerx,
                shooter.rect.bottom,
                ENEMY_BULLET_SPEED,
                COLOR_ORANGE,
                is_player=False,
            )
            self.enemy_bullets.add(enemy_bullet)
            self.all_sprites.add(enemy_bullet)

    def spawn_explosion(self, center_pos, size=(48, 48)):
        """지정한 위치에 다단계 도트 폭발 애니메이션을 생성합니다."""
        explosion = Explosion(center_pos, size=size)
        self.explosions.add(explosion)
        self.all_sprites.add(explosion)

    def check_collisions(self):
        """미사일 격추(점수 획득) 및 플레이어 피격(생명 차감 및 승패)을 판정합니다."""
        # 1. 플레이어 미사일과 적의 충돌 판정 (맞은 적 위치에 폭발 애니메이션 + 점수 획득)
        hits = pygame.sprite.groupcollide(
            self.enemies, self.player_bullets, True, True
        )
        if hits:
            self.sound_manager.play("explosion")
            for hit_enemy in hits:
                self.score += hit_enemy.score_value
                self.spawn_explosion(hit_enemy.rect.center, size=(48, 48))

        # 모든 적을 격추했다면 남은 생명 보너스 점수 합산 후 승리!
        if len(self.enemies) == 0:
            self.score += self.lives * LIFE_BONUS_SCORE
            self.sound_manager.play("victory")
            self.game_state = "VICTORY"
            return

        # 2. 적의 총알에 플레이어가 맞았는지 판정 (생명 1개씩 차감)
        bullet_hits = pygame.sprite.spritecollide(
            self.player, self.enemy_bullets, True
        )
        if bullet_hits and not self.player.is_invincible():
            self.lives -= 1
            if self.lives > 0:
                # 아직 생명이 남아있다면 소형 피격 폭발 + 1.2초 무적 깜빡임 부여
                self.spawn_explosion(self.player.rect.center, size=(44, 44))
                self.sound_manager.play("explosion")
                self.player.trigger_hit_invincibility()
            else:
                # 생명이 모두 소진(0개)되면 대형 폭발 후 게임오버!
                self.lives = 0
                self.spawn_explosion(self.player.rect.center, size=(68, 68))
                self.player.kill()
                self.sound_manager.play("player_explosion")
                self.sound_manager.play("gameover")
                self.game_state = "GAME_OVER"
                return

        # 3. 적 본체가 플레이어 위치까지 침공했는지 판정 (침공 허용 시 즉시 게임오버)
        for enemy in self.enemies:
            if (
                enemy.rect.colliderect(self.player.rect)
                or enemy.rect.bottom >= self.player.rect.top
            ):
                self.lives = 0
                self.spawn_explosion(self.player.rect.center, size=(68, 68))
                self.player.kill()
                self.sound_manager.play("player_explosion")
                self.sound_manager.play("gameover")
                self.game_state = "GAME_OVER"
                return

    def update(self):
        """매 프레임의 상태를 업데이트합니다."""
        # 폭발 애니메이션은 승패 결정 직후에도 자연스럽게 이어지도록 항상 업데이트
        self.explosions.update()

        if self.game_state != "PLAYING":
            return

        # 현재 눌려있는 키 상태 확인
        keys = pygame.key.get_pressed()
        self.player.update(keys)

        # 스페이스바를 누르면 플레이어 미사일 발사 + 비프/레이저 발사음 재생
        if keys[pygame.K_SPACE]:
            bullet = self.player.shoot()
            if bullet:
                self.sound_manager.play("shoot")
                self.player_bullets.add(bullet)
                self.all_sprites.add(bullet)

        # 미사일 및 총알 이동 업데이트
        self.player_bullets.update()
        self.enemy_bullets.update()

        # 적 군단 이동 및 공격 업데이트
        self.update_enemies()

        # 충돌 및 승패 판정
        self.check_collisions()

    def draw_hud(self):
        """화면 상단 좌측(점수/남은 적)과 우측 상단(생명 숫자)을 그립니다."""
        # 왼쪽 상단: 점수 및 남은 외계인 수 표시
        left_text = self.hud_font.render(
            f"점수: {self.score:,}점   |   남은 외계인: {len(self.enemies)}마리",
            True,
            COLOR_WHITE,
        )
        self.screen.blit(left_text, (20, 14))

        # 오른쪽 상단: 남은 생명 개수를 숫자로 명확히 표시 (생명 수에 따라 색상 변화)
        if self.lives >= 3:
            life_color = COLOR_GREEN
        elif self.lives == 2:
            life_color = COLOR_YELLOW
        else:
            life_color = COLOR_RED

        life_text = self.hud_font.render(f"생명: {self.lives}", True, life_color)
        life_rect = life_text.get_rect(topright=(SCREEN_WIDTH - 24, 14))
        self.screen.blit(life_text, life_rect)

    def draw_end_screen(self):
        """게임 종료(승리/패배) 시 알파벳 3글자 입력창과 영구 랭킹 보드를 그립니다."""
        # 반투명 어두운 배경 오버레이
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 190))
        self.screen.blit(overlay, (0, 0))

        # 상단: VICTORY 또는 GAME OVER 배너 및 결과 문구
        if self.game_state == "VICTORY":
            if self.victory_banner:
                self.screen.blit(
                    self.victory_banner,
                    self.victory_banner.get_rect(center=(SCREEN_WIDTH // 2, 100)),
                )
            msg = f"승리! 최종 점수: {self.score:,}점 (생명 보너스 포함)"
            msg_color = COLOR_CYAN
        else:
            if self.gameover_banner:
                self.screen.blit(
                    self.gameover_banner,
                    self.gameover_banner.get_rect(center=(SCREEN_WIDTH // 2, 100)),
                )
            msg = f"게임 오버! 최종 점수: {self.score:,}점"
            msg_color = COLOR_RED

        title_surf = self.title_font.render(msg, True, msg_color)
        self.screen.blit(
            title_surf, title_surf.get_rect(center=(SCREEN_WIDTH // 2, 175))
        )

        # 단계 1: 알파벳 3글자 이니셜 입력 화면
        if not self.name_input_done:
            prompt_surf = self.ui_font.render(
                "랭킹에 등록할 알파벳 3글자 이니셜을 입력하고 [Enter]를 누르세요!",
                True,
                COLOR_WHITE,
            )
            self.screen.blit(
                prompt_surf, prompt_surf.get_rect(center=(SCREEN_WIDTH // 2, 230))
            )

            # 3글자 슬롯 표시 (예: [ A ] [ B ] [ _ ])
            slots = []
            for i in range(3):
                if i < len(self.player_initials):
                    slots.append(f" {self.player_initials[i]} ")
                else:
                    slots.append(" _ ")
            slot_str = "   ".join(slots)
            slot_surf = self.title_font.render(slot_str, True, COLOR_YELLOW)
            box_rect = slot_surf.get_rect(center=(SCREEN_WIDTH // 2, 285))
            pygame.draw.rect(
                self.screen,
                COLOR_CYAN,
                box_rect.inflate(40, 20),
                width=2,
                border_radius=8,
            )
            self.screen.blit(slot_surf, box_rect)

        # 단계 2: 이니셜 등록 완료 후 재시작 안내
        else:
            restart_surf = self.ui_font.render(
                "랭킹 등록 완료! 다시 시작하려면 [R] 키, 종료하려면 [ESC] 키를 누르세요.",
                True,
                COLOR_YELLOW,
            )
            self.screen.blit(
                restart_surf,
                restart_surf.get_rect(center=(SCREEN_WIDTH // 2, 240)),
            )

        # 하단: 명예의 전당 영구 랭킹 보드 (TOP 5)
        rank_header = self.rank_font.render(
            "=== 명예의 전당 랭킹 (TOP 5) ===", True, COLOR_CYAN
        )
        self.screen.blit(
            rank_header, rank_header.get_rect(center=(SCREEN_WIDTH // 2, 345))
        )

        if not self.rankings:
            empty_surf = self.ui_font.render(
                "아직 등록된 랭킹 기록이 없습니다.", True, COLOR_WHITE
            )
            self.screen.blit(
                empty_surf, empty_surf.get_rect(center=(SCREEN_WIDTH // 2, 395))
            )
        else:
            start_y = 385
            for idx, entry in enumerate(self.rankings[:5]):
                r_name = entry.get("name", "AAA")
                r_score = entry.get("score", 0)
                # 방금 등록한 내 기록이면 노란색으로 강조
                is_current = (
                    self.name_input_done
                    and r_name == self.player_initials
                    and r_score == self.score
                )
                row_color = COLOR_YELLOW if is_current else COLOR_WHITE
                row_str = f"{idx + 1}위.   {r_name}   ............   {r_score:,}점"
                row_surf = self.rank_font.render(row_str, True, row_color)
                self.screen.blit(
                    row_surf,
                    row_surf.get_rect(center=(SCREEN_WIDTH // 2, start_y + idx * 34)),
                )

    def draw(self):
        """화면에 배경, 모든 캐릭터/총알, UI 텍스트를 그립니다."""
        self.screen.fill(COLOR_BLACK)

        # 인트로 화면 상태일 때 인트로 배경 이미지를 화면 가득 출력
        if self.game_state == "INTRO":
            if self.intro_image:
                self.screen.blit(self.intro_image, (0, 0))
            else:
                title_surf = self.title_font.render(
                    "우주 방어 게임 (SPACE DEFENDER)", True, COLOR_CYAN
                )
                sub_surf = self.ui_font.render(
                    "시작하려면 [스페이스바]를 누르세요", True, COLOR_WHITE
                )
                self.screen.blit(
                    title_surf,
                    title_surf.get_rect(
                        center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 - 20)
                    ),
                )
                self.screen.blit(
                    sub_surf,
                    sub_surf.get_rect(
                        center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 + 35)
                    ),
                )
        else:
            if self.game_bg_image:
                self.screen.blit(self.game_bg_image, (0, 0))
            self.all_sprites.draw(self.screen)
            self.draw_hud()

            if self.game_state in ("VICTORY", "GAME_OVER"):
                self.draw_end_screen()

        pygame.display.flip()

    def run(self):
        """게임의 메인 루프를 실행합니다."""
        while True:
            self.handle_events()
            self.update()
            self.draw()
            self.clock.tick(FPS)


if __name__ == "__main__":
    game = SpaceDefenderGame()
    game.run()
