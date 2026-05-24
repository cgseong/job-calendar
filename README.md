# IT개발/데이터 신입 채용 캘린더

학부생들의 취업을 돕기 위한 **실시간 채용 캘린더** 웹 애플리케이션입니다.  
사람인 웹 크롤링을 통해 IT개발/데이터 직무의 신입 채용공고를 자동 수집하여 캘린더에 표시합니다.

![Python](https://img.shields.io/badge/Python-3.9+-blue)
![Flask](https://img.shields.io/badge/Flask-3.1-green)
![FullCalendar](https://img.shields.io/badge/FullCalendar-6.1-orange)

## 주요 기능

- 🗓️ 채용 공고를 **캘린더 형태**로 시각화 (마감일 기준)
- 🎨 **마감 임박도**에 따른 색상 표시 (빨강/주황/파랑/초록)
- 📋 공고 클릭 시 **상세 정보** 모달 및 바로 지원 링크
- 📊 사이드바에 **채용 현황 통계** + 마감 임박 공고 목록
- 🔍 회사별/직무별/지역별 **필터링** 지원
- 🔄 **실시간 크롤링** (API 키 불필요!)

## 데이터 소스 & 검색 조건

| 항목 | 내용 |
|------|------|
| 데이터 소스 | 사람인(saramin.co.kr) 웹 크롤링 |
| 직무 | IT개발/데이터 (웹개발, 백엔드, 프론트엔드, 풀스택, AI, 데이터엔지니어) |
| 경력 | 신입 |
| 지역 | 전국 |
| 수집량 | 최대 150건 |

## 기술 스택

- **Backend**: Python 3.9+, Flask 3.1
- **크롤링**: requests, BeautifulSoup4
- **Frontend**: HTML5, CSS3, JavaScript (Vanilla)
- **캘린더**: [FullCalendar 6.x](https://fullcalendar.io/)
- **배포**: GitHub Actions + GitHub Pages

## 설치 및 실행

### 1. 의존성 설치

```bash
pip install -r requirements.txt
```

### 2. 환경 변수 설정 (선택)

```bash
cp .env.example .env
```

> API 키 없이도 정상 동작합니다. 사람인 웹 크롤링 방식으로 실시간 데이터를 수집합니다.

### 3. 서버 실행

```bash
python app.py
```

브라우저에서 `http://localhost:5000` 으로 접속하세요.

## 프로젝트 구조

```
job-calendar/
├── app.py                # Flask 메인 애플리케이션
├── job_fetcher.py        # 사람인 웹 크롤링 모듈 (핵심)
├── jobkorea_crawler.py   # 잡코리아 크롤링 모듈 (보조)
├── config.py             # 크롤링 설정 (키워드, 헤더, 속도 제어)
├── build_static.py       # GitHub Pages 정적 사이트 빌드
├── requirements.txt      # Python 패키지 의존성
├── .env.example          # 환경 변수 예제
├── .gitignore
├── data/                 # 수집 데이터 저장 (자동 갱신)
├── templates/
│   └── index.html        # 캘린더 UI (FullCalendar + 사이드바)
└── .github/
    └── workflows/
        └── update-jobs.yml  # 매일 자동 크롤링 & 배포
```

## API 엔드포인트

| 메서드 | 경로 | 설명 |
|--------|------|------|
| GET | `/` | 메인 캘린더 페이지 |
| GET | `/api/events` | 캘린더 이벤트 데이터 (필터링 지원) |
| GET | `/api/jobs` | 채용공고 목록 (정렬+필터링) |
| GET | `/api/filters` | 사용 가능한 필터 옵션 |
| POST | `/api/refresh` | 채용 정보 강제 갱신 |

## 캘린더 색상 가이드

| 색상 | 의미 |
|------|------|
| 🔴 빨강 | 3일 이내 마감 (긴급!) |
| 🟠 주황 | 7일 이내 마감 |
| 🔵 파랑 | 14일 이내 마감 |
| 🟢 초록 | 여유 있음 |
| ⚫ 회색 | 마감됨 |

## GitHub Actions 자동화

- **매일 오전 9시(KST)** 자동으로 채용 데이터 수집
- 수집된 데이터를 `data/jobs.json`에 저장 및 자동 커밋
- GitHub Pages로 정적 사이트 자동 배포

## 라이센스

MIT License
