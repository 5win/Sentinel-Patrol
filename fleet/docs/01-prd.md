# Sentinel-Patrol — 관제 & Fleet Management 올인원 웹 플랫폼 PRD

- 문서 버전: 0.1 (초안)
- 최종 수정일: 2026-04-14
- 담당: Sentinel-Patrol 팀
- 상태: Draft — UI/UX 디자인 착수 전, 하류 에이전트의 유일한 기준 문서

> 이 문서는 Sentinel-Patrol 프로젝트의 **올인원 관제 + Fleet Management System(FMS) 웹 플랫폼**에 대한 제품 요구사항 정의서(PRD)이다.
> 하류 서브에이전트(`ui-ux-designer`, `api-designer`, `be-engineer`, `fe-engineer`)는 이 문서를 유일한 입력으로 삼아 각자의 산출물(`02-ui-ux-design.md`, `03-api-design.md`, `fleet/frontend/**`, `fleet/backend/**`, `04-backend-notes.md`, `05-frontend-notes.md`)을 작성한다.

---

## 1. 배경과 목표

### 1.1 배경 — 지금 어디까지 구현되어 있는가

현재 Sentinel-Patrol은 **단일 로봇이 동작하는 ROS2 시스템**과 **최소 기능의 단일 페이지 관제 대시보드**까지 완성돼 있다.

| 구성 | 경로 | 현재 책임 |
| --- | --- | --- |
| 순찰 상태머신 | `src/patrol_manager/patrol_manager/patrol_manager_node.py` | `IDLE/PATROLLING/WAIT/EMERGENCY/AVOIDING/RETURNING` 상태 전이, YAML에서 읽어온 고정 waypoint 순회, Nav2 `NavigateToPose` / `Spin` action 호출, `/patrol/state`·`/patrol/waypoints`·`/patrol/current_waypoint` 퍼블리시 |
| 안전 계층 | `patrol_sensors/patrol_safety_gate.py`, `scan_logger.py` | `/front_scan` 기반 독립 안전 정지, `/cmd_vel` 중재 |
| 비전 | `patrol_vision/vision_node.py` | YOLO 기반 사람 검출 후 `/detections` 퍼블리시 |
| 관제 백엔드 | `fleet/backend/main.py` | FastAPI + rclpy(별도 스레드). `/amcl_pose`, `/plan`, `/patrol/state`, `/patrol/waypoints`, `/patrol/current_waypoint`를 구독해 WebSocket `/ws`로 브로드캐스트. 정적 대시보드 서빙 |
| 관제 프런트 | `fleet/frontend/dashboard/index.html` + `prepare_map.py` | 단일 HTML + canvas. `map_config.js`에 박제된 단일 맵 위에 waypoint/plan/robot 오버레이 렌더링 |
| Waypoint 정의 | `src/patrol_manager/config/waypoints.yaml` | 파일에 하드코딩된 단일 순찰 경로 |

### 1.2 한계 — 왜 PRD가 필요한가

현 구조는 **"1 로봇 × 1 맵 × 1 고정 순찰"을 시각화하는 읽기 전용 뷰어**에 가깝다. 다음 요구를 전혀 수용하지 못한다.

- 로봇이 여러 대로 늘어났을 때의 식별/구분/선택
- 맵이 여러 개일 때의 등록·전환·편집
- 임무(Mission)라는 개념 자체 — 현재는 "YAML에 적힌 waypoint를 끝없이 돈다"뿐이다
- 운영자가 시스템에 개입하는 **쓰기 경로** (수동 조종, waypoint 편집, 임무 할당, 지도 편집)
- 카메라 영상·알림·이벤트 히스토리 같은 **운영 관점 기능**
- FMS로 가기 위한 **확장 포인트** (임무 큐, 스케줄러, 스테이션, 권한 등)

### 1.3 제품 목표 (North Star)

> **"한 브라우저 탭에서 순찰 로봇 한 대든 수십 대든, 보고 · 조종하고 · 임무를 내리고 · 맵과 경로를 편집할 수 있다."**

세부 목표:

