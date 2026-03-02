"""성능 모니터링 대시보드.

실행: streamlit run dashboard/performance.py --server.port 8503
"""

import streamlit as st
import requests
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta

# API 기본 URL
API_BASE_URL = "http://localhost:8002/api/v1"


st.set_page_config(
    page_title="FAQ 생성기 성능 모니터링",
    page_icon="📊",
    layout="wide",
)

st.title("📊 FAQ 생성기 성능 모니터링")

# 사이드바 - 조회 기간 설정
st.sidebar.header("⚙️ 설정")
hours = st.sidebar.slider("조회 기간 (시간)", 1, 168, 24, 1)

# 새로고침 버튼
if st.sidebar.button("🔄 새로고침", use_container_width=True):
    st.rerun()

st.sidebar.markdown("---")
st.sidebar.info(f"**조회 기간**: 최근 {hours}시간")

try:
    # API 연결 확인
    health_response = requests.get(f"{API_BASE_URL.replace('/api/v1', '')}/health", timeout=2)
    if health_response.status_code != 200:
        st.error("❌ API 서버에 연결할 수 없습니다. 서버가 실행 중인지 확인하세요.")
        st.stop()
    
    # ===========================
    # 전체 메트릭 요약
    # ===========================
    st.header("📈 전체 메트릭 요약")
    
    summary_response = requests.get(f"{API_BASE_URL}/metrics/summary?hours={hours}")
    summary = summary_response.json()
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric(
            label="🔄 총 동기화 횟수",
            value=f"{summary['sync']['total_syncs']:,}회",
            delta=f"성공률: {summary['sync']['success_rate']*100:.1f}%",
        )
        st.metric(
            label="⏱️ 평균 동기화 시간",
            value=f"{summary['sync']['avg_duration_ms']:.0f}ms",
        )
    
    with col2:
        st.metric(
            label="🔍 총 검색 횟수",
            value=f"{summary['search']['total_searches']:,}회",
            delta=f"성공률: {summary['search']['success_rate']*100:.1f}%",
        )
        st.metric(
            label="⏱️ 평균 검색 시간",
            value=f"{summary['search']['avg_duration_ms']:.0f}ms",
        )
    
    with col3:
        st.metric(
            label="💬 총 챗봇 응답",
            value=f"{summary['chat']['total_chats']:,}회",
            delta=f"성공률: {summary['chat']['success_rate']*100:.1f}%",
        )
        st.metric(
            label="⏱️ 평균 응답 시간",
            value=f"{summary['chat']['avg_total_duration_ms']:.0f}ms",
        )
    
    st.markdown("---")
    
    # ===========================
    # 동기화 성능
    # ===========================
    st.header("🔄 동기화 성능")
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        sync_stats = summary['sync']
        st.subheader("동기화 통계")
        
        # 동기화 유형 비율
        fig_sync_type = go.Figure(data=[go.Pie(
            labels=['증분 업데이트', '전체 동기화'],
            values=[sync_stats['incremental_syncs'], sync_stats['full_syncs']],
            hole=0.4,
            marker=dict(colors=['#3498db', '#e74c3c']),
        )])
        fig_sync_type.update_layout(
            title="동기화 유형 분포",
            height=300,
        )
        st.plotly_chart(fig_sync_type, use_container_width=True)
    
    with col2:
        st.subheader("최근 동기화")
        recent_syncs = requests.get(f"{API_BASE_URL}/metrics/sync/recent?limit=5").json()
        
        for sync in recent_syncs:
            status_emoji = "✅" if sync['success'] else "❌"
            sync_type_emoji = "⚡" if sync['sync_type'] == "incremental" else "🔄"
            
            st.write(f"{status_emoji} {sync_type_emoji} **{sync['sync_type']}**")
            st.caption(f"FAQ: {sync['faq_count']}개 | 시간: {sync['duration_ms']:.0f}ms")
            st.caption(f"청크: {sync['chunk_count']}개 | {sync['timestamp'][:19]}")
            st.markdown("---")
    
    # ===========================
    # 검색 성능
    # ===========================
    st.header("🔍 검색 성능")
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.subheader("검색 통계")
        search_stats = summary['search']
        
        # 검색 시간 분포 (최근 검색 기반)
        recent_searches = requests.get(f"{API_BASE_URL}/metrics/search/recent?limit=50").json()
        
        if recent_searches:
            search_df = pd.DataFrame(recent_searches)
            search_df['timestamp'] = pd.to_datetime(search_df['timestamp'])
            
            fig_search = px.scatter(
                search_df,
                x='timestamp',
                y='duration_ms',
                color='collection',
                size='result_count',
                hover_data=['query', 'result_count'],
                title="검색 응답 시간 추이",
                color_discrete_map={
                    'faq_knowledge': '#2ecc71',
                    'faq_documents': '#3498db',
                },
            )
            fig_search.update_layout(height=350)
            st.plotly_chart(fig_search, use_container_width=True)
        else:
            st.info("검색 데이터가 없습니다.")
    
    with col2:
        st.subheader("컬렉션별 통계")
        if recent_searches:
            collection_stats = search_df.groupby('collection').agg({
                'duration_ms': 'mean',
                'result_count': 'mean',
            }).round(1)
            
            st.dataframe(
                collection_stats.rename(columns={
                    'duration_ms': '평균 시간 (ms)',
                    'result_count': '평균 결과 수',
                }),
                use_container_width=True,
            )
            
            st.metric(
                label="총 검색 횟수",
                value=f"{len(recent_searches)}회",
            )
            st.metric(
                label="평균 결과 수",
                value=f"{search_stats['avg_results']:.1f}개",
            )
    
    # ===========================
    # 챗봇 성능
    # ===========================
    st.header("💬 챗봇 성능")
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.subheader("응답 시간 분석")
        chat_stats = summary['chat']
        recent_chats = requests.get(f"{API_BASE_URL}/metrics/chat/recent?limit=50").json()
        
        if recent_chats:
            chat_df = pd.DataFrame(recent_chats)
            chat_df['timestamp'] = pd.to_datetime(chat_df['timestamp'])
            
            # 검색 vs LLM 시간 비교
            time_comparison = pd.DataFrame({
                '구분': ['검색 시간', 'LLM 시간'],
                '평균 시간 (ms)': [
                    chat_stats['avg_search_duration_ms'],
                    chat_stats['avg_llm_duration_ms'],
                ],
            })
            
            fig_time = px.bar(
                time_comparison,
                x='구분',
                y='평균 시간 (ms)',
                title="검색 vs LLM 처리 시간",
                color='구분',
                color_discrete_map={
                    '검색 시간': '#3498db',
                    'LLM 시간': '#e74c3c',
                },
            )
            fig_time.update_layout(height=300, showlegend=False)
            st.plotly_chart(fig_time, use_container_width=True)
            
            # 전체 응답 시간 추이
            fig_chat = px.line(
                chat_df,
                x='timestamp',
                y='duration_ms',
                title="챗봇 응답 시간 추이",
                markers=True,
            )
            fig_chat.update_layout(height=300)
            st.plotly_chart(fig_chat, use_container_width=True)
        else:
            st.info("챗봇 데이터가 없습니다.")
    
    with col2:
        st.subheader("신뢰도 분포")
        confidence_dist = chat_stats['confidence_distribution']
        
        fig_confidence = go.Figure(data=[go.Pie(
            labels=['High', 'Medium', 'Low'],
            values=[
                confidence_dist['high'],
                confidence_dist['medium'],
                confidence_dist['low'],
            ],
            hole=0.4,
            marker=dict(colors=['#2ecc71', '#f39c12', '#e74c3c']),
        )])
        fig_confidence.update_layout(height=300)
        st.plotly_chart(fig_confidence, use_container_width=True)
        
        st.metric(
            label="총 대화 수",
            value=f"{chat_stats['total_chats']}회",
        )
        st.metric(
            label="평균 청크 수",
            value=f"{chat_df['chunk_count'].mean():.1f}개" if len(chat_df) > 0 else "N/A",
        )
    
    # ===========================
    # 상세 로그
    # ===========================
    st.header("📋 상세 로그")
    
    tab1, tab2, tab3 = st.tabs(["🔄 동기화", "🔍 검색", "💬 챗봇"])
    
    with tab1:
        st.subheader("최근 동기화 로그")
        sync_logs = requests.get(f"{API_BASE_URL}/metrics/sync/recent?limit=20").json()
        
        if sync_logs:
            sync_log_df = pd.DataFrame(sync_logs)
            sync_log_df['timestamp'] = pd.to_datetime(sync_log_df['timestamp']).dt.strftime('%Y-%m-%d %H:%M:%S')
            sync_log_df = sync_log_df[[
                'timestamp', 'sync_type', 'faq_count', 'chunk_count',
                'deleted_count', 'duration_ms', 'success'
            ]]
            sync_log_df.columns = [
                '시간', '유형', 'FAQ 수', '청크 수', '삭제 수', '소요 시간 (ms)', '성공'
            ]
            st.dataframe(sync_log_df, use_container_width=True, height=400)
        else:
            st.info("동기화 로그가 없습니다.")
    
    with tab2:
        st.subheader("최근 검색 로그")
        search_logs = requests.get(f"{API_BASE_URL}/metrics/search/recent?limit=20").json()
        
        if search_logs:
            search_log_df = pd.DataFrame(search_logs)
            search_log_df['timestamp'] = pd.to_datetime(search_log_df['timestamp']).dt.strftime('%Y-%m-%d %H:%M:%S')
            search_log_df = search_log_df[[
                'timestamp', 'query', 'collection', 'result_count',
                'duration_ms', 'use_mmr', 'success'
            ]]
            search_log_df.columns = [
                '시간', '쿼리', '컬렉션', '결과 수', '소요 시간 (ms)', 'MMR', '성공'
            ]
            st.dataframe(search_log_df, use_container_width=True, height=400)
        else:
            st.info("검색 로그가 없습니다.")
    
    with tab3:
        st.subheader("최근 챗봇 로그")
        chat_logs = requests.get(f"{API_BASE_URL}/metrics/chat/recent?limit=20").json()
        
        if chat_logs:
            chat_log_df = pd.DataFrame(chat_logs)
            chat_log_df['timestamp'] = pd.to_datetime(chat_log_df['timestamp']).dt.strftime('%Y-%m-%d %H:%M:%S')
            chat_log_df = chat_log_df[[
                'timestamp', 'message', 'language', 'confidence',
                'duration_ms', 'search_duration_ms', 'llm_duration_ms', 'success'
            ]]
            chat_log_df.columns = [
                '시간', '메시지', '언어', '신뢰도',
                '전체 시간 (ms)', '검색 시간 (ms)', 'LLM 시간 (ms)', '성공'
            ]
            st.dataframe(chat_log_df, use_container_width=True, height=400)
        else:
            st.info("챗봇 로그가 없습니다.")

except requests.exceptions.ConnectionError:
    st.error("❌ API 서버에 연결할 수 없습니다. `http://localhost:8002`에서 서버가 실행 중인지 확인하세요.")
except Exception as e:
    st.error(f"❌ 오류 발생: {e}")
    st.exception(e)

# 푸터
st.markdown("---")
st.caption("FAQ 생성기 v1.2.0 | 성능 모니터링 대시보드")
