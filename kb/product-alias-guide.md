# BozorCheck Product Alias Guide

상품명 정규화용 별칭 사전. 표준 코드는 10개 + UNKNOWN.
각 항목: 표준코드 | 우즈베크어(라틴) | 러시아어 | 영어 | 한국어 | 변형(variant) | 기본 단위.

## TOMATO — 토마토
- Uzbek: pomidor, pamidor, pomidorlar
- Russian: помидор, помидоры, томат
- English: tomato, tomatoes
- Korean: 토마토
- Variants: GREENHOUSE (greenhouse pomidor, теплица, 하우스), PINK_GREENHOUSE (pink greenhouse pomidor, розовый тепличный, 핑크 하우스)
- Default unit: KG

## CUCUMBER — 오이
- Uzbek: bodring, bodringlar
- Russian: огурец, огурцы
- English: cucumber, cucumbers
- Korean: 오이
- Default unit: KG

## CARROT — 당근
- Uzbek: sabzi
- Russian: морковь, морковка
- English: carrot, carrots
- Korean: 당근
- Default unit: KG

## POTATO — 감자
- Uzbek: kartoshka
- Russian: картошка, картофель
- English: potato, potatoes
- Korean: 감자
- Default unit: KG

## ONION — 양파
- Uzbek: piyoz
- Russian: лук, репчатый лук
- English: onion, onions
- Korean: 양파
- Default unit: KG

## APPLE — 사과
- Uzbek: olma
- Russian: яблоко, яблоки
- English: apple, apples
- Korean: 사과
- Default unit: KG

## RICE — 쌀
- Uzbek: guruch
- Russian: рис
- English: rice
- Korean: 쌀
- Default unit: KG

## EGGS — 달걀
- Uzbek: tuxum, tuxumlar
- Russian: яйца, яйцо
- English: eggs, egg
- Korean: 달걀, 계란
- Note: "tuxum 10 dona", "яйца 10 шт", "달걀 10개" → unit PCS_10
- Default unit: PCS_10

## VEGETABLE_OIL — 식용유
- Uzbek: o'simlik yog'i, osimlik yogi, yog'
- Russian: растительное масло, подсолнечное масло
- English: vegetable oil, sunflower oil, cottonseed oil
- Korean: 식용유
- Default unit: LITER

## BEEF — 소고기
- Uzbek: mol go'shti, mol goshti, go'sht (goat/lamb 아님이 명확할 때만)
- Russian: говядина
- English: beef
- Korean: 소고기, 쇠고기
- Default unit: KG

## 단위 표현 매핑
- KG: kg, kilo, kilogramm, кг, килограмм, 킬로, 키로
- PCS_10: 10 dona, 10 ta, 10 шт, 10개, ten pieces
- LITER: litr, l, литр, л, 리터
- BUNDLE: bog', bir bog', пучок, 한 단, bunch
- PCS: dona, ta, шт, штука, 개, piece

## 매핑 실패 규칙
- 위 10개 표준코드에 매핑할 수 없는 상품(빵, 유제품, 말린 과일, 향신료 등)은
  standardProductCode = UNKNOWN, needsHumanReview = true.
- 철자 변형/오타는 편집거리와 어근으로 추정하되, 확신이 낮으면(0.65 미만) UNKNOWN 처리.
- 별칭이 두 상품에 걸치면(예: go'sht 단독 = 고기 전반) UNKNOWN + 사람 검토.
