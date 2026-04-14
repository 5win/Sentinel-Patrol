# Sentinel-Patrol — API 설계 계약서 (03-api-design.md)

- 문서 버전: 0.1
- 작성일: 2026-04-14
- 상태: Draft — be-engineer / fe-engineer 구현용 단일 기준 문서
- 상류 입력: `fleet/docs/01-prd.md` (v0.1), `fleet/docs/02-ui-ux-design.md` (v0.1)

> be-engineer와 fe-engineer는 이 문서만 보고 추가 협의 없이 구현한다.  
> 이 문서에 없는 엔드포인트·필드·에러 코드는 존재하지 않는다.  
> 모호한 사항은 11절 Open Questions를 참조한다.

---

## 목차

1. [Overview & Scope](#1-overview--scope)
2. [Conventions](#2-conventions)
3. [Shared Schemas](#3-shared-schemas)
4. [REST API](#4-rest-api)
5. [Realtime API (WebSocket)](#5-realtime-api-websocket)
6. [Commands & Control Flow](#6-commands--control-flow)
7. [Authorization Matrix](#7-authorization-matrix)
8. [Error Taxonomy](#8-error-taxonomy)
9. [Mapping: UI Screens → API Surface](#9-mapping-ui-screens--api-surface)
10. [Changes vs. Current Backend](#10-changes-vs-current-backend)
11. [Open Questions](#11-open-questions)

---

## 1. Overview & Scope

### 1.1 역할 분리 원칙

| 채널 | 용도 |
|---|---|
| **REST `/api/v1/...`** | 스냅샷 조회, 리소스 CRUD, 명령 발행(idempotency-key 포함), 인증, 페이지네이션 |
| **WebSocket `/ws`** | 고빈도 텔레메트리 스트림(pose/state/plan/waypoints/current_wp), 실시간 알림, teleop 명령 전송 |

### 1.2 현재 백엔드 요약

`fleet/backend/main.py`는 단일 ROS 노드가 `/amcl_pose`, `/plan`, `/patrol/state`, `/patrol/waypoints`, `/patrol/current_waypoint`를 구독해 WebSocket `/ws`로 브로드캐스트하는 최소 구현이다.

이 문서의 계약을 충족하려면 **대부분의 경로가 신규 구현이며**, 기존 WS 메시지 포맷은 `robotId` 추가 및 envelope 변경이 필요하다. 상세는 10절 참조.

### 1.3 구현 단계 (Phase)별 우선순위

이 문서는 Phase 1~3의 API 계약 전체를 기술한다. Phase 표기가 있는 항목은 해당 Phase 이전에는 구현하지 않아도 된다.

---

## 2. Conventions

### 2.1 버저닝

```
REST   base path:  /api/v1
WebSocket path:    /ws
정적 에셋:          /static (맵 이미지 등)
```

모든 REST 엔드포인트는 `/api/v1/` prefix를 가진다. 하위 호환이 깨지는 변경이 생기면 `/api/v2/`를 신설하고 v1을 일정 기간 병행 운영한다.

### 2.2 Auth & Session

#### 2.2.1 인증 방식

테스트 편의를 위해 **단순 opaque session token** 방식을 사용한다.

- `POST /api/v1/auth/login` → `{ token, expires_at }` 반환
- 반환된 `token`은 **30일** 유효한 불투명 문자열(예: 128-bit hex 또는 UUID v4 기반 서버 생성값)이다.
- 이후 모든 REST 요청은 `Authorization: Bearer <token>` 헤더를 포함한다.
- FE는 토큰을 **localStorage**에 저장한다. 페이지 재방문 시 저장된 토큰으로 자동 인증 → "매번 로그인" 부담 없음.
- `refresh` 엔드포인트는 존재하지 않는다. 토큰 만료 시 단순 재로그인.
- 토큰은 서버 DB(또는 인메모리 테이블)에 `(token, user_id, expires_at)` 형태로 저장된다. 요청마다 DB에서 조회하여 검증.

**하드코딩 계정 (시드):** BE는 초기화 시 아래 계정을 DB에 시드한다.

| username | password | role  |
|---|---|---|
| `admin`  | `admin`  | admin |

추가 계정은 DB를 직접 편집하거나 시드 스크립트로 삽입한다. 회원가입 API는 없다.

#### 2.2.2 WebSocket 핸드셰이크 인증

```
GET ws://host/ws?token=<session_token>
```

서버는 연결 수락 전 토큰을 DB에서 조회·검증한다. 유효하지 않거나 만료된 경우 HTTP 401로 업그레이드를 거부한다.

#### 2.2.3 역할 정책

단일 역할 `admin`만 존재한다. 로그인된 사용자는 모든 API에 접근 가능하다. RBAC 확장은 하지 않는다.

### 2.3 Time, Units, Coordinate Frames, IDs

| 항목 | 규약 |
|---|---|
| **시간 표기** | RFC 3339 UTC. 예: `"2026-04-14T09:12:34.123Z"`. WebSocket telemetry는 epoch milliseconds(`ts_ms: number`) 추가 허용 (파싱 비용 절감) |
| **좌표 프레임** | ROS `map` frame 기준. x-right, y-up (ROS 관례). Canvas 렌더 시 y-flip은 프런트엔드 책임 |
| **거리 단위** | 미터 (m) |
| **각도 단위** | 라디안 (rad). 범위 `-π ~ π` |
| **선속도 단위** | m/s |
| **각속도 단위** | rad/s |
| **배터리** | 0.0 ~ 1.0 (float). UI는 `Math.round(battery * 100)%`로 표시 |
| **ID 형식** | 문자열 UUID v4. 예: `"550e8400-e29b-41d4-a716-446655440000"`. robotId는 ROS 네임스페이스에서 파생 가능하나 UUID가 기준 |
| **로봇 색인 (hueIndex)** | 0~9 정수. `robotId` 해시로 FE에서 결정적 계산 (OQ-UI-3 참조) |

### 2.4 Error Model

모든 에러 응답은 `application/problem+json` (RFC 7807) 스타일을 따른다.

```json
{
  "type":     "https://sentinel-patrol.internal/errors/robot-not-found",
  "title":    "Robot Not Found",
  "status":   404,
  "detail":   "Robot with id '550e8400...' does not exist.",
  "instance": "/api/v1/robots/550e8400-e29b-41d4-a716-446655440000",
  "code":     "ROBOT_NOT_FOUND"
}
```

| 필드 | 타입 | 설명 |
|---|---|---|
| `type` | string (URI) | 에러 타입 식별자. 이 문서의 8절 목록 참조 |
| `title` | string | 사람이 읽을 수 있는 에러 요약 (고정 문자열) |
| `status` | integer | HTTP 상태 코드 |
| `detail` | string | 이 요청에서 무슨 일이 있었는지 구체적 설명 |
| `instance` | string | 에러가 발생한 요청 경로 |
| `code` | string | FE가 switch/case할 수 있는 도메인 에러 코드 (8절 참조) |

### 2.5 Pagination / Filtering / Sorting

#### 페이지네이션

커서 기반과 오프셋 기반을 혼용한다.

- **이벤트 로그, 상태 히스토리**: 커서 기반 (`cursor`, `limit`)
- **로봇 목록, 임무 목록**: 오프셋 기반 (`page`, `page_size`, 기본 `page_size=50`)

응답 공통 래퍼:

```json
{
  "data":       [...],
  "pagination": {
    "page":       1,
    "page_size":  50,
    "total":      150,
    "has_next":   true,
    "next_cursor": "eyJpZCI6IjEyMyJ9"
  }
}
```

커서 기반 응답은 `total` 생략 가능, `next_cursor`가 `null`이면 마지막 페이지.

#### 필터

쿼리 파라미터. 복수값은 쉼표 구분.

```
GET /api/v1/robots?status=PATROLLING,EMERGENCY&map_id=<uuid>
GET /api/v1/events?robot_id=<uuid>&event_type=STATE,TELEOP&from=2026-04-14T00:00:00Z&to=2026-04-14T23:59:59Z
```

#### 정렬

```
GET /api/v1/robots?sort=status&order=asc
GET /api/v1/events?sort=ts&order=desc  (기본값)
```

---

## 3. Shared Schemas

모든 스키마는 JSON Schema Draft 2020-12 표기를 따른다. `$ref`는 이 절의 `#/definitions/스키마명`을 참조한다.

### 3.1 RobotStatus (열거형)

```
"IDLE" | "PATROLLING" | "WAIT" | "EMERGENCY" | "AVOIDING" | "RETURNING" | "MANUAL" | "OFFLINE"
```

- `OFFLINE`: 백엔드가 마지막 텔레메트리 수신 후 15초 이상 경과 시 내부적으로 설정하는 파생 상태. ROS 토픽으로 오는 상태가 아니라 백엔드 계산값.

### 3.2 Pose

```json
{
  "x":   { "type": "number", "description": "map frame x, meters" },
  "y":   { "type": "number", "description": "map frame y, meters" },
  "yaw": { "type": "number", "description": "heading angle, radians, range [-π, π]" }
}
```

### 3.3 Waypoint

```json
{
  "index":  { "type": "integer", "description": "0-based sequence index" },
  "x":      { "type": "number",  "description": "map frame x, meters" },
  "y":      { "type": "number",  "description": "map frame y, meters" },
  "yaw":    { "type": "number",  "description": "radians" },
  "label":  { "type": ["string", "null"], "description": "optional human-readable label" }
}
```

### 3.4 Robot

```json
{
  "id":               { "type": "string", "format": "uuid" },
  "name":             { "type": "string", "description": "human-readable name, e.g. 'Robot-01'" },
  "ros_namespace":    { "type": "string", "description": "ROS namespace prefix, e.g. '/robot_01'" },
  "model":            { "type": ["string", "null"] },
  "is_simulated":     { "type": "boolean", "description": "true if this is a simulated robot (see OQ-UI-1)" },
  "current_map_id":   { "type": ["string", "null"], "format": "uuid" },
  "current_mission_id": { "type": ["string", "null"], "format": "uuid" },
  "current_assignment_id": { "type": ["string", "null"], "format": "uuid" },
  "status":           { "$ref": "#/definitions/RobotStatus" },
  "pose":             { "$ref": "#/definitions/Pose", "nullable": true },
  "battery":          { "type": ["number", "null"], "minimum": 0.0, "maximum": 1.0,
                        "description": "null if battery telemetry is not available (OQ-UI-2)" },
  "last_seen_at":     { "type": ["string", "null"], "format": "date-time",
                        "description": "RFC 3339 UTC timestamp of last telemetry received" },
  "created_at":       { "type": "string", "format": "date-time" },
  "updated_at":       { "type": "string", "format": "date-time" }
}
```

### 3.5 Map

```json
{
  "id":          { "type": "string", "format": "uuid" },
  "name":        { "type": "string" },
  "description": { "type": ["string", "null"] },
  "image_url":   { "type": "string", "description": "정적 서빙 URL, e.g. /static/maps/{id}/map.png" },
  "resolution":  { "type": "number", "description": "meters per pixel" },
  "origin_x":    { "type": "number", "description": "map origin x in world frame, meters" },
  "origin_y":    { "type": "number", "description": "map origin y in world frame, meters" },
  "origin_yaw":  { "type": "number", "description": "map origin yaw, radians" },
  "width_px":    { "type": "integer", "description": "image width in pixels" },
  "height_px":   { "type": "integer", "description": "image height in pixels" },
  "robot_count": { "type": "integer", "description": "number of robots currently using this map (computed field)" },
  "created_at":  { "type": "string", "format": "date-time" },
  "updated_at":  { "type": "string", "format": "date-time" }
}
```

**맵 좌표 변환 (FE 구현 참고)**:
```
pixel_x = (world_x - origin_x) / resolution
pixel_y = height_px - (world_y - origin_y) / resolution   // y-flip
```

### 3.6 Mission

```json
{
  "id":          { "type": "string", "format": "uuid" },
  "name":        { "type": "string" },
  "map_id":      { "type": "string", "format": "uuid" },
  "waypoints":   { "type": "array", "items": { "$ref": "#/definitions/Waypoint" } },
  "closed_loop": { "type": "boolean", "description": "true = 마지막 WP 후 첫 WP로 복귀" },
  "description": { "type": ["string", "null"] },
  "created_at":  { "type": "string", "format": "date-time" },
  "updated_at":  { "type": "string", "format": "date-time" }
}
```

### 3.7 Assignment

```json
{
  "id":              { "type": "string", "format": "uuid" },
  "robot_id":        { "type": "string", "format": "uuid" },
  "mission_id":      { "type": "string", "format": "uuid" },
  "assigned_by":     { "type": "string", "format": "uuid", "description": "user_id" },
  "assigned_at":     { "type": "string", "format": "date-time" },
  "status":          { "type": "string", "enum": ["running", "paused", "cancelled", "done"] },
  "current_wp_index":{ "type": ["integer", "null"], "description": "0-based, null if not started" },
  "started_at":      { "type": ["string", "null"], "format": "date-time" },
  "ended_at":        { "type": ["string", "null"], "format": "date-time" }
}
```

### 3.8 Event (감사 로그)

```json
{
  "id":        { "type": "string", "format": "uuid" },
  "ts":        { "type": "string", "format": "date-time" },
  "ts_ms":     { "type": "integer", "description": "epoch milliseconds, FE 사용 편의" },
  "actor":     { "type": ["string", "null"], "description": "user_id 또는 'system'" },
  "robot_id":  { "type": ["string", "null"], "format": "uuid" },
  "event_type":{ "type": "string", "enum": ["STATE", "TELEOP", "MISSION", "MAP", "WAYPOINT", "SYSTEM", "ALARM"] },
  "payload":   { "type": "object", "description": "event_type별 상세 페이로드, 3.8.1 참조" }
}
```

#### 3.8.1 Event payload 스키마 (event_type별)

| event_type | payload 필드 |
|---|---|
| `STATE` | `{ prev: RobotStatus, next: RobotStatus }` |
| `TELEOP` | `{ action: "start" \| "stop", operator_id: string }` |
| `MISSION` | `{ action: "assign" \| "cancel" \| "pause" \| "resume" \| "done", mission_id: string, assignment_id: string }` |
| `MAP` | `{ action: "create" \| "update" \| "delete", map_id: string, map_name: string }` |
| `WAYPOINT` | `{ action: "push", mission_id: string, waypoint_count: integer }` |
| `SYSTEM` | `{ message: string }` |
| `ALARM` | `{ alarm_type: AlarmType, severity: "info" \| "warn" \| "critical", message: string }` |

### 3.9 Alarm

```json
{
  "id":          { "type": "string", "format": "uuid" },
  "robot_id":    { "type": ["string", "null"], "format": "uuid" },
  "alarm_type":  { "type": "string", "enum": ["EMERGENCY", "DISCONNECT", "BATTERY_LOW", "NAV_GOAL_FAILED", "MANUAL_STOP"] },
  "severity":    { "type": "string", "enum": ["info", "warn", "critical"] },
  "message":     { "type": "string" },
  "ts":          { "type": "string", "format": "date-time" },
  "acknowledged":{ "type": "boolean" },
  "acknowledged_by": { "type": ["string", "null"], "description": "user_id" },
  "acknowledged_at": { "type": ["string", "null"], "format": "date-time" }
}
```

### 3.10 User

```json
{
  "id":         { "type": "string", "format": "uuid" },
  "username":   { "type": "string" },
  "role":       { "type": "string", "enum": ["admin"],
                  "description": "단일 역할 admin 고정. RBAC 미적용." },
  "created_at": { "type": "string", "format": "date-time" }
}
```

**DB 시드 (초기화 시 자동 삽입):**

| id | username | password (bcrypt hash 저장 권장) | role |
|---|---|---|---|
| `550e8400-e29b-41d4-a716-446655440000` | `admin` | `admin` | `admin` |

> 테스트 목적이므로 plain-text 비교도 허용하나, bcrypt 단방향 해시 저장을 권장한다.

### 3.11 TeleopLock

```json
{
  "robot_id":   { "type": "string", "format": "uuid" },
  "locked_by":  { "type": "string", "format": "uuid", "description": "user_id" },
  "locked_at":  { "type": "string", "format": "date-time" },
  "expires_at": { "type": "string", "format": "date-time",
                  "description": "데드맨 타임아웃으로 자동 해제 시각" }
}
```

---

## 4. REST API

모든 엔드포인트:
- 성공 응답 Content-Type: `application/json`
- 에러 응답 Content-Type: `application/problem+json`
- 인증: `Authorization: Bearer <token>` (명시적 예외 제외)

### 4.1 Auth

#### POST /api/v1/auth/login

로그인. 세션 토큰 발급.

**인증 불필요**

**Request body:**
```json
{
  "username": "admin",
  "password": "admin"
}
```

**Response 200:**
```json
{
  "token": "a3f9e2b1c84d7e6f0a1b2c3d4e5f6a7b",
  "expires_at": "2026-05-14T09:12:34Z",
  "user": {
    "id": "550e8400-e29b-41d4-a716-446655440000",
    "username": "admin",
    "role": "admin"
  }
}
```

- `token`: 서버가 생성한 128-bit hex 문자열 (32자). DB에 저장됨.
- `expires_at`: 발급 시각 + 30일 (RFC 3339 UTC).
- FE는 토큰을 localStorage에 저장한다. 이후 모든 요청에 `Authorization: Bearer <token>` 헤더 포함.

**Errors:**
| Status | code | 설명 |
|---|---|---|
| 401 | `INVALID_CREDENTIALS` | 사용자명 또는 비밀번호 불일치 |

---

#### GET /api/v1/auth/me

현재 인증된 사용자 정보. FE 앱 마운트 시 localStorage 토큰의 유효성을 확인하는 용도.

**Response 200:**
```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "username": "admin",
  "role": "admin",
  "created_at": "2026-01-01T00:00:00Z"
}
```

**Errors:**
| Status | code | 설명 |
|---|---|---|
| 401 | `UNAUTHORIZED` | 토큰 없음, 토큰 불일치, 또는 만료 |

---

#### POST /api/v1/auth/logout

현재 토큰을 DB에서 삭제하여 즉시 무효화.

**Response 204:** No Content

---

### 4.2 Robots

#### GET /api/v1/robots

로봇 목록 조회. (S1 플릿 리스트, S2 Fleet Overview)

**Query parameters:**

| 파라미터 | 타입 | 기본값 | 설명 |
|---|---|---|---|
| `status` | string (comma) | — | 필터: IDLE,PATROLLING 등 |
| `map_id` | uuid | — | 해당 맵의 로봇만 |
| `sort` | string | `name` | `name`, `status`, `battery`, `last_seen_at` |
| `order` | string | `asc` | `asc`, `desc` |
| `page` | integer | 1 | |
| `page_size` | integer | 50 | 최대 100 |

**Response 200:**
```json
{
  "data": [
    {
      "id": "550e8400-e29b-41d4-a716-446655440000",
      "name": "Robot-01",
      "ros_namespace": "/robot_01",
      "model": null,
      "is_simulated": false,
      "current_map_id": "7c9e6679-7425-40de-944b-e07fc1f90ae7",
      "current_mission_id": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
      "current_assignment_id": "1b9d6bcd-bbfd-4b2d-9b5d-ab8dfbbd4bed",
      "status": "PATROLLING",
      "pose": { "x": 1.234, "y": -0.872, "yaw": 0.785 },
      "battery": 0.85,
      "last_seen_at": "2026-04-14T09:12:34.123Z",
      "created_at": "2026-01-01T00:00:00Z",
      "updated_at": "2026-04-14T09:12:34Z"
    }
  ],
  "pagination": {
    "page": 1,
    "page_size": 50,
    "total": 3,
    "has_next": false,
    "next_cursor": null
  }
}
```

---

#### GET /api/v1/robots/:robotId

단일 로봇 상세 조회. (S3 Robot Detail)

**Response 200:** Robot 스키마 (단일 객체, `data` 래퍼 없음)

```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "name": "Robot-01",
  "ros_namespace": "/robot_01",
  "model": null,
  "is_simulated": false,
  "current_map_id": "7c9e6679-7425-40de-944b-e07fc1f90ae7",
  "current_mission_id": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
  "current_assignment_id": "1b9d6bcd-bbfd-4b2d-9b5d-ab8dfbbd4bed",
  "status": "PATROLLING",
  "pose": { "x": 1.234, "y": -0.872, "yaw": 0.785 },
  "battery": 0.85,
  "last_seen_at": "2026-04-14T09:12:34.123Z",
  "created_at": "2026-01-01T00:00:00Z",
  "updated_at": "2026-04-14T09:12:34Z"
}
```

**Errors:**
| Status | code |
|---|---|
| 404 | `ROBOT_NOT_FOUND` |

---

#### GET /api/v1/robots/:robotId/waypoints

로봇에 현재 로드된 waypoint 목록. (S3 텔레메트리, S6 편집기 초기값)

**Response 200:**
```json
{
  "robot_id": "550e8400-...",
  "mission_id": "3fa85f64-...",
  "waypoints": [
    { "index": 0, "x": 1.2, "y": -0.8, "yaw": 0.0, "label": null },
    { "index": 1, "x": 3.4, "y":  1.2, "yaw": 1.57, "label": "gate" }
  ],
  "current_wp_index": 1,
  "closed_loop": true
}
```

**Errors:**
| Status | code |
|---|---|
| 404 | `ROBOT_NOT_FOUND` |

---

#### GET /api/v1/robots/:robotId/status-history

로봇의 최근 상태 전이 히스토리. (S3 Plan Timeline)

**Query parameters:**

| 파라미터 | 기본값 | 설명 |
|---|---|---|
| `from` | 30분 전 | RFC 3339 |
| `to` | 현재 | RFC 3339 |
| `limit` | 100 | 최대 500 |

**Response 200:**
```json
{
  "robot_id": "550e8400-...",
  "transitions": [
    {
      "ts": "2026-04-14T09:12:00Z",
      "ts_ms": 1744622520000,
      "from_status": "IDLE",
      "to_status": "PATROLLING",
      "pose": { "x": 0.0, "y": 0.0, "yaw": 0.0 }
    }
  ]
}
```

---

### 4.3 Robot Control

#### POST /api/v1/robots/:robotId/control/start

로봇을 MANUAL(teleop) 모드로 전환. teleop 락 획득 포함.

**Request body:**
```json
{
  "idempotency_key": "550e8400-e29b-41d4-a716-446655440001"
}
```

**Response 200:**
```json
{
  "robot_id": "550e8400-...",
  "status": "MANUAL",
  "lock": {
    "robot_id": "550e8400-...",
    "locked_by": "user-uuid",
    "locked_at": "2026-04-14T09:30:00Z",
    "expires_at": "2026-04-14T09:30:30Z"
  }
}
```

**Errors:**
| Status | code | 설명 |
|---|---|---|
| 404 | `ROBOT_NOT_FOUND` | |
| 409 | `TELEOP_ALREADY_LOCKED` | 다른 운영자가 조종 중 |
| 422 | `ROBOT_CANNOT_ENTER_MANUAL` | EMERGENCY 등 전환 불가 상태 (OQ-API-1) |

---

#### POST /api/v1/robots/:robotId/control/stop

MANUAL 모드 종료. teleop 락 해제.

**Request body:**
```json
{
  "idempotency_key": "550e8400-e29b-41d4-a716-446655440002",
  "resume_mission": true
}
```

- `resume_mission`: true이면 중단됐던 Assignment를 `running`으로 복귀 시도.

**Response 200:**
```json
{
  "robot_id": "550e8400-...",
  "status": "PATROLLING",
  "assignment_resumed": true
}
```

**Errors:**
| Status | code |
|---|---|
| 404 | `ROBOT_NOT_FOUND` |
| 409 | `NOT_IN_MANUAL_MODE` |
| 403 | `TELEOP_LOCK_MISMATCH` |

---

#### POST /api/v1/robots/:robotId/control/emergency-stop

긴급 정지. 상태를 EMERGENCY로 전환하고 cmd_vel 0 발행.

**Request body:**
```json
{ "idempotency_key": "..." }
```

**Response 200:**
```json
{ "robot_id": "...", "status": "EMERGENCY" }
```

**Errors:**
| Status | code |
|---|---|
| 404 | `ROBOT_NOT_FOUND` |

---

### 4.4 Assignments (임무 할당)

#### POST /api/v1/assignments

임무 할당. 단일 또는 복수 로봇에 동시 할당 가능.

**Request body:**
```json
{
  "idempotency_key": "unique-key-per-operation",
  "robot_ids": ["550e8400-...", "7c9e6679-..."],
  "mission_id": "3fa85f64-5717-4562-b3fc-2c963f66afa6"
}
```

**Response 201:**
```json
{
  "assignments": [
    {
      "id": "1b9d6bcd-bbfd-4b2d-9b5d-ab8dfbbd4bed",
      "robot_id": "550e8400-...",
      "mission_id": "3fa85f64-...",
      "assigned_by": "user-uuid",
      "assigned_at": "2026-04-14T09:28:10Z",
      "status": "running",
      "current_wp_index": null,
      "started_at": null,
      "ended_at": null
    }
  ]
}
```

**Errors:**
| Status | code | 설명 |
|---|---|---|
| 404 | `ROBOT_NOT_FOUND` | robot_ids 중 존재하지 않는 ID 포함 |
| 404 | `MISSION_NOT_FOUND` | |
| 409 | `ROBOT_ALREADY_HAS_RUNNING_ASSIGNMENT` | 이미 실행 중인 임무 있음. 취소 후 재할당 필요 |
| 422 | `MISSION_MAP_MISMATCH` | 임무의 map_id와 로봇의 current_map_id 불일치 |

---

#### GET /api/v1/assignments/:assignmentId

**Response 200:** Assignment 스키마

---

#### PATCH /api/v1/assignments/:assignmentId

Assignment 상태 변경 (pause, resume, cancel).

**Request body:**
```json
{
  "status": "paused",
  "idempotency_key": "..."
}
```

허용 상태 전이:
- `running` → `paused`, `cancelled`
- `paused` → `running`, `cancelled`

**Response 200:** 갱신된 Assignment 스키마

**Errors:**
| Status | code |
|---|---|
| 404 | `ASSIGNMENT_NOT_FOUND` |
| 409 | `INVALID_STATUS_TRANSITION` |

---

### 4.5 Maps

#### GET /api/v1/maps

맵 목록 조회. (S1 맵 셀렉터, S5 Maps 화면)

**Query parameters:**

| 파라미터 | 기본값 | 설명 |
|---|---|---|
| `page` | 1 | |
| `page_size` | 50 | |

**Response 200:**
```json
{
  "data": [
    {
      "id": "7c9e6679-7425-40de-944b-e07fc1f90ae7",
      "name": "Warehouse-A",
      "description": "1층 창고",
      "image_url": "/static/maps/7c9e6679-7425-40de-944b-e07fc1f90ae7/map.png",
      "resolution": 0.05,
      "origin_x": -10.0,
      "origin_y": -10.0,
      "origin_yaw": 0.0,
      "width_px": 400,
      "height_px": 400,
      "robot_count": 2,
      "created_at": "2026-01-01T00:00:00Z",
      "updated_at": "2026-04-14T09:00:00Z"
    }
  ],
  "pagination": { ... }
}
```

---

#### GET /api/v1/maps/:mapId

단일 맵 조회.

**Response 200:** Map 스키마 (단일 객체)

**Errors:**
| Status | code |
|---|---|
| 404 | `MAP_NOT_FOUND` |

---

#### POST /api/v1/maps

맵 업로드 (Phase 3). `.yaml` + `.pgm` 파일을 multipart/form-data로 수신.

**Request:** `Content-Type: multipart/form-data`

| 필드 | 타입 | 설명 |
|---|---|---|
| `name` | string (form field) | 맵 이름 |
| `description` | string (optional) | 설명 |
| `yaml_file` | file | ROS 맵 `.yaml` |
| `pgm_file` | file | ROS 맵 `.pgm` |

**서버 처리**: 현 `prepare_map.py` 로직 (pgm → png 변환, 메타 추출)을 수행.

**Response 201:** Map 스키마 (image_url에 변환된 png 경로 포함)

**Errors:**
| Status | code | 설명 |
|---|---|---|
| 400 | `INVALID_MAP_FILES` | yaml/pgm 파싱 실패 |
| 409 | `MAP_NAME_CONFLICT` | 동일 이름 맵 존재 |
| 413 | `FILE_TOO_LARGE` | 50MB 초과 |

---

#### PATCH /api/v1/maps/:mapId

맵 메타데이터 수정 (이름, 설명).

**Request body:**
```json
{
  "name": "Warehouse-A v2",
  "description": "업데이트된 설명"
}
```

**Response 200:** 갱신된 Map 스키마

**Errors:**
| Status | code |
|---|---|
| 404 | `MAP_NOT_FOUND` |
| 409 | `MAP_NAME_CONFLICT` |

---

#### DELETE /api/v1/maps/:mapId

맵 삭제. 참조 중인 임무/로봇이 있으면 실패.

**Response 204:** No Content

**Errors:**
| Status | code | detail 예시 |
|---|---|---|
| 404 | `MAP_NOT_FOUND` | |
| 409 | `MAP_IN_USE` | `"Map is used by missions: [uuid1], robots: [uuid2]"` |

---

### 4.6 Missions

#### GET /api/v1/missions

임무 목록 조회. (S7 Missions)

**Query parameters:**

| 파라미터 | 설명 |
|---|---|
| `map_id` | 해당 맵의 임무만 |
| `page`, `page_size` | 페이지네이션 |

**Response 200:**
```json
{
  "data": [
    {
      "id": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
      "name": "구역A 순찰",
      "map_id": "7c9e6679-7425-40de-944b-e07fc1f90ae7",
      "waypoints": [
        { "index": 0, "x": 1.2, "y": -0.8, "yaw": 0.0, "label": null },
        { "index": 1, "x": 3.4, "y":  1.2, "yaw": 1.57, "label": null }
      ],
      "closed_loop": true,
      "description": null,
      "created_at": "2026-04-10T10:00:00Z",
      "updated_at": "2026-04-14T08:00:00Z"
    }
  ],
  "pagination": { ... }
}
```

---

#### GET /api/v1/missions/:missionId

**Response 200:** Mission 스키마

**Errors:**
| Status | code |
|---|---|
| 404 | `MISSION_NOT_FOUND` |

---

#### POST /api/v1/missions

임무 생성 (Phase 3, "Save as Mission").

**Request body:**
```json
{
  "name": "구역A 순찰",
  "map_id": "7c9e6679-...",
  "waypoints": [
    { "index": 0, "x": 1.2, "y": -0.8, "yaw": 0.0, "label": null }
  ],
  "closed_loop": true,
  "description": null
}
```

**Response 201:** Mission 스키마

**Errors:**
| Status | code |
|---|---|
| 404 | `MAP_NOT_FOUND` |
| 422 | `WAYPOINTS_EMPTY` |
| 409 | `MISSION_NAME_CONFLICT` |

---

#### PUT /api/v1/missions/:missionId

임무 전체 수정 (waypoints 포함).

**Request body:** POST와 동일 (id, created_at 제외)

**Response 200:** Mission 스키마

**Errors:**
| Status | code |
|---|---|
| 404 | `MISSION_NOT_FOUND` |
| 422 | `WAYPOINTS_EMPTY` |

---

#### DELETE /api/v1/missions/:missionId

임무 삭제. 실행 중인 Assignment가 있으면 실패.

**Response 204:** No Content

**Errors:**
| Status | code |
|---|---|
| 404 | `MISSION_NOT_FOUND` |
| 409 | `MISSION_HAS_RUNNING_ASSIGNMENT` |

---

#### POST /api/v1/missions/:missionId/push

저장된 임무의 waypoints를 지정 로봇에 즉시 전달 (Phase 3, "Push to Robot").

**Request body:**
```json
{
  "robot_id": "550e8400-...",
  "idempotency_key": "..."
}
```

**서버 동작**: ROS 서비스 `/<robot_ns>/set_waypoints`를 호출해 patrol_manager에 새 waypoints를 전달. 응답은 ROS 서비스 응답이 오거나 timeout(3s)까지 대기.

**Response 200:**
```json
{
  "robot_id": "550e8400-...",
  "mission_id": "3fa85f64-...",
  "pushed_at": "2026-04-14T09:30:00Z",
  "waypoint_count": 8
}
```

**Errors:**
| Status | code | 설명 |
|---|---|---|
| 404 | `ROBOT_NOT_FOUND` | |
| 404 | `MISSION_NOT_FOUND` | |
| 422 | `MISSION_MAP_MISMATCH` | |
| 504 | `ROS_SERVICE_TIMEOUT` | patrol_manager가 응답 없음 |

---

### 4.7 Events (감사 로그)

#### GET /api/v1/events

이벤트 목록 조회. (S9 Events)

**Query parameters:**

| 파라미터 | 기본값 | 설명 |
|---|---|---|
| `robot_id` | — | 특정 로봇 필터 |
| `event_type` | — | STATE,TELEOP,MISSION,MAP,WAYPOINT,SYSTEM,ALARM (쉼표 구분) |
| `from` | 24시간 전 | RFC 3339 |
| `to` | 현재 | RFC 3339 |
| `cursor` | — | 커서 기반 페이지네이션 |
| `limit` | 50 | 최대 200 |
| `order` | `desc` | `asc`, `desc` (ts 기준) |

**Response 200:**
```json
{
  "data": [
    {
      "id": "a3b4c5d6-...",
      "ts": "2026-04-14T14:32:01Z",
      "ts_ms": 1744641121000,
      "actor": "user-uuid",
      "robot_id": "550e8400-...",
      "event_type": "STATE",
      "payload": { "prev": "PATROLLING", "next": "WAIT" }
    }
  ],
  "pagination": {
    "has_next": true,
    "next_cursor": "eyJ0cyI6MTc0NDY0MTEyMTAwMH0="
  }
}
```

---

#### GET /api/v1/events/export

이벤트 CSV 다운로드. 동일 필터 파라미터 사용.

**Response 200:**
- `Content-Type: text/csv; charset=utf-8`
- `Content-Disposition: attachment; filename="events_2026-04-14.csv"`

CSV 컬럼: `id, ts, actor, robot_id, event_type, payload`

---

### 4.8 Alarms

#### GET /api/v1/alarms

현재 미확인 알람 목록. (헤더 알림 벨 카운트)

**Query parameters:**

| 파라미터 | 기본값 |
|---|---|
| `acknowledged` | `false` |
| `robot_id` | — |
| `limit` | 50 |

**Response 200:**
```json
{
  "data": [
    {
      "id": "b2c3d4e5-...",
      "robot_id": "550e8400-...",
      "alarm_type": "EMERGENCY",
      "severity": "critical",
      "message": "장애물 감지로 긴급 정지",
      "ts": "2026-04-14T14:31:55Z",
      "acknowledged": false,
      "acknowledged_by": null,
      "acknowledged_at": null
    }
  ],
  "unacknowledged_count": 3
}
```

---

#### POST /api/v1/alarms/:alarmId/acknowledge

알람 확인 처리.

**Response 200:**
```json
{
  "id": "b2c3d4e5-...",
  "acknowledged": true,
  "acknowledged_by": "user-uuid",
  "acknowledged_at": "2026-04-14T14:33:00Z"
}
```

**Errors:**
| Status | code |
|---|---|
| 404 | `ALARM_NOT_FOUND` |
| 409 | `ALARM_ALREADY_ACKNOWLEDGED` |

---

### 4.9 System

#### GET /api/v1/system/time

서버 현재 시간. FE가 클라이언트 드리프트를 계산하는 데 사용.

**인증 불필요**

**Response 200:**
```json
{
  "server_time": "2026-04-14T09:12:34.567Z",
  "ts_ms": 1744622354567
}
```

---

## 5. Realtime API (WebSocket)

### 5.1 Connection & Auth Handshake

```
GET /ws?token=<session_token>
Upgrade: websocket
```

- 서버는 연결 수락 전 토큰을 DB에서 조회하여 검증한다 (만료 여부 포함).
- 유효하지 않으면 HTTP 401 응답 후 연결 종료.
- 연결 수락 후 서버는 즉시 **snapshot** 메시지를 전송한다 (5.5절 참조).

### 5.2 메시지 Envelope

**서버 → 클라이언트:**

```json
{
  "v":       1,
  "type":    "<메시지 타입>",
  "robot_id": "<uuid 또는 null>",
  "ts_ms":   1744622354567,
  "data":    { ... }
}
```

| 필드 | 설명 |
|---|---|
| `v` | 프로토콜 버전 (현재 1). 하위 호환 확인용 |
| `type` | 메시지 타입 식별자 (5.3 목록 참조) |
| `robot_id` | 해당 메시지가 특정 로봇에 관한 경우 UUID, 시스템 메시지는 null |
| `ts_ms` | 서버 발신 시각 (epoch ms). 클라이언트 드리프트 보정 기준 |
| `data` | 메시지 타입별 페이로드 |

**클라이언트 → 서버:**

```json
{
  "v":    1,
  "type": "<메시지 타입>",
  "data": { ... }
}
```

### 5.3 서버 → 클라이언트 메시지 타입

| type | 설명 | robot_id |
|---|---|---|
| `snapshot` | 연결/재연결 시 전체 상태 스냅샷 | null |
| `pose` | 로봇 pose 업데이트 (~10Hz) | 해당 로봇 UUID |
| `state` | 로봇 상태 전이 | 해당 로봇 UUID |
| `waypoints` | 로봇 waypoint 목록 갱신 | 해당 로봇 UUID |
| `current_wp` | 현재 목적지 waypoint index | 해당 로봇 UUID |
| `plan` | Nav2 경로 계획 갱신 | 해당 로봇 UUID |
| `alarm` | 새 알람 발생 | 해당 로봇 UUID 또는 null |
| `event` | 감사 이벤트 (실시간 append) | 해당 로봇 UUID 또는 null |
| `robot_online` | 로봇이 ROS 토픽 수신 시작 (새로 연결) | 해당 로봇 UUID |
| `robot_offline` | 로봇 토픽 15초 이상 미수신 | 해당 로봇 UUID |
| `teleop_lock_change` | teleop 락 획득/해제 | 해당 로봇 UUID |
| `assignment_update` | Assignment 상태 변경 | 해당 로봇 UUID |
| `pong` | 하트비트 응답 | null |
| `error` | 서버 측 에러 (명령 처리 실패 등) | null 또는 해당 UUID |

### 5.4 메시지 상세 & 예시

#### snapshot

연결/재연결 시 서버가 즉시 전송하는 전체 상태 스냅샷.

```json
{
  "v": 1,
  "type": "snapshot",
  "robot_id": null,
  "ts_ms": 1744622354567,
  "data": {
    "robots": [
      {
        "id": "550e8400-...",
        "status": "PATROLLING",
        "pose": { "x": 1.234, "y": -0.872, "yaw": 0.785 },
        "waypoints": [
          { "index": 0, "x": 1.2, "y": -0.8, "yaw": 0.0, "label": null }
        ],
        "current_wp_index": 1,
        "plan": [{ "x": 1.2, "y": -0.8 }, { "x": 1.5, "y": -0.5 }],
        "battery": 0.85,
        "last_seen_at": "2026-04-14T09:12:34.123Z"
      }
    ],
    "alarms": [
      {
        "id": "b2c3d4e5-...",
        "robot_id": "550e8400-...",
        "alarm_type": "EMERGENCY",
        "severity": "critical",
        "message": "긴급 정지",
        "ts": "2026-04-14T14:31:55Z",
        "acknowledged": false
      }
    ]
  }
}
```

#### pose

```json
{
  "v": 1,
  "type": "pose",
  "robot_id": "550e8400-e29b-41d4-a716-446655440000",
  "ts_ms": 1744622354567,
  "data": {
    "x":   1.234,
    "y":  -0.872,
    "yaw": 0.785
  }
}
```

#### state

```json
{
  "v": 1,
  "type": "state",
  "robot_id": "550e8400-...",
  "ts_ms": 1744622354567,
  "data": {
    "status": "EMERGENCY",
    "prev_status": "PATROLLING"
  }
}
```

#### waypoints

```json
{
  "v": 1,
  "type": "waypoints",
  "robot_id": "550e8400-...",
  "ts_ms": 1744622354567,
  "data": {
    "mission_id": "3fa85f64-...",
    "waypoints": [
      { "index": 0, "x": 1.2, "y": -0.8, "yaw": 0.0, "label": null },
      { "index": 1, "x": 3.4, "y":  1.2, "yaw": 1.57, "label": null }
    ],
    "closed_loop": true
  }
}
```

#### current_wp

```json
{
  "v": 1,
  "type": "current_wp",
  "robot_id": "550e8400-...",
  "ts_ms": 1744622354567,
  "data": {
    "index": 2,
    "total": 8
  }
}
```

#### plan

```json
{
  "v": 1,
  "type": "plan",
  "robot_id": "550e8400-...",
  "ts_ms": 1744622354567,
  "data": {
    "points": [
      { "x": 1.234, "y": -0.872 },
      { "x": 1.500, "y": -0.500 }
    ]
  }
}
```

#### alarm

```json
{
  "v": 1,
  "type": "alarm",
  "robot_id": "550e8400-...",
  "ts_ms": 1744622354567,
  "data": {
    "id": "b2c3d4e5-...",
    "alarm_type": "EMERGENCY",
    "severity": "critical",
    "message": "장애물 감지로 긴급 정지",
    "ts": "2026-04-14T14:31:55Z"
  }
}
```

#### event

```json
{
  "v": 1,
  "type": "event",
  "robot_id": "550e8400-...",
  "ts_ms": 1744622354567,
  "data": {
    "id": "a3b4c5d6-...",
    "ts": "2026-04-14T14:32:01Z",
    "actor": "user-uuid",
    "event_type": "STATE",
    "payload": { "prev": "PATROLLING", "next": "WAIT" }
  }
}
```

#### robot_online / robot_offline

```json
{
  "v": 1,
  "type": "robot_online",
  "robot_id": "550e8400-...",
  "ts_ms": 1744622354567,
  "data": {
    "name": "Robot-01"
  }
}
```

#### teleop_lock_change

```json
{
  "v": 1,
  "type": "teleop_lock_change",
  "robot_id": "550e8400-...",
  "ts_ms": 1744622354567,
  "data": {
    "action": "acquired",
    "locked_by": "user-uuid",
    "locked_at": "2026-04-14T09:30:00Z",
    "expires_at": "2026-04-14T09:30:30Z"
  }
}
```

`action`: `"acquired"` | `"released"` | `"expired"`

#### assignment_update

```json
{
  "v": 1,
  "type": "assignment_update",
  "robot_id": "550e8400-...",
  "ts_ms": 1744622354567,
  "data": {
    "assignment_id": "1b9d6bcd-...",
    "mission_id": "3fa85f64-...",
    "mission_name": "구역A 순찰",
    "status": "running",
    "current_wp_index": 3
  }
}
```

#### error

```json
{
  "v": 1,
  "type": "error",
  "robot_id": null,
  "ts_ms": 1744622354567,
  "data": {
    "code": "TELEOP_COMMAND_REJECTED",
    "message": "Safety gate blocked the command",
    "ref_id": "client-request-id-if-any"
  }
}
```

### 5.5 클라이언트 → 서버 메시지 타입

#### ping (하트비트)

클라이언트가 30초마다 전송. 서버는 `pong`으로 응답.

```json
{
  "v": 1,
  "type": "ping",
  "data": { "ts_ms": 1744622354567 }
}
```

**pong 응답:**
```json
{
  "v": 1,
  "type": "pong",
  "robot_id": null,
  "ts_ms": 1744622354570,
  "data": { "client_ts_ms": 1744622354567 }
}
```

#### teleop_cmd

수동 조종 명령. MANUAL 모드인 로봇에만 유효.

```json
{
  "v": 1,
  "type": "teleop_cmd",
  "data": {
    "robot_id": "550e8400-...",
    "linear_x":  0.3,
    "angular_z": 0.0,
    "ts_ms": 1744622354567
  }
}
```

| 필드 | 타입 | 범위 | 설명 |
|---|---|---|---|
| `robot_id` | string | — | 조종 대상 로봇 UUID |
| `linear_x` | number | -1.0 ~ 1.0 | 정규화된 전진/후진. 실제 m/s 스케일링은 백엔드에서 수행 |
| `angular_z` | number | -1.0 ~ 1.0 | 정규화된 회전. 실제 rad/s 스케일링은 백엔드에서 수행 |
| `ts_ms` | integer | — | 클라이언트 발신 시각. 데드맨 타이머 계산에 사용 |

**서버 동작**:
1. 토큰의 user_id가 해당 로봇의 teleop_lock 소유자인지 확인.
2. 확인 성공 시 `/<robot_ns>/cmd_vel_manager`에 `geometry_msgs/Twist` publish.
3. 확인 실패 시 `error` 메시지로 `TELEOP_LOCK_MISMATCH` 반환.
4. 마지막 `teleop_cmd` 수신 후 **200ms** 경과 시 자동으로 `linear_x=0, angular_z=0` 명령을 publish (데드맨 타이머).

**실제 속도 스케일링 (be-engineer 구현 기준):**
- `linear_x`: × 0.5 m/s (최대 선속도, OQ-API-2에서 조정 가능)
- `angular_z`: × 1.0 rad/s (최대 각속도)

### 5.6 Reconnection & Resync (snapshot + delta)

FE 재연결 전략:

```
1. 초기 연결 또는 reconnect
2. 연결 성공 즉시 서버가 snapshot 메시지 전송
3. FE: snapshot을 수신해 robots Map<robotId, RobotState>를 전체 교체
4. 이후 delta 메시지(pose, state, waypoints 등)를 incremental 적용
```

**FE 재연결 백오프 전략** (ui-ux-design.md 7.4 준수):
- 1회: 즉시 재시도
- 2회: 1초 후
- 이후: 지수 백오프 (2s, 4s, 8s, ... 최대 30s)

### 5.7 Backpressure & Rate Limits

#### pose 메시지 스로틀 (서버 측)

ROS `/amcl_pose`는 ~10Hz로 수신되지만, 서버는 WS 클라이언트당 최대 **10Hz (100ms 간격)** 으로 전송한다. 10Hz보다 빠르게 도착하면 최신값을 보관하다가 다음 전송 주기에 전송 (샘플링 아님, 항상 최신값).

#### teleop_cmd 수신 제한 (서버 측)

동일 로봇에 대해 같은 클라이언트에서 **50ms 간격** 미만으로 오는 teleop_cmd는 무시 (단, 마지막 수신 시각은 갱신하여 데드맨 타이머 리셋).

#### WebSocket 연결 수

동시 WS 연결: 제한 없음 (동시 접속 운영자 10명 기준, 50 연결 안정 목표).

---

## 6. Commands & Control Flow

### 6.1 Idempotency Key 전략

명령성 REST API (POST/PATCH)는 `idempotency_key` 필드를 요청에 포함한다.

- 클라이언트는 UUID v4를 생성해 `idempotency_key`로 전송한다.
- 서버는 24시간 동안 동일 `idempotency_key`에 대해 동일 응답을 반환 (멱등성 보장).
- 네트워크 재시도 시 duplicate 작업 방지에 사용.

### 6.2 임무 할당 lifecycle

```
FE                    BE                     ROS (patrol_manager)
 |                     |                            |
 | POST /assignments   |                            |
 |-------------------->|                            |
 |                     | DB에 Assignment 생성       |
 |                     | status=running             |
 |                     |                            |
 |                     | ROS srv: set_waypoints     |
 |                     |--------------------------->|
 |                     |                            | waypoints 적용
 |                     |<---------------------------|
 |                     |                            |
 | 201 Assignment      |                            |
 |<--------------------|                            |
 |                     |                            |
 | WS: assignment_update (status=running)           |
 |<--------------------|                            |
 |                     |                            |
 | WS: state (PATROLLING)                           |
 |<-------------------------------------------------|
```

### 6.3 Teleop lifecycle

```
FE                    BE                     ROS (patrol_manager)
 |                     |                            |
 | POST control/start  |                            |
 |-------------------->|                            |
 |                     | teleop_lock 획득           |
 |                     | MANUAL 상태 요청            |
 |                     |--------------------------->|
 |                     |<---------------------------|
 | 200 {lock, status}  |                            |
 |<--------------------|                            |
 |                     |                            |
 | WS: teleop_lock_change (acquired)                |
 |<--------------------|                            |
 |                     |                            |
 | WS: teleop_cmd (반복)                            |
 |-------------------->| cmd_vel_manager publish    |
 |                     |--------------------------->|
 |                     |                            |
 | [200ms 무입력]       |                            |
 |                     | deadman: zero vel publish  |
 |                     |--------------------------->|
 |                     |                            |
 | POST control/stop   |                            |
 |-------------------->|                            |
 |                     | teleop_lock 해제           |
 |                     | (resume_mission 처리)      |
 | 200 {status}        |                            |
 |<--------------------|                            |
 |                     |                            |
 | WS: teleop_lock_change (released)                |
 |<--------------------|                            |
```

### 6.4 Waypoint Push lifecycle (Phase 3)

```
FE                    BE                     ROS
 |                     |                      |
 | POST /missions/:id/push                    |
 |-------------------->|                      |
 |                     | ROS srv: set_waypoints (3s timeout)
 |                     |--------------------->|
 |                     |                      | 적용 (다음 WP부터)
 |                     |<---------------------|
 | 200 {pushed_at, count}                     |
 |<--------------------|                      |
 |                     |                      |
 | WS: waypoints (갱신된 목록)                |
 |<--------------------------------------------|
```

---

## 7. Authorization Matrix

단일 역할 `admin`만 존재한다. 로그인(유효한 세션 토큰 보유)한 사용자는 아래 모든 엔드포인트에 접근 가능하다. 미인증 요청은 401을 반환한다.

| 액션 | 비인증 | admin (로그인) |
|---|---|---|
| `POST /api/v1/auth/login` | O (인증 불필요) | O |
| `GET /api/v1/system/time` | O (인증 불필요) | O |
| 그 외 모든 REST 엔드포인트 | 401 | O |
| WS 연결 (`/ws?token=...`) | 401 | O |
| WS `teleop_cmd` | — | O |

> RBAC(역할 기반 접근 제어)는 이 시스템에 적용하지 않는다.

---

## 8. Error Taxonomy

FE는 `code` 필드로 switch/case하여 처리한다.

### 8.1 인증/권한 에러

| code | status | FE 처리 |
|---|---|---|
| `UNAUTHORIZED` | 401 | localStorage 토큰 삭제 후 로그인 화면으로 리다이렉트. 토큰 만료·없음·불일치 모두 이 코드로 통일. |
| `INVALID_CREDENTIALS` | 401 | 로그인 폼에 "아이디 또는 비밀번호가 올바르지 않습니다." 인라인 에러 표시. |
| `TELEOP_LOCK_MISMATCH` | 403 | Toast "다른 운영자가 조종 중입니다." |

> `TOKEN_EXPIRED` / `TOKEN_INVALID` / `FORBIDDEN` / `TOO_MANY_REQUESTS` 코드는 이 시스템에서 사용하지 않는다.

### 8.2 리소스 에러

| code | status | FE 처리 |
|---|---|---|
| `ROBOT_NOT_FOUND` | 404 | Toast "로봇을 찾을 수 없습니다." |
| `MAP_NOT_FOUND` | 404 | Toast "맵을 찾을 수 없습니다." |
| `MISSION_NOT_FOUND` | 404 | Toast "임무를 찾을 수 없습니다." |
| `ASSIGNMENT_NOT_FOUND` | 404 | Toast "할당 정보를 찾을 수 없습니다." |
| `ALARM_NOT_FOUND` | 404 | 무시 (이미 삭제됐을 가능성) |

### 8.3 비즈니스 로직 에러

| code | status | FE 처리 |
|---|---|---|
| `TELEOP_ALREADY_LOCKED` | 409 | 인라인 에러 "다른 운영자가 조종 중 (locked_by 표시)" |
| `NOT_IN_MANUAL_MODE` | 409 | Toast "로봇이 수동 조종 모드가 아닙니다." |
| `ROBOT_CANNOT_ENTER_MANUAL` | 422 | Toast "현재 상태에서 수동 조종이 불가합니다." |
| `ROBOT_ALREADY_HAS_RUNNING_ASSIGNMENT` | 409 | 확인 다이얼로그 "현재 임무를 취소하고 새 임무를 할당하겠습니까?" |
| `MISSION_MAP_MISMATCH` | 422 | 인라인 에러 "로봇의 현재 맵과 임무의 맵이 다릅니다." |
| `MISSION_HAS_RUNNING_ASSIGNMENT` | 409 | 인라인 에러 "실행 중인 할당이 있어 삭제할 수 없습니다." |
| `MAP_IN_USE` | 409 | 인라인 에러 "이 맵을 사용하는 임무/로봇이 있습니다." |
| `INVALID_STATUS_TRANSITION` | 409 | Toast "허용되지 않는 상태 전환입니다." |
| `WAYPOINTS_EMPTY` | 422 | 인라인 에러 "waypoint를 1개 이상 추가하세요." |
| `MAP_NAME_CONFLICT` | 409 | 인라인 에러 "동일한 이름의 맵이 이미 있습니다." |
| `MISSION_NAME_CONFLICT` | 409 | 인라인 에러 "동일한 이름의 임무가 이미 있습니다." |
| `ALARM_ALREADY_ACKNOWLEDGED` | 409 | 무시 (UI 상태 갱신만) |

### 8.4 파일/서버 에러

| code | status | FE 처리 |
|---|---|---|
| `INVALID_MAP_FILES` | 400 | 인라인 에러 "유효하지 않은 맵 파일입니다. .yaml/.pgm 쌍을 확인하세요." |
| `FILE_TOO_LARGE` | 413 | 인라인 에러 "파일 크기가 50MB를 초과합니다." |
| `ROS_SERVICE_TIMEOUT` | 504 | Toast "로봇 응답 없음 — 연결 상태를 확인하세요." |
| `INTERNAL_SERVER_ERROR` | 500 | Toast "서버 오류 — 잠시 후 재시도하세요." |

### 8.5 WebSocket 에러 코드 (WS error 메시지의 `code` 필드)

| code | 설명 | FE 처리 |
|---|---|---|
| `TELEOP_COMMAND_REJECTED` | 안전 게이트 차단 | HUD에 "Safety gate blocked" 표시 |
| `TELEOP_LOCK_MISMATCH` | 락 소유자 불일치 | Teleop 모드 강제 종료 + Toast |
| `INVALID_MESSAGE_FORMAT` | 메시지 포맷 오류 | 콘솔 로그만 (사용자 노출 불필요) |

---

## 9. Mapping: UI Screens → API Surface

### S1 — Live Ops Dashboard

| 데이터 | API |
|---|---|
| 맵 목록 (셀렉터) | `GET /api/v1/maps` |
| 로봇 목록 + 초기 상태 | `GET /api/v1/robots` |
| 실시간 pose/state/waypoints/current_wp/plan | WS `pose`, `state`, `waypoints`, `current_wp`, `plan` |
| 알람 (헤더 벨 배지) | `GET /api/v1/alarms?acknowledged=false` + WS `alarm` |
| 연결 상태 | WS 연결 상태 자체 |

### S2 — Fleet Overview

| 데이터 | API |
|---|---|
| 로봇 테이블 (필터/정렬) | `GET /api/v1/robots?status=...&map_id=...&sort=...` |
| 일괄 임무 할당 | `POST /api/v1/assignments` (robot_ids 배열) |
| 일괄 긴급 정지 | `POST /api/v1/robots/:id/control/emergency-stop` (복수 호출) |

### S3 — Robot Detail

| 데이터 | API |
|---|---|
| 로봇 정보 | `GET /api/v1/robots/:robotId` |
| 최근 이벤트 (하단 로그) | `GET /api/v1/events?robot_id=:id&limit=50` |
| 상태 타임라인 | `GET /api/v1/robots/:robotId/status-history?from=...` |
| 실시간 스트림 | WS `pose`, `state`, `current_wp`, `plan` (robot_id 필터링) |
| Teleop 진입 | `POST /api/v1/robots/:robotId/control/start` |

### S4 — Teleop

| 데이터 | API |
|---|---|
| MANUAL 모드 진입 | `POST /api/v1/robots/:robotId/control/start` |
| 조종 명령 | WS `teleop_cmd` (client → server) |
| MANUAL 모드 종료 | `POST /api/v1/robots/:robotId/control/stop` |
| 실시간 포즈 | WS `pose` |
| 락 상태 변경 알림 | WS `teleop_lock_change` |

### S5 — Maps

| 데이터 | API |
|---|---|
| 맵 목록 | `GET /api/v1/maps` |
| 맵 업로드 | `POST /api/v1/maps` |
| 맵 삭제 | `DELETE /api/v1/maps/:mapId` |
| 맵 메타 수정 | `PATCH /api/v1/maps/:mapId` |

### S6 — Map Editor

| 데이터 | API |
|---|---|
| 맵 정보 (이미지, 메타) | `GET /api/v1/maps/:mapId` |
| 기존 임무 waypoints 로드 | `GET /api/v1/missions/:missionId` |
| 임무 저장 (Save as Mission) | `POST /api/v1/missions` 또는 `PUT /api/v1/missions/:id` |
| Push to Robot | `POST /api/v1/missions/:missionId/push` |

### S7 — Missions

| 데이터 | API |
|---|---|
| 임무 목록 | `GET /api/v1/missions?map_id=...` |
| 임무 삭제 | `DELETE /api/v1/missions/:missionId` |

### S8 — Mission Detail

| 데이터 | API |
|---|---|
| 임무 상세 | `GET /api/v1/missions/:missionId` |
| 임무 할당 | `POST /api/v1/assignments` |
| 임무 수정 | `PUT /api/v1/missions/:missionId` |

### S9 — Events

| 데이터 | API |
|---|---|
| 이벤트 목록 (필터/정렬) | `GET /api/v1/events?robot_id=...&event_type=...&from=...` |
| 실시간 신규 이벤트 | WS `event` |
| CSV 다운로드 | `GET /api/v1/events/export` |

### S11 — Login

| 데이터 | API |
|---|---|
| 로그인 | `POST /api/v1/auth/login` |
| 현재 사용자 정보 | `GET /api/v1/auth/me` |

---

## 10. Changes vs. Current Backend

현재 `fleet/backend/main.py`와 이 계약의 차이를 나열한다. be-engineer는 이 항목을 리팩토링 체크리스트로 사용한다.

### 10.1 WS 메시지 포맷 변경 (Breaking)

| 현재 | 변경 후 | 이유 |
|---|---|---|
| `{"type": "pose", "data": {...}}` | `{"v":1, "type":"pose", "robot_id":"...", "ts_ms":..., "data":{...}}` | 멀티 로봇 식별, 프로토콜 버전 추적, 타임스탬프 |
| `{"type": "state", "data": "PATROLLING"}` | `{"v":1, "type":"state", "robot_id":"...", "ts_ms":..., "data":{"status":"PATROLLING","prev_status":"IDLE"}}` | 이전 상태 포함, 멀티 로봇 |
| `{"type": "current_wp", "data": 2}` | `{"v":1, "type":"current_wp", ..., "data":{"index":2,"total":8}}` | total 추가 |

**마이그레이션**: 현재 FE(`fleet/frontend/dashboard/index.html`)는 구 포맷을 파싱한다. FE 전면 재작성(React) 시 새 포맷으로 전환. 과도기 없이 단번 교체 가능 (단일 FE 클라이언트, 프로덕션 사용자 없음).

### 10.2 신규 구현 필요 항목

| 항목 | 우선순위 |
|---|---|
| 세션 토큰 검증 미들웨어 (DB 조회 방식, 30일 만료) | Phase 1 |
| DB (SQLite 또는 PostgreSQL) — Robot, Map, Mission, Assignment, Event, Alarm 테이블 | Phase 1 |
| `GET/POST /api/v1/robots`, `GET /api/v1/robots/:id` | Phase 1 |
| `GET /api/v1/maps` | Phase 1 |
| `GET /api/v1/events` | Phase 1 |
| `GET /api/v1/alarms` | Phase 1 |
| WS snapshot 메시지 (재연결 시) | Phase 1 |
| `robot_online` / `robot_offline` WS 이벤트 (15s 타임아웃 감지) | Phase 1 |
| ROS 네임스페이스 분리 (`/<robot_ns>/amcl_pose` 등) | Phase 1 |
| `POST /api/v1/robots/:id/control/start/stop` + teleop 락 | Phase 2 |
| WS `teleop_cmd` 처리 + deadman timer | Phase 2 |
| `POST /api/v1/maps` (파일 업로드) | Phase 3 |
| `POST /api/v1/missions`, `PUT`, `DELETE` | Phase 3 |
| `POST /api/v1/missions/:id/push` + ROS `set_waypoints` 서비스 호출 | Phase 3 |
| `POST /api/v1/assignments` + ROS 연동 | Phase 3 |

### 10.3 ROS 측 변경 필요 (be-engineer → patrol_manager)

| 변경 | 설명 |
|---|---|
| 토픽 네임스페이스화 | `/amcl_pose` → `/<robot_ns>/amcl_pose` 등 (PRD 6.1) |
| `set_waypoints` ROS 서비스 추가 | patrol_manager가 동적 waypoint 수신 (PRD 6.2, OQ-API-4) |
| `MANUAL` 상태 추가 | patrol_manager 상태머신에 MANUAL 상태 추가 또는 대안 구현 (OQ-API-1) |
| 배터리 토픽 | `/battery_state` 구독 추가 (OQ-UI-2, PRD OQ-3) |

---

## 11. Open Questions

be-engineer, fe-engineer는 아래 항목이 해소될 때까지 해당 기능 구현을 대기하거나, 항목 옆에 적힌 기본값으로 구현한다.

### OQ-API-1 — MANUAL 상태 진입 방식

**질문**: patrol_manager 상태머신에 `MANUAL` 상태를 신규 추가하는가, 아니면 `WAIT` 상태에서 외부 `cmd_vel`을 허용하는가?  
**영향**: `POST /api/v1/robots/:id/control/start`의 서버 동작 및 ROS 서비스 설계.  
**기본값 (해소 전 구현용)**: `MANUAL` 상태를 신규 추가. patrol_manager에 `~/enter_manual` 서비스 구현.  
**담당**: be-engineer (ROS 상태머신 설계) + pm (요구사항 확인)

### OQ-API-2 — Teleop 최대 속도

**질문**: 수동 조종 시 최대 선속도/각속도 한계값은 얼마인가? 로봇 모델별로 다른가?  
**영향**: WS `teleop_cmd` 정규화 스케일링 값.  
**기본값**: linear_x × 0.5 m/s, angular_z × 1.0 rad/s.  
**담당**: be-engineer (하드웨어 사양 확인)

### OQ-API-3 — 배터리 텔레메트리 소스

**질문**: 로봇이 `/battery_state` (sensor_msgs/BatteryState) 토픽을 publish하는가? 없다면 백엔드는 `battery: null`을 반환한다. (PRD OQ-3)  
**영향**: Robot 스키마의 `battery` 필드 nullable 처리는 이미 반영.  
**기본값**: `battery: null` 반환. FE는 `--` 표시 (OQ-UI-2 적용).  
**담당**: be-engineer

### OQ-API-4 — `set_waypoints` ROS 서비스 인터페이스

**질문**: patrol_manager에 추가할 `set_waypoints` ROS 서비스의 메시지 타입은 무엇인가? 커스텀 서비스인가, 기존 `rcl_interfaces`를 재사용하는가? (PRD 6.2)  
**기본값**: `geometry_msgs/PoseArray` 기반 커스텀 서비스 `sentinel_msgs/srv/SetWaypoints`.  
**담당**: be-engineer

### OQ-API-5 — 카메라 스트리밍 방식 (Phase 2)

**질문**: MJPEG over HTTP vs WebRTC. (PRD OQ-1, F-MON-3)  
**영향**: Phase 2의 카메라 엔드포인트 설계 전체. 이 문서는 Phase 2 카메라 API를 현재 포함하지 않는다.  
**담당**: api-designer + be-engineer (Phase 2 시작 전 이 문서 업데이트)

### OQ-API-6 — Teleop 락 자동 만료 시간

**질문**: 데드맨 타이머(200ms 무입력 → 정지 명령)와 별개로, teleop 락 자체의 만료 시간은 얼마인가? 운영자가 브라우저를 닫으면 어떻게 되는가?  
**기본값**: WS 연결이 끊기면 즉시 락 해제. 마지막 `teleop_cmd` 후 30초 경과 시 락 자동 만료 + `WAIT` 상태 전환.  
**담당**: be-engineer

### OQ-API-7 — is_simulated 필드 관리 방법

**질문**: `is_simulated` 필드를 로봇 등록 시 수동으로 설정하는가, 아니면 ROS 환경변수/파라미터에서 자동 감지하는가? (OQ-UI-1)  
**기본값**: 로봇 등록(또는 시드 설정) 시 수동 설정.  
**담당**: be-engineer

### OQ-API-8 — DB 선택

**질문**: SQLite(단일 파일, 운영 단순) vs PostgreSQL(Phase 4+ 확장 고려)?  
**기본값**: SQLite + SQLAlchemy. 마이그레이션 도구는 Alembic.  
**담당**: be-engineer

### OQ-UI-3 응답 — Robot Identity Hue 계산

`api-designer` 입장: 서버가 `hue_index`를 반환할 필요 없음. FE에서 `robotId` UUID의 해시값을 0~9로 매핑하는 결정적 함수로 계산 권장. Robot 스키마에 `hue_index` 필드를 추가하지 않는다.

---

---

## 인증 간소화 결정 근거

이 시스템은 실사용이 아닌 테스트 목적으로 운용되며, 매번 로그인하는 부담을 최소화하는 것이 목표이다. JWT + refresh 토큰 구조는 토큰 수명 관리·갱신 로직이 FE/BE 양쪽에 필요해 구현 복잡도가 불필요하게 높아지므로, 30일 유효 opaque session token + localStorage 저장 방식으로 대체한다.

---

*이 문서의 변경은 api-designer가 수행한다. be-engineer / fe-engineer는 이 문서를 직접 수정하지 않고 변경 요청을 api-designer에게 전달한다.*
