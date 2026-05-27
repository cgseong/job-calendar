"""
IT/인터넷 신입 채용 캘린더 - Streamlit 앱
- 사람인 웹 크롤링 기반 채용 정보 수집
- 캘린더 시각화 + 필터링 + 통계
- Streamlit Cloud 배포용
"""
import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
from job_fetcher import fetch_all_jobs, apply_filters, get_available_filters

# 페이지 설정
st.set_page_config(
    page_title="IT/인터넷 신입 채용 캘린더",
    page_icon="📅",
    layout="wide",
    initial_sidebar_state="expanded",
)

# 커스텀 CSS
st.markdown("""
<style>
    .main-header {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        padding: 24px 32px;
        border-radius: 12px;
        margin-bottom: 24px;
    }
    .main-header h1 {
        color: white;
        margin-bottom: 8px;
    }
    .main-header p {
        color: rgba(255,255,255,0.9);
        font-size: 14px;
    }
    .stat-card {
        background: #f8f9ff;
        border-radius: 12px;
        padding: 16px;
        text-align: center;
        border: 1px solid #e8eaf6;
    }
    .stat-number {
        font-size: 28px;
        font-weight: 700;
        color: #667eea;
    }
    .stat-label {
        font-size: 12px;
        color: #888;
        margin-top: 4px;
    }
    .urgent-badge {
        background: #ffeaea;
        color: #e53935;
        padding: 2px 8px;
        border-radius: 10px;
        font-size: 11px;
        font-weight: 500;
    }
    .soon-badge {
        background: #fff3e0;
        color: #ff9800;
        padding: 2px 8px;
        border-radius: 10px;
        font-size: 11px;
        font-weight: 500;
    }
    .normal-badge {
        background: #e3f2fd;
        color: #2196f3;
        padding: 2px 8px;
        border-radius: 10px;
        font-size: 11px;
        font-weight: 500;
    }
    .stMetric {
        background: #f8f9ff;
        border-radius: 12px;
        padding: 8px;
    }
</style>
""", unsafe_allow_html=True)


@st.cache_data(ttl=3600)
def load_jobs():
    """채용 데이터를 로드합니다 (1시간 캐시)."""
    return fetch_all_jobs()


def get_days_left(deadline_str):
    """마감일까지 남은 일수를 계산합니다."""
    try:
        deadline = datetime.strptime(deadline_str, "%Y-%m-%d").date()
        return (deadline - datetime.now().date()).days
    except (ValueError, TypeError):
        return None


def get_urgency_color(days_left):
    """마감 임박도에 따른 색상을 반환합니다."""
    if days_left is None:
        return "#9e9e9e"
    elif days_left < 0:
        return "#9e9e9e"  # 마감됨
    elif days_left <= 3:
        return "#e53935"  # 긴급
    elif days_left <= 7:
        return "#ff9800"  # 주의
    elif days_left <= 14:
        return "#2196f3"  # 보통
    else:
        return "#4caf50"  # 여유


def get_urgency_label(days_left):
    """마감 임박도 라벨을 반환합니다."""
    if days_left is None:
        return "알 수 없음"
    elif days_left < 0:
        return "마감됨"
    elif days_left <= 3:
        return f"D-{days_left} (긴급!)"
    elif days_left <= 7:
        return f"D-{days_left}"
    elif days_left <= 14:
        return f"D-{days_left}"
    else:
        return f"D-{days_left} (여유)"


# ===== 메인 앱 =====

# 헤더
st.markdown("""
<div class="main-header">
    <h1>📅 IT/인터넷 신입 채용 캘린더</h1>
    <p>학부생을 위한 실시간 IT 채용 정보 - 사람인 크롤링 기반</p>
</div>
""", unsafe_allow_html=True)

# 데이터 로드
with st.spinner("채용 정보를 수집하고 있습니다..."):
    jobs = load_jobs()

# ===== 사이드바: 필터 =====
st.sidebar.header("🔍 필터")

filter_options = get_available_filters(jobs)

# 회사 필터
selected_company = st.sidebar.selectbox(
    "회사",
    options=["전체"] + filter_options.get("companies", []),
    index=0,
)

# 지역 필터
selected_location = st.sidebar.selectbox(
    "지역",
    options=["전국"] + filter_options.get("locations", []),
    index=0,
)

# 직무 카테고리 필터
selected_category = st.sidebar.selectbox(
    "직무 카테고리",
    options=["전체"] + filter_options.get("categories", []),
    index=0,
)

