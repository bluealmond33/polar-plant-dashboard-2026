import io
import os
import numpy as np
import pandas as pd
import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots


# ─────────────────────────────────────────────
# 페이지 설정 & 한글 폰트 (필수 7)
# ─────────────────────────────────────────────
st.set_page_config(page_title="극지식물 생육 분석 대시보드", layout="wide")

st.markdown(
    """
<style>
@import url('https://fonts.googleapis.com/css2?family=Noto+Sans+KR&display=swap');
html, body, [class*="css"] {
   font-family: 'Noto Sans KR', 'Malgun Gothic', sans-serif;
}
</style>
""",
    unsafe_allow_html=True,
)


# ─────────────────────────────────────────────
# CSV 읽기 (필수 1)
# ─────────────────────────────────────────────
@st.cache_data
def read_csv(file):
    if file is None:
        return pd.DataFrame()
    data = file.getvalue()
    for enc in ("utf-8-sig", "cp949"):
        try:
            return pd.read_csv(io.BytesIO(data), encoding=enc)
        except Exception:
            pass
    return pd.DataFrame()


# ─────────────────────────────────────────────
# 열 이름 표준화 (필수 2 — 명세 그대로)
# ─────────────────────────────────────────────
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
            num = pd.to_numeric(
                df[c].astype(str).str.replace(",", "")
                .str.extract(r"(-?\d+\.?\d*)")[0],
                errors="coerce",
            )
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
            parsed[bad] = (
                pd.to_datetime(parts[0], format="%Y%m%d")
                + pd.to_timedelta(parts[1].astype(int), unit="h")
            )
        df["time"] = parsed

    return df


# ─────────────────────────────────────────────
# 통계 용어 설명
# ─────────────────────────────────────────────
STAT_GLOSS = {
    "평균": "모든 값을 더해 개수로 나눈 값. 자료의 대표값으로 자주 씁니다.",
    "표준편차": "값들이 평균에서 얼마나 흩어져 있는지를 나타냅니다. 작을수록 값들이 평균 근처에 모여 있습니다.",
    "상관계수": "-1에서 1 사이의 값으로, 두 변수가 함께 움직이는 정도를 나타냅니다. 1에 가까울수록 함께 증가, -1에 가까울수록 반대로 움직입니다.",
    "최대": "자료에서 가장 큰 값.",
    "최소": "자료에서 가장 작은 값.",
    "중앙값": "값을 크기순으로 나열했을 때 한가운데 있는 값. 극단값의 영향을 덜 받습니다.",
}


# ─────────────────────────────────────────────
# 사이드바
# ─────────────────────────────────────────────
st.sidebar.title("📂 데이터 업로드")

env_file = st.sidebar.file_uploader("환경 CSV 업로드", type=["csv"])
growth_file = st.sidebar.file_uploader("생육 결과 CSV 업로드", type=["csv"])

growth_cols = [
    "잎 수",
    "지상부 길이",
    "지하부 길이",
    "생중량",
    "지상부 질량",
    "지하부 질량",
]
selected_growth = st.sidebar.multiselect(
    "📊 생육 측정 항목 선택 (탭3에서 사용)",
    growth_cols,
    default=["잎 수", "지상부 길이", "생중량"],
)

st.sidebar.markdown("---")
st.sidebar.info("CSV를 업로드하면 탭이 활성화됩니다. 두 파일 모두 올리셔도 되고, 하나만 올리셔도 해당 탭이 동작합니다.")


# ─────────────────────────────────────────────
# 데이터 로드 & 표준화 (맨 위에서 한 번만)
# ─────────────────────────────────────────────
with st.spinner("데이터를 읽고 정리 중입니다..."):
    env_df = read_csv(env_file)
    growth_df = read_csv(growth_file)

    if not env_df.empty:
        env_df = std_cols(env_df)
    if not growth_df.empty:
        growth_df = std_cols(growth_df)

school_name_env = ""
school_name_growth = ""
if env_file is not None:
    school_name_env = os.path.basename(env_file.name).split("_")[0]
if growth_file is not None:
    school_name_growth = os.path.basename(growth_file.name).split("_")[0]


