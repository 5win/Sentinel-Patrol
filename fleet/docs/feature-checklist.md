# Sentinel-Patrol — 기능 구현 체크리스트

`fleet/docs/03-api-design.md`에 명세된 단위 기능을 체크리스트로 정리한 문서. 구현 진행 상황 추적용.

- 각 항목 옆 `[P1]/[P2]/[P3]`는 구현 Phase.
- 최상위 섹션은 카테고리, 하위 항목은 구현 단위(엔드포인트/메시지/모델).

---

## 1. 기반 / Conventions

- [ ] REST base path `/api/v1` 라우터 구성 [P1]
- [ ] WebSocket 경로 `/ws` 라우터 구성 [P1]
- [ ] 정적 에셋 경로 `/static` (맵 이미지) [P1]
- [ ] RFC 7807 `application/problem+json` 에러 응답 미들웨어 [P1]
- [ ] 타임스탬프 규약 (RFC 3339 UTC, WS는 `ts_ms` 추가) [P1]
- [ ] 단위/좌표 규약 (m, rad, ROS `map` frame) [P1]
- [ ] UUID v4 ID 정책 [P1]
- [ ] 페이지네이션 표준 (`page`, `page_size`, `total`) [P1]
- [ ] 필터/정렬 쿼리 파라미터 표준 [P1]

## 2. 인증 / 권한 (단순 세션 토큰)

- [ ] 세션 토큰 검증 미들웨어 (DB 조회, 30일 만료) [P1]
- [ ] WebSocket 핸드셰이크 토큰 검증 (`?token=`) [P1]
- [ ] 하드코딩 시드 계정 `admin` / `admin` 등록 [P1]
- [ ] 비인증 vs admin 2단계 접근 제어 [P1]

## 3. 공용 스키마 (Shared Schemas)

- [ ] `RobotStatus` 열거형 (IDLE/PATROLLING/WAIT/EMERGENCY/AVOIDING/RETURNING/MANUAL/OFFLINE) [P1]
- [ ] `Pose` 스키마 [P1]
- [ ] `Waypoint` 스키마 [P1]
- [ ] `Robot` 스키마 (`battery` nullable, `is_simulated` 포함) [P1]
- [ ] `Map` 스키마 [P1]
- [ ] `Mission` 스키마 [P3]
- [ ] `Assignment` 스키마 [P3]
- [ ] `Event` 스키마 + event_type별 payload [P1]
- [ ] `Alarm` 스키마 [P1]
- [ ] `User` 스키마 [P1]
- [ ] `TeleopLock` 스키마 [P2]

## 4. REST — Auth

- [ ] `POST /api/v1/auth/login` [P1]
- [ ] `POST /api/v1/auth/logout` [P1]
- [ ] `GET  /api/v1/auth/me` [P1]

## 5. REST — Robots

- [ ] `GET  /api/v1/robots` (필터/정렬/페이지네이션) [P1]
- [ ] `GET  /api/v1/robots/:robotId` [P1]
- [ ] `GET  /api/v1/robots/:robotId/waypoints` [P1]
- [ ] `GET  /api/v1/robots/:robotId/status-history` [P1]

## 6. REST — Robot Control

- [ ] `POST /api/v1/robots/:robotId/control/start` (teleop 락 획득) [P2]
- [ ] `POST /api/v1/robots/:robotId/control/stop` (락 해제) [P2]
- [ ] `POST /api/v1/robots/:robotId/control/emergency-stop` [P2]

## 7. REST — Assignments

- [ ] `POST /api/v1/assignments` (멀티 로봇 `robot_ids[]`) [P3]
- [ ] `GET  /api/v1/assignments/:assignmentId` [P3]
- [ ] `PATCH /api/v1/assignments/:assignmentId` [P3]

## 8. REST — Maps

- [ ] `GET  /api/v1/maps` [P1]
- [ ] `GET  /api/v1/maps/:mapId` [P1]
- [ ] `POST /api/v1/maps` (파일 업로드) [P3]
- [ ] `PATCH /api/v1/maps/:mapId` [P3]
- [ ] `DELETE /api/v1/maps/:mapId` [P3]

## 9. REST — Missions

- [ ] `GET  /api/v1/missions` [P3]
- [ ] `GET  /api/v1/missions/:missionId` [P3]
- [ ] `POST /api/v1/missions` [P3]
- [ ] `PUT  /api/v1/missions/:missionId` [P3]
- [ ] `DELETE /api/v1/missions/:missionId` [P3]
- [ ] `POST /api/v1/missions/:missionId/push` (ROS `set_waypoints` 호출) [P3]

## 10. REST — Events / Alarms / System

- [ ] `GET  /api/v1/events` [P1]
- [ ] `GET  /api/v1/events/export` [P1]
- [ ] `GET  /api/v1/alarms` [P1]
- [ ] `POST /api/v1/alarms/:alarmId/acknowledge` [P1]
- [ ] `GET  /api/v1/system/time` [P1]

## 11. WebSocket — Envelope & Infra

- [ ] 메시지 envelope `{v, type, robot_id, ts_ms, data}` [P1]
- [ ] 연결 인증 핸드셰이크 [P1]
- [ ] 하트비트 (`ping`/`pong`) [P1]
- [ ] 재연결 시 `snapshot` 전송 (snapshot + delta 복원) [P1]
- [ ] pose 메시지 스로틀 (서버 측) [P1]
- [ ] `teleop_cmd` 수신 레이트 리밋 [P2]
- [ ] WebSocket 동시 연결 수 제한 [P1]

## 12. WebSocket — 서버→클라 메시지

- [ ] `snapshot` [P1]
- [ ] `pose` (신 포맷, robot_id 포함) [P1]
- [ ] `state` (prev_status 포함) [P1]
- [ ] `waypoints` [P1]
- [ ] `current_wp` (`index`, `total`) [P1]
- [ ] `plan` [P1]
- [ ] `alarm` [P1]
- [ ] `event` [P1]
- [ ] `robot_online` / `robot_offline` (15s 타임아웃 감지) [P1]
- [ ] `teleop_lock_change` [P2]
- [ ] `assignment_update` [P3]
- [ ] `error` [P1]

## 13. WebSocket — 클라→서버 메시지

- [ ] `ping` 하트비트 [P1]
- [ ] `teleop_cmd` (linear_x / angular_z) [P2]

## 14. Control Flow & Lifecycle

- [ ] Idempotency-Key 헤더 처리 [P1]
- [ ] Assignment lifecycle (REST → ROS `set_waypoints` → WS `assignment_update`) [P3]
- [ ] Teleop lifecycle (락 획득 → WS 명령 → 락 해제) [P2]
- [ ] Teleop 데드맨 타이머 (200ms) [P2]
- [ ] Teleop 락 자동 만료 (30s, WS 끊김 시 즉시 해제) [P2]
- [ ] Waypoint Push lifecycle [P3]

## 15. 에러 모델 (Error Taxonomy)

- [ ] 인증/권한 에러 코드군 [P1]
- [ ] 리소스 에러 코드군 [P1]
- [ ] 비즈니스 로직 에러 코드군 [P1]
- [ ] 파일/서버 에러 코드군 [P1]
- [ ] WebSocket error 코드군 [P1]

## 16. 인프라 / 데이터 저장

- [ ] DB 선택 및 스키마 (SQLite + SQLAlchemy, Alembic 마이그레이션) [P1]
- [ ] Robot / Map / Mission / Assignment / Event / Alarm 테이블 [P1~P3]
- [ ] 감사 로그 `Event` 기록 파이프라인 [P1]

## 17. ROS 연동 변경 (patrol_manager 측)

- [ ] 토픽 네임스페이스화 (`/<robot_ns>/amcl_pose` 등) [P1]
- [ ] `set_waypoints` ROS 서비스 추가 [P3]
- [ ] `MANUAL` 상태 추가 (또는 WAIT에서 cmd_vel 허용) [P2]
- [ ] `/battery_state` 구독 [P1]

## 18. 기존 백엔드 리팩토링 (Breaking)

- [ ] WS `pose` 메시지 신 포맷 전환 [P1]
- [ ] WS `state` 메시지 신 포맷 (`{status, prev_status}`) [P1]
- [ ] WS `current_wp` 메시지 신 포맷 (`{index, total}`) [P1]
- [ ] 기존 대시보드(`fleet/frontend/dashboard/index.html`) 교체 [P1]

## 19. Open Questions (해소 추적)

- [ ] OQ-API-1 — MANUAL 상태 진입 방식 (기본값: 신규 상태 + `~/enter_manual` 서비스)
- [ ] OQ-API-2 — Teleop 최대 속도 (기본값: 0.5 m/s, 1.0 rad/s)
- [ ] OQ-API-3 — 배터리 텔레메트리 소스 (기본값: `battery: null`)
- [ ] OQ-API-4 — `set_waypoints` 서비스 인터페이스 (기본값: `sentinel_msgs/srv/SetWaypoints`)
- [ ] OQ-API-5 — 카메라 스트리밍 방식 (Phase 2 시작 전 해소 필요)
- [ ] OQ-API-6 — Teleop 락 자동 만료 시간 (기본값: 30s)
- [ ] OQ-API-7 — is_simulated 관리 방법 (기본값: 수동 설정)
- [ ] OQ-API-8 — DB 선택 (기본값: SQLite)
