import streamlit as st
import random
import matplotlib.pyplot as plt
import pandas as pd

# 1. 페이지 설정
st.set_page_config(page_title="바카라 전략 분석기 Pro", layout="wide")
st.title("📊 바카라 13종 전략 통합 시뮬레이터")

with st.expander("💡 사용법 및 전략 설명"):
    st.markdown("""
    * **타이 표시:** 출목표 원 위에 녹색 사선과 숫자로 표시됩니다.
    * **전략:** 밑줄(줄타기), 전전 따라가기, 반대로 꺾기 등 13종을 동시 분석합니다.
    * **뱅커식스(B6):** 뱅커 6점 승리 시 수익의 50%만 지급하는 룰을 반영합니다.
    """)

# 2. 사이드바 설정
st.sidebar.header("🕹️ 공통 설정")
num_games = st.sidebar.slider("생성할 판 수", 30, 200, 72)
unit_bet_input = st.sidebar.number_input("기본 베팅액 (만원)", 1, 30, 1)
unit_bet = unit_bet_input * 10000
max_steps = st.sidebar.slider("시스템 최대 단계", 2, 4, 3)
MAX_LIMIT = 500000 

def run_simulation(results_raw, b6_flags, pos_type, sys_type):
    balance, current_step = 0, 1
    balance_history = [0]
    detailed_logs, pure_results = [], []
    
    for i in range(len(results_raw)):
        actual = results_raw[i]
        b6_event = b6_flags[i]
        
        # [포지션 결정]
        bet_on = None
        if pos_type == "플레이어에만 베팅": bet_on = "P"
        elif pos_type == "뱅커에만 베팅": bet_on = "B"
        elif pos_type == "밑줄 따라가기": bet_on = pure_results[-1] if len(pure_results) >= 1 else "P"
        elif pos_type == "전전 결과 따라가기": bet_on = pure_results[-2] if len(pure_results) >= 2 else "P"
        elif pos_type == "반대로 꺾기":
            if len(pure_results) >= 1: bet_on = "B" if pure_results[-1] == "P" else "P"
            else: bet_on = "P"

        # [베팅 금액]
        if sys_type == "고정 베팅": bet_amount = unit_bet
        else: bet_amount = unit_bet * (2 ** (current_step - 1))
        if bet_amount > MAX_LIMIT: bet_amount = unit_bet 

        # [수익 판정]
        pnl, note = 0, ""
        if actual == 'T': pnl = 0 
        else:
            if bet_on == actual:
                pnl = bet_amount * 0.5 if (bet_on == 'B' and b6_event) else bet_amount
                current_step = 1 
            else:
                pnl = -bet_amount
                current_step = min(current_step + 1, max_steps) if current_step < max_steps else 1
            pure_results.append(actual)
        
        balance += pnl
        balance_history.append(balance)
        detailed_logs.append({"판": i+1, "결과": actual, "베팅": bet_on, "금액": f"{int(bet_amount):,}원", "수익": f"{int(pnl):,}원", "누적": f"{int(balance):,}원", "비고": note})
        
    return int(balance), balance_history, detailed_logs

# 3. 실행 버튼 및 데이터 생성
if st.sidebar.button("전체 시뮬레이션 실행"):
    results_raw = random.choices(['B', 'P', 'T'], weights=[45.8, 44.6, 9.6], k=num_games)
    b6_flags = [res == 'B' and random.random() < 0.12 for res in results_raw]

    pos_strategies = ["플레이어에만 베팅", "뱅커에만 베팅", "밑줄 따라가기", "전전 결과 따라가기", "반대로 꺾기"]
    sys_strategies = ["고정 베팅", "마틴게일", "역마틴게일"]
    
    summary_data, all_histories, all_logs = [], {}, {}
    for pos in pos_strategies:
        for sys in sys_strategies:
            final_profit, history, logs = run_simulation(results_raw, b6_flags, pos, sys)
            strategy_name = f"{pos} | {sys}"
            summary_data.append({"포지션 전략": pos, "베팅 시스템": sys, "최종 수익(원)": final_profit})
            all_histories[strategy_name] = history
            all_logs[strategy_name] = logs

    st.session_state.update({'results_raw': results_raw, 'b6_flags': b6_flags, 'summary_data': summary_data, 'all_histories': all_histories, 'all_logs': all_logs})

