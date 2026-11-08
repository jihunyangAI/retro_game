# ==========================================
# 우주 방어 게임 (Space Defender) - 환경 설정 파일
# 게임의 화면 크기, 색상, 속도, 난이도 수치를 한곳에서 관리합니다.
# ==========================================

# 1. 화면 및 프레임 설정
SCREEN_WIDTH = 800          # 화면 가로 크기 (픽셀)
SCREEN_HEIGHT = 600         # 화면 세로 크기 (픽셀)
FPS = 60                    # 초당 프레임 수 (게임 진행 속도 기준)
GAME_TITLE = "우주 방어 게임 (Space Defender)"

# 2. 색상 정의 (RGB 값: 빨강, 초록, 파랑)
COLOR_BLACK = (0, 0, 0)         # 배경색: 검정 (우주 공간)
COLOR_WHITE = (255, 255, 255)   # 기본 글자색: 흰색
COLOR_GREEN = (0, 255, 0)       # 플레이어 색상: 초록색
COLOR_RED = (255, 50, 50)       # 적(외계인) 색상: 빨간색
COLOR_YELLOW = (255, 255, 0)    # 플레이어 미사일 색상: 노란색
COLOR_ORANGE = (255, 140, 0)    # 적 총알 색상: 주황색
COLOR_CYAN = (0, 255, 255)      # 승리 메시지 강조 색상: 청록색

# 3. 플레이어 설정
PLAYER_WIDTH = 36           # 플레이어 가로 길이 (기존 52에서 축소하여 날렵하게 조정)
PLAYER_HEIGHT = 34          # 플레이어 세로 길이 (기존 48에서 축소)
PLAYER_SPEED = 6            # 플레이어 좌우 이동 속도
PLAYER_COOLDOWN = 400       # 미사일 발사 쿨타임 (밀리초 단위: 400ms = 0.4초)
PLAYER_INITIAL_LIVES = 3    # 게임 시작 시 기본 생명 개수 (3개)
PLAYER_INVINCIBLE_MS = 1200 # 피격 후 일시 무적 시간 (밀리초 단위: 1.2초)

# 4. 점수 및 랭킹 설정
ENEMY_ROW_SCORES = {
    0: 300,                 # 1열(맨 위) 대장/UFO 외계인 격추 점수
    1: 200,                 # 2열(가운데) 전투/중장갑 외계인 격추 점수
    2: 100,                 # 3열(맨 아래) 정찰 외계인 격추 점수
}
LIFE_BONUS_SCORE = 500      # 승리 시 남은 생명 1개당 추가 보너스 점수
RANKING_FILE = "rankings.json"  # 영구 랭킹 저장 파일명
MAX_RANKINGS = 5            # 화면에 표시할 최대 랭킹 순위 수 (TOP 5)

# 5. 적(외계인) 군단 설정 (3줄 x 8칸 = 24마리)
ENEMY_ROWS = 3              # 적 배치 줄 수 (행)
ENEMY_COLS = 8              # 한 줄당 적의 수 (열)
ENEMY_WIDTH = 38            # 적 가로 길이 (기존 52에서 축소하여 비율 맞춤)
ENEMY_HEIGHT = 30           # 적 세로 길이 (기존 40에서 축소)
ENEMY_H_SPACE = 75          # 적 좌우 간격
ENEMY_V_SPACE = 55          # 적 상하 간격
ENEMY_START_X = 110         # 첫 번째 적 생성 시작 X 좌표
ENEMY_START_Y = 70          # 첫 번째 적 생성 시작 Y 좌표
ENEMY_SPEED_X = 2           # 적 군단 기본 좌우 이동 속도
ENEMY_DROP_Y = 25           # 화면 끝에 닿았을 때 아래로 내려오는 거리
ENEMY_SHOOT_INTERVAL = 900  # 적이 총알을 쏘는 주기 (밀리초 단위: 900ms = 0.9초)

# 5. 미사일 및 총알 설정
BULLET_WIDTH = 6            # 총알 가로 길이
BULLET_HEIGHT = 16          # 총알 세로 길이
PLAYER_BULLET_SPEED = -8    # 플레이어 미사일 속도 (위로 올라가므로 음수)
ENEMY_BULLET_SPEED = 5      # 적 총알 속도 (아래로 내려오므로 양수)
