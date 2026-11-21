import io
import re

import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st
from plotly.subplots import make_subplots

# ─────────────────────────────────────────────
# 기본 설정
# ─────────────────────────────────────────────
st.set_page_config(
    page_title="극지식물 생중량, 무엇이 결정할까?",
    page_icon="🧊",
    layout="wide",
)

st.markdown(
    """
<style>
@import url('https://fonts.googleapis.com/css2?family=Noto+Sans+KR:wght@400;700&display=swap');
html, body, [class*="css"] {
   font-family: 'Noto Sans KR', 'Malgun Gothic', sans-serif;
}
</style>
""",
    unsafe_allow_html=True,
)

FONT = dict(family="Malgun Gothic, Apple SD Gothic Neo, Noto Sans KR, sans-serif")
GREEN = "#2E7D32"
ORANGE = "#EF6C00"
GRAY = "#B0BEC5"
BLUE = "#1565C0"


# ─────────────────────────────────────────────
# 데이터 읽기 · 열 이름 표준화
# ─────────────────────────────────────────────
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


# ─────────────────────────────────────────────
# 통계 도우미 함수
# ─────────────────────────────────────────────
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


def add_trend(fig, sub, x, y, row=None, col=None, color=ORANGE):
    a, b = np.polyfit(sub[x], sub[y], 1)
    xs = np.linspace(sub[x].min(), sub[x].max(), 50)
    trace = go.Scatter(
        x=xs, y=a * xs + b, mode="lines",
        line=dict(color=color, width=3, dash="dash"),
        name="추세선", showlegend=False, hoverinfo="skip",
    )
    if row is None:
        fig.add_trace(trace)
    else:
        fig.add_trace(trace, row=row, col=col)
    return a, b


def scatter_with_trend(df, x, y, color=GREEN, title=""):
    sub = pair_values(df, x, y)
    if sub is None:
        return None, None, None
    hover = df.loc[sub.index, "개체번호"].map(id_label) if "개체번호" in df.columns else sub.index.astype(str)
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=sub[x], y=sub[y], mode="markers",
        marker=dict(size=11, color=color, opacity=0.75, line=dict(width=1, color="white")),
        text=hover, hovertemplate="개체 %{text}<br>" + x + ": %{x}<br>" + y + ": %{y}<extra></extra>",
        showlegend=False,
    ))
    a, b = add_trend(fig, sub, x, y)
    r = float(np.corrcoef(sub[x], sub[y])[0, 1])
    fig.update_layout(
        title=title, xaxis_title=x, yaxis_title=y, font=FONT,
        height=430, margin=dict(t=60, l=10, r=10, b=10),
    )
    return fig, r, (a, b)


UNITS = {"생중량": "g", "잎 수": "장", "지상부 길이": "mm", "지하부 길이": "mm", "지상부 질량": "g", "지하부 질량": "g"}
EXCLUDE = {"time", "개체번호", "생중량", "지상부 질량", "지하부 질량"}


def growth_candidates(df):
    return [c for c in df.columns if c not in EXCLUDE and pd.api.types.is_numeric_dtype(df[c]) and df[c].notna().sum() >= 3]


# ─────────────────────────────────────────────
# 사이드바 · 데이터 업로드 (맨 위에서 한 번만 읽기)
# ─────────────────────────────────────────────
st.sidebar.header("📂 데이터 업로드")
env_file = st.sidebar.file_uploader("환경 데이터 CSV", type="csv")
growth_file = st.sidebar.file_uploader("생육 결과 데이터 CSV", type="csv")

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
if candidates:
    st.sidebar.divider()
    st.sidebar.header("🔎 생육 측정 항목 선택")
    default_idx = candidates.index("잎 수") if "잎 수" in candidates else 0
    explore_col = st.sidebar.selectbox("탭3 '직접 탐색'에서 생중량과 비교할 항목", candidates, index=default_idx)

st.sidebar.divider()
st.sidebar.caption(
    "📌 **상관계수(r)란?** -1~1 사이 값으로, 1에 가까울수록 한쪽이 커질 때 다른 쪽도 커지는 관계가 강하다는 뜻이에요.\n\n"
    "📌 **결정계수(R²)** = r². 한 항목이 다른 항목의 차이를 몇 % 설명하는지 나타내요."
)

# ─────────────────────────────────────────────
# 제목
# ─────────────────────────────────────────────
st.title("🧊 극지식물 생중량, 무엇이 결정할까?")
st.markdown(f"#### {school} 개체별 생육 차이 분석 — *같은 스마트팜, 다른 성장*")

