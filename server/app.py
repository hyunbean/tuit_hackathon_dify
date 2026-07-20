"""BozorCheck 레퍼런스 백엔드 (FastAPI).

핸드오프 문서의 협업 계약을 그대로 구현한 데모:
- GET  /api/v1/products, /api/v1/markets      시드 카탈로그
- POST /api/v1/price-check                    결정론적 가격 판정 (source of truth)
- POST /api/v1/agent/price-coach              판정 + Dify 설명 계층 (실패 시 AI만 비활성)
- /                                           웹 데모 (가격 판정 카드 + AI Coach 카드)

실행: uvicorn server.app:app --reload  (레포 루트에서)
"""
from __future__ import annotations

from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field

from server import dify_client
from server.pricing import check_price
from server.seed import MARKETS, PRODUCTS

app = FastAPI(title="BozorCheck Reference Backend", version="1.0.0")
STATIC = Path(__file__).resolve().parent / "static"


class PriceQuery(BaseModel):
    productCode: str
    marketCode: str
    quotedPrice: float = Field(gt=0)
    unitCode: str = "KG"
    locale: str = "ko"
    includeBargainPhrase: bool = True


@app.get("/api/v1/products")
def products():
    return [{"code": c, **p} for c, p in PRODUCTS.items()]


@app.get("/api/v1/markets")
def markets():
    return [{"code": c, "name": n} for c, n in MARKETS.items()]


def _price_check_or_404(q: PriceQuery):
    try:
        return check_price(q.productCode, q.marketCode, q.quotedPrice, q.unitCode)
    except (KeyError, LookupError) as e:
        raise HTTPException(status_code=404, detail=str(e)) from e


@app.post("/api/v1/price-check")
def price_check(q: PriceQuery):
    return _price_check_or_404(q).__dict__


@app.post("/api/v1/agent/price-coach")
async def price_coach(q: PriceQuery):
    """입력 검증 → price check 재사용 → Dify 호출 → 응답 검증 → 반환."""
    import json

    pc = _price_check_or_404(q)
    dify_inputs = {
        "locale": q.locale,
        "productCode": pc.productCode, "productName": pc.productName,
        "marketCode": pc.marketCode, "marketName": pc.marketName,
        "quotedPrice": pc.quotedPrice, "unitCode": pc.unitCode,
        "backendVerdict": pc.verdict,
        "fairLow": pc.fairLow, "fairMid": pc.fairMid, "fairHigh": pc.fairHigh,
        "recommendedTargetPrice": pc.recommendedTargetPrice,
        "confidenceScore": pc.confidenceScore, "sampleCount": pc.sampleCount,
        "sourceBreakdownJson": json.dumps(pc.sourceBreakdown, ensure_ascii=False),
        "includeOptionalPhrase": "true" if q.includeBargainPhrase else "false",
    }
    try:
        ai = await dify_client.run_price_insight(dify_inputs)
        # 방어선: LLM이 verdict를 바꿨다고 자백하면 AI 카드를 버린다
        if str(ai.get("changedBackendVerdict", "false")).lower() == "true":
            raise dify_client.DifyUnavailable("verdict change detected")
        coach = {"status": "ok", **{k: ai.get(k) for k in (
            "insightText", "confidenceExplanation", "sourceSummary",
            "marketComparisonInsight", "recommendedAction",
            "optionalBargainPhrase")}}
    except dify_client.DifyUnavailable as e:
        coach = {"status": "unavailable", "reason": str(e)}
    return {"priceCheck": pc.__dict__, "aiCoach": coach}


@app.get("/")
def index():
    return FileResponse(STATIC / "index.html")