# ─────────────────────────────────────────────
# 탭
# ─────────────────────────────────────────────
tab1, tab2, tab3 = st.tabs(
    ["📈 환경 데이터 탐색", "🌱 생육 결과 분석", "🔗 환경-생육 관계"]
)


# ═════════════════════════════════════════════
# 탭 1 — 환경 데이터 탐색
# ═════════════════════════════════════════════
with tab1:
    try:
        if env_df.empty:
            st.info("📁 환경 CSV를 사이드바에서 업로드해 주세요.")
        else:
            name = school_name_env or "업로드된 파일"
            st.subheader(f"🏫 {name} — 환경 데이터")

            # ── 시간별 환경 추이 (서브플롯) ──
            if "time" in env_df.columns:
                env_cols = [c for c in ["temperature", "humidity", "ph", "ec"] if c in env_df.columns]
                if env_cols:
                    fig_ts = make_subplots(
                        rows=len(env_cols), cols=1,
                        shared_xaxes=True,
                        vertical_spacing=0.08,
                    )
                    for i, col in enumerate(env_cols, start=1):
                        d = env_df[["time", col]].dropna()
                        if len(d) >= 2:
                            fig_ts.add_trace(
                                go.Scatter(
                                    x=d["time"], y=d[col],
                                    mode="lines", name=col,
                                ),
                                row=i, col=1,
                            )
                    fig_ts.update_layout(
                        height=260 * len(env_cols),
                        font=dict(family="Malgun Gothic, Apple SD Gothic Neo, sans-serif"),
                        margin=dict(l=40, r=20, t=30, b=20),
                    )
                    st.plotly_chart(fig_ts, width="stretch")
                else:
                    st.info("📊 표시할 환경 측정 열(temperature, humidity, ph, ec)이 없습니다.")
            else:
                st.info("⏰ 'time' 열을 찾을 수 없어 시간 추이 그래프를 그리지 못했습니다.")

            st.markdown("---")

            # ── 요약 통계 카드 ──
            st.subheader("📋 환경 요약 통계")
            env_num_cols = [c for c in ["temperature", "humidity", "ph", "ec"] if c in env_df.columns]
            if env_num_cols:
                summary_rows = []
                for col in env_num_cols:
                    s = env_df[col].dropna()
                    if len(s) >= 2:
                        summary_rows.append({
                            "측정 항목": col,
                            "평균": f"{s.mean():.2f}",
                            "표준편차": f"{s.std():.2f}",
                            "최대": f"{s.max():.2f}",
                            "최소": f"{s.min():.2f}",
                            "데이터 수": f"{len(s)}",
                        })
                if summary_rows:
                    st.dataframe(
                        pd.DataFrame(summary_rows),
                        width="stretch",
                    )
                else:
                    st.info("표시할 요약 통계가 없습니다.")

                with st.expander("📖 통계 용어 간단 설명"):
                    for term, desc in STAT_GLOSS.items():
                        st.write(f"**{term}**: {desc}")
            else:
                st.info("표시할 숫자 열이 없습니다.")

            # ── 결측 구간 안내 ──
            if "time" in env_df.columns:
                gap_count = env_df["time"].isna().sum()
                if gap_count > 0:
                    st.warning(
                        f"⚠️ 시간 정보가 없는 행이 {gap_count}개 있습니다. "
                        "센서가 측정하지 못한 구간일 수 있습니다."
                    )
    except Exception as e:
        st.warning(f"⚠️ 이 부분은 데이터 형식 때문에 표시하지 못했어요: {e}")


