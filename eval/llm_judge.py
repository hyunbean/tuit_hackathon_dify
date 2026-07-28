"""LLM-judge 이중 채점 — 규칙 기반 스코어러와 독립적으로 출력을 평가해 불일치를 잡아낸다.

Kaggle 카드소비 프로젝트에서 쓴 "외부 AI 2개 교차검증(합의는 채택, 불일치는 의심,
최종 판정은 실측)" 패턴을 이 하네스에도 적용한 것 — 규칙 채점기(eval/scoring.py) 자체가
가질 수 있는 편향(골든셋 기대값 오류, 놓친 규칙)을 잡기 위한 두 번째 독립 채점 축이다.

최종 pass/fail 판정은 여전히 규칙 기반 스코어러(SCORERS)가 낸다 — judge는 사람이
재검토할 불일치 케이스를 찾아내는 용도로만 쓴다. 완전성(기능 누락) 체크가 아니라
정확성(출력이 맞는가) 판정의 신뢰도를 검증하는 것이라, "골든셋 여러 개 만들어 COUNT로
대조"하는 완전성 체크와는 다른 축이다.

백엔드 선택 (--backend api|cli, run_eval.py 경유):
- api (기본값, 하위호환): Anthropic API 직접 호출. ANTHROPIC_API_KEY 필요, 종량제 비용 발생.
- cli: `claude -p "<prompt>"`로 셸아웃. Claude Code 구독 한도를 쓰고 API 키가 필요 없다 —
  이 judge 축은 회귀 하네스 필수 경로가 아닌 opt-in 보강 체크라서, 반복 실행 비용을
  API 종량제 대신 이미 있는 구독으로 돌리는 쪽이 이 프로젝트 예산에 더 잘 맞는다.
  기본값을 api로 유지한 건 기존 호출자(테스트, CI에 ANTHROPIC_API_KEY를 이미 등록한
  파이프라인이 있다면)의 동작을 바꾸지 않기 위해서다 — 필요하면 명시적으로 cli를 켠다.
"""
from __future__ import annotations

import json
import os
import subprocess

ANTHROPIC_API_URL = "https://api.anthropic.com/v1/messages"
MODEL = os.environ.get("EVAL_JUDGE_MODEL", "claude-sonnet-5")

# Default backend for judge()/cross_validate() when the caller doesn't pass one explicitly.
# Kept as "api" for backward compat with existing callers/tests that predate --backend;
# run_eval.py's --backend flag (default "api") is the supported way to switch this.
DEFAULT_BACKEND = os.environ.get("EVAL_JUDGE_BACKEND", "api")

JUDGE_PROMPT = """당신은 BozorCheck 워크플로우 출력을 검수하는 독립 심사자입니다.
아래 케이스의 입력과 출력을 보고, 이 출력이 통과할 만한지 판단하세요.

기준:
- 입력에 없는 가격/숫자를 새로 지어내지 않았는가
- 금칙어(바가지·사기 등 상인 비난 표현)가 없는가
- 백엔드 판정을 임의로 바꾸지 않았는가
- (해당되면) 표본 부족 경고 문구가 있는가

워크플로우: {workflow}
케이스 노트: {note}
입력: {inputs}
출력: {outputs}

JSON으로만 답하세요: {{"pass": true 또는 false, "reason": "한 줄 이유"}}
"""


def _build_prompt(workflow: str, case: dict, outputs: dict) -> str:
    return JUDGE_PROMPT.format(
        workflow=workflow,
        note=case.get("note", ""),
        inputs=json.dumps(case.get("inputs", {}), ensure_ascii=False),
        outputs=json.dumps(outputs, ensure_ascii=False),
    )


def _parse_judge_text(text: str) -> dict:
    """공통 파싱 경로 — api/cli 백엔드 모두 같은 방식으로 응답을 해석한다."""
    text = text.strip()
    try:
        parsed = json.loads(text)
    except json.JSONDecodeError:
        return {"skipped": True, "reason": f"judge 응답 파싱 실패: {text[:200]}"}
    return {"pass": bool(parsed.get("pass")), "reason": parsed.get("reason", "")}


