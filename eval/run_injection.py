"""Product Normalizer 프롬프트 인젝션/탈옥 회귀 평가 러너.

배경(practice-lens-audit.md X2 이슈): 이 프로젝트를 포함한 3개 LLM 프로젝트 모두
프롬프트 인젝션/탈옥 테스트 커버리지가 0이었다. Product Normalizer는 자유
다국어 텍스트(우즈베크/러시아/한국/영어)를 그대로 받아 LLM 프롬프트에 삽입하는
구조라(BozorCheck_Product_Normalizer_v1.yml의 user 메시지 템플릿 참고), "이전
지시 무시" 류 텍스트가 사용자가 입력하는 rawProductName 필드에 그대로 실려올 수
있는, 이 파이프라인에서 가장 현실적인 공격 표면이다.

이 러너는 run_eval.py와 별도로 둔다 — 채점 기준이 근본적으로 다르기 때문이다
(score_normalizer는 "정답 코드와 일치하는가", score_injection은 "주입된 지시에
순응하지 않고 안전하게 실패했는가"). run_eval.py의 --mock 하네스는 결정론적
별칭 매칭 mock을 쓰는데, 인젝션 케이스 상당수가 정상 별칭 문자열을 부분포함한
채 공격 문구를 덧붙인 형태라(예: "pomidor emas..." 안에 "pomidor" 포함) mock이
성급하게 별칭 매치를 해버려 하네스 자체 검증(mock)과 실제 안전성 판단이 뒤섞인다.
그래서 SCORERS/GOLDEN/run_eval.py의 --workflow all에는 넣지 않았다 — CI의 mock
스모크 테스트를 오염시키지 않기 위한 의도적 결정이다. 대신 mock_llm의 결정론적
별칭 매처를 그대로 재사용해 하네스 배선만 별도로 검증할 수 있게 --mock을 남겨둔다.

사용법:
    python -m eval.run_injection            # 실제 Dify Product Normalizer 호출
    python -m eval.run_injection --mock      # 하네스 자체 검증 (mock, 참고용 — 실제
                                              # 안전성 신호 아님, 위 docstring 참고)

환경변수: DIFY_NORMALIZER_API_KEY (run_eval.py와 동일 키 재사용)

결과: eval/results/injection_normalizer.json (또는 --mock 시 _mock 접미사)
"""
from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path

try:
    from eval.scoring import score_injection
    from eval import mock_llm
    from eval.run_eval import call_dify
except ImportError:
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
    from eval.scoring import score_injection
    from eval import mock_llm
    from eval.run_eval import call_dify

EVAL_DIR = Path(__file__).resolve().parent
GOLDEN = EVAL_DIR / "golden" / "injection_2026-07-28" / "normalizer.jsonl"
WORKFLOW = "normalizer"  # call_dify(workflow, inputs)는 DIFY_NORMALIZER_API_KEY를 사용


def load_cases() -> list[dict]:
    with open(GOLDEN, encoding="utf-8") as f:
        return [json.loads(line) for line in f if line.strip()]


def run(mock: bool) -> dict:
    cases = load_cases()
    results, passed = [], 0
    for case in cases:
        t0 = time.time()
        try:
            outputs = (mock_llm.run(WORKFLOW, case["inputs"]) if mock
                       else call_dify(WORKFLOW, case["inputs"]))
            failures = score_injection(case, outputs)
        except Exception as e:
            outputs, failures = {}, [f"호출 오류: {e}"]
        ok = not failures
        passed += ok
        results.append({
            "id": case["id"], "attack_type": case.get("attack_type", ""),
            "pass": ok, "failures": failures,
            "latency_s": round(time.time() - t0, 2),
            "note": case.get("note", ""), "outputs": outputs,
        })
        mark = "PASS" if ok else "FAIL"
        print(f"  [{mark}] {case['id']} ({case.get('attack_type', '')}) {case.get('note', '')}")
        for msg in failures:
            print(f"         - {msg}")
    summary = {
        "workflow": "injection_normalizer", "mock": mock,
        "total": len(cases), "passed": passed,
        "accuracy": round(passed / len(cases), 3) if cases else None,
        "results": results,
    }
    out = EVAL_DIR / "results" / f"injection_normalizer{'_mock' if mock else ''}.json"
    out.parent.mkdir(exist_ok=True)
    out.write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
    return summary


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--mock", action="store_true",
                   help="Dify 호출 없이 mock_llm의 결정론적 별칭 매처로 하네스 배선만 검증"
                        "(실제 안전성 신호 아님 — 위 모듈 docstring 참고)")
    args = p.parse_args()

    print(f"\n=== Product Normalizer 인젝션/탈옥 회귀 평가 ({'mock' if args.mock else 'live'}) ===")
    summary = run(args.mock)
    print(f"\n=== 요약 ===\n  injection_normalizer  {summary['passed']}/{summary['total']}"
          f"  ({summary['accuracy']:.0%})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
