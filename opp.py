import streamlit as st
import random
import matplotlib.pyplot as plt
import pandas as pd

# 1. 페이지 설정
st.set_page_config(page_title="바카라 전략 분석기 Pro", layout="wide")
st.title("📊 바카라 12종 전략 통합 시뮬레이터")

# 전략 설명서 (세션 상태 사용 설명 포함)
with st.expander("💡 사용법 및 룰 확인"):
    st.markdown("""
    * **데이터 유지:** '시뮬레이션 실행' 버튼을 한 번 누르면 데이터가 고정됩니다. 이후 하단에서 전략을 바꿔가며 상세 내역을 보셔도 리셋되지 않습니다.
    * **뱅커 식스(B6) 룰:** 뱅커 승리 시 6점으로 이기면 수익의 50%만 지급합니다.
    * **시스템 리셋:** 승리하거나 설정한 최대 단계 도달 시 초기화됩니다.
    """)

# 2. 사이드바 설정
st.sidebar.header("🕹️ 공통 설정")
num_games = st.sidebar.slider("생성할 판 수", 30, 200, 72)
unit_bet_input = st.sidebar.number_input("기본 베팅액 (만원)", 1, 30, 1)
unit_bet = unit_bet_input * 10000
max_steps = st.sidebar.slider("시스템 최대 단계", 2, 4, 3)
MAX_LIMIT = 300000 

# 시뮬레이션 엔진 (기존 로직 유지)
def run_simulation(results_raw, b6_flags, pos_type, sys_type):
    balance = 0
    current_step = 1
    balance_history = [0]
    detailed_logs = []
    
    for i in range(len(results_raw)):
        actual = results_raw[i]
        b6_event = b6_flags[i]
        
        # [포지션 로직]
        if pos_type == "플레이어 올인": bet_on = "P"
        elif pos_type == "뱅커 올인": bet_on = "B"
        elif pos_type == "전전 따라가기": bet_on = results_raw[i-2] if i >= 2 else "P"
        elif pos_type == "반대로 꺾기":
            prev = results_raw[i-1] if i >= 1 else "P"
            bet_on = "B" if prev == "P" else "P"

        # [베팅 금액 로직]
        if sys_type == "고정 베팅": bet_amount = unit_bet
        else: bet_amount = unit_bet * (2 ** (current_step - 1))
        if bet_amount > MAX_LIMIT: bet_amount = unit_bet 

        # [수익 판정]
        pnl = 0
        note = ""
        if actual != 'T':
            if bet_on == actual:
                pnl = bet_amount * 0.5 if (bet_on == 'B' and b6_event) else bet_amount
                current_step = 1 
            else:
                pnl = -bet_amount
                if current_step >= max_steps: current_step = 1
                else: current_step += 1
        
        balance += pnl
        balance_history.append(balance)
        detailed_logs.append({"판": i+1, "결과": actual, "베팅": bet_on, "금액": f"{int(bet_amount):,}원", "수익": f"{int(pnl):,}원", "누적": f"{int(balance):,}원", "비고": note})
        
    return int(balance), balance_history, detailed_logs

# 3. 데이터 생성 및 시뮬레이션 실행 (중요: 세션 상태에 저장)
if st.sidebar.button("전체 전략 시뮬레이션 실행"):
    results_raw = []
    b6_flags = []
    for _ in range(num_games):
        res = random.choices(['B', 'P', 'T'], weights=[45.8, 44.6, 9.6], k=1)[0]
        results_raw.append(res)
        b6_flags.append(res == 'B' and random.random() < 0.12)

    pos_strategies = ["플레이어 올인", "뱅커 올인", "전전 따라가기", "반대로 꺾기"]
    sys_strategies = ["고정 베팅", "마틴게일", "역마틴게일"]
    
    summary_data = []
    all_histories = {}
    all_logs = {}

    for pos in pos_strategies:
        for sys in sys_strategies:
            final_profit, history, logs = run_simulation(results_raw, b6_flags, pos, sys)
            strategy_name = f"{pos} | {sys}"
            summary_data.append({"포지션 전략": pos, "베팅 시스템": sys, "최종 수익(원)": final_profit})
            all_histories[strategy_name] = history
            all_logs[strategy_name] = logs

    # 세션 상태에 데이터 저장
    st.session_state['results_raw'] = results_raw
    st.session_state['summary_data'] = summary_data
    st.session_state['all_histories'] = all_histories
    st.session_state['all_logs'] = all_logs

# 4. 화면 출력부 (세션 상태에 데이터가 있을 때만 표시)
if 'results_raw' in st.session_state:
    # 출목표 그래프
    st.subheader("🔵 이번 슈의 결과 (출목표)")
    x, y, colors, types, curr_x, curr_y, prev_r = [], [], [], [], 0, 0, None
    for res in [r for r in st.session_state['results_raw'] if r != 'T']:
        if prev_r and res != prev_r: curr_x += 1; curr_y = 0
        elif prev_r and res == prev_r: 
            curr_y += 1
            if curr_y >= 6: curr_y = 5; curr_x += 1
        x.append(curr_x); y.append(curr_y); colors.append('red' if res == 'B' else 'blue'); types.append(res); prev_r = res
    fig, ax = plt.subplots(figsize=(12, 2))
    for i in range(len(x)):
        ax.add_patch(plt.Circle((x[i], 5-y[i]), 0.35, color=colors[i], fill=False, lw=2))
        ax.text(x[i], 5-y[i], types[i], color=colors[i], ha='center', va='center', fontsize=7, fontweight='bold')
    ax.set_xlim(-0.5, max(x)+1 if x else 10); ax.set_ylim(-0.5, 5.5); ax.set_aspect('equal'); plt.axis('off')
    st.pyplot(fig)

    # 요약 테이블
    st.subheader("🏆 전략별 수익 순위")
    df_summary = pd.DataFrame(st.session_state['summary_data']).sort_values(by="최종 수익(원)", ascending=False).reset_index(drop=True)
    df_summary.index = df_summary.index + 1
    
    def style_profit(val):
        color = '#FF0000' if val > 0 else '#1976D2'
        return f'color: {color}; font-weight: 900; font-size: 16px'

    st.dataframe(df_summary.style.applymap(style_profit, subset=['최종 수익(원)']).format({'최종 수익(원)': '{:,.0f}원'}), use_container_width=True)

    # 수익 추이 그래프
    st.subheader("📈 전략별 누적 수익 비교")
    st.line_chart(pd.DataFrame(st.session_state['all_histories']))

    # 상세 내역 (이제 리셋되지 않습니다!)
    st.divider()
    st.subheader("🔍 전략별 상세 베팅 내역")
    selected_strategy = st.selectbox("상세 정보를 볼 전략을 선택하세요:", list(st.session_state['all_logs'].keys()))
    
    if selected_strategy:
        st.write(f"**[{selected_strategy}]** 전략 기록")
        st.table(pd.DataFrame(st.session_state['all_logs'][selected_strategy]))
