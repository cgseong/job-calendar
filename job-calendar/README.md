# IT/인터넷 신입 채용 캘린더

학부생들의 취업을 돕기 위한 **실시간 채용 캘린더** 웹 애플리케이션입니다.

![Python](https://img.shields.io/badge/Python-3.9+-blue)
![Flask](https://img.shields.io/badge/Flask-3.1-green)
![FullCalendar](https://img.shields.io/badge/FullCalendar-6.1-orange)

## 주요 기능

- 채용 공고를 **캘린더 형태**로 시각화 (마감일 기준)
- **마감 임박도**에 따른 색상 표시 (빨강/주황/파랑/초록)
- 공고 클릭 시 **상세 정보** 모달 및 바로 지원 링크
- 사이드바에 **마감 임박 공고** 목록 표시
- **사람인 Open API** 연동 (실시간 데이터)

## 검색 조건

| 항목 | 조건 |
|------|------|
| 직무 | IT/인터넷 |
| 업종 | IT/통신 |
| 경력 | 신입 |
| 지역 | 전국 |

## 기술 스택

- **Backend**: Python, Flask
- **Frontend**: HTML5, CSS3, JavaScript
- **캘린더**: [FullCalendar 6.x](https://fullcalendar.io/)
- **데이터 소스**: 사람인 Open API (`oapi.saramin.co.kr`)

## 설치 및 실행

### 1. 의존성 설치

```bash
cd job-calendar
pip install -r requirements.txt
```

### 2. 환경 변수 설정 (선택)

```bash
cp .env.example .env
# .env 파일을 편집하여 사람인 API 키를 입력합니다.
# API 키가 없어도 샘플 데이터로 동작합니다.
```

> 사람인 API 키는 [https://oapi.saramin.co.kr](https://oapi.saramin.co.kr) 에서 무료로 발급받을 수 있습니다.

### 3. 서버 실행

```bash
python app.py
```

브라우저에서 `http://localhost:5000` 으로 접속하세요.

## 프로젝트 구조

```
job-calendar/
├── app.py              # Flask 메인 애플리케이션
├── job_fetcher.py      # 채용 정보 수집 모듈 (사람인 API 연동)
├── config.py           # 설정 파일 (검색 조건, API 설정)
├── requirements.txt    # Python 패키지 의존성
├── .env.example        # 환경 변수 예제
├── .gitignore
├── templates/
│   └── index.html      # 캘린더 UI (FullCalendar + 사이드바)
└── static/             # 정적 파일 (필요 시)
```

## 캘린더 색상 가이드

| 색상 | 의미 |
|------|------|
| 🔴 빨강 | 3일 이내 마감 (긴급!) |
| 🟠 주황 | 7일 이내 마감 |
| 🔵 파랑 | 14일 이내 마감 |
| 🟢 초록 | 여유 있음 |
| ⚫ 회색 | 마감됨 |

## API 엔드포인트

| 메서드 | 경로 | 설명 |
|--------|------|------|
| GET | `/` | 메인 캘린더 페이지 |
| GET | `/api/events` | 캘린더 이벤트 데이터 |
| GET | `/api/jobs` | 채용공고 목록 |
| POST | `/api/refresh` | 채용 정보 강제 갱신 |

## 확장 방향

- [ ] 크롤링 기반 데이터 수집 추가 (잡코리아, 프로그래머스 등)
- [ ] 알림 기능 (마감 D-3, D-1 알림)
- [ ] 관심 공고 북마크
- [ ] 회사별/직무별 필터링 기능
- [ ] 배포 자동화 (GitHub Actions + 정기 데이터 갱신)

## 라이센스

MIT License
