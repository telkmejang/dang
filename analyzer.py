import json
from openai import OpenAI
from config import OPENAI_API_KEY

client = OpenAI(api_key=OPENAI_API_KEY) if OPENAI_API_KEY else None


def analyze_deal(item: dict) -> dict:
    if not client:
        return {"is_deal": True, "reason": "OpenAI 키 미설정(테스트 통과)"}

    prompt = f"""
당신은 중고거래 시세 및 급매 판별 전문가입니다.
아래 당근마켓 매물 정보를 보고, 구매할 만한 가치가 있는 '꿀매(급매/시세보다 저렴함)'인지 판단하세요.
나눔이거나 터무니없는 낚시 글, 매입 업자 글은 제외하세요.

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
