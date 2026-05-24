"""
잡코리아 채용공고 크롤링 모듈
- IT/인터넷 직무, 신입 채용공고 수집
- requests + BeautifulSoup 기반
"""
import requests
from bs4 import BeautifulSoup
from datetime import datetime, timedelta
import re
import time
import random


# 잡코리아 검색 URL 구조
JOBKOREA_BASE_URL = "https://www.jobkorea.co.kr"
JOBKOREA_SEARCH_URL = "https://www.jobkorea.co.kr/Search/"

# 검색 조건 (IT/인터넷, 신입, 전국)
JOBKOREA_PARAMS = {
    "stext": "",               # 검색어 (빈값 = 전체)
    "tabType": "recruit",      # 채용공고 탭
    "Page_No": "1",            # 페이지 번호
    "Ord": "RegDtDesc",        # 정렬: 최신등록순 (RegDtDesc), 마감순(EndDtAsc)
    "duty_step1": "10031",     # 직무 대분류: IT·인터넷
    "duty_step2": "",          # 직무 중분류 (전체)
    "careerType": "1",         # 경력: 신입(1), 경력(2), 경력무관(3)
}

# IT 직무 중분류 코드
IT_DUTY_CODES = {
    "10031001": "웹개발",
    "10031002": "서버/백엔드 개발",
    "10031003": "프론트엔드 개발",
    "10031004": "SW 엔지니어",
    "10031005": "앱개발",
    "10031006": "시스템 엔지니어",
    "10031007": "네트워크 엔지니어",
    "10031008": "보안 엔지니어",
    "10031009": "DBA",
    "10031010": "QA",
    "10031011": "데이터 엔지니어",
    "10031012": "AI/머신러닝",
    "10031013": "게임 개발",
    "10031014": "클라우드",
    "10031015": "DevOps",
}

# HTTP 요청 헤더
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                  "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "ko-KR,ko;q=0.9,en-US;q=0.8,en;q=0.7",
    "Accept-Encoding": "gzip, deflate, br",
    "Connection": "keep-alive",
    "Referer": "https://www.jobkorea.co.kr/",
}


def crawl_jobkorea(pages=3, keyword=""):
    """
    잡코리아에서 IT/인터넷 신입 채용공고를 크롤링합니다.

    Args:
        pages (int): 크롤링할 페이지 수 (기본 3페이지, 페이지당 약 20개)
        keyword (str): 추가 검색 키워드 (예: "백엔드", "프론트엔드")

    Returns:
        list: 채용공고 목록 (dict 리스트)
    """
    all_jobs = []

    for page in range(1, pages + 1):
        try:
            jobs = _crawl_page(page, keyword)
            all_jobs.extend(jobs)
            print(f"[잡코리아] 페이지 {page} 크롤링 완료 ({len(jobs)}개)")

            # 서버 부하 방지를 위한 딜레이
            if page < pages:
                time.sleep(random.uniform(1.0, 2.0))

        except Exception as e:
            print(f"[잡코리아] 페이지 {page} 크롤링 실패: {e}")
            continue

    print(f"[잡코리아] 총 {len(all_jobs)}개 채용공고 수집 완료")
    return all_jobs


def _crawl_page(page_no, keyword=""):
    """
    잡코리아 검색 결과 한 페이지를 크롤링합니다.

    Args:
        page_no (int): 페이지 번호
        keyword (str): 검색 키워드

    Returns:
        list: 해당 페이지의 채용공고 리스트
    """
    params = JOBKOREA_PARAMS.copy()
    params["Page_No"] = str(page_no)
    if keyword:
        params["stext"] = keyword

    try:
        response = requests.get(
            JOBKOREA_SEARCH_URL,
            params=params,
            headers=HEADERS,
            timeout=15,
        )
        response.raise_for_status()
        response.encoding = "utf-8"
    except requests.exceptions.RequestException as e:
        print(f"[잡코리아] HTTP 요청 실패: {e}")
        return []

    soup = BeautifulSoup(response.text, "html.parser")
    jobs = []

    # 채용공고 목록 파싱
    # 잡코리아 검색 결과의 채용공고 리스트 구조
    job_items = soup.select("article.list-item") or soup.select("div.list-item")

    if not job_items:
        # 대체 셀렉터 시도
        job_items = soup.select("div.recruit-info") or soup.select("li.list-post")

    if not job_items:
        # 최종 대체: 테이블 구조
        job_items = soup.select("tr.list-post") or soup.select("div.post-list-info")

    for item in job_items:
        try:
            job = _parse_job_item(item)
            if job:
                jobs.append(job)
        except Exception as e:
            continue

    # 파싱 실패 시 대체 파싱 시도
    if not jobs:
        jobs = _alternative_parse(soup)

    return jobs


