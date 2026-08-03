# 배포 (Hugging Face Spaces)

`server/`의 레퍼런스 백엔드 + 웹 데모를 무료로 공개 배포하는 절차입니다.

## 왜 Hugging Face Spaces인가

- 무료 CPU 티어로 Docker 컨테이너를 그대로 실행
- AI 포트폴리오 맥락에서 링크 자체가 신호가 된다
- 키가 없어도 데모가 성립한다 — `DIFY_PRICE_INSIGHT_API_KEY`를 설정하지 않으면
  AI Coach 카드만 `unavailable`이 되고 가격 판정은 정상 동작한다.
  이 폴백 동작 자체가 핸드오프 문서에 정의된 실패 처리 규칙이므로 데모로서 성립한다.

## 절차

1. https://huggingface.co/new-space 에서 Space 생성
   - Space name: `bozorcheck-demo`
   - SDK: **Docker** → Blank
   - Hardware: CPU basic (무료)

2. 로컬에서 Space를 클론하고 필요한 파일만 복사

   ```bash
   git clone https://huggingface.co/spaces/<HF_USERNAME>/bozorcheck-demo
   cd bozorcheck-demo

   # 이 저장소에서 가져올 파일
   cp <이_저장소>/Dockerfile .
   cp <이_저장소>/requirements.txt .
   cp -r <이_저장소>/server .
   cp <이_저장소>/deploy/hf-space-README.md README.md   # ← HF 설정 frontmatter 포함

   git add -A && git commit -m "Deploy BozorCheck reference backend" && git push
   ```

3. (선택) AI Coach까지 살리려면 Space → Settings → **Variables and secrets**에서
   `DIFY_PRICE_INSIGHT_API_KEY` 추가. 설정하지 않아도 데모는 동작한다.

4. 빌드가 끝나면 `https://<HF_USERNAME>-bozorcheck-demo.hf.space` 에서 열린다.
   이 주소를 이 저장소 README 상단과 포트폴리오에 라이브 데모 링크로 추가한다.

## 다른 호스트

`Dockerfile`은 `PORT` 환경변수를 존중하므로 Render·Railway·Fly.io에도 그대로 올라간다.
`README.md`의 frontmatter는 Hugging Face 전용이라 다른 호스트에서는 필요 없다.

## 로컬 확인

```bash
pip install -r requirements.txt
uvicorn server.app:app --port 8600     # → http://localhost:8600
python -m pytest server/test_server.py -q
```
