"""
채용 캘린더 설정 파일
- 사람인 Open API 파라미터 설정
- IT/인터넷 직무, IT/통신 업종, 신입, 전국
"""
import os
from dotenv import load_dotenv

load_dotenv()

# 사람인 Open API 설정
SARAMIN_API_KEY = os.getenv("SARAMIN_API_KEY", "")
SARAMIN_API_URL = "https://oapi.saramin.co.kr/job-search"

# 검색 조건
SEARCH_PARAMS = {
    # 직무 코드: IT/인터넷 (직무 중분류)
    # 2 = IT개발·데이터, 84 = 정보보안, 16 = 인터넷·IT
    "job_mid_cd": "2",
    
    # 업종 코드: IT/통신
    # 3 = IT·웹·통신
    "ind_cd": "3",
    
    # 경력 조건: 신입
    # 1 = 신입
    "exp_cd": "1",
    
    # 지역: 전국 (지정 안하면 전국)
    # "loc_cd": "",
    
    # 정렬: 마감일순
    "sort": "pd",
    
    # 결과 개수
    "count": "110",
}

# Flask 설정
FLASK_PORT = int(os.getenv("FLASK_PORT", 5000))
