"""
실시간 채용 캘린더 웹 애플리케이션
- IT/인터넷 직무, IT/통신 업종, 신입, 전국
- 사람인 Open API 연동
- FullCalendar.js 기반 캘린더 UI
"""
from flask import Flask, render_template, jsonify, request
from job_fetcher import fetch_jobs_from_saramin, get_calendar_events
from config import FLASK_PORT

app = Flask(__name__)

# 캐시된 채용 데이터
cached_jobs = None


@app.route("/")
def index():
    """메인 캘린더 페이지"""
    return render_template("index.html")


@app.route("/api/events")
def api_events():
    """
    캘린더 이벤트 API 엔드포인트
    FullCalendar에서 호출하여 채용 공고를 이벤트로 표시
    """
    global cached_jobs
    
    # 강제 새로고침 파라미터
    refresh = request.args.get("refresh", "false") == "true"
    
    if cached_jobs is None or refresh:
        cached_jobs = fetch_jobs_from_saramin()
    
    events = get_calendar_events(cached_jobs)
    return jsonify(events)


@app.route("/api/jobs")
def api_jobs():
    """
    채용 공고 목록 API
    필터링 및 정렬 지원
    """
    global cached_jobs
    
    if cached_jobs is None:
        cached_jobs = fetch_jobs_from_saramin()
    
    # 정렬: 마감일 가까운 순
    sorted_jobs = sorted(
        cached_jobs,
        key=lambda x: x.get("deadline", "9999-12-31")
    )
    
    return jsonify(sorted_jobs)


@app.route("/api/refresh", methods=["POST"])
def api_refresh():
    """채용 정보 강제 갱신"""
    global cached_jobs
    cached_jobs = fetch_jobs_from_saramin()
    return jsonify({"status": "ok", "count": len(cached_jobs)})


if __name__ == "__main__":
    print("=" * 50)
    print("  IT/인터넷 신입 채용 캘린더 서버 시작")
    print("  http://localhost:5000")
    print("=" * 50)
    app.run(debug=True, port=FLASK_PORT, host="0.0.0.0")
