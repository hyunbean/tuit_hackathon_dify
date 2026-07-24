"""LLM-judge 이중 채점 — 규칙 기반 스코어러와 독립적으로 출력을 평가해 불일치를 잡아낸다.

Kaggle 카드소비 프로젝트에서 쓴 "외부 AI 2개 교차검증(합의는 채택, 불일치는 의심,
최종 판정은 실측)" 패턴을 이 하네스에도 적용한 것 — 규칙 채점기(eval/scoring.py) 자체가
가질 수 있는 편향(골든셋 기대값 오류, 놓친 규칙)을 잡기 위한 두 번째 독립 채점 축이다.

최종 pass/fail 판정은 여전히 규칙 기반 스코어러(SCORERS)가 낸다 — judge는 사람이
재검토할 불일치 케이스를 찾아내는 용도로만 쓴다. 완전성(기능 누락) 체크가 아니라
정확성(출력이 맞는가) 판정의 신뢰도를 검증하는 것이라, "골든셋 여러 개 만들어 COUNT로
대조"하는 완전성 체크와는 다른 축이다.
"""
from __future__ import annotations

import json
import os

ANTHROPIC_API_URL = "https://api.anthropic.com/v1/messages"
MODEL = os.environ.get("EVAL_JUDGE_MODEL", "claude-sonnet-5")

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


def judge(workflow: str, case: dict, outputs: dict) -> dict:
    """규칙 채점기와 독립적으로 이 출력을 평가한다.

    ANTHROPIC_API_KEY가 없으면 스킵을 알린다(회귀 하네스 자체는 judge 없이도 돈다 —
    judge는 opt-in 보강 채점 축이지 필수 의존성이 아니다).
    """
    key = os.environ.get("ANTHROPIC_API_KEY")
    if not key:
        return {"skipped": True, "reason": "ANTHROPIC_API_KEY 없음"}

    import requests

    prompt = JUDGE_PROMPT.format(
        workflow=workflow,
        note=case.get("note", ""),
        inputs=json.dumps(case.get("inputs", {}), ensure_ascii=False),
        outputs=json.dumps(outputs, ensure_ascii=False),
    )
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
        text = res.json()["content"][0]["text"].strip()
    except Exception as e:  # 호출 실패는 판정 불가로 기록 — 규칙 채점 결과에는 영향 없음
        return {"skipped": True, "reason": f"judge 호출 오류: {e}"}

    try:
        parsed = json.loads(text)
    except json.JSONDecodeError:
        return {"skipped": True, "reason": f"judge 응답 파싱 실패: {text[:200]}"}
    return {"pass": bool(parsed.get("pass")), "reason": parsed.get("reason", "")}


def cross_validate(workflow: str, case: dict, outputs: dict, rule_pass: bool) -> dict:
    """규칙 채점 결과와 judge 결과를 비교한다.

    최종 판정(pass/fail)은 항상 규칙 채점기 기준으로 유지한다 — judge 결과로 결과를
    뒤집지 않는다. agree=False인 케이스만 사람이 재검토하도록 표시하는 용도.
    """
    result = judge(workflow, case, outputs)
    if result.get("skipped"):
        return {"judge_pass": None, "agree": None, "judge_reason": result["reason"]}
    judge_pass = result["pass"]
    return {
        "judge_pass": judge_pass,
        "agree": judge_pass == rule_pass,
        "judge_reason": result.get("reason", ""),
    }
