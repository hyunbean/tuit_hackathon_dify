---
title: BozorCheck AI Demo
emoji: 🍅
colorFrom: red
colorTo: yellow
sdk: docker
app_port: 7860
pinned: false
---

# BozorCheck AI — 레퍼런스 백엔드 데모

우즈베키스탄 재래시장 시세 조회 서비스의 AI 파트 데모입니다.

**설계 원칙:** 가격 계산·공정가 범위·판정은 **백엔드가 단일 진실 원천(source of truth)**이고,
LLM은 그 판정을 사용자 언어로 설명하는 **설명 계층**만 담당합니다.
LLM이 판정을 바꾸면 코드가 감지해 AI 카드를 버립니다.

- `POST /api/v1/price-check` — 시드 관측치 분위수 기반 결정론적 판정 (LLM 미사용)
- `POST /api/v1/agent/price-coach` — 판정 재사용 → Dify 호출 → 응답 검증

`DIFY_PRICE_INSIGHT_API_KEY` 시크릿이 설정되지 않으면 AI Coach 카드만 `unavailable`로
표시되고 가격 판정은 정상 동작합니다 — 이것 자체가 핸드오프 문서에 정의된 실패 처리 규칙입니다.

소스: https://github.com/hyunbean/tuit_hackathon_dify