# ═════════════════════════════════════════════
# 탭 2 — 생육 결과 분석
# ═════════════════════════════════════════════
with tab2:
    try:
        if growth_df.empty:
            st.info("📁 생육 결과 CSV를 사이드바에서 업로드해 주세요.")
        else:
            name = school_name_growth or "업로드된 파일"
            st.subheader(f"🌱 {name} — 생육 결과 분석")

            if "개체번호" not in growth_df.columns:
                st.info("'개체번호' 열이 없어 개체별 분석을 진행할 수 없습니다.")
            else:
                growth_num_cols = [
                    c for c in [
                        "잎 수", "지상부 길이", "지하부 길이",
                        "생중량", "지상부 질량", "지하부 질량",
                    ]
                    if c in growth_df.columns
                ]
                if not growth_num_cols:
                    st.info("표시할 생육 측정 열이 없습니다.")
                else:
                    # ── 개체별 요약 테이블 ──
                    st.subheader("📊 개체별 생육 요약")
                    summary = growth_df[["개체번호"] + growth_num_cols].dropna(
                        subset=growth_num_cols, how="all"
                    )
                    if len(summary) > 1:
                        st.dataframe(summary, width="stretch")

                        # ── 생육 항목별 막대 그래프 ──
                        st.subheader("📊 개체별 생육 지표 비교")
                        plot_cols = growth_num_cols[:3]
                        if plot_cols:
                            fig_bar = make_subplots(
                                rows=1, cols=len(plot_cols),
                                subplot_titles=plot_cols,
                            )
                            for i, col in enumerate(plot_cols, start=1):
                                d = growth_df[["개체번호", col]].dropna()
                                if len(d) >= 2:
                                    fig_bar.add_trace(
                                        go.Bar(
                                            x=d["개체번호"],
                                            y=d[col],
                                            name=col,
                                            fillcolor="#4C72B0",
                                        ),
                                        row=1, col=i,
                                    )
                            fig_bar.update_layout(
                                font=dict(family="Malgun Gothic, Apple SD Gothic Neo, sans-serif"),
                                margin=dict(l=40, r=20, t=30, b=20),
                            )
                            st.plotly_chart(fig_bar, width="stretch")

                    # ── 생중량 상위·하위 개체 ──
                    if "생중량" in growth_df.columns:
                        st.subheader("🏆 생중량 상위·하위 개체")
                        gw = growth_df[["개체번호", "생중량"]].dropna()
                        if len(gw) >= 2:
                            top_n = min(5, len(gw))
                            bottom_n = min(5, len(gw))
                            top_idx = gw["생중량"].nlargest(top_n).index
                            bottom_idx = gw["생중량"].nsmallest(bottom_n).index

                            col_t, col_b = st.columns(2)
                            with col_t:
                                st.markdown("### 🔺 생중량 상위 개체")
                                top_df = gw.loc[top_idx].sort_values("생중량", ascending=False)
                                st.dataframe(top_df, width="stretch")
                                fig_top = go.Figure()
                                fig_top.add_trace(go.Bar(
                                    x=top_df["개체번호"],
                                    y=top_df["생중량"],
                                    fillcolor="#2CA02C",
                                    name="생중량",
                                ))
                                fig_top.update_layout(
                                    font=dict(family="Malgun Gothic, Apple SD Gothic Neo, sans-serif"),
                                    xaxis_title="개체번호",
                                    yaxis_title="생중량 (g)",
                                    margin=dict(l=40, r=20, t=20, b=20),
                                )
                                st.plotly_chart(fig_top, width="stretch")

                            with col_b:
                                st.markdown("### 🔻 생중량 하위 개체")
                                bottom_df = gw.loc[bottom_idx].sort_values("생중량", ascending=True)
                                st.dataframe(bottom_df, width="stretch")
                                fig_bottom = go.Figure()
                                fig_bottom.add_trace(go.Bar(
                                    x=bottom_df["개체번호"],
                                    y=bottom_df["생중량"],
                                    fillcolor="#D62728",
                                    name="생중량",
                                ))
                                fig_bottom.update_layout(
                                    font=dict(family="Malgun Gothic, Apple SD Gothic Neo, sans-serif"),
                                    xaxis_title="개체번호",
                                    yaxis_title="생중량 (g)",
                                    margin=dict(l=40, r=20, t=20, b=20),
                                )
                                st.plotly_chart(fig_bottom, width="stretch")

                    # ── 생육 분포 (상자 그림) ──
                    if len(growth_num_cols) >= 1:
                        st.subheader("📊 생육 지표 분포")
                        box_cols = [c for c in growth_num_cols if c != "개체번호"]
                        if box_cols:
                            d_box = growth_df[box_cols].dropna()
                            if len(d_box) >= 2:
                                fig_box = go.Figure()
                                colors = [
                                    "#4C72B0", "#55A868", "#C44E52",
                                    "#8172B3", "#CCB974", "#64B5CD",
                                ]
                                for i, col in enumerate(box_cols):
                                    fig_box.add_trace(go.Box(
                                        y=d_box[col].dropna(),
                                        name=col,
                                        fillcolor=colors[i % len(colors)],
                                        marker=dict(size=3),
                                    ))
                                fig_box.update_layout(
                                    font=dict(family="Malgun Gothic, Apple SD Gothic Neo, sans-serif"),
                                    xaxis_title="측정 항목",
                                    yaxis_title="값",
                                    margin=dict(l=40, r=20, t=20, b=20),
                                )
                                st.plotly_chart(fig_box, width="stretch")

                    # ── 요약 통계 ──
                    st.markdown("---")
                    st.subheader("📋 생육 요약 통계")
                    if growth_num_cols:
                        grow_summary_rows = []
                        for col in growth_num_cols:
                            s = growth_df[col].dropna()
                            if len(s) >= 2:
                                grow_summary_rows.append({
                                    "측정 항목": col,
                                    "평균": f"{s.mean():.2f}",
                                    "표준편차": f"{s.std():.2f}",
                                    "최대": f"{s.max():.2f}",
                                    "최소": f"{s.min():.2f}",
                                    "중앙값": f"{s.median():.2f}",
                                    "데이터 수": f"{len(s)}",
                                })
                        if grow_summary_rows:
                            st.dataframe(
                                pd.DataFrame(grow_summary_rows),
                                width="stretch",
                            )
                        else:
                            st.info("표시할 요약 통계가 없습니다.")
    except Exception as e:
        st.warning(f"⚠️ 이 부분은 데이터 형식 때문에 표시하지 못했어요: {e}")


