import streamlit as st
import random
import matplotlib.pyplot as plt
import pandas as pd

# 1. 페이지 설정
st.set_page_config(page_title="바카라 전략 분석기 Pro", layout="wide")
st.title("📊 바카라 12종 전략 통합 시뮬레이터")

# 전략에 대한 친절한 설명 추가
with st.expander("💡 전략 설명서 (클릭하여 확인)"):
    st.markdown("""
    **[포지션 전략]**
    * **플레이어 올인:** 무조건 플레이어(P)에게만 베팅합니다.
    * **뱅커 올인:** 무조건 뱅커(B)에게만 베팅합니다. (6점 승리 시 50% 수익 룰 적용)
    * **전전 결과 따라가기:** 이번 판이 아닌, 2판 전의 결과와 동일하게 베팅합니다.
    * **반대로 꺾기:** 직전 결과의 반대(P가 나오면 B, B가 나오면 P)로 베팅합니다.

    **[베팅 시스템]**
    * **고정 베팅:** 수익/손실에 상관없이 항상 동일한 금액을 베팅합니다.
    * **마틴게일:** 패배 시 베팅금을 2배로 올립니다. 승리하거나 최대 단계 도달 시 초기화됩니다.
    * **역마틴게일:** 승리 시 베팅금을 2배로 올립니다. 패배하거나 최대 단계 도달 시 초기화됩니다.
    """)

# 2. 사이드바 설정
st.sidebar.header("🕹️ 공통 설정")
num_games = st.sidebar.slider("생성할 판 수", 30, 200, 72)
unit_bet = st.sidebar.number_input("기본 베팅액 (만원)", 1, 30, 1) * 10000
max_steps = st.sidebar.slider("시스템 최대 단계 (마틴/역마틴)", 2, 4, 3)
MAX_LIMIT = 300000 

def run_simulation(results_raw, b6_flags, pos_type, sys_type):
    balance = 0
    current_step = 1
    balance_history = [0]
    
    for i in range(len(results_raw)):
        actual = results_raw[i]
        b6_event = b6_flags[i]
        
        # [포지션 로직]
        bet_on = None
        if pos_type == "플레이어 올인": bet_on = "P"
        elif pos_type == "뱅커 올인": bet_on = "B"
        elif pos_type == "전전 따라가기":
            bet_on = results_raw[i-2] if i >= 2 else "P"
        elif pos_type == "반대로 꺾기":
            prev = results_raw[i-1] if i >= 1 else "P"
            bet_on = "B" if prev == "P" else "P"

        # [베팅 금액 로직]
        if sys_type == "고정 베팅": 
            bet_amount = unit_bet
        else: 
            bet_amount = unit_bet * (2 ** (current_step - 1))
        
        if bet_amount > MAX_LIMIT: bet_amount = unit_bet 

        # [결과 판정]
        pnl = 0
        if actual == 'T': 
            pnl = 0
        else:
            if bet_on == actual: # 승리
                pnl = bet_amount * 0.5 if (bet_on == 'B' and b6_event) else bet_amount
                # 승리 시 리셋 (마틴/역마틴 공통)
                current_step = 1 
            else: # 패배
                pnl = -bet_amount
                # 패배 시 단계 상승 (마틴/역마틴 공통으로 단계 조절 로직 적용)
                if current_step >= max_steps: current_step = 1
                else: current_step += 1
                
        balance += pnl
        balance_history.append(balance)
        
    return int(balance), balance_history

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
    all_history = {}

    for pos in pos_strategies:
        for sys in sys_strategies:
            final_profit, history = run_simulation(results_raw, b6_flags, pos, sys)
            strategy_name = f"{pos} + {sys}"
            summary_data.append({
                "포지션 전략": pos,
                "베팅 시스템": sys,
                "최종 수익(만원)": final_profit / 10000
            })
            all_history[strategy_name] = history

    # 출목표 출력
    st.subheader("🔵 생성된 게임 슈 (출목표)")
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

    # 결과 테이블 출력 (색상 개선)
    st.subheader("📋 12종 전략 통합 분석 결과")
    df_summary = pd.DataFrame(summary_data)
    
    def color_profit(val):
        # 수익이 0보다 크면 짙은 빨간색, 작으면 짙은 파란색 (가독성 증대)
        color = '#D32F2F' if val > 0 else '#1976D2'
        return f'color: {color}; font-weight: bold'
    
    st.dataframe(
        df_summary.style.applymap(color_profit, subset=['최종 수익(만원)']), 
        use_container_width=True
    )

    # 수익 추이 그래프
    st.subheader("📈 전략별 수익 추이 비교")
    chart_data = pd.DataFrame({k: v for k, v in all_history.items()})
    st.line_chart(chart_data)

    # 다운로드 버튼
    csv = df_summary.to_csv(index=False).encode('utf-8-sig')
    st.download_button("📊 분석 결과 다운로드 (엑셀용)", csv, "baccarat_strategy.csv", "text/csv")
