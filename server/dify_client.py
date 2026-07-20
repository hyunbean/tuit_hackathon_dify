"""Spring→Dify 호출 규칙(핸드오프 문서 8장)의 파이썬 구현.

- API 키는 서버 환경변수에만 존재 (프론트 전달 금지)
- blocking 모드, 타임아웃, 실패 시 AI 카드만 unavailable 처리
"""
from __future__ import annotations

import os
from typing import Any

import httpx

BASE_URL = os.environ.get("DIFY_BASE_URL", "https://api.dify.ai/v1").rstrip("/")
PRICE_INSIGHT_KEY_ENV = "DIFY_PRICE_INSIGHT_API_KEY"
TIMEOUT_S = 30.0


class DifyUnavailable(Exception):
    """키 미설정·타임아웃·파싱 실패 — AI Coach 카드를 끄고 가격 판정만 노출."""


async def run_price_insight(inputs: dict[str, Any]) -> dict[str, Any]:
    key = os.environ.get(PRICE_INSIGHT_KEY_ENV)
    if not key:
        raise DifyUnavailable(f"{PRICE_INSIGHT_KEY_ENV} not set")
    try:
        async with httpx.AsyncClient(timeout=TIMEOUT_S) as client:
            res = await client.post(
                f"{BASE_URL}/workflows/run",
                headers={"Authorization": f"Bearer {key}",
                         "Content-Type": "application/json"},
                json={"inputs": inputs, "response_mode": "blocking",
                      "user": "bozorcheck-demo"},
            )
            res.raise_for_status()
            outputs = (res.json().get("data") or {}).get("outputs")
    except (httpx.HTTPError, ValueError) as e:
        raise DifyUnavailable(str(e)) from e
    if not outputs or not str(outputs.get("insightText", "")).strip():
        raise DifyUnavailable("empty outputs")
    return outputs