1. **Observability (보기)** — 여러 로봇의 상태/위치/카메라/임무를 실시간으로 한눈에 본다.
2. **Controllability (조종)** — 필요할 때 한 로봇을 집어 들어 상태 전이 또는 직접 조종으로 개입한다.
3. **Authoring (저작)** — 지도·waypoint·임무를 GUI에서 편집하고 즉시 반영한다.
4. **Fleet-readiness (확장)** — 지금은 단일 로봇 운영도 무리 없이 되지만, 구조는 수십 대 플릿에서도 무너지지 않는다.

### 1.4 비목표 (Out of Scope)

다음은 이번 제품의 1차 범위에 **포함하지 않는다**.

- SLAM·맵 생성 자체 (맵은 외부 툴로 만들고 업로드만 지원)
- ROS 메시지 정의 확장이 필요한 신규 자율 기능 (상위 행동 생성 AI 등)
- 실시간 화상 회의·음성 통신
- 모바일 네이티브 앱 (반응형 웹까지만)
- 다국어 — 일단 한국어 + 영어 혼용 UI, i18n은 Phase 후순위
- 쿠버네티스·멀티 리전 운영 (단일 사이트 단일 서버 전제)

---

## 2. 사용자와 시나리오

### 2.1 1차 페르소나

| 페르소나 | 하루의 중심 과업 | 이 제품에서 가장 자주 쓰는 화면 |
| --- | --- | --- |
| **관제 운영자 (Operator)** — 순찰 중인 로봇을 교대 근무로 모니터링하고 이상 상황에 개입 | 여러 로봇 상태 확인, 알림 수신, 필요 시 수동 정지/조종, 임무 재할당 | Live Ops Dashboard, Robot Detail, Teleop |
| **필드 엔지니어 (Field Engineer)** — 로봇 도입·맵 셋업·경로 튜닝 담당 | 맵 업로드, waypoint 배치, 임무 템플릿 정의, 시뮬레이션 검증 | Map Editor, Mission Designer |
| **플릿 매니저 (Fleet Manager)** — 운영 KPI와 스케줄을 설계 | 로봇 등록·폐기, 임무 스케줄링, 운영 리포트 열람 | Fleet Overview, Schedule, Analytics |

### 2.2 핵심 사용자 시나리오

**S1. 교대 시작 — 상태 훑기.**
운영자가 로그인하면 Live Ops Dashboard에서 전체 로봇의 위치·상태·배터리·현재 임무를 한 화면에서 훑는다. `EMERGENCY` 상태 로봇은 즉시 눈에 띄어야 한다.

**S2. 알림에 응답 — 개입하기.**
`Robot-03`이 `EMERGENCY`에 들어갔다고 알림이 뜬다. 운영자는 해당 로봇을 선택해 Robot Detail로 진입, 카메라 스트리밍을 열고 상황을 확인한 뒤 수동 조종 모드로 전환해 로봇을 빼낸다. 복귀 후 다시 기존 임무로 되돌린다.

**S3. 새 구역 도입 — 맵과 경로 준비.**
필드 엔지니어가 새로 스캔한 `Warehouse-B` 맵을 업로드한다. Map Editor에서 맵을 열고, 지도 위 클릭으로 waypoint를 놓아 `구역A 순찰` 임무 템플릿을 만든다. 저장하면 해당 임무가 Mission Library에 등록된다.

**S4. 임무 내리기 — 할당.**
플릿 매니저가 `Robot-01`, `Robot-02`에 `구역A 순찰`, `Robot-03`에 `구역B 순찰`을 동시에 할당한다. 로봇이 해당 임무를 수락하면 실시간으로 대시보드의 임무 배지가 갱신된다.

**S5. 순찰 중 경로 수정 — 저작과 반영.**
운영자가 순찰 중인 로봇의 waypoint를 GUI에서 드래그로 옮긴 뒤 "저장"을 누른다. 변경은 즉시 로봇으로 내려가 다음 목적지부터 적용된다. 되돌리기도 가능하다.

---

## 3. 기능 요구사항

기능은 두 대분류로 나눈다. **관제 시스템**은 1차 릴리스에 들어갈 실질 기능이고, **FMS**는 구조만 깔고 Todo로 남겨두는 확장 축이다.

### 3.1 관제 시스템 (Monitoring & Tele-op)

#### F-MON-1. Live Ops Dashboard — 멀티 로봇 실시간 지도 뷰

- 선택된 맵 위에 **현재 순찰 중인 모든 로봇**을 겹쳐 그린다.
- 로봇별로 시각적으로 구분된다 (색/번호/라벨). 마우스 호버 시 요약 툴팁, 클릭 시 선택 상태 진입.
- 각 로봇의 **전체 waypoint 경로**와 **현재 목적지**가 구분되어 표시된다 (예: 전 waypoint는 점선, 현재 목적지는 강조 마커).
- Nav2 `/plan`이 있으면 현재 경로도 함께 표시한다 (현 백엔드는 단일 로봇 `/plan`만 구독 중이므로 로봇별로 네임스페이스 분리 필요).
- 지도 확대/축소, 팬, "로봇으로 카메라 이동" 단축 동작 지원.
- 좌/우 사이드 패널에 로봇 리스트와 상세 요약(상태, 배터리, 현재 임무, 현재 waypoint 번호)을 배치한다.
- 여러 맵이 등록되어 있을 때 맵 전환 셀렉터를 제공한다. **서로 다른 맵 위의 로봇은 같은 지도 뷰에 섞어 그리지 않는다.**
- 상태 색상 규약은 현재 대시보드(`index.html`)의 토큰을 계승한다: IDLE/PATROLLING/WAIT/EMERGENCY/AVOIDING/RETURNING.

**수용 기준**
- 관제 운영자는 한 화면에서 "어느 맵 위에, 어떤 로봇이, 어떤 상태로, 어느 목적지로 가고 있는지"를 3초 이내에 파악할 수 있어야 한다.
- 새 로봇이 붙거나 떨어질 때 페이지 새로고침 없이 목록/지도에 반영된다.

#### F-MON-2. Robot Detail & Telemetry

- 로봇 하나를 선택하면 상세 패널(또는 상세 페이지)에서 다음을 본다.
  - 포즈 (`x`, `y`, `yaw`), 현재 상태, 현재 waypoint 번호와 좌표
  - 배터리·연결 상태·최근 에러·마지막 텔레메트리 수신 시각 (현재 ROS 토픽엔 없음 → **Open Question OQ-3**)
  - 현재 임무 이름과 진행률
  - 최근 N분간의 상태 전이 타임라인
- **내부 동작**: 백엔드가 로봇 네임스페이스별로 토픽을 구독하고, 프런트에 `robotId` 필드가 붙은 통합 이벤트 스트림을 내보낸다.

#### F-MON-3. 카메라 실시간 스트리밍

- 선택된 로봇의 카메라 영상을 관제 화면에 실시간 스트리밍한다.
- 여러 카메라가 있을 경우 전환할 수 있어야 한다 (예: front / rear).
- 지연 목표: glass-to-glass < 500ms (로컬 네트워크 기준).
- 상세 화면에서 화면 크기 토글(작게 / 크게 / 팝아웃) 지원.
- **기술 접근**: 1차로 MJPEG over HTTP 또는 `web_video_server`의 기존 스트림을 FastAPI 프록시로 노출하는 단순 경로를 권장. 향후 WebRTC로 업그레이드 가능하도록 프런트 컴포넌트를 영상 소스 URL에 추상화한다. 최종 결정은 `api-designer`와 `be-engineer`의 설계 단계에서 확정한다 — **OQ-1**.

#### F-MON-4. 수동 조종 (Teleoperation)

- 운영자는 한 로봇을 선택해 **"수동 조종 모드"로 상태를 전환**시킨 뒤 직접 조종할 수 있다.
- 현 `patrol_manager`의 상태머신에는 수동 조종 상태가 없다. 기존 상태머신을 깨지 않도록 **새 상태(`MANUAL`)를 추가**하거나, `WAIT` 상태에서 외부 `cmd_vel`을 허용하는 방식 중 한 가지로 구현한다 — **OQ-2**.
- 조종 UI는 화면 키패드 + 키보드 WASD + 게임패드(선택) 입력을 지원한다. 조종 명령은 WebSocket으로 백엔드에 보내고, 백엔드가 `/cmd_vel_manager`로 publish한다.
- 안전 장치:
  - 수동 조종은 `patrol_safety_gate`의 거부를 받는다 (danger 상황에선 속도 0으로 클램프).
  - 운영자 입력이 200ms 이상 끊기면 자동 정지 (데드맨 스위치).
  - 한 로봇은 한 번에 **한 운영자만** 조종할 수 있다 (조종 락, **OQ-4**).
  - 조종 시작·종료는 감사 로그(F-FMS-7)에 남는다.

#### F-MON-5. Map 레지스트리 (등록/수정/삭제)

- 맵은 "이름 + 이미지(`.pgm`) + 메타데이터(`resolution`, `origin`, `width`, `height`) + 식별자"를 가진 1급 리소스로 승격된다.
- **등록**: 필드 엔지니어가 ROS 표준 맵 쌍(`.yaml` + `.pgm`)을 업로드한다. 서버는 `prepare_map.py`가 하던 이미지 변환과 메타 추출을 그대로 수행한다. 저장소는 파일 시스템(1차) — **OQ-5**.
- **수정**: 이름·설명·연결된 waypoint 세트 변경 등 메타데이터 수준의 수정. 이미지 자체의 픽셀 편집은 비목표.
- **삭제**: 참조 중인 임무·로봇이 없을 때만 삭제 가능. 있으면 "어떤 임무/로봇이 사용 중"인지 알려준다.
- **활성 맵**: 각 로봇은 "지금 올라가 있는 맵"을 가진다. 로봇을 다른 맵으로 옮기는 조작은 1차 범위에 포함하지 않고 **OQ-6**으로 남긴다.

#### F-MON-6. Waypoint / 경로 편집기 (Map-Editor)

- 맵을 열면 캔버스 위에 **waypoint 배치 도구**가 활성화된다.
  - **추가**: 지도 클릭으로 새 waypoint 삽입. 각 waypoint는 `(x, y, yaw)`를 가진다. yaw는 드래그 회전 핸들로 조정.
  - **이동**: 기존 waypoint를 드래그.
  - **삭제**: 선택 후 `Delete` 키.
  - **순서 변경**: 좌측 리스트에서 드래그 앤 드롭, 또는 지도 위 번호 배지 드래그.
  - **닫힌 루프 / 열린 경로** 토글.
- **저장 경로**: 저장 시 waypoint 세트는 서버에 "Mission"의 일부로 저장된다. 선택된 로봇에 즉시 적용하는 "Push to robot" 액션이 별도로 있어, 저장과 배포를 분리한다.
- **핫 리로드**: Push to robot을 하면 `patrol_manager`가 새 waypoint를 받아 **다음 목적지부터** 적용한다. 현재 노드는 YAML 파일을 시작 시 1회만 로딩하므로 **동적 로드 경로를 추가해야 한다** (예: `/patrol/waypoints`를 서비스 혹은 파라미터 업데이트로 수신). — **OQ-7**
- **Undo / Revert**: 편집 중 되돌리기, 저장 전 원본으로 되돌리기, 저장 이후에도 버전 히스토리에서 복원.

#### F-MON-7. 임무 할당 (Mission Assignment)

- "임무"는 `(맵 ID, waypoint 시퀀스, 선택적 파라미터)`로 구성된 저장 가능한 템플릿이다. 예: `구역A 순찰`, `구역B 순찰`.
- 운영자는 **맵을 고르고 → 로봇을 고르고 → 임무를 고르고 → "할당"** 단 한 번으로 내릴 수 있다.
- 할당 결과는:
  - 대상 로봇의 waypoint를 해당 임무로 교체.
  - 로봇의 상태를 `PATROLLING`으로 진입시킨다.
  - 대시보드의 "현재 임무" 배지를 갱신.
  - 감사 로그에 기록.
- 여러 로봇에 동시에 같은 임무를 할당할 수 있다 (멀티 선택).
- **임무 취소 / 일시정지 / 재개**는 1차 릴리스 범위에 포함한다.

#### F-MON-8. 알림 & 이벤트 스트림

- `EMERGENCY`, 통신 끊김, 배터리 저전력, Nav2 goal 실패 등은 상단 알림 센터에 쌓인다.
- 알림을 클릭하면 해당 로봇의 Robot Detail로 점프한다.
- 모든 상태 전이 이벤트는 **F-FMS-7 감사 로그**에도 함께 기록된다.

### 3.2 Fleet Management System (FMS 확장축)

> FMS는 아직 구상 중이다. **1차 릴리스에서는 "UI에 자리만 만들고, 데이터 구조/네임스페이스/권한 경계를 미리 준비해 놓는다."**
> 아래 항목은 대부분 **Todo**다. 디자이너/엔지니어는 이 섹션의 항목들을 "지금 구현하지 않더라도 구조가 이것들을 자연스럽게 수용할 수 있는가"의 체크리스트로 사용한다.

#### F-FMS-1. Fleet Overview (1차 포함)

- 모든 로봇의 카드/테이블 뷰. 필드: `robotId`, `name`, `status`, `battery`, `currentMap`, `currentMission`, `lastSeenAt`.
- 필터·검색·정렬.
- 대량 선택 후 단체 액션 (정지, 임무 일괄 할당).

#### F-FMS-2. Robot Registry / Commissioning  **[Todo]**

- 로봇 등록/해제, 네임스페이스·시리얼·모델·이름 편집.
- 1차 릴리스는 "서버 구성 파일 또는 DB 시드로 고정 목록을 읽어들이는" 수준이어도 되지만, **프런트는 "로봇 CRUD"가 가능한 구조로 페이지 껍데기를 잡아 둔다.**

#### F-FMS-3. Mission Library & Scheduler  **[Todo]**

- 저장된 임무 템플릿 목록, 카테고리/태그.
- 스케줄러: cron 유사 문법 또는 "매일 08:00 ~ 20:00 10분 간격" 같은 반복 규칙.
- 1차 릴리스에서는 **반복 없이 즉시 실행만 구현**하고, 반복/예약은 Todo로 스키마에 자리만 남긴다.

#### F-FMS-4. 충전/도킹 스테이션 관리  **[Todo]**

- 스테이션을 맵 위의 1급 객체로 표시.
- 저전력 자동 복귀, 대기열.

#### F-FMS-5. 교통/자원 중재  **[Todo]**

- 교차로·병목 구간에서의 다중 로봇 충돌 방지, 존 기반 우선권.
- 현 ROS 스택엔 전혀 없는 기능이므로, **FMS 확장 단계에서 전담 노드가 추가될 자리**로만 남겨둔다.

#### F-FMS-6. 존(Zone) & 레이어  **[Todo]**

- 맵 위에 no-go, speed-limit, patrol-only 같은 zone을 폴리곤으로 그릴 수 있는 레이어 시스템.
- Map Editor(F-MON-6)와 같은 캔버스를 공유하므로 **레이어 추상화가 1차에서부터 필요하다**.

#### F-FMS-7. 감사 로그 & 이벤트 히스토리  **[1차 최소 구현]**

- 운영자 조작 (수동 조종 시작/종료, 임무 할당, waypoint 편집, 맵 등록/삭제)과 로봇 상태 전이를 시간 순으로 기록.
- 필터: 로봇, 운영자, 이벤트 타입, 기간.
- 1차 릴리스는 **append-only 로그 테이블 + 조회 화면**까지.

#### F-FMS-8. 권한/역할 (RBAC)  **[Todo, 1차는 단일 역할]**

- 역할: `viewer`, `operator`, `engineer`, `admin`.
- 1차 릴리스는 **단일 역할 (= admin) + 세션 기반 로그인**만. 하지만 API와 프런트 라우팅은 역할 체크가 들어갈 수 있는 지점을 미리 준비한다.

#### F-FMS-9. 분석 대시보드  **[Todo]**

- 일/주간 임무 완료율, 총 이동 거리, 이벤트 건수, 평균 배터리 소비.
- 1차엔 빈 페이지 + "Coming soon" 정도.

#### F-FMS-10. 외부 시스템 연동  **[Todo]**

- WMS/ERP/관리자 대시보드와의 연동을 위한 공개 REST API와 Webhook.
- 1차 API 설계 시 **내부 API와 공개 API를 경로 레벨에서 분리해 둔다** (`/api/v1/internal/...` vs `/api/v1/public/...` 등).

---

## 4. 비기능 요구사항

- **실시간성**
  - 포즈·상태 메시지 → 화면 반영: p95 < 300ms (로컬 네트워크).
  - 카메라 스트리밍 지연: < 500ms 목표.
  - 수동 조종 입력 → `/cmd_vel_manager` 발행: < 150ms.
