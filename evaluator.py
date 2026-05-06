import anthropic
from config import Config

_client = None

def get_client():
    global _client
    if _client is None:
        _client = anthropic.Anthropic(api_key=Config.ANTHROPIC_API_KEY)
    return _client

SYSTEM_PROMPT = """당신은 텔레그램 투자/주식 채널의 포스트를 분석하는 전문가입니다.
포스트를 읽고 투자 판단에 실제로 도움이 되는지 평가해주세요.

평가 기준 (각 항목 2점, 총 10점):
1. 구체성: 막연한 감이 아니라 종목, 섹터, 지표 등 구체적인 내용이 있는가
2. 근거: 매수/매도 혹은 시장 판단의 논리적 근거가 제시되어 있는가
3. 시의성: 지금 시장 상황이나 최근 이슈와 연관성이 있는가
4. 신뢰도: 단순 뇌동매매 유도나 과장 없이 균형잡힌 시각인가
5. 행동가능성: 읽고 나서 실제 투자 판단에 활용할 수 있는 정보인가

반드시 아래 JSON 형식으로만 응답하세요:
{"score": <1-10 정수>, "summary": "<한국어로 2-3줄 핵심 요약>", "reason": "<점수 이유 한 줄>"}"""

async def evaluate_post(text: str) -> tuple[int, str, str]:
    """Returns (score, summary, reason)"""
    try:
        message = get_client().messages.create(
            model="claude-haiku-4-5-20251001",
            max_tokens=300,
            system=SYSTEM_PROMPT,
            messages=[{"role": "user", "content": f"다음 포스트를 평가해주세요:\n\n{text[:2000]}"}],
        )
        import json
        result = json.loads(message.content[0].text)
        return int(result["score"]), result["summary"], result["reason"]
    except Exception as e:
        print(f"[Evaluator] Error: {e}")
        return 0, "", str(e)
