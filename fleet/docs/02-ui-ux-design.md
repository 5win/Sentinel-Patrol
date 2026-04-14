# Sentinel-Patrol — UI/UX 디자인 문서

- 문서 버전: 0.1
- 작성일: 2026-04-14
- 상태: 확정(Phase 1 구현용). fe-engineer와 api-designer의 단일 기준 문서.

---

## 1. Design Direction

**"Operator-grade dark command surface — refined minimalism reinterpreted for real-time robot surveillance, where the map is the canvas and every pixel of chrome earns its place."**

이 인터페이스는 "예쁜 대시보드"가 아니라 **작전 지휘소**다. 운용자는 8시간 교대 중 이 화면을 쉼 없이 응시한다. 디자인의 첫 번째 목적은 인지 부하를 낮추는 것이고, 두 번째 목적은 이상 상황을 즉시 눈에 튀게 만드는 것이다.

### The One Thing People Will Remember

맵 위를 이동한 로봇의 **궤적이 인광(phosphorescent) 잔상처럼** 남았다가 30초에 걸쳐 서서히 소멸한다. 가장 밝은 점이 현재 위치고, 꼬리는 시간이 지날수록 투명도가 0으로 감소하는 그라데이션 선이다. 색상은 해당 로봇의 식별 색(로봇별 할당된 hue)을 사용하며, 궤적 전체가 동시에 페이드되는 게 아니라 꼬리 끝부터 먼저 소멸한다. 이 디테일 하나가 "지도 뷰어"와 "살아 있는 관제 화면"을 구분한다.

---

## 2. Anti-patterns (금지)

다음은 fe-engineer가 `frontend-design` 스킬을 호출할 때 **절대 적용하지 말아야 할 것**들이다.

| 금지 항목 | 이유 |
|---|---|
| **Inter / Roboto / Arial / system-ui 폰트** | Generic AI aesthetic의 대표격. 이 화면만의 성격을 즉시 소멸시킨다. |
| **보라색 / 인디고 계열 액센트** | Linear 복사본으로 보인다. 도메인(로봇 관제)과 연관성도 없다. |
| **둥근 카드 + box-shadow 나열** | 정보 밀도를 낮추고 "SaaS 랜딩 페이지" 느낌을 준다. 계층은 border와 여백으로만 표현한다. |
| **의미 없는 그라데이션 배경** | 어두운 균일 배경이 맵 오버레이의 대비를 살린다. 크롬 영역에 그라데이션 없음. |
| **bounce / spring 이징** | 작전 환경에서 장식적 물리 모션은 신뢰를 깎는다. |
| **스켈레톤 로더 남용** | 빠른 텔레메트리 루프에서는 pulse 애니메이션이 오히려 스트레스 유발. 로딩 상태는 텍스트 표시로 처리. |
| **차트/그래프 과잉** | 1차 릴리스는 수치와 상태 pill 위주. 분석 차트는 Phase 4 Analytics 화면 전용. |

---

## 3. Personas & Core Journeys

### 3.1 페르소나

**P1 — 관제 운영자 (Operator)**
- 역할: 교대 근무로 전체 플릿 상태를 모니터링. 이상 발생 시 직접 개입.
- 주요 화면: Live Ops Dashboard → Robot Detail → Teleop
- 특성: 다수 로봇을 동시에 관찰해야 하므로 **주변 시야(peripheral vision)** 활용. 이상 상태는 색과 아이콘으로 먼저 감지, 텍스트 확인은 나중.
- 필요: 키보드로 빠른 로봇 선택, 명령 실행. 마우스 이동 최소화.

**P2 — 필드 엔지니어 (Field Engineer)**
- 역할: 새 맵 등록, waypoint 배치, 임무 템플릿 제작.
- 주요 화면: Map Editor, Mission Designer
- 특성: 정밀한 포인팅 작업. 드래그·클릭이 많다. 오류 복구(Undo)가 중요.
- 필요: 맵 위에서 좌표 편집 도구가 직관적이어야 한다. 저장과 배포가 명확히 구분되어야 한다.

**P3 — 플릿 매니저 (Fleet Manager)**
- 역할: 운영 KPI 확인, 임무 스케줄 설계, 로봇 등록/폐기.
- 주요 화면: Fleet Overview, Schedule, (미래) Analytics
- 특성: 로그와 이력에 관심. 실시간 개입보다 계획과 사후 분석.
- 필요: 테이블 뷰, 필터·정렬, 감사 로그 조회.

### 3.2 핵심 사용자 여정

**J1 — 교대 시작 상태 스캔 (P1)**
```
로그인 → Live Ops Dashboard 진입
→ 맵 위 전체 로봇 위치/상태를 3초 내 파악
→ 좌측 플릿 리스트에서 이상 상태 로봇 식별
→ 문제 없으면 대기. 이상 있으면 J2로.
```

**J2 — 긴급 상황 개입 (P1)**
```
EMERGENCY 알림 수신 (토스트 + 오디오 신호)
→ 알림 클릭 또는 키보드 단축키로 Robot Detail 진입
→ 카메라 스트리밍 확인
→ "수동 조종 모드" 전환
→ WASD / 화면 키패드로 로봇 이동
→ 수동 조종 종료 → 임무 재개 명령
→ 감사 로그 자동 기록
```

**J3 — 새 맵과 임무 등록 (P2)**
```
Fleet 사이드바 → Maps
→ "Upload Map" → .yaml + .pgm 드롭
→ Map Editor 진입 → 맵 위 클릭으로 waypoint 배치
→ 루프/경로 토글, waypoint 순서 조정
→ "Save as Mission" → 이름 입력 → Mission Library 등록
→ "Push to Robot" 선택 → 할당 확인
```

**J4 — 임무 할당 (P3 또는 P1)**
```
Fleet Overview → 로봇 선택 (단일 또는 멀티)
→ "Assign Mission" 액션 → 임무 선택 다이얼로그
→ 확인 → 대시보드 임무 배지 실시간 갱신
→ 감사 로그 자동 기록
```

---

## 4. Information Architecture & Screen Inventory

### 4.1 글로벌 네비게이션 구조

```
Sentinel-Patrol
├── Live Ops Dashboard          [/ 또는 /dashboard]      — 메인 진입점
├── Fleet Overview              [/fleet]                  — 전체 로봇 테이블
├── Robot Detail                [/robots/:robotId]        — 단일 로봇 상세
├── Maps                        [/maps]                   — 맵 레지스트리
│   └── Map Editor              [/maps/:mapId/edit]       — 맵 편집 + WP 배치
├── Missions                    [/missions]               — 임무 라이브러리
│   └── Mission Detail          [/missions/:missionId]    — 임무 상세/편집
├── Events                      [/events]                 — 감사 로그
└── Settings                    [/settings]               — 시스템 설정
```

### 4.2 화면 인벤토리

