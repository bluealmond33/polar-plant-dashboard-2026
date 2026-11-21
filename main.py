import html
import io
import re

import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st
from plotly.subplots import make_subplots

# ═════════════════════════════════════════════
# 기본 설정
# ═════════════════════════════════════════════
st.set_page_config(
    page_title="극지식물 생중량, 무엇이 결정할까?",
    page_icon="🧊",
    layout="wide",
)

# 디자인 팔레트 — 극지(Polar): 빙하 블루 · 오로라 · 극야 네이비
INK = "#0B1E33"
MUTED = "#5E7389"
LINE = "#DCE6EF"
BG = "#EEF4F9"
CARD = "#FFFFFF"
ACCENT = "#1287A8"
ACCENT_SOFT = "#E0F1F7"
AURORA = "#5FE0C8"
WARM = "#F08A4B"
WARM_SOFT = "#FDEDE3"
NEUTRAL = "#C9D6E2"
BLUE = "#7468E8"
FONT_FAMILY = "Pretendard Variable, Pretendard, Noto Sans KR, Malgun Gothic, Apple SD Gothic Neo, sans-serif"

st.markdown(
    f"""
<style>
@import url('https://cdn.jsdelivr.net/gh/orioncactus/pretendard@v1.3.9/dist/web/variable/pretendardvariable-dynamic-subset.min.css');
@import url('https://fonts.googleapis.com/css2?family=Noto+Sans+KR:wght@400;500;700&display=swap');

html, body, [class*="css"], .stApp, button, input, textarea {{
    font-family: 'Pretendard Variable', Pretendard, 'Noto Sans KR', 'Malgun Gothic', sans-serif;
}}
.stApp {{
    color: {INK};
    background:
        radial-gradient(1200px 500px at 85% -10%, rgba(95,224,200,0.18), transparent 60%),
        radial-gradient(900px 500px at 0% 0%, rgba(116,104,232,0.10), transparent 55%),
        linear-gradient(180deg, #E6F0F8 0%, {BG} 35%, #F5F9FC 100%);
    background-attachment: fixed;
}}
[data-testid="stHeader"] {{ background: transparent; }}
.block-container {{ padding: 2rem 3.2rem 4rem; max-width: 1640px; }}

/* ── 사이드바 (얼음판) ── */
[data-testid="stSidebar"] {{ background: rgba(255,255,255,0.72); backdrop-filter: blur(14px);
    border-right: 1px solid {LINE}; }}
[data-testid="stSidebar"] * {{ color: {INK}; }}
.side-brand {{ font-size: 15px; font-weight: 800; letter-spacing: -0.02em; margin: 4px 0 4px; }}
.side-brand span {{ color: {ACCENT}; }}
.side-label {{ font-size: 11px; font-weight: 700; letter-spacing: .16em; color: {MUTED}; margin: 22px 0 6px; }}
.side-note {{ font-size: 12.5px; line-height: 1.7; color: {MUTED}; background: linear-gradient(135deg, {ACCENT_SOFT}, #F1EFFD);
    border-radius: 16px; padding: 14px 16px; margin-top: 14px; }}
.side-note b {{ color: {INK}; }}
[data-testid="stFileUploaderDropzone"] {{ background: rgba(238,244,249,0.9); border: 1.5px dashed {NEUTRAL}; border-radius: 16px; }}

/* ── 히어로 (북극의 밤: 오로라 · 눈 · 빙산) ── */
.hero {{ position: relative; overflow: hidden; border-radius: 32px; padding: 60px 60px 120px; margin-bottom: 28px;
    background: linear-gradient(180deg, #030B17 0%, #071A30 45%, #0D2A4A 80%, #16406A 100%);
    box-shadow: 0 30px 70px rgba(7,26,48,0.30); }}
.aurora {{ position: absolute; inset: -20% -10% 30% -10%; pointer-events: none; filter: blur(28px); opacity: .9;
    background:
        radial-gradient(40% 55% at 70% 40%, rgba(95,224,200,0.75), transparent 70%),
        radial-gradient(30% 45% at 88% 30%, rgba(116,104,232,0.70), transparent 70%),
        radial-gradient(35% 40% at 48% 20%, rgba(56,189,248,0.55), transparent 70%),
        radial-gradient(25% 35% at 30% 35%, rgba(95,224,200,0.30), transparent 70%);
    animation: aurora 16s ease-in-out infinite alternate; }}
@keyframes aurora {{
    0%   {{ transform: translateX(-4%) skewX(-6deg) scaleY(1); opacity: .75; }}
    50%  {{ transform: translateX(3%) skewX(4deg) scaleY(1.12); opacity: 1; }}
    100% {{ transform: translateX(-2%) skewX(-2deg) scaleY(0.95); opacity: .8; }} }}
.stars {{ position: absolute; inset: 0; pointer-events: none; opacity: .7;
    background-image:
        radial-gradient(1.3px 1.3px at 12% 18%, #fff, transparent), radial-gradient(1px 1px at 24% 52%, #fff, transparent),
        radial-gradient(1.5px 1.5px at 41% 12%, #fff, transparent), radial-gradient(1px 1px at 57% 44%, #fff, transparent),
        radial-gradient(1.2px 1.2px at 66% 8%, #fff, transparent), radial-gradient(1px 1px at 81% 22%, #fff, transparent),
        radial-gradient(1.4px 1.4px at 93% 10%, #fff, transparent), radial-gradient(1px 1px at 6% 40%, #fff, transparent),
        radial-gradient(1.2px 1.2px at 34% 30%, #fff, transparent); }}
.snow {{ position: absolute; left: 0; right: 0; top: -300px; bottom: 0; pointer-events: none; background-repeat: repeat; }}
.snow.s1 {{ background-size: 300px 300px; opacity: .9; animation: fall 22s linear infinite;
    background-image:
        radial-gradient(2.2px 2.2px at 20px 30px, #fff, transparent), radial-gradient(1.6px 1.6px at 90px 140px, #fff, transparent),
        radial-gradient(2.4px 2.4px at 160px 60px, #fff, transparent), radial-gradient(1.8px 1.8px at 230px 200px, #fff, transparent),
        radial-gradient(2px 2px at 280px 110px, #fff, transparent), radial-gradient(1.5px 1.5px at 130px 250px, #fff, transparent); }}
.snow.s2 {{ background-size: 200px 200px; opacity: .55; animation: fall2 14s linear infinite;
    background-image:
        radial-gradient(1.2px 1.2px at 40px 50px, #fff, transparent), radial-gradient(1px 1px at 120px 20px, #fff, transparent),
        radial-gradient(1.3px 1.3px at 170px 130px, #fff, transparent), radial-gradient(1px 1px at 70px 170px, #fff, transparent); }}
@keyframes fall  {{ from {{ transform: translate(0, 0); }} to {{ transform: translate(-40px, 300px); }} }}
@keyframes fall2 {{ from {{ transform: translate(0, 0); }} to {{ transform: translate(30px, 200px); }} }}
.berg {{ position: absolute; left: 0; right: 0; bottom: 0; pointer-events: none; }}
.berg.b1 {{ height: 120px; background: linear-gradient(180deg, #5C88B3, #2E557F);  opacity: .55;
    clip-path: polygon(0 100%, 0 70%, 6% 52%, 11% 64%, 19% 22%, 25% 40%, 31% 30%, 38% 62%, 46% 45%, 53% 58%, 61% 18%, 66% 34%, 72% 28%, 79% 60%, 86% 38%, 93% 52%, 100% 40%, 100% 100%); }}
.berg.b2 {{ height: 78px; background: linear-gradient(180deg, #F4FAFF 0%, #CFE3F2 45%, #9DC1DD 100%);
    clip-path: polygon(0 100%, 0 62%, 8% 40%, 13% 55%, 22% 30%, 30% 58%, 41% 46%, 48% 64%, 57% 34%, 63% 50%, 70% 26%, 78% 54%, 88% 36%, 95% 56%, 100% 44%, 100% 100%); }}
.berg.b3 {{ height: 22px; background: linear-gradient(180deg, rgba(238,244,249,0.0), {BG}); }}
.hero-c {{ position: relative; z-index: 2; }}
.eyebrow {{ display: inline-flex; align-items: center; gap: 10px; font-size: 12px; font-weight: 700;
    letter-spacing: .22em; color: {AURORA}; text-transform: uppercase; }}
.eyebrow .pin {{ padding: 4px 10px; border-radius: 999px; background: rgba(95,224,200,0.12);
    border: 1px solid rgba(95,224,200,0.35); letter-spacing: .12em; }}
.hero-title {{ font-size: clamp(42px, 4.4vw, 68px); font-weight: 800; line-height: 1.08;
    letter-spacing: -0.045em; color: #fff; margin: 20px 0 14px; text-shadow: 0 4px 30px rgba(0,0,0,0.35); }}
.hero-title span {{ background: linear-gradient(90deg, {AURORA}, #8EC5FF 55%, #B4A8FF);
    -webkit-background-clip: text; background-clip: text; color: transparent; }}
.hero-sub {{ font-size: 18px; color: rgba(235,245,255,0.75); letter-spacing: -0.01em; }}
.hero-tags {{ display: flex; gap: 10px; margin-top: 28px; flex-wrap: wrap; }}
.hero-tag {{ font-size: 13px; font-weight: 600; color: rgba(255,255,255,0.92); padding: 8px 15px; border-radius: 999px;
    background: rgba(255,255,255,0.08); border: 1px solid rgba(255,255,255,0.18); backdrop-filter: blur(8px); }}
.bear {{ position: absolute; right: 7%; bottom: 52px; z-index: 2; font-size: 46px; filter: drop-shadow(0 6px 10px rgba(0,0,0,.25)); }}
@media (prefers-reduced-motion: reduce) {{ .aurora, .snow {{ animation: none; }} }}

/* ── 탭 (알약 모양) ── */
.stTabs [role="tablist"] {{ gap: 6px; background: rgba(255,255,255,0.85); padding: 6px; border-radius: 999px;
    border: 1px solid {LINE}; width: fit-content; box-shadow: 0 6px 20px rgba(11,30,51,0.05); }}
.stTabs [role="tab"] {{ height: 44px; padding: 0 26px; border-radius: 999px; background: transparent;
    border: none; display: flex; align-items: center; cursor: pointer; }}
.stTabs [role="tab"] p {{ font-weight: 600; font-size: 15px; color: {MUTED}; }}
.stTabs [role="tab"][aria-selected="true"] {{ background: linear-gradient(135deg, #0B1E33, #13385E) !important; }}
.stTabs [role="tab"][aria-selected="true"] p {{ color: #fff !important; }}
.stTabs [data-baseweb="tab-highlight"], .stTabs [data-baseweb="tab-border"],
.stTabs .react-aria-SelectionIndicator {{ display: none !important; }}
.stTabs [role="tabpanel"] {{ padding-top: 26px; }}

/* ── 스테퍼 ── */
.stepper {{ display: flex; align-items: center; gap: 10px; margin-bottom: 26px; font-size: 13.5px; color: {MUTED}; }}
.step {{ display: flex; align-items: center; gap: 8px; font-weight: 600; }}
.dot {{ width: 28px; height: 28px; border-radius: 50%; display: grid; place-items: center; font-size: 12px;
    background: #fff; border: 1px solid {LINE}; color: {MUTED}; }}
.step.on {{ color: {INK}; }}
.step.on .dot {{ background: linear-gradient(135deg, {ACCENT}, {BLUE}); border-color: transparent; color: #fff;
    box-shadow: 0 0 0 5px rgba(18,135,168,0.14); }}
.step.done .dot {{ background: {ACCENT_SOFT}; border-color: {ACCENT_SOFT}; color: {ACCENT}; }}
.bar {{ flex: 0 0 44px; height: 1px; background: {NEUTRAL}; }}

/* ── 섹션 제목 ── */
.sec {{ margin: 44px 0 16px; }}
.sec-k {{ font-size: 11.5px; font-weight: 700; letter-spacing: .18em; color: {ACCENT}; }}
.sec .sec-k::before {{ content: "❄  "; letter-spacing: 0; }}
.sec-t {{ font-size: 28px; font-weight: 800; letter-spacing: -0.035em; color: {INK}; margin-top: 6px; }}
.sec-d {{ font-size: 15px; color: {MUTED}; margin-top: 6px; line-height: 1.6; }}

/* ── 공통 카드 (얼음 유리) ── */
.callout, [data-testid="stMetric"], [data-testid="stPlotlyChart"], [data-testid="stExpander"] {{
    background: rgba(255,255,255,0.82); border: 1px solid rgba(255,255,255,0.95);
    box-shadow: 0 10px 30px rgba(11,30,51,0.06), inset 0 0 0 1px {LINE}, inset 0 2px 0 rgba(255,255,255,1);
    backdrop-filter: blur(10px); }}

.callout {{ border-radius: 22px; padding: 24px 26px; height: 100%; }}
.callout .lb {{ font-size: 11.5px; font-weight: 700; letter-spacing: .16em; margin-bottom: 10px; color: {MUTED}; }}
.callout .bd {{ font-size: 18px; font-weight: 600; line-height: 1.6; letter-spacing: -0.02em; color: {INK}; }}
.callout.accent {{ background: linear-gradient(135deg, #E0F3F9, #E9F8F4); }}
.callout.accent .lb {{ color: {ACCENT}; }}
.callout.warm {{ background: linear-gradient(135deg, #FDEDE3, #FFF5EE); }}
.callout.warm .lb {{ color: {WARM}; }}
.callout.ink {{ position: relative; overflow: hidden; border: none;
    background:
        radial-gradient(500px 200px at 90% 0%, rgba(95,224,200,0.35), transparent 60%),
        radial-gradient(400px 200px at 100% 100%, rgba(116,104,232,0.40), transparent 60%),
        linear-gradient(135deg, #071526, #0B1E33 60%, #10294A);
    box-shadow: 0 20px 50px rgba(11,30,51,0.22); padding: 34px 36px; }}
.callout.ink .lb, .callout.ink .bd {{ position: relative; z-index: 1; }}
.callout.ink .lb {{ color: {AURORA}; }}
.callout.ink .bd {{ color: #fff; font-size: 23px; line-height: 1.55; }}
.callout.ink b {{ color: {AURORA}; }}
.note {{ font-size: 13.5px; color: {MUTED}; line-height: 1.75; margin: 8px 2px 0; }}
.note b {{ color: {INK}; }}
.next {{ margin-top: 44px; padding: 20px 24px; border-radius: 18px; border: 1px dashed {NEUTRAL};
    background: rgba(255,255,255,0.5); color: {MUTED}; font-weight: 600; font-size: 15px; }}
.next b {{ color: {ACCENT}; }}
.chips {{ display: flex; gap: 16px; font-size: 13px; color: {MUTED}; margin: 2px 0 10px; }}
.chip::before {{ content: ""; display: inline-block; width: 10px; height: 10px; border-radius: 3px;
    margin-right: 6px; vertical-align: -1px; background: var(--c); }}

/* ── 지표 카드 ── */
[data-testid="stMetric"] {{ border-radius: 20px; padding: 18px 22px; }}
[data-testid="stMetricLabel"] p {{ font-size: 13px; color: {MUTED}; font-weight: 600; }}
[data-testid="stMetricValue"] {{ font-size: 32px; font-weight: 800; letter-spacing: -0.03em; color: {INK}; }}

/* ── 그래프·표·기타 ── */
[data-testid="stPlotlyChart"] {{ border-radius: 24px; padding: 16px 16px 16px; overflow: hidden; }}
[data-testid="stDataFrame"] {{ border-radius: 16px; overflow: hidden; border: 1px solid {LINE}; background: #fff; }}
[data-testid="stExpander"] {{ border-radius: 18px; }}
[data-testid="stAlert"] {{ border-radius: 16px; border: none; }}
.stDownloadButton button {{ background: linear-gradient(135deg, #0B1E33, #13385E); color: #fff; border: none;
    border-radius: 999px; padding: 11px 24px; font-weight: 600; box-shadow: 0 8px 20px rgba(11,30,51,0.18); }}
.stDownloadButton button:hover {{ background: linear-gradient(135deg, {ACCENT}, {BLUE}); color: #fff; }}
[data-testid="stSlider"] [role="group"] {{ filter: hue-rotate(195deg) saturate(0.85); }}
hr {{ border-color: {LINE} !important; }}
</style>
""",
    unsafe_allow_html=True,
)


