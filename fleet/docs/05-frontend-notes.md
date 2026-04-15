# Sentinel Patrol — Frontend Implementation Notes

- 문서 버전: 0.3
- 작성일: 2026-04-14
- 담당: fe-engineer
- 상류 입력: `02-ui-ux-design.md` (v0.1), `03-api-design.md` (v0.1)

---

## 1. 구현 범위

이번 작업은 `fleet/frontend/dashboard/index.html` (vanilla HTML/JS)을 **React 18 + Vite + TypeScript** 기반으로 재구현하는 것이다. 현재 index.html에 존재하는 기능만 이식했으며, 디자인 문서에 기술된 그 외 기능은 의도적으로 제외했다.

### 포함된 기능 (5가지)

| # | 기능 | 구현 위치 |
|---|---|---|
| 1 | **헤더**: 제목, WS 연결 상태 배지, 로봇 상태 pill, pose 텍스트 | `src/components/Header.tsx` |
| 2 | **WebSocket 클라이언트**: `ws://${location.host}/ws` 연결, 1초 후 재연결 | `src/hooks/useFleetSocket.ts` |
| 3 | **메시지 핸들링**: `pose`, `plan`, `state`, `waypoints`, `current_wp` 5타입 | `src/hooks/useFleetSocket.ts` |
| 4 | **맵 캔버스 렌더링**: MAP_CONFIG 로드, world→pixel 변환, waypoint/plan/robot 오버레이 | `src/components/MapCanvas.tsx` |
| 5 | **상태별 색상**: idle/patrolling/wait/emergency/avoiding/returning (디자인 토큰 적용) | `src/index.css` |

### 의도적으로 제외한 기능

현재 `index.html`에 없기 때문에 이번 작업에서 제외한 항목들 (디자인 문서에는 기술되어 있음):

- Nav Sidebar (플릿 리스트, 네비게이션 링크)
- Context Panel (선택된 로봇 상세)
- 알람/이벤트 패널
- 인광(phosphorescent) 궤적 페이드 (디자인 문서 Section 2 "The One Thing People Will Remember" 항목)
- 스테일 데이터 표현 (2초/5초/15초 임계값별 시각화)
- 로봇 선택 인터랙션 (hover/click)
- 알림 벨 아이콘
- 사용자 아바타/메뉴
- 라우팅 (단일 페이지 앱 고정)
- MANUAL 상태 색 (백엔드 API에서 현재 전송 안 함)

---

## 2. 디렉터리 구조

```
fleet/frontend/                    ← Vite 프로젝트 루트 (곧 FastAPI dist 서빙 루트)
├── package.json
├── vite.config.ts                 ← outDir: dist (기본값), publicDir: public (기본값)
├── tsconfig.json
├── tsconfig.app.json
├── tsconfig.node.json
├── eslint.config.js
├── index.html                     ← Vite 진입점 (소스)
├── prepare_map.py                 ← ROS map PGM/YAML → public/map.png + public/map_config.js
├── src/
│   ├── main.tsx                   ← React 루트 마운트
│   ├── App.tsx                    ← 최상위 컴포넌트 (MAP_CONFIG 유무 분기)
│   ├── index.css                  ← 디자인 토큰 + 전체 스타일 (CSS Variables)
│   ├── types.ts                   ← TypeScript 타입 정의
│   ├── hooks/
│   │   └── useFleetSocket.ts      ← WS 연결 + useReducer 상태 관리
│   └── components/
│       ├── Header.tsx             ← 헤더 (연결 상태, 상태 pill, pose)
│       └── MapCanvas.tsx          ← 캔버스 렌더링 (map/waypoints/plan/robot)
├── public/                        ← 정적 자산 (Vite가 dist/ 루트에 그대로 복사)
│   ├── favicon.svg
│   ├── icons.svg
│   ├── map_config.js              ← prepare_map.py 산출물 (gitignored)
│   └── map.png                    ← prepare_map.py 산출물 (gitignored)
├── dist/                          ← 빌드 산출물 (gitignored)
│   ├── index.html
│   ├── assets/
│   │   ├── index-[hash].js
│   │   └── index-[hash].css
│   ├── map_config.js              ← public/map_config.js 복사본
│   └── map.png                    ← public/map.png 복사본
└── node_modules/                  ← (gitignored)
```

---

## 3. 실행 / 빌드 명령

```bash
cd fleet/frontend

# 의존성 설치 (최초 1회)
npm install

# 개발 서버 (HMR)
npm run dev
# → http://localhost:5173 에서 접근

# 프로덕션 빌드 → fleet/frontend/dist/
npm run build
# tsc -b && vite build

# 타입 체크만
npx tsc --noEmit
```

