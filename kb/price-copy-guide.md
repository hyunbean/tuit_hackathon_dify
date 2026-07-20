# BozorCheck Price Copy Guide

가격 판정 설명 문구 가이드. 백엔드 verdict는 절대 바꾸지 않고, 아래 톤에 맞춰 설명만 생성한다.

## 판정별 권장 문구 (한국어 기준)
- CHEAP → "좋은 가격입니다. 품질만 확인해 보세요." (uiSeverity: success)
- FAIR → "현재 시세 범위 안에 있습니다." (uiSeverity: info)
- EXPENSIVE → "조금 높은 편입니다. 중앙값 근처로 흥정해 보세요." (uiSeverity: warning)
- VERY_EXPENSIVE → "상당히 높은 편입니다. 다른 가게와 비교해 보세요." (uiSeverity: danger)

## 판정별 권장 문구 (영어)
- CHEAP → "This is a good price. Just check the quality."
- FAIR → "This is within the current market range."
- EXPENSIVE → "This is a bit high. Try negotiating near the median price."
- VERY_EXPENSIVE → "This is considerably high. Compare with other stalls."

## 판정별 권장 문구 (러시아어)
- CHEAP → "Это хорошая цена. Просто проверьте качество."
- FAIR → "Цена в пределах текущего рыночного диапазона."
- EXPENSIVE → "Немного дороговато. Попробуйте поторговаться ближе к средней цене."
- VERY_EXPENSIVE → "Цена заметно выше обычной. Сравните с другими продавцами."

## 판정별 권장 문구 (우즈베크어)
- CHEAP → "Bu yaxshi narx. Faqat sifatini tekshiring."
- FAIR → "Narx hozirgi bozor oralig'ida."
- EXPENSIVE → "Biroz qimmatroq. O'rtacha narxga yaqin savdolashib ko'ring."
- VERY_EXPENSIVE → "Narx odatdagidan ancha yuqori. Boshqa do'konlar bilan solishtiring."

## 데이터 부족(LOW DATA) 문구 — confidence < 0.5 또는 표본 < 3이면 필수
- 한국어: "아직 이 시장의 데이터가 충분하지 않습니다. 참고용으로만 확인해 주세요."
- 영어: "Data for this market is still limited. Please use this for reference only."
- 러시아어: "Данных по этому рынку пока недостаточно. Используйте только как ориентир."
- 우즈베크어: "Bu bozor bo'yicha ma'lumotlar hali yetarli emas. Faqat ma'lumot uchun foydalaning."

## 출처 요약 표기 원칙
- 항상 표본 출처를 요약한다. 예: "현장 조사 2건, 사용자 제보 1건 기준입니다." /
  "Based on 2 field surveys and 1 user report."
- FIELD_SURVEY = 현장 조사 / field survey / полевой опрос
- USER_REPORT = 사용자 제보 / user report / сообщение пользователя
- 사용자 제보가 즉시 시세에 반영된 것처럼 표현하지 않는다.

## 숫자 사용 규칙
- 입력으로 받은 가격(fairLow/fairMid/fairHigh/quotedPrice/recommendedTargetPrice) 외의
  새로운 가격 숫자를 만들지 않는다.
- 가격은 천 단위 구분 쉼표로 쓰고 통화(UZS/so'm/숨/сум)를 붙인다.

## 정중한 흥정 문장 예시 (recommendedTargetPrice가 16,000일 때)
- 우즈베크어: "Biroz arzonroq bera olasizmi? 16 ming so'm bo'ladimi?"
- 러시아어: "Можно немного дешевле? За 16 тысяч можно?"
- 한국어: "조금 깎아주실 수 있나요? 16,000숨에 가능할까요?"
- 영어: "Could you make it a bit cheaper? Would 16,000 soum be possible?"
- FAIR/CHEAP 판정에서는 과도한 흥정을 유도하지 않는다 (가벼운 비교 제안까지만).
