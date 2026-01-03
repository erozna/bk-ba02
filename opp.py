import streamlit as st
import random
import matplotlib.pyplot as plt
import pandas as pd

# 1. 페이지 설정
st.set_page_config(page_title="바카라 전략 분석기 Pro", layout="wide")
st.title("📊 바카라 13종 전략 통합 시뮬레이터")

# 2. 사이드바 및 시뮬레이션 로직 (기존 유지)
st.sidebar.header("🕹️ 공통 설정")
num_games = st.sidebar.slider("생성할 판 수", 30, 200, 72)
unit_bet_input = st.sidebar.number_input("기본 베팅액 (만원)", 1, 30, 1)
unit_bet = unit_bet_input * 10000
max_steps = st.sidebar.slider("시스템 최대 단계", 2, 4, 3)
MAX_LIMIT = 500000 

def run_simulation(results_raw, b6_flags, pos_type, sys_type):
    balance = 0
    current_step = 1
    balance_history = [0]
    detailed_logs = []
    pure_results = [] 
    
    for i in range(len(results_raw)):
        actual = results_raw[i]
        b6_event = b6_flags[i]
        
        # [포지션 및 베팅 로직 생략 - 이전과 동일]
        bet_on = None
        if pos_type == "플레이어에만 베팅": bet_on = "P"
        elif pos_type == "뱅커에만 베팅": bet_on = "B"
        elif pos_type == "밑줄 따라가기": bet_on = pure_results[-1] if len(pure_results) >= 1 else "P"
        elif pos_type == "전전 결과 따라가기": bet_on = pure_results[-2] if len(pure_results) >= 2 else "P"
        elif pos_type == "반대로 꺾기":
            if len(pure_results) >= 1: bet_on = "B" if pure_results[-1] == "P" else "P"
            else: bet_on = "P"

        if sys_type == "고정 베팅": bet_amount = unit_bet
        else: bet_amount = unit_bet * (2 ** (current_step - 1))
        if bet_amount > MAX_LIMIT: bet_amount = unit_bet 

        pnl = 0
        note = ""
        if actual == 'T': 
            pnl = 0 
        else:
            if bet_on == actual:
                pnl = bet_amount * 0.5 if (bet_on == 'B' and b6_event) else bet_amount
                current_step = 1 
            else:
                pnl = -bet_amount
                if current_step >= max_steps: current_step = 1
                else: current_step += 1
            pure_results.append(actual)
        
        balance += pnl
        balance_history.append(balance)
        detailed_logs.append({"판": i+1, "결과": actual, "베팅": bet_on, "금액": f"{int(bet_amount):,}원", "수익": f"{int(pnl):,}원", "누적": f"{int(balance):,}원", "비고": note})
        
    return int(balance), balance_history, detailed_logs

if st.sidebar.button("전체 시뮬레이션 실행"):
    results_raw = []
    b6_flags = []
    for _ in range(num_games):
        res = random.choices(['B', 'P', 'T'], weights=[45.8, 44.6, 9.6], k=1)[0]
        results_raw.append(res)
        b6_flags.append(res == 'B' and random.random() < 0.12)

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

# 3. 화면 출력부
if 'results_raw' in st.session_state:
    # 통계 카드 (생략 - 이전과 동일)
    
    # --- [수정된 출목표 로직] ---
    st.subheader("🔵 이번 슈의 결과 (출목표 - 타이 포함)")
    
    x, y, colors, types, tie_counts = [], [], [], [], []
    curr_x, curr_y = 0, 0
    prev_r = None
    
    # 데이터를 순회하며 좌표와 타이 횟수 계산
    for res in st.session_state['results_raw']:
        if res == 'T':
            if len(tie_counts) > 0:
                tie_counts[-1] += 1 # 직전 결과에 타이 횟수 추가
            continue
        
        if prev_r and res != prev_r:
            curr_x += 1
            curr_y = 0
        elif prev_r and res == prev_r:
            curr_y += 1
            if curr_y >= 6:
                curr_y = 5
                curr_x += 1
        
        x.append(curr_x)
        y.append(curr_y)
        colors.append('red' if res == 'B' else 'blue')
        types.append(res)
        tie_counts.append(0) # 새로운 결과가 나올 때 타이 횟수 0으로 시작
        prev_r = res

    fig, ax = plt.subplots(figsize=(12, 2.5))
    for i in range(len(x)):
        # 메인 원 (P/B)
        circle = plt.Circle((x[i], 5-y[i]), 0.35, color=colors[i], fill=False, lw=2)
        ax.add_patch(circle)
        ax.text(x[i], 5-y[i], types[i], color=colors[i], ha='center', va='center', fontsize=7, fontweight='bold')
        
        # 타이 표시 (숫자가 있으면 녹색으로 표시)
        if tie_counts[i] > 0:
            ax.text(x[i]+0.25, 5-y[i]+0.25, str(tie_counts[i]), color='green', fontsize=8, fontweight='bold')
            # 타이가 있음을 알리는 녹색 사선 효과 (선택사항)
            ax.plot([x[i]-0.2, x[i]+0.2], [5-y[i]-0.2, 5-y[i]+0.2], color='green', lw=1.5)

    ax.set_xlim(-0.5, max(x)+1 if x else 10)
    ax.set_ylim(-0.5, 5.5)
    ax.set_aspect('equal')
    plt.axis('off')
    st.pyplot(fig)
    
    # [순위 테이블 및 차트 생략 - 이전과 동일]
