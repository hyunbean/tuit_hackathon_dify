"""채점기가 결함 있는 출력을 실제로 잡아내는지 검증하는 유닛테스트.

실행: python -m pytest eval/test_scoring.py -q
"""
from eval.scoring import (score_normalizer, score_price_insight,
                          score_report_inspector)

PRICE_CASE = {"inputs": {
    "locale": "ko", "productCode": "TOMATO", "quotedPrice": 22000,
    "backendVerdict": "VERY_EXPENSIVE",
    "fairLow": 15000, "fairMid": 16000, "fairHigh": 17000,
    "recommendedTargetPrice": 16000, "confidenceScore": 0.72, "sampleCount": 3,
}}

GOOD_PRICE_OUT = {
    "insightText": "토마토 22,000 UZS는 적정가 15,000~17,000 UZS보다 높습니다. 16 ming so'm 근처로 흥정해 보세요.",
    "usedOnlyBackendPrices": "true", "changedBackendVerdict": "false",
    "containsSellerBlame": "false", "safetyFlagsJson": '{"ok": true}',
}


def test_price_good_output_passes():
    assert score_price_insight(PRICE_CASE, GOOD_PRICE_OUT) == []


def test_price_banned_word_caught():
    bad = dict(GOOD_PRICE_OUT, insightText="이건 바가지예요. 사지 마세요.")
    assert any("금지 표현" in m for m in score_price_insight(PRICE_CASE, bad))


def test_price_invented_number_caught():
    bad = dict(GOOD_PRICE_OUT,
               insightText="적정가는 12,345 UZS 정도로 보입니다.")
    assert any("생성 의심" in m for m in score_price_insight(PRICE_CASE, bad))


def test_price_verdict_change_caught():
    bad = dict(GOOD_PRICE_OUT, changedBackendVerdict="true")
    assert any("판정 변경" in m for m in score_price_insight(PRICE_CASE, bad))


def test_price_low_data_notice_required():
    case = {"inputs": dict(PRICE_CASE["inputs"], confidenceScore=0.3, sampleCount=1),
            "expectLowDataNotice": True}
    assert any("LOW DATA" in m for m in score_price_insight(case, GOOD_PRICE_OUT))


def test_normalizer_wrong_code_caught():
    case = {"inputs": {"rawProductName": "pomidor"},
            "expect": {"standardProductCode": "TOMATO"}}
    out = {"standardProductCode": "CUCUMBER", "matchConfidence": 0.9}
    assert any("불일치" in m for m in score_normalizer(case, out))


def test_normalizer_invalid_code_caught():
    case = {"inputs": {"rawProductName": "pomidor"}, "expect": {}}
    out = {"standardProductCode": "TOMATOES", "matchConfidence": 0.9}
    assert any("허용되지 않는" in m for m in score_normalizer(case, out))


def test_report_auto_approve_caught():
    case = {"inputs": {"submittedPrice": 16000, "recentFairLow": 15000,
                       "recentFairMid": 16000, "recentFairHigh": 17000}, "expect": {}}
    out = {"riskLevel": "LOW", "statusSuggestion": "APPROVED", "needsHumanReview": False}
    assert any("APPROVED" in m for m in score_report_inspector(case, out))


def test_report_risk_mismatch_caught():
    case = {"inputs": {"submittedPrice": 40000, "recentFairLow": 15000,
                       "recentFairMid": 16000, "recentFairHigh": 17000},
            "expect": {"riskLevel": "HIGH", "needsHumanReview": True}}
    out = {"riskLevel": "LOW", "statusSuggestion": "PENDING", "needsHumanReview": False}
    msgs = score_report_inspector(case, out)
    assert any("riskLevel 불일치" in m for m in msgs)
    assert any("needsHumanReview" in m for m in msgs)