# ═════════════════════════════════════════════
# 화면 구성 도우미 (HTML 조각)
# ═════════════════════════════════════════════
def md(text):
    st.markdown(text, unsafe_allow_html=True)


def section(kicker, title, desc=""):
    d = f'<div class="sec-d">{desc}</div>' if desc else ""
    md(f'<div class="sec"><div class="sec-k">{kicker}</div><div class="sec-t">{title}</div>{d}</div>')


def callout(label, body, kind=""):
    fx = '<div class="snow s1"></div><div class="snow s2"></div>' if kind == "ink" else ""
    md(f'<div class="callout {kind}">{fx}<div class="lb">{label}</div><div class="bd">{body}</div></div>')


def note(text):
    md(f'<div class="note">{text}</div>')


def stepper(active):
    names = ["가설", "검증", "발견"]
    parts = []
    for i, n in enumerate(names):
        cls = "on" if i == active else ("done" if i < active else "")
        mark = "✓" if i < active else str(i + 1)
        parts.append(f'<div class="step {cls}"><div class="dot">{mark}</div>{n}</div>')
        if i < len(names) - 1:
            parts.append('<div class="bar"></div>')
    md(f'<div class="stepper">{"".join(parts)}</div>')


def style(fig, height=380, title=""):
    # 모든 그래프에 같은 미니멀 스타일 적용 (width는 넣지 않음)
    layout = dict(
        template="plotly_white",
        font=dict(family=FONT_FAMILY, color=INK, size=13),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        height=height,
        margin=dict(t=54 if title else 14, l=6, r=6, b=16),
        hoverlabel=dict(bgcolor="white", bordercolor=LINE, font=dict(family=FONT_FAMILY, color=INK)),
    )
    if title:
        layout["title"] = dict(text=title, x=0.01, xanchor="left", font=dict(size=15, color=INK))
    fig.update_layout(**layout)
    fig.update_xaxes(showgrid=False, zeroline=False, linecolor=LINE, tickcolor=LINE,
                     tickfont=dict(color=MUTED), title_font=dict(color=MUTED, size=12))
    fig.update_yaxes(gridcolor="#E6EEF5", zeroline=False, linecolor="rgba(0,0,0,0)",
                     tickfont=dict(color=MUTED), title_font=dict(color=MUTED, size=12))
    return fig


