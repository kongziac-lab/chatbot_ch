"""성능 메트릭 수집 및 관리 모듈.

동기화 시간, 검색 성능, API 응답 시간 등을 측정하고 저장합니다.
"""

import json
import time
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Optional, Dict, List
from dataclasses import dataclass, asdict
from collections import deque

from loguru import logger


# 메트릭 저장 경로
METRICS_DIR = Path(__file__).parent.parent.parent / "metrics"
METRICS_DIR.mkdir(exist_ok=True)

# 메트릭 파일
SYNC_METRICS_FILE = METRICS_DIR / "sync_metrics.jsonl"
SEARCH_METRICS_FILE = METRICS_DIR / "search_metrics.jsonl"
CHAT_METRICS_FILE = METRICS_DIR / "chat_metrics.jsonl"

# 인메모리 캐시 (최근 100개)
_sync_cache: deque = deque(maxlen=100)
_search_cache: deque = deque(maxlen=100)
_chat_cache: deque = deque(maxlen=100)


@dataclass
class SyncMetric:
    """동기화 성능 메트릭."""
    timestamp: str
    sync_type: str  # "full" or "incremental"
    duration_ms: float
    faq_count: int
    chunk_count: int
    deleted_count: int
    success: bool
    error: Optional[str] = None


@dataclass
class SearchMetric:
    """검색 성능 메트릭."""
    timestamp: str
    query: str
    collection: str
    top_k: int
    duration_ms: float
    result_count: int
    use_mmr: bool
    success: bool
    error: Optional[str] = None


@dataclass
class ChatMetric:
    """챗봇 성능 메트릭."""
    timestamp: str
    message: str
    language: str
    duration_ms: float
    search_duration_ms: float
    llm_duration_ms: float
    confidence: str
    chunk_count: int
    success: bool
    error: Optional[str] = None


