"""FAQ 관리자 대시보드 (Streamlit).

실행:
    streamlit run dashboard/app.py
"""

import time
import pandas as pd
import streamlit as st

import api_client as api

st.set_page_config(
    page_title="FAQ 관리 대시보드",
    page_icon="📋",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ---------------------------------------------------------------------------
# 사이드바 네비게이션
# ---------------------------------------------------------------------------

PAGES = ["대시보드", "문서 관리", "FAQ 검수", "통계"]
page = st.sidebar.selectbox("페이지", PAGES)
st.sidebar.markdown("---")
st.sidebar.caption("FAQ 생성기 v1.0")


# ---------------------------------------------------------------------------
# 헬퍼
# ---------------------------------------------------------------------------

@st.cache_data(ttl=300)
def load_faqs(cat_major=None, cat_minor=None):
    try:
        return pd.DataFrame(api.get_faqs(cat_major, cat_minor))
    except Exception as e:
        st.error(f"FAQ 로드 실패: {e}")
        return pd.DataFrame()


STATUS_COLORS = {
    "게시중":   "🟢",
    "자동생성": "🟡",
    "검수대기": "🟠",
    "폐기":     "🔴",
}


def status_badge(status: str) -> str:
    return f"{STATUS_COLORS.get(status, '⚪')} {status}"


# ===========================================================================
# 1. 대시보드
# ===========================================================================

if page == "대시보드":
    st.title("📋 FAQ 관리 대시보드")

    df = load_faqs()

    if df.empty:
        st.info("데이터가 없습니다. 문서를 업로드하고 FAQ를 생성하세요.")
        st.stop()

    # ── 요약 카드 ─────────────────────────────────────────────────────
    status_col = "상태" if "상태" in df.columns else None
    counts = df[status_col].value_counts() if status_col else {}

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("전체 FAQ", len(df))
    col2.metric("🟢 게시중",   counts.get("게시중",   0))
    col3.metric("🟡 자동생성", counts.get("자동생성", 0))
    col4.metric("🔴 폐기",     counts.get("폐기",     0))

    st.divider()

    # ── 차트 ──────────────────────────────────────────────────────────
    chart_col1, chart_col2 = st.columns(2)

    with chart_col1:
        st.subheader("카테고리별 FAQ 분포")
        if "카테고리(대분류)" in df.columns:
            cat_counts = df["카테고리(대분류)"].value_counts().reset_index()
            cat_counts.columns = ["카테고리", "건수"]
            st.bar_chart(cat_counts.set_index("카테고리"))
        else:
            st.info("카테고리 데이터 없음")

    with chart_col2:
        st.subheader("적용범위별 현황")
        if "적용범위" in df.columns and df["적용범위"].notna().any():
            scope_counts = df["적용범위"].value_counts().reset_index()
            scope_counts.columns = ["적용범위", "건수"]
            st.bar_chart(scope_counts.set_index("적용범위"))
        else:
            st.info("적용범위 데이터 없음")

    # ── 최근 생성 FAQ ─────────────────────────────────────────────────
    st.subheader("최근 생성 FAQ (최대 10건)")
    date_col = "생성일" if "생성일" in df.columns else None
    recent = (
        df.sort_values(date_col, ascending=False).head(10)
        if date_col
        else df.head(10)
    )

    display_cols = [c for c in ["고유번호", "카테고리(대분류)", "질문(한국어)", "상태", "생성일"]
                    if c in recent.columns]
    if display_cols:
        st.dataframe(recent[display_cols], use_container_width=True, hide_index=True)


# ===========================================================================
# 2. 문서 관리
# ===========================================================================

elif page == "문서 관리":
    st.title("📁 문서 관리")

    # ── 파일 업로드 ───────────────────────────────────────────────────
    st.subheader("문서 업로드")
    with st.form("upload_form", clear_on_submit=True):
        uploaded = st.file_uploader(
            "PDF 또는 DOCX 파일을 드래그 앤 드롭하세요",
            type=["pdf", "docx"],
            accept_multiple_files=False,
        )
        doc_type = st.selectbox("문서 유형", ["안내", "공지", "규정"])
        uploader = st.text_input("업로더 (부서명 등)", placeholder="예: 국제처")
        submitted = st.form_submit_button("업로드 및 인덱싱")

    if submitted and uploaded:
        with st.spinner(f"'{uploaded.name}' 업로드 중..."):
            try:
                result = api.upload_document(
                    file_bytes=uploaded.read(),
                    filename=uploaded.name,
                    doc_type=doc_type,
                )
                st.success(
                    f"✅ 업로드 완료!\n\n"
                    f"- 문서 ID: `{result['document_id']}`\n"
                    f"- 청크 수: {result['num_chunks']}개\n"
                    f"- 총 페이지: {result['total_pages']}페이지"
                )
                st.session_state["last_doc_id"] = result["document_id"]
                st.session_state["last_doc_name"] = uploaded.name
            except Exception as e:
                st.error(f"업로드 실패: {e}")

    st.divider()

    # ── FAQ 생성 ──────────────────────────────────────────────────────
    st.subheader("FAQ 자동 생성")
    doc_id_input = st.text_input(
        "문서 ID",
        value=st.session_state.get("last_doc_id", ""),
        placeholder="업로드 후 자동 입력됩니다",
    )

    gen_col1, gen_col2, gen_col3 = st.columns(3)
    department  = gen_col1.text_input("생성 부서", placeholder="예: 국제처")
    cat_major   = gen_col2.text_input("대분류",    placeholder="예: 학생생활")
    cat_minor   = gen_col3.text_input("중분류",    placeholder="예: 입학")

    if st.button("FAQ 생성 시작", type="primary", disabled=not doc_id_input):
        try:
            res = api.start_pipeline(doc_id_input, department, cat_major, cat_minor)
            job_id = res["job_id"]
            st.info(f"파이프라인 시작! job_id: `{job_id}`")
            st.session_state["pipeline_job_id"] = job_id
        except Exception as e:
            st.error(f"파이프라인 시작 실패: {e}")

    # ── 파이프라인 상태 ───────────────────────────────────────────────
    if "pipeline_job_id" in st.session_state:
        job_id = st.session_state["pipeline_job_id"]
        st.subheader(f"파이프라인 상태 — `{job_id}`")

        status_placeholder = st.empty()
        if st.button("상태 새로고침"):
            try:
                s = api.get_pipeline_status(job_id)
                with status_placeholder.container():
                    sc1, sc2, sc3, sc4 = st.columns(4)
                    sc1.metric("상태",        s["status"])
                    sc2.metric("원시 질문 수", s["raw_questions"])
                    sc3.metric("고유 질문 수", s["unique_questions"])
                    sc4.metric("저장된 FAQ",  s["saved_faqs"])
                    if s["error"]:
                        st.error(f"오류: {s['error']}")
                    if s["status"] == "completed":
                        load_faqs.clear()
            except Exception as e:
                st.error(f"상태 조회 실패: {e}")


# ===========================================================================
# 3. FAQ 검수
# ===========================================================================

elif page == "FAQ 검수":
    st.title("✏️ FAQ 검수")

    # ── 필터 ──────────────────────────────────────────────────────────
    filter_col1, filter_col2, filter_col3 = st.columns(3)
    filter_status  = filter_col1.selectbox("상태 필터", ["전체", "자동생성", "검수대기", "게시중", "폐기"])
    filter_major   = filter_col2.text_input("대분류 필터")
    filter_minor   = filter_col3.text_input("중분류 필터")

    df = load_faqs(
        cat_major=filter_major or None,
        cat_minor=filter_minor or None,
    )

    if df.empty:
        st.info("FAQ가 없습니다.")
        st.stop()

    if filter_status != "전체" and "상태" in df.columns:
        df = df[df["상태"] == filter_status]

    st.caption(f"총 {len(df)}건")

    # ── FAQ 목록 + 개별 검수 ──────────────────────────────────────────
    if "고유번호" not in df.columns:
        st.dataframe(df, use_container_width=True)
        st.stop()

    for _, row in df.iterrows():
        faq_id = row.get("고유번호", "")
        with st.expander(
            f"{status_badge(row.get('상태',''))}  {row.get('질문(한국어)','')[:80]}",
            expanded=False,
        ):
            tab_ko, tab_zh = st.tabs(["한국어", "中文"])

            with tab_ko:
                new_q = st.text_area("질문(한국어)", value=row.get("질문(한국어)",""), key=f"qko_{faq_id}")
                new_a = st.text_area("답변(한국어)", value=row.get("답변(한국어)",""), height=150, key=f"ako_{faq_id}")

            with tab_zh:
                new_qzh = st.text_area("질문(중국어)", value=row.get("질문(중국어)",""), key=f"qzh_{faq_id}")
                new_azh = st.text_area("답변(중국어)", value=row.get("답변(중국어)",""), height=150, key=f"azh_{faq_id}")

                if st.button("🔄 번역 재생성", key=f"retrans_{faq_id}"):
                    with st.spinner("번역 중..."):
                        try:
                            t = api.translate_qa(new_q, new_a)
                            st.session_state[f"qzh_{faq_id}"] = t["question_zh"]
                            st.session_state[f"azh_{faq_id}"] = t["answer_zh"]
                            st.success("번역 완료 — 저장 버튼으로 반영하세요.")
                        except Exception as e:
                            st.error(f"번역 실패: {e}")

            btn_col1, btn_col2, _ = st.columns([1, 1, 4])
            if btn_col1.button("✅ 승인 (게시중)", key=f"approve_{faq_id}"):
                st.success(f"FAQ `{faq_id}` 승인 완료 (Sheets 직접 수정 필요)")
                load_faqs.clear()
            if btn_col2.button("❌ 폐기", key=f"reject_{faq_id}"):
                st.warning(f"FAQ `{faq_id}` 폐기 처리 (Sheets 직접 수정 필요)")
                load_faqs.clear()

    st.divider()

    # ── 일괄 승인 ─────────────────────────────────────────────────────
    st.subheader("일괄 처리")
    st.caption("자동생성 상태 FAQ를 모두 검수대기로 변경하려면 아래 버튼을 사용하세요.")
    if st.button("전체 자동생성 → 검수대기 변경"):
        st.info("Google Sheets에서 직접 상태 열을 일괄 변경하세요.")


# ===========================================================================
# 4. 통계
# ===========================================================================

elif page == "통계":
    st.title("📊 통계")

    df = load_faqs()

    if df.empty:
        st.info("데이터가 없습니다.")
        st.stop()

    col_a, col_b = st.columns(2)

    # ── 조회수 Top 10 ─────────────────────────────────────────────────
    with col_a:
        st.subheader("조회수 Top 10")
        if "조회수" in df.columns and "질문(한국어)" in df.columns:
            top_views = (
                df[["질문(한국어)", "조회수"]]
                .dropna()
                .sort_values("조회수", ascending=False)
                .head(10)
            )
            top_views["조회수"] = pd.to_numeric(top_views["조회수"], errors="coerce").fillna(0)
            st.bar_chart(top_views.set_index("질문(한국어)"))
        else:
            st.info("조회수 데이터 없음")

    # ── 도움됨 비율 낮은 FAQ ──────────────────────────────────────────
    with col_b:
        st.subheader("도움됨 비율 낮은 FAQ (개선 필요)")
        if "도움됨비율" in df.columns and "질문(한국어)" in df.columns:
            low_helpful = (
                df[["질문(한국어)", "도움됨비율", "카테고리(대분류)"]]
                .dropna(subset=["도움됨비율"])
                .copy()
            )
            low_helpful["도움됨비율"] = pd.to_numeric(low_helpful["도움됨비율"], errors="coerce")
            low_helpful = (
                low_helpful[low_helpful["도움됨비율"] < 50]
                .sort_values("도움됨비율")
                .head(10)
            )
            if not low_helpful.empty:
                st.dataframe(low_helpful, use_container_width=True, hide_index=True)
            else:
                st.success("도움됨 비율 50% 미만 FAQ가 없습니다.")
        else:
            st.info("도움됨비율 데이터 없음")

    st.divider()

    # ── 월별 생성 추이 ────────────────────────────────────────────────
    st.subheader("월별 FAQ 생성 추이")
    if "생성일" in df.columns:
        df_date = df.copy()
        df_date["생성일"] = pd.to_datetime(df_date["생성일"], errors="coerce")
        df_date = df_date.dropna(subset=["생성일"])
        df_date["월"] = df_date["생성일"].dt.to_period("M").astype(str)

        monthly = df_date.groupby(["월", "상태"]).size().reset_index(name="건수")
        pivot = monthly.pivot(index="월", columns="상태", values="건수").fillna(0)

        if not pivot.empty:
            st.area_chart(pivot)
        else:
            st.info("월별 데이터가 부족합니다.")
    else:
        st.info("생성일 데이터 없음")
