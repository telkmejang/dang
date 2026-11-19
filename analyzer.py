import json
from openai import OpenAI
from config import OPENAI_API_KEY

client = OpenAI(api_key=OPENAI_API_KEY) if OPENAI_API_KEY else None


def analyze_deal(item: dict, brand_hint: str = "") -> dict:
    if not client:
        return {"is_deal": True, "reason": "OpenAI 키 미설정(테스트 통과)"}

    prompt = f"""
당신은 중고 명품·스트릿·고프코어 리셀 시세 및 급매 판별 전문가입니다.
아래 당근마켓 매물 정보를 보고, 시세 대비 충분한 마진을 기대할 수 있는 '꿀매'인지 판단하세요.

[제외 대상 - is_deal: false]
1. 나눔, 구매희망/삽니다 글, 매입 업자/대행 광고 글
2. 레플리카·가품 의심 매물(정가·중고시세 대비 비정상적으로 싼 고가 브랜드 매물 등)
3. 오염, 찢김, 구멍, 심한 보풀/변색, 수선 이력 등 상태 하자가 있는 매물
4. 쇼핑백, 박스, 케이스, 행거, 여분 단추·택 등 본품이 아니거나 부속품만 파는 매물
5. 단가가 낮거나 차익이 적은 단순 소품·양말·기본 티셔츠 위주 매물

[우대 대상 - is_deal: true 가능성 높음]
- 자켓, 패딩, 바람막이(쉘), 니트, 가디건, 후드, 팬츠 등 단가가 높고 시세 방어가 잘 되는 의류

- 관심 브랜드 힌트: {brand_hint or "미지정"}
- 제목: {item['title']}
- 상세/가격정보: {item['info']}

반드시 아래 JSON 형식으로만 응답하세요:
{{"is_deal": true 또는 false, "reason": "한 줄 판단 사유"}}
"""
    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}],
            response_format={"type": "json_object"},
            temperature=0.2,
            timeout=15,
        )
        result = json.loads(response.choices[0].message.content)
        return {
            "is_deal": bool(result.get("is_deal", False)),
            "reason": result.get("reason", "사유 없음"),
        }
    except Exception as e:
        print(f"[AI 분석 에러] {item['title']} -> {e}")
        return {"is_deal": False, "reason": "분석 실패"}
