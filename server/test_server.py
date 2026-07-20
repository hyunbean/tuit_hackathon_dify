"""백엔드 유닛/통합 테스트.

실행: python -m pytest server/test_server.py -q
Dify 키 없이도 전부 통과해야 한다 (AI unavailable 폴백 경로 검증 포함).
"""
from fastapi.testclient import TestClient

from server.app import app
from server.pricing import check_price

client = TestClient(app)


def test_verdict_boundaries():
    pc = check_price("TOMATO", "TASHKENT_CHORSU", 100, "KG")
    assert pc.verdict == "CHEAP"
    fair = check_price("TOMATO", "TASHKENT_CHORSU", pc.fairMid, "KG")
    assert fair.verdict == "FAIR"
    exp = check_price("TOMATO", "TASHKENT_CHORSU", pc.fairHigh * 1.1, "KG")
    assert exp.verdict == "EXPENSIVE"
    very = check_price("TOMATO", "TASHKENT_CHORSU", pc.fairHigh * 3, "KG")
    assert very.verdict == "VERY_EXPENSIVE"


def test_fair_range_ordering():
    pc = check_price("RICE", "TASHKENT_CHORSU", 12000, "KG")
    assert pc.fairLow <= pc.fairMid <= pc.fairHigh
    assert pc.recommendedTargetPrice == pc.fairMid
    assert pc.sampleCount > 0 and 0 < pc.confidenceScore <= 0.95


def test_market_difference():
    chorsu = check_price("TOMATO", "TASHKENT_CHORSU", 16000, "KG")
    oloy = check_price("TOMATO", "TASHKENT_OLOY", 16000, "KG")
    assert oloy.fairMid > chorsu.fairMid  # Oloy 시드는 8% 높게


def test_catalog_endpoints():
    assert len(client.get("/api/v1/products").json()) == 10
    assert len(client.get("/api/v1/markets").json()) == 2


def test_price_check_endpoint():
    res = client.post("/api/v1/price-check", json={
        "productCode": "TOMATO", "marketCode": "TASHKENT_CHORSU",
        "quotedPrice": 22000, "unitCode": "KG"})
    assert res.status_code == 200
    assert res.json()["verdict"] == "VERY_EXPENSIVE"


def test_unknown_product_404():
    res = client.post("/api/v1/price-check", json={
        "productCode": "BREAD", "marketCode": "TASHKENT_CHORSU", "quotedPrice": 1000})
    assert res.status_code == 404


def test_price_coach_fallback_without_key(monkeypatch):
    monkeypatch.delenv("DIFY_PRICE_INSIGHT_API_KEY", raising=False)
    res = client.post("/api/v1/agent/price-coach", json={
        "productCode": "TOMATO", "marketCode": "TASHKENT_CHORSU",
        "quotedPrice": 22000})
    assert res.status_code == 200
    body = res.json()
    assert body["priceCheck"]["verdict"] == "VERY_EXPENSIVE"  # 판정은 항상 유효
    assert body["aiCoach"]["status"] == "unavailable"          # AI 카드만 꺼짐


def test_demo_page_served():
    res = client.get("/")
    assert res.status_code == 200
    assert "BozorCheck" in res.text
