import streamlit as st
import random
import matplotlib.pyplot as plt
import pandas as pd

# 1. 페이지 설정
st.set_page_config(page_title="바카라 전략 분석기 Pro", layout="wide")
st.title("📊 바카라 13종 전략 통합 시뮬레이터")

with st.expander("💡 사용법 및 전략 설명"):
    st.markdown("""
    * **플레이어/뱅커에만 베팅:** 한 쪽 포지션만 고수합니다.
    * **밑줄 따라가기:** 직전 결과(타이 제외)와 동일한 곳에 베팅합니다. (줄타기 전략)
    * **전전 결과 따라가기:** 두 판 전 결과(타이 제외)와 동일하게 베팅합니다.
    * **반대로 꺾기:** 직전 결과(타이 제외)의 반대편에 베팅합니다.
    * **확률 통계:** 이번 슈에서 실제로 발생한 각 결과의 빈도와 확률을 보여줍니다.
    """)

# 2. 사이드바 설정
st.sidebar.header("🕹️ 공통 설정")
num_games = st.sidebar.slider("생성할 판 수", 30, 200, 72)
unit_bet_input = st.sidebar.number_input("기본 베팅액 (만원)", 1, 30, 1)
unit_bet = unit_bet_input * 10000
max_steps = st.sidebar.slider("시스템 최대 단계", 2, 4, 3)
MAX_LIMIT = 500000 # 베팅 한도 상향

def run_simulation(results_raw, b6_flags, pos_type, sys_type):
    balance = 0
    current_step = 1
    balance_history = [0]
    detailed_logs = []
    pure_results = [] # 타이 제외 결과
    
    for i in range(len(results_raw)):
        actual = results_raw[i]
        b6_event = b6_flags[i]
        
        # [포지션 로직]
        bet_on = None
        if pos_type == "플레이어에만 베팅": bet_on = "P"
        elif pos_type == "뱅커에만 베팅": bet_on = "B"
        elif pos_type == "밑줄 따라가기":
            bet_on = pure_results[-1] if len(pure_results) >= 1 else "P"
        elif pos_type == "전전 결과 따라가기":
            bet_on = pure_results[-2] if len(pure_results) >= 2 else "P"
        elif pos_type == "반대로 꺾기":
            if len(pure_results) >= 1:
                bet_on = "B" if pure_results[-1] == "P" else "P"
            else: bet_on = "P"

        # [베팅 금액 로직]
        if sys_type == "고정 베팅": bet_amount = unit_bet
        else: bet_amount = unit_bet * (2 ** (current_step - 1))
        if bet_amount > MAX_LIMIT: bet_amount = unit_bet 

        # [수익 판정]
        pnl = 0
        note = ""
        if actual == 'T': 
            pnl = 0 
        else:
            if bet_on == actual:
                if bet_on == 'B' and b6_event:
                    pnl = bet_amount * 0.5
                    note = "B6 당첨(50%)"
                else: pnl = bet_amount
                current_step = 1 
            else:
                pnl = -bet_amount
                if current_step >= max_steps: current_step = 1
                else: current_step += 1
            pure_results.append(actual)
        
        balance += pnl
        balance_history.append(balance)
        detailed_logs.append({
            "판": i+1, "결과": actual, "베팅": bet_on, 
            "금액": f"{int(bet_amount):,}원", "수익": f"{int(pnl):,}원", 
            "누적": f"{int(balance):,}원", "비고": note
        })
        
    return int(balance), balance_history, detailed_logs

# 3. 데이터 생성 및 실행
if st.sidebar.button("전체 시뮬레이션 실행"):
    results_raw = []
    b6_flags = []
    for _ in range(num_games):
        res = random.choices(['B', 'P', 'T'], weights=[45.8, 44.6, 9.6], k=1)[0]
        results_raw.append(res)
        b6_flags.append(res == 'B' and random.random() < 0.12) # 뱅커 승리 중 약 12%가 B6

    # 전략 리스트 업데이트
    pos_strategies = ["플레이어에만 베팅", "뱅커에만 베팅", "밑줄 따라가기", "전전 결과 따라가기", "반대로 꺾기"]
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

    st.session_state['results_raw'] = results_raw
    st.session_state['b6_flags'] = b6_flags
    st.session_state['summary_data'] = summary_data
    st.session_state['all_histories'] = all_histories
    st.session_state['all_logs'] = all_logs

# 4. 화면 출력부
if 'results_raw' in st.session_state:
    # 4-1. 통계 정보 계산
    res_list = st.session_state['results_raw']
    b6_list = st.session_state['b6_flags']
    total = len(res_list)
    b_count = res_list.count('B')
    p_count = res_list.count('P')
    t_count = res_list.count('T')
    b6_count = sum(b6_list)

    st.subheader("📊 이번 슈 출현 통계")
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("뱅커(B)", f"{b_count}회", f"{(b_count/total)*100:.1f}%")
    col2.metric("플레이어(P)", f"{p_count}회", f"{(p_count/total)*100:.1f}%")
    col3.metric("타이(T)", f"{t_count}회", f"{(t_count/total)*100:.1f}%")
    col4.metric("뱅커식스(B6)", f"{b6_count}회", f"{(b6_count/total)*100:.1f}%", delta_color="inverse")

    # 4-2. 출목표 그래프
    st.subheader("🔵 이번 슈의 결과 (출목표)")
    x, y, colors, types, curr_x, curr_y, prev_r = [], [], [], [], 0, 0, None
    for idx, res in enumerate([r for r in res_list if r != 'T']):
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

    # 4-3. 순위 테이블
    st.subheader("🏆 전략별 수익 순위")
    df_summary = pd.DataFrame(st.session_state['summary_data']).sort_values(by="최종 수익(원)", ascending=False).reset_index(drop=True)
    df_summary.index = df_summary.index + 1
    
    def style_profit(val):
        color = '#FF0000' if val > 0 else '#1976D2'
        return f'color: {color}; font-weight: 900; font-size: 16px'

    st.dataframe(df_summary.style.applymap(style_profit, subset=['최종 수익(원)']).format({'최종 수익(원)': '{:,.0f}원'}), use_container_width=True)

    # 4-4. 누적 차트
    st.subheader("📈 전략별 누적 수익 비교")
    st.line_chart(pd.DataFrame(st.session_state['all_histories']))

    # 4-5. 상세 정보 조회
    st.divider()
    st.subheader("🔍 전략별 상세 베팅 내역")
    selected_strategy = st.selectbox("상세 정보를 볼 전략을 선택하세요:", list(st.session_state['all_logs'].keys()))
    
    if selected_strategy:
        st.write(f"**[{selected_strategy}]** 상세 기록")
        st.table(pd.DataFrame(st.session_state['all_logs'][selected_strategy]))
