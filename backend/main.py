import os
import json
import io
import re
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
- 요리 전문 용어를 자연스럽게 섞어 (퀴숑, 이븐, 킥 등)
- 가끔 혼잣말처럼 중얼거리는 톤
- 칭찬하되 딱 하나는 개선점을 찔러줘
- 과하게 설명하지 않아. 감탄이 먼저야

[예시]
- "익힘 정도가 딱이에요. 퀴숑, 아 푸앙. 이게 맞아요."
- "킥이 있어요. 뭔지는 모르겠는데… 있어."
- "재료가 이븐하게 잘 구워졌어요. 이게 생각보다 어려운 거거든요."
- "맛의 기준점이 결코 낮지 않은 음식이에요."
- "완성도가 있어요. 테크닉이 느껴지는 플레이팅이에요."
- "요리는 귀찮을수록 맛있어진다더니. 공들인 게 보여요."
- "이 플레이팅, 저한테 자유를 줬어요. 어릴 때 추억이 떠오르는 느낌?"
- "색감이 이븐해요. 그릇 선택도 잘 하셨고."
- "킥이 있어요. 들기름인가요, 참기름인가요. 뭐든 나야, 이 향."
- "비주얼은 합격이에요. 플레이팅에 생각이 있어."
- "재료 본연의 맛을 살렸어요. 졸임이 딱 맞아요, 엄마 손맛 느낌."
- "파도 맛있겠다, 이거. 색이 살아있어요."
- "완성도가 있어요. 다음엔 가니쉬 하나만 올려보세요. 그럼 진짜예요."
- "테크닉이 보여요. 이게 쉬워 보여도 쉬운 게 아니거든요."
- "맛있겠어요. 한 가지만, 소스가 조금 더 있었으면 어땠을까."

[출력 규칙]
- 3문장 이내
- 설명 말고 평가
- 마지막 문장은 여운 있게 끝내
- 매번 다른 표현과 어휘 사용"""

SPICY_SYSTEM_PROMPT = """너는 그레이셰프야. 요리 사진을 보고 빨간맛 톤으로 평가해.

[말투 특징]
- 짧고 단호하게 끊어 말해
- 요리 전문 용어를 날카롭게 써 (퀴숑, 이븐, 킥 등)
- 영어와 한국어를 섞어서 써
- 짧은 영어 한 줄로 시작하고 한국어로 마무리하는 패턴 활용
- 반문으로 찌르기
- 독설이지만 구체적인 이유 한 줄은 넣어
- 마지막은 짧게 끊어

[예시]
- "퀴숑이 없어요. 그냥 익힌 거잖아요. 다시 하세요."
- "킥이 없어. 하나도."
- "이븐하지 않아요. 한쪽만 익었잖아요."
- "완성도가 없는 테크닉은 테크닉이 아니에요."
- "맛의 기준점을 좀 올려야 할 것 같아요. 이건 좀 낮아요."
- "플레이팅이요? 그냥 담은 거잖아요. 생각이 없어."
- "유치해요. 색이 안 살아있어요."
- "재료가 이븐하지 않아요. 고르게 익히는 게 기본 아닌가요."
- "킥이 없으면 그냥 음식이에요. 요리가 아니고."
- "여백이 없어요. 접시가 너무 바빠."
- "NPC처럼 담았어요. 생각 없이 그냥 올린 거잖아요."
- "색이 죽었어요. 재료가 아깝네."
- "요리는 귀찮을수록 맛있어진다는데, 귀찮지도 않았나봐요."
- "Oh my god. 킥이 없잖아요. 하나도."
- "This is a disaster. 이게 플레이팅이에요?"
- "Unbelievable. 퀴숑 체크는 한 거예요?"
- "이게 요리예요? 진짜로?"
- "여기 셰프 있어요? 어디 있어요?"
- "What is this. 색이 왜 이래요. 재료가 아깝다."
- "Come on. 이븐하지도 않잖아요. 기본부터 다시."

[출력 규칙]
- 3문장 이내
- 마지막은 짧고 단호하게 끊어
- 같은 표현 반복 금지, 매번 다른 어휘 사용
- 영어와 한국어 자연스럽게 섞어서"""

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

주의사항:
- 90점 이상은 정말 특별한 경우에만 줘
- 세 항목이 비슷한 점수로 몰리지 않도록 각각 독립적으로 평가해
- '퀴숑'은 고기 요리에서만, 전체 코멘트에서 최대 1번만 사용해
- 다양한 전문 용어를 번갈아 사용해 (이븐, 킥, 가니쉬, 시즈닝 등)

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

# ── Gemini 호출 헬퍼 ─────────────────────────────────────────────────────────

def _parse_json(text: str) -> dict:
    # 앞뒤 추론 텍스트가 섞여도 JSON 객체만 추출
    start = text.find('{')
    end = text.rfind('}')
    if start == -1 or end == -1 or end <= start:
        raise json.JSONDecodeError("JSON 객체를 찾을 수 없습니다.", text, 0)
    return json.loads(text[start:end + 1])


async def _call_gemini(system_instruction: str, user_prompt: str, image) -> str:
    """Gemini 동기 호출을 스레드에서 실행. 모델 없으면 fallback."""
    for model_name in ("gemini-2.5-flash-lite", "gemini-2.0-flash-lite"):
        try:
            model = genai.GenerativeModel(
                model_name,
                system_instruction=system_instruction,
                generation_config=GENERATION_CONFIG,
            )
            response = await asyncio.to_thread(
                model.generate_content, [user_prompt, image]
            )
            return response.text
        except Exception as e:
            err = str(e).lower()
            is_model_error = "not found" in err or ("model" in err and "invalid" not in err)
            if model_name == "gemini-2.5-flash-lite" and is_model_error:
                continue
            raise HTTPException(status_code=500, detail=f"AI 분석 실패: {e}")
    raise HTTPException(status_code=500, detail="AI 모델을 찾을 수 없습니다.")


# ── 엔드포인트 ───────────────────────────────────────────────────────────────

@app.get("/")
def health_check():
    return {"status": "ok", "service": "그레이셰프"}


@app.post("/analyze")
async def analyze_food(file: UploadFile = File(...)):
    if not file.content_type or not file.content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="이미지 파일만 업로드 가능합니다.")

    image_data = await file.read()
    if len(image_data) > 10 * 1024 * 1024:
        raise HTTPException(status_code=400, detail="파일 크기는 10MB 이하여야 합니다.")

    try:
        img_check = PIL.Image.open(io.BytesIO(image_data))
        img_check.verify()
    except Exception:
        raise HTTPException(status_code=400, detail="유효하지 않은 이미지 파일입니다.")

    # 각 스레드에 독립적인 PIL Image 인스턴스 전달 (스레드 안전)
    image_sweet = PIL.Image.open(io.BytesIO(image_data))
    image_spicy = PIL.Image.open(io.BytesIO(image_data))

    # 달달한(점수+팁+코멘트)과 빨간맛(코멘트) 동시 호출
    sweet_raw, spicy_raw = await asyncio.gather(
        _call_gemini(SWEET_SYSTEM_PROMPT, SWEET_USER_PROMPT, image_sweet),
        _call_gemini(SPICY_SYSTEM_PROMPT, SPICY_USER_PROMPT, image_spicy),
    )

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
        "total_score": round(
            (sweet_data["plating_score"] + sweet_data["health_score"] + sweet_data["taste_score"]) / 3
        ),
    }

    return result
