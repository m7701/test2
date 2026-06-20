"""KOSPI 50일 이격도(Disparity Index) 차트 생성 스크립트.

이격도(Disparity Index) = (종가 / N일 이동평균) x 100

  - 100  : 주가가 이동평균선과 일치
  - >100 : 주가가 이동평균선 위 (단기 과열 신호)
  - <100 : 주가가 이동평균선 아래 (단기 침체 신호)

데이터 소스
-----------
기본적으로 로컬 CSV(data/kospi.csv)를 사용한다. 이 CSV는 KOSPI 종합지수(^KS11)의
일별 OHLCV 데이터(yfinance 포맷)이다. 네트워크가 가능한 환경이라면
FinanceDataReader 또는 yfinance로 최신 데이터를 받아 --source live 로 쓸 수 있다.
"""

from __future__ import annotations

import argparse
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from matplotlib.font_manager import FontProperties, fontManager
import pandas as pd

BASE = Path(__file__).resolve().parent
FONT_PATH = BASE / "fonts" / "NanumGothic.ttf"
DEFAULT_CSV = BASE / "data" / "kospi.csv"


def setup_korean_font() -> FontProperties:
    """한글 폰트(NanumGothic)를 등록하고 FontProperties 를 반환한다."""
    if FONT_PATH.exists():
        fontManager.addfont(str(FONT_PATH))
        fp = FontProperties(fname=str(FONT_PATH))
        plt.rcParams["font.family"] = fp.get_name()
    else:
        fp = FontProperties()
    plt.rcParams["axes.unicode_minus"] = False  # 음수 부호 깨짐 방지
    return fp


def load_local(csv_path: Path) -> pd.DataFrame:
    """yfinance 멀티헤더 포맷 CSV를 읽어 Date 인덱스와 Close 컬럼을 반환한다."""
    # 1행: Price,Close,High,...  2행: Ticker,^KS11,...  3행: Date,,,...
    df = pd.read_csv(csv_path, skiprows=3, header=None)
    df.columns = ["Date", "Close", "High", "Low", "Open", "Volume"]
    df["Date"] = pd.to_datetime(df["Date"])
    df = df.sort_values("Date").set_index("Date")
    return df[["Close"]].astype(float)


def load_live() -> pd.DataFrame:
    """FinanceDataReader 또는 yfinance 로 최신 KOSPI 데이터를 받는다."""
    try:
        import FinanceDataReader as fdr  # type: ignore
        df = fdr.DataReader("KS11")
        return df[["Close"]].astype(float)
    except Exception:
        import yfinance as yf  # type: ignore
        df = yf.download("^KS11", period="2y", auto_adjust=False)
        df = df[["Close"]]
        df.columns = ["Close"]
        return df.astype(float)


def compute_disparity(df: pd.DataFrame, window: int) -> pd.DataFrame:
    """N일 이동평균과 이격도를 계산한다."""
    df = df.copy()
    df[f"MA{window}"] = df["Close"].rolling(window).mean()
    df["Disparity"] = df["Close"] / df[f"MA{window}"] * 100
    return df


