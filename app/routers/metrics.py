"""성능 메트릭 조회 API."""

from fastapi import APIRouter, Query
from typing import Dict, List

from app.utils.metrics import metrics_collector

router = APIRouter(prefix="/metrics", tags=["Metrics"])


@router.get("/sync/recent", response_model=List[Dict])
async def get_recent_syncs(limit: int = Query(10, ge=1, le=100)):
    """최근 동기화 메트릭 조회.
    
    Args:
        limit: 조회할 개수 (1-100)
    
    Returns:
        최근 동기화 메트릭 목록
    """
    return metrics_collector.get_recent_syncs(limit=limit)


@router.get("/sync/stats", response_model=Dict)
async def get_sync_stats(hours: int = Query(24, ge=1, le=168)):
    """동기화 통계 조회.
    
    Args:
        hours: 조회 기간 (시간 단위, 1-168)
    
    Returns:
        동기화 통계
    """
    return metrics_collector.get_sync_stats(hours=hours)


@router.get("/search/recent", response_model=List[Dict])
async def get_recent_searches(limit: int = Query(10, ge=1, le=100)):
    """최근 검색 메트릭 조회.
    
    Args:
        limit: 조회할 개수 (1-100)
    
    Returns:
        최근 검색 메트릭 목록
    """
    return metrics_collector.get_recent_searches(limit=limit)


@router.get("/search/stats", response_model=Dict)
async def get_search_stats(hours: int = Query(24, ge=1, le=168)):
    """검색 통계 조회.
    
    Args:
        hours: 조회 기간 (시간 단위, 1-168)
    
    Returns:
        검색 통계
    """
    return metrics_collector.get_search_stats(hours=hours)


@router.get("/chat/recent", response_model=List[Dict])
async def get_recent_chats(limit: int = Query(10, ge=1, le=100)):
    """최근 챗봇 메트릭 조회.
    
    Args:
        limit: 조회할 개수 (1-100)
    
    Returns:
        최근 챗봇 메트릭 목록
    """
    return metrics_collector.get_recent_chats(limit=limit)


@router.get("/chat/stats", response_model=Dict)
async def get_chat_stats(hours: int = Query(24, ge=1, le=168)):
    """챗봇 통계 조회.
    
    Args:
        hours: 조회 기간 (시간 단위, 1-168)
    
    Returns:
        챗봇 통계
    """
    return metrics_collector.get_chat_stats(hours=hours)


@router.get("/summary", response_model=Dict)
async def get_metrics_summary(hours: int = Query(24, ge=1, le=168)):
    """전체 메트릭 요약.
    
    Args:
        hours: 조회 기간 (시간 단위, 1-168)
    
    Returns:
        전체 메트릭 요약
    """
    sync_stats = metrics_collector.get_sync_stats(hours=hours)
    search_stats = metrics_collector.get_search_stats(hours=hours)
    chat_stats = metrics_collector.get_chat_stats(hours=hours)
    
    return {
        "period_hours": hours,
        "sync": sync_stats,
        "search": search_stats,
        "chat": chat_stats,
    }