- **동시성 / 규모**
  - 동시 접속 운영자: 10명 기준 안정 동작.
  - 동시 연결 로봇: **1차 릴리스 목표 10대, 구조 목표 50대**.
- **안정성 / 실패 모드**
  - WebSocket 연결이 끊기면 자동 재연결 (현 대시보드의 `setTimeout(connect, 1000)` 재연결 로직을 계승).
  - 백엔드 재시작 시 프런트는 마지막 캐시 상태로 계속 그리며 끊김 배지를 표시.
  - 한 로봇의 ROS 통신 두절이 다른 로봇의 텔레메트리 표시를 막지 않는다.
- **보안**
  - 로그인 세션 필수, HTTPS 전제.
  - 조종·편집 API는 역할 체크가 들어갈 수 있는 지점을 준비 (RBAC는 Todo).
- **브라우저 지원**
  - 최신 Chrome/Edge/Firefox/Safari. IE 미지원. 1920×1080 데스크탑 해상도 기본, 1366×768까지 사용 가능해야 함.
- **코드·아키텍처**
  - 백엔드: 작게 나눈 모듈러 모놀리식, FastAPI·rclpy·Pythonic 관용 준수 (`be-engineer` 지침).
  - 프런트: React + TypeScript 권장. 캔버스는 현 vanilla canvas 구현을 React 컴포넌트로 리팩토링 — **OQ-8** (프레임워크 확정은 `fe-engineer`).

---

## 5. 시스템 모델 (개념 데이터 모델)

> 이 데이터 모델은 **개념 수준**이다. 실제 스키마·필드 타입은 `api-designer`가 `03-api-design.md`에서 확정한다.

- **Robot** — `robotId`, `name`, `model`, `rosNamespace`, `currentMapId`, `currentMissionId`, `status`, `battery`, `lastSeenAt`
- **Map** — `mapId`, `name`, `imagePath`, `resolution`, `origin`, `width`, `height`, `createdAt`, `updatedAt`
- **Mission** — `missionId`, `name`, `mapId`, `waypoints[]`, `closedLoop`, `createdAt`, `updatedAt`
- **Waypoint** — `x`, `y`, `yaw`, `label?`
- **Assignment** — `assignmentId`, `missionId`, `robotId`, `assignedBy`, `assignedAt`, `state(running/paused/cancelled/done)`
- **Event** (감사 로그) — `eventId`, `ts`, `actor`, `robotId?`, `type`, `payload`
- **User** — `userId`, `name`, `role` (1차는 admin 단일)

**불변 조건 (Invariants)**
- Mission은 반드시 하나의 Map에 소속된다.
- 한 로봇은 한 순간 최대 하나의 `running` Assignment만 가진다.
- 수동 조종 모드인 로봇은 Assignment를 가질 수 있지만, 진행 상태는 `paused`이다.

---

## 6. 공개 표면(외부 I/O)의 변경점

PRD 단계에서 최소한으로 합의해 두어야 할 "하류가 반드시 다뤄야 할 I/O 변화"다.

1. **ROS 토픽 네임스페이스화**
   현재 `/amcl_pose`, `/plan`, `/patrol/state` 등은 전역이다. 다중 로봇 시 `/<robot_ns>/amcl_pose` 형태로 네임스페이스를 두고, 백엔드는 런타임에 알려진 로봇 목록만큼 구독을 붙인다. `patrol_manager_node`도 네임스페이스 하에 launch될 수 있도록 고정 topic 경로 대신 launch 파라미터에서 resolve되게 정리한다.
2. **Waypoint 동적 수신 채널**
   `patrol_manager`는 현재 시작 시 YAML을 1회 읽는다. 실시간 편집을 지원하려면 새 waypoint 세트를 받아 반영하는 경로(서비스 또는 topic)를 추가해야 한다. 제안: ROS 서비스 `~/set_waypoints`.
3. **Teleop 명령 수신 경로**
   `/cmd_vel_manager`는 이미 존재한다. 백엔드가 운영자 WebSocket 입력을 이 토픽으로 변환해 publish하고, `MANUAL` 상태(또는 대체)에서만 유효하게 만든다.