if env_file is None and growth_file is None:
    st.info("👈 왼쪽 사이드바에서 환경 데이터 CSV와 생육 결과 데이터 CSV를 올려 주세요. 한 파일만 올려도 해당 부분은 볼 수 있어요.")

has_growth = (not growth_df.empty) and ("생중량" in growth_df.columns)

tab1, tab2, tab3 = st.tabs(["🌱 1막 · 우리의 가설", "🔍 2막 · 가설 검증", "💡 3막 · 대안 탐색"])

# ─────────────────────────────────────────────
# 탭1: 우리의 가설
# ─────────────────────────────────────────────
with tab1:
    try:
        c1, c2 = st.columns(2)
        with c1:
            st.info("❓ **연구 질문**\n\n같은 스마트팜에서 같은 기간 자란 식물들, 생중량 차이는 얼마나 크고 무엇으로 설명될까?")
        with c2:
            st.success("💭 **우리의 가설**\n\n지상부 길이와 지하부 길이는 강한 상관관계를 가지고, 두 길이는 생중량을 잘 설명할 것이다.")

        st.subheader("📋 실험 개요")
        m1, m2, m3, m4 = st.columns(4)
        if not growth_df.empty:
            m1.metric("개체 수", f"{len(growth_df)}개")
        else:
            m1.metric("개체 수", "—")
        if "time" in env_df.columns and env_df["time"].notna().sum() >= 2:
            t = env_df["time"].dropna()
            m2.metric("측정 기간", f"{(t.max().normalize() - t.min().normalize()).days + 1}일")
        else:
            m2.metric("측정 기간", "—")
        if "temperature" in env_df.columns and env_df["temperature"].notna().any():
            m3.metric("평균 온도", f"{env_df['temperature'].dropna().mean():.2f} °C")
        else:
            m3.metric("평균 온도", "—")
        if "humidity" in env_df.columns and env_df["humidity"].notna().any():
            m4.metric("평균 습도", f"{env_df['humidity'].dropna().mean():.2f} %")
        else:
            m4.metric("평균 습도", "—")

        st.divider()
        st.subheader("⚖️ 같은 스마트팜, 생중량은 얼마나 달랐을까?")
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
                    k3.metric("개체 간 차이", f"약 {w.max() / w.min():.0f}배")
                else:
                    k3.metric("개체 간 차이", f"{w.max() - w.min():.2f} g")

                bar = growth_df.loc[w.index].copy()
                bar["라벨"] = bar["개체번호"].map(id_label) if "개체번호" in bar.columns else (bar.index + 1).astype(str)
                bar = bar.sort_values("생중량", ascending=False).reset_index(drop=True)
                n_hi = min(5, len(bar) // 2)
                colors = []
                for i in range(len(bar)):
                    if i < n_hi:
                        colors.append(GREEN)
                    elif i >= len(bar) - n_hi:
                        colors.append(ORANGE)
                    else:
                        colors.append(GRAY)
                fig = go.Figure(go.Bar(
                    x=bar["라벨"], y=bar["생중량"], marker_color=colors,
                    hovertemplate="개체 %{x}<br>생중량 %{y:.2f} g<extra></extra>",
                ))
                fig.add_hline(y=w.mean(), line_dash="dot", line_color=BLUE,
                              annotation_text=f"평균 {w.mean():.2f} g", annotation_position="top right")
                fig.update_layout(
                    title=f"개체별 생중량 (🟩 상위 {n_hi}개체 · 🟧 하위 {n_hi}개체)",
                    xaxis_title="개체번호", yaxis_title="생중량 (g)", font=FONT, height=420,
                    xaxis=dict(type="category"), margin=dict(t=60, l=10, r=10, b=10),
                )
                st.plotly_chart(fig, width="stretch")

                fig = px.histogram(bar, x="생중량", nbins=min(15, max(5, len(bar) // 4)),
                                   color_discrete_sequence=[GREEN])
                fig.add_vline(x=w.mean(), line_dash="dash", line_color=ORANGE,
                              annotation_text=f"평균 {w.mean():.2f}", annotation_position="top right")
                fig.add_vline(x=w.median(), line_dash="dot", line_color=BLUE,
                              annotation_text=f"중앙값 {w.median():.2f}", annotation_position="top left")
                fig.update_layout(title="생중량 분포 (히스토그램)", xaxis_title="생중량 (g)",
                                  yaxis_title="개체 수", font=FONT, height=380, bargap=0.05,
                                  margin=dict(t=60, l=10, r=10, b=10))
                st.plotly_chart(fig, width="stretch")
                if w.mean() > w.median():
                    st.caption(f"📌 평균({w.mean():.2f} g)이 중앙값({w.median():.2f} g)보다 커요 → 소수의 무거운 개체가 평균을 끌어올렸다는 뜻이에요. "
                               "중앙값은 값을 크기순으로 줄 세웠을 때 한가운데 값이에요.")
                else:
                    st.caption(f"📌 평균({w.mean():.2f} g)이 중앙값({w.median():.2f} g)보다 작거나 같아요 → 가벼운 개체 쪽으로 치우친 값이 평균을 낮췄어요.")

        st.divider()
        st.subheader("🌡️ 스마트팜 환경은 어땠을까?")
        if env_file is None:
            st.info("환경 데이터 CSV를 올리면 온도·습도 변화가 나타나요.")
        else:
            env_cols = [c for c in ["temperature", "humidity", "ph", "ec"] if c in env_df.columns]
            names = {"temperature": "온도 (°C)", "humidity": "습도 (%)", "ph": "pH", "ec": "EC (dS/m)"}
            line_cols = [c for c in ["temperature", "humidity"] if c in env_df.columns]
            if "time" in env_df.columns and env_df["time"].notna().sum() >= 2 and line_cols:
                daily = env_df.dropna(subset=["time"]).set_index("time")[line_cols].resample("D").mean().dropna(how="all")
                fig = make_subplots(rows=len(line_cols), cols=1, shared_xaxes=True,
                                    subplot_titles=[f"일평균 {names[c]}" for c in line_cols])
                line_colors = {"temperature": ORANGE, "humidity": BLUE}
                for i, c in enumerate(line_cols, start=1):
                    fig.add_trace(go.Scatter(x=daily.index, y=daily[c], mode="lines+markers",
                                             line=dict(color=line_colors[c]), marker=dict(size=4),
                                             name=names[c]), row=i, col=1)
                fig.update_layout(font=FONT, height=230 * len(line_cols) + 60, showlegend=False,
                                  margin=dict(t=50, l=10, r=10, b=10))
                st.plotly_chart(fig, width="stretch")
            else:
                st.info("시간 열 또는 온도·습도 열이 없어 꺾은선 그래프는 건너뛰었어요.")

            if env_cols:
                rows = []
                for c in env_cols:
                    s = env_df[c].dropna()
                    if len(s) >= 2:
                        rows.append({"항목": names[c], "평균": round(s.mean(), 2), "표준편차": round(s.std(), 2),
                                     "최소": round(s.min(), 2), "최대": round(s.max(), 2)})
                if rows:
                    st.dataframe(pd.DataFrame(rows), width="stretch", hide_index=True)
                    st.caption("📌 **표준편차**: 값들이 평균에서 얼마나 흩어져 있는지 나타내요. 클수록 변동이 컸다는 뜻이에요.")
            else:
                st.info("환경 데이터에서 온도·습도·pH·EC 열을 찾지 못했어요.")

        st.markdown("### 👉 다음 탭에서 이 가설이 맞는지 확인해 봐요!")
    except Exception as e:
        st.warning(f"⚠️ 이 부분은 데이터 형식 때문에 표시하지 못했어요: {e}")

# ─────────────────────────────────────────────
# 탭2: 가설 검증
# ─────────────────────────────────────────────
with tab2:
    try:
        st.subheader("🔍 가설을 두 부분으로 나눠 확인해 봐요")
        st.markdown("> 가설: **①** 지상부 길이와 지하부 길이는 강한 상관관계를 가지고, **②** 두 길이는 생중량을 잘 설명할 것이다.")

        if growth_file is None:
            st.info("생육 결과 데이터 CSV를 올리면 가설 검증 결과가 나타나요.")
        else:
            # 검증 ①
            st.markdown("### 검증 ① 지상부 길이 ↔ 지하부 길이")
            fig, r1, _ = scatter_with_trend(growth_df, "지상부 길이", "지하부 길이", color=BLUE)
            if fig is None:
                st.info("지상부 길이·지하부 길이 값이 부족해 검증 ①을 건너뛰었어요.")
            else:
                fig.update_layout(title=f"지상부 길이 vs 지하부 길이  (r = {r1:.2f}, {strength(r1)})")
                st.plotly_chart(fig, width="stretch")
                if abs(r1) >= 0.7:
                    st.success(f"✅ r = {r1:.2f} — 강한 상관! 가설 앞부분은 맞았어요.")
                else:
                    st.warning(f"❌ r = {r1:.2f} ({strength(r1)}) — 가설 앞부분도 데이터와 맞지 않았어요.")

            st.divider()
            # 검증 ②
            st.markdown("### 검증 ② 길이 → 생중량")
            pairs = [("지상부 길이", "생중량"), ("지하부 길이", "생중량")]
            subs = [pair_values(growth_df, x, y) for x, y in pairs]
            valid = [(p, s) for p, s in zip(pairs, subs) if s is not None]
            if not valid:
                st.info("길이·생중량 값이 부족해 검증 ②를 건너뛰었어요.")
            else:
                titles = []
                for (x, y), s in valid:
                    r = float(np.corrcoef(s[x], s[y])[0, 1])
                    titles.append(f"{x} vs 생중량 (r = {r:.2f}, R² = {r * r * 100:.1f}%)")
                fig = make_subplots(rows=1, cols=len(valid), subplot_titles=titles)
                ids = growth_df["개체번호"].map(id_label) if "개체번호" in growth_df.columns else growth_df.index.astype(str)
                for i, ((x, y), s) in enumerate(valid, start=1):
                    fig.add_trace(go.Scatter(
                        x=s[x], y=s[y], mode="markers",
                        marker=dict(size=10, color=GRAY, line=dict(width=1, color="#546E7A")),
                        text=ids.loc[s.index], showlegend=False,
                        hovertemplate="개체 %{text}<br>" + x + ": %{x}<br>생중량: %{y}<extra></extra>",
                    ), row=1, col=i)
                    add_trend(fig, s, x, y, row=1, col=i)
                    fig.update_xaxes(title_text=f"{x} (mm)", row=1, col=i)
                    fig.update_yaxes(title_text="생중량 (g)", row=1, col=i)
                fig.update_layout(font=FONT, height=430, margin=dict(t=60, l=10, r=10, b=10))
                st.plotly_chart(fig, width="stretch")

            # 결과 표
            st.markdown("### 📊 상관계수 결과 표")
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
            if rows:
                st.dataframe(pd.DataFrame(rows), width="stretch", hide_index=True)
                st.caption("📌 **R²(결정계수)** = r × r. 예를 들어 R² = 9%면 생중량 차이의 9%만 그 항목으로 설명된다는 뜻이에요.")
            else:
                st.info("계산할 수 있는 상관계수가 없어요.")

            # 설명력 막대
            len_r = {x: pearson(growth_df, x, "생중량") for x in ["지상부 길이", "지하부 길이"]}
            len_r = {k: v for k, v in len_r.items() if v is not None}
            if len_r:
                fig = go.Figure(go.Bar(
                    y=list(len_r.keys()), x=[v * v * 100 for v in len_r.values()], orientation="h",
                    marker_color=GRAY, text=[f"{v * v * 100:.1f}%" for v in len_r.values()], textposition="outside",
                ))
                fig.add_vline(x=100, line_dash="dot", line_color=BLUE, annotation_text="100% (완벽하게 설명)")
                fig.update_layout(title="길이가 생중량 차이를 설명하는 비율 (R²)", xaxis=dict(range=[0, 110], title="설명력 (%)"),
                                  font=FONT, height=260, margin=dict(t=60, l=10, r=10, b=10))
                st.plotly_chart(fig, width="stretch")

                best = max(abs(v) for v in len_r.values())
                pct = max(v * v for v in len_r.values()) * 100
                if best < 0.4:
                    st.warning(f"❌ **가설 뒷부분은 틀렸어요!** 두 길이 모두 생중량과 약한 상관이고, 많아야 생중량 차이의 {pct:.1f}%밖에 설명하지 못해요.")
                elif best < 0.7:
                    st.warning(f"🤔 길이와 생중량은 보통 수준의 상관이에요. 생중량 차이의 최대 {pct:.1f}%를 설명해서 '잘 설명한다'고 하기엔 부족해요.")
                else:
                    st.success(f"✅ 길이가 생중량 차이의 최대 {pct:.1f}%를 설명해요. 가설 뒷부분도 맞았어요.")

            st.caption("💭 생각해 볼 점: 길이는 식물의 '키'만 보여 줄 뿐, 잎이 얼마나 빽빽한지·줄기가 얼마나 굵은지는 담지 못해요.")
            st.markdown("### 🤔 그럼 생중량을 결정하는 건 대체 뭘까? 다음 탭에서 찾아봐요!")
    except Exception as e:
        st.warning(f"⚠️ 이 부분은 데이터 형식 때문에 표시하지 못했어요: {e}")

# ─────────────────────────────────────────────
# 탭3: 대안 탐색
# ─────────────────────────────────────────────
with tab3:
    try:
        if growth_file is None:
            st.info("생육 결과 데이터 CSV를 올리면 대안 탐색 결과가 나타나요.")
        elif not has_growth:
            st.info("생육 데이터에서 생중량(또는 지상부·지하부 질량) 열을 찾지 못했어요.")
        else:
            st.subheader("🏆 생중량과 가장 관련 깊은 항목은?")
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
                plot_rank = list(reversed(rank))
                fig = go.Figure(go.Bar(
                    y=[c for c, _ in plot_rank], x=[r for _, r in plot_rank], orientation="h",
                    marker_color=[GREEN if c == top else GRAY for c, _ in plot_rank],
                    text=[f"{r:.2f}" for _, r in plot_rank], textposition="outside",
                ))
                fig.add_vline(x=0.7, line_dash="dot", line_color=ORANGE, annotation_text="강한 상관 기준 0.7")
                fig.update_layout(title="생중량과의 상관계수(r) 순위", xaxis=dict(range=[min(0, min(r for _, r in rank)) - 0.1, 1.05], title="r"),
                                  font=FONT, height=120 + 60 * len(rank), margin=dict(t=60, l=10, r=10, b=10))
                st.plotly_chart(fig, width="stretch")

                len_rs = [abs(r) for c, r in rank if "길이" in c]
                m1, m2, m3 = st.columns(3)
                m1.metric("🥇 1위 항목", top)
                m2.metric("상관계수 r", f"{top_r:.2f}", strength(top_r))
                if len_rs and max(len_rs) > 0 and "길이" not in top:
                    ratio = (top_r ** 2) / (max(len_rs) ** 2)
                    m3.metric("설명력 R²", f"{top_r ** 2 * 100:.1f}%", f"길이보다 약 {ratio:.0f}배 높음")
                else:
                    m3.metric("설명력 R²", f"{top_r ** 2 * 100:.1f}%")

                st.divider()
                unit = UNITS.get(top, "")
                fig, r, ab = scatter_with_trend(growth_df, top, "생중량", color=GREEN)
                has_model = fig is not None
                if fig is not None:
                    a, b = ab
                    sign = "+" if b >= 0 else "−"
                    eq = f"생중량 = {a:.4f} × {top} {sign} {abs(b):.4f}"
                    fig.update_layout(title=f"{top} vs 생중량  (r = {r:.2f})", xaxis_title=f"{top} ({unit})" if unit else top,
                                      yaxis_title="생중량 (g)")
                    fig.add_annotation(xref="paper", yref="paper", x=0.02, y=0.98, showarrow=False, align="left",
                                       text=f"<b>{eq}</b><br>R² = {r * r * 100:.1f}%",
                                       bgcolor="rgba(255,255,255,0.85)", bordercolor=GREEN, borderwidth=1)
                    st.plotly_chart(fig, width="stretch")
                    st.caption("📌 **회귀식**: 점들 사이를 가장 잘 지나는 직선의 식이에요. 기울기 a는 '항목이 1 늘 때 생중량이 평균적으로 얼마나 느는지'를 뜻해요.")

                # 상위·하위 25% 비교
                st.divider()
                st.subheader(f"⚔️ 생중량 상위 25% vs 하위 25%, {top}은 얼마나 달랐을까?")
                sub = growth_df[["생중량", top]].dropna()
                if len(sub) < 8:
                    st.info("개체 수가 적어 그룹 비교를 건너뛰었어요.")
                else:
                    q75, q25 = sub["생중량"].quantile(0.75), sub["생중량"].quantile(0.25)
                    hi = sub[sub["생중량"] >= q75][top]
                    lo = sub[sub["생중량"] <= q25][top]
                    g1, g2, g3 = st.columns(3)
                    g1.metric(f"상위 25% 평균 {top}", f"{hi.mean():.1f} {unit}", f"{len(hi)}개체", delta_color="off")
                    g2.metric(f"하위 25% 평균 {top}", f"{lo.mean():.1f} {unit}", f"{len(lo)}개체", delta_color="off")
                    if lo.mean() > 0:
                        g3.metric("차이", f"약 {hi.mean() / lo.mean():.1f}배")
                    else:
                        g3.metric("차이", f"{hi.mean() - lo.mean():.1f} {unit}")
                    fig = go.Figure()
                    fig.add_trace(go.Box(y=hi, name="생중량 상위 25%", marker=dict(color=GREEN), fillcolor="rgba(46,125,50,0.35)", boxpoints="all", jitter=0.4))
                    fig.add_trace(go.Box(y=lo, name="생중량 하위 25%", marker=dict(color=ORANGE), fillcolor="rgba(239,108,0,0.35)", boxpoints="all", jitter=0.4))
                    fig.update_layout(yaxis_title=f"{top} ({unit})" if unit else top, font=FONT, height=400,
                                      showlegend=False, margin=dict(t=30, l=10, r=10, b=10))
                    st.plotly_chart(fig, width="stretch")
                    st.caption("📌 **박스플롯**: 상자 가운데 선은 중앙값, 상자는 가운데 50% 개체가 있는 범위예요.")

                # 예측기
                if has_model:
                    st.divider()
                    st.subheader("🧮 생중량 예측기")
                    s = growth_df[top].dropna()
                    lo_v, hi_v = float(s.min()), float(s.max())
                    if hi_v > lo_v:
                        val = st.slider(f"{top} 값을 골라 보세요", min_value=lo_v, max_value=hi_v, value=float(s.median()))
                        pred = ab[0] * val + ab[1]
                        st.metric(f"{top} {val:g}{unit}일 때 예상 생중량", f"{max(pred, 0):.2f} g")
                        st.caption("⚠️ 실제 데이터 범위 밖의 값은 예측이 부정확해서 슬라이더를 실제 범위로 제한했어요.")

                # 직접 탐색
                st.divider()
                st.subheader("🔎 직접 탐색")
                if explore_col is None:
                    st.info("사이드바에서 비교할 항목을 골라 주세요.")
                else:
                    fig2, r2, _ = scatter_with_trend(growth_df, explore_col, "생중량", color=BLUE,
                                                     title=f"{explore_col} vs 생중량")
                    if fig2 is None:
                        st.info("이 항목은 값이 부족해 그래프를 그릴 수 없어요.")
                    else:
                        fig2.update_layout(title=f"{explore_col} vs 생중량  (r = {r2:.2f}, {strength(r2)})")
                        st.plotly_chart(fig2, width="stretch")

                # 결론
                st.divider()
                w = growth_df["생중량"].dropna()
                fold = f"약 {w.max() / w.min():.0f}배" if w.min() > 0 else f"{w.max() - w.min():.2f} g"
                len_pct = max(len_rs) ** 2 * 100 if len_rs else None
                msg = f"🎯 **결론**: 같은 스마트팜에서도 생중량은 {fold} 차이가 났고, "
                if len_pct is not None and "길이" not in top:
                    msg += f"그 차이를 가장 잘 설명하는 항목은 길이(설명력 최대 {len_pct:.1f}%)가 아니라 **{top}**(설명력 {top_r ** 2 * 100:.1f}%)였어요."
                else:
                    msg += f"생중량과 가장 관련이 깊은 항목은 **{top}**(설명력 {top_r ** 2 * 100:.1f}%)이었어요."
                st.success(msg)

                with st.expander("🧭 한계와 다음 실험"):
                    st.markdown(
                        "- **상관관계 ≠ 인과관계**: 잎이 많아서 무거운 건지, 잘 자라서 잎도 많고 무거운 건지는 이 데이터로 알 수 없어요.\n"
                        "- **기록되지 않은 정보**: 개체별 측정일·재배 위치·초기 상태가 없어 차이의 원인을 특정할 수 없어요.\n"
                        f"- **표본 수**: {len(growth_df)}개체로 다른 환경이나 식물에 일반화하기엔 한계가 있어요.\n"
                        "- **다음 실험 제안**: 주 1회 정기 측정 + 재배 위치·초기 크기 기록 → 생장 속도와 환경의 관계까지 분석 가능"
                    )

            st.download_button(
                "⬇️ 생육 데이터 CSV 다운로드 (생중량 포함)",
                data=growth_df.to_csv(index=False).encode("utf-8-sig"),
                file_name=f"{school}_생육데이터_분석용.csv",
                mime="text/csv",
            )
    except Exception as e:
        st.warning(f"⚠️ 이 부분은 데이터 형식 때문에 표시하지 못했어요: {e}")