# ═════════════════════════════════════════════
# 데이터 읽기 · 열 이름 표준화
# ═════════════════════════════════════════════
def read_csv_bytes(data):
    for enc in ("utf-8-sig", "cp949"):
        try:
            return pd.read_csv(io.BytesIO(data), encoding=enc)
        except Exception:
            pass
    return pd.DataFrame()


def std_cols(df):
    df = df.copy()
    df.columns = [str(c).strip() for c in df.columns]
    rename = {}
    for c in df.columns:
        k = c.lower().replace(" ", "")
        if k in ("time", "categories", "시간", "날짜", "datetime", "date"):
            rename[c] = "time"
        elif k in ("temperature", "온도"):
            rename[c] = "temperature"
        elif k in ("humidity", "습도"):
            rename[c] = "humidity"
        elif k == "ph":
            rename[c] = "ph"
        elif k == "ec":
            rename[c] = "ec"
        elif "생중량" in k:
            rename[c] = "생중량"
        elif "잎" in k:
            rename[c] = "잎 수"
        elif "지상부" in k and "길이" in k:
            rename[c] = "지상부 길이"
        elif "지하부" in k and "길이" in k:
            rename[c] = "지하부 길이"
        elif "지상부" in k and ("질량" in k or "무게" in k):
            rename[c] = "지상부 질량"
        elif "지하부" in k and ("질량" in k or "무게" in k):
            rename[c] = "지하부 질량"
        elif "개체" in k:
            rename[c] = "개체번호"
    df = df.rename(columns=rename)
    for c in df.columns:
        if c in ("time", "개체번호"):
            continue
        if not pd.api.types.is_numeric_dtype(df[c]):
            num = pd.to_numeric(df[c].astype(str).str.replace(",", "").str.extract(r"(-?\d+\.?\d*)")[0], errors="coerce")
            if num.notna().mean() >= 0.5:
                df[c] = num
    if "생중량" not in df.columns and {"지상부 질량", "지하부 질량"} <= set(df.columns):
        df["생중량"] = df["지상부 질량"] + df["지하부 질량"]
    if "time" in df.columns:
        t = df["time"].astype(str).str.strip()
        parsed = pd.to_datetime(t, errors="coerce", format="mixed")
        bad = parsed.isna() & t.str.match(r"^\d{8}_\d{1,2}$")
        if bad.any():
            parts = t[bad].str.split("_", expand=True)
            parsed[bad] = pd.to_datetime(parts[0], format="%Y%m%d") + pd.to_timedelta(parts[1].astype(int), unit="h")
        df["time"] = parsed
    return df


