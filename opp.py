import streamlit as st
import random
import matplotlib.pyplot as plt
import pandas as pd

# 1. 페이지 설정
st.set_page_config(page_title="바카라 전략 시뮬레이터 Pro", layout="wide")
st.title("🎰 AI 바카라 출목표 & 전략 시뮬레이터 (Banker 6 Rule)")

# 2. 사이드바 설정
st.sidebar.header("🕹️ 게임 및 전략 설정")
num_games = st.sidebar.slider("생성할 판 수", 30, 100, 72)
unit_bet = st.sidebar.number_input("기본 베팅액 (만원)", 1, 30, 1) * 10000

st.sidebar.subheader("🎯 포지션 전략")
pos_strategy = st.sidebar.selectbox("베팅 위치", 
    ["항상 뱅커", "항상 플레이어", "직전 결과 따라가기", "반대로 꺾기"])

st.sidebar.subheader("💰 베팅 시스템")
sys_strategy = st.sidebar.selectbox("시스템 선택", ["고정 베팅", "마틴게일", "역마틴게일"])
max_steps = st.sidebar.slider("시스템 단계 (2~4단계)", 2, 4, 3)

MAX_LIMIT = 300000 # 최대 베팅 한도

if st.sidebar.button("시뮬레이션 실행"):
    # 3. 데이터 생성 (뱅커 식스 판단을 위해 점수 데이터도 함께 생성)
    # 실제 카드를 뽑는 대신 뱅커가 6으로 이길 확률(약 5.39%)을 고려하여 로직 구성
    results_raw = []
    is_banker_six = [] # 뱅커가 6으로 이겼는지 여부 저장
    
    for _ in range(num_games):
        res = random.choices(['B', 'P', 'T'], weights=[45.8, 44.6, 9.6], k=1)[0]
        results_raw.append(res)
        # 뱅커가 이겼을 때, 약 12%의 확률로 6점으로 이김 (전체 판수 대비 약 5.4%)
        if res == 'B' and random.random() < 0.12:
            is_banker_six.append(True)
        else:
            is_banker_six.append(False)
    
    # 4. 상단 기본 통계
    b_count, p_count, t_count = results_raw.count('B'), results_raw.count('P'), results_raw.count('T')
    b_six_count = is_banker_six.count(True)
    
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Banker (B6)", f"{b_count}회 ({b_six_count}회)")
    c2.metric("Player", f"{p_count}회")
    c3.metric("Tie", f"{t_count}회")
    c4.metric("Total", f"{len(results_raw)}판")

    # 5. 시뮬레이션 로직
    balance = 0
    balance_history = [0]
    bet_details = []
    current_step = 1

    for i in range(len(results_raw)):
        actual = results_raw[i]
        b6_event = is_banker_six[i]
        
        # 포지션 결정
        if i == 0: bet_on = "B"
        else:
            prev = next((r for r in reversed(results_raw[:i]) if r != 'T'), "B")
            if pos_strategy == "항상 뱅커": bet_on = "B"
            elif pos_strategy == "항상 플레이어": bet_on = "P"
            elif pos_strategy == "직전 결과 따라가기": bet_on = prev
            elif pos_strategy == "반대로 꺾기": bet_on = "P" if prev == "B" else "B"

        # 베팅 금액 결정
        if sys_strategy == "고정 베팅": bet_amount = unit_bet
        else: bet_amount = unit_bet * (2 ** (current_step - 1))

        # 한도 체크
        if bet_amount > MAX_LIMIT:
            bet_amount = unit_bet
            current_step = 1

        # 결과 판정 (Banker 6 룰 적용)
        pnl = 0
        note = ""
        if actual != 'T':
            if bet_on == actual:
                if bet_on == 'B' and b6_event: # 뱅커 식스 발생!
                    pnl = bet_amount * 0.5
                    note = "Banker 6 (50%)"
                else: 
                    pnl = bet_amount # 일반 승리는 100% 지급
                
                if sys_strategy == "마틴게일": current_step = 1
                elif sys_strategy == "역마틴게일": current_step = min(current_step + 1, max_steps)
            else:
                pnl = -bet_amount
                if sys_strategy == "마틴게일": current_step = min(current_step + 1, max_steps)
                elif sys_strategy == "역마틴게일": current_step = 1
        
        balance += pnl
        balance_history.append(balance)
        bet_details.append({
            "판": i+1, "결과": actual, "비고": note, "베팅": bet_on, 
            "금액": int(bet_amount), "수익": int(pnl), "누적": int(balance)
        })

    # 6. 본매 출목표 그래픽 (생략 없이 유지)
    st.subheader("🔵 본매 출목표")
    x, y, colors, types, curr_x, curr_y, prev_r = [], [], [], [], 0, 0, None
    plot_results = [(r, s) for r, s in zip(results_raw, is_banker_six) if r != 'T']
    
    for res, is_six in plot_results:
        if prev_r and res != prev_r: curr_x += 1; curr_y = 0
        elif prev_r and res == prev_r: 
            curr_y += 1
            if curr_y >= 6: curr_y = 5; curr_x += 1
        x.append(curr_x); y.append(curr_y); colors.append('red' if res == 'B' else 'blue'); types.append(res); prev_r = res
    
    fig, ax = plt.subplots(figsize=(12, 3))
    for i in range(len(x)):
        ax.add_patch(plt.Circle((x[i], 5-y[i]), 0.35, color=colors[i], fill=False, lw=2))
        ax.text(x[i], 5-y[i], types[i], color=colors[i], ha='center', va='center', fontsize=8, fontweight='bold')
    ax.set_xlim(-0.5, max(x)+1 if x else 10); ax.set_ylim(-0.5, 5.5); ax.set_aspect('equal'); plt.axis('off')
    st.pyplot(fig)

    # 7. 수익 그래프 및 통계
    col_left, col_right = st.columns([1, 1])
    with col_left:
        st.subheader("📈 누적 수익 추이")
        st.line_chart(balance_history)
    with col_right:
        st.subheader("💰 시뮬레이션 통계")
        st.write(f"- 최종 수익: **{int(balance/10000)}** 만원")
        st.write(f"- 최고 수익: **{int(max(balance_history)/10000)}** 만원")
        st.write(f"- 뱅커 식스 발생: **{b_six_count}** 회")

    # 8. 상세 데이터
    st.subheader("📋 상세 베팅 데이터")
    df = pd.DataFrame(bet_details)
    st.dataframe(df, use_container_width=True)
    
    csv = df.to_csv(index=False).encode('utf-8-sig')
    st.download_button("📊 결과 엑셀 다운로드", csv, "baccarat_b6_report.csv", "text/csv")