### 맵 자산 준비

```bash
cd fleet/frontend
python3 prepare_map.py ~/waffle_map.yaml
# → public/map.png, public/map_config.js 생성
# 이후 npm run build 하면 dist/ 에도 복사됨
```

### 빌드 출력 경로 설명

`vite.config.ts`는 `outDir`/`publicDir` 모두 Vite 기본값을 사용한다.
- `publicDir`: `public/` — `prepare_map.py` 산출물을 이 경로에 두면 개발 서버와 빌드 모두에서 `/map_config.js`, `/map.png`로 접근 가능
- `outDir`: `dist/` — `npm run build` 결과물이 여기에 출력됨

백엔드 기동 후 `http://localhost:<port>/` 에 접근하면 `dist/index.html` (React 앱)이 로드된다.

---

## 4. WebSocket 메시지 → 컴포넌트 매핑

```
WebSocket /ws
  └── useFleetSocket (useReducer)
        ├── pose       → FleetState.pose        → Header (pose text)
        │                                       → MapCanvas (robot circle + arrow)
        ├── state      → FleetState.state       → Header (state pill + class)
        ├── waypoints  → FleetState.waypoints   → MapCanvas (dashed loop + numbered markers)
        ├── current_wp → FleetState.currentWp   → MapCanvas (current target highlight)
        └── plan       → FleetState.plan        → MapCanvas (blue polyline)
```

`wsStatus` (connecting/connected/disconnected)는 WS 이벤트로 직접 관리하며 `Header`의 연결 배지에 반영된다.

---

## 5. 디자인 / 명세 대비 차이점과 사유

| 항목 | 디자인 문서 명세 | 실제 구현 | 사유 |
|---|---|---|---|
| 레이아웃 | 3-Pane (Header + Nav Sidebar + Main + Context Panel) | Header + Main(캔버스)만 | 현재 index.html에 sidebar/context panel 없음 |
| 인광 궤적 | 30초 페이드 그라데이션 꼬리 | 미구현 | 현재 index.html에 없음 |
| 스테일 데이터 시각화 | 2/5/15초 임계값별 색상·배너 | 미구현 | 현재 index.html에 없음 |
| WS 재연결 백오프 | 지수 백오프 (최대 30초) | 고정 1초 재연결 | 현재 index.html 동작과 동일하게 유지 |
| 폰트 | Geist + Geist Mono + DM Sans | 동일 (Google Fonts CDN) | 디자인 문서 권장 Primary Pairing 그대로 적용 |
| 상태 색 | OKLCH 토큰 | OKLCH CSS Variables | 디자인 토큰 그대로 적용 |
| EMERGENCY 배경 pulse | 1Hz 미세 pulse | CSS animation 적용 | 디자인 문서 8.3 준수 |

---

## 6. 백엔드 영향 (be-engineer 처리 필요)

빌드 출력 경로가 `fleet/frontend/dashboard/` → `fleet/frontend/dist/`로 변경되었다.

`fleet/backend/main.py`의 `DASHBOARD_DIR` 경로를 다음과 같이 변경해야 한다:

```python
# 변경 전
DASHBOARD_DIR = Path(__file__).parent.parent / "frontend" / "dashboard"

# 변경 후
FRONTEND_DIST_DIR = Path(__file__).parent.parent / "frontend" / "dist"
# app.mount("/", StaticFiles(directory=FRONTEND_DIST_DIR, html=True), ...)
```

변수명도 `FRONTEND_DIST_DIR`로 변경하는 것이 의미상 더 명확하다.

---

## 7. Open Questions

| ID | 내용 | 영향 |
|---|---|---|
| OQ-FE-1 | `map_config.js`가 없을 때 빈 맵/플레이스홀더 캔버스를 보여줄지, 현재처럼 에러 메시지만 보여줄지 | UX 결정 필요 |
| OQ-FE-2 | WebSocket 재연결을 고정 1초로 유지할지 지수 백오프(최대 30초)로 업그레이드할지 | `03-api-design.md` Section 7.4는 지수 백오프를 명시하지만 현재 index.html은 고정 1초. 이번 작업 범위에서는 현행 동작 유지. |
| OQ-FE-3 | 인광 궤적 기능 추가 시점 | `pose` 이력을 유지하는 별도 상태 + canvas 렌더 로직 필요. useFleetSocket에 history buffer 추가 예정. |
| OQ-FE-4 | `favicon.svg`가 Vite 기본 파일인데 Sentinel 브랜드 아이콘으로 교체 필요 | 디자인 자산 작업 필요 |