# 4. 화면 출력부
if 'results_raw' in st.session_state:
    res_list = st.session_state['results_raw']
    b6_list = st.session_state['b6_flags']
    
    # --- 통계 카드 (오류 수정 지점) ---
    st.subheader("📊 이번 슈 출현 통계")
    total = len(res_list)
    b, p, t = res_list.count('B'), res_list.count('P'), res_list.count('T')
    b6 = sum(b6_list)

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("뱅커(B)", f"{b}회", f"{(b/total)*100:.1f}%")
    c2.metric("플레이어(P)", f"{p}회", f"{(p/total)*100:.1f}%")
    c3.metric("타이(T)", f"{t}회", f"{(t/total)*100:.1f}%")
    c4.metric("뱅커식스(B6)", f"{b6}회", f"{(b6/total)*100:.1f}%", delta_color="inverse")

    # --- 출목표 (타이 표시 포함) ---
    st.subheader("🔵 이번 슈의 결과 (출목표 - 타이 포함)")
    
    x, y, colors, types, tie_counts = [], [], [], [], []
    curr_x, curr_y, prev_r = 0, 0, None
    for res in res_list:
        if res == 'T':
            if len(tie_counts) > 0: tie_counts[-1] += 1
            continue
        if prev_r and res != prev_r: curr_x += 1; curr_y = 0
        elif prev_r and res == prev_r:
            curr_y += 1
            if curr_y >= 6: curr_y = 5; curr_x += 1
        x.append(curr_x); y.append(curr_y); colors.append('red' if res == 'B' else 'blue'); types.append(res); tie_counts.append(0); prev_r = res

    fig, ax = plt.subplots(figsize=(12, 2.5))
    for i in range(len(x)):
        ax.add_patch(plt.Circle((x[i], 5-y[i]), 0.35, color=colors[i], fill=False, lw=2))
        ax.text(x[i], 5-y[i], types[i], color=colors[i], ha='center', va='center', fontsize=7, fontweight='bold')
        if tie_counts[i] > 0:
            ax.text(x[i]+0.25, 5-y[i]+0.25, str(tie_counts[i]), color='green', fontsize=8, fontweight='bold')
            ax.plot([x[i]-0.2, x[i]+0.2], [5-y[i]-0.2, 5-y[i]+0.2], color='green', lw=1.5)
    ax.set_xlim(-0.5, max(x)+1 if x else 10); ax.set_ylim(-0.5, 5.5); ax.set_aspect('equal'); plt.axis('off')
    st.pyplot(fig)

    # --- 순위 테이블 및 상세 내역 (생략 없이 유지) ---
    st.subheader("🏆 전략별 수익 순위")
    df_summary = pd.DataFrame(st.session_state['summary_data']).sort_values(by="최종 수익(원)", ascending=False).reset_index(drop=True)
    df_summary.index += 1
    st.dataframe(df_summary.style.applymap(lambda v: f"color: {'#FF0000' if v > 0 else '#1976D2'}; font-weight: 900", subset=['최종 수익(원)']).format({'최종 수익(원)': '{:,.0f}원'}), use_container_width=True)

    st.subheader("📈 전략별 누적 수익 비교")
    st.line_chart(pd.DataFrame(st.session_state['all_histories']))

    st.divider()
    st.subheader("🔍 전략별 상세 베팅 내역")
    selected_strategy = st.selectbox("전략을 선택하세요:", list(st.session_state['all_logs'].keys()))
    if selected_strategy:
        st.table(pd.DataFrame(st.session_state['all_logs'][selected_strategy]))
