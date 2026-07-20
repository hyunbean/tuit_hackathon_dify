"""BozorCheck Dify 워크플로우 회귀 평가 러너.

사용법:
    python -m eval.run_eval --workflow all --mock          # API 없이 하네스 검증
    python -m eval.run_eval --workflow normalizer          # 실제 Dify 호출
    python -m eval.run_eval --workflow price_insight report_inspector

실제 호출에 필요한 환경변수:
    DIFY_BASE_URL                  (기본 https://api.dify.ai/v1)
    DIFY_NORMALIZER_API_KEY        Product Normalizer 워크플로우 API 키
    DIFY_PRICE_INSIGHT_API_KEY     Price Insight Explainer 워크플로우 API 키
    DIFY_REPORT_INSPECTOR_API_KEY  Report Inspector 워크플로우 API 키

결과는 콘솔 요약 + eval/results/<workflow>.json 에 저장된다.
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import time
from pathlib import Path

try:  # 패키지 실행(-m eval.run_eval)과 직접 실행 둘 다 지원
    from eval.scoring import SCORERS
    from eval import mock_llm
except ImportError:
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
    from eval.scoring import SCORERS
    from eval import mock_llm

EVAL_DIR = Path(__file__).resolve().parent
GOLDEN = {
    "normalizer": EVAL_DIR / "golden" / "normalizer.jsonl",
    "price_insight": EVAL_DIR / "golden" / "price_insight.jsonl",
    "report_inspector": EVAL_DIR / "golden" / "report_inspector.jsonl",
}
KEY_ENV = {
    "normalizer": "DIFY_NORMALIZER_API_KEY",
    "price_insight": "DIFY_PRICE_INSIGHT_API_KEY",
    "report_inspector": "DIFY_REPORT_INSPECTOR_API_KEY",
}


def load_cases(workflow: str) -> list[dict]:
    with open(GOLDEN[workflow], encoding="utf-8") as f:
        return [json.loads(line) for line in f if line.strip()]


def call_dify(workflow: str, inputs: dict) -> dict:
    import requests

    base = os.environ.get("DIFY_BASE_URL", "https://api.dify.ai/v1").rstrip("/")
    key = os.environ.get(KEY_ENV[workflow])
    if not key:
        raise SystemExit(
            f"환경변수 {KEY_ENV[workflow]} 가 없습니다. "
            f"Dify 콘솔에서 워크플로우 API 키를 발급해 설정하거나 --mock 으로 실행하세요."
        )
    res = requests.post(
        f"{base}/workflows/run",
        headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json"},
        json={"inputs": inputs, "response_mode": "blocking", "user": "bozorcheck-eval"},
        timeout=60,
    )
    res.raise_for_status()
    body = res.json()
    outputs = (body.get("data") or {}).get("outputs")
    if outputs is None:
        raise RuntimeError(f"outputs 없음 — 응답: {json.dumps(body, ensure_ascii=False)[:300]}")
    return outputs


def run(workflow: str, mock: bool, max_cases: int | None) -> dict:
    cases = load_cases(workflow)[:max_cases]
    scorer = SCORERS[workflow]
    results, passed = [], 0
    for case in cases:
        t0 = time.time()
        try:
            outputs = (mock_llm.run(workflow, case["inputs"]) if mock
                       else call_dify(workflow, case["inputs"]))
            failures = scorer(case, outputs)
        except Exception as e:  # 호출 실패도 케이스 실패로 기록
            outputs, failures = {}, [f"호출 오류: {e}"]
        ok = not failures
        passed += ok
        results.append({
            "id": case["id"], "pass": ok, "failures": failures,
            "latency_s": round(time.time() - t0, 2),
            "note": case.get("note", ""), "outputs": outputs,
        })
        mark = "PASS" if ok else "FAIL"
        print(f"  [{mark}] {case['id']} {case.get('note', '')}")
        for msg in failures:
            print(f"         - {msg}")
    summary = {
        "workflow": workflow, "mock": mock,
        "total": len(cases), "passed": passed,
        "accuracy": round(passed / len(cases), 3) if cases else None,
        "results": results,
    }
    out = EVAL_DIR / "results" / f"{workflow}{'_mock' if mock else ''}.json"
    out.parent.mkdir(exist_ok=True)
    out.write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
    return summary


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--workflow", nargs="+", default=["all"],
                   choices=[*SCORERS, "all"])
    p.add_argument("--mock", action="store_true",
                   help="Dify 호출 없이 mock 응답으로 하네스 자체를 검증")
    p.add_argument("--max-cases", type=int, default=None)
    args = p.parse_args()

    targets = list(SCORERS) if "all" in args.workflow else args.workflow
    summaries = []
    for wf in targets:
        print(f"\n=== {wf} ({'mock' if args.mock else 'live'}) ===")
        summaries.append(run(wf, args.mock, args.max_cases))

    print("\n=== 요약 ===")
    worst = 1.0
    for s in summaries:
        print(f"  {s['workflow']:<18} {s['passed']}/{s['total']}  ({s['accuracy']:.0%})")
        worst = min(worst, s["accuracy"] or 0)
    return 0 if worst == 1.0 or not args.mock else 1  # mock은 100%가 정상


if __name__ == "__main__":
    raise SystemExit(main())
