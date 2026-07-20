"""BozorCheck 워크플로우 출력 채점 규칙.

각 함수는 (case, outputs) → list[str] (실패 사유 목록, 비어 있으면 통과).
LLM-as-judge 없이 결정론적 규칙만 사용한다 — 핸드오프 문서의
"테스트 통과 기준"(새 가격 생성 금지, 금칙어 0건, JSON 파싱 가능)을 코드로 옮긴 것.
"""
from __future__ import annotations

import json
import re

# 핸드오프 문서 + DSL 프롬프트의 금지 표현 (ko/en/ru)
BANNED_WORDS = [
    "바가지", "사기", "속았다", "사지 마세요", "상인이 잘못",
    "rip-off", "ripoff", "scam", "fraud", "cheating", "bad seller",
    "обман", "мошенничество", "развод", "не покупайте",
]

ALLOWED_PRODUCT_CODES = {
    "TOMATO", "CUCUMBER", "CARROT", "POTATO", "ONION",
    "APPLE", "RICE", "EGGS", "VEGETABLE_OIL", "BEEF", "UNKNOWN",
}
ALLOWED_UNIT_CODES = {"KG", "PCS_10", "LITER", "BUNDLE", "PCS", "UNKNOWN"}
ALLOWED_RISK_LEVELS = {"LOW", "MEDIUM", "HIGH"}


def _texts(outputs: dict, *keys: str) -> str:
    return " ".join(str(outputs.get(k, "")) for k in keys)


def _to_bool(v) -> bool:
    if isinstance(v, bool):
        return v
    return str(v).strip().lower() == "true"


def check_no_banned_words(text: str) -> list[str]:
    low = text.lower()
    return [f"금지 표현 발견: {w!r}" for w in BANNED_WORDS if w.lower() in low]


def check_no_invented_prices(text: str, inputs: dict) -> list[str]:
    """텍스트의 1,000 이상 숫자는 전부 입력값에서 온 것이어야 한다.

    입력 숫자의 파생값(천 단위 축약 "16 ming"/"16천" 등)도 허용한다.
    작은 숫자(표본 수, 신뢰도 %, 날짜)는 검사하지 않는다.
    """
    allowed: set[float] = set()
    for v in inputs.values():
        if isinstance(v, (int, float)):
            allowed.add(float(v))
            allowed.add(float(v) / 1000)  # "22000" -> "22 ming/천/тысяч"
        elif isinstance(v, str) and v.strip().startswith(("[", "{")):
            try:
                for n in re.findall(r"-?\d+\.?\d*", v):
                    allowed.add(float(n))
                    allowed.add(float(n) / 1000)
            except ValueError:
                pass
    failures = []
    for tok in re.findall(r"\d[\d,.]*", text):
        norm = tok.replace(",", "").rstrip(".")
        try:
            num = float(norm)
        except ValueError:
            continue
        if num >= 1000 and num not in allowed:
            failures.append(f"입력에 없는 가격/숫자 생성 의심: {tok}")
    return failures


def score_normalizer(case: dict, outputs: dict) -> list[str]:
    f: list[str] = []
    expect = case.get("expect", {})
    code = outputs.get("standardProductCode")
    if code not in ALLOWED_PRODUCT_CODES:
        f.append(f"허용되지 않는 productCode: {code!r}")
    if "standardProductCode" in expect and code != expect["standardProductCode"]:
        f.append(f"productCode 불일치: 기대 {expect['standardProductCode']} / 실제 {code}")
    if "variant" in expect and outputs.get("variant") != expect["variant"]:
        f.append(f"variant 불일치: 기대 {expect['variant']} / 실제 {outputs.get('variant')}")
    unit = outputs.get("normalizedUnitCode")
    if unit and unit not in ALLOWED_UNIT_CODES:
        f.append(f"허용되지 않는 unitCode: {unit!r}")
    if "normalizedUnitCode" in expect and unit != expect["normalizedUnitCode"]:
        f.append(f"unitCode 불일치: 기대 {expect['normalizedUnitCode']} / 실제 {unit}")
    if expect.get("needsHumanReview") and not _to_bool(outputs.get("needsHumanReview")):
        f.append("needsHumanReview=true 여야 하는데 false")
    try:
        conf = float(outputs.get("matchConfidence", 0))
        if not 0 <= conf <= 1:
            f.append(f"matchConfidence 범위 밖: {conf}")
    except (TypeError, ValueError):
        f.append(f"matchConfidence가 숫자가 아님: {outputs.get('matchConfidence')!r}")
    return f


