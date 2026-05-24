"""
채용 캘린더 설정 파일
- 사람인 웹 크롤링 기반 채용 정보 수집
- IT개발/데이터 직무, 전 지역, 신입
"""
import os
from dotenv import load_dotenv

load_dotenv()

# 사람인 웹 크롤링 설정
SARAMIN_BASE_URL = "https://www.saramin.co.kr/zf_user/search/recruit"

# 검색 키워드 (IT개발/데이터 직무 관련)
# 여러 키워드로 검색하여 다양한 IT 채용공고를 수집
SEARCH_KEYWORDS = [
    "웹개발자",
    "백엔드 개발",
    "프론트엔드 개발",
    "풀스택 개발자",
    "데이터 엔지니어",
    "AI 개발자",
]

# 검색 파라미터 (공통)
SEARCH_PARAMS = {
    "searchType": "search",
    "recruitSort": "pd",          # 마감일순 정렬
    "recruitPageCount": "40",     # 페이지당 40건
    "exp_cd": "1",                # 신입
    # 지역: 파라미터 미지정 = 전 지역
}

# 크롤링 설정
CRAWL_CONFIG = {
    "max_pages_per_keyword": 2,   # 키워드당 최대 크롤링 페이지 수
    "request_delay": 1.0,         # 요청 간 대기 시간(초)
    "timeout": 10,                # HTTP 요청 타임아웃(초)
    "max_total_jobs": 150,        # 최대 수집 공고 수
}

# HTTP 요청 헤더 (봇 차단 방지)
REQUEST_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "ko-KR,ko;q=0.9,en-US;q=0.8,en;q=0.7",
    "Accept-Encoding": "gzip, deflate, br",
    "Connection": "keep-alive",
}

# Flask 설정
FLASK_PORT = int(os.getenv("FLASK_PORT", 5000))
