# 프롬프트 변경 이력 (Prompt Changelog)

이 문서는 세 Dify DSL 파일(`BozorCheck_Product_Normalizer_v1.yml`,
`BozorCheck_Price_Insight_v1.yml`, `BozorCheck_Report_Inspector_v1.yml`)에 실제로
남아 있는 git 커밋 이력만 근거로 재구성한 프롬프트 변경 이력입니다. 추정이나 커밋에
없는 내용은 포함하지 않았습니다 — `git log --follow`/`git show`로 확인한 실제 diff와
커밋 메시지만 사용했습니다.

세 파일 모두 지금까지 커밋 이력이 짧습니다(각 3~4건). 히스토리가 두껍지 않은 만큼,
아래 표는 사실상 각 파일의 전체 변경 이력입니다.

## Product Normalizer (`BozorCheck_Product_Normalizer_v1.yml`)

| 날짜 | 커밋 | 변경 내용 | 이유 |
|---|---|---|---|
| 2026-07-10 | `43bd48a` | 최초 커밋 — 워크플로우 및 LLM 프롬프트 전체 신규 작성 | 커밋 메시지: "Three agent workflow DSL files owned by the Dify track of the KMU x TUIT global hackathon team project" — 해커톤 산출물 최초 등록 |
| 2026-07-11 | `09c5577` | 전처리 코드 노드가 정리한 단위(unit) 텍스트를 LLM 프롬프트 입력으로 전달하도록 7줄 추가 | 커밋 메시지: "Product Normalizer: pass cleaned unit text to the LLM prompt" — 이 커밋은 Price Insight/Report Inspector의 `{{{#` → `{{#` 템플릿 변수 오타 수정도 포함하지만, Product Normalizer 파일 자체의 diff는 단위 텍스트 전달 관련 부분만 해당 |
| 2026-07-22 | `5ceba02` | 시스템 프롬프트에 `bodring`(→CUCUMBER), `olma`(→APPLE, `sotib olmang`과의 동형이의어 명시적 해소 포함), `bog'`/`bir bog'`(→단위 BUNDLE) 규칙 3줄 추가 | 커밋 메시지 및 README §"normalizer 실패 3건 진단": 골든셋 60케이스 중 우즈베크어 입력 3건(N08/N18/N40)이 실패해 원인 진단(검색 슬롯 경쟁 확인, `top_k` 증가는 반증되어 원복) 끝에 프롬프트에 직접 규칙을 추가하는 국소 패치로 해결(92%→98%, 이후 동형이의어 수정으로 →100%) |

## Price Insight Explainer (`BozorCheck_Price_Insight_v1.yml`)

| 날짜 | 커밋 | 변경 내용 | 이유 |
|---|---|---|---|
| 2026-07-10 | `43bd48a` | 최초 커밋 — 워크플로우 및 LLM 프롬프트 전체 신규 작성 | 위와 동일 |
| 2026-07-11 | `09c5577` | 잘못된 템플릿 변수 표기(`{{{#` → `{{#`) 수정, LLM에게 요청 locale로 사용자 문구를 쓰도록 지시하는 규칙 추가, `containsSellerBlame`을 실제 금칙어 감지 로직에 연결(기존 하드코딩 `false` 대체), `fairMid` 셀렉터 타입 수정(string→number), 미사용 코드 노드 입력 제거 | 커밋 메시지: "Fix malformed template variables... Price Insight: wire containsSellerBlame to actual forbidden-word detection instead of hardcoded false; fix fairMid selector type... Instruct LLMs to write user-facing text in the request locale" |

이 이후 이 파일에 대한 추가 커밋은 git 이력에 없습니다 — 2026-07-11 이후 프롬프트
변경은 **커밋 이력에서 확인되지 않습니다.**

## Report Inspector (`BozorCheck_Report_Inspector_v1.yml`)

| 날짜 | 커밋 | 변경 내용 | 이유 |
|---|---|---|---|
| 2026-07-10 | `43bd48a` | 최초 커밋 — 워크플로우 및 LLM 프롬프트 전체 신규 작성 | 위와 동일 |
| 2026-07-11 | `09c5577` | 잘못된 템플릿 변수 표기(`{{{#` → `{{#`) 수정, reject-candidate 분기의 출력 타입 수정(`anomalyReasonsJson` string, `needsHumanReview` boolean), phantom `result` 출력 제거, 복사된 End 노드 제목 정정, `matchConfidence` 누락 시 보수적 기본값(1→0)으로 변경, 러시아어 금칙어 감지/치환 추가 | 커밋 메시지 그대로 — DSL 버그 수정 및 안전 개선 |
| 2026-07-21 | `c9c56ea` | **그래프 구조 변경, 프롬프트 텍스트 자체는 변경 없음**: 정상 경로와 조기-REJECT 경로를 Variable Aggregator 노드로 병합해 End 노드를 하나로 통일(diff 확인: `targetType: end` → `targetType: variable-aggregator`, 새 노드/엣지 추가), `needsHumanReview` 타입을 boolean→string으로 변경 | 커밋 메시지: "Report Inspector DSL: 최신 Dify의 출력 변수 고유 규칙 대응" — 최신 Dify 버전이 End 노드의 출력 변수명 중복을 허용하지 않아 발생한 import 오류를 구조 변경으로 해결한 것이며, LLM 프롬프트 본문 수정은 diff에 없음 |

## 커밋 메시지에서 근거가 불충분한 부분

- `09c5577`의 "Instruct LLMs to write user-facing text in the request locale"가 세
  워크플로우 프롬프트 중 정확히 어느 줄에 해당하는지는 diff 확인으로 특정했으나, 왜
  이 시점에 이 요구사항이 추가됐는지(예: 실제 다국어 응답 오류를 겪었는지)는 커밋
  메시지에서 근거 확인 불가 — 문맥상 안전/품질 개선 묶음 커밋의 일부로 추정될 뿐입니다.
- 세 파일 모두 최초 커밋(`43bd48a`) 시점 프롬프트의 최초 설계 근거(왜 이런 문구를
  택했는지)는 커밋 메시지에 없고, 파일 자체의 diff(신규 추가)로만 확인 가능합니다.

## 히스토리가 얕은 이유

이 저장소는 2026-07-10에 해커톤 산출물로 처음 커밋됐고, 이후 약 2주간(~2026-07-22)
버그 수정과 평가 기반 프롬프트 패치가 이어진 뒤로는 DSL 파일 자체에 대한 추가 커밋이
없습니다. 즉 프롬프트 변경 이력은 총 3~4건으로 짧으며, 이 문서는 그 전체를 담고 있습니다.
