import os
import json
from openai import OpenAI

client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))

SYSTEM_PROMPT = """
당신은 빈티지샵 사입(도매·리셀) 전문 바이어입니다.
제공된 당근마켓 중고 매물(브랜드, 제목, 가격, 설명)을 보고, 빈티지샵에서 재판매했을 때 충분한 마진이 남을 매물인지 판단하세요.

[사입 통과 기준 - 아래 조건을 충족해야 true]
1. 마진 확보(최우선): 일반 번개장터·크림·빈티지샵 판매 시세 대비 최소 35~50% 이상 저렴하게 올라온 급매가여야 함. (단순 개인 거래 적정가 수준은 마진이 안 남으므로 제외)
2. 재판매 회전율: 아우터(자켓, 코트, 패딩, 플리스), 니트, 스웻셔츠/후드, 데님·워크팬츠, 가방/모자 등 빈티지샵에서 수요가 확실한 품목 우선.
3. 빈티지 특성 반영: 자연스러운 에이징, 미세한 사용감, 세탁으로 지워질 오염, 단추 분실 등 수선·케어가 가능한 수준의 하자는 감안함. 오히려 하자를 이유로 시세보다 대폭 저렴하게 나온 매물은 사입 기회로 보고 긍정 평가할 것.
4. 시세 모호성 처리: 연식이 오래된 아카이브·구형 택·희귀 모델이라 정확한 시세 산정이 어렵더라도, 브랜드 체급 대비 절대 가격이 매우 낮으면(예: 고가 브랜드 아우터/니트가 몇만 원대) 사입 후보로 통과시킬 것.

[사입 제외 기준 - 아래에 해당하면 무조건 false]
1. 가품, 레플리카, 스타일 제품, 정가품 의심 매물 (매장 판매 불가 리스크)
2. 찢어짐, 심각한 변색/이염, 곰팡이, 악취, 지퍼/부자재 파손 등 복구가 불가능해 상품 가치가 없는 폐급 상태
3. 마진이 거의 남지 않는 개인 간 평균 시세 매물 또는 고가 매물
4. 구매 희망 글("구해요", "삽니다"), 대여/교환, 브랜드와 무관한 잡화·광고성 게시글

반드시 아래 JSON 형식으로만 응답하세요.
{
  "is_deal": true 또는 false,
  "estimated_margin": "높음 / 보통 / 낮음 중 하나",
  "reason": "예상 재판매가 대비 사입 메리트 또는 제외 사유를 한 줄로 요약"
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
            temperature=0.2,
            response_format={"type": "json_object"},
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": user_content},
            ],
        )

        raw_text = response.choices[0].message.content
        result = json.loads(raw_text)

        is_deal = bool(result.get("is_deal", False))
        margin = str(result.get("estimated_margin", "")).strip()
        reason = str(result.get("reason", "사유 없음")).strip()

        formatted_reason = f"[마진: {margin}] {reason}" if margin else reason
        return is_deal, formatted_reason

    except Exception as e:
        print(f"[AI 판정 오류] {item.get('title', '')}: {e}")
        return False, f"AI 분석 오류: {e}"


if __name__ == "__main__":
    sample_item = {
        "brand": "스톤아일랜드",
        "title": "스톤아일랜드 구형 코튼 니트 L",
        "price": "90,000원",
        "description": "옛날 모델이라 사용감 좀 있고 소매 살짝 보풀 있습니다. 옷장 정리로 싸게 넘겨요.",
    }
    ok, msg = evaluate_deal(sample_item)
    print(f"결과: {ok} | 사유: {msg}")