@st.cache_data
def load_data(data):
    raw = read_csv_bytes(data)
    if raw.empty:
        return raw
    return std_cols(raw)


def school_name(file):
    # 파일명 앞부분(첫 '_' 앞)을 학교명으로 사용
    if file is None:
        return ""
    stem = re.sub(r"\.csv$", "", str(file.name), flags=re.IGNORECASE)
    return re.split(r"[_\-\s]", stem)[0]


def id_label(v):
    # 개체번호를 원래 모양(56, A1)으로 표시
    if isinstance(v, (float, np.floating)) and float(v).is_integer():
        return str(int(v))
    return str(v)


# ═════════════════════════════════════════════
# 통계 도우미 함수
# ═════════════════════════════════════════════
def pair_values(df, x, y):
    if x not in df.columns or y not in df.columns:
        return None
    sub = df[[x, y]].apply(pd.to_numeric, errors="coerce").dropna()
    if len(sub) < 3 or sub[x].nunique() < 2 or sub[y].nunique() < 2:
        return None
    return sub


def pearson(df, x, y):
    sub = pair_values(df, x, y)
    if sub is None:
        return None
    return float(np.corrcoef(sub[x], sub[y])[0, 1])


def strength(r):
    a = abs(r)
    if a >= 0.7:
        return "강함"
    if a >= 0.4:
        return "보통"
    return "약함"


def add_trend(fig, sub, x, y, row=None, col=None, color=WARM):
    a, b = np.polyfit(sub[x], sub[y], 1)
    xs = np.linspace(sub[x].min(), sub[x].max(), 50)
    trace = go.Scatter(
        x=xs, y=a * xs + b, mode="lines",
        line=dict(color=color, width=2.5),
        name="추세선", showlegend=False, hoverinfo="skip",
    )
    if row is None:
        fig.add_trace(trace)
    else:
        fig.add_trace(trace, row=row, col=col)
    return a, b


def scatter_with_trend(df, x, y, color=ACCENT, title=""):
    sub = pair_values(df, x, y)
    if sub is None:
        return None, None, None
    hover = df.loc[sub.index, "개체번호"].map(id_label) if "개체번호" in df.columns else sub.index.astype(str)
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=sub[x], y=sub[y], mode="markers",
        marker=dict(size=11, color=color, opacity=0.78, line=dict(width=1.5, color="white")),
        text=hover, hovertemplate="<b>개체 %{text}</b><br>" + x + " %{x}<br>" + y + " %{y}<extra></extra>",
        showlegend=False,
    ))
    a, b = add_trend(fig, sub, x, y)
    r = float(np.corrcoef(sub[x], sub[y])[0, 1])
    style(fig, height=420, title=title)
    fig.update_layout(xaxis_title=x, yaxis_title=y)
    return fig, r, (a, b)


UNITS = {"생중량": "g", "잎 수": "장", "지상부 길이": "mm", "지하부 길이": "mm", "지상부 질량": "g", "지하부 질량": "g"}
EXCLUDE = {"time", "개체번호", "생중량", "지상부 질량", "지하부 질량"}


def growth_candidates(df):
    return [c for c in df.columns if c not in EXCLUDE and pd.api.types.is_numeric_dtype(df[c]) and df[c].notna().sum() >= 3]


# ═════════════════════════════════════════════
# 사이드바 · 데이터 업로드 (맨 위에서 한 번만 읽기)
# ═════════════════════════════════════════════
with st.sidebar:
    md('<div class="side-brand">🐻‍❄️ Arctic Plant <span>Lab</span></div>')
    md('<div class="side-label">DATA</div>')
    env_file = st.file_uploader("환경 데이터 CSV", type="csv")
    growth_file = st.file_uploader("생육 결과 데이터 CSV", type="csv")

env_df = pd.DataFrame()
growth_df = pd.DataFrame()
with st.spinner("데이터를 읽는 중이에요..."):
    if env_file is not None:
        env_df = load_data(env_file.getvalue())
    if growth_file is not None:
        growth_df = load_data(growth_file.getvalue())

school = school_name(growth_file) or school_name(env_file) or "우리 학교"

candidates = growth_candidates(growth_df) if not growth_df.empty else []
explore_col = None
with st.sidebar:
    if candidates:
        md('<div class="side-label">EXPLORE</div>')
        default_idx = candidates.index("잎 수") if "잎 수" in candidates else 0
        explore_col = st.selectbox("생중량과 비교할 생육 항목 (3막 직접 탐색)", candidates, index=default_idx)
    md(
        '<div class="side-note"><b>상관계수 r</b> — -1~1 사이 값. 1에 가까울수록 한쪽이 커질 때 다른 쪽도 함께 커지는 관계가 강해요.'
        '<br><br><b>결정계수 R²</b> — r을 제곱한 값. 한 항목이 다른 항목의 차이를 몇 % 설명하는지 알려 줘요.</div>'
    )

# ═════════════════════════════════════════════
# 히어로
# ═════════════════════════════════════════════
tags = []
if not growth_df.empty:
    tags.append(f"🌱 {len(growth_df)}개체")
if "time" in env_df.columns and env_df["time"].notna().sum() >= 2:
    tt = env_df["time"].dropna()
    tags.append(f"🗓 {tt.min():%Y.%m.%d} – {tt.max():%Y.%m.%d}")
if "temperature" in env_df.columns and env_df["temperature"].notna().any():
    tags.append(f"🌡 평균 {env_df['temperature'].dropna().mean():.1f}°C")
tags.append("📊 가설 → 검증 → 발견")
hero_tags = "".join(f'<span class="hero-tag">{t}</span>' for t in tags)
md(
    '<div class="hero"><div class="aurora"></div><div class="stars"></div>'
    '<div class="snow s1"></div><div class="snow s2"></div>'
    '<div class="berg b1"></div><div class="berg b2"></div><div class="berg b3"></div>'
    '<div class="bear">🐻‍❄️</div>'
    f'<div class="hero-c"><div class="eyebrow">❄ Arctic Plant Lab <span class="pin">{html.escape(school)}</span></div>'
    '<div class="hero-title">극지식물 생중량,<br><span>무엇이</span> 결정할까?</div>'
    '<div class="hero-sub">같은 스마트팜, 다른 성장 — 북극에서 온 식물들의 개체별 생육 차이 분석</div>'
    f'<div class="hero-tags">{hero_tags}</div></div></div>'
)

