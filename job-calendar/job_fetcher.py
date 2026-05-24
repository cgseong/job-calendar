"""
채용 정보 수집 모듈 (웹 크롤링 방식)
- 사람인(saramin.co.kr) 검색 결과를 BeautifulSoup으로 파싱
- IT개발/데이터 직무, 전 지역, 신입 대상
- API 키 불필요
"""
import requests
import time
import re
from datetime import datetime, timedelta
from bs4 import BeautifulSoup
from config import (
    SARAMIN_BASE_URL,
    SEARCH_KEYWORDS,
    SEARCH_PARAMS,
    CRAWL_CONFIG,
    REQUEST_HEADERS,
)


def fetch_jobs_from_saramin():
    """
    사람인 웹사이트에서 IT개발/데이터 신입 채용공고를 크롤링합니다.
    여러 검색 키워드를 사용하여 다양한 IT 직무의 공고를 수집합니다.

    Returns:
        list: 채용공고 목록 (dict 리스트)
    """
    all_jobs = {}  # URL 기준 중복 제거용 dict
    max_total = CRAWL_CONFIG["max_total_jobs"]

    for keyword in SEARCH_KEYWORDS:
        if len(all_jobs) >= max_total:
            break

        jobs = _crawl_keyword(keyword)
        for job in jobs:
            if len(all_jobs) >= max_total:
                break
            # URL 기준 중복 제거
            job_key = job.get("url", job.get("id", ""))
            if job_key and job_key not in all_jobs:
                all_jobs[job_key] = job

    result = list(all_jobs.values())
    print(f"[INFO] 총 {len(result)}개의 IT개발/데이터 채용공고를 수집했습니다.")

    if not result:
        print("[WARN] 크롤링 결과가 없습니다. 샘플 데이터를 사용합니다.")
        return get_sample_jobs()

    return result


def _crawl_keyword(keyword):
    """
    특정 키워드로 사람인 채용공고를 크롤링합니다.

    Args:
        keyword (str): 검색 키워드

    Returns:
        list: 파싱된 채용공고 리스트
    """
    jobs = []
    max_pages = CRAWL_CONFIG["max_pages_per_keyword"]
    delay = CRAWL_CONFIG["request_delay"]

    for page in range(1, max_pages + 1):
        params = {
            **SEARCH_PARAMS,
            "searchword": keyword,
            "recruitPage": str(page),
        }

        try:
            response = requests.get(
                SARAMIN_BASE_URL,
                params=params,
                headers=REQUEST_HEADERS,
                timeout=CRAWL_CONFIG["timeout"],
            )
            response.raise_for_status()

            page_jobs = _parse_search_results(response.text)
            jobs.extend(page_jobs)

            print(f"  [크롤링] '{keyword}' 페이지 {page}: {len(page_jobs)}건 수집")

            if len(page_jobs) < 10:
                # 결과가 적으면 더 이상 페이지가 없는 것
                break

            if page < max_pages:
                time.sleep(delay)

        except requests.exceptions.RequestException as e:
            print(f"  [ERROR] '{keyword}' 페이지 {page} 크롤링 실패: {e}")
            break

    return jobs


def _parse_search_results(html):
    """
    사람인 검색 결과 HTML을 파싱하여 채용공고 데이터를 추출합니다.

    Args:
        html (str): 검색 결과 HTML

    Returns:
        list: 파싱된 채용공고 리스트
    """
    soup = BeautifulSoup(html, "html.parser")
    items = soup.select(".item_recruit")
    jobs = []

    for item in items:
        try:
            job = _parse_job_item(item)
            if job and _is_it_related(job):
                jobs.append(job)
        except Exception as e:
            # 개별 항목 파싱 실패 시 건너뛰기
            continue

    return jobs


def _parse_job_item(item):
    """
    개별 채용공고 항목을 파싱합니다.

    Args:
        item: BeautifulSoup element (.item_recruit)

    Returns:
        dict: 파싱된 채용공고 정보
    """
    # 회사명
    company_el = item.select_one(".corp_name a")
    company = company_el.text.strip() if company_el else ""

    # 채용 제목 및 URL
    title_el = item.select_one(".job_tit a")
    title = title_el.text.strip() if title_el else ""
    job_url = ""
    if title_el and title_el.get("href"):
        href = title_el["href"]
        if href.startswith("http"):
            job_url = href
        else:
            job_url = f"https://www.saramin.co.kr{href}"

    # 근무 조건 (지역, 경력, 학력, 고용형태, 급여)
    conditions = item.select(".job_condition span")
    cond_texts = [c.text.strip() for c in conditions]

    location = cond_texts[0] if len(cond_texts) > 0 else "전국"
    experience = cond_texts[1] if len(cond_texts) > 1 else "신입"
    education = cond_texts[2] if len(cond_texts) > 2 else ""
    job_type = cond_texts[3] if len(cond_texts) > 3 else ""
    salary = cond_texts[4] if len(cond_texts) > 4 else "회사내규에 따름"

    # 마감일
    deadline_el = item.select_one(".job_date .date")
    deadline_text = deadline_el.text.strip() if deadline_el else ""
    deadline_date = _parse_deadline(deadline_text)

    # 업종/직무 키워드
    sector_el = item.select_one(".job_sector")
    sector = ""
    if sector_el:
        sector = sector_el.text.strip()
        # '수정일', '등록일' 이후 텍스트 제거
        sector = re.split(r"\s*(수정일|등록일)\s*", sector)[0].strip()

    if not title or not company:
        return None

    return {
        "id": _generate_id(company, title),
        "title": title,
        "company": company,
        "location": location,
        "experience": experience,
        "education": education,
        "job_type": job_type,
        "industry": sector if sector else "IT/통신",
        "deadline": deadline_date,
        "start_date": "",  # 크롤링으로는 등록일 정확히 알기 어려움
        "url": job_url,
        "salary": salary,
    }


def _parse_deadline(deadline_text):
    """
    마감일 텍스트를 YYYY-MM-DD 형식으로 변환합니다.

    Args:
        deadline_text (str): 마감일 텍스트 (예: "~ 06/15(일)", "내일마감", "채용시")

    Returns:
        str: YYYY-MM-DD 형식 날짜 문자열, 파싱 불가 시 빈 문자열
    """
    today = datetime.now()

    if not deadline_text:
        return ""

    # "내일마감"
    if "내일" in deadline_text:
        deadline = today + timedelta(days=1)
        return deadline.strftime("%Y-%m-%d")

    # "오늘마감"
    if "오늘" in deadline_text:
        return today.strftime("%Y-%m-%d")

    # "채용시", "상시채용" → 30일 후로 설정
    if "채용시" in deadline_text or "상시" in deadline_text:
        deadline = today + timedelta(days=30)
        return deadline.strftime("%Y-%m-%d")

    # "~ MM/DD(요일)" 형식
    match = re.search(r"(\d{2})/(\d{2})", deadline_text)
    if match:
        month = int(match.group(1))
        day = int(match.group(2))
        year = today.year

        # 월이 현재보다 작으면 내년으로 간주
        if month < today.month - 1:
            year += 1

        try:
            deadline = datetime(year, month, day)
            return deadline.strftime("%Y-%m-%d")
        except ValueError:
            return ""

    return ""


def _is_it_related(job):
    """
    채용공고가 IT개발/데이터 직무와 관련이 있는지 판별합니다.

    Args:
        job (dict): 채용공고 정보

    Returns:
        bool: IT 관련 여부
    """
    it_keywords = [
        "개발", "프론트", "백엔드", "풀스택", "서버",
        "웹", "앱", "모바일", "소프트웨어", "SW",
        "Java", "Python", "React", "Spring", "Node",
        "AI", "인공지능", "머신러닝", "딥러닝", "데이터",
        "DBA", "DevOps", "클라우드", "인프라", "보안",
        "QA", "테스트", "자동화", "게임", "Unity",
        "iOS", "Android", "Kotlin", "Flutter", "API",
        "시스템", "네트워크", "블록체인", "임베디드", "펌웨어",
        "SE", "엔지니어", "IT", "정보", "컴퓨터",
    ]

    check_text = f"{job.get('title', '')} {job.get('industry', '')}"

    return any(kw.lower() in check_text.lower() for kw in it_keywords)


def _generate_id(company, title):
    """공고 고유 ID 생성"""
    import hashlib
    raw = f"{company}_{title}"
    return hashlib.md5(raw.encode("utf-8")).hexdigest()[:12]


def get_sample_jobs():
    """
    데모용 샘플 채용 데이터를 생성합니다.
    크롤링 실패 시 폴백으로 사용됩니다.
    """
    today = datetime.now()

    sample_jobs = [
        {
            "id": "sample_001",
            "title": "[신입] 백엔드 개발자 (Java/Spring)",
            "company": "카카오",
            "location": "경기 판교",
            "experience": "신입",
            "job_type": "정규직",
            "industry": "IT/통신",
            "deadline": (today + timedelta(days=5)).strftime("%Y-%m-%d"),
            "start_date": (today - timedelta(days=10)).strftime("%Y-%m-%d"),
            "url": "https://careers.kakao.com",
            "salary": "회사내규에 따름",
        },
        {
            "id": "sample_002",
            "title": "[신입/인턴] 프론트엔드 개발자 (React)",
            "company": "네이버",
            "location": "경기 성남시",
            "experience": "신입",
            "job_type": "정규직",
            "industry": "IT/통신",
            "deadline": (today + timedelta(days=7)).strftime("%Y-%m-%d"),
            "start_date": (today - timedelta(days=5)).strftime("%Y-%m-%d"),
            "url": "https://recruit.navercorp.com",
            "salary": "회사내규에 따름",
        },
        {
            "id": "sample_003",
            "title": "2026 신입 개발자 채용 (AI/ML)",
            "company": "삼성SDS",
            "location": "서울 송파구",
            "experience": "신입",
            "job_type": "정규직",
            "industry": "IT/통신",
            "deadline": (today + timedelta(days=14)).strftime("%Y-%m-%d"),
            "start_date": (today - timedelta(days=3)).strftime("%Y-%m-%d"),
            "url": "https://www.samsungsds.com/kr/careers",
            "salary": "4,000만원 이상",
        },
        {
            "id": "sample_004",
            "title": "[신입] iOS 앱 개발자",
            "company": "라인플러스",
            "location": "경기 판교",
            "experience": "신입",
            "job_type": "정규직",
            "industry": "IT/통신",
            "deadline": (today + timedelta(days=10)).strftime("%Y-%m-%d"),
            "start_date": (today - timedelta(days=7)).strftime("%Y-%m-%d"),
            "url": "https://careers.linecorp.com",
            "salary": "회사내규에 따름",
        },
        {
            "id": "sample_005",
            "title": "클라우드 엔지니어 (AWS/GCP) 신입",
            "company": "NHN",
            "location": "경기 판교",
            "experience": "신입",
            "job_type": "정규직",
            "industry": "IT/통신",
            "deadline": (today + timedelta(days=3)).strftime("%Y-%m-%d"),
            "start_date": (today - timedelta(days=14)).strftime("%Y-%m-%d"),
            "url": "https://recruit.nhn.com",
            "salary": "3,600만원 이상",
        },
        {
            "id": "sample_006",
            "title": "[채용전환형 인턴] 데이터 엔지니어",
            "company": "쿠팡",
            "location": "서울 송파구",
            "experience": "신입",
            "job_type": "인턴",
            "industry": "IT/통신",
            "deadline": (today + timedelta(days=20)).strftime("%Y-%m-%d"),
            "start_date": (today - timedelta(days=2)).strftime("%Y-%m-%d"),
            "url": "https://www.coupang.jobs",
            "salary": "회사내규에 따름",
        },
        {
            "id": "sample_007",
            "title": "DevOps/SRE 신입 엔지니어",
            "company": "토스",
            "location": "서울 강남구",
            "experience": "신입",
            "job_type": "정규직",
            "industry": "IT/통신",
            "deadline": (today + timedelta(days=8)).strftime("%Y-%m-%d"),
            "start_date": (today - timedelta(days=6)).strftime("%Y-%m-%d"),
            "url": "https://toss.im/career",
            "salary": "5,000만원 이상",
        },
        {
            "id": "sample_008",
            "title": "[신입] 보안 엔지니어 (정보보안)",
            "company": "SK쉴더스",
            "location": "서울 중구",
            "experience": "신입",
            "job_type": "정규직",
            "industry": "IT/통신",
            "deadline": (today + timedelta(days=12)).strftime("%Y-%m-%d"),
            "start_date": (today - timedelta(days=4)).strftime("%Y-%m-%d"),
            "url": "https://www.skshieldus.com",
            "salary": "3,800만원 이상",
        },
        {
            "id": "sample_009",
            "title": "2026 하반기 신입 개발자 공개채용",
            "company": "LG CNS",
            "location": "서울 마포구",
            "experience": "신입",
            "job_type": "정규직",
            "industry": "IT/통신",
            "deadline": (today + timedelta(days=25)).strftime("%Y-%m-%d"),
            "start_date": today.strftime("%Y-%m-%d"),
            "url": "https://www.lgcns.com/careers",
            "salary": "회사내규에 따름",
        },
        {
            "id": "sample_010",
            "title": "[신입] QA 엔지니어 (자동화 테스트)",
            "company": "배달의민족",
            "location": "서울 송파구",
            "experience": "신입",
            "job_type": "정규직",
            "industry": "IT/통신",
            "deadline": (today + timedelta(days=6)).strftime("%Y-%m-%d"),
            "start_date": (today - timedelta(days=8)).strftime("%Y-%m-%d"),
            "url": "https://career.woowahan.com",
            "salary": "4,200만원 이상",
        },
    ]

    return sample_jobs


def fetch_all_jobs():
    """
    모든 채용 데이터를 수집합니다. (app.py 호환용)
    사람인 웹 크롤링을 통해 IT개발/데이터 채용공고를 가져옵니다.

    Returns:
        list: 채용공고 목록
    """
    return fetch_jobs_from_saramin()


