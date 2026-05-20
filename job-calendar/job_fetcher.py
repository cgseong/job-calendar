"""
채용 정보 수집 통합 모듈
- 사람인 Open API + 잡코리아 크롤링 통합
- API 키 미설정 시 샘플 데이터 제공 (데모용)
"""
import requests
import json
import os
from datetime import datetime, timedelta
from config import SARAMIN_API_KEY, SARAMIN_API_URL, SEARCH_PARAMS
from jobkorea_crawler import crawl_jobkorea, get_jobkorea_sample_data


def fetch_all_jobs():
    """
    모든 소스(사람인 + 잡코리아)에서 채용공고를 수집하여 통합합니다.

    Returns:
        list: 통합된 채용공고 목록
    """
    all_jobs = []

    # 1. 사람인 API 데이터
    saramin_jobs = fetch_jobs_from_saramin()
    for job in saramin_jobs:
        job.setdefault("source", "사람인")
    all_jobs.extend(saramin_jobs)
    print(f"[통합] 사람인: {len(saramin_jobs)}개")

    # 2. 잡코리아 크롤링 데이터
    jobkorea_jobs = fetch_jobs_from_jobkorea()
    all_jobs.extend(jobkorea_jobs)
    print(f"[통합] 잡코리아: {len(jobkorea_jobs)}개")

    # 중복 제거 (회사명 + 제목 기준)
    all_jobs = _deduplicate(all_jobs)
    print(f"[통합] 최종: {len(all_jobs)}개 (중복 제거 후)")

    return all_jobs


def fetch_jobs_from_saramin():
    """
    사람인 Open API에서 IT/인터넷 신입 채용공고를 가져옵니다.

    Returns:
        list: 채용공고 목록 (dict 리스트)
    """
    if not SARAMIN_API_KEY:
        print("[INFO] 사람인 API 키가 설정되지 않았습니다. 샘플 데이터를 사용합니다.")
        return get_sample_jobs()

    params = {
        "access-key": SARAMIN_API_KEY,
        **SEARCH_PARAMS
    }

    try:
        response = requests.get(SARAMIN_API_URL, params=params, timeout=10)
        response.raise_for_status()

        data = response.json()
        jobs = data.get("jobs", {}).get("job", [])

        return parse_saramin_jobs(jobs)

    except requests.exceptions.RequestException as e:
        print(f"[ERROR] 사람인 API 호출 실패: {e}")
        return get_sample_jobs()


def fetch_jobs_from_jobkorea():
    """
    잡코리아에서 IT/인터넷 신입 채용공고를 크롤링합니다.

    Returns:
        list: 채용공고 목록 (dict 리스트)
    """
    try:
        jobs = crawl_jobkorea(pages=3, keyword="IT 개발")
        if not jobs:
            print("[INFO] 잡코리아 크롤링 결과 없음. 샘플 데이터를 사용합니다.")
            jobs = get_jobkorea_sample_data()
        return jobs
    except Exception as e:
        print(f"[ERROR] 잡코리아 크롤링 실패: {e}")
        return get_jobkorea_sample_data()


def _deduplicate(jobs):
    """
    회사명 + 제목 조합으로 중복 제거합니다.
    """
    seen = set()
    unique_jobs = []

    for job in jobs:
        key = (job.get("company", "").strip(), job.get("title", "").strip())
        if key not in seen:
            seen.add(key)
            unique_jobs.append(job)

    return unique_jobs


def parse_saramin_jobs(jobs):
    """
    사람인 API 응답을 캘린더 이벤트 형식으로 변환합니다.
    """
    parsed = []

    for job in jobs:
        position = job.get("position", {})
        company = job.get("company", {}).get("detail", {})

        # 마감일 파싱
        expiration_timestamp = job.get("expiration-timestamp", "")
        if expiration_timestamp:
            try:
                deadline = datetime.fromtimestamp(int(expiration_timestamp))
                deadline_str = deadline.strftime("%Y-%m-%d")
            except (ValueError, TypeError):
                deadline_str = ""
        else:
            deadline_str = job.get("expiration-date", "")

        # 시작일 (공고 등록일)
        opening_timestamp = job.get("opening-timestamp", "")
        if opening_timestamp:
            try:
                start_date = datetime.fromtimestamp(int(opening_timestamp))
                start_str = start_date.strftime("%Y-%m-%d")
            except (ValueError, TypeError):
                start_str = ""
        else:
            start_str = ""

        parsed.append({
            "id": job.get("id", ""),
            "title": position.get("title", "채용공고"),
            "company": company.get("name", ""),
            "location": position.get("location", {}).get("name", "전국"),
            "experience": position.get("experience-level", {}).get("name", "신입"),
            "job_type": position.get("job-type", {}).get("name", ""),
            "industry": position.get("industry", {}).get("name", "IT/통신"),
            "deadline": deadline_str,
            "start_date": start_str,
            "url": job.get("url", ""),
            "salary": job.get("salary", {}).get("name", "회사내규에 따름"),
            "source": "사람인",
        })

    return parsed


