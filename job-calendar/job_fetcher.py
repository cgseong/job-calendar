"""
채용 정보 수집 모듈
- 사람인 Open API를 통한 실시간 채용 정보 수집
- API 키 미설정 시 샘플 데이터 제공 (데모용)
"""
import requests
import json
import os
from datetime import datetime, timedelta
from config import SARAMIN_API_KEY, SARAMIN_API_URL, SEARCH_PARAMS


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


def parse_saramin_jobs(jobs):
    """
    사람인 API 응답을 캘린더 이벤트 형식으로 변환합니다.
    
    Args:
        jobs (list): 사람인 API 원본 응답의 job 리스트
    
    Returns:
        list: 파싱된 채용공고 리스트
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
        })
    
    return parsed


def get_sample_jobs():
    """
    데모용 샘플 채용 데이터를 생성합니다.
    실제 IT/통신 업계 신입 채용 형태를 반영합니다.
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
        },
    ]
    
    return sample_jobs


def get_calendar_events(jobs=None):
    """
    채용공고를 FullCalendar 이벤트 형식으로 변환합니다.
    마감일 기준으로 캘린더에 표시됩니다.
    
    Args:
        jobs (list, optional): 채용공고 리스트. None이면 API에서 가져옴.
    
    Returns:
        list: FullCalendar 이벤트 형식 리스트
    """
    if jobs is None:
        jobs = fetch_jobs_from_saramin()
    
    events = []
    
    # 마감일 임박도에 따른 색상 지정
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
            "start": job.get("start_date", job["deadline"]),
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
            }
        }
        events.append(event)
    
    return events


if __name__ == "__main__":
    # 테스트 실행
    print("=== IT/인터넷 신입 채용 정보 수집 ===")
    jobs = fetch_jobs_from_saramin()
    print(f"\n총 {len(jobs)}개의 채용공고를 수집했습니다.\n")
    
    for job in jobs[:5]:
        print(f"  [{job['company']}] {job['title']}")
        print(f"    - 마감일: {job['deadline']}")
        print(f"    - 근무지: {job['location']}")
        print(f"    - 급여: {job['salary']}")
        print()
