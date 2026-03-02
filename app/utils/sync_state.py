"""마지막 FAQ 동기화 시간 추적 모듈.

증분 업데이트를 위해 마지막 동기화 시간을 파일로 저장/조회합니다.
"""

import json
from datetime import datetime
from pathlib import Path
from typing import Optional

from loguru import logger

# sync_state.json 파일 위치
SYNC_STATE_FILE = Path(__file__).parent.parent.parent / "sync_state.json"


def get_last_sync_time() -> Optional[datetime]:
    """마지막 FAQ 동기화 시간을 조회합니다.
    
    Returns:
        마지막 동기화 시간 (없으면 None)
    """
    if not SYNC_STATE_FILE.exists():
        logger.debug("동기화 상태 파일 없음 | 첫 동기화로 판단")
        return None
    
    try:
        with open(SYNC_STATE_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
            last_sync_str = data.get("last_sync_time")
            if last_sync_str:
                return datetime.fromisoformat(last_sync_str)
    except Exception as e:
        logger.warning("동기화 시간 조회 실패 | error={}", e)
    
    return None


def update_last_sync_time(sync_time: Optional[datetime] = None) -> None:
    """마지막 FAQ 동기화 시간을 업데이트합니다.
    
    Args:
        sync_time: 동기화 시간 (기본값: 현재 시간)
    """
    if sync_time is None:
        sync_time = datetime.now()
    
    try:
        data = {
            "last_sync_time": sync_time.isoformat(),
            "updated_at": datetime.now().isoformat()
        }
        with open(SYNC_STATE_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        
        logger.info("동기화 시간 업데이트 | sync_time={}", sync_time.isoformat())
    except Exception as e:
        logger.error("동기화 시간 저장 실패 | error={}", e)


def reset_sync_state() -> None:
    """동기화 상태를 초기화합니다 (전체 동기화 강제 실행용)."""
    if SYNC_STATE_FILE.exists():
        SYNC_STATE_FILE.unlink()
        logger.info("동기화 상태 초기화 완료")