def apply_filters(jobs, filters):
    """
    채용공고 목록에 필터를 적용합니다.

    Args:
        jobs (list): 채용공고 리스트
        filters (dict): 필터 조건
            - company (str): 회사명 (부분 일치)
            - job_category (str): 직무 카테고리 (부분 일치)
            - source (str): 데이터 소스 (현재는 '사람인'만 존재)
            - location (str): 지역 (부분 일치)

    Returns:
        list: 필터링된 채용공고 리스트
    """
    filtered = jobs

    if filters.get("company"):
        keyword = filters["company"].lower()
        filtered = [j for j in filtered if keyword in j.get("company", "").lower()]

    if filters.get("job_category"):
        keyword = filters["job_category"].lower()
        filtered = [
            j for j in filtered
            if keyword in j.get("title", "").lower()
            or keyword in j.get("industry", "").lower()
        ]

    if filters.get("location"):
        keyword = filters["location"].lower()
        filtered = [j for j in filtered if keyword in j.get("location", "").lower()]

    # source 필터 (현재는 모두 사람인이므로 무시)
    if filters.get("source") and filters["source"] != "all":
        pass  # 향후 다중 소스 지원 시 구현

    return filtered


def get_available_filters(jobs):
    """
    현재 수집된 채용공고에서 사용 가능한 필터 옵션을 추출합니다.

    Args:
        jobs (list): 채용공고 리스트

    Returns:
        dict: 필터 옵션 목록
    """
    companies = sorted(set(j.get("company", "") for j in jobs if j.get("company")))
    locations = sorted(set(j.get("location", "").split(" ")[0] for j in jobs if j.get("location")))
    sources = ["사람인"]

    # 직무 카테고리 추출 (industry 필드에서)
    categories = set()
    for j in jobs:
        industry = j.get("industry", "")
        for keyword in industry.split(","):
            keyword = keyword.strip()
            if keyword:
                categories.add(keyword)

    return {
        "companies": companies[:50],  # 상위 50개만
        "locations": [loc for loc in locations if loc],
        "categories": sorted(categories)[:30],
        "sources": sources,
    }


def get_calendar_events(jobs=None, filters=None):
    """
    채용공고를 FullCalendar 이벤트 형식으로 변환합니다.
    마감일 기준으로 캘린더에 표시됩니다.

    Args:
        jobs (list, optional): 채용공고 리스트. None이면 크롤링으로 가져옴.
        filters (dict, optional): 필터 조건. None이면 전체 표시.

    Returns:
        list: FullCalendar 이벤트 형식 리스트
    """
    if jobs is None:
        jobs = fetch_jobs_from_saramin()

    # 필터 적용
    if filters:
        jobs = apply_filters(jobs, filters)

    events = []
    today = datetime.now().date()

    for job in jobs:
        if not job.get("deadline"):
            continue

        try:
            deadline = datetime.strptime(job["deadline"], "%Y-%m-%d").date()
        except (ValueError, TypeError):
            continue

        days_left = (deadline - today).days

        # 색상 지정 (마감 임박도)
        if days_left < 0:
            color = "#9e9e9e"  # 회색 - 마감됨
        elif days_left <= 3:
            color = "#e53935"  # 빨강 - 3일 이내 마감
        elif days_left <= 7:
            color = "#ff9800"  # 주황 - 7일 이내 마감
        elif days_left <= 14:
            color = "#2196f3"  # 파랑 - 14일 이내
        else:
            color = "#4caf50"  # 초록 - 여유

        event = {
            "id": job.get("id", ""),
            "title": f"[{job.get('company', '')}] {job.get('title', '')}",
            "start": job["deadline"],
            "end": job["deadline"],
            "color": color,
            "extendedProps": {
                "company": job.get("company", ""),
                "location": job.get("location", ""),
                "experience": job.get("experience", ""),
                "job_type": job.get("job_type", ""),
                "industry": job.get("industry", ""),
                "salary": job.get("salary", ""),
                "url": job.get("url", ""),
                "deadline": job["deadline"],
                "days_left": days_left,
            },
        }
        events.append(event)

    return events


if __name__ == "__main__":
    # 테스트 실행
    print("=" * 60)
    print("  IT개발/데이터 신입 채용 정보 수집 (사람인 웹 크롤링)")
    print("=" * 60)

    jobs = fetch_jobs_from_saramin()
    print(f"\n총 {len(jobs)}개의 채용공고를 수집했습니다.\n")

    print("-" * 60)
    for job in jobs[:10]:
        print(f"  [{job['company']}] {job['title']}")
        print(f"    마감일: {job['deadline']} | 지역: {job['location']}")
        print(f"    경력: {job['experience']} | 형태: {job['job_type']}")
        print(f"    URL: {job['url'][:60]}...")
        print()

    # 캘린더 이벤트 변환 테스트
    events = get_calendar_events(jobs)
    print(f"\n캘린더 이벤트 {len(events)}개 생성 완료")