def get_sample_jobs():
    """
    데모용 샘플 채용 데이터를 생성합니다. (사람인 소스)
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
            "source": "사람인",
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
            "source": "사람인",
        },
        {
            "id": "sample_003",
            "title": "2025 신입 개발자 채용 (AI/ML)",
            "company": "삼성SDS",
            "location": "서울 송파구",
            "experience": "신입",
            "job_type": "정규직",
            "industry": "IT/통신",
            "deadline": (today + timedelta(days=14)).strftime("%Y-%m-%d"),
            "start_date": (today - timedelta(days=3)).strftime("%Y-%m-%d"),
            "url": "https://www.samsungsds.com/kr/careers",
            "salary": "4,000만원 이상",
            "source": "사람인",
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
            "source": "사람인",
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
            "source": "사람인",
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
            "source": "사람인",
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
            "source": "사람인",
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
            "source": "사람인",
        },
        {
            "id": "sample_009",
            "title": "2025 하반기 신입 개발자 공개채용",
            "company": "LG CNS",
            "location": "서울 마포구",
            "experience": "신입",
            "job_type": "정규직",
            "industry": "IT/통신",
            "deadline": (today + timedelta(days=25)).strftime("%Y-%m-%d"),
            "start_date": today.strftime("%Y-%m-%d"),
            "url": "https://www.lgcns.com/careers",
            "salary": "회사내규에 따름",
            "source": "사람인",
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
            "source": "사람인",
        },
        {
            "id": "sample_011",
            "title": "게임 서버 개발자 (신입/경력)",
            "company": "넥슨",
            "location": "경기 성남시",
            "experience": "신입",
            "job_type": "정규직",
            "industry": "IT/통신",
            "deadline": (today + timedelta(days=15)).strftime("%Y-%m-%d"),
            "start_date": (today - timedelta(days=1)).strftime("%Y-%m-%d"),
            "url": "https://career.nexon.com",
            "salary": "회사내규에 따름",
            "source": "사람인",
        },
        {
            "id": "sample_012",
            "title": "[신입] 풀스택 개발자 (Node.js/React)",
            "company": "당근",
            "location": "서울 서초구",
            "experience": "신입",
            "job_type": "정규직",
            "industry": "IT/통신",
            "deadline": (today + timedelta(days=9)).strftime("%Y-%m-%d"),
            "start_date": (today - timedelta(days=5)).strftime("%Y-%m-%d"),
            "url": "https://about.daangn.com/jobs",
            "salary": "회사내규에 따름",
            "source": "사람인",
        },
        {
            "id": "sample_013",
            "title": "인프라 엔지니어 신입 (리눅스/네트워크)",
            "company": "KT",
            "location": "서울 종로구",
            "experience": "신입",
            "job_type": "정규직",
            "industry": "IT/통신",
            "deadline": (today + timedelta(days=18)).strftime("%Y-%m-%d"),
            "start_date": (today - timedelta(days=9)).strftime("%Y-%m-%d"),
            "url": "https://recruit.kt.com",
            "salary": "3,500만원 이상",
            "source": "사람인",
        },
        {
            "id": "sample_014",
            "title": "[신입] Android 앱 개발자 (Kotlin)",
            "company": "야놀자",
            "location": "서울 강남구",
            "experience": "신입",
            "job_type": "정규직",
            "industry": "IT/통신",
            "deadline": (today + timedelta(days=11)).strftime("%Y-%m-%d"),
            "start_date": (today - timedelta(days=3)).strftime("%Y-%m-%d"),
            "url": "https://yanolja.in/ko/recruit",
            "salary": "회사내규에 따름",
            "source": "사람인",
        },
        {
            "id": "sample_015",
            "title": "DBA/데이터베이스 관리자 (신입)",
            "company": "SKT",
            "location": "서울 중구",
            "experience": "신입",
            "job_type": "정규직",
            "industry": "IT/통신",
            "deadline": (today + timedelta(days=4)).strftime("%Y-%m-%d"),
            "start_date": (today - timedelta(days=12)).strftime("%Y-%m-%d"),
            "url": "https://www.sktelecom.com/recruit",
            "salary": "4,500만원 이상",
            "source": "사람인",
        },
    ]

    return sample_jobs


def get_calendar_events(jobs=None, filters=None):
    """
    채용공고를 FullCalendar 이벤트 형식으로 변환합니다.
    마감일 기준으로 캘린더에 표시됩니다.

    Args:
        jobs (list, optional): 채용공고 리스트. None이면 전체 소스에서 가져옴.
        filters (dict, optional): 필터 조건 (company, job_category, source)

    Returns:
        list: FullCalendar 이벤트 형식 리스트
    """
    if jobs is None:
        jobs = fetch_all_jobs()

    # 필터링 적용
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
            "start": job.get("start_date") or job["deadline"],
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
                "source": job.get("source", ""),
            }
        }
        events.append(event)

    return events


def apply_filters(jobs, filters):
    """
    필터 조건에 맞는 채용공고만 반환합니다.

    Args:
        jobs (list): 전체 채용공고 리스트
        filters (dict): 필터 조건
            - company: 회사명 (부분 일치)
            - job_category: 직무 카테고리 키워드 (예: "백엔드", "프론트엔드")
            - source: 데이터 소스 ("사람인", "잡코리아", "all")
            - location: 지역 키워드

    Returns:
        list: 필터링된 채용공고 리스트
    """
    filtered = jobs

    # 회사명 필터
    company = filters.get("company", "").strip()
    if company:
        filtered = [j for j in filtered if company.lower() in j.get("company", "").lower()]

    # 직무 카테고리 필터
    job_category = filters.get("job_category", "").strip()
    if job_category:
        keywords = _get_category_keywords(job_category)
        filtered = [
            j for j in filtered
            if any(kw in j.get("title", "").lower() for kw in keywords)
        ]

    # 소스 필터
    source = filters.get("source", "").strip()
    if source and source != "all":
        filtered = [j for j in filtered if j.get("source", "") == source]

    # 지역 필터
    location = filters.get("location", "").strip()
    if location and location != "전국":
        filtered = [j for j in filtered if location in j.get("location", "")]

    return filtered


def _get_category_keywords(category):
    """
    직무 카테고리에 해당하는 키워드 리스트를 반환합니다.
    """
    category_map = {
        "백엔드": ["백엔드", "backend", "서버", "server", "java", "spring", "node", "python", "django", "flask", "go"],
        "프론트엔드": ["프론트엔드", "frontend", "front-end", "react", "vue", "angular", "html", "css", "javascript", "typescript"],
        "풀스택": ["풀스택", "fullstack", "full-stack", "full stack"],
        "모바일": ["모바일", "mobile", "ios", "android", "swift", "kotlin", "flutter", "react native", "앱"],
        "데이터": ["데이터", "data", "빅데이터", "분석", "analytics", "etl", "warehouse", "dba", "database"],
        "AI/ML": ["ai", "ml", "머신러닝", "딥러닝", "machine learning", "deep learning", "인공지능", "nlp", "컴퓨터비전"],
        "DevOps": ["devops", "sre", "인프라", "infrastructure", "클라우드", "cloud", "aws", "gcp", "azure", "kubernetes", "docker"],
        "보안": ["보안", "security", "정보보안", "침해", "취약점", "모의해킹", "cert"],
        "QA": ["qa", "테스트", "test", "품질", "quality"],
        "게임": ["게임", "game", "unity", "unreal", "클라이언트"],
    }

    category_lower = category.lower()

    # 정확한 매칭
    for key, keywords in category_map.items():
        if category_lower == key.lower() or category_lower in [k.lower() for k in keywords[:2]]:
            return keywords

    # 부분 매칭
    for key, keywords in category_map.items():
        if category_lower in key.lower():
            return keywords

    # 매칭 안 되면 입력값 자체를 키워드로
    return [category_lower]


def get_available_filters(jobs):
    """
    현재 데이터에서 사용 가능한 필터 옵션을 추출합니다.

    Args:
        jobs (list): 채용공고 리스트

    Returns:
        dict: 필터 옵션 (companies, categories, sources, locations)
    """
    companies = sorted(set(j.get("company", "") for j in jobs if j.get("company")))
    sources = sorted(set(j.get("source", "") for j in jobs if j.get("source")))
    locations = sorted(set(j.get("location", "") for j in jobs if j.get("location")))

    # 직무 카테고리 자동 분류
    categories = [
        "백엔드", "프론트엔드", "풀스택", "모바일",
        "데이터", "AI/ML", "DevOps", "보안", "QA", "게임"
    ]

    return {
        "companies": companies,
        "categories": categories,
        "sources": sources,
        "locations": locations,
    }


if __name__ == "__main__":
    # 테스트 실행
    print("=== IT/인터넷 신입 채용 정보 통합 수집 ===\n")
    jobs = fetch_all_jobs()
    print(f"\n총 {len(jobs)}개의 채용공고를 수집했습니다.\n")

    for job in jobs[:5]:
        print(f"  [{job.get('source', '')}] [{job['company']}] {job['title']}")
        print(f"    - 마감일: {job['deadline']}")
        print(f"    - 근무지: {job['location']}")
        print(f"    - 급여: {job['salary']}")
        print()

    # 필터 테스트
    print("\n=== 필터링 테스트 (백엔드) ===")
    filtered = apply_filters(jobs, {"job_category": "백엔드"})
    print(f"  백엔드 관련: {len(filtered)}개")
    for j in filtered[:3]:
        print(f"    - [{j['company']}] {j['title']}")
