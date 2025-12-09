import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px

# -----------------------------------------------------------------------------
# 1. Page Configuration & Title
# -----------------------------------------------------------------------------
st.set_page_config(
    page_title="Tridge Revenue Simulation (2026-2028)",
    page_icon="📈",
    layout="wide"
)

st.title("🌐 B2B Platform Revenue Simulator (2026-2028)")
st.markdown("""
이 대시보드는 **트릿지(Tridge)** 모델을 기반으로 한 3개년 매출 시뮬레이터입니다.  
좌측의 **주요 변수(Key Drivers)**를 조절하여 초기 미팅 중심의 매출이 커미션 중심의 **Recurring Revenue(J-Curve)**로 전환되는 과정을 확인하세요.
""")

# -----------------------------------------------------------------------------
# 2. Sidebar: Input Variables
# -----------------------------------------------------------------------------
st.sidebar.header("🎛️ 시뮬레이션 변수 설정")

# 1. 초기 바이어 수
initial_buyers = st.sidebar.slider(
    "1. 초기 바이어 수 (명)", 
    min_value=10, max_value=500, value=50, step=10,
    help="2026년 1월 기준 활성 바이어 수"
)

# 2. 월별 바이어 증가 수
monthly_growth = st.sidebar.slider(
    "2. 월별 바이어 증가 (명/월)", 
    min_value=1, max_value=50, value=2, step=1,
    help="매월 신규로 유입되는 바이어 수"
)

# 3. 미팅 단가
meeting_fee = st.sidebar.slider(
    "3. 미팅 단가 ($/건)", 
    min_value=100, max_value=5000, value=1000, step=100,
    help="바이어-서플라이어 매칭 1건당 과금액"
)

# 4. 커미션 요율
commission_rate_percent = st.sidebar.slider(
    "4. 커미션 요율 (%)", 
    min_value=0.5, max_value=10.0, value=1.0, step=0.1,
    help="거래 성사 시 매출액 대비 수수료율"
)
commission_rate = commission_rate_percent / 100.0

# 5. 커미션 존속 기간
commission_duration_years = st.sidebar.slider(
    "5. 커미션 존속 기간 (년)", 
    min_value=1, max_value=5, value=1, step=1,
    help="한 번 성사된 거래에서 커미션이 발생하는 지속 기간 (재발주 가정)"
)
commission_duration_months = commission_duration_years * 12

st.sidebar.markdown("---")
st.sidebar.info(
    """
    **ℹ️ 고정 가정 (Fixed Assumptions)**
    - **기간:** 36개월 (26.01 ~ 28.12)
    - **거래 전환율:** 20% (미팅 5건 중 1건)
    - **평균 거래액:** $100,000
    - **바이어 활동성:** 연차별 증가 (0.25회 → 0.5회 → 0.83회/월)
    """
)

# -----------------------------------------------------------------------------
# 3. Calculation Logic (Simulation Engine)
# -----------------------------------------------------------------------------

# 고정 변수
TICKET_SIZE = 100000  # $100,000
CONVERSION_RATE = 0.20 # 20%

# 데이터 저장을 위한 리스트
simulation_data = []
dates = pd.date_range(start='2026-01-01', periods=36, freq='MS')
new_deals_history = [] # 과거 거래 건수 추적용 (Recurring Revenue 계산)

for i, date in enumerate(dates):
    year = date.year
    month_idx = i  # 0부터 시작하는 경과 개월 수
    
    # 3-1. 바이어 활동성 (Buyer Activity) 결정
    if year == 2026:
        activity_per_month = 3 / 12  # 연 3회 -> 월 0.25회
    elif year == 2027:
        activity_per_month = 6 / 12  # 연 6회 -> 월 0.5회
    else: # 2028
        activity_per_month = 10 / 12 # 연 10회 -> 월 0.83회
        
    # 3-2. 활성 바이어 수 계산
    current_buyers = initial_buyers + (month_idx * monthly_growth)
    
    # 3-3. 미팅 매출 (Revenue A)
    monthly_meetings = current_buyers * activity_per_month
    revenue_meeting = monthly_meetings * meeting_fee
    
    # 3-4. 신규 거래 건수
    new_deals = monthly_meetings * CONVERSION_RATE
    new_deals_history.append(new_deals)
    
    # 3-5. 커미션 매출 (Revenue B) - Recurring Logic
    # 최근 N개월(존속 기간) 동안 발생한 거래 건수의 합을 구함 (해당 거래들이 이번 달에도 매출 발생)
    # 예: 존속 기간 12개월이면, 이번 달 포함 과거 11개월 전까지의 신규 거래 합계
    start_idx = max(0, len(new_deals_history) - commission_duration_months)
    active_recurring_deals = sum(new_deals_history[start_idx:])
    
    revenue_commission = active_recurring_deals * TICKET_SIZE * commission_rate
    
    # 데이터 집계
    total_revenue = revenue_meeting + revenue_commission
    
    simulation_data.append({
        "Date": date,
        "Year": str(year),
        "YearMonth": date.strftime("%Y-%m"),
        "Active Buyers": int(current_buyers),
        "Monthly Meetings": round(monthly_meetings, 1),
        "New Deals": round(new_deals, 1),
        "Cumulative Active Deals": round(active_recurring_deals, 1),
        "Meeting Revenue": revenue_meeting,
        "Commission Revenue": revenue_commission,
        "Total Revenue": total_revenue
    })