def _parse_job_item(item):
    """
    개별 채용공고 항목을 파싱합니다.

    Args:
        item: BeautifulSoup Tag 객체

    Returns:
        dict or None: 파싱된 채용공고 정보
    """
    # 공고 제목 & 링크
    title_elem = (
        item.select_one("a.list-item-title") or
        item.select_one("a.title") or
        item.select_one("div.post-list-info a") or
        item.select_one("a[href*='/Recruit/']") or
        item.select_one("a")
    )

    if not title_elem:
        return None

    title = title_elem.get_text(strip=True)
    url = title_elem.get("href", "")
    if url and not url.startswith("http"):
        url = JOBKOREA_BASE_URL + url

    # 회사명
    company_elem = (
        item.select_one("a.list-item-corp") or
        item.select_one("a.corp-name") or
        item.select_one("div.post-list-corp a") or
        item.select_one("span.corp-name")
    )
    company = company_elem.get_text(strip=True) if company_elem else ""

    # 마감일
    deadline_elem = (
        item.select_one("span.date") or
        item.select_one("p.option span.date") or
        item.select_one("span.exp")
    )
    deadline_text = deadline_elem.get_text(strip=True) if deadline_elem else ""
    deadline = _parse_deadline(deadline_text)

    # 근무지
    location_elem = (
        item.select_one("span.loc") or
        item.select_one("li.loc") or
        item.select_one("span.cell.local")
    )
    location = location_elem.get_text(strip=True) if location_elem else "전국"

    # 경력 조건
    career_elem = (
        item.select_one("span.career") or
        item.select_one("li.exp")
    )
    experience = career_elem.get_text(strip=True) if career_elem else "신입"

    # 학력
    education_elem = item.select_one("span.edu") or item.select_one("li.edu")
    education = education_elem.get_text(strip=True) if education_elem else ""

    if not title:
        return None

    return {
        "id": f"jk_{hash(url) % 100000:05d}",
        "title": title,
        "company": company,
        "location": location,
        "experience": experience,
        "job_type": "정규직",
        "industry": "IT/통신",
        "deadline": deadline,
        "start_date": "",  # 크롤링에서는 등록일 파싱 어려움
        "url": url,
        "salary": "회사내규에 따름",
        "source": "잡코리아",
    }


def _alternative_parse(soup):
    """
    기본 파싱 실패 시 대체 파싱을 시도합니다.
    잡코리아 HTML 구조가 변경될 경우를 대비한 fallback.
    """
    jobs = []

    # 모든 링크에서 /Recruit/ 패턴을 가진 것을 찾아 파싱
    links = soup.find_all("a", href=re.compile(r"/Recruit/GI_Read/"))
    seen_urls = set()

    for link in links:
        url = link.get("href", "")
        if url in seen_urls:
            continue
        seen_urls.add(url)

        title = link.get_text(strip=True)
        if not title or len(title) < 3:
            continue

        full_url = JOBKOREA_BASE_URL + url if not url.startswith("http") else url

        jobs.append({
            "id": f"jk_{hash(full_url) % 100000:05d}",
            "title": title,
            "company": "",
            "location": "전국",
            "experience": "신입",
            "job_type": "정규직",
            "industry": "IT/통신",
            "deadline": "",
            "start_date": "",
            "url": full_url,
            "salary": "회사내규에 따름",
            "source": "잡코리아",
        })

    return jobs


