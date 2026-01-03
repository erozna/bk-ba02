import streamlit as st
import random
import matplotlib.pyplot as plt
import pandas as pd

# 1. 페이지 설정
st.set_page_config(page_title="바카라 전략 분석기 Pro", layout="wide")
st.title("📊 바카라 12종 전략 통합 시뮬레이터")

# 전략 설명서
with st.expander("💡 전략 및 수익 계산 룰 확인"):
    st.markdown("""
    * **금액 표시:** 모든 수익은 '원' 단위로 표시됩니다.
    * **뱅커 식스(B6) 룰:** 뱅커 베팅 승리 시, 6점으로 이기면 수익의 **50%만 지급**합니다.
    * **시스템 리셋:** 마틴/역마틴은 **승리하거나 설정한 최대 단계에 도달**하면 초기화됩니다.
    * **전전 따라가기:** 2판 전의 결과와 동일한 곳에 베팅합니다.
    """)

# 2. 사이드바 설정
st.sidebar.header("🕹️ 공통 설정")
num_games = st.sidebar.slider("생성할 판 수", 30, 200, 72)
unit_bet_input = st.sidebar.number_input("기본 베팅액 (만원)", 1, 30, 1)
unit_bet = unit_bet_input * 10000
max_steps = st.sidebar.slider("시스템 최대 단계", 2, 4, 3)
MAX_LIMIT = 300000 

def run_simulation(results_raw, b6_flags, pos_type, sys_type):
    balance = 0
    current_step = 1
    balance_history = [0]
    detailed_logs = []
    
    for i in range(len(results_raw)):
        actual = results_raw[i]
        b6_event = b6_flags[i]
        
        # [포지션 결정]
        bet_on = None
        if pos_type == "플레이어 올인": bet_on = "P"
        elif pos_type == "뱅커 올인": bet_on = "B"
        elif pos_type == "전전 따라가기":
            bet_on = results_raw[i-2] if i >= 2 else "P"
        elif pos_type == "반대로 꺾기":
            prev = results_raw[i-1] if i >= 1 else "P"
            bet_on = "B" if prev == "P" else "P"

        # [베팅 금액 결정]
        if sys_type == "고정 베팅": bet_amount = unit_bet
        else: bet_amount = unit_bet * (2 ** (current_step - 1))
        
        if bet_amount > MAX_LIMIT: bet_amount = unit_bet 

        # [수익 판정]
        pnl = 0
        note = ""
        if actual != 'T':
            if bet_on == actual: # 승리
                if bet_on == 'B' and b6_event:
                    pnl = bet_amount * 0.5
                    note = "B6(50%)"
                else:
                    pnl = bet_amount
                current_step = 1 
            else: # 패배
                pnl = -bet_amount
                if current_step >= max_steps: current_step = 1
                else: current_step += 1
        
        balance += pnl
        balance_history.append(balance)
        detailed_logs.append({
            "판": i+1,
            "결과": actual,
            "베팅위치": bet_on,
            "베팅금액": f"{int(bet_amount):,}원",
            "수익": f"{int(pnl):,}원",
            "누적손익": f"{int(balance):,}원",
            "비고": note
        })
        
    return int(balance), balance_history, detailed_logs

if st.sidebar.button("전체 전략 시뮬레이션 실행"):
    # 데이터 생성
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
            summary_data.append({
                "포지션 전략": pos,
                "베팅 시스템": sys,
                "최종 수익(원)": final_profit
            })
            all_histories[strategy_name] = history
            all_logs[strategy_name] = logs

    # 3. 결과 테이블 (수익 순위 정렬 및 원 단위 표시)
    df_summary = pd.DataFrame(summary_data)
    df_summary = df_summary.sort_values(by="최종 수익(원)", ascending=False).reset_index(drop=True)
    df_summary.index = df_summary.index + 1
    
    # 원 단위 콤마 포맷팅 함수
    def format_krw(val):
        return f"{int(val):,}원"

    st.subheader("🏆 전략별 수익 순위")
    
    def style_profit(val):
        color = '#FF0000' if val > 0 else '#0000FF'
        return f'color: {color}; font-weight: 900; font-size: 16px'

    # 화면 표시용 복사본
    df_display = df_summary.copy()
    df_display["최종 수익(원)"] = df_display["최종 수익(원)"].apply(format_krw)
    
    st.dataframe(
        df_summary.style.applymap(style_profit, subset=['최종 수익(원)']).format({'최종 수익(원)': '{:,.0f}원'}),
        use_container_width=True
    )

    # 4. 상세 내역 조회 (새로 추가된 기능)
    st.divider()
    st.subheader("🔍 전략별 상세 베팅 내역")
    selected_strategy = st.selectbox("상세 정보를 볼 전략을 선택하세요:", list(all_logs.keys()))
    
    if selected_strategy:
        st.write(f"**[{selected_strategy}]** 전략의 판별 상세 기록입니다.")
        df_logs = pd.DataFrame(all_logs[selected_strategy])
        st.table(df_logs) # 데이터가 길 경우를 위해 테이블 형태로 표시

    # 5. 수익 차트
    st.subheader("📈 전략별 누적 수익 비교 차트")
    st.line_chart(pd.DataFrame({k: v for k, v in all_histories.items()}))
