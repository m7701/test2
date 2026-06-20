#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
KOSPI 50일 이격도(Disparity Index) 차트 + 단기하락 분석

이격도(Disparity Index) = 종가 / N일 이동평균 * 100
  - 100  : 주가가 이동평균선과 일치
  - >100 : 이동평균선 위 (단기 과열 가능)
  - <100 : 이동평균선 아래 (단기 침체 가능)

사용법:
  pip install FinanceDataReader matplotlib pandas numpy
  python kospi_disparity.py                       # 기본: 최근 2년, 50일 이격도
  python kospi_disparity.py --ma 50 --years 3
  python kospi_disparity.py --start 2024-01-01 --end 2026-06-19
  python kospi_disparity.py --demo                # 데이터 접근이 막힌 환경에서 형식만 미리보기(가짜 데이터)

데이터 소스 우선순위: FinanceDataReader(KRX/네이버) -> yfinance(^KS11) -> pykrx
"""
import argparse
import sys
from datetime import datetime, timedelta

import numpy as np
import pandas as pd


# ----------------------------------------------------------------------------
# 1) 데이터 로딩 (여러 소스 폴백)
# ----------------------------------------------------------------------------
def load_kospi(start, end, source="auto"):
    """KOSPI 종가 시계열(Series, index=날짜)을 반환. 실패 시 예외.

    source: auto(krx->fdr->yahoo) | krx | fdr | yahoo
    """
    errors = []

    # (1) pykrx — 한국거래소(KRX) 공식 지수 데이터에 가장 직접적
    if source in ("auto", "krx"):
        try:
            from pykrx import stock
            s_str = pd.Timestamp(start).strftime("%Y%m%d")
            e_str = pd.Timestamp(end).strftime("%Y%m%d")
            df = stock.get_index_ohlcv(s_str, e_str, "1001")  # 1001 = KOSPI 종합지수
            if df is not None and len(df) > 0:
                s = df["종가"].dropna()
                s.name = "KOSPI"
                print(f"[데이터] pykrx(KRX 한국거래소) 사용, {len(s)}일 "
                      f"({s.index[0].date()} ~ {s.index[-1].date()})")
                return s
        except Exception as e:  # noqa: BLE001
            errors.append(f"pykrx(KRX): {e}")

    # (2) FinanceDataReader — KRX/네이버 기반, 국내에서 안정적
    if source in ("auto", "fdr"):
        try:
            import FinanceDataReader as fdr
            df = fdr.DataReader("KS11", start, end)  # KS11 = KOSPI 종합지수
            if df is not None and len(df) > 0:
                s = df["Close"].dropna()
                s.name = "KOSPI"
                print(f"[데이터] FinanceDataReader 사용, {len(s)}일 ({s.index[0].date()} ~ {s.index[-1].date()})")
                return s
        except Exception as e:  # noqa: BLE001
            errors.append(f"FinanceDataReader: {e}")

    # (3) yfinance (^KS11) — 해외 폴백
    if source not in ("auto", "yahoo"):
        raise RuntimeError("데이터 로딩 실패:\n" + "\n".join(f"  - {x}" for x in errors))
    try:
        import yfinance as yf
        df = yf.download("^KS11", start=start, end=end, progress=False, auto_adjust=True)
        if df is not None and len(df) > 0:
            close = df["Close"]
            if isinstance(close, pd.DataFrame):  # 멀티인덱스 컬럼 방어
                close = close.iloc[:, 0]
            s = close.dropna()
            s.name = "KOSPI"
            print(f"[데이터] yfinance 사용, {len(s)}일 ({s.index[0].date()} ~ {s.index[-1].date()})")
            return s
    except Exception as e:  # noqa: BLE001
        errors.append(f"yfinance: {e}")

    raise RuntimeError(
        "KOSPI 데이터를 가져오지 못했습니다. 인터넷(KRX/네이버/야후) 접근이 필요합니다.\n"
        + "\n".join(f"  - {x}" for x in errors)
    )


def demo_series(start, end):
    """데이터 접근이 막힌 환경에서 '차트 형식'만 확인하기 위한 가짜 데이터."""
    idx = pd.bdate_range(start=start, end=end)
    rng = np.random.default_rng(42)
    rets = rng.normal(0.0004, 0.011, len(idx))
    # 몇 번의 인위적 단기 급락 삽입
    for k in (int(len(idx) * 0.45), int(len(idx) * 0.72), int(len(idx) * 0.9)):
        rets[k:k + 5] -= 0.02
    price = 2500 * np.exp(np.cumsum(rets))
    s = pd.Series(price, index=idx, name="KOSPI(DEMO-가짜)")
    return s


# ----------------------------------------------------------------------------
# 2) 이격도 계산
# ----------------------------------------------------------------------------
def disparity(close, window):
    ma = close.rolling(window).mean()
    disp = close / ma * 100.0
    return ma, disp


# ----------------------------------------------------------------------------
# 3) 단기하락 구간 탐지 + 직전 고점에서의 이격도
# ----------------------------------------------------------------------------
def find_short_term_drops(close, disp, lookback=20, drop_pct=4.0):
    """
    국소 고점(지난 lookback일 내 최고가) 이후 일정 기간 내 drop_pct% 이상 하락한 지점을
    '단기하락'으로 보고, 그 고점일의 이격도를 함께 반환.
    """
    rows = []
    n = len(close)
    fwd = 15  # 고점 이후 며칠 안에 하락이 나왔는지 확인할 창
    last_peak_date = None
    for i in range(lookback, n - 1):
        window_max = close.iloc[i - lookback:i + 1].max()
        if close.iloc[i] < window_max - 1e-9:
            continue  # 국소 고점이 아님
        future = close.iloc[i + 1:i + 1 + fwd]
        if len(future) == 0:
            continue
        trough = future.min()
        dd = (trough / close.iloc[i] - 1.0) * 100.0
        if dd <= -drop_pct:
            d = close.index[i]
            # 너무 촘촘한 중복 고점 제거
            if last_peak_date is not None and (d - last_peak_date).days < 10:
                continue
            last_peak_date = d
            rows.append({
                "고점일": d.date(),
                "고점지수": round(float(close.iloc[i]), 2),
                "이격도": round(float(disp.iloc[i]), 2),
                "이후낙폭%": round(float(dd), 2),
            })
    return pd.DataFrame(rows)


# ----------------------------------------------------------------------------
# 4) 차트
# ----------------------------------------------------------------------------
def setup_korean_font():
    import matplotlib
    import matplotlib.pyplot as plt
    matplotlib.rcParams["axes.unicode_minus"] = False
    for cand in ["NanumGothic", "Malgun Gothic", "AppleGothic", "NanumBarunGothic", "Noto Sans CJK KR"]:
        try:
            from matplotlib import font_manager as fm
            if any(cand.lower() in f.name.lower() for f in fm.fontManager.ttflist):
                plt.rcParams["font.family"] = cand
                return True
        except Exception:  # noqa: BLE001
            pass
    return False  # 한글 폰트 없음 -> 영어 라벨 사용


def plot(close, ma, disp, window, drops, out_png, has_korean):
    import matplotlib.pyplot as plt

    def L(ko, en):
        return ko if has_korean else en

    fig, (ax1, ax2) = plt.subplots(
        2, 1, figsize=(13, 9), sharex=True,
        gridspec_kw={"height_ratios": [2, 1]},
    )

    # 상단: 지수 + 이동평균
    ax1.plot(close.index, close.values, color="#222", lw=1.1, label="KOSPI")
    ax1.plot(ma.index, ma.values, color="#d62728", lw=1.3,
             label=L(f"{window}일 이동평균", f"{window}-day MA"))
    ax1.set_title(L(f"KOSPI 종가와 {window}일 이동평균", f"KOSPI Close & {window}-day MA"),
                  fontsize=13, fontweight="bold")
    ax1.legend(loc="upper left")
    ax1.grid(alpha=0.3)

    # 단기하락 고점 표시
    if drops is not None and len(drops) > 0:
        peak_dates = pd.to_datetime(drops["고점일"])
        peak_vals = drops["고점지수"].values
        ax1.scatter(peak_dates, peak_vals, color="#1f77b4", zorder=5, s=35,
                    label=L("단기하락 직전 고점", "pre-drop peak"))

    # 하단: 이격도
    ax2.plot(disp.index, disp.values, color="#2ca02c", lw=1.1,
             label=L(f"{window}일 이격도", f"{window}-day Disparity"))
    ax2.axhline(100, color="#888", lw=1.0, ls="-")
    ax2.axhline(110, color="#d62728", lw=0.9, ls="--",
                label=L("과열 110", "Overbought 110"))
    ax2.axhline(105, color="#ff7f0e", lw=0.8, ls=":")
    ax2.axhline(95, color="#1f77b4", lw=0.8, ls=":")
    ax2.axhline(90, color="#1f77b4", lw=0.9, ls="--",
                label=L("침체 90", "Oversold 90"))
    ax2.fill_between(disp.index, 110, disp.values, where=(disp.values >= 110),
                     color="#d62728", alpha=0.15)
    ax2.fill_between(disp.index, 90, disp.values, where=(disp.values <= 90),
                     color="#1f77b4", alpha=0.15)

    if drops is not None and len(drops) > 0:
        peak_dates = pd.to_datetime(drops["고점일"])
        ax2.scatter(peak_dates, drops["이격도"].values, color="#1f77b4", zorder=5, s=35)

    ax2.set_title(L(f"KOSPI {window}일 이격도 (종가/{window}일MA×100)",
                    f"KOSPI {window}-day Disparity (Close/{window}-MA×100)"),
                  fontsize=12, fontweight="bold")
    ax2.legend(loc="upper left", ncol=2, fontsize=9)
    ax2.grid(alpha=0.3)

    fig.tight_layout()
    fig.savefig(out_png, dpi=130)
    print(f"[저장] {out_png}")


# ----------------------------------------------------------------------------
def main():
    ap = argparse.ArgumentParser(description="KOSPI 50일 이격도 차트/분석")
    ap.add_argument("--ma", type=int, default=50, help="이동평균 기간 (기본 50)")
    ap.add_argument("--years", type=int, default=2, help="조회 기간(년), start 미지정 시 사용")
    ap.add_argument("--start", type=str, default=None)
    ap.add_argument("--end", type=str, default=None)
    ap.add_argument("--drop", type=float, default=4.0, help="단기하락 기준 낙폭%% (기본 4%%)")
    ap.add_argument("--out", type=str, default="kospi_disparity.png")
    ap.add_argument("--source", choices=["auto", "krx", "fdr", "yahoo"], default="auto",
                    help="데이터 소스 (auto=KRX→FDR→Yahoo, krx=한국거래소 직접)")
    ap.add_argument("--demo", action="store_true", help="가짜 데이터로 차트 형식만 미리보기")
    args = ap.parse_args()

    end = pd.Timestamp(args.end) if args.end else pd.Timestamp.today()
    start = pd.Timestamp(args.start) if args.start else end - pd.DateOffset(years=args.years)
    # 이동평균 워밍업 위해 시작일 이전 데이터도 확보
    fetch_start = start - pd.DateOffset(days=int(args.ma * 2.2))

    if args.demo:
        print("[주의] --demo 모드: 아래 결과는 '가짜 데이터'이며 실제 KOSPI가 아닙니다.")
        close_full = demo_series(fetch_start, end)
    else:
        close_full = load_kospi(fetch_start, end, source=args.source)

    ma_full, disp_full = disparity(close_full, args.ma)

    # 표시 구간 자르기
    close = close_full[close_full.index >= start]
    ma = ma_full[ma_full.index >= start]
    disp = disp_full[disp_full.index >= start]

    drops = find_short_term_drops(close, disp, lookback=args.ma // 2, drop_pct=args.drop)

    print("\n=== 현재 상태 ===")
    print(f"최근일: {close.index[-1].date()}  종가: {close.iloc[-1]:,.2f}  "
          f"{args.ma}일선: {ma.iloc[-1]:,.2f}  이격도: {disp.iloc[-1]:.2f}")
    print(f"표시구간 이격도  최소 {disp.min():.2f} / 평균 {disp.mean():.2f} / 최대 {disp.max():.2f}")

    print(f"\n=== 단기하락(직후 {args.drop:.0f}% 이상 하락) 직전 고점의 이격도 ===")
    if len(drops) == 0:
        print("해당 구간에 기준을 충족하는 단기하락 없음.")
    else:
        print(drops.to_string(index=False))
        print(f"\n→ 단기하락 직전 고점 이격도 평균 ≈ {drops['이격도'].mean():.2f} "
              f"(범위 {drops['이격도'].min():.2f} ~ {drops['이격도'].max():.2f})")

    has_korean = setup_korean_font()
    if not has_korean:
        print("[알림] 한글 폰트 미설치 → 차트 라벨은 영어로 표기합니다. "
              "(설치: NanumGothic 등)")
    plot(close, ma, disp, args.ma, drops, args.out, has_korean)


if __name__ == "__main__":
    sys.exit(main())
