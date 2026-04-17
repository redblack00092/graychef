import os
import json
import io
import asyncio
import PIL.Image
import google.generativeai as genai
from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv

load_dotenv()

api_key = os.getenv("GEMINI_API_KEY")
if not api_key:
    raise RuntimeError("GEMINI_API_KEY 환경변수가 설정되지 않았습니다.")

genai.configure(api_key=api_key)

app = FastAPI(title="그레이셰프 API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["POST", "GET"],
    allow_headers=["*"],
)

# ── 시스템 프롬프트 ──────────────────────────────────────────────────────────

SWEET_SYSTEM_PROMPT = """너는 그레이셰프야. 요리 사진을 보고 달달한 톤으로 평가해.

[말투 특징]
- 짧고 여운 있게 끊어 말해
- 요리 전문 용어를 자연스럽게 섞어
- 가끔 혼잣말처럼 중얼거리는 톤
- 칭찬하되 딱 하나는 개선점을 찔러줘
- 과하게 설명하지 않아. 감탄이 먼저야

[출력 규칙]
- 3문장 이내
- 설명 말고 평가
- 마지막 문장은 여운 있게 끝내
- 매번 다른 표현과 어휘 사용"""
- 코멘트에 점수 표기는 하지 말것

SPICY_SYSTEM_PROMPT = """너는 그레이셰프야. 요리 사진을 보고 빨간맛 톤으로 평가해.

[말투 특징]
- 짧고 단호하게 끊어 말해
- 요리 전문 용어를 날카롭게 써
- 영어와 한국어를 섞어서 써
- 짧은 영어 한 줄로 시작하고 한국어로 마무리하는 패턴 활용
- 반문으로 찌르기
- 독설이지만 구체적인 이유 한 줄은 넣어
- 마지막은 짧게 끊어

[출력 규칙]
- 3문장 이내
- 마지막은 짧고 단호하게 끊어
- 같은 표현 반복 금지, 매번 다른 어휘 사용
- 영어와 한국어 자연스럽게 섞어서"""
- 코멘트에 점수 표기는 하지 말것

# ── 유저 프롬프트 ────────────────────────────────────────────────────────────

FOOD_RECOGNITION_PREFIX = """반드시 아래 순서대로 진행해.

[1단계 - 음식 인식]
사진 속 음식이 무엇인지 먼저 파악해.
- 어떤 요리인지 (한식/양식/중식/일식 등)
- 주재료가 뭔지
- 조리 방식이 뭔지 (볶음/구이/찜/튀김 등)
- 판단이 어려우면 가장 가능성 높은 음식으로 추측해서 진행해

[2단계 - 음식 특성 기반 평가 기준 설정]
인식한 음식에 맞게 평가 기준을 조정해.
- 국물 요리면 색감보다 재료 구성 비중을 높여
- 구이 요리면 퀴숑(익힘 정도)을 중요하게 봐
- 비빔 요리면 색 균형과 재료 다양성을 중점으로 봐

[3단계 - 평가 및 코멘트 생성]
1~2단계 결과를 바탕으로 점수와 코멘트를 생성해.
코멘트 첫 문장에 음식 이름을 자연스럽게 언급해.
예: "오 제육볶음이네요." / "이거 파스타죠?" / "된장찌개인가요, 이거."

"""

SCORE_GUIDELINES = """
[점수 기준 — 반드시 준수]
점수 범위: 0~99점 (플레이팅 / 건강 / 예상 맛 각각 독립 평가)

분포 가이드라인:
- 0~20점:  요리라고 보기 어려운 수준
- 21~40점: 심각한 문제 있음
- 41~55점: 아쉬운 부분이 많음
- 56~70점: 평균적인 가정식 수준
- 71~82점: 잘 만든 편
- 83~91점: 매우 훌륭함 (자주 주지 말 것)
- 92~99점: 거의 레스토랑 수준 (극히 드물게)

엄격한 기준:
- 잘 만든 가정식은 61~72점
- 정말 훌륭한 요리만 73점 이상
- 80점 이상은 레스토랑 수준일 때만
- 90점 이상은 절대 주지 말 것
- 세 항목 점수 차이가 최소 5점 이상 나도록 독립적으로 평가해

"""