if env_file is None and growth_file is None:
    st.info("왼쪽 사이드바에서 환경 데이터 CSV와 생육 결과 데이터 CSV를 올려 주세요. 한 파일만 올려도 해당 부분은 볼 수 있어요.")

has_growth = (not growth_df.empty) and ("생중량" in growth_df.columns)

tab1, tab2, tab3 = st.tabs(["01  가설", "02  검증", "03  발견"])

# ═════════════════════════════════════════════
# 탭1: 우리의 가설
# ═════════════════════════════════════════════
with tab1:
    try:
        stepper(0)
        c1, c2 = st.columns(2, gap="medium")
        with c1:
            callout("RESEARCH QUESTION", "같은 스마트팜에서 같은 기간 자란 식물들,<br>생중량 차이는 얼마나 크고 무엇으로 설명될까?")
        with c2:
            callout("OUR HYPOTHESIS", "지상부 길이와 지하부 길이는 강한 상관관계를 가지고, 두 길이는 생중량을 잘 설명할 것이다.", "accent")

        section("OVERVIEW", "실험 개요")
        m1, m2, m3, m4 = st.columns(4)
        m1.metric("개체 수", f"{len(growth_df)}개" if not growth_df.empty else "—")
        if "time" in env_df.columns and env_df["time"].notna().sum() >= 2:
            t = env_df["time"].dropna()
            m2.metric("측정 기간", f"{(t.max().normalize() - t.min().normalize()).days + 1}일")
        else:
            m2.metric("측정 기간", "—")
        if "temperature" in env_df.columns and env_df["temperature"].notna().any():
            m3.metric("평균 온도", f"{env_df['temperature'].dropna().mean():.1f}°C")
        else:
            m3.metric("평균 온도", "—")
        if "humidity" in env_df.columns and env_df["humidity"].notna().any():
            m4.metric("평균 습도", f"{env_df['humidity'].dropna().mean():.1f}%")
        else:
            m4.metric("평균 습도", "—")

        section("FRESH WEIGHT", "같은 스마트팜, 생중량은 얼마나 달랐을까?")
        if growth_file is None:
            st.info("생육 결과 데이터 CSV를 올리면 개체별 생중량 비교가 나타나요.")
        elif not has_growth:
            st.info("생육 데이터에서 생중량(또는 지상부·지하부 질량) 열을 찾지 못했어요.")
        else:
            w = growth_df["생중량"].dropna()
            if len(w) < 2:
                st.info("생중량 값이 2개 미만이라 비교할 수 없어요.")
            else:
                k1, k2, k3 = st.columns(3)
                k1.metric("가장 가벼운 개체", f"{w.min():.2f} g")
                k2.metric("가장 무거운 개체", f"{w.max():.2f} g")
                if w.min() > 0:
                    k3.metric("개체 간 차이", f"{w.max() / w.min():.0f}배")
                else:
                    k3.metric("개체 간 차이", f"{w.max() - w.min():.2f} g")

                bar = growth_df.loc[w.index].copy()
                bar["라벨"] = bar["개체번호"].map(id_label) if "개체번호" in bar.columns else (bar.index + 1).astype(str)
                bar = bar.sort_values("생중량", ascending=False).reset_index(drop=True)
                n_hi = min(5, len(bar) // 2)
                colors = []
                for i in range(len(bar)):
                    if i < n_hi:
                        colors.append(ACCENT)
                    elif i >= len(bar) - n_hi:
                        colors.append(WARM)
                    else:
                        colors.append(NEUTRAL)
                md(f'<div class="chips"><span class="chip" style="--c:{ACCENT}">상위 {n_hi}개체</span>'
                   f'<span class="chip" style="--c:{WARM}">하위 {n_hi}개체</span>'
                   f'<span class="chip" style="--c:{BLUE}">평균선</span></div>')
                fig = go.Figure(go.Bar(
                    x=bar["라벨"], y=bar["생중량"], marker_color=colors,
                    hovertemplate="<b>개체 %{x}</b><br>생중량 %{y:.2f} g<extra></extra>",
                ))
                fig.add_hline(y=w.mean(), line_dash="dot", line_color=BLUE, line_width=1.5,
                              annotation_text=f"평균 {w.mean():.2f} g", annotation_position="top left",
                              annotation_font_color=BLUE)
                style(fig, height=400, title="개체별 생중량")
                fig.update_layout(xaxis=dict(type="category", title="개체번호"), yaxis_title="생중량 (g)",
                                  bargap=0.25, barcornerradius=4)
                st.plotly_chart(fig, width="stretch")

                fig = px.histogram(bar, x="생중량", nbins=min(15, max(5, len(bar) // 4)),
                                   color_discrete_sequence=[ACCENT])
                fig.add_vline(x=w.mean(), line_dash="dash", line_color=WARM, line_width=1.5)
                fig.add_vline(x=w.median(), line_dash="dot", line_color=BLUE, line_width=1.5)
                right_is_mean = w.mean() >= w.median()
                fig.add_annotation(x=w.mean(), y=1, yref="paper", showarrow=False, yanchor="bottom",
                                   xanchor="left" if right_is_mean else "right", xshift=6 if right_is_mean else -6,
                                   text=f"평균 {w.mean():.2f}", font=dict(color=WARM, size=12))
                fig.add_annotation(x=w.median(), y=1, yref="paper", showarrow=False, yanchor="bottom",
                                   xanchor="right" if right_is_mean else "left", xshift=-6 if right_is_mean else 6,
                                   text=f"중앙값 {w.median():.2f}", font=dict(color=BLUE, size=12))
                style(fig, height=380, title="생중량 분포")
                fig.update_traces(marker_line_color="white", marker_line_width=1.5, opacity=0.9)
                fig.update_layout(xaxis_title="생중량 (g)", yaxis_title="개체 수", bargap=0.04, barcornerradius=4)
                h1, h2 = st.columns([2.2, 1], gap="medium")
                with h1:
                    st.plotly_chart(fig, width="stretch")
                with h2:
                    st.metric("평균", f"{w.mean():.2f} g")
                    st.metric("중앙값", f"{w.median():.2f} g")
                    st.metric("표준편차", f"{w.std():.2f} g")
                    if w.mean() > w.median():
                        note(f"평균이 중앙값보다 커요 → 소수의 무거운 개체가 평균을 끌어올렸어요. "
                             "<b>중앙값</b>은 크기순으로 줄 세웠을 때 한가운데 값이에요.")
                    else:
                        note("평균이 중앙값보다 작거나 같아요 → 가벼운 개체 쪽 값이 평균을 낮췄어요.")

        section("ENVIRONMENT", "스마트팜 환경은 어땠을까?")
        if env_file is None:
            st.info("환경 데이터 CSV를 올리면 온도·습도 변화가 나타나요.")
        else:
            env_cols = [c for c in ["temperature", "humidity", "ph", "ec"] if c in env_df.columns]
            names = {"temperature": "온도 (°C)", "humidity": "습도 (%)", "ph": "pH", "ec": "EC (dS/m)"}
            line_cols = [c for c in ["temperature", "humidity"] if c in env_df.columns]
            if "time" in env_df.columns and env_df["time"].notna().sum() >= 2 and line_cols:
                daily = env_df.dropna(subset=["time"]).set_index("time")[line_cols].resample("D").mean().dropna(how="all")
                fig = make_subplots(rows=len(line_cols), cols=1, shared_xaxes=True, vertical_spacing=0.12,
                                    subplot_titles=[f"일평균 {names[c]}" for c in line_cols])
                line_colors = {"temperature": WARM, "humidity": ACCENT}
                fills = {"temperature": "rgba(240,138,75,0.10)", "humidity": "rgba(18,135,168,0.10)"}
                for i, c in enumerate(line_cols, start=1):
                    fig.add_trace(go.Scatter(x=daily.index, y=daily[c], mode="lines",
                                             line=dict(color=line_colors[c], width=2.2, shape="spline"),
                                             fill="tozeroy", fillcolor=fills[c], name=names[c]), row=i, col=1)
                style(fig, height=230 * len(line_cols) + 40)
                fig.update_layout(showlegend=False, margin=dict(t=40, l=6, r=6, b=6))
                fig.update_annotations(font=dict(size=13, color=MUTED), x=0, xanchor="left")
                for i, c in enumerate(line_cols, start=1):
                    s = daily[c].dropna()
                    if len(s) >= 2:
                        pad = (s.max() - s.min()) * 0.15 + 0.5
                        fig.update_yaxes(range=[s.min() - pad, s.max() + pad], row=i, col=1)
                e1, e2 = st.columns([1.9, 1], gap="medium")
                with e1:
                    st.plotly_chart(fig, width="stretch")
            else:
                e1, e2 = st.columns([1.9, 1], gap="medium")
                with e1:
                    st.info("시간 열 또는 온도·습도 열이 없어 꺾은선 그래프는 건너뛰었어요.")

            with e2:
                rows = []
                for c in env_cols:
                    s = env_df[c].dropna()
                    if len(s) >= 2:
                        rows.append({"항목": names[c], "평균": round(s.mean(), 2), "표준편차": round(s.std(), 2),
                                     "최소": round(s.min(), 2), "최대": round(s.max(), 2)})
                if rows:
                    st.dataframe(pd.DataFrame(rows), width="stretch", hide_index=True)
                    note("<b>표준편차</b> — 값들이 평균에서 얼마나 흩어져 있는지 나타내요. 클수록 변동이 컸다는 뜻이에요.")
                else:
                    st.info("환경 데이터에서 온도·습도·pH·EC 열을 찾지 못했어요.")

        md('<div class="next">다음 → <b>02 검증</b> 탭에서 이 가설이 맞는지 확인해 봐요</div>')
    except Exception as e:
        st.warning(f"⚠️ 이 부분은 데이터 형식 때문에 표시하지 못했어요: {e}")

# ═════════════════════════════════════════════
# 탭2: 가설 검증
# ═════════════════════════════════════════════
with tab2:
    try:
        stepper(1)
        callout("HYPOTHESIS CHECK", "가설을 두 부분으로 나눠 확인해요.<br>"
                "<b>①</b> 두 길이는 서로 강한 상관이 있다 &nbsp;·&nbsp; <b>②</b> 두 길이는 생중량을 잘 설명한다")

        if growth_file is None:
            st.info("생육 결과 데이터 CSV를 올리면 가설 검증 결과가 나타나요.")
        else:
            section("CHECK 01", "지상부 길이 ↔ 지하부 길이")
            fig, r1, _ = scatter_with_trend(growth_df, "지상부 길이", "지하부 길이", color=BLUE)
            if fig is None:
                st.info("지상부 길이·지하부 길이 값이 부족해 검증 ①을 건너뛰었어요.")
            else:
                c1, c2 = st.columns([2.2, 1], gap="medium")
                with c1:
                    fig.update_layout(title=None, margin=dict(t=14, l=6, r=6, b=16))
                    st.plotly_chart(fig, width="stretch")
                with c2:
                    st.metric(f"상관계수 r · {strength(r1)}", f"{r1:.2f}")
                    if abs(r1) >= 0.7:
                        callout("VERDICT ①", "✅ 강한 상관!<br>가설 앞부분은 맞았어요.", "accent")
                    else:
                        callout("VERDICT ①", "❌ 상관이 강하지 않아요.<br>가설 앞부분도 데이터와 달랐어요.", "warm")

            section("CHECK 02", "길이 → 생중량", "길이가 길수록 생중량도 클까요?")
            pairs = [("지상부 길이", "생중량"), ("지하부 길이", "생중량")]
            subs = [pair_values(growth_df, x, y) for x, y in pairs]
            valid = [(p, s) for p, s in zip(pairs, subs) if s is not None]
            if not valid:
                st.info("길이·생중량 값이 부족해 검증 ②를 건너뛰었어요.")
            else:
                titles = []
                for (x, y), s in valid:
                    r = float(np.corrcoef(s[x], s[y])[0, 1])
                    titles.append(f"{x}  ·  r {r:.2f}  ·  R² {r * r * 100:.1f}%")
                fig = make_subplots(rows=1, cols=len(valid), subplot_titles=titles, horizontal_spacing=0.08)
                ids = growth_df["개체번호"].map(id_label) if "개체번호" in growth_df.columns else growth_df.index.astype(str)
                for i, ((x, y), s) in enumerate(valid, start=1):
                    fig.add_trace(go.Scatter(
                        x=s[x], y=s[y], mode="markers",
                        marker=dict(size=10, color="#9AA8A3", opacity=0.8, line=dict(width=1.5, color="white")),
                        text=ids.loc[s.index], showlegend=False,
                        hovertemplate="<b>개체 %{text}</b><br>" + x + " %{x}<br>생중량 %{y}<extra></extra>",
                    ), row=1, col=i)
                    add_trend(fig, s, x, y, row=1, col=i)
                    fig.update_xaxes(title_text=f"{x} (mm)", row=1, col=i)
                    fig.update_yaxes(title_text="생중량 (g)", row=1, col=i)
                style(fig, height=420)
                fig.update_layout(margin=dict(t=44, l=6, r=6, b=6))
                fig.update_annotations(font=dict(size=13, color=INK))
                st.plotly_chart(fig, width="stretch")

            section("RESULT", "상관계수 한눈에 보기")
            rows = []
            checks = [("지상부 길이", "지하부 길이", "①"), ("지상부 길이", "생중량", "②"), ("지하부 길이", "생중량", "②")]
            for x, y, part in checks:
                r = pearson(growth_df, x, y)
                if r is None:
                    continue
                ok = abs(r) >= 0.7
                rows.append({"가설": part, "비교 쌍": f"{x} ↔ {y}", "r": round(r, 2),
                             "R² (설명력)": f"{r * r * 100:.1f}%", "강도": strength(r),
                             "판정": "✅ 예상과 일치" if ok else "❌ 예상과 다름"})
            res1, res2 = st.columns([1.35, 1], gap="medium")
            with res1:
                if rows:
                    st.dataframe(pd.DataFrame(rows), width="stretch", hide_index=True)
                    note("<b>R²(결정계수)</b> = r × r. R² = 9%면 생중량 차이의 9%만 그 항목으로 설명된다는 뜻이에요. "
                         "기준: |r| ≥ 0.7 강함 · 0.4~0.7 보통 · 0.4 미만 약함")
                else:
                    st.info("계산할 수 있는 상관계수가 없어요.")

            len_r = {x: pearson(growth_df, x, "생중량") for x in ["지상부 길이", "지하부 길이"]}
            len_r = {k: v for k, v in len_r.items() if v is not None}
            if len_r:
                fig = go.Figure()
                fig.add_trace(go.Bar(y=list(len_r.keys()), x=[100] * len(len_r), orientation="h",
                                     marker_color="#E6EEF5", hoverinfo="skip", showlegend=False))
                fig.add_trace(go.Bar(
                    y=list(len_r.keys()), x=[v * v * 100 for v in len_r.values()], orientation="h",
                    marker_color=WARM, text=[f"  {v * v * 100:.1f}%" for v in len_r.values()],
                    textposition="outside", textfont=dict(color=INK, size=14), showlegend=False,
                    hovertemplate="%{y}<br>설명력 %{x:.1f}%<extra></extra>",
                ))
                style(fig, height=230, title="길이가 생중량 차이를 설명하는 비율 (100% 중)")
                fig.update_layout(barmode="overlay", bargap=0.45, barcornerradius=8,
                                  xaxis=dict(range=[0, 100], showticklabels=False, showgrid=False),
                                  yaxis=dict(showgrid=False))
                with res2:
                    st.plotly_chart(fig, width="stretch")
                st.write("")

                best = max(abs(v) for v in len_r.values())
                pct = max(v * v for v in len_r.values()) * 100
                if best < 0.4:
                    callout("VERDICT ②", f"❌ 가설 뒷부분은 틀렸어요.<br>두 길이 모두 약한 상관이고, 많아야 생중량 차이의 <b>{pct:.1f}%</b>만 설명해요.", "warm")
                elif best < 0.7:
                    callout("VERDICT ②", f"🤔 보통 수준의 상관이에요.<br>생중량 차이의 최대 <b>{pct:.1f}%</b>를 설명해서 '잘 설명한다'고 하기엔 부족해요.", "warm")
                else:
                    callout("VERDICT ②", f"✅ 길이가 생중량 차이의 최대 <b>{pct:.1f}%</b>를 설명해요. 가설 뒷부분도 맞았어요.", "accent")

            note("<br>💭 길이는 식물의 '키'만 보여 줄 뿐, 잎이 얼마나 빽빽한지·줄기가 얼마나 굵은지는 담지 못해요.")
            md('<div class="next">그럼 생중량을 결정하는 건 대체 뭘까? → <b>03 발견</b> 탭에서 찾아봐요</div>')
    except Exception as e:
        st.warning(f"⚠️ 이 부분은 데이터 형식 때문에 표시하지 못했어요: {e}")

# ═════════════════════════════════════════════
# 탭3: 대안 탐색
# ═════════════════════════════════════════════
with tab3:
    try:
        stepper(2)
        if growth_file is None:
            st.info("생육 결과 데이터 CSV를 올리면 대안 탐색 결과가 나타나요.")
        elif not has_growth:
            st.info("생육 데이터에서 생중량(또는 지상부·지하부 질량) 열을 찾지 못했어요.")
        else:
            rank = []
            for c in candidates:
                r = pearson(growth_df, c, "생중량")
                if r is not None:
                    rank.append((c, r))
            if not rank:
                st.info("생중량과 비교할 수 있는 생육 항목이 없어요.")
            else:
                rank.sort(key=lambda t: abs(t[1]), reverse=True)
                top, top_r = rank[0]
                unit = UNITS.get(top, "")
                len_rs = [abs(r) for c, r in rank if "길이" in c]

                section("RANKING", "생중량과 가장 관련 깊은 항목은?", "생중량을 뺀 모든 생육 항목의 상관계수를 비교했어요.")
                plot_rank = list(reversed(rank))
                fig = go.Figure(go.Bar(
                    y=[c for c, _ in plot_rank], x=[r for _, r in plot_rank], orientation="h",
                    marker_color=[ACCENT if c == top else NEUTRAL for c, _ in plot_rank],
                    text=[f"  {r:.2f}" for _, r in plot_rank], textposition="outside",
                    textfont=dict(size=14, color=INK),
                    hovertemplate="%{y}<br>r = %{x:.2f}<extra></extra>",
                ))
                fig.add_vline(x=0.7, line_dash="dot", line_color=WARM, line_width=1.5,
                              annotation_text="강한 상관 0.7", annotation_position="bottom right", annotation_font_color=WARM)
                style(fig, height=max(360, 110 + 56 * len(rank)))
                fig.update_layout(bargap=0.4, barcornerradius=8,
                                  xaxis=dict(range=[min(0, min(r for _, r in rank)) - 0.1, 1.05], title="상관계수 r"),
                                  yaxis=dict(showgrid=False))
                rk1, rk2 = st.columns([2.2, 1], gap="medium")
                with rk1:
                    st.plotly_chart(fig, width="stretch")
                with rk2:
                    st.metric("🥇 1위 항목", top)
                    st.metric(f"상관계수 r · {strength(top_r)}", f"{top_r:.2f}")
                    if len_rs and max(len_rs) > 0 and "길이" not in top:
                        ratio = (top_r ** 2) / (max(len_rs) ** 2)
                        st.metric("설명력 R²", f"{top_r ** 2 * 100:.1f}%", f"길이보다 약 {ratio:.0f}배")
                    else:
                        st.metric("설명력 R²", f"{top_r ** 2 * 100:.1f}%")

                section("REGRESSION", f"{top}이 늘면 생중량도 늘까?", "회귀식으로 관계를 정리하고, 오른쪽 예측기로 직접 확인해 보세요.")
                rg1, rg2 = st.columns([1.9, 1], gap="medium")
                fig, r, ab = scatter_with_trend(growth_df, top, "생중량", color=ACCENT)
                has_model = fig is not None
                if has_model:
                    a, b = ab
                    sign = "+" if b >= 0 else "−"
                    eq = f"생중량 = {a:.4f} × {top} {sign} {abs(b):.4f}"
                    fig.update_layout(title=None, margin=dict(t=14, l=6, r=6, b=16),
                                      xaxis_title=f"{top} ({unit})" if unit else top, yaxis_title="생중량 (g)")
                    fig.add_annotation(xref="paper", yref="paper", x=0.02, y=0.97, showarrow=False, align="left",
                                       text=f"<b>{eq}</b><br><span style='color:{MUTED}'>r = {r:.2f}  ·  R² = {r * r * 100:.1f}%</span>",
                                       bgcolor="rgba(255,255,255,0.92)", bordercolor=LINE, borderwidth=1, borderpad=10,
                                       font=dict(size=13, color=INK))
                    with rg1:
                        st.plotly_chart(fig, width="stretch")
                        note("<b>회귀식</b> — 점들 사이를 가장 잘 지나는 직선의 식이에요. 기울기 a는 항목이 1 늘 때 생중량이 평균적으로 얼마나 느는지를 뜻해요.")
                    with rg2:
                        md('<div class="sec-k" style="margin:6px 0 10px">🧮 PREDICTOR</div>')
                        s = growth_df[top].dropna()
                        lo_v, hi_v = float(s.min()), float(s.max())
                        if hi_v > lo_v:
                            val = st.slider(f"{top} 값을 골라 보세요", min_value=lo_v, max_value=hi_v, value=float(s.median()))
                            pred = ab[0] * val + ab[1]
                            st.metric(f"{top} {val:g}{unit}일 때 예상 생중량", f"{max(pred, 0):.2f} g")
                            note("실제 데이터 범위 밖은 예측이 부정확해서 슬라이더를 실제 범위로 제한했어요.")
                        else:
                            st.info("값이 모두 같아 예측기를 만들 수 없어요.")

                section("TOP vs BOTTOM", f"생중량 상위 25% vs 하위 25%, {top}은?")
                sub = growth_df[["생중량", top]].dropna()
                if len(sub) < 8:
                    st.info("개체 수가 적어 그룹 비교를 건너뛰었어요.")
                else:
                    q75, q25 = sub["생중량"].quantile(0.75), sub["생중량"].quantile(0.25)
                    hi = sub[sub["생중량"] >= q75][top]
                    lo = sub[sub["생중량"] <= q25][top]
                    c1, c2 = st.columns([1, 2], gap="medium")
                    with c1:
                        st.metric(f"상위 25% 평균 {top} · {len(hi)}개체", f"{hi.mean():.1f}{unit}")
                        st.metric(f"하위 25% 평균 {top} · {len(lo)}개체", f"{lo.mean():.1f}{unit}")
                        if lo.mean() > 0:
                            st.metric("차이", f"{hi.mean() / lo.mean():.1f}배")
                        else:
                            st.metric("차이", f"{hi.mean() - lo.mean():.1f}{unit}")
                    with c2:
                        bfig = go.Figure()
                        bfig.add_trace(go.Box(y=hi, name="상위 25%", marker=dict(color=ACCENT, size=6),
                                              line=dict(color=ACCENT), fillcolor="rgba(18,135,168,0.18)",
                                              boxpoints="all", jitter=0.45, pointpos=0))
                        bfig.add_trace(go.Box(y=lo, name="하위 25%", marker=dict(color=WARM, size=6),
                                              line=dict(color=WARM), fillcolor="rgba(240,138,75,0.18)",
                                              boxpoints="all", jitter=0.45, pointpos=0))
                        style(bfig, height=380)
                        bfig.update_layout(showlegend=False, yaxis_title=f"{top} ({unit})" if unit else top, margin=dict(t=14, l=6, r=6, b=40))
                        st.plotly_chart(bfig, width="stretch")
                    note("<b>박스플롯</b> — 상자 가운데 선은 중앙값, 상자는 가운데 50% 개체가 있는 범위예요.")

                section("EXPLORE", "직접 탐색", "사이드바에서 다른 항목을 골라 생중량과 비교해 보세요.")
                if explore_col is None:
                    st.info("사이드바에서 비교할 항목을 골라 주세요.")
                else:
                    r_pre = pearson(growth_df, explore_col, "생중량")
                    ttl = f"{explore_col} vs 생중량  ·  r {r_pre:.2f} ({strength(r_pre)})" if r_pre is not None else ""
                    fig2, r2, _ = scatter_with_trend(growth_df, explore_col, "생중량", color=BLUE, title=ttl)
                    if fig2 is None:
                        st.info("이 항목은 값이 부족해 그래프를 그릴 수 없어요.")
                    else:
                        st.plotly_chart(fig2, width="stretch")

                section("CONCLUSION", "결론")
                w = growth_df["생중량"].dropna()
                fold = f"약 {w.max() / w.min():.0f}배" if w.min() > 0 else f"{w.max() - w.min():.2f} g"
                len_pct = max(len_rs) ** 2 * 100 if len_rs else None
                body = f"같은 스마트팜에서도 생중량은 <b>{fold}</b> 차이가 났고,<br>"
                if len_pct is not None and "길이" not in top:
                    body += (f"그 차이를 가장 잘 설명하는 항목은 길이(설명력 {len_pct:.1f}%)가 아니라 "
                             f"<b>{html.escape(top)}</b>(설명력 {top_r ** 2 * 100:.1f}%)였어요.")
                else:
                    body += f"생중량과 가장 관련이 깊은 항목은 <b>{html.escape(top)}</b>(설명력 {top_r ** 2 * 100:.1f}%)이었어요."
                callout("KEY FINDING", body, "ink")

                st.write("")
                with st.expander("한계와 다음 실험"):
                    st.markdown(
                        "- **상관관계 ≠ 인과관계** — 잎이 많아서 무거운 건지, 잘 자라서 잎도 많고 무거운 건지는 이 데이터로 알 수 없어요.\n"
                        "- **기록되지 않은 정보** — 개체별 측정일·재배 위치·초기 상태가 없어 차이의 원인을 특정할 수 없어요.\n"
                        f"- **표본 수** — {len(growth_df)}개체로 다른 환경이나 식물에 일반화하기엔 한계가 있어요.\n"
                        "- **다음 실험 제안** — 주 1회 정기 측정 + 재배 위치·초기 크기 기록 → 생장 속도와 환경의 관계까지 분석 가능"
                    )

            st.write("")
            st.download_button(
                "생육 데이터 CSV 다운로드  ↓",
                data=growth_df.to_csv(index=False).encode("utf-8-sig"),
                file_name=f"{school}_생육데이터_분석용.csv",
                mime="text/csv",
            )
    except Exception as e:
        st.warning(f"⚠️ 이 부분은 데이터 형식 때문에 표시하지 못했어요: {e}")