class MetricsCollector:
    """메트릭 수집기."""

    @staticmethod
    def _parse_timestamp(raw: str) -> datetime:
        """ISO 타임스탬프를 비교 가능한 naive UTC datetime으로 변환."""
        dt = datetime.fromisoformat(raw)
        if dt.tzinfo is not None:
            return dt.astimezone(timezone.utc).replace(tzinfo=None)
        return dt

    @staticmethod
    def _read_recent_from_file(file_path: Path, limit: int) -> List[Dict]:
        """JSONL 파일에서 최근 N개 레코드 조회 (시간순 정렬)."""
        rows: List[Dict] = []
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                for line in f:
                    try:
                        data = json.loads(line)
                        rows.append(data)
                    except json.JSONDecodeError:
                        continue
        except FileNotFoundError:
            return []

        rows.sort(
            key=lambda r: MetricsCollector._parse_timestamp(str(r.get("timestamp", "")))
            if r.get("timestamp")
            else datetime.min
        )
        return rows[-limit:]
    
    @staticmethod
    def _append_to_file(file_path: Path, data: dict) -> None:
        """메트릭을 JSONL 파일에 추가."""
        try:
            with open(file_path, "a", encoding="utf-8") as f:
                f.write(json.dumps(data, ensure_ascii=False) + "\n")
        except Exception as e:
            logger.error("메트릭 저장 실패 | file={} | error={}", file_path, e)
    
    @staticmethod
    def record_sync(metric: SyncMetric) -> None:
        """동기화 메트릭 기록."""
        data = asdict(metric)
        MetricsCollector._append_to_file(SYNC_METRICS_FILE, data)
        _sync_cache.append(data)
        logger.debug("동기화 메트릭 기록 | type={} | duration={}ms", 
                    metric.sync_type, metric.duration_ms)
    
    @staticmethod
    def record_search(metric: SearchMetric) -> None:
        """검색 메트릭 기록."""
        data = asdict(metric)
        MetricsCollector._append_to_file(SEARCH_METRICS_FILE, data)
        _search_cache.append(data)
        logger.debug("검색 메트릭 기록 | duration={}ms | results={}", 
                    metric.duration_ms, metric.result_count)
    
    @staticmethod
    def record_chat(metric: ChatMetric) -> None:
        """챗봇 메트릭 기록."""
        data = asdict(metric)
        MetricsCollector._append_to_file(CHAT_METRICS_FILE, data)
        _chat_cache.append(data)
        logger.debug("챗봇 메트릭 기록 | duration={}ms | confidence={}", 
                    metric.duration_ms, metric.confidence)
    
    @staticmethod
    def get_recent_syncs(limit: int = 10) -> List[Dict]:
        """최근 동기화 메트릭 조회."""
        from_file = MetricsCollector._read_recent_from_file(SYNC_METRICS_FILE, limit)
        return from_file if from_file else list(_sync_cache)[-limit:]
    
    @staticmethod
    def get_recent_searches(limit: int = 10) -> List[Dict]:
        """최근 검색 메트릭 조회."""
        from_file = MetricsCollector._read_recent_from_file(SEARCH_METRICS_FILE, limit)
        return from_file if from_file else list(_search_cache)[-limit:]
    
    @staticmethod
    def get_recent_chats(limit: int = 10) -> List[Dict]:
        """최근 챗봇 메트릭 조회."""
        from_file = MetricsCollector._read_recent_from_file(CHAT_METRICS_FILE, limit)
        return from_file if from_file else list(_chat_cache)[-limit:]
    
    @staticmethod
    def get_sync_stats(hours: int = 24) -> Dict:
        """동기화 통계 (최근 N시간)."""
        cutoff = datetime.now(timezone.utc).replace(tzinfo=None) - timedelta(hours=hours)
        
        total_count = 0
        incremental_count = 0
        full_count = 0
        total_duration = 0.0
        success_count = 0
        
        try:
            with open(SYNC_METRICS_FILE, "r", encoding="utf-8") as f:
                for line in f:
                    try:
                        data = json.loads(line)
                        ts = MetricsCollector._parse_timestamp(data["timestamp"])
                        
                        if ts >= cutoff:
                            total_count += 1
                            if data["success"]:
                                success_count += 1
                            total_duration += data["duration_ms"]
                            
                            if data["sync_type"] == "incremental":
                                incremental_count += 1
                            else:
                                full_count += 1
                    except (json.JSONDecodeError, KeyError, ValueError):
                        continue
        except FileNotFoundError:
            pass
        
        avg_duration = total_duration / total_count if total_count > 0 else 0
        
        return {
            "period_hours": hours,
            "total_syncs": total_count,
            "incremental_syncs": incremental_count,
            "full_syncs": full_count,
            "success_rate": success_count / total_count if total_count > 0 else 0,
            "avg_duration_ms": avg_duration,
        }
    
    @staticmethod
    def get_search_stats(hours: int = 24) -> Dict:
        """검색 통계 (최근 N시간)."""
        cutoff = datetime.now(timezone.utc).replace(tzinfo=None) - timedelta(hours=hours)
        
        total_count = 0
        total_duration = 0.0
        success_count = 0
        total_results = 0
        
        try:
            with open(SEARCH_METRICS_FILE, "r", encoding="utf-8") as f:
                for line in f:
                    try:
                        data = json.loads(line)
                        ts = MetricsCollector._parse_timestamp(data["timestamp"])
                        
                        if ts >= cutoff:
                            total_count += 1
                            if data["success"]:
                                success_count += 1
                            total_duration += data["duration_ms"]
                            total_results += data["result_count"]
                    except (json.JSONDecodeError, KeyError, ValueError):
                        continue
        except FileNotFoundError:
            pass
        
        avg_duration = total_duration / total_count if total_count > 0 else 0
        avg_results = total_results / total_count if total_count > 0 else 0
        
        return {
            "period_hours": hours,
            "total_searches": total_count,
            "success_rate": success_count / total_count if total_count > 0 else 0,
            "avg_duration_ms": avg_duration,
            "avg_results": avg_results,
        }
    
    @staticmethod
    def get_chat_stats(hours: int = 24) -> Dict:
        """챗봇 통계 (최근 N시간)."""
        cutoff = datetime.now(timezone.utc).replace(tzinfo=None) - timedelta(hours=hours)
        
        total_count = 0
        total_duration = 0.0
        total_search_duration = 0.0
        total_llm_duration = 0.0
        success_count = 0
        confidence_counts = {"high": 0, "medium": 0, "low": 0}
        
        try:
            with open(CHAT_METRICS_FILE, "r", encoding="utf-8") as f:
                for line in f:
                    try:
                        data = json.loads(line)
                        ts = MetricsCollector._parse_timestamp(data["timestamp"])
                        
                        if ts >= cutoff:
                            total_count += 1
                            if data["success"]:
                                success_count += 1
                            total_duration += data["duration_ms"]
                            total_search_duration += data["search_duration_ms"]
                            total_llm_duration += data["llm_duration_ms"]
                            
                            confidence = data.get("confidence", "low")
                            if confidence in confidence_counts:
                                confidence_counts[confidence] += 1
                    except (json.JSONDecodeError, KeyError, ValueError):
                        continue
        except FileNotFoundError:
            pass
        
        avg_duration = total_duration / total_count if total_count > 0 else 0
        avg_search = total_search_duration / total_count if total_count > 0 else 0
        avg_llm = total_llm_duration / total_count if total_count > 0 else 0
        
        return {
            "period_hours": hours,
            "total_chats": total_count,
            "success_rate": success_count / total_count if total_count > 0 else 0,
            "avg_total_duration_ms": avg_duration,
            "avg_search_duration_ms": avg_search,
            "avg_llm_duration_ms": avg_llm,
            "confidence_distribution": confidence_counts,
        }


# 타이머 컨텍스트 매니저
class Timer:
    """성능 측정 타이머."""
    
    def __init__(self):
        self.start_time = None
        self.end_time = None
        self.elapsed_ms = 0.0
    
    def __enter__(self):
        self.start_time = time.time()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.end_time = time.time()
        self.elapsed_ms = (self.end_time - self.start_time) * 1000
    
    def get_elapsed_ms(self) -> float:
        """경과 시간 (밀리초)."""
        return self.elapsed_ms


# 전역 인스턴스
metrics_collector = MetricsCollector()
