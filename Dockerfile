FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY server/ ./server/

# Hugging Face Spaces는 7860, 그 외 호스트는 PORT 환경변수를 준다
ENV PORT=7860
EXPOSE 7860

# DIFY_PRICE_INSIGHT_API_KEY가 없으면 AI Coach 카드만 unavailable로 표시되고
# 가격 판정(백엔드 source of truth)은 정상 동작한다 — 핸드오프 문서의 실패 처리 규칙
CMD ["sh", "-c", "uvicorn server.app:app --host 0.0.0.0 --port ${PORT}"]