# 마감 상태 필터
deadline_filter = st.sidebar.selectbox(
    "마감 상태",
    options=["전체", "지원 가능", "3일 내 마감", "7일 내 마감", "14일 내 마감", "마감됨"],
    index=0,
)

# 고용 형태 필터
job_types = sorted(set(j.get("job_type", "") for j in jobs if j.get("job_type")))
selected_job_type = st.sidebar.selectbox(
    "고용 형태",
    options=["전체"] + job_types,
    index=0,
)

# 키워드 검색
search_keyword = st.sidebar.text_input("🔎 키워드 검색", placeholder="예: React, Python, 백엔드")

# 새로고침 버튼
if st.sidebar.button("🔄 데이터 새로고침", use_container_width=True):
    st.cache_data.clear()
    st.rerun()

# 범례
st.sidebar.markdown("---")
st.sidebar.markdown("### 🎨 마감 임박도")
st.sidebar.markdown("""
- 🔴 3일 이내 마감 (긴급!)
- 🟠 7일 이내 마감
- 🔵 14일 이내 마감
- 🟢 여유 있음
- ⚫ 마감됨
""")

# ===== 필터 적용 =====
filters = {}
if selected_company != "전체":
    filters["company"] = selected_company
if selected_location != "전국":
    filters["location"] = selected_location
if selected_category != "전체":
    filters["job_category"] = selected_category

filtered_jobs = apply_filters(jobs, filters) if filters else jobs

# 키워드 검색 적용
if search_keyword:
    keyword_lower = search_keyword.lower()
    filtered_jobs = [
        j for j in filtered_jobs
        if keyword_lower in j.get("title", "").lower()
        or keyword_lower in j.get("company", "").lower()
        or keyword_lower in j.get("industry", "").lower()
    ]

# 고용 형태 필터
if selected_job_type != "전체":
    filtered_jobs = [j for j in filtered_jobs if j.get("job_type") == selected_job_type]

# 마감 상태 필터
if deadline_filter != "전체":
    today = datetime.now().date()
    filtered_deadline_jobs = []
    for j in filtered_jobs:
        days_left = get_days_left(j.get("deadline", ""))
        if days_left is None:
            continue
        if deadline_filter == "지원 가능" and days_left >= 0:
            filtered_deadline_jobs.append(j)
        elif deadline_filter == "3일 내 마감" and 0 <= days_left <= 3:
            filtered_deadline_jobs.append(j)
        elif deadline_filter == "7일 내 마감" and 0 <= days_left <= 7:
            filtered_deadline_jobs.append(j)
        elif deadline_filter == "14일 내 마감" and 0 <= days_left <= 14:
            filtered_deadline_jobs.append(j)
        elif deadline_filter == "마감됨" and days_left < 0:
            filtered_deadline_jobs.append(j)
    filtered_jobs = filtered_deadline_jobs

# ===== 통계 카드 =====
today = datetime.now().date()
total_count = len(filtered_jobs)
urgent_count = sum(1 for j in filtered_jobs if get_days_left(j.get("deadline", "")) is not None and 0 <= get_days_left(j.get("deadline", "")) <= 3)
week_count = sum(1 for j in filtered_jobs if get_days_left(j.get("deadline", "")) is not None and 0 <= get_days_left(j.get("deadline", "")) <= 7)
active_count = sum(1 for j in filtered_jobs if get_days_left(j.get("deadline", "")) is not None and get_days_left(j.get("deadline", "")) >= 0)

col1, col2, col3, col4 = st.columns(4)
with col1:
    st.metric("📋 전체 공고", total_count)
with col2:
    st.metric("🔴 3일 내 마감", urgent_count)
with col3:
    st.metric("🟠 7일 내 마감", week_count)
with col4:
    st.metric("✅ 지원 가능", active_count)

st.markdown("---")

# ===== 캘린더 뷰 (월별 요약) =====
tab1, tab2, tab3, tab4 = st.tabs(["📅 캘린더 뷰", "📋 리스트 뷰", "📊 통계", "🏢 부산 공공기관"])

