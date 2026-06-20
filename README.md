# KOSPI 이동평균 · 이격도(Disparity Index) 차트

KOSPI 종합지수(^KS11)의 **이동평균선과 이격도**를 시각화합니다.
이평선(5/10/20/50/120/200일)을 체크박스로 토글하는 **인터랙티브 웹페이지**(`index.html`)와,
정적 PNG를 만드는 **파이썬 스크립트**(`kospi_disparity.py`)를 모두 제공합니다.

> 이격도(Disparity Index) = (종가 / N일 이동평균) × 100
>
> - **100** : 주가가 이동평균선과 일치
> - **>100** : 주가가 이동평균선 위 (단기 과열 신호)
> - **<100** : 주가가 이동평균선 아래 (단기 침체 신호)

## 1. 인터랙티브 웹페이지 (`index.html`)

상단 "KOSPI 가격 및 이동평균", 하단 "KOSPI 이격도" 2단 구성. 이평선 체크박스로
원하는 기간을 켜고 끌 수 있습니다. Chart.js를 `vendor/`에 내장해 **외부 CDN 없이**
열립니다.

```bash
# 로컬 확인
python3 -m http.server 8000   # http://localhost:8000 접속
```

GitHub Pages로 배포하려면 저장소 Settings → Pages 에서 브랜치를 지정하면
`index.html`이 그대로 서비스됩니다.

![KOSPI 이격도 차트](kospi_disparity.png)

## 2. 정적 PNG 스크립트 (`kospi_disparity.py`)

```bash
pip install matplotlib pandas
python3 kospi_disparity.py                 # 50일 이격도 (기본)
python3 kospi_disparity.py --window 20     # 20일 이격도
python3 kospi_disparity.py --out chart.png # 출력 경로 지정
```

## 데이터

- 로컬 데이터는 `data/kospi.csv`(`Date,Close`)이며 기간은
  **2024-10-31 ~ 2026-06-19** 입니다. 공개 데이터 피드(Yahoo `^KS11` 기반)를
  병합했고, 겹치는 구간은 소수점까지 교차검증해 일치를 확인했습니다.
  - 2026-06-19 종가 9,052.42 / 50일 이동평균 7,466.78 → **50일 이격도 121.2**
- 네트워크가 가능한 환경에서는 최신 데이터를 직접 받을 수 있습니다:

  ```bash
  pip install finance-datareader   # 또는 yfinance
  python3 kospi_disparity.py --source live
  ```

## 파일

| 경로 | 설명 |
|------|------|
| `index.html` | 인터랙티브 차트 페이지 (이평선 토글) |
| `data.js` | 페이지에 내장되는 KOSPI 일별 종가 |
| `vendor/chart.umd.min.js` | Chart.js (MIT) — CDN 없이 동작 |
| `kospi_disparity.py` | 정적 이격도 차트 생성 스크립트 |
| `data/kospi.csv` | KOSPI 일별 종가 데이터 |
| `fonts/NanumGothic.ttf` | 정적 차트 한글 렌더링용 폰트 (OFL) |
| `kospi_disparity.png` | 생성된 정적 차트 이미지 |
