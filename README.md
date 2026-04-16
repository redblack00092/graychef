# 그레이셰프 (Grey Chef)

요리 사진 한 장으로 AI 셰프에게 플레이팅 평가를 받아보세요.

---

## 소개

그레이셰프는 음식 사진을 업로드하면 AI가 플레이팅, 건강, 예상 맛을 분석하고 두 가지 톤으로 평가해주는 모바일 최적화 웹 서비스입니다. 달달한 칭찬이 필요할 때, 날카로운 독설이 듣고 싶을 때 모두 가능합니다.

---

## 주요 기능

- 📷 **사진 업로드** — 갤러리 선택 또는 모바일 카메라 직접 촬영
- 📊 **3가지 점수 평가** — 플레이팅 / 건강 / 예상 맛 (0~99점)
- 🌶 **빨간맛 코멘트** — 직설적이고 날카로운 셰프의 독설
- 🍯 **달달한 코멘트** — 따뜻하고 칭찬 위주의 평가
- 📤 **결과 공유** — 분석 결과를 이미지로 캡처해 공유

---

## 기술 스택

| 영역 | 기술 |
|------|------|
| Frontend | React + Tailwind CSS + Vite |
| Backend | Python FastAPI |
| AI | Google Gemini 2.5 Flash |
| 배포 | AWS EC2 + Nginx + pm2 |

---

## 로컬 실행

### 요구사항
- Python 3.9+
- Node.js 18+

### 백엔드

```bash
make backend
```

### 프론트엔드 (새 터미널)

```bash
make frontend
```

브라우저에서 `http://localhost:5173` 접속

> `make backend`는 가상환경 생성 → 패키지 설치 → 서버 실행을 자동으로 처리합니다.

---

## 환경변수 설정

`backend/.env` 파일을 생성하고 아래 내용을 입력하세요.

```env
GEMINI_API_KEY=발급받은_키_입력
```

> `.env` 파일은 `.gitignore`에 포함되어 있어 Git에 업로드되지 않습니다.

---

## 배포 (AWS EC2)

```bash
git clone <repo-url>
cd graychef

# .env 파일 생성 후 API 키 입력
echo "GEMINI_API_KEY=발급받은_키" > backend/.env

# 배포 스크립트 실행
chmod +x deploy.sh
./deploy.sh
```

`deploy.sh`가 아래 작업을 자동으로 처리합니다.

1. 백엔드 패키지 설치
2. 프론트엔드 빌드
3. pm2로 백엔드 서버 실행
4. Nginx 설정 적용
