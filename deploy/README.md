# 배포 (Render)

`server/`의 레퍼런스 백엔드 + 웹 데모를 무료로 공개 배포하는 절차입니다.

## 왜 Render인가

- 기존 `Dockerfile`을 그대로 감지해서 빌드 — 별도 설정 파일 불필요
- 무료 티어에 카드 등록 불필요, GitHub OAuth로 바로 가입
- 키가 없어도 데모가 성립한다 — `DIFY_PRICE_INSIGHT_API_KEY`를 설정하지 않으면
  AI Coach 카드만 `unavailable`이 되고 가격 판정은 정상 동작한다.
  이 폴백 동작 자체가 핸드오프 문서에 정의된 실패 처리 규칙이므로 데모로서 성립한다.
- 참고: Hugging Face Spaces는 2026년 기준 Docker/Gradio SDK 호스팅에 PRO 구독이
  필요해져(Static Space만 무료) 이 프로젝트(FastAPI 백엔드)에는 맞지 않는다.

## 절차

1. https://render.com 에서 GitHub 계정으로 가입
2. **New +** → **Web Service** → 이 저장소(`hyunbean/tuit_hackathon_dify`) 연결
3. 설정
   - Runtime: **Docker** (루트의 `Dockerfile`을 자동 감지)
   - Instance Type: **Free**
4. (선택) AI Coach까지 살리려면 **Environment** 탭에서
   `DIFY_PRICE_INSIGHT_API_KEY` 추가. 설정하지 않아도 데모는 동작한다.
5. **Create Web Service** — 빌드가 끝나면 `https://<서비스명>.onrender.com`에서 열린다.
   이 주소를 이 저장소 README 상단과 포트폴리오에 라이브 데모 링크로 추가한다.

## 무료 티어 특성

15분간 요청이 없으면 인스턴스가 슬립하고, 슬립 후 첫 요청은 콜드 스타트로
수십 초 걸릴 수 있다. 포트폴리오 데모 용도로는 감수할 만한 트레이드오프다.

## 다른 호스트

`Dockerfile`은 `PORT` 환경변수를 존중하므로 Railway·Fly.io에도 그대로 올라간다.

## 로컬 확인

```bash
pip install -r requirements.txt
uvicorn server.app:app --port 8600     # → http://localhost:8600
python -m pytest server/test_server.py -q
```
