"""
정적 사이트 빌드 스크립트
- GitHub Pages 배포를 위해 API 응답을 JSON 파일로 생성
- index.html을 정적 버전으로 변환하여 dist/ 에 출력
"""
import json
import os
import shutil
from datetime import datetime
from job_fetcher import fetch_all_jobs, get_calendar_events, get_available_filters


def build():
    """정적 사이트를 빌드합니다."""
    print("=== 정적 사이트 빌드 시작 ===")
    print(f"빌드 시각: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    # dist 디렉토리 생성
    dist_dir = "dist"
    if os.path.exists(dist_dir):
        shutil.rmtree(dist_dir)
    os.makedirs(dist_dir, exist_ok=True)
    os.makedirs(os.path.join(dist_dir, "api"), exist_ok=True)

    # 채용 데이터 수집
    print("\n[1/4] 채용 데이터 수집 중...")
    jobs = fetch_all_jobs()
    print(f"  → {len(jobs)}개 수집 완료")

    # API 응답을 JSON 파일로 저장
    print("[2/4] API JSON 파일 생성 중...")

    # /api/events
    events = get_calendar_events(jobs)
    with open(os.path.join(dist_dir, "api", "events.json"), "w", encoding="utf-8") as f:
        json.dump(events, f, ensure_ascii=False, indent=2)

    # /api/jobs
    sorted_jobs = sorted(jobs, key=lambda x: x.get("deadline", "9999-12-31"))
    with open(os.path.join(dist_dir, "api", "jobs.json"), "w", encoding="utf-8") as f:
        json.dump(sorted_jobs, f, ensure_ascii=False, indent=2)

    # /api/filters
    filters = get_available_filters(jobs)
    with open(os.path.join(dist_dir, "api", "filters.json"), "w", encoding="utf-8") as f:
        json.dump(filters, f, ensure_ascii=False, indent=2)

    # 메타 정보
    meta = {
        "updated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "total_count": len(jobs),
        "events_count": len(events),
    }
    with open(os.path.join(dist_dir, "api", "meta.json"), "w", encoding="utf-8") as f:
        json.dump(meta, f, ensure_ascii=False, indent=2)

    print(f"  → events.json ({len(events)}개)")
    print(f"  → jobs.json ({len(sorted_jobs)}개)")
    print(f"  → filters.json")
    print(f"  → meta.json")

    # index.html 생성 (정적 버전)
    print("[3/4] index.html 정적 버전 생성 중...")
    build_static_html(dist_dir, meta)

    # static 디렉토리 복사
    print("[4/4] 정적 파일 복사 중...")
    static_src = "static"
    if os.path.exists(static_src):
        shutil.copytree(static_src, os.path.join(dist_dir, "static"))

    print(f"\n=== 빌드 완료! ===")
    print(f"출력 디렉토리: {dist_dir}/")
    print(f"총 공고 수: {len(jobs)}개")


def build_static_html(dist_dir, meta):
    """
    정적 배포용 index.html을 생성합니다.
    Flask API 호출 대신 JSON 파일을 직접 참조하도록 수정합니다.
    """
    # 원본 템플릿 읽기
    with open("templates/index.html", "r", encoding="utf-8") as f:
        html = f.read()

    # API URL을 정적 JSON 파일 경로로 변환
    html = html.replace("'/api/events'", "'api/events.json'")
    html = html.replace("/api/events", "api/events.json")
    html = html.replace("'/api/filters'", "'api/filters.json'")
    html = html.replace("/api/filters", "api/filters.json")
    html = html.replace("'/api/refresh'", "'api/events.json'")
    html = html.replace("/api/refresh", "api/events.json")

    # 새로고침 버튼을 "마지막 갱신" 정보로 대체
    updated_at = meta.get("updated_at", "")
    html = html.replace(
        "fetch('api/events.json', { method: 'POST' })",
        "fetch('api/events.json')"
    )

    # 갱신 알림 메시지 수정
    html = html.replace(
        "채용 정보가 갱신되었습니다!",
        f"마지막 갱신: {updated_at}"
    )

    # 정적 페이지 안내 배너 추가 (헤더 p 태그 뒤)
    static_notice = f'<p style="font-size:12px;opacity:0.7;margin-top:4px;">마지막 데이터 갱신: {updated_at} | 매일 오전 9시(KST) 자동 갱신됩니다</p>'
    html = html.replace(
        '<div class="badges">',
        f'{static_notice}\n        <div class="badges">'
    )

    with open(os.path.join(dist_dir, "index.html"), "w", encoding="utf-8") as f:
        f.write(html)

    print(f"  → index.html (정적 버전)")


if __name__ == "__main__":
    build()
