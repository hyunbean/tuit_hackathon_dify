"""Dify 호출 없이 하네스를 검증하기 위한 결정론적 mock.

실제 워크플로우의 규칙(별칭 매핑, 위험도 규칙, 안전 플래그)을 단순화해 재현한다.
CI에서는 이 mock으로 골든셋·채점기·러너가 맞물려 도는지 확인하고,
실제 품질 측정은 API 키를 넣은 live 실행으로 한다.
"""
from __future__ import annotations

import unicodedata

ALIAS = {
    "pomidor": ("TOMATO", None), "помидор": ("TOMATO", None), "토마토": ("TOMATO", None),
    "tomato": ("TOMATO", None), "pomidorr": ("TOMATO", None), "pamidor": ("TOMATO", None),
    "bodring": ("CUCUMBER", None), "огурец": ("CUCUMBER", None), "오이": ("CUCUMBER", None),
    "sabzi": ("CARROT", None), "морковь": ("CARROT", None), "당근": ("CARROT", None),
    "kartoshka": ("POTATO", None), "картошка": ("POTATO", None), "감자": ("POTATO", None),
    "piyoz": ("ONION", None), "лук": ("ONION", None), "양파": ("ONION", None),
    "olma": ("APPLE", None), "яблоко": ("APPLE", None), "사과": ("APPLE", None),
    "guruch": ("RICE", None), "рис": ("RICE", None), "쌀": ("RICE", None),
    "tuxum": ("EGGS", None), "яйца": ("EGGS", None), "달걀": ("EGGS", None),
    "beef": ("BEEF", None), "говядина": ("BEEF", None), "소고기": ("BEEF", None),
    "mol go'shti": ("BEEF", None),
    "o'simlik yog'i": ("VEGETABLE_OIL", None), "osimlik yogi": ("VEGETABLE_OIL", None),
    "sunflower oil": ("VEGETABLE_OIL", None), "растительное масло": ("VEGETABLE_OIL", None),
    "식용유": ("VEGETABLE_OIL", None),
}
VARIANT_MARKERS = {"pink greenhouse": "PINK_GREENHOUSE", "greenhouse": "GREENHOUSE"}
UNIT_MARKERS = {"10 dona": "PCS_10", "10 шт": "PCS_10", "10개": "PCS_10",
                "litr": "LITER", "литр": "LITER", "리터": "LITER",
                "bog'": "BUNDLE", "단": "BUNDLE", "kg": "KG"}


def _norm(s: str) -> str:
    s = unicodedata.normalize("NFKC", s).lower().strip()
    return s.replace("‘", "'").replace("’", "'")


def _normalizer(inputs: dict) -> dict:
    raw = _norm(inputs.get("rawProductName", ""))
    variant = next((v for m, v in VARIANT_MARKERS.items() if m in raw), None)
    unit = next((u for m, u in UNIT_MARKERS.items() if m in raw), None)
    if unit is None and _norm(inputs.get("unitText", "") or "") == "kg":
        unit = "KG"
    code = None
    for alias, (c, _) in ALIAS.items():
        if alias in raw:
            code = c
            break
    if code is None:
        return {"standardProductCode": "UNKNOWN", "standardProductName": None,
                "variant": None, "normalizedUnitCode": unit or "UNKNOWN",
                "matchConfidence": 0.1, "needsHumanReview": True,
                "reason": "no alias match"}
    return {"standardProductCode": code, "standardProductName": code.title(),
            "variant": variant, "normalizedUnitCode": unit,
            "matchConfidence": 0.95, "needsHumanReview": False, "reason": "alias match"}


_VERDICT_TEXT = {
    "CHEAP": "좋은 가격입니다. 품질만 확인해 보세요.",
    "FAIR": "현재 시세 범위 안에 있습니다.",
    "EXPENSIVE": "조금 높은 편입니다. 중앙값 근처로 흥정해 보세요.",
    "VERY_EXPENSIVE": "상당히 높은 편입니다. 다른 가게와 비교해 보세요.",
}


def _price_insight(inputs: dict) -> dict:
    verdict = inputs.get("backendVerdict", "FAIR")
    low_data = float(inputs.get("confidenceScore", 1)) < 0.5 or int(inputs.get("sampleCount", 99)) < 3
    text = (f"{inputs.get('marketName', '시장')}의 {inputs.get('productName', '상품')} "
            f"{inputs.get('quotedPrice'):,} UZS/{inputs.get('unitCode')} — {_VERDICT_TEXT[verdict]} "
            f"적정가 범위는 {inputs.get('fairLow'):,}~{inputs.get('fairHigh'):,} UZS, "
            f"중앙값은 {inputs.get('fairMid'):,} UZS입니다.")
    if low_data:
        text += " 표본이 적어 참고용으로만 확인해 주세요."
    include = str(inputs.get("includeOptionalPhrase", "")).lower() == "true"
    phrase = ""
    if include and verdict in ("EXPENSIVE", "VERY_EXPENSIVE"):
        target = inputs.get("recommendedTargetPrice") or inputs.get("fairMid")
        phrase = f"Biroz arzonroq bera olasizmi? {int(target / 1000)} ming so'm bo'ladimi?"
    return {"insightText": text,
            "confidenceExplanation": "표본이 적습니다" if low_data else "표본이 충분합니다",
            "sourceSummary": "현장 조사 및 사용자 제보 기준입니다.",
            "marketComparisonInsight": "", "recommendedAction": "",
            "optionalBargainPhrase": phrase,
            "safetyFlagsJson": '{"usedOnlyBackendPrices": true}',
            "usedOnlyBackendPrices": "true", "changedBackendVerdict": "false",
            "containsSellerBlame": "false", "aiStatus": "ok"}


def _report_inspector(inputs: dict) -> dict:
    price = float(inputs.get("submittedPrice", 0))
    low, high = float(inputs["recentFairLow"]), float(inputs["recentFairHigh"])
    low_conf = float(inputs.get("confidenceScore", 1)) < 0.5 or int(inputs.get("sampleCount", 99)) < 3
    weak_match = float(inputs.get("matchConfidence", 1)) < 0.7
    if price <= 0:
        risk, status, review = "HIGH", "REJECT_CANDIDATE", True
    elif price > high * 2 or price < low * 0.5:
        risk, status, review = "HIGH", "FLAGGED", True
    elif low_conf or weak_match:
        risk, status, review = "MEDIUM", "PENDING", True
    else:
        risk, status, review = "LOW", "PENDING", False
    return {"normalizedProductCode": inputs.get("productCode"),
            "riskLevel": risk, "statusSuggestion": status,
            "needsHumanReview": review,
            "anomalyReasonsJson": "[]",
            "reviewNote": "규칙 기반 검토 노트 (mock)",
            "userMessage": "제보가 접수되었습니다. 검토 후 시세에 반영됩니다.",
            "operatorChecklistJson": "[]"}


def run(workflow: str, inputs: dict) -> dict:
    return {"normalizer": _normalizer,
            "price_insight": _price_insight,
            "report_inspector": _report_inspector}[workflow](inputs)