def _judge_via_api(prompt: str) -> dict:
    """Anthropic API를 직접 호출 — 종량제 API 비용이 든다.

    ANTHROPIC_API_KEY가 없으면 스킵을 알린다(회귀 하네스 자체는 judge 없이도 돈다 —
    judge는 opt-in 보강 채점 축이지 필수 의존성이 아니다).
    """
    key = os.environ.get("ANTHROPIC_API_KEY")
    if not key:
        return {"skipped": True, "reason": "ANTHROPIC_API_KEY 없음"}

    import requests

    try:
        res = requests.post(
            ANTHROPIC_API_URL,
            headers={
                "x-api-key": key,
                "anthropic-version": "2023-06-01",
                "content-type": "application/json",
            },
            json={
                "model": MODEL,
                "max_tokens": 200,
                "messages": [{"role": "user", "content": prompt}],
            },
            timeout=30,
        )
        res.raise_for_status()
        text = res.json()["content"][0]["text"]
    except Exception as e:  # 호출 실패는 판정 불가로 기록 — 규칙 채점 결과에는 영향 없음
        return {"skipped": True, "reason": f"judge 호출 오류: {e}"}

    return _parse_judge_text(text)


def _judge_via_cli(prompt: str) -> dict:
    """`claude -p` CLI로 셸아웃 — Claude Code 구독을 쓰고, 종량제 API 요금이 붙지 않는다.

    ANTHROPIC_API_KEY가 전혀 필요 없다. `claude` 실행 파일이 PATH에 없거나 호출이
    실패하면(타임아웃 포함) skip으로 기록한다 — api 백엔드와 동일하게 judge 실패가
    규칙 채점 결과에 영향을 주지 않는다.
    """
    try:
        res = subprocess.run(
            ["claude", "-p", prompt],
            capture_output=True,
            text=True,
            timeout=60,
        )
    except FileNotFoundError:
        return {"skipped": True, "reason": "claude CLI를 찾을 수 없음 (PATH 확인 필요)"}
    except subprocess.TimeoutExpired:
        return {"skipped": True, "reason": "claude CLI 호출 타임아웃"}
    except Exception as e:  # 그 외 subprocess 실패
        return {"skipped": True, "reason": f"judge 호출 오류: {e}"}

    if res.returncode != 0:
        return {"skipped": True, "reason": f"claude CLI 비정상 종료(code={res.returncode}): {res.stderr[:200]}"}

    return _parse_judge_text(res.stdout)


_BACKENDS = {"api": _judge_via_api, "cli": _judge_via_cli}


def judge(workflow: str, case: dict, outputs: dict, backend: str = DEFAULT_BACKEND) -> dict:
    """규칙 채점기와 독립적으로 이 출력을 평가한다.

    backend="api" (기본값, 하위호환): Anthropic API 직접 호출, ANTHROPIC_API_KEY 필요, 종량제 비용.
    backend="cli": `claude -p` 서브프로세스 호출, Claude Code 구독 사용, API 키 불필요.
    """
    try:
        backend_fn = _BACKENDS[backend]
    except KeyError:
        raise ValueError(f"알 수 없는 backend: {backend!r} (api 또는 cli)")

    prompt = _build_prompt(workflow, case, outputs)
    return backend_fn(prompt)


def cross_validate(workflow: str, case: dict, outputs: dict, rule_pass: bool,
                    backend: str = DEFAULT_BACKEND) -> dict:
    """규칙 채점 결과와 judge 결과를 비교한다.

    최종 판정(pass/fail)은 항상 규칙 채점기 기준으로 유지한다 — judge 결과로 결과를
    뒤집지 않는다. agree=False인 케이스만 사람이 재검토하도록 표시하는 용도.
    """
    result = judge(workflow, case, outputs, backend=backend)
    if result.get("skipped"):
        return {"judge_pass": None, "agree": None, "judge_reason": result["reason"]}
    judge_pass = result["pass"]
    return {
        "judge_pass": judge_pass,
        "agree": judge_pass == rule_pass,
        "judge_reason": result.get("reason", ""),
    }