| ID | 화면 이름 | Phase | 핵심 목적 |
|---|---|---|---|
| S1 | Live Ops Dashboard | 1 | 전체 플릿 실시간 맵 뷰 + 상태 |
| S2 | Fleet Overview | 1 | 로봇 목록 테이블, 필터/정렬 |
| S3 | Robot Detail | 1 | 단일 로봇 텔레메트리 + 히스토리 |
| S4 | Teleop | 2 | 수동 조종 전용 모드 |
| S5 | Maps | 3 | 맵 레지스트리 목록 |
| S6 | Map Editor | 3 | 맵 위 waypoint 편집 |
| S7 | Missions | 3 | 임무 라이브러리 목록 |
| S8 | Mission Detail | 3 | 임무 상세 편집 |
| S9 | Events | 1(최소) | 감사 로그 + 이벤트 스트림 |
| S10 | Settings | 1(껍데기) | 시스템 설정 |
| S11 | Login | 1 | 세션 기반 로그인 |

---

## 5. Layout System

### 5.1 기본 3-Pane 레이아웃

대부분의 화면은 아래 3영역 구조를 기본으로 한다.

```
┌──────────────────────────────────────────────────────────────┐
│  Global Header (48px 고정)                                   │
│  로고 | 현재 화면명 | 연결 상태 | 알림 | 사용자 메뉴          │
├──────┬───────────────────────────────────────────┬───────────┤
│      │                                           │           │
│  Nav │             Main Area                     │  Context  │
│ Side │    (맵, 테이블, 편집 캔버스 등)             │   Panel   │
│ 240px│                                           │   320px   │
│      │                                           │  (접힘    │
│      │                                           │   가능)   │
│      │                                           │           │
└──────┴───────────────────────────────────────────┴───────────┘
```

- **Global Header**: 48px 고정. 전체 화면에 걸쳐 공통.
- **Nav Sidebar**: 240px 고정. 화면 이동, 플릿 리스트 요약. `⌘[` 또는 `[`로 접기(160px 아이콘 전용 모드).
- **Main Area**: 나머지 너비 전체. 화면에 따라 맵 캔버스, 테이블, 편집기로 채워짐.
- **Context Panel**: 320px. 선택된 로봇/맵/임무의 상세 정보. `]`로 접기. Live Ops에서는 로봇 선택 시 자동 열림.

### 5.2 화면별 레이아웃 변주

| 화면 | Nav | Main | Context | 비고 |
|---|---|---|---|---|
| S1 Live Ops | 240px (플릿 리스트) | 맵 캔버스 (flex 1) | 320px (선택 로봇 상세) | Context는 선택 시만 열림 |
| S2 Fleet Overview | 240px | 테이블 전체 너비 | — | Context 없음 |
| S3 Robot Detail | 240px | 맵 + 텔레메트리 | 320px (타임라인) | |
| S4 Teleop | 없음 | 맵 + 조종 HUD | 320px (상태) | 전체 화면 모드. Nav 자동 숨김 |
| S6 Map Editor | 없음 | 맵 캔버스 전체 | 320px (WP 리스트) | 툴바는 캔버스 위 플로팅 |
| S9 Events | 240px | 이벤트 테이블 | — | |

### 5.3 그리드와 간격

- **베이스 유닛**: 4px
- **컨텐츠 패딩**: 패널 내부 16px (4u)
- **섹션 간격**: 24px (6u)
- **컴포넌트 내부 gap**: 8px (2u) 또는 12px (3u)
- **헤더 높이**: 48px (Global), 40px (패널 섹션)
- **행(row) 높이**: 테이블/리스트 기본 36px, 밀도 모드 28px

### 5.4 반응형 정책

- **기준 해상도**: 1920×1080 (주 타겟)
- **최소 지원**: 1366×768 (이하에서는 Context Panel 자동 숨김, 오버레이로 전환)
- **1440px 이하**: Context Panel이 오버레이(슬라이드인) 모드로 전환
- **모바일**: 비목표. 1024px 미만은 "지원되지 않는 해상도" 배너 표시 후 제한적 읽기 전용 모드

---

## 6. Visual Language

### 6.1 Typography

**원칙**: 모노스페이스 accent가 이 UI의 특성을 가장 강하게 드러낸다. 모든 기계적 데이터(좌표, ID, 타임스탬프, 수치)는 모노 폰트로 강제한다.

#### 6.1.1 Primary Pairing (권장)

| 용도 | 폰트 | 이유 |
|---|---|---|
| **Display / UI 라벨** | **Geist** (Vercel) | Linear와 유사한 차분한 기하학적 sans-serif이지만 Inter보다 좁은 자간과 독특한 터미널 형태가 관제 UI에 어울림 |
| **Body / 설명문** | **DM Sans** | Geist보다 약간 더 부드럽고 가독성이 높아 긴 설명 텍스트에 적합. Geist와 쌍을 이룰 때 지나치게 비슷하지 않음 |
| **Mono (데이터)** | **Geist Mono** | Display 폰트와 동일 패밀리여서 시각적 통일감 유지. 숫자 정렬이 뛰어남 |

#### 6.1.2 대체 Pairing (A안)

| 용도 | 폰트 |
|---|---|
| Display / UI 라벨 | **Outfit** |
| Body | **DM Sans** |
| Mono | **JetBrains Mono** |

#### 6.1.3 대체 Pairing (B안 — 가장 개성 강조)

| 용도 | 폰트 |
|---|---|
| Display / UI 라벨 | **Space Grotesk** |
| Body | **IBM Plex Sans** |
| Mono | **IBM Plex Mono** |

#### 6.1.4 타입 스케일

| 토큰 | 크기 | 행간 | 웨이트 | 용도 |
|---|---|---|---|---|
| `--text-2xl` | 24px | 32px | 600 | 화면 제목 (Robot ID 등) |
| `--text-xl` | 20px | 28px | 500 | 섹션 제목 |
| `--text-lg` | 16px | 24px | 500 | 패널 헤더, 중요 레이블 |
| `--text-base` | 14px | 20px | 400 | 본문, 테이블 셀, 설명 |
| `--text-sm` | 12px | 16px | 400 | 보조 정보, 타임스탬프 레이블 |
| `--text-xs` | 11px | 14px | 400 | 배지, 최소 캡션 |
| `--text-mono-base` | 13px | 18px | 400 | 텔레메트리 수치, 좌표 |
| `--text-mono-sm` | 11px | 14px | 400 | 타임스탬프, ID 축약 |

### 6.2 Color Tokens

#### 6.2.1 액센트 컬러 결정

순찰 로봇 관제라는 도메인의 액센트는 **Amber / 주황-황색 계열**로 정한다.
- 이유: 산업·안전 분야의 보편적 경고 색과 연결되면서도 "관제 시스템"의 야간 모드 오렌지 스크린 전통(레이더 화면 등)을 환기한다. 빨강/초록 상태 색과 팔레트에서 충분한 거리를 유지한다.
- 기준값: OKLCH `0.78 0.17 70` (황금빛 amber)

#### 6.2.2 전체 색 토큰

아래 값은 모두 OKLCH 표기. `light-dark()` CSS 함수로 라이트/다크 동시 지원 가능하도록 설계하되, **다크 테마가 기본**.

**배경 계층 (Background)**

```css
--bg-base:      oklch(0.10 0.005 240);   /* #0e1015 — 최저 배경, 화면 전체 */
--bg-surface:   oklch(0.14 0.006 240);   /* #161b23 — 패널, 사이드바 */
--bg-elevated:  oklch(0.18 0.007 240);   /* #1d2330 — 카드, 드롭다운, 모달 */
--bg-overlay:   oklch(0.22 0.008 240);   /* #242b38 — 호버, 인라인 선택 배경 */
--bg-inverse:   oklch(0.95 0.003 240);   /* 라이트 테마용 전환 배경 */
```

**전경 (Foreground)**

```css
--fg-primary:   oklch(0.93 0.010 240);   /* #e8eaf0 — 주요 텍스트 */
--fg-secondary: oklch(0.72 0.015 240);   /* #9fa8b8 — 보조 텍스트 */
--fg-muted:     oklch(0.52 0.012 240);   /* #626d82 — 비활성, 플레이스홀더 */
--fg-disabled:  oklch(0.38 0.008 240);   /* #424d5e — 비활성화 상태 */
--fg-inverse:   oklch(0.10 0.005 240);   /* 라이트 배경 위 텍스트 */
```

**테두리 (Border)**

```css
--border-subtle:  oklch(0.24 0.010 240); /* #282f3d — 패널 구분선, 기본 */
--border-default: oklch(0.32 0.012 240); /* #353f52 — 컴포넌트 경계 */
--border-strong:  oklch(0.44 0.015 240); /* #4d5a72 — 포커스 링, 강조 경계 */
--border-focus:   oklch(0.78 0.17 70);   /* amber — 포커스 링 (접근성) */
```

**액센트 (Amber)**

```css
--accent:          oklch(0.78 0.17 70);  /* 기본 액센트 — 선택, 활성, CTA */
--accent-dim:      oklch(0.60 0.14 70);  /* 호버 상태 */
--accent-subtle:   oklch(0.20 0.06 70);  /* 액센트 배경 틴트 */
--accent-fg:       oklch(0.10 0.005 240);/* 액센트 배경 위 텍스트 */
```

**상태 색 (Status)**

```css
/* IDLE */
--status-idle:        oklch(0.55 0.010 240);  /* 무채색 회색 */
--status-idle-bg:     oklch(0.18 0.008 240);

/* PATROLLING */
--status-ok:          oklch(0.72 0.18 145);   /* 청록 녹색 */
--status-ok-bg:       oklch(0.16 0.06 145);

/* WAIT */
--status-warn:        oklch(0.78 0.17 70);    /* amber (액센트와 동일) */
--status-warn-bg:     oklch(0.18 0.07 70);

/* EMERGENCY */
--status-crit:        oklch(0.65 0.24 25);    /* 선명한 적색 */
--status-crit-bg:     oklch(0.16 0.09 25);

/* AVOIDING */
--status-avoid:       oklch(0.74 0.18 45);    /* 주황 */
--status-avoid-bg:    oklch(0.17 0.07 45);

/* RETURNING */
--status-return:      oklch(0.72 0.15 225);   /* 하늘색 */
--status-return-bg:   oklch(0.16 0.06 225);

/* MANUAL */
--status-manual:      oklch(0.70 0.16 280);   /* 파랑-보라 (도메인에서 유일하게 쿨 컬러) */
--status-manual-bg:   oklch(0.16 0.06 280);

/* 연결 상태 */
--status-connected:    var(--status-ok);
--status-disconnected: var(--status-crit);
--status-stale:        oklch(0.60 0.12 55);   /* 탁한 황색 — 데이터 지연/스테일 */
--status-stale-bg:     oklch(0.17 0.05 55);
```

**맵 오버레이 색 (Canvas)**

```css
--map-robot-trail-alpha-start: 0.85;  /* 현재 위치 직전 잔상 밝기 */
--map-robot-trail-alpha-end:   0.0;   /* 30초 뒤 꼬리 끝 밝기 */
--map-waypoint-default:  oklch(0.80 0.15 75);  /* amber tint */
--map-waypoint-current:  oklch(0.90 0.18 70);  /* 현재 목적지 강조 */
--map-waypoint-done:     oklch(0.45 0.05 240); /* 지나온 waypoint */
--map-plan-path:         oklch(0.65 0.15 220); /* Nav2 plan 경로 */
--map-plan-path-alpha:   0.8;
```

**로봇별 식별 색 (Robot Identity Hues)**

10대 로봇까지 고려한 hue 팔레트. 각 로봇은 이 hue에서 파생된 OKLCH 색을 일관되게 사용한다.

```
Robot 0: hue 145  (청록 — 기본 단일 로봇과 동일)
Robot 1: hue 210  (하늘)
Robot 2: hue 30   (주황)
Robot 3: hue 290  (보라)
Robot 4: hue 170  (민트)
Robot 5: hue 55   (황색)
Robot 6: hue 350  (분홍)
Robot 7: hue 250  (인디고)
Robot 8: hue 100  (연두)
Robot 9: hue 0    (빨강 — EMERGENCY와 혼동 방지를 위해 마지막 순위)
```

### 6.3 Spacing, Radius, Borders

**간격 스케일**

```css
--space-1:  4px
--space-2:  8px
--space-3:  12px
--space-4:  16px
--space-5:  20px
--space-6:  24px
--space-8:  32px
--space-10: 40px
--space-12: 48px
--space-16: 64px
```

**코너 반경**

```css
--radius-sm:   3px   /* 작은 배지, pill */
--radius-base: 6px   /* 버튼, 입력, 패널 */
--radius-lg:   8px   /* 모달, 드롭다운 */
--radius-full: 999px /* 상태 dot, 원형 버튼 */
```

**보더 굵기**

```css
--border-width-thin:    1px   /* 기본 모든 테두리 */
--border-width-default: 1px   /* (다크 UI에서는 1px이 최적) */
--border-width-focus:   2px   /* 포커스 링 */
```

### 6.4 Motion Tokens

**원칙**: 모든 모션은 상태 변화의 "확인"이지 장식이 아니다. 짧고 날카롭게.

```css
--duration-instant:  80ms   /* 즉각 반응: 호버 배경색 변화 */
--duration-fast:    120ms   /* 대부분의 상태 전이: 버튼 클릭, 선택 */
--duration-base:    180ms   /* 패널 슬라이드인, 드롭다운 열기 */
--duration-slow:    250ms   /* 모달 열기, 대형 패널 전환 */

--ease-out:  cubic-bezier(0.16, 1, 0.3, 1)   /* 기본. 모든 진입 애니메이션 */
--ease-in:   cubic-bezier(0.4, 0, 1, 1)      /* 나가는 애니메이션 (닫기, 사라짐) */
--ease-linear: linear                         /* 진행 바, 타이머 */
```

**사용 맥락**

| 토큰 | 사용처 |
|---|---|
| `instant + ease-out` | 호버, 포커스 배경 변화, 색 전환 |
| `fast + ease-out` | 버튼 클릭 피드백, 상태 pill 색 전환, 선택 배경 |
| `base + ease-out` | 사이드 패널 슬라이드인, 드롭다운 팝업, 툴팁 등장 |
| `slow + ease-out` | 모달 진입, Context Panel 열기/닫기 |
| `linear` | 텔레메트리 수치 업데이트 표시(단, 수치 자체는 즉시 변경), 연결 복구 대기 표시 |

**금지 모션**

- `bounce`, `spring`, `elastic` easing
- `transform: scale()` 을 사용하는 팝인 효과 (단, 마우스 클릭 피드백 제외)
- 1초 이상 지속하는 전환
- 로봇 위치 보간 애니메이션 — 로봇 위치는 즉시 업데이트 (보간하면 실제 위치와 괴리)

**특수: 인광 궤적 페이드**

```css
/* 30초 구간의 trailing fade — CSS가 아닌 Canvas 렌더링으로 구현 */
/* 각 프레임에서: opacity = 1 - (age_seconds / 30) */
/* 꼬리 세그먼트별로 age를 계산해 가장 오래된 세그먼트부터 투명화 */
```

---

## 7. Realtime Data Patterns

### 7.1 데이터 스트림 목록 (현재 백엔드 기준)

| 메시지 타입 | 소스 | 빈도 | 프런트 갱신 방식 |
|---|---|---|---|
| `pose` | `/amcl_pose` | ~10Hz | 즉시 Canvas 재렌더 + 텔레메트리 패널 수치 업데이트 |
| `state` | `/patrol/state` | 이벤트성 | 상태 pill 색 전환 (`fast` motion) + 감사 로그 append |
| `waypoints` | `/patrol/waypoints` | 시작 시 1회 (latched) | Canvas waypoint 마커 재렌더 + WP 리스트 갱신 |
| `current_wp` | `/patrol/current_waypoint` | waypoint 도달마다 | 현재 목적지 마커 강조 갱신 |
| `plan` | `/plan` | 경로 계획마다 | Nav2 plan 경로선 재렌더 |

### 7.2 업데이트 빈도와 스로틀 전략

- **pose**: p95 < 300ms 목표 (PRD 비기능 요구사항). 10Hz로 오면 100ms마다 최신값만 반영. Canvas 는 `requestAnimationFrame`으로 렌더.
- **state**: 이벤트 기반이므로 스로틀 없음. 즉시 반영.
- **plan**: 용량이 클 수 있음 (수백 points). 수신 즉시 Canvas 업데이트, 별도 스로틀 없음.
- **프런트 상태 관리**: 로봇별로 `Map<robotId, RobotState>` 구조. 멀티 로봇 확장을 염두에 둔 구조. (Phase 1에서 단일 로봇이어도 동일 구조 사용)

### 7.3 스테일(Stale) 데이터 표현

마지막 텔레메트리 수신 이후 경과 시간을 기준으로 시각적 단계를 부여한다.

| 경과 시간 | 표현 |
|---|---|
| < 2초 | 정상. 연결 도트 초록 |
| 2–5초 | 연결 도트 amber. 텔레메트리 수치에 `--status-stale` 색 적용 |
| 5–15초 | 연결 도트 적색 점멸(1Hz). 패널에 "Data delayed Ns" 배너 |
| 15초+ | 연결 도트 적색 고정. 맵 위 로봇 아이콘 투명도 40%. "Connection lost" 배너 |

### 7.4 WebSocket 연결 상태

```
CONNECTING  → 헤더 연결 표시 회색 + "Connecting…" 텍스트
CONNECTED   → 헤더 연결 표시 초록 + 로봇 수 표시
DISCONNECTED→ 헤더 연결 표시 적색 + "Reconnecting in Ns…" + 전체 화면 비활성화 배너 없음 (읽기 전용 캐시 상태로 계속 표시)
ERROR       → 토스트 "WebSocket error — check network"
```

자동 재연결: 1초 후 첫 재시도, 이후 지수 백오프 (최대 30초 간격).

### 7.5 로봇 선택 상태 위계

| 상태 | 표현 |
|---|---|
| 기본 (unselected) | 로봇 색 도트 + 방향 화살표 |
| 호버 | 로봇 주변 halo (동일 hue, 30% 투명도, `instant` 전환) |
| 선택됨 | 로봇 주변 실선 링 (2px, 동일 hue) + Context Panel 자동 열림 |
| 포커스 (키보드) | `--border-focus` 2px 링 (amber) |

---

## 8. Component Inventory

모든 컴포넌트는 다음 상태를 최소 명세한다: `default`, `hover`, `active/pressed`, `selected`, `focused`, `disabled`, `loading`, `error`.

### 8.1 Global Header

**구성**: `[로고 + 제품명]` | `[현재 화면 breadcrumb]` | `[연결 상태 도트]` | `[알림 벨 아이콘 + 카운트 배지]` | `[사용자 아바타]`

- 높이: 48px. 배경: `--bg-surface`. 하단 보더: `1px --border-subtle`.
- 로고 영역: 32px × 32px 아이콘 + "Sentinel" 텍스트 (`--text-lg`, 600).
- 연결 상태: 8px dot. 색은 `--status-connected` / `--status-disconnected`. 애니메이션: 끊겼을 때 0.8Hz pulse.
- 알림 벨: 미확인 알림 있을 때 amber 배지 (카운트). 클릭 시 알림 드롭다운.

### 8.2 Nav Sidebar

**구성**: 상단 내비게이션 링크 + 하단 플릿 요약 리스트

- 너비: 240px 전개, 48px 아이콘 전용 (접힘)
- 내비게이션 링크: 아이콘 + 텍스트 라벨. 활성 화면은 `--accent-subtle` 배경 + `--accent` 좌측 3px border.
- 플릿 요약 리스트: 각 로봇을 한 줄 `RobotMiniRow`로 표시. 상태 dot + 이름 + 배터리 수치.
- 하단: 설정 링크 + 사용자명.

### 8.3 Status Pill

상태를 나타내는 인라인 배지. 텍스트 + 좌측 3px 컬러 dot.

```
상태별 색: --status-{idle|ok|warn|crit|avoid|return|manual}
배경: --status-{...}-bg
텍스트: --fg-primary
폰트: --text-xs, 600, letter-spacing: 0.06em, uppercase
패딩: 2px 8px
반지름: --radius-sm
```

**상태 목록**:
- `IDLE` — 회색
- `PATROLLING` — 초록
- `WAIT` — amber
- `EMERGENCY` — 적색 (1Hz 미세 pulse 배경)
- `AVOIDING` — 주황
- `RETURNING` — 하늘색
- `MANUAL` — 블루-퍼플

### 8.4 Robot Card (Fleet List 내)

Nav Sidebar 또는 Fleet Overview 테이블의 로봇 행.

```
┌─────────────────────────────────┐
│ [•] Robot-01   PATROLLING  🔋85%│
│     구역A 순찰 · WP 3/8          │
└─────────────────────────────────┘
```

- 높이: 56px (리스트), 36px (밀도 모드)
- 좌측 컬러 바 (4px): 로봇 식별 hue
- 호버: `--bg-overlay`
- 선택: `--bg-overlay` + 좌측 컬러 바 2px→4px
- EMERGENCY 상태: 전체 행 배경 `--status-crit-bg`, 텍스트 `--status-crit`

### 8.5 Telemetry Row

Robot Detail의 수치 표시 행. 레이블 + 값의 2-컬럼 레이아웃.

```
pose.x     1.234 m
pose.y    -0.872 m
yaw        45.2 °
state      PATROLLING
waypoint   3 / 8
```

- 레이블: `--text-sm`, `--fg-muted`, 100px 고정 너비
- 값: `--text-mono-base`, `--fg-primary`
- 행 높이: 28px
- 스테일 상태: 값 텍스트 색을 `--status-stale`로 전환

### 8.6 Map Canvas Overlay Layer

캔버스 위에 그려지는 레이어 시스템. z-order (아래부터):

1. **Map Image Layer** — 배경 맵 이미지 (grayscale filter 적용: 원본보다 10% 어둡게, 채도 제거 후 청색 tint)
2. **Zone Layer** (FMS 확장용 자리 예약) — 폴리곤 영역
3. **Plan Path Layer** — Nav2 plan 경로선. `--map-plan-path`, 2px, opacity 0.8
4. **Waypoint Layer** — waypoint 마커. amber dot + 번호 레이블
5. **Robot Trail Layer** — 인광 잔상 궤적 (30초 fade)
6. **Robot Layer** — 로봇 아이콘 (원 + 방향 화살표)
7. **Interaction Layer** — 호버 halo, 선택 링, 드래그 핸들 (편집 모드)
8. **HUD Layer** — 맵 위 플로팅 툴바 (확대/축소, 레이어 토글)

**맵 좌표 변환**: `worldToPixel(wx, wy)` 함수는 현재 `index.html`의 구현을 계승. `cfg.resolution`, `cfg.origin`, `cfg.height` 사용. ROS y-up → canvas y-down 플립.

**맵 인터랙션**:
- 드래그: 팬
- 스크롤: 줌 (min 0.2x, max 8x)
- 더블클릭 로봇: 해당 로봇 선택 + Context Panel 열기
- `F` 키: 선택된 로봇으로 카메라 이동 ("Follow" 토글)

### 8.7 Command Palette

`⌘K`(macOS) / `Ctrl+K`(Windows/Linux)로 열리는 전역 커맨드 팔레트.

```
┌──────────────────────────────────────────┐
│ > _                                      │  ← 검색 입력
├──────────────────────────────────────────┤
│  최근 명령                                │
│  ↳ Robot-01 상세 보기                     │
│  ↳ 임무 할당                              │
├──────────────────────────────────────────┤
│  화면 이동                                │
│  go Dashboard          g d               │
│  go Fleet Overview     g f               │
│  go Events             g e               │
├──────────────────────────────────────────┤
│  로봇 액션                                │
│  Select Robot-01       1                 │
│  Emergency Stop All    !                 │
└──────────────────────────────────────────┘
```

- 배경: `--bg-elevated`. 보더: `1px --border-default`. 반지름: `--radius-lg`.
- 입력: `--text-base`, `--fg-primary`. placeholder: `--fg-muted`.
- 항목 호버/포커스: `--bg-overlay`. 선택: amber 좌측 2px border.
- 너비: 560px. 최대 높이: 480px. 위치: 화면 중앙 상단 1/3.
- 오버레이 배경: rgba(0,0,0,0.5) `backdrop-blur(4px)`.
- 열기: `base + ease-out`. 닫기: `fast + ease-in`.

### 8.8 Notification Toast

알림 토스트. 화면 우상단 stack.

```
┌──────────────────────────────────────────┐
│ [!] EMERGENCY — Robot-03                 │
│     장애물 감지로 긴급 정지                │
│     [상세 보기]                    [×]    │
└──────────────────────────────────────────┘
```

- 너비: 320px. 보더 좌측 4px: 알림 심각도 색.
- 중요도:
  - `EMERGENCY`: `--status-crit` 보더, 배경 `--status-crit-bg`
  - 경고: `--status-warn` 보더
  - 정보: `--border-default` 보더
- EMERGENCY 토스트는 자동 소멸 없음 (명시적 닫기 필요).
- 일반 정보 토스트: 5초 후 자동 소멸 + 하단 타이머 바.
- Stack: 최대 5개. 6번째는 "N more…" collapse.

### 8.9 Waypoint Marker (Canvas)

| 상태 | 외형 |
|---|---|
| 기본 | 8px amber dot + 흰 번호 텍스트 + 얇은 외곽선 |
| 현재 목적지 | 12px amber dot + 바깥 pulse ring (1Hz, `--status-warn`) |
| 지나온 | 6px 흰 dot, 투명도 50% |
| 편집 모드 hover | 16px dot + 십자 핸들 표시 |
| 편집 모드 선택 | amber 링 + yaw 회전 핸들 |

### 8.10 Plan Timeline (Robot Detail)

최근 N분간 상태 전이를 가로 타임라인으로 표시.

```
[ IDLE ]────[ PATROLLING ─────────────── ]──[ WAIT ]──[ PATROLLING ──── ]
  09:12              09:13                    09:45        09:46
```

- 높이: 40px 트랙 + 24px 타임 레이블
- 각 구간은 상태 색으로 채색
- 마우스 호버 시 해당 시점의 포즈와 이벤트 툴팁
- 시간 범위: 기본 최근 30분. 드래그로 스크롤, 핀치/스크롤로 줌.

### 8.11 Teleop HUD

S4 Teleop 화면 전용. 맵 위 플로팅 조종 UI.

```
        [ ↑ ]
  [ ← ] [ ■ ] [ → ]       ← WASD / 방향키 / 클릭
        [ ↓ ]

선속도:  0.0 m/s    각속도: 0.0 rad/s
데드맨:  ████████░░  (200ms 타이머)
```

- 배경: `--bg-elevated`, opacity 0.92
- 비상 정지 버튼 (■): 24×24px, `--status-crit` 배경, 항상 활성
- 데드맨 타이머 바: 입력 없을 때 200ms에 걸쳐 소진. 소진 시 자동 정지 + 시각 경고.
- 조종 중에는 다른 로봇 클릭/화면 전환이 잠금 (확인 다이얼로그 표시).

---

## 9. Keyboard Interaction Map

### 9.1 글로벌 단축키

| 단축키 | 동작 |
|---|---|
| `⌘K` / `Ctrl+K` | Command Palette 열기 |
| `⌘/` / `Ctrl+/` | 단축키 도움말 모달 |
| `Esc` | 선택 해제 / 모달 닫기 / Command Palette 닫기 |
| `g d` | go Dashboard |
| `g f` | go Fleet Overview |
| `g e` | go Events |
| `g m` | go Maps |
| `g s` | go Settings |

### 9.2 Live Ops Dashboard 단축키

| 단축키 | 동작 |
|---|---|
| `1`–`9`, `0` | 로봇 1–10 직접 선택 |
| `j` / `k` | 플릿 리스트에서 이전/다음 로봇 |
| `Enter` | 선택된 로봇의 Robot Detail 열기 |
| `F` | 선택된 로봇으로 카메라 Follow 토글 |
| `r` | 선택된 로봇으로 맵 카메라 리셋 |
| `+` / `-` | 맵 줌 인/아웃 |
| `Space` | 맵 팬 모드 토글 (기본: 드래그 팬) |
| `f` | 플릿 리스트 필터 |

### 9.3 Robot Detail 단축키

| 단축키 | 동작 |
|---|---|
| `t` | Teleop 모드 진입 |
| `[` / `]` | Context Panel 접기/펴기 |
| `Backspace` | 뒤로 (Dashboard로) |

### 9.4 Teleop 단축키

| 단축키 | 동작 |
|---|---|
| `W` / `↑` | 전진 |
| `S` / `↓` | 후진 |
| `A` / `←` | 좌회전 |
| `D` / `→` | 우회전 |
| `Space` | 즉시 정지 (dead stop) |
| `Esc` | Teleop 모드 종료 확인 |

### 9.5 Map Editor 단축키

| 단축키 | 동작 |
|---|---|
| `v` | 선택 도구 |
| `a` | waypoint 추가 도구 |
| `Del` / `Backspace` | 선택된 waypoint 삭제 |
| `⌘Z` / `Ctrl+Z` | Undo |
| `⌘⇧Z` / `Ctrl+Y` | Redo |
| `⌘S` / `Ctrl+S` | 저장 |
| `Esc` | 현재 도구 취소 / 선택 해제 |

---

## 10. Empty / Loading / Error / Disconnected States

### 10.1 Empty States

| 화면 | 조건 | 표시 내용 |
|---|---|---|
| Live Ops Dashboard — 맵 | 등록된 맵 없음 | 중앙에 맵 아이콘 + "등록된 맵이 없습니다. Maps에서 맵을 업로드하세요." + [맵 업로드] CTA |
| Live Ops Dashboard — 플릿 리스트 | 연결된 로봇 없음 | "연결된 로봇이 없습니다." + 연결 도트 회색 |
| Fleet Overview | 로봇 0대 | 중앙에 로봇 아이콘 + "등록된 로봇이 없습니다." (Robot Registry 링크) |
| Events | 이벤트 없음 | "아직 기록된 이벤트가 없습니다." |
| Missions | 임무 없음 | "저장된 임무가 없습니다. Map Editor에서 경로를 만들어 저장하세요." + [맵 열기] CTA |

### 10.2 Loading States

**원칙**: 스켈레톤 대신 텍스트 표시. 빠른 텔레메트리 루프에서 pulse 애니메이션은 시각적 노이즈가 된다.

| 화면 | 로딩 표현 |
|---|---|
| 맵 이미지 로딩 | 캔버스 배경 `--bg-base` + 중앙 "맵 로딩 중…" 텍스트 (`--fg-muted`) |
| 초기 WebSocket 연결 | 헤더 연결 도트 `pulse` + "Connecting to fleet backend…" |
| Robot Detail 첫 진입 | 각 Telemetry Row의 값 위치에 "—" 표시 + `--fg-muted` |
| 임무 할당 중 | 버튼 텍스트 "할당 중…" + 비활성화 |

### 10.3 Error States

| 오류 | 표현 |
|---|---|
| 맵 이미지 로드 실패 | 캔버스에 "맵 이미지를 불러올 수 없습니다. 서버 로그를 확인하세요." + [재시도] |
| API 오류 (5xx) | Toast "서버 오류 — 잠시 후 재시도" |
| 권한 오류 (403) | Toast "이 작업을 수행할 권한이 없습니다." |
| 임무 할당 실패 | 인라인 오류 메시지 (다이얼로그 내) + 재시도 버튼 |
| Teleop 데드맨 타임아웃 | 빨간 바 + "입력 없음 — 자동 정지됨" 오버레이 (로봇 정지 후) |

### 10.4 Disconnected State

WebSocket 연결이 끊어진 상태.

- **헤더**: 연결 도트 적색 pulse + "Disconnected — Reconnecting…"
- **화면**: 화면 전체를 가리지 않음. 기존 캐시 데이터를 그대로 표시하되, 각 로봇 행과 텔레메트리 값에 `--status-stale` 적용.
- **재연결 배너**: 화면 상단 아래 4px 고정 바 (배경 `--status-crit-bg`, 텍스트 `--status-crit`). "WebSocket 연결 끊김 — 재연결 중… (Xs 후 재시도)"
- **조작 제한**: 명령(임무 할당, 조종)은 비활성화. 툴팁: "연결이 복구되면 사용 가능합니다."

---

## 11. Screen-by-screen Specs

### 11.1 S1 — Live Ops Dashboard

**목적**: 전체 플릿 상태를 3초 이내에 파악한다.

**레이아웃**:
```
┌─────────────────────────────────────────────────────────────────────┐
│ Header: Sentinel-Patrol  |  Dashboard  |  [연결●] [🔔3] [사용자▾]   │
├────────────┬────────────────────────────────────┬────────────────────┤
│ Nav Side   │         Map Canvas                 │  Robot Detail      │
│            │                                    │  Context Panel     │
│ [Dashboard]│  [맵 이름▾]  [레이어 토글] [팔로우] │                    │
│ [Fleet]    │                                    │  Robot-01          │
│ [Maps]     │  ┌──────────────────────────────┐  │  ● PATROLLING      │
│ [Missions] │  │                              │  │  WP 3 / 8          │
│ [Events]   │  │  [맵 배경]                    │  │                    │
│            │  │    ◉ Robot-01 (WP→3)         │  │  구역A 순찰         │
│ ─────────  │  │    ◎ Robot-02 (WP→5)         │  │                    │
│ Fleet      │  │    ◈ Robot-03 ⚠ EMERGENCY    │  │  Pose              │
│            │  │       ~~~~~~~~~~~~~~~~       │  │  x  1.234 m       │
│ ● Robot-01 │  │  (궤적 잔상)                  │  │  y -0.872 m       │
│   PATROL   │  │                              │  │  yaw  45.2°       │
│ ● Robot-02 │  └──────────────────────────────┘  │                    │
│   PATROL   │                                    │  [Robot Detail →]  │
│ ⚠ Robot-03 │  [+] [-] [◎] [맵 fit]             │  [수동 조종]        │
│   EMERG    │                                    │                    │
└────────────┴────────────────────────────────────┴────────────────────┘
```

**핵심 동작**:
- 맵 셀렉터: 등록된 맵 목록을 드롭다운으로 선택. 다른 맵 로봇은 표시 안 됨.
- EMERGENCY 로봇: 전체 Robot Card가 `--status-crit-bg`로 강조 + 맵 위 아이콘도 pulse.
- 로봇 클릭: Context Panel 슬라이드인 (`base + ease-out`).
- Context Panel "Robot Detail →" 링크: S3으로 이동.

**데이터 요구**:
- `GET /api/v1/maps` — 맵 목록
- `GET /api/v1/robots` — 로봇 목록 (배터리, 현재 임무 포함)
- `WS /ws` — 실시간 pose/state/waypoints/current_wp/plan 스트림 (robotId 필드 포함)

### 11.2 S2 — Fleet Overview

**목적**: 전체 로봇 상태를 테이블로 정렬/필터/검색한다.

**레이아웃**:
```
┌─────────────────────────────────────────────────┐
│ Fleet Overview              [+ 로봇 등록(Todo)]  │
│                                                  │
│ [검색__________] [상태▾] [맵▾] [임무▾]            │
├──────┬────────┬──────────┬──────┬───────┬────────┤
│ ID   │ 이름   │ 상태      │ 배터리│ 맵    │ 임무   │
├──────┼────────┼──────────┼──────┼───────┼────────┤
│ R-01 │ Robot-01│●PATROL  │  85% │ Wh-A  │ 구역A  │
│ R-02 │ Robot-02│●PATROL  │  72% │ Wh-A  │ 구역B  │
│ R-03 │ Robot-03│⚠EMERG   │  61% │ Wh-B  │ —      │
└──────┴────────┴──────────┴──────┴───────┴────────┘
│ 로봇 3대 (1 EMERGENCY)   [일괄 정지] [임무 할당]  │
```

**동작**:
- 행 클릭: Robot Detail(S3)로 이동
- 다중 선택: checkbox + `Shift+click` 범위 선택
- 일괄 액션: 선택된 로봇에 임무 할당, 정지 등
- 컬럼 정렬: 클릭으로 asc/desc 토글

**데이터 요구**:
- `GET /api/v1/robots?filter=...&sort=...` — 페이지네이션 포함

### 11.3 S3 — Robot Detail

**목적**: 단일 로봇의 실시간 텔레메트리, 맵 위치, 상태 히스토리를 한 화면에서 본다.

**레이아웃**:
```
┌─────────────────────────────────────────────────────────────────┐
│ Header                                                          │
├────────────┬──────────────────────────────┬─────────────────────┤
│ Nav Side   │  Robot-01  ● PATROLLING  [조종 모드] [임무 재할당]  │
│            ├──────────────────────────────┼─────────────────────┤
│            │                              │  상태 타임라인        │
│            │  Mini Map                    │                      │
│            │  (해당 로봇 중심)             │  [─IDLE─][─PATROL─] │
│            │                              │   09:12    09:13     │
│            ├──────────────────────────────┤                      │
│            │  Telemetry                   │  현재 임무            │
│            │  pose.x   1.234 m            │  구역A 순찰           │
│            │  pose.y  -0.872 m            │  WP 3/8 (37%)        │
│            │  yaw       45.2°             │                      │
│            │  WP        3 / 8             │  카메라 (Phase 2)     │
│            │  배터리    85%  (OQ-3)        │  [스트리밍 영역]      │
│            │  마지막 수신  0.2s ago        │                      │
│            │                              │  최근 이벤트          │
│            │  이벤트 로그 (최근 5건)       │  09:45 WP 3 도달     │
│            │  ...                         │  09:13 PATROL 시작   │
└────────────┴──────────────────────────────┴─────────────────────┘
```

**데이터 요구**:
- `GET /api/v1/robots/:robotId` — 로봇 정보
- `GET /api/v1/events?robotId=:robotId&limit=50` — 최근 이벤트
- `WS /ws` — 해당 로봇의 실시간 스트림

### 11.4 S4 — Teleop

**목적**: 운영자가 로봇을 직접 조종한다. 다른 기능 접근은 최소화하고 조종에 집중.

**레이아웃**:
```
┌─────────────────────────────────────────────────────────────┐
│ [⬅ 조종 종료]  Robot-01  ⚡ MANUAL  |  데드맨 ████████░░  │
├──────────────────────────────────────┬──────────────────────┤
│                                      │ 속도                  │
│   맵 캔버스 (전체 너비)               │ 선속도  0.0 m/s       │
│   (선택 로봇 추적 + 경로 표시)        │ 각속도  0.0 rad/s     │
│                                      │                      │
│                                      │ 조종 키              │
│   ┌───────────────────────────┐      │  W/↑  전진           │
│   │  조종 패드 (플로팅 HUD)    │      │  S/↓  후진           │
│   │     [ ↑ ]                │      │  A/←  좌회전         │
│   │  [← ] [■] [ →]           │      │  D/→  우회전         │
│   │     [ ↓ ]                │      │  SPC  즉시 정지       │
│   └───────────────────────────┘      │                      │
│                                      │ 안전                  │
│                                      │ 안전게이트  활성       │
└──────────────────────────────────────┴──────────────────────┘
```

**동작**:
- 화면 진입 시 자동으로 MANUAL 상태 요청 API 호출.
- 데드맨 타이머: 입력 없을 때 200ms 안에 0으로 감소. 0이 되면 정지 + 시각 경고.
- 조종 종료: "조종 종료" 버튼 또는 `Esc`. 확인 다이얼로그 후 이전 임무 재개 여부 선택.

**데이터 요구**:
- `POST /api/v1/robots/:robotId/control/start` — MANUAL 모드 진입
- `WS /ws` — teleop 명령 전송 (client → server)
- `POST /api/v1/robots/:robotId/control/stop` — MANUAL 모드 종료

### 11.5 S5 — Maps

**목적**: 맵 레지스트리 목록 관리.

```
┌──────────────────────────────────────────────────┐
│ Maps                          [+ 맵 업로드]       │
│                                                   │
│ ┌────────────┐  ┌────────────┐                    │
│ │ [맵 썸네일] │  │ [맵 썸네일] │                    │
│ │ Warehouse-A │  │ Warehouse-B │                    │
│ │ 3대 사용 중 │  │ 1대 사용 중 │                    │
│ │ [편집] [삭제]│  │ [편집] [삭제]│                   │
│ └────────────┘  └────────────┘                    │
└──────────────────────────────────────────────────┘
```

**업로드 플로우**:
1. 파일 드롭 또는 선택 (`.yaml` + `.pgm` 쌍).
2. 서버에서 `prepare_map.py` 로직 수행 후 미리보기 렌더.
3. 이름 입력 → 저장.

### 11.6 S6 — Map Editor

**목적**: 맵 위에 waypoint를 배치/편집한다.

**레이아웃**:
```
┌───────────────────────────────────────────────┬─────────────────┐
│  [← 뒤로]  Warehouse-A  편집 중   [저장] [되돌리기]  [Push to Robot] │
├───────────────────────────────────────────────┼─────────────────┤
│                                               │ Waypoints        │
│  맵 캔버스 전체 (편집 모드)                    │                  │
│                                               │ 1. (1.2, -0.8)  │
│  플로팅 툴바:                                  │ 2. (3.4,  1.2)  │
│  [선택 ▷] [추가 +] [삭제 ×]                   │ 3. (0.0,  2.5)  │
│  [루프 ⟲] [열린경로 →]                        │                  │
│                                               │ [루프 ⟲ 닫기]   │
│   ①──②                                       │                  │
│   |    \                                      │ 저장된 임무명    │
│   ④────③                                     │ [구역A 순찰▾]    │
│                                               │                  │
└───────────────────────────────────────────────┴─────────────────┘
```

**동작**:
- waypoint 추가: 도구 선택 후 맵 클릭. 즉시 번호 배지 표시.
- waypoint 이동: 드래그.
- yaw 조정: 선택 후 외곽 핸들 드래그.
- 순서 변경: 우측 리스트 드래그 앤 드롭.
- **저장 vs 배포 분리**: "저장"은 서버에만 저장. "Push to Robot"은 별도 확인 후 로봇에 전달.
- Undo 스택: 최대 50 단계. `⌘Z`.