4. **WebSocket 메시지 스키마의 확장**
   현재 메시지는 `{type, data}`에 단일 로봇 전제다. 모든 상태/포즈/plan 메시지에 `robotId` 필드를 추가하고, 클라이언트 → 서버 방향의 명령 메시지 타입도 새로 정의한다 (예: `teleop`, `assign_mission`, `save_waypoints`). 상세는 `03-api-design.md`.
5. **맵 파일 저장소와 정적 서빙**
   현재 `fleet/frontend/dashboard/map.png`은 `prepare_map.py`가 덮어쓰는 단일 파일이다. 여러 맵을 다루려면 맵별 디렉터리와 경로 규약, 정적 서빙 경로(예: `/api/v1/maps/{mapId}/image.png`)가 필요하다.

---

## 7. 단계별 계획 (Phased Roadmap)

### Phase 0 — 디자인 & 계약 확정
- `ui-ux-designer` → `02-ui-ux-design.md` 초안
- `api-designer` → `03-api-design.md` (REST + WebSocket 계약, robotId 필드 도입, teleop/assign/save 메시지 정의)
- Open Questions 해소

### Phase 1 — 멀티 로봇 읽기 전용 대시보드
- 목표: **현재 단일 로봇 읽기 전용 대시보드를 N대로 확장**
- 완성 기준:
  - 여러 로봇을 로봇 목록 + 단일 맵 위에 함께 표시
  - Live Ops Dashboard(F-MON-1), Robot Detail(F-MON-2), Fleet Overview(F-FMS-1)
  - 감사 로그 Append 경로만 활성, 조회 UI는 최소
- 범위 제외: 카메라 스트리밍, 수동 조종, Map CRUD, Mission 편집

### Phase 2 — 개입 (Intervention)
- 카메라 스트리밍 (F-MON-3)
- 수동 조종 (F-MON-4) + patrol state machine에 `MANUAL` 혹은 대체 경로 도입
- 알림 센터 (F-MON-8) 1차
- 감사 로그 UI (F-FMS-7)

### Phase 3 — 저작 (Authoring)
- Map 레지스트리 (F-MON-5)
- Waypoint/경로 편집기 (F-MON-6)
- Mission Library 최소 구현, Mission Assignment (F-MON-7)

### Phase 4 — FMS 확장축 개통
- Robot Registry(F-FMS-2) 풀 구현, Scheduler(F-FMS-3) 최소
- Zone / Layer 레이어 시스템 기반 (F-FMS-6) 도입
- 분석 대시보드(F-FMS-9) 골격

### Phase 5+ — 장기
- 교통 중재(F-FMS-5), 스테이션(F-FMS-4), 외부 연동(F-FMS-10), RBAC 완전체(F-FMS-8)

> 각 페이즈의 종료 조건은 "해당 페이즈에 나열된 기능이 S1~S5 시나리오에서 깨지지 않고 작동한다"이다.

---

## 8. 성공 지표

- **정량**
  - 1차 릴리스(Phase 2 종료 시점): 동시 로봇 10대 · 운영자 5명 · 주당 가동 시간 40시간 이상 무장애.
  - 알림 → 운영자 개입(수동 조종 시작)까지 중앙값 < 10초.
  - Waypoint 편집 저장 → 로봇 반영 중앙값 < 2초.
- **정성**
  - 운영자 3인 사용성 인터뷰에서 "지금 어떤 로봇이 어떤 상태인지 화면에서 즉시 알 수 있다"는 응답이 전원 Yes.
  - 필드 엔지니어가 문서 없이 30분 내에 새 맵과 임무를 등록·할당하는 실습 과제를 완수.

---

## 9. 리스크