with tab1:
    st.subheader("📅 마감일 캘린더")

    # 날짜별 공고 수 집계
    if filtered_jobs:
        deadline_data = []
        for job in filtered_jobs:
            if job.get("deadline"):
                days_left = get_days_left(job["deadline"])
                if days_left is not None:
                    deadline_data.append({
                        "날짜": job["deadline"],
                        "회사": job.get("company", ""),
                        "제목": job.get("title", ""),
                        "D-Day": days_left,
                        "상태": get_urgency_label(days_left),
                    })

        if deadline_data:
            df_calendar = pd.DataFrame(deadline_data)
            df_calendar["날짜"] = pd.to_datetime(df_calendar["날짜"])

            # 날짜별 공고 수
            daily_counts = df_calendar.groupby(df_calendar["날짜"].dt.date).size().reset_index(name="공고 수")
            daily_counts.columns = ["날짜", "공고 수"]

            st.bar_chart(
                data=daily_counts.set_index("날짜"),
                y="공고 수",
                use_container_width=True,
            )

            # 이번 주 마감 공고
            st.markdown("#### 📌 이번 주 마감 공고")
            this_week = [d for d in deadline_data if 0 <= d["D-Day"] <= 7]
            this_week.sort(key=lambda x: x["D-Day"])

            if this_week:
                for item in this_week:
                    emoji = "🔴" if item["D-Day"] <= 3 else "🟠"
                    st.markdown(f"{emoji} **D-{item['D-Day']}** | [{item['회사']}] {item['제목']}")
            else:
                st.info("이번 주 마감 공고가 없습니다.")
        else:
            st.info("표시할 캘린더 데이터가 없습니다.")
    else:
        st.info("필터 조건에 맞는 공고가 없습니다.")

with tab2:
    st.subheader("📋 채용 공고 목록")

    if filtered_jobs:
        # 정렬 옵션
        sort_option = st.selectbox(
            "정렬",
            ["마감 임박순", "회사명순", "최신 등록순"],
            index=0,
        )

        sorted_jobs = filtered_jobs.copy()
        if sort_option == "마감 임박순":
            sorted_jobs.sort(key=lambda x: x.get("deadline", "9999-12-31"))
        elif sort_option == "회사명순":
            sorted_jobs.sort(key=lambda x: x.get("company", ""))
        elif sort_option == "최신 등록순":
            sorted_jobs.sort(key=lambda x: x.get("start_date", ""), reverse=True)

        # 공고 목록 표시
        for idx, job in enumerate(sorted_jobs):
            days_left = get_days_left(job.get("deadline", ""))
            urgency = get_urgency_label(days_left)
            color = get_urgency_color(days_left)

            with st.expander(
                f"{'🔴' if days_left is not None and 0 <= days_left <= 3 else '🟠' if days_left is not None and 0 <= days_left <= 7 else '🔵' if days_left is not None and 0 <= days_left <= 14 else '🟢' if days_left is not None and days_left > 14 else '⚫'} [{job.get('company', '')}] {job.get('title', '')}",
                expanded=False,
            ):
                col_a, col_b = st.columns(2)
                with col_a:
                    st.markdown(f"**회사명:** {job.get('company', '')}")
                    st.markdown(f"**근무지:** {job.get('location', '')}")
                    st.markdown(f"**경력:** {job.get('experience', '')}")
                    st.markdown(f"**고용형태:** {job.get('job_type', '')}")
                with col_b:
                    st.markdown(f"**업종:** {job.get('industry', '')}")
                    st.markdown(f"**급여:** {job.get('salary', '')}")
                    st.markdown(f"**마감일:** {job.get('deadline', '')} ({urgency})")

                if job.get("url"):
                    st.link_button("🔗 지원하러 가기", job["url"])
    else:
        st.info("필터 조건에 맞는 공고가 없습니다.")

with tab3:
    st.subheader("📊 채용 통계")

    if filtered_jobs:
        col_s1, col_s2 = st.columns(2)

        with col_s1:
            # 회사별 공고 수
            st.markdown("#### 🏢 회사별 공고 수 (Top 10)")
            company_counts = pd.Series([j.get("company", "") for j in filtered_jobs]).value_counts().head(10)
            st.bar_chart(company_counts)

        with col_s2:
            # 지역별 공고 수
            st.markdown("#### 📍 지역별 공고 수")
            location_counts = pd.Series([j.get("location", "").split(" ")[0] for j in filtered_jobs]).value_counts().head(10)
            st.bar_chart(location_counts)

        col_s3, col_s4 = st.columns(2)

        with col_s3:
            # 고용형태별
            st.markdown("#### 💼 고용형태별")
            type_counts = pd.Series([j.get("job_type", "미표기") or "미표기" for j in filtered_jobs]).value_counts()
            st.bar_chart(type_counts)

        with col_s4:
            # 마감 임박도 분포
            st.markdown("#### ⏰ 마감 임박도 분포")
            urgency_data = {"긴급(3일내)": 0, "주의(7일내)": 0, "보통(14일내)": 0, "여유": 0, "마감": 0}
            for j in filtered_jobs:
                dl = get_days_left(j.get("deadline", ""))
                if dl is None:
                    continue
                elif dl < 0:
                    urgency_data["마감"] += 1
                elif dl <= 3:
                    urgency_data["긴급(3일내)"] += 1
                elif dl <= 7:
                    urgency_data["주의(7일내)"] += 1
                elif dl <= 14:
                    urgency_data["보통(14일내)"] += 1
                else:
                    urgency_data["여유"] += 1

            st.bar_chart(pd.Series(urgency_data))
    else:
        st.info("통계를 표시할 데이터가 없습니다.")

