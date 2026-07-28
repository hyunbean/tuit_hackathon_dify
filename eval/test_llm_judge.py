"""cross_validate의 일치/불일치 판단 로직과 judge()의 api/cli 백엔드를 검증.

실제 Anthropic API도, 실제 `claude` CLI도 호출하지 않는다 — 앞부분은 llm_judge.judge를
monkeypatch로 대체해 cross_validate가 규칙 판정과 judge 판정을 올바르게 비교하는지만
확인하고, 뒷부분은 requests.post / subprocess.run 자체를 monkeypatch해 각 백엔드가
응답을 올바르게 파싱하고 실패를 skip으로 처리하는지 확인한다.

실행: python -m pytest eval/test_llm_judge.py -q
"""
import subprocess

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


# --- backend="cli" (`claude -p` 서브프로세스) ---
# 아래는 실제 claude CLI를 셸아웃하지 않는다 — subprocess.run 자체를 monkeypatch한다.

class _FakeCompletedProcess:
    def __init__(self, stdout="", stderr="", returncode=0):
        self.stdout = stdout
        self.stderr = stderr
        self.returncode = returncode


def test_cli_backend_parses_stdout_json(monkeypatch):
    def fake_run(cmd, capture_output, text, timeout):
        assert cmd[0] == "claude"
        assert cmd[1] == "-p"
        return _FakeCompletedProcess(stdout='{"pass": true, "reason": "ok"}')

    monkeypatch.setattr(subprocess, "run", fake_run)
    result = llm_judge.judge("normalizer", {"inputs": {}}, {}, backend="cli")
    assert result == {"pass": True, "reason": "ok"}


def test_cli_backend_skips_when_claude_not_found(monkeypatch):
    def fake_run(*a, **k):
        raise FileNotFoundError()

    monkeypatch.setattr(subprocess, "run", fake_run)
    result = llm_judge.judge("normalizer", {"inputs": {}}, {}, backend="cli")
    assert result["skipped"] is True


def test_cli_backend_skips_on_nonzero_exit(monkeypatch):
    def fake_run(*a, **k):
        return _FakeCompletedProcess(stdout="", stderr="boom", returncode=1)

    monkeypatch.setattr(subprocess, "run", fake_run)
    result = llm_judge.judge("normalizer", {"inputs": {}}, {}, backend="cli")
    assert result["skipped"] is True
    assert "boom" in result["reason"]


def test_cli_backend_skips_on_unparseable_output(monkeypatch):
    def fake_run(*a, **k):
        return _FakeCompletedProcess(stdout="not json")

    monkeypatch.setattr(subprocess, "run", fake_run)
    result = llm_judge.judge("normalizer", {"inputs": {}}, {}, backend="cli")
    assert result["skipped"] is True


def test_cross_validate_threads_backend_through_to_judge(monkeypatch):
    seen = {}

    def fake_judge(workflow, case, outputs, backend="api"):
        seen["backend"] = backend
        return {"pass": True, "reason": "ok"}

    monkeypatch.setattr(llm_judge, "judge", fake_judge)
    llm_judge.cross_validate("normalizer", {}, {}, rule_pass=True, backend="cli")
    assert seen["backend"] == "cli"


def test_unknown_backend_raises():
    import pytest
    with pytest.raises(ValueError):
        llm_judge.judge("normalizer", {"inputs": {}}, {}, backend="carrier-pigeon")