def plot(df: pd.DataFrame, window: int, out_path: Path, fp: FontProperties) -> None:
    ma_col = f"MA{window}"
    plot_df = df.dropna(subset=["Disparity"])

    fig, (ax1, ax2) = plt.subplots(
        2, 1, figsize=(13, 9), sharex=True,
        gridspec_kw={"height_ratios": [2, 1.3]},
    )

    # --- 상단: KOSPI 지수 + 이동평균선 ---
    ax1.plot(df.index, df["Close"], color="#1f4e79", lw=1.4, label="KOSPI 종가")
    ax1.plot(df.index, df[ma_col], color="#e07b00", lw=1.4,
             label=f"{window}일 이동평균")
    ax1.set_title(f"KOSPI 종합지수와 {window}일 이격도(Disparity Index)",
                  fontproperties=fp, fontsize=16, pad=12)
    ax1.set_ylabel("지수", fontproperties=fp, fontsize=11)
    ax1.legend(prop=fp, loc="upper left", framealpha=0.9)
    ax1.grid(True, alpha=0.3)

    # --- 하단: 이격도 ---
    ax2.plot(plot_df.index, plot_df["Disparity"], color="#9b1c31", lw=1.4,
             label=f"{window}일 이격도")
    ax2.axhline(100, color="black", lw=1.0, ls="-", alpha=0.7)
    ax2.axhline(105, color="#c44", lw=0.9, ls="--", alpha=0.7)
    ax2.axhline(95, color="#268", lw=0.9, ls="--", alpha=0.7)
    ax2.fill_between(plot_df.index, 100, plot_df["Disparity"],
                     where=plot_df["Disparity"] >= 100,
                     color="#c44", alpha=0.12)
    ax2.fill_between(plot_df.index, 100, plot_df["Disparity"],
                     where=plot_df["Disparity"] < 100,
                     color="#268", alpha=0.12)

    # 과열(105)/침체(95) 기준선 주석
    ax2.text(plot_df.index[1], 105.15, "과열 기준 105", fontproperties=fp,
             fontsize=9, color="#c44", va="bottom")
    ax2.text(plot_df.index[1], 94.85, "침체 기준 95", fontproperties=fp,
             fontsize=9, color="#268", va="top")

    ax2.set_ylabel("이격도 (%)", fontproperties=fp, fontsize=11)
    ax2.set_xlabel("날짜", fontproperties=fp, fontsize=11)
    ax2.legend(prop=fp, loc="upper left", framealpha=0.9)
    ax2.grid(True, alpha=0.3)

    ax2.xaxis.set_major_locator(mdates.MonthLocator(interval=1))
    ax2.xaxis.set_major_formatter(mdates.DateFormatter("%Y-%m"))
    fig.autofmt_xdate(rotation=45)

    # 최근값 표기
    last = plot_df.iloc[-1]
    ax2.annotate(f"{last['Disparity']:.1f}",
                 xy=(plot_df.index[-1], last["Disparity"]),
                 xytext=(8, 0), textcoords="offset points",
                 fontproperties=fp, fontsize=10, fontweight="bold",
                 color="#9b1c31", va="center")

    period = f"{df.index[0].date()} ~ {df.index[-1].date()}"
    fig.text(0.99, 0.01, f"기간: {period}  |  이격도 = 종가 / {window}일 이동평균 x 100",
             fontproperties=fp, fontsize=9, color="gray", ha="right")

    fig.tight_layout(rect=(0, 0.02, 1, 1))
    fig.savefig(out_path, dpi=150, bbox_inches="tight")
    print(f"저장 완료: {out_path}")
    print(f"기간: {period}")
    print(f"최근 종가: {df['Close'].iloc[-1]:.2f}, "
          f"{window}일 이동평균: {df[ma_col].iloc[-1]:.2f}, "
          f"이격도: {last['Disparity']:.2f}")


def main() -> None:
    parser = argparse.ArgumentParser(description="KOSPI 이격도 차트 생성")
    parser.add_argument("--window", type=int, default=50, help="이동평균 기간 (기본 50)")
    parser.add_argument("--source", choices=["local", "live"], default="local",
                        help="데이터 소스 (local: data/kospi.csv, live: 온라인 조회)")
    parser.add_argument("--csv", type=Path, default=DEFAULT_CSV, help="로컬 CSV 경로")
    parser.add_argument("--out", type=Path, default=BASE / "kospi_disparity.png",
                        help="출력 PNG 경로")
    args = parser.parse_args()

    fp = setup_korean_font()
    df = load_live() if args.source == "live" else load_local(args.csv)
    df = compute_disparity(df, args.window)
    plot(df, args.window, args.out, fp)


if __name__ == "__main__":
    main()
