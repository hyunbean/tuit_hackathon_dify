"""[사후측정 2026-07-28] 진짜 holdout 재측정 러너.

배경(C14/X3 이슈): eval/golden/*.jsonl의 60케이스는 실패 3건(N08/N18/N40)을
진단·패치하는 과정과 그 이후 "60/60 100%" 재확인 측정 모두에 이미 노출됐다 —
같은 골든셋으로 튜닝하고 같은 골든셋으로 재측정한 것이므로, README의 "100%"는
낙관적으로 편향된 수치다.

이 스크립트는 그 문제를 고치기 위한 것이 아니라(과거를 바꿀 수 없다), 정직하게
새 holdout을 만들어 지금 다시 잰다:
  - N08/N18/N40은 README에 실명으로 등장하는, 확실히 튜닝에 쓰인 케이스라서 완전히 제외.
  - 나머지 57케이스(정규화 37 + 가격설명 10 + 제보검수 10)에서 시드 고정 랜덤 샘플링으로
    새 holdout 15건(정규화10/가격설명3/제보검수2, 비율 유지)을 뽑았다.
    샘플링 코드와 시드(20260728)는 이 커밋 히스토리에 남아 있어 재현 가능하다.

**정직하게 남겨두는 것**: 이건 "원래 튜닝에 안 쓰인 걸 사후에 증명 가능한" 완벽한
holdout이 아니다 — N08/N18/N40을 뺀 나머지 57건도 최종 "60/60 재확인" 라운드에
같이 실행됐다는 사실 자체는 부정할 수 없다(그때는 개별 케이스 단위로 프롬프트를
더 건드리지 않았을 뿐). 다만 이름이 명시적으로 남아 프롬프트 수정의 직접 대상이었던
3건만이라도 확실히 빼고, 새로 무작위로 뽑아 지금 시점에 다시 재는 것이 "역사를
검증할 수 없으니 완벽히 분리됐다고 거짓 주장"하는 것보다는 정직하다.

사용법:
    python -m eval.run_holdout                 # 실제 Dify 호출 (DIFY_*_API_KEY 필요)
    python -m eval.run_holdout --mock           # 하네스 자체 검증용

결과: eval/results/holdout_<workflow>.json
"""
from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path

try:
    from eval.scoring import SCORERS
    from eval import mock_llm
    from eval.run_eval import call_dify
except ImportError:
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
    from eval.scoring import SCORERS
    from eval import mock_llm
    from eval.run_eval import call_dify

EVAL_DIR = Path(__file__).resolve().parent
HOLDOUT_DIR = EVAL_DIR / "golden" / "holdout_2026-07-28"
EXCLUDED_FROM_HOLDOUT_POOL = {"N08", "N18", "N40"}  # named in README as tuning-diagnosed cases


def load_holdout_cases(workflow: str) -> list[dict]:
    path = HOLDOUT_DIR / f"{workflow}.jsonl"
    with open(path, encoding="utf-8") as f:
        return [json.loads(line) for line in f if line.strip()]


def run(workflow: str, mock: bool) -> dict:
    cases = load_holdout_cases(workflow)
    scorer = SCORERS[workflow]
    results, passed = [], 0
    for case in cases:
        t0 = time.time()
        try:
            outputs = (mock_llm.run(workflow, case["inputs"]) if mock
                       else call_dify(workflow, case["inputs"]))
            failures = scorer(case, outputs)
        except Exception as e:
            outputs, failures = {}, [f"호출 오류: {e}"]
        ok = not failures
        passed += ok
        results.append({
            "id": case["id"], "pass": ok, "failures": failures,
            "latency_s": round(time.time() - t0, 2),
            "note": case.get("note", ""), "outputs": outputs,
        })
        print(f"  [{'PASS' if ok else 'FAIL'}] {case['id']} {case.get('note', '')}")
        for msg in results[-1]["failures"]:
            print(f"         - {msg}")
    summary = {
        "workflow": workflow, "mock": mock, "holdout_label": "new holdout, not from original tuning process",
        "excluded_from_pool": sorted(EXCLUDED_FROM_HOLDOUT_POOL),
        "total": len(cases), "passed": passed,
        "accuracy": round(passed / len(cases), 3) if cases else None,
        "results": results,
    }
    out = EVAL_DIR / "results" / f"holdout_{workflow}{'_mock' if mock else ''}.json"
    out.parent.mkdir(exist_ok=True)
    out.write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
    return summary


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--mock", action="store_true")
    args = p.parse_args()

    summaries = [run(wf, args.mock) for wf in SCORERS]
    print("\n=== holdout 요약 (2026-07-28) ===")
    total_passed = sum(s["passed"] for s in summaries)
    total_cases = sum(s["total"] for s in summaries)
    for s in summaries:
        print(f"  {s['workflow']:<18} {s['passed']}/{s['total']}  ({s['accuracy']:.0%})")
    print(f"  {'합계':<18} {total_passed}/{total_cases}  ({total_passed/total_cases:.0%})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
