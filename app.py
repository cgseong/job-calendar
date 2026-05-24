"""
실시간 채용 캘린더 웹 애플리케이션
- IT/인터넷 직무, IT/통신 업종, 신입, 전국
- 사람인 Open API + 잡코리아 크롤링 통합
- 회사별/직무별 필터링 지원
- FullCalendar.js 기반 캘린더 UI
"""
from flask import Flask, render_template, jsonify, request
from job_fetcher import fetch_all_jobs, get_calendar_events, apply_filters, get_available_filters
from config import FLASK_PORT

app = Flask(__name__)

# 캐시된 채용 데이터
cached_jobs = None


def _get_jobs():
    """캐시된 채용 데이터를 반환하거나 새로 수집합니다."""
    global cached_jobs
    if cached_jobs is None:
        cached_jobs = fetch_all_jobs()
    return cached_jobs


@app.route("/")
def index():
    """메인 캘린더 페이지"""
    return render_template("index.html")


@app.route("/api/events")
def api_events():
    """
    캘린더 이벤트 API 엔드포인트
    FullCalendar에서 호출하여 채용 공고를 이벤트로 표시

    Query Params:
        refresh (str): "true"이면 캐시 갱신
        company (str): 회사명 필터 (부분 일치)
        job_category (str): 직무 카테고리 필터
        source (str): 데이터 소스 필터 ("사람인", "잡코리아", "all")
        location (str): 지역 필터
    """
    global cached_jobs

    refresh = request.args.get("refresh", "false") == "true"
    if cached_jobs is None or refresh:
        cached_jobs = fetch_all_jobs()

    # 필터 파라미터 수집
    filters = {
        "company": request.args.get("company", ""),
        "job_category": request.args.get("job_category", ""),
        "source": request.args.get("source", ""),
        "location": request.args.get("location", ""),
    }

    # 필터가 모두 비어있으면 None (전체 표시)
    has_filter = any(v for v in filters.values())
    events = get_calendar_events(cached_jobs, filters if has_filter else None)

    return jsonify(events)


@app.route("/api/jobs")
def api_jobs():
    """
    채용 공고 목록 API (필터링 + 정렬 지원)

    Query Params:
        company (str): 회사명 필터
        job_category (str): 직무 카테고리 필터
        source (str): 데이터 소스 필터
        location (str): 지역 필터
    """
    jobs = _get_jobs()

    # 필터 파라미터 수집
    filters = {
        "company": request.args.get("company", ""),
        "job_category": request.args.get("job_category", ""),
        "source": request.args.get("source", ""),
        "location": request.args.get("location", ""),
    }

    has_filter = any(v for v in filters.values())
    if has_filter:
        jobs = apply_filters(jobs, filters)

    # 정렬: 마감일 가까운 순
    sorted_jobs = sorted(
        jobs,
        key=lambda x: x.get("deadline", "9999-12-31")
    )

    return jsonify(sorted_jobs)


@app.route("/api/filters")
def api_filters():
    """
    사용 가능한 필터 옵션 API
    UI에서 드롭다운 옵션을 동적으로 생성할 때 사용
    """
    jobs = _get_jobs()
    filters = get_available_filters(jobs)
    return jsonify(filters)


@app.route("/api/refresh", methods=["POST"])
def api_refresh():
    """채용 정보 강제 갱신 (사람인 + 잡코리아 재수집)"""
    global cached_jobs
    cached_jobs = fetch_all_jobs()
    return jsonify({"status": "ok", "count": len(cached_jobs)})


if __name__ == "__main__":
    import socket

    def find_available_port(start_port=5001, max_tries=10):
        """사용 가능한 포트를 찾습니다."""
        for port in range(start_port, start_port + max_tries):
            try:
                with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                    s.bind(("0.0.0.0", port))
                    return port
            except OSError:
                continue
        return start_port + max_tries

    port = FLASK_PORT
    # 포트가 사용 중이면 자동으로 다른 포트 탐색
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.bind(("0.0.0.0", port))
    except OSError:
        port = find_available_port(port + 1)
        print(f"[WARN] 포트 {FLASK_PORT}이 사용 중입니다. 포트 {port}으로 시작합니다.")

    print("=" * 50)
    print("  IT/인터넷 신입 채용 캘린더 서버 시작")
    print(f"  http://localhost:{port}")
    print("  데이터 소스: 사람인 API + 잡코리아 크롤링")
    print("=" * 50)
    app.run(debug=True, port=port, host="0.0.0.0", use_reloader=False)
