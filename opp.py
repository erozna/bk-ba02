import streamlit as st
import random
import matplotlib.pyplot as plt
import pandas as pd

# 1. 페이지 설정
st.set_page_config(page_title="바카라 12종 전략 분석기", layout="wide")
st.title("📊 바카라 12종 전략 통합 시뮬레이터")

# 2. 사이드바 설정
st.sidebar.header("🕹️ 공통 설정")
num_games = st.sidebar.slider("생성할 판 수", 30, 200, 72)
unit_bet = st.sidebar.number_input("기본 베팅액 (만원)", 1, 30, 1) * 10000
max_steps = st.sidebar.slider("마틴/역마틴 최대 단계", 2, 4, 3)
MAX_LIMIT = 300000 # 최대 베팅 한도

# 시뮬레이션 엔진 함수 (재사용을 위해 함수화)
def run_simulation(results_raw, b6_flags, pos_type, sys_type):
    balance = 0
    current_step = 1
    balance_history = [0]
    
    for i in range(len(results_raw)):
        actual = results_raw[i]
        b6_event = b6_flags[i]
        
        # [포지션 로직]
        bet_on = None
        if pos_type == "Always P": bet_on = "P"
        elif pos_type == "Always B": bet_on = "B"
        elif pos_type == "Follow 2-back": # 전전 결과 따라가기
            bet_on = results_raw[i-2] if i >= 2 else "P"
        elif pos_type == "Opposite": # 반대로 꺾기
            prev = results_raw[i-1] if i >= 1 else "P"
            bet_on = "B" if prev == "P" else "P"

        # [베팅 금액 로직]
        if sys_type == "Flat": bet_amount = unit_bet
        else: bet_amount = unit_bet * (2 ** (current_step - 1))
        
        if bet_amount > MAX_LIMIT: bet_amount = unit_bet # 한도 초과 시 리셋

        # [결과 판정]
        pnl = 0
        if actual == 'T': # 타이 시 베팅 유지 (수익 0)
            pnl = 0
        else:
            if bet_on == actual: # 적중
                pnl = bet_amount * 0.5 if (bet_on == 'B' and b6_event) else bet_amount
                # 적중 시 무조건 리셋 (마틴/역마틴 공통)
                current_step = 1 
            else: # 실패
                pnl = -bet_amount
                # 실패 시 단계 상승, 최종단계 도달 시 리셋
                if current_step >= max_steps: current_step = 1
                else: current_step += 1
                
        balance += pnl
        balance_history.append(balance)
        
    return int(balance), balance_history

if st.sidebar.button("전체 전략 시뮬레이션 실행"):
    # 3. 데이터 생성 (한 번 생성한 데이터로 12종 전략에 똑같이 적용)
    results_raw = []
    b6_flags = []
    for _ in range(num_games):
        res = random.choices(['B', 'P', 'T'], weights=[45.8, 44.6, 9.6], k=1)[0]
        results_raw.append(res)
        b6_flags.append(res == 'B' and random.random() < 0.12)

    # 4. 12종 전략 실행
    pos_strategies = ["Always P", "Always B", "Follow 2-back", "Opposite"]
    sys_strategies = ["Flat", "Martingale", "Anti-Martingale"]
    
    summary_data = []
    all_history = {}

    for pos in pos_strategies:
        for sys in sys_strategies:
            final_profit, history = run_simulation(results_raw, b6_flags, pos, sys)
            strategy_name = f"{pos} + {sys}"
            summary_data.append({
                "포지션 전략": pos,
                "베팅 시스템": sys,
                "최종 수익(원)": final_profit,
                "최종 수익(만원)": final_profit / 10000
            })
            all_history[strategy_name] = history

    # 5. 결과 화면 출력
    st.subheader("🔵 본매 출목표 (생성된 슈)")
    # (출목표 그래픽 로직은 기존과 동일)
    x, y, colors, types, curr_x, curr_y, prev_r = [], [], [], [], 0, 0, None
    for res in [r for r in results_raw if r != 'T']:
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

    # 6. 12종 전략 통합 결과 테이블
    st.subheader("📋 12종 전략 통합 분석 결과")
    df_summary = pd.DataFrame(summary_data)
    
    # 수익률에 따라 색상 지정
    def highlight_profit(val):
        color = 'red' if val < 0 else 'blue'
        return f'color: {color}'
    
    st.dataframe(df_summary.style.applymap(highlight_profit, subset=['최종 수익(만원)']), use_container_width=True)

    # 7. 통합 수익 그래프
    st.subheader("📈 전략별 수익 추이 비교")
    chart_data = pd.DataFrame({k: v for k, v in all_history.items()})
    st.line_chart(chart_data)

    # 8. 데이터 다운로드
    csv = df_summary.to_csv(index=False).encode('utf-8-sig')
    st.download_button("📊 12종 요약 결과 다운로드", csv, "strategy_analysis.csv", "text/csv")
