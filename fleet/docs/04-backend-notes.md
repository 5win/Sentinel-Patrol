# 04 Backend Notes

## 구현 범위

현재 `fleet/backend/main.py`는 단일 파일 구현 상태입니다. 계약서(`03-api-design.md`)가 갱신되는 시점에 레이어 분리 리팩토링을 진행할 예정입니다.

## 정적 파일 서빙 경로 변경 이력

| 날짜       | 변경 내용 |
|------------|-----------|
| 2026-04-14 | 프론트엔드 빌드 출력 경로 변경에 따라 정적 파일 마운트 경로 수정 |

### 변경 전

```python
DASHBOARD_DIR = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "frontend", "dashboard")
)
app.mount("/", StaticFiles(directory=DASHBOARD_DIR, html=True), name="dashboard")
```

### 변경 후

```python
FRONTEND_DIST_DIR = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "frontend", "dist")
)
app.mount("/", StaticFiles(directory=FRONTEND_DIST_DIR, html=True), name="frontend")
```

배경: `fleet/frontend/`가 Vite 프로젝트 루트로 재편되면서 빌드 출력 경로가 `frontend/dashboard/` → `frontend/dist/`로 변경되었습니다 (참고: `05-frontend-notes.md` 섹션 6).

## ROS Topic / QoS 호환성

기존 구독 토픽과 QoS 설정을 그대로 유지합니다.

| 토픽 | 타입 | QoS |
|------|------|-----|
| `/amcl_pose` | `PoseWithCovarianceStamped` | depth=10 |
| `/plan` | `Path` | depth=10 |
| `/patrol/state` | `String` | depth=10 |
| `/patrol/waypoints` | `PoseArray` | TRANSIENT_LOCAL, depth=1 (latched) |
| `/patrol/current_waypoint` | `Int32` | depth=10 |

## 실행 방법

ROS2 Humble/Iron 환경에서:

```bash
# 프로젝트 루트에서
source /opt/ros/humble/setup.bash
uvicorn fleet.backend.main:app --host 0.0.0.0 --port 8000 --reload
```

또는 `fleet/backend/` 디렉터리에서:

```bash
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

## Open Questions

- `03-api-design.md` 계약서가 작성되면, 현재 단일 파일 구조를 아키텍처 원칙에 따라 레이어 분리 리팩토링해야 합니다.
