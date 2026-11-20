import os
import json
from openai import OpenAI

client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))

SYSTEM_PROMPT = """
당신은 빈티지샵 사입(도매·리셀) 전문 바이어입니다.
제공된 당근마켓 중고 매물(브랜드, 제목, 가격, 설명)을 보고, 놓치면 아까울 만한 사입 후보인지 판단하세요.
기준은 너무 깐깐하지 않게 잡아서, 유망한 매물은 가급적 통과(true)시키세요.

[사입 통과 기준 - 아래 중 하나라도 해당하면 true]
1. 마진 기회의 폭: 일반 중고·리셀 플랫폼(번개장터, 크림, 후루츠패밀리 등) 시세보다 약 25~30% 이상 저렴한 매물부터 유연하게 통과시키세요. 마진 상한은 없으며, 시세 대비 훨씬 싸서 40~50% 이상 고마진이 기대되는 매물은 최우선으로 통과시키세요.
2. 유연한 라인 판정: 버버리·폴로·노스페이스·리바이스·칼하트·몽벨 등 인기 브랜드는 상위·빈티지 라인은 물론이고, 기본템이라도 절대 가격이 저렴해 리셀·세팅 여지가 보이면 통과하세요.
3. 하자·에이징 긍정 반영: 자연스러운 에이징, 사용감, 구김, 미세 오염, 단추/부자재 경미한 손실, 케어·수선 가능 하자는 감점 요인이 아니라 오히려 싸게 나온 기회로 보세요.
4. 시세 불확실 시 통과: 모델명이 애매하거나 구형·빈티지라 시세 계산이 딱 떨어지지 않더라도, 브랜드 네임밸류 대비 가격이 낮아 보이면 놓치지 말고 true로 판정하세요.

[사입 제외 기준 - 확실한 경우에만 false]
1. 명백한 가품, 레플리카, 이미테이션, 정가품 의심 매물
2. 찢어짐, 심한 곰팡이/악취/이염, 수선 불가 수준의 심각한 파손으로 판매가 불가능한 상태
3. 시세보다 오히려 비싸거나, 매입가 대비 남는 게 전혀 없는 정가·고가 매물
4. "구해요/삽니다", 나눔/교환 요청, 무관한 잡화·도배성 광고

반드시 아래 JSON 형식으로만 응답하세요.
{
  "is_deal": true 또는 false,
  "estimated_margin": "초고마진(50%+) / 높음 / 보통 / 애매(참고) 중 하나",
  "reason": "통과 또는 제외 이유를 한 줄로 간결하게 요약"
}
""".strip()


def evaluate_deal(item: dict) -> tuple[bool, str]:
    user_content = (
        f"검색 브랜드: {item.get('brand', '미상')}\n"
        f"제목: {item.get('title', '')}\n"
        f"가격: {item.get('price', '')}\n"
        f"설명: {item.get('description', '')}"
    )

    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            temperature=0.3,
            response_format={"type": "json_object"},
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": user_content},
            ],
        )

        result = json.loads(response.choices[0].message.content)
        is_deal = bool(result.get("is_deal", False))
        margin = str(result.get("estimated_margin", "")).strip()
        reason = str(result.get("reason", "사유 없음")).strip()

        formatted_reason = f"[마진: {margin}] {reason}" if margin else reason
        return is_deal, formatted_reason

    except Exception as e:
        print(f"[AI 판정 오류] {item.get('title', '')}: {e}")
        return False, f"AI 분석 오류: {e}"


def analyze_deal(item: dict) -> tuple[bool, str]:
    return evaluate_deal(item)
    