with tab4:
    st.subheader("🏢 부산지역 공공기관 채용 정보")
    st.markdown("부산 소재 공공기관의 채용 공고만 필터링하여 보여줍니다.")

    # 공공기관 키워드 목록
    public_org_keywords = [
        "공사", "공단", "공공", "진흥원", "연구원", "재단",
        "센터", "원자력", "항만", "교통", "환경", "수자원",
        "정보통신", "과학기술", "한국", "국립", "시설관리",
        "도시공사", "관광공사", "해양", "부산", "BPA",
        "BIPA", "동남권", "부산정보산업진흥원",
    ]

    # 부산지역 + 공공기관 필터링
    busan_public_jobs = []
    for job in jobs:  # 전체 jobs에서 필터 (사이드바 필터 무관)
        location = job.get("location", "").lower()
        company = job.get("company", "")
        title = job.get("title", "")
        industry = job.get("industry", "")

        # 부산 지역 확인
        is_busan = "부산" in location

        # 공공기관 확인 (회사명 또는 제목에 공공기관 키워드 포함)
        is_public = any(
            kw in company or kw in title or kw in industry
            for kw in public_org_keywords
        )

        if is_busan and is_public:
            busan_public_jobs.append(job)

    # 통계 표시
    busan_total = len(busan_public_jobs)
    busan_active = sum(
        1 for j in busan_public_jobs
        if get_days_left(j.get("deadline", "")) is not None
        and get_days_left(j.get("deadline", "")) >= 0
    )

    col_b1, col_b2, col_b3 = st.columns(3)
    with col_b1:
        st.metric("전체 공고", busan_total)
    with col_b2:
        st.metric("지원 가능", busan_active)
    with col_b3:
        st.metric("마감됨", busan_total - busan_active)

    st.markdown("---")

    if busan_public_jobs:
        # 마감 임박순 정렬
        busan_public_jobs.sort(key=lambda x: x.get("deadline", "9999-12-31"))

        for job in busan_public_jobs:
            days_left = get_days_left(job.get("deadline", ""))
            urgency = get_urgency_label(days_left)

            # 이모지 결정
            if days_left is not None and 0 <= days_left <= 3:
                emoji = "🔴"
            elif days_left is not None and 0 <= days_left <= 7:
                emoji = "🟠"
            elif days_left is not None and 0 <= days_left <= 14:
                emoji = "🔵"
            elif days_left is not None and days_left > 14:
                emoji = "🟢"
            else:
                emoji = "⚫"

            with st.expander(
                f"{emoji} [{job.get('company', '')}] {job.get('title', '')}",
                expanded=False,
            ):
                col_a, col_b = st.columns(2)
                with col_a:
                    st.markdown(f"**회사명:** {job.get('company', '')}")
                    st.markdown(f"**근무지:** {job.get('location', '')}")
                    st.markdown(f"**경력:** {job.get('experience', '')}")
                    st.markdown(f"**고용형태:** {job.get('job_type', '')}")
                with col_b:
                    st.markdown(f"**업종:** {job.get('industry', '')}")
                    st.markdown(f"**급여:** {job.get('salary', '')}")
                    st.markdown(f"**마감일:** {job.get('deadline', '')} ({urgency})")

                if job.get("url"):
                    st.link_button("🔗 지원하러 가기", job["url"])
    else:
        st.info(
            "현재 부산지역 공공기관 채용 공고가 없습니다.\n\n"
            "크롤링 데이터에 부산 소재 공공기관 공고가 포함되면 여기에 표시됩니다."
        )

# 푸터
st.markdown("---")
st.markdown(
    "<div style='text-align: center; color: #888; font-size: 12px;'>"
    "IT/인터넷 신입 채용 캘린더 | 데이터 출처: 사람인 | "
    "매일 자동 갱신됩니다"
    "</div>",
    unsafe_allow_html=True,
)
