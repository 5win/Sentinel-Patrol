# Sentinel-Patrol — Claude 작업 지침

순찰 로봇 관제 및 플릿 관리 시스템. 프론트/백엔드는 `fleet/` 하위에 구현한다.

## 서브에이전트 파이프라인

사용자 요청이 아래 범주에 해당하면 **반드시 해당 서브에이전트를 호출**해 그 지침을 따르게 한다. 에이전트 정의는 `.claude/agents/` 아래에 있으며 각 에이전트는 지정된 문서를 산출한다.

```
pm              ──(fleet/docs/01-prd.md)──────────▶  ui-ux-designer  ──(fleet/docs/02-ui-ux-design.md)──┐
                                                                                                        ├──▶  fe-engineer  ──▶  fleet/frontend/**
                                                     api-designer    ──(fleet/docs/03-api-design.md)────┤                   └──▶  fleet/docs/05-frontend-notes.md
                                                                                                        └──▶  be-engineer  ──▶  fleet/backend/**
                                                                                                                            └──▶  fleet/docs/04-backend-notes.md
```

## 라우팅 규칙

- **PRD 작성/수정, 제품 요구사항, 문제 정의, 범위·기능 요구사항 갱신** → `pm` (절대 메인 스레드에서 직접 `fleet/docs/01-prd.md`를 쓰거나 고치지 말 것)
- **UI/UX 디자인, 화면 구성, 디자인 토큰, 사용자 플로우** → `ui-ux-designer`
- **REST/WebSocket API 계약, 스키마, 에러 모델** → `api-designer`
- **`fleet/backend/` 구현·리팩토링(Python/FastAPI/ROS2)** → `be-engineer`
- **`fleet/frontend/` 구현·리팩토링(React) — 모든 UI 작업** → `fe-engineer`

## 작업 원칙

- 하류 에이전트는 상류 에이전트의 산출 문서를 유일한 기준으로 삼는다. 문서 외의 임의 결정 금지.
- 산출 문서(`fleet/docs/0X-*.md`)가 없거나 오래되었으면 먼저 상류 에이전트부터 호출해 최신화한다.
- 각 에이전트는 모호함을 자체 문서의 `Open Questions`로 되돌린다. 사용자가 해소할 때까지 하류는 대기한다.
- UI 구현 시 fe-engineer는 Claude Code의 `frontend-design` 스킬을 반드시 사용한다.