# DataFrame 생성
df = pd.DataFrame(simulation_data)

# -----------------------------------------------------------------------------
# 4. KPI Summary
# -----------------------------------------------------------------------------
total_revenue_3yr = df["Total Revenue"].sum()
revenue_2028 = df[df["Year"] == "2028"]["Total Revenue"].sum()
avg_monthly_rev_2028 = revenue_2028 / 12
commission_share_2028 = (df[df["Year"] == "2028"]["Commission Revenue"].sum() / revenue_2028) * 100

st.subheader("📊 Key Performance Indicators (KPIs)")
col1, col2, col3, col4 = st.columns(4)

with col1:
    st.metric(label="3개년 총 누적 매출", value=f"${total_revenue_3yr:,.0f}")
with col2:
    st.metric(label="2028년 월평균 매출", value=f"${avg_monthly_rev_2028:,.0f}")
with col3:
    st.metric(label="2028년 커미션 비중", value=f"{commission_share_2028:.1f}%")
with col4:
    st.metric(label="최종 활성 바이어 수", value=f"{df['Active Buyers'].iloc[-1]:,}명")

# -----------------------------------------------------------------------------
# 5. Visualizations
# -----------------------------------------------------------------------------

# Layout: Chart 1 and Chart 2
tab1, tab2 = st.tabs(["💰 매출 구성 (Revenue Stack)", "👥 바이어 성장 추이 (Buyer Growth)"])

with tab1:
    st.markdown("##### 월별 매출 구성 변화 (Meeting vs Commission)")
    # Stacked Bar Chart
    fig_rev = go.Figure()
    
    fig_rev.add_trace(go.Bar(
        x=df["Date"], y=df["Meeting Revenue"],
        name="Meeting Revenue", marker_color='#4C78A8' # Blueish
    ))
    fig_rev.add_trace(go.Bar(
        x=df["Date"], y=df["Commission Revenue"],
        name="Commission Revenue", marker_color='#F58518' # Orangeish
    ))
    
    fig_rev.update_layout(
        barmode='stack',
        xaxis_title="Month",
        yaxis_title="Revenue ($)",
        hovermode="x unified",
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
    )
    st.plotly_chart(fig_rev, use_container_width=True)
    st.caption("💡 **Insight:** 초기에는 미팅 매출이 주를 이루지만, 시간이 지날수록 누적된 거래에서 발생하는 커미션 매출이 급증하는지 확인하세요.")

with tab2:
    st.markdown("##### 활성 바이어 및 거래 건수 증가 추이")
    
    fig_growth = go.Figure()
    
    # 왼쪽 Y축: 바이어 수
    fig_growth.add_trace(go.Scatter(
        x=df["Date"], y=df["Active Buyers"],
        name="Active Buyers", mode='lines+markers', line=dict(color='#2CA02C', width=3)
    ))
    
    # 오른쪽 Y축: 월 미팅 수
    fig_growth.add_trace(go.Scatter(
        x=df["Date"], y=df["Monthly Meetings"],
        name="Monthly Meetings", mode='lines', line=dict(color='#D62728', dash='dot'),
        yaxis="y2"
    ))
    
    fig_growth.update_layout(
        xaxis_title="Month",
        yaxis=dict(title="Active Buyers"),
        yaxis2=dict(title="Monthly Meetings", overlaying="y", side="right"),
        hovermode="x unified",
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
    )
    st.plotly_chart(fig_growth, use_container_width=True)

# -----------------------------------------------------------------------------
# 6. Data Table & Download
# -----------------------------------------------------------------------------
st.markdown("### 📝 상세 데이터 테이블")

# 보여줄 컬럼 선택 및 포맷팅
display_df = df[[
    "YearMonth", "Active Buyers", "Monthly Meetings", "New Deals", 
    "Cumulative Active Deals", "Meeting Revenue", "Commission Revenue", "Total Revenue"
]].copy()

# 포맷팅 적용 (화면 표시용)
format_dict = {
    "Meeting Revenue": "${:,.0f}",
    "Commission Revenue": "${:,.0f}",
    "Total Revenue": "${:,.0f}",
    "Monthly Meetings": "{:,.1f}",
    "New Deals": "{:,.1f}",
    "Cumulative Active Deals": "{:,.1f}"
}

st.dataframe(
    display_df.style.format(format_dict),
    use_container_width=True,
    height=300
)

# CSV 다운로드 버튼
csv = display_df.to_csv(index=False).encode('utf-8')
st.download_button(
    label="📥 전체 데이터 다운로드 (CSV)",
    data=csv,
    file_name='tridge_revenue_simulation.csv',
    mime='text/csv',
)