def _parse_deadline(text):
    """
    마감일 텍스트를 날짜 형식으로 변환합니다.

    Args:
        text (str): 마감일 텍스트 (예: "~06/15(일)", "D-5", "오늘마감", "상시채용")

    Returns:
        str: YYYY-MM-DD 형식의 날짜 또는 빈 문자열
    """
    if not text:
        return ""

    today = datetime.now()

    # "~MM/DD" 패턴
    match = re.search(r"~?\s*(\d{1,2})/(\d{1,2})", text)
    if match:
        month = int(match.group(1))
        day = int(match.group(2))
        year = today.year
        # 이미 지난 달이면 내년으로
        if month < today.month or (month == today.month and day < today.day):
            year += 1
        try:
            deadline = datetime(year, month, day)
            return deadline.strftime("%Y-%m-%d")
        except ValueError:
            pass

    # "~YYYY.MM.DD" 패턴
    match = re.search(r"(\d{4})[.\-/](\d{1,2})[.\-/](\d{1,2})", text)
    if match:
        try:
            deadline = datetime(int(match.group(1)), int(match.group(2)), int(match.group(3)))
            return deadline.strftime("%Y-%m-%d")
        except ValueError:
            pass

    # "D-N" 패턴
    match = re.search(r"D-(\d+)", text)
    if match:
        days = int(match.group(1))
        deadline = today + timedelta(days=days)
        return deadline.strftime("%Y-%m-%d")

    # "오늘마감"
    if "오늘" in text:
        return today.strftime("%Y-%m-%d")

    # "내일마감"
    if "내일" in text:
        return (today + timedelta(days=1)).strftime("%Y-%m-%d")

    # "상시채용" - 30일 후로 설정
    if "상시" in text:
        return (today + timedelta(days=30)).strftime("%Y-%m-%d")

    return ""