SWEET_USER_PROMPT = FOOD_RECOGNITION_PREFIX + SCORE_GUIDELINES + """분석이 끝나면 아래 JSON 형식으로만 응답하세요.
마크다운 코드 블록 없이 순수 JSON만 반환하세요.

- plating_score: 위 기준에 따라 독립 평가한 플레이팅/비주얼 점수 (0~99 정수)
- health_score: 위 기준에 따라 독립 평가한 건강도 점수 (0~99 정수)
- taste_score: 위 기준에 따라 독립 평가한 예상 맛 점수 (0~99 정수)
- sweet_comment: 네 말투와 스타일로 쓴 달달한 코멘트 (첫 문장에 음식 이름 언급)
- tip_plating: 플레이팅 개선을 위한 구체적 팁 (1-2문장)
- tip_taste: 예상 맛을 올리기 위한 구체적 팁 (1-2문장)
- tip_health: 건강을 더 챙기기 위한 구체적 팁 (1-2문장)

{
  "plating_score": 정수,
  "health_score": 정수,
  "taste_score": 정수,
  "sweet_comment": "문자열",
  "tip_plating": "문자열",
  "tip_taste": "문자열",
  "tip_health": "문자열"
}"""

SPICY_USER_PROMPT = FOOD_RECOGNITION_PREFIX + SCORE_GUIDELINES + """분석이 끝나면 아래 JSON 형식으로만 응답하세요.
마크다운 코드 블록 없이 순수 JSON만 반환하세요.

- spicy_comment: 네 말투와 스타일로 쓴 빨간맛 코멘트 (첫 문장에 음식 이름 언급)

{
  "spicy_comment": "문자열"
}"""

GENERATION_CONFIG = {
    "temperature": 0.9,
}

# ── 이미지 전처리 ─────────────────────────────────────────────────────────────

MAX_IMAGE_PX = 1024  # 긴 변 최대 픽셀

def _preprocess_image(image_data: bytes) -> PIL.Image.Image:
    """검증 → 리사이즈 → JPEG 재인코딩 → 픽셀 로드. 원본 bytes는 호출 측에서 del."""
    # 검증
    try:
        tmp = PIL.Image.open(io.BytesIO(image_data))
        tmp.verify()
    except Exception:
        raise HTTPException(status_code=400, detail="유효하지 않은 이미지 파일입니다.")

    # 재오픈 (verify() 이후 이미지 상태 손상됨)
    image = PIL.Image.open(io.BytesIO(image_data))

    # 리사이즈 (긴 변 MAX_IMAGE_PX 이하로)
    if max(image.size) > MAX_IMAGE_PX:
        image.thumbnail((MAX_IMAGE_PX, MAX_IMAGE_PX), PIL.Image.LANCZOS)

    # RGB 변환 후 JPEG 재인코딩 (메모리 절감)
    if image.mode != "RGB":
        image = image.convert("RGB")

    buf = io.BytesIO()
    image.save(buf, format="JPEG", quality=85, optimize=True)
    image.close()

    buf.seek(0)
    image = PIL.Image.open(buf)
    image.load()   # 픽셀 데이터를 메모리에 완전히 로드
    buf.close()    # 버퍼 해제

    return image

NOT_FOOD_RESPONSE = {
    "plating_score": 0,
    "health_score": 0,
    "taste_score": 0,
    "total_score": 0,
    "is_food": False,
    "sweet_comment": "이거 음식이 맞나요? 저는 요리만 평가할 수 있어요.",
    "spicy_comment": "음식 사진을 올려주세요. 이건 평가 대상이 아니에요.",
    "tip_plating": "음식 사진을 올려주세요.",
    "tip_taste": "음식 사진을 올려주세요.",
    "tip_health": "음식 사진을 올려주세요.",
}

# ── Gemini 호출 헬퍼 ─────────────────────────────────────────────────────────

def _parse_json(text: str) -> dict:
    start = text.find('{')
    end = text.rfind('}')
    if start == -1 or end == -1 or end <= start:
        raise json.JSONDecodeError("JSON 객체를 찾을 수 없습니다.", text, 0)
    return json.loads(text[start:end + 1])


async def _is_food(image: PIL.Image.Image) -> bool:
    """음식 여부를 빠르게 판별. YES/NO만 응답."""
    for model_name in ("gemini-2.5-flash-lite", "gemini-2.0-flash-lite"):
        try:
            model = genai.GenerativeModel(model_name)
            response = await asyncio.to_thread(
                model.generate_content,
                ["이 사진에 음식이 있으면 YES, 없으면 NO 만 답해줘.", image],
            )
            answer = response.text.strip().upper()
            print(f"  [음식 판별] 응답: {answer!r}")
            return answer.startswith("YES")
        except Exception as e:
            err = str(e).lower()
            if model_name == "gemini-2.5-flash-lite" and ("not found" in err or "model" in err):
                continue
            raise HTTPException(status_code=500, detail=f"음식 판별 실패: {e}")
    raise HTTPException(status_code=500, detail="AI 모델을 찾을 수 없습니다.")


