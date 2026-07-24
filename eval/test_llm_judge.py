"""cross_validate의 일치/불일치 판단 로직을 검증.

실제 Anthropic API를 호출하지 않는다 — llm_judge.judge를 monkeypatch로 대체해
cross_validate가 규칙 판정과 judge 판정을 올바르게 비교하는지만 확인한다.

실행: python -m pytest eval/test_llm_judge.py -q
"""
from eval import llm_judge


def test_agree_when_both_pass(monkeypatch):
    monkeypatch.setattr(llm_judge, "judge",
                         lambda *a, **k: {"pass": True, "reason": "ok"})
    result = llm_judge.cross_validate("price_insight", {}, {}, rule_pass=True)
    assert result["agree"] is True
    assert result["judge_pass"] is True


def test_disagree_when_rule_passes_but_judge_fails(monkeypatch):
    monkeypatch.setattr(llm_judge, "judge",
                         lambda *a, **k: {"pass": False, "reason": "숫자 생성 의심"})
    result = llm_judge.cross_validate("price_insight", {}, {}, rule_pass=True)
    assert result["agree"] is False
    assert result["judge_reason"] == "숫자 생성 의심"


def test_skipped_when_no_api_key(monkeypatch):
    monkeypatch.setattr(llm_judge, "judge",
                         lambda *a, **k: {"skipped": True, "reason": "ANTHROPIC_API_KEY 없음"})
    result = llm_judge.cross_validate("normalizer", {}, {}, rule_pass=True)
    assert result["agree"] is None
    assert result["judge_pass"] is None


def test_rule_verdict_unaffected_by_judge(monkeypatch):
    """cross_validate는 최종 pass/fail을 뒤집지 않는다 — agree 플래그만 남긴다."""
    monkeypatch.setattr(llm_judge, "judge",
                         lambda *a, **k: {"pass": True, "reason": "judge는 통과라 봄"})
    result = llm_judge.cross_validate("report_inspector", {}, {}, rule_pass=False)
    assert result["agree"] is False
    assert "judge_pass" in result and "agree" in result
    assert "pass" not in result  # 최종 판정 필드를 새로 만들지 않음 — run_eval의 rule_pass가 그대로 pass