def score_price_insight(case: dict, outputs: dict) -> list[str]:
    f: list[str] = []
    inputs = case["inputs"]
    text = _texts(outputs, "insightText", "recommendedAction",
                  "optionalBargainPhrase", "marketComparisonInsight")
    if not str(outputs.get("insightText", "")).strip():
        f.append("insightText 비어 있음")
    f += check_no_banned_words(text)
    f += check_no_invented_prices(text, inputs)
    if not _to_bool(outputs.get("usedOnlyBackendPrices", "true")):
        f.append("usedOnlyBackendPrices=false — 백엔드 외 가격 사용 자백")
    if _to_bool(outputs.get("changedBackendVerdict", "false")):
        f.append("changedBackendVerdict=true — 백엔드 판정 변경")
    if _to_bool(outputs.get("containsSellerBlame", "false")):
        f.append("containsSellerBlame=true")
    flags_raw = outputs.get("safetyFlagsJson")
    if flags_raw:
        try:
            json.loads(flags_raw) if isinstance(flags_raw, str) else flags_raw
        except json.JSONDecodeError:
            f.append("safetyFlagsJson JSON 파싱 실패")
    if case.get("expectLowDataNotice"):
        notice = _texts(outputs, "insightText", "confidenceExplanation").lower()
        markers = ["참고용", "부족", "표본", "limited", "reference only", "few",
                   "недостаточно", "мало данных", "kam", "cheklangan"]
        if not any(m in notice for m in markers):
            f.append("LOW DATA 경고 문구 누락")
    if str(inputs.get("includeOptionalPhrase", "")).lower() == "false" \
            and str(outputs.get("optionalBargainPhrase", "")).strip():
        f.append("includeOptionalPhrase=false인데 흥정 문장 생성됨")
    return f


def score_report_inspector(case: dict, outputs: dict) -> list[str]:
    f: list[str] = []
    expect = case.get("expect", {})
    risk = outputs.get("riskLevel")
    if risk and risk not in ALLOWED_RISK_LEVELS:
        f.append(f"허용되지 않는 riskLevel: {risk!r}")
    if "riskLevel" in expect and risk != expect["riskLevel"]:
        f.append(f"riskLevel 불일치: 기대 {expect['riskLevel']} / 실제 {risk}")
    if "statusSuggestion" in expect and outputs.get("statusSuggestion") != expect["statusSuggestion"]:
        f.append(f"statusSuggestion 불일치: 기대 {expect['statusSuggestion']}"
                 f" / 실제 {outputs.get('statusSuggestion')}")
    if outputs.get("statusSuggestion") == "APPROVED":
        f.append("APPROVED 자동 확정 금지 (핸드오프 문서 규칙)")
    if expect.get("needsHumanReview") and not _to_bool(outputs.get("needsHumanReview")):
        f.append("needsHumanReview=true 여야 하는데 false")
    f += check_no_banned_words(_texts(outputs, "reviewNote", "userMessage"))
    for k in ("anomalyReasonsJson", "operatorChecklistJson"):
        raw = outputs.get(k)
        if raw and isinstance(raw, str):
            try:
                json.loads(raw)
            except json.JSONDecodeError:
                f.append(f"{k} JSON 파싱 실패")
    return f


SCORERS = {
    "normalizer": score_normalizer,
    "price_insight": score_price_insight,
    "report_inspector": score_report_inspector,
}