def get_jobkorea_sample_data():
    """
    크롤링 실패 시 사용할 잡코리아 샘플 데이터를 반환합니다.
    실제 IT 업계 채용 형태를 반영한 데모 데이터입니다.
    """
    today = datetime.now()

    return [
        {
            "id": "jk_sample_001",
            "title": "[신입] Python 백엔드 개발자",
            "company": "비바리퍼블리카(토스)",
            "location": "서울 강남구",
            "experience": "신입",
            "job_type": "정규직",
            "industry": "IT/통신",
            "deadline": (today + timedelta(days=6)).strftime("%Y-%m-%d"),
            "start_date": (today - timedelta(days=4)).strftime("%Y-%m-%d"),
            "url": "https://www.jobkorea.co.kr",
            "salary": "회사내규에 따름",
            "source": "잡코리아",
        },
        {
            "id": "jk_sample_002",
            "title": "웹 프론트엔드 개발 (Vue.js/TypeScript)",
            "company": "크래프톤",
            "location": "서울 강남구",
            "experience": "신입/경력",
            "job_type": "정규직",
            "industry": "IT/통신",
            "deadline": (today + timedelta(days=12)).strftime("%Y-%m-%d"),
            "start_date": (today - timedelta(days=2)).strftime("%Y-%m-%d"),
            "url": "https://www.jobkorea.co.kr",
            "salary": "4,000만원 이상",
            "source": "잡코리아",
        },
        {
            "id": "jk_sample_003",
            "title": "[신입] 클라우드 인프라 엔지니어 (AWS)",
            "company": "카카오엔터프라이즈",
            "location": "경기 판교",
            "experience": "신입",
            "job_type": "정규직",
            "industry": "IT/통신",
            "deadline": (today + timedelta(days=8)).strftime("%Y-%m-%d"),
            "start_date": (today - timedelta(days=6)).strftime("%Y-%m-%d"),
            "url": "https://www.jobkorea.co.kr",
            "salary": "회사내규에 따름",
            "source": "잡코리아",
        },
        {
            "id": "jk_sample_004",
            "title": "데이터 분석가 (신입/인턴전환)",
            "company": "우아한형제들",
            "location": "서울 송파구",
            "experience": "신입",
            "job_type": "정규직",
            "industry": "IT/통신",
            "deadline": (today + timedelta(days=4)).strftime("%Y-%m-%d"),
            "start_date": (today - timedelta(days=8)).strftime("%Y-%m-%d"),
            "url": "https://www.jobkorea.co.kr",
            "salary": "3,800만원 이상",
            "source": "잡코리아",
        },
        {
            "id": "jk_sample_005",
            "title": "[채용전환형] ML 엔지니어 인턴",
            "company": "네이버클라우드",
            "location": "경기 성남시",
            "experience": "신입",
            "job_type": "인턴",
            "industry": "IT/통신",
            "deadline": (today + timedelta(days=16)).strftime("%Y-%m-%d"),
            "start_date": (today - timedelta(days=1)).strftime("%Y-%m-%d"),
            "url": "https://www.jobkorea.co.kr",
            "salary": "회사내규에 따름",
            "source": "잡코리아",
        },
        {
            "id": "jk_sample_006",
            "title": "iOS 개발자 (Swift) 신입",
            "company": "쏘카",
            "location": "서울 성동구",
            "experience": "신입",
            "job_type": "정규직",
            "industry": "IT/통신",
            "deadline": (today + timedelta(days=9)).strftime("%Y-%m-%d"),
            "start_date": (today - timedelta(days=3)).strftime("%Y-%m-%d"),
            "url": "https://www.jobkorea.co.kr",
            "salary": "회사내규에 따름",
            "source": "잡코리아",
        },
        {
            "id": "jk_sample_007",
            "title": "[신입] 정보보안 컨설턴트",
            "company": "안랩",
            "location": "경기 판교",
            "experience": "신입",
            "job_type": "정규직",
            "industry": "IT/통신",
            "deadline": (today + timedelta(days=11)).strftime("%Y-%m-%d"),
            "start_date": (today - timedelta(days=5)).strftime("%Y-%m-%d"),
            "url": "https://www.jobkorea.co.kr",
            "salary": "3,500만원 이상",
            "source": "잡코리아",
        },
        {
            "id": "jk_sample_008",
            "title": "게임 클라이언트 프로그래머 (Unity)",
            "company": "넷마블",
            "location": "서울 구로구",
            "experience": "신입",
            "job_type": "정규직",
            "industry": "IT/통신",
            "deadline": (today + timedelta(days=13)).strftime("%Y-%m-%d"),
            "start_date": (today - timedelta(days=7)).strftime("%Y-%m-%d"),
            "url": "https://www.jobkorea.co.kr",
            "salary": "4,200만원 이상",
            "source": "잡코리아",
        },
        {
            "id": "jk_sample_009",
            "title": "[신입] DevOps 엔지니어 (K8s/Docker)",
            "company": "카카오뱅크",
            "location": "경기 판교",
            "experience": "신입",
            "job_type": "정규직",
            "industry": "IT/통신",
            "deadline": (today + timedelta(days=7)).strftime("%Y-%m-%d"),
            "start_date": (today - timedelta(days=4)).strftime("%Y-%m-%d"),
            "url": "https://www.jobkorea.co.kr",
            "salary": "회사내규에 따름",
            "source": "잡코리아",
        },
        {
            "id": "jk_sample_010",
            "title": "플랫폼 서버 개발자 (Java/Kotlin)",
            "company": "컬리",
            "location": "서울 송파구",
            "experience": "신입/경력",
            "job_type": "정규직",
            "industry": "IT/통신",
            "deadline": (today + timedelta(days=5)).strftime("%Y-%m-%d"),
            "start_date": (today - timedelta(days=10)).strftime("%Y-%m-%d"),
            "url": "https://www.jobkorea.co.kr",
            "salary": "4,500만원 이상",
            "source": "잡코리아",
        },
    ]


if __name__ == "__main__":
    print("=== 잡코리아 IT/인터넷 신입 채용공고 크롤링 ===\n")

    # 크롤링 시도
    jobs = crawl_jobkorea(pages=2, keyword="IT 개발")

    # 크롤링 결과가 없으면 샘플 데이터 사용
    if not jobs:
        print("[INFO] 크롤링 결과가 없어 샘플 데이터를 사용합니다.\n")
        jobs = get_jobkorea_sample_data()

    print(f"\n총 {len(jobs)}개의 채용공고를 수집했습니다.\n")
    for job in jobs[:5]:
        print(f"  [{job['company']}] {job['title']}")
        print(f"    - 마감일: {job['deadline']}")
        print(f"    - 근무지: {job['location']}")
        print()
