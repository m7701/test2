# TG Investment Monitor Bot

텔레그램 투자/주식 채널을 모니터링하다가 Claude AI가 높은 점수를 준 포스트만 알림으로 받는 봇.

## 구조

```
채널들 → Telethon으로 수신 → Claude AI 품질 평가 (1~10점) → 기준 이상이면 나에게 알림 + 원본 포워드
```

## 셋업 순서

### 1. 준비물 발급

| 항목 | 방법 |
|------|------|
| Telegram API ID/Hash | [my.telegram.org](https://my.telegram.org) → API development tools |
| Anthropic API Key | [console.anthropic.com](https://console.anthropic.com) |

### 2. 로컬에서 세션 문자열 생성 (최초 1회)

```bash
pip install -r requirements.txt
cp .env.example .env
# .env에 TG_API_ID, TG_API_HASH 먼저 입력 후:
python auth.py
```

출력된 SESSION STRING을 `.env`의 `TG_SESSION=` 뒤에 붙여넣기.

### 3. .env 나머지 항목 채우기

```env
TG_NOTIFY_TARGET=me          # 알림 받을 대상 (me = 내 저장된 메시지)
TG_CHANNELS=@channel1,@channel2   # 모니터링할 채널들
MIN_SCORE=7                  # 알림 최소 점수 (1~10)
```

### 4. 로컬 테스트

```bash
python main.py
```

### 5. Railway 배포 (24시간 운영)

1. [railway.app](https://railway.app) 가입 → New Project → Deploy from GitHub
2. 이 레포 연결
3. Variables 탭에서 `.env` 항목들 모두 입력
4. Deploy → worker가 자동 시작

## AI 평가 기준

Claude가 각 포스트를 아래 5가지 항목 기준으로 10점 만점 채점:

1. **구체성** — 종목/섹터/지표 등 구체적 언급
2. **근거** — 매수/매도 판단의 논리적 근거
3. **시의성** — 현재 시장 상황과 연관성
4. **신뢰도** — 균형잡힌 시각, 과장 없음
5. **행동가능성** — 실제 투자 판단에 활용 가능

`MIN_SCORE` 이상이면 알림 + 원본 포워드.
