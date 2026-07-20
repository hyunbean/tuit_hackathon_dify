"""데모용 시드 데이터 — MVP 10개 품목 × 타슈켄트 시장 2곳.

실서비스라면 DB(현장 조사 + 승인된 사용자 제보)에서 오는 관측치를
데모에서는 고정 시드로 대체한다. 가격 단위: UZS.
"""

PRODUCTS = {
    "TOMATO": {"name": "토마토 (Pomidor)", "unit": "KG"},
    "CUCUMBER": {"name": "오이 (Bodring)", "unit": "KG"},
    "CARROT": {"name": "당근 (Sabzi)", "unit": "KG"},
    "POTATO": {"name": "감자 (Kartoshka)", "unit": "KG"},
    "ONION": {"name": "양파 (Piyoz)", "unit": "KG"},
    "APPLE": {"name": "사과 (Olma)", "unit": "KG"},
    "RICE": {"name": "쌀 (Guruch)", "unit": "KG"},
    "EGGS": {"name": "달걀 10개 (Tuxum)", "unit": "PCS_10"},
    "VEGETABLE_OIL": {"name": "식용유 (O'simlik yog'i)", "unit": "LITER"},
    "BEEF": {"name": "소고기 (Mol go'shti)", "unit": "KG"},
}

MARKETS = {
    "TASHKENT_CHORSU": "Chorsu Bazaar",
    "TASHKENT_OLOY": "Oloy Bazaar",
}

_BASE = {  # (fair 중심가, Chorsu 기준) — Oloy는 약 8% 높게 설정
    "TOMATO": 16000, "CUCUMBER": 9000, "CARROT": 4500, "POTATO": 5500,
    "ONION": 3500, "APPLE": 11000, "RICE": 12000, "EGGS": 13000,
    "VEGETABLE_OIL": 20000, "BEEF": 95000,
}
_SPREAD = [0.92, 0.96, 1.0, 1.0, 1.04, 1.08]  # 6개 관측치 분포
_SOURCES = ["FIELD_SURVEY", "FIELD_SURVEY", "FIELD_SURVEY",
            "USER_REPORT", "USER_REPORT", "FIELD_SURVEY"]

OBSERVATIONS = [
    {
        "productCode": code,
        "marketCode": market,
        "pricePerUnit": round(base * mult * (1.08 if market == "TASHKENT_OLOY" else 1.0)),
        "source": src,
    }
    for code, base in _BASE.items()
    for market in MARKETS
    for mult, src in zip(_SPREAD, _SOURCES)
]
