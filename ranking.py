# ==========================================
# 우주 방어 게임 (Space Defender) - 영구 랭킹 관리 모듈
# 알파벳 3글자 이니셜과 점수를 JSON 파일(rankings.json)에 저장하고
# 게임을 다시 켜도 랭킹 기록이 유지되도록 관리합니다.
# ==========================================

import os
import sys
import json
from settings import RANKING_FILE, MAX_RANKINGS

# EXE 배포 파일로 실행될 때는 EXE 파일이 있는 폴더에 랭킹을 영구 저장
if getattr(sys, "frozen", False):
    BASE_DIR = os.path.dirname(sys.executable)
else:
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))

RANKING_PATH = os.path.join(BASE_DIR, RANKING_FILE)


def load_rankings():
    """저장된 랭킹 파일(rankings.json)을 읽어 점수 내림차순 리스트로 반환합니다."""
    if not os.path.exists(RANKING_PATH):
        return []

    try:
        with open(RANKING_PATH, "r", encoding="utf-8") as f:
            data = json.load(f)
            if isinstance(data, list):
                # 점수 기준 내림차순 정렬 후 상위 MAX_RANKINGS 개 반환
                sorted_data = sorted(
                    data, key=lambda item: item.get("score", 0), reverse=True
                )
                return sorted_data[:MAX_RANKINGS]
    except Exception as e:
        print(f"랭킹 파일 로드 오류: {e}", flush=True)

    return []


def save_ranking(name, score):
    """새로운 플레이어 이니셜(3글자)과 점수를 저장하고 최신 상위 랭킹 리스트를 반환합니다."""
    rankings = load_rankings()
    clean_name = (name.strip().upper() or "AAA")[:3]
    rankings.append({"name": clean_name, "score": int(score)})

    # 점수 내림차순 정렬 및 상위 랭킹 유지
    rankings.sort(key=lambda item: item.get("score", 0), reverse=True)
    rankings = rankings[:MAX_RANKINGS]

    try:
        with open(RANKING_PATH, "w", encoding="utf-8") as f:
            json.dump(rankings, f, ensure_ascii=False, indent=2)
    except Exception as e:
        print(f"랭킹 파일 저장 오류: {e}", flush=True)

    return rankings
