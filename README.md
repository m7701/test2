# test2

## KOSPI 50일 이격도 차트 (`kospi_disparity.py`)

KOSPI 종합지수의 **50일 이격도(Disparity Index = 종가 / 50일 이동평균 × 100)** 를 계산하고
차트(지수+이동평균, 이격도+과열/침체 밴드)를 그리며, **단기하락 직전 고점의 이격도**를 표로 출력합니다.

### 실행

```bash
pip install pykrx matplotlib pandas numpy   # KRX(한국거래소) 직접 데이터
python kospi_disparity.py --source krx       # 최근 2년, 50일 이격도
```

데이터 소스 옵션:

```bash
python kospi_disparity.py --source krx    # 한국거래소(pykrx) 직접 — 가장 본질적
python kospi_disparity.py --source fdr    # FinanceDataReader (KRX/네이버)
python kospi_disparity.py --source yahoo  # yfinance (^KS11)
python kospi_disparity.py                 # auto: KRX → FDR → Yahoo 순 폴백
```

자주 쓰는 옵션:

```bash
python kospi_disparity.py --ma 50 --years 3        # 이동평균 기간 / 조회 연수
python kospi_disparity.py --start 2024-01-01 --end 2026-06-19
python kospi_disparity.py --drop 4                 # 단기하락 기준 낙폭(%)
python kospi_disparity.py --demo                   # 데이터 없이 차트 형식만 미리보기(가짜 데이터)
```

결과: `kospi_disparity.png` 저장 + 콘솔에 현재 이격도/단기하락 표 출력.

### 네트워크 메모 (Claude Code on the web)

금융 데이터 사이트는 기본 허용목록에 없습니다. 환경의 **Network access → Custom**에서
**Allowed domains**에 아래를 추가하세요(패키지 매니저 기본 목록 포함 체크):

```
*.krx.co.kr
finance.naver.com
api.finance.naver.com
*.finance.yahoo.com
```

허용목록 변경은 **새 세션부터 적용**됩니다(기존에 떠 있는 세션에는 반영되지 않음).