| 리스크 | 영향 | 대응 |
| --- | --- | --- |
| ROS ↔ 웹 사이의 실시간성이 다중 로봇에서 무너짐 | 대시보드 먹통 | 백엔드에서 토픽 스트림을 로봇 단위로 throttle + 최신값 유지, WebSocket은 델타 전송 |
| `patrol_manager`의 상태머신에 수동 조종을 끼워 넣다가 기존 안전 계층이 깨짐 | 충돌 위험 | `MANUAL` 상태에서도 `patrol_safety_gate`가 우선, 데드맨 타이머 150~200ms |
| 여러 로봇이 동시에 Nav2를 점유할 때 네트워크/CPU 폭증 | 전체 지연 | 단일 머신 가정을 명확히 하고 scale-out은 Phase 후순위로 미룸 |
| 카메라 스트리밍 기술 선택 실패 | 영상 끊김, 개발 재작업 | 1차 MJPEG 프록시로 빠르게 개통 후 WebRTC 교체 가능하게 프런트 영상 컴포넌트 추상화 |
| 맵·임무 편집과 반영 사이 일관성 깨짐 (저장 직후 재시작) | 경로 유실 | 저장은 DB/파일에만, "push to robot"을 명시적 액션으로 분리 |

---

## 10. Open Questions (하류 에이전트에게)

> **OQ는 이 PRD를 기준으로 하류 에이전트가 답을 갖고 돌아와야 할 항목이다. 각자 담당 문서에서 결정을 내리거나, 결정이 불가능한 경우 이 목록에 덧붙인다.**

- **OQ-1. 카메라 스트리밍 방식.** MJPEG over HTTP + FastAPI 프록시(단순/즉시) vs WebRTC(지연/확장성). 1차 릴리스 범위 내에서 선택. — `api-designer`, `be-engineer`
- **OQ-2. 수동 조종을 위한 상태 확장.** `PatrolState`에 `MANUAL`을 추가할 것인가, 기존 `WAIT`을 확장할 것인가? 안전 게이트와의 상호작용 포함. — `be-engineer`
- **OQ-3. 배터리/헬스 텔레메트리 소스.** 현재 ROS 토픽에 없음. `sensor_msgs/BatteryState`를 기본으로 가정해도 되는가? 없는 로봇은 어떻게 표시하는가? — `be-engineer`
- **OQ-4. 수동 조종 락.** "한 로봇을 한 운영자만" 원칙은 서버 측 상태로 강제. 세션 만료·강제 해제 규칙은? — `api-designer`
- **OQ-5. 맵 파일 저장소.** 파일시스템 디렉터리 vs DB BLOB vs 오브젝트 스토리지. 1차는 파일시스템 권장. — `be-engineer`
- **OQ-6. 로봇의 현재 맵 전환.** 로봇을 다른 맵으로 옮기는 조작은 SLAM 재초기화 등을 수반한다. 1차 릴리스엔 "로봇별 맵은 고정"으로 묶어두는지 여부. — `be-engineer`
- **OQ-7. Waypoint 동적 반영.** `patrol_manager`에 ROS 서비스 `~/set_waypoints`를 추가하는 방향 권장. 진행 중인 goal 취소 후 새 인덱스부터 재개 vs 현재 goal 완료 후 다음부터 반영 — 동작 선택. — `be-engineer`
- **OQ-8. 프런트 프레임워크 확정.** React + Vite + TypeScript + 캔버스 라이브러리(예: Konva 또는 직접 구현) 선택. — `fe-engineer`
- **OQ-9. 인증 방식.** 세션 쿠키 vs JWT, 초기 사용자 프로비저닝 방법. — `api-designer`, `be-engineer`
- **OQ-10. 시뮬레이션/실물 구분.** 대시보드에서 시뮬레이션 로봇과 실물 로봇을 구분해 표기할 필요가 있는가? 운영 리스크 관점. — `ui-ux-designer`

---

## 11. 용어

- **Patrol Manager** — 로봇 내에서 순찰 상태머신을 돌리는 ROS2 노드. 지금은 1대에 1개.
- **Fleet Backend** — 웹 플랫폼의 서버. FastAPI + rclpy. 로봇(ROS) ↔ 브라우저(WebSocket/REST) 브리지.
- **Waypoint** — 순찰 경로의 한 점. `(x, y, yaw)`.
- **Mission** — 맵 + waypoint 시퀀스로 구성된 저장 가능한 임무 템플릿.
- **Assignment** — 특정 로봇에 특정 임무를 할당한 인스턴스.
- **Teleop (Teleoperation)** — 운영자가 로봇을 원격으로 직접 조종하는 것.
- **RBAC** — Role-Based Access Control. 역할 기반 접근 제어.
- **Glass-to-glass** — 카메라 렌즈부터 화면 픽셀까지의 엔드 투 엔드 지연.