# ═════════════════════════════════════════════
# 탭 3 — 환경-생육 관계
# ═════════════════════════════════════════════
with tab3:
    try:
        if env_df.empty or growth_df.empty:
            if env_df.empty and growth_df.empty:
                st.info("📁 환경 CSV와 생육 결과 CSV를 모두 사이드바에서 업로드해 주세요.")
            elif env_df.empty:
                st.info("📁 환경 CSV를 사이드바에서 업로드해 주세요. (탭3은 두 파일이 모두 필요합니다)")
            else:
                st.info("📁 생육 결과 CSV를 사이드바에서 업로드해 주세요. (탭3은 두 파일이 모두 필요합니다)")
        else:
            name = school_name_growth or "업로드된 파일"
            st.subheader(f"🔗 {name} — 환경과 생육의 관계")

            if "개체번호" not in growth_df.columns:
                st.info("'개체번호' 열이 없어 관계 분석을 진행할 수 없습니다.")
            else:
                env_num_cols = [c for c in ["temperature", "humidity", "ph", "ec"] if c in env_df.columns]
                growth_num_cols = [
                    c for c in [
                        "잎 수", "지상부 길이", "지하부 길이",
                        "생중량", "지상부 질량", "지하부 질량",
                    ]
                    if c in growth_df.columns
                ]

                if not env_num_cols:
                    st.info("환경 측정 열(temperature, humidity, ph, ec)이 없어 관계 분석을 진행할 수 없습니다.")
                elif not growth_num_cols:
                    st.info("생육 측정 열이 없어 관계 분석을 진행할 수 없습니다.")
                else:
                    st.info(
                        "⚠️ 환경 데이터는 시간별 측정값이고 생육 데이터는 개체별 측정값이라 "
                        "직접 병합이 어렵습니다. 대신 생육 지표 간 상관을 분석합니다."
                    )

                    # ── 생육 지표 간 상관계수 행렬 ──
                    st.subheader("📊 생육 지표 간 상관계수")
                    if len(growth_num_cols) >= 2:
                        corr_df = growth_df[growth_num_cols].dropna()
                        if len(corr_df) >= 2:
                            corr = corr_df.corr(numeric_only=True)
                            fig_corr = px.imshow(
                                corr,
                                text_auto=".2f",
                                color_continuous_scale="RdBu_r",
                                aspect="auto",
                            )
                            fig_corr.update_layout(
                                font=dict(family="Malgun Gothic, Apple SD Gothic Neo, sans-serif"),
                                title="생육 지표 간 상관계수 행렬",
                                margin=dict(l=40, r=20, t=40, b=20),
                            )
                            st.plotly_chart(fig_corr, width="stretch")

                            st.markdown("**상관계수 해석**: 1에 가까울수록 두 지표가 함께 증가, -1에 가까울수록 반대로 움직입니다. 0에 가까우면 관계가 약합니다.")
                        else:
                            st.info("상관계수를 계산할 데이터가 부족합니다.")

                    # ── 생육 항목 간 산점도 (선택) ──
                    if len(growth_num_cols) >= 2:
                        st.subheader("📈 생육 지표 간 관계 (산점도)")
                        x_col = st.selectbox(
                            "X축 선택",
                            growth_num_cols,
                            index=0,
                        )
                        y_col = st.selectbox(
                            "Y축 선택",
                            [c for c in growth_num_cols if c != x_col],
                            index=min(1, len(growth_num_cols) - 1),
                        )

                        d_scatter = growth_df[[x_col, y_col]].dropna()
                        if len(d_scatter) >= 2:
                            # 추세선 직접 계산 (np.polyfit)
                            x_vals = d_scatter[x_col].values
                            y_vals = d_scatter[y_col].values
                            slope, intercept = np.polyfit(x_vals, y_vals, 1)
                            x_line = np.linspace(x_vals.min(), x_vals.max(), 100)
                            y_line = slope * x_line + intercept

                            corr_val = d_scatter[x_col].corr(d_scatter[y_col])

                            fig_scatter = go.Figure()
                            fig_scatter.add_trace(go.Scatter(
                                x=d_scatter[x_col],
                                y=d_scatter[y_col],
                                mode="markers",
                                marker=dict(size=8, color="#4C72B0"),
                                name="개체",
                            ))
                            fig_scatter.add_trace(go.Scatter(
                                x=x_line,
                                y=y_line,
                                mode="lines",
                                line=dict(color="#D62728", width=2),
                                name=f"추세선 (r={corr_val:.2f})",
                            ))
                            fig_scatter.update_layout(
                                font=dict(family="Malgun Gothic, Apple SD Gothic Neo, sans-serif"),
                                xaxis_title=x_col,
                                yaxis_title=y_col,
                                margin=dict(l=40, r=20, t=30, b=20),
                            )
                            st.plotly_chart(fig_scatter, width="stretch")

                            st.markdown(
                                f"**상관계수 r = {corr_val:.2f}** "
                                f"— 두 지표 사이의 선형 관계 정도를 나타냅니다. "
                                f"추세선의 기울기는 **{slope:.3f}**로, "
                                f"{x_col}이 1 단위 증가할 때 {y_col}은 평균 {slope:.3f} 단위 변화합니다."
                            )
                        else:
                            st.info("산점도를 그릴 데이터가 부족합니다.")

                    # ── 생육 지표 요약 통계 ──
                    st.markdown("---")
                    st.subheader("📋 생육 요약 통계")
                    if growth_num_cols:
                        grow_summary_rows = []
                        for col in growth_num_cols:
                            s = growth_df[col].dropna()
                            if len(s) >= 2:
                                grow_summary_rows.append({
                                    "측정 항목": col,
                                    "평균": f"{s.mean():.2f}",
                                    "표준편차": f"{s.std():.2f}",
                                    "최대": f"{s.max():.2f}",
                                    "최소": f"{s.min():.2f}",
                                    "중앙값": f"{s.median():.2f}",
                                    "데이터 수": f"{len(s)}",
                                })
                        if grow_summary_rows:
                            st.dataframe(
                                pd.DataFrame(grow_summary_rows),
                                width="stretch",
                            )

                    # ── CSV 다운로드 ──
                    st.markdown("---")
                    st.subheader("📥 생육 데이터 다운로드 (한글 깨짐 방지)")
                    if not growth_df.empty:
                        csv_data = growth_df.to_csv(index=False).encode("utf-8-sig")
                        st.download_button(
                            label="📥 생육 결과 CSV 다운로드",
                            data=csv_data,
                            file_name=f"{school_name_growth or '생육결과'}_정리.csv",
                            mime="text/csv",
                        )
    except Exception as e:
        st.warning(f"⚠️ 이 부분은 데이터 형식 때문에 표시하지 못했어요: {e}")
