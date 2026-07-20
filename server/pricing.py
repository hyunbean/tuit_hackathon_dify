"""결정론적 가격 판정 — 핸드오프 문서의 "가격 계산은 백엔드" 원칙 구현.

fairLow/Mid/High는 시드 관측치의 25/50/75 분위수.
verdict는 백엔드가 결정하며 LLM은 절대 바꾸지 못한다(source of truth).
"""
from __future__ import annotations

import statistics
from dataclasses import dataclass

from server.seed import OBSERVATIONS, PRODUCTS, MARKETS


@dataclass
class PriceCheck:
    productCode: str
    productName: str
    marketCode: str
    marketName: str
    quotedPrice: float
    unitCode: str
    fairLow: int
    fairMid: int
    fairHigh: int
    verdict: str
    recommendedTargetPrice: int
    confidenceScore: float
    sampleCount: int
    sourceBreakdown: dict


def _quantiles(values: list[float]) -> tuple[int, int, int]:
    if len(values) == 1:
        v = values[0]
        return int(v * 0.95), int(v), int(v * 1.05)
    q = statistics.quantiles(values, n=4)
    return int(q[0]), int(statistics.median(values)), int(q[2])


def check_price(product_code: str, market_code: str,
                quoted_price: float, unit_code: str) -> PriceCheck:
    if product_code not in PRODUCTS:
        raise KeyError(f"unknown product: {product_code}")
    if market_code not in MARKETS:
        raise KeyError(f"unknown market: {market_code}")
    obs = [o for o in OBSERVATIONS
           if o["productCode"] == product_code and o["marketCode"] == market_code]
    if not obs:
        raise LookupError(f"no observations for {product_code}@{market_code}")

    prices = [o["pricePerUnit"] for o in obs]
    low, mid, high = _quantiles(prices)
    if quoted_price < low:
        verdict = "CHEAP"
    elif quoted_price <= high:
        verdict = "FAIR"
    elif quoted_price <= high * 1.15:
        verdict = "EXPENSIVE"
    else:
        verdict = "VERY_EXPENSIVE"

    n = len(prices)
    confidence = round(min(0.95, 0.3 + 0.05 * n), 2)
    breakdown: dict[str, int] = {}
    for o in obs:
        breakdown[o["source"]] = breakdown.get(o["source"], 0) + 1

    return PriceCheck(
        productCode=product_code, productName=PRODUCTS[product_code]["name"],
        marketCode=market_code, marketName=MARKETS[market_code],
        quotedPrice=quoted_price, unitCode=unit_code,
        fairLow=low, fairMid=mid, fairHigh=high, verdict=verdict,
        recommendedTargetPrice=mid, confidenceScore=confidence,
        sampleCount=n, sourceBreakdown=breakdown,
    )
