# BozorCheck Safety Copy Guide

판매자 비난 금지·중립 표현 원칙과 운영자 검토 가이드.

## 금지 표현 (절대 사용 금지)
- 한국어: 바가지, 사기, 속았다, 사지 마세요, 상인이 잘못했습니다
- 영어: rip-off, scam, fraud, cheating, bad seller
- 러시아어: обман, мошенничество, не покупайте, плохой продавец
- 우즈베크어: aldash, firibgarlik, sotib olmang

## 금지 표현 → 중립 대체 표현
- "바가지" → "높은 편"
- "사기" → "가격 차이"
- "사지 마세요" → "품질과 가격을 한 번 더 확인해 보세요"
- "상인이 잘못했습니다" → "품목, 품질, 시장 상황에 따라 가격 차이가 있을 수 있습니다"
- "scam / fraud" → "unusual pricing"
- "не покупайте" → "сравните цены у соседних продавцов"

## 바자르 문화 원칙
- 흥정은 바자르의 일상적인 문화다. 흥정 문장은 항상 정중한 의문형으로 쓴다.
- 가격 차이는 품질·품종·시기·거래 관계에 따라 자연스럽게 생긴다는 전제를 유지한다.
- 관광객(tourist)에게는 흥정 표현을 더 간단하고 발음하기 쉬운 문장으로 제안한다.
- 특정 상인·가게를 지목해 평가하지 않는다.

## 제보 검수(Report Inspector) 운영 원칙
- 자동 승인은 없다. statusSuggestion은 PENDING / REVIEW_REQUIRED / FLAGGED /
  REJECT_CANDIDATE만 사용하고, APPROVED는 시스템이 제안할 수 없다.
- 위험도 기준: 제보가 fairHigh의 2배 초과 또는 fairLow의 절반 미만이면 HIGH(FLAGGED),
  적정 범위 밖이면 MEDIUM(REVIEW_REQUIRED), 범위 안이면 LOW(PENDING).
- 가격이 0 이하이거나 필수 정보가 없으면 REJECT_CANDIDATE.
- 제보자에게 보내는 메시지는 항상 접수 사실만 알린다:
  "제보가 접수되었습니다. 검토 후 시세에 반영됩니다." /
  "Your report was received and will be reviewed before being used."

## 운영자 체크리스트 템플릿
- 품목 변형(variant) 확인 — 하우스/핑크 하우스 등 품종 차이가 가격 차이를 설명하는가
- 제출 단위 확인 — kg/10개/리터/단 착오 여부 (큰 이탈의 흔한 원인)
- 인근 관측치와 비교 — 같은 시장·같은 날짜의 다른 표본과 대조
- 표본 수·신뢰도 확인 — 데이터가 적으면 단독 제보로 시세를 흔들지 않는다
- 정규화 결과 확인 — 상품 매칭 확신도가 낮으면 사람이 재분류