async def _call_gemini(system_instruction: str, user_prompt: str, image: PIL.Image.Image) -> str:
    for model_name in ("gemini-2.5-flash-lite", "gemini-2.0-flash-lite"):
        try:
            print(f"  [Gemini] {model_name} 호출 중...")
            model = genai.GenerativeModel(
                model_name,
                system_instruction=system_instruction,
                generation_config=GENERATION_CONFIG,
            )
            response = await asyncio.to_thread(
                model.generate_content, [user_prompt, image]
            )
            print(f"  [Gemini] {model_name} 응답 수신 완료")
            return response.text
        except Exception as e:
            err = str(e).lower()
            is_model_error = "not found" in err or ("model" in err and "invalid" not in err)
            if model_name == "gemini-2.5-flash-lite" and is_model_error:
                print(f"  [Gemini] {model_name} 없음, fallback 시도")
                continue
            raise HTTPException(status_code=500, detail=f"AI 분석 실패: {e}")
    raise HTTPException(status_code=500, detail="AI 모델을 찾을 수 없습니다.")


# ── 엔드포인트 ───────────────────────────────────────────────────────────────

@app.get("/api/health")
def health_check():
    return {"status": "ok", "service": "그레이셰프"}


@app.post("/api/analyze")
async def analyze_food(file: UploadFile = File(...)):
    print(f"[요청 수신] content_type={file.content_type}, filename={file.filename}")

    if not file.content_type or not file.content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="이미지 파일만 업로드 가능합니다.")

    image_data = await file.read()
    print(f"[파일 읽기 완료] size={len(image_data):,} bytes")

    if len(image_data) > 10 * 1024 * 1024:
        raise HTTPException(status_code=400, detail="파일 크기는 10MB 이하여야 합니다.")

    # 이미지 전처리 (리사이즈 + 재인코딩)
    image = _preprocess_image(image_data)
    del image_data  # 원본 bytes 즉시 해제
    print(f"[이미지 전처리 완료] size={image.size}")

    # 음식 여부 판별
    print("[음식 판별 시작]")
    try:
        food_detected = await asyncio.wait_for(_is_food(image), timeout=10.0)
    except asyncio.TimeoutError:
        food_detected = True  # 판별 실패 시 분석 진행
    if not food_detected:
        print("[음식 아님] 기본 응답 반환")
        image.close()
        return NOT_FOOD_RESPONSE
    print("[음식 확인됨] 평가 진행")

    try:
        # sweet 호출
        print("[Gemini sweet 호출 시작]")
        sweet_raw = await asyncio.wait_for(
            _call_gemini(SWEET_SYSTEM_PROMPT, SWEET_USER_PROMPT, image),
            timeout=60.0,
        )
        print("[Gemini sweet 완료]")

        # spicy 호출
        print("[Gemini spicy 호출 시작]")
        spicy_raw = await asyncio.wait_for(
            _call_gemini(SPICY_SYSTEM_PROMPT, SPICY_USER_PROMPT, image),
            timeout=60.0,
        )
        print("[Gemini spicy 완료]")

    except asyncio.TimeoutError:
        raise HTTPException(status_code=504, detail="AI 분석 시간이 초과됐습니다. 다시 시도해 주세요.")
    finally:
        image.close()  # 이미지 메모리 해제

    try:
        sweet_data = _parse_json(sweet_raw)
    except json.JSONDecodeError:
        raise HTTPException(status_code=500, detail="달달한 코멘트 응답 파싱 실패")

    try:
        spicy_data = _parse_json(spicy_raw)
    except json.JSONDecodeError:
        raise HTTPException(status_code=500, detail="빨간맛 코멘트 응답 파싱 실패")

    sweet_required = ["plating_score", "health_score", "taste_score",
                      "sweet_comment", "tip_plating", "tip_taste", "tip_health"]
    for key in sweet_required:
        if key not in sweet_data:
            raise HTTPException(status_code=500, detail=f"응답 필드 누락: {key}")

    if "spicy_comment" not in spicy_data:
        raise HTTPException(status_code=500, detail="응답 필드 누락: spicy_comment")

    result = {
        **sweet_data,
        "spicy_comment": spicy_data["spicy_comment"],
        "is_food": True,
        "total_score": round(
            (sweet_data["plating_score"] + sweet_data["health_score"] + sweet_data["taste_score"]) / 3
        ),
    }

    print(f"[응답 완료] total_score={result['total_score']}")
    return result