### 11.7 S7/S8 — Missions (List + Detail)

**S7 Missions 목록**:
```
┌────────────────────────────────────────────┐
│ Missions                     [+ 새 임무]   │
│ [검색_______] [맵▾] [태그▾]               │
│                                             │
│ 구역A 순찰    Warehouse-A  8 WP  ●활성 2대  │
│ 구역B 순찰    Warehouse-A  6 WP  ●활성 1대  │
│ 전체 순회     Warehouse-B  12 WP ○비활성    │
└────────────────────────────────────────────┘
```

**S8 Mission Detail**: 임무 이름, 맵, waypoint 리스트, 편집 링크, 현재 할당된 로봇 목록, "할당" 버튼.

### 11.8 S9 — Events (감사 로그)

**목적**: 모든 상태 전이, 운영자 조작 이벤트를 시간순으로 열람.

```
┌───────────────────────────────────────────────────────────┐
│ Events                                   [CSV 다운로드]   │
│ [검색_______] [로봇▾] [이벤트 타입▾] [기간▾]              │
├────────────┬────────────┬──────────┬───────────────────────┤
│ 시각        │ 로봇       │ 타입      │ 상세                  │
├────────────┼────────────┼──────────┼───────────────────────┤
│ 14:32:01   │ Robot-01   │ STATE    │ PATROLLING → WAIT     │
│ 14:31:55   │ Robot-03   │ TELEOP   │ 수동 조종 시작 (op:kim)│
│ 14:28:10   │ Robot-02   │ MISSION  │ 구역B 순찰 할당        │
└────────────┴────────────┴──────────┴───────────────────────┘
```

- 시각: `--text-mono-sm`, `--fg-muted`
- 이벤트 타입 배지: 타입별 색 (STATE: gray, TELEOP: amber, MISSION: blue, EMERGENCY: red)
- 실시간 append: 새 이벤트는 맨 위에 `fast + ease-out` 슬라이드인

### 11.9 S11 — Login

최소한의 로그인 화면.

```
┌──────────────────────────────────────────┐
│                                          │
│           Sentinel-Patrol                │
│           순찰 로봇 관제 시스템            │
│                                          │
│  [사용자명 ___________________________]  │
│  [비밀번호 ___________________________]  │
│                                          │
│           [로그인]                        │
│                                          │
└──────────────────────────────────────────┘
```

- 배경: `--bg-base`. 폼 배경: `--bg-surface`. 보더: `1px --border-default`.
- 에러: 폼 위 인라인 텍스트 (`--status-crit`). 토스트 없음.

---

## 12. Accessibility

- **포커스 링**: 모든 인터랙티브 요소에 `--border-focus` 2px 링. `:focus-visible`만 적용 (마우스 클릭 시 링 없음).
- **색 대비**: `--fg-primary` on `--bg-base` — WCAG AA 이상. 상태 텍스트는 색만으로 구분하지 않고 텍스트 레이블 병행.
- **키보드 완전 접근**: 모든 주요 동작은 키보드만으로 가능. 마우스 필수 동작 없음.
- **ARIA**: `role="alert"` (Toast, EMERGENCY), `aria-live="polite"` (텔레메트리 업데이트), `aria-label` (아이콘 버튼 전수).
- **모션 감소**: `prefers-reduced-motion: reduce` 미디어 쿼리 준수. 트레일 페이드와 pulse를 정적으로 대체.
- **확대 지원**: 브라우저 125%, 150% 줌에서 레이아웃 깨지지 않음. 맵 캔버스는 자체 줌 핸들러 사용.

---

## 13. Open Questions (하류 에이전트 및 PM에게)

### ui-ux-designer가 제기하는 새 OQ

**OQ-UI-1 (PRD OQ-10 응답) — 시뮬레이션/실물 로봇 구분**
PRD OQ-10에서 ui-ux-designer에게 질문을 넘겼다. 제안: 로봇 이름/ID에 `[SIM]` 접두 배지(배경 `--bg-elevated`, 텍스트 `--fg-muted`)를 추가. 맵 위 로봇 아이콘에 점선 외곽선(실선 = 실물, 점선 = 시뮬). 데이터 모델에 `isSimulated: boolean` 필드가 필요. — `api-designer`, `be-engineer`에게 확인 요청.

**OQ-UI-2 — 배터리 없는 로봇의 표시**
PRD OQ-3에서 배터리 텔레메트리가 없는 로봇을 어떻게 표시하는지 질문. 제안: 배터리 수치 위치에 `—` 표시 + 툴팁 "배터리 정보 미지원". 배터리 부재가 오류가 아님을 명확히 구분. — `api-designer`에게 API 필드 nullable 처리 요청.

**OQ-UI-3 — 다중 로봇 동일 맵 시 Robot Identity Hue 할당 시점**
로봇 hue는 서버에서 고정 할당해야 하는가, 프런트에서 `robotId` 기준으로 결정적으로 계산해야 하는가? 제안: `robotId`의 hash → hue index 결정적 매핑. 서버 API 필드 불필요. — `fe-engineer` 결정 사항. 단, 로봇 0–9까지 hue 순서는 이 문서가 정의한 순서를 따름.

**OQ-UI-4 — Plan Path와 Waypoint 경로선의 시각적 분리**
Nav2 `/plan`이 있을 때 "Nav2 계획 경로"(파란 실선)와 "waypoint 순서 연결선"(amber 점선)이 겹칠 수 있다. 레이어 순서와 색으로 충분히 구분되는지 Phase 1 구현 후 검토 필요. — `fe-engineer` 구현 후 리뷰.

**OQ-UI-5 — Teleop 화면에서 카메라 스트리밍 동시 표시 여부**
Phase 2에서 카메라와 Teleop이 동시에 필요하다. 현재 S4 레이아웃은 카메라 영역을 우측 패널에 자리만 예약해두었다. 맵 + 카메라 동시 표시 비율(50:50 vs 70:30 vs PiP)을 Phase 2 설계 시 확정 필요. — `ui-ux-designer` (Phase 2 때 이 문서 업데이트 예정).

**OQ-UI-6 — 알림 오디오 신호 정책**
PRD F-MON-8에서 알림 센터 언급이 있지만 오디오 신호 여부는 명시되지 않음. EMERGENCY 알림 시 브라우저 오디오 알림(짧은 경고음)을 기본 활성화할지, 사용자 설정으로 옵트인할지 결정 필요. — `pm` 또는 `fe-engineer`에서 결정.

### PRD에서 이미 제기된 OQ 중 ui-ux-designer의 입장

- **OQ-2 (MANUAL 상태)**: UI는 `MANUAL` 상태를 완전한 상태로 취급하고 전용 Status Pill을 정의했다. 상태머신 결정은 `be-engineer` 결정에 따른다.
- **OQ-8 (프레임워크)**: React + TypeScript + Canvas (Konva 또는 직접 구현) 권장. 맵 편집기(S6)는 드래그/터치 인터랙션이 많아 Konva 레이어 추상화가 유리하다. 최종 결정은 `fe-engineer`.
