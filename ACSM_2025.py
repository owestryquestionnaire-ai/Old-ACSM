import streamlit as st
from datetime import date

PAGE_TITLE = "運動準備度四合一評估"
SESSION_KEYS = {
    "parq_yes_count": "parq_yes_count",
    "tab2_answers": "tab2_answers",
    "symptoms_count": "symptoms_count",
    "exercise_class": "exercise_class"
}
def calculate_risk_from_tab2(answers_dict, hdl_mg_dl=0, fbg_mmol=0.0, ogtt_mmol=0.0):
    positive_items = [k for k, v in answers_dict.items() if v]
    raw_count = len(positive_items)
    ifgigt_by_value = (5.55 <= fbg_mmol <= 6.94) or (7.77 <= ogtt_mmol <= 11.04)
    if ifgigt_by_value and "IFG/IGT" not in positive_items:
        raw_count += 1
    hdl_protective = (hdl_mg_dl >= 60)
    net_count = max(0, raw_count - 1) if hdl_protective else raw_count
    return raw_count, net_count, positive_items, ifgigt_by_value, hdl_protective

def calculate_thr(age, rhr, risk_level_str):
    mhr = 220 - age
    if rhr >= mhr:
        return None, "靜息心率不可大於或等於估計最大心率 (220 - 年齡)。"
    hrr = mhr - rhr
    if risk_level_str == "low":
        lp, up = 0.50, 0.85
        advice = "低風險：可考慮中強度到較高強度（漸進）。"
    elif risk_level_str == "moderate":
        lp, up = 0.40, 0.60
        advice = "中等風險：建議從輕到中等強度開始。"
    else:
        lp, up = 0.30, 0.39
        advice = "高風險：須先獲得醫療許可，建議非常輕度運動（<40% HRR）。"
    lower = int((hrr * lp) + rhr)
    upper = int((hrr * up) + rhr)
    thr_text = f"估計 MHR: {mhr} bpm\nRHR: {rhr} bpm\nHRR: {hrr} bpm\n"
    thr_text += (f"THR 區間: {lower} - {upper} bpm\n" if risk_level_str != "high" else f"THR 上限: {upper} bpm\n")
    thr_text += advice
    return thr_text, None

def classify_exercise_risk(parq_yes_count, tab2_net_count, known_disease=False, symptoms_count=0):
    if known_disease or symptoms_count >= 1:
        return "Class III", "已知疾病或有主要徵狀，需醫療評估與許可。"
    if (parq_yes_count != 0 and tab2_net_count == 2) or (tab2_net_count >= 2):
        return "Class II", "危險因子較多或 PAR-Q 有陽性且 Tab2 = 2，建議醫療評估或謹慎增加運動。"
    if parq_yes_count == 0 and tab2_net_count <= 1:
        return "Class I", "PAR-Q 無陽性且危險因子淨數 ≤1，可開始或繼續運動。"
    return "Unclassified", "未符合明確規則，請進一步評估。"

def today_str():
    return date.today().strftime("%m/%d/%Y")
def inject_global_css():
    st.markdown(
        """
        <style>
        html, body, .reportview-container, .main, .block-container { font-size: 16px; }
        h1 { font-size: 28px !important; }
        h2 { font-size: 22px !important; }
        h3 { font-size: 18px !important; }
        .stMarkdown p { font-size: 16px !important; line-height: 1.4; }
        label, button, input, select { font-size: 16px !important; }
        .stCaption { font-size: 12px !important; }
        pre, code { font-size: 15px !important; }
        </style>
        """,
        unsafe_allow_html=True,
    )
def tab_parq():
    st.header("1. PAR-Q（體能活動適應能力問卷）")
    p1 = st.radio("1. 醫生是否曾說您有心臟病且只能在醫生建議下運動？", ("否", "是"), key="parq1", horizontal=True)
    p2 = st.radio("2. 體能活動時您會有胸痛或不適？", ("否", "是"), key="parq2", horizontal=True)
    p3 = st.radio("3. 過去一個月內未活動時曾感胸痛？", ("否", "是"), key="parq3", horizontal=True)
    p4 = st.radio("4. 是否有頭暈、失去平衡或曾昏厥？", ("否", "是"), key="parq4", horizontal=True)
    p5 = st.radio("5. 骨骼或關節問題會因活動而惡化？", ("否", "是"), key="parq5", horizontal=True)
    p6 = st.radio("6. 醫師是否為您處方血壓或心臟用藥？", ("否", "是"), key="parq6", horizontal=True)
    p7 = st.radio("7. 是否有其他原因使您不應該進行體能活動？", ("否", "是"), key="parq7", horizontal=True)

    parq_yes_count = sum(1 for a in [p1, p2, p3, p4, p5, p6, p7] if a == "是")
    st.session_state[SESSION_KEYS["parq_yes_count"]] = parq_yes_count
    if parq_yes_count > 0:
        st.error(f"PAR-Q 有 {parq_yes_count} 項為「是」。建議諮詢醫師。")
    else:
        st.success("PAR-Q 無陽性（目前）。")
def tab_tab2():
    st.header("2. 心血管疾病風險問卷（輸入區，自動儲存）")
    q1 = st.radio("1. 年齡: 男性 ≥45 或 女性 ≥55？", ("否", "是"), key="q_age", horizontal=True)
    q2 = st.radio("2. 家族早發史（父親/男性近親 <55 或 母親/女性近親 <65）？", ("否", "是"), key="q_famhx", horizontal=True)
    q3 = st.radio("3. 吸煙或戒煙 <6 個月 / 長期暴露？", ("否", "是"), key="q_smoke", horizontal=True)
    q4 = st.radio("4. 無定期運動（未達每週≥3天、每次≥30分）？", ("否", "是"), key="q_sedentary", horizontal=True)
    q5 = st.radio("5. 肥胖：BMI ≥30 或 男性腰圍>102cm / 女性>88cm？", ("否", "是"), key="q_obesity", horizontal=True)
    q6 = st.radio("6. 高血壓：正在服用降壓藥 或 兩次測量中 SBP ≥130 或 DBP ≥80？", ("否", "是"), key="q_htn", horizontal=True)
    q7 = st.radio("7. 高膽固醇：正在服用降脂藥 或 血脂異常？", ("否", "是"), key="q_lipids", horizontal=True)

    st.markdown("---")
    st.subheader("8. 前期糖尿病 (IFG/IGT)")
    q8_manual = st.radio("是否已被診斷為 IFG/IGT？", ("否", "是"), key="q_ifg_manual", horizontal=True)
    fbg = st.number_input("空腹血糖 FBG (mmol/L)", min_value=0.0, max_value=50.0, value=0.0, format="%.2f", key="q_fbg")
    ogtt = st.number_input("OGTT 2小時值 (mmol/L)", min_value=0.0, max_value=50.0, value=0.0, format="%.2f", key="q_ogtt")
    st.caption("IFG 門檻：FBG 5.55–6.94 mmol/L；IGT 門檻：OGTT 7.77–11.04 mmol/L")

    st.markdown("---")
    hdl = st.number_input("最近 HDL (mg/dL)（若不知輸入 0）", min_value=0, max_value=200, value=0, key="q_hdl")

    st.session_state[SESSION_KEYS["tab2_answers"]] = {
        "年齡門檻": (q1 == "是"),
        "家族早發史": (q2 == "是"),
        "吸煙/近期戒菸/暴露": (q3 == "是"),
        "久坐/無定期運動": (q4 == "是"),
        "肥胖/高腰圍": (q5 == "是"),
        "高血壓/服藥或兩次測量升高": (q6 == "是"),
        "高膽固醇/服藥或血脂異常": (q7 == "是"),
        "IFG_manual": (q8_manual == "是"),
        "FBG_mmol": fbg,
        "OGTT_mmol": ogtt,
        "HDL_mg_dl": hdl
    }
    st.info("輸入已自動暫存。完成第3表後按「完成表3並最終送出評估（含 THR）」。")
def tab3_final_submit():
    st.header("3. 主要徵狀（心血管 / 呼吸 / 代謝）")
    st.write("在過去 12 個月內，是否有下列症狀？")
    c1 = st.checkbox("胸痛或胸悶（活動或休息時）", key="s_chest")
    c2 = st.checkbox("輕微活動或休息時呼吸困難", key="s_breath")
    c3 = st.checkbox("頭暈、昏厥或失去意識", key="s_dizzy")
    c4 = st.checkbox("不尋常的疲勞", key="s_fatigue")
    c5 = st.checkbox("心悸或不規則心跳", key="s_palpit")
    c6 = st.checkbox("下肢水腫（腳踝/足部腫脹）", key="s_swelling")

    st.markdown("---")
    st.subheader("可選：輸入年齡與靜息心率以立即計算 THR")
    age_for_thr = st.number_input("年齡（歲）", min_value=1, max_value=120, value=30, key="s_age")
    rhr_for_thr = st.number_input("靜息心率 RHR（bpm）", min_value=30, max_value=150, value=60, key="s_rhr")

    if st.button("完成表3並最終送出評估（含 THR）"):
        symptoms_count = sum(1 for v in [c1, c2, c3, c4, c5, c6] if v)
        st.session_state[SESSION_KEYS["symptoms_count"]] = symptoms_count
        st.success(f"第3表已儲存，偵測到 {symptoms_count} 項主要徵狀（若>0請就醫）。")

        parq_yes = st.session_state.get(SESSION_KEYS["parq_yes_count"], None)
        tab2 = st.session_state.get(SESSION_KEYS["tab2_answers"], None)
        if parq_yes is None or tab2 is None:
            st.warning("請先完成第1表與第2表（PAR-Q 與心血管風險問卷），再進行最終評估。")
            st.stop()

        raw_count, net_count, positive_items, ifgigt_flag, hdl_protect = calculate_risk_from_tab2(
            {k: tab2[k] for k in tab2 if k in [
                "年齡門檻","家族早發史","吸煙/近期戒菸/暴露","久坐/無定期運動","肥胖/高腰圍",
                "高血壓/服藥或兩次測量升高","高膽固醇/服藥或血脂異常"
            ]},
            hdl_mg_dl=tab2.get("HDL_mg_dl", 0),
            fbg_mmol=tab2.get("FBG_mmol", 0.0),
            ogtt_mmol=tab2.get("OGTT_mmol", 0.0)
        )

        known_disease_flag = any("高血壓" in s or "高膽固醇" in s or "肥胖" in s for s in positive_items)

        exercise_class, reason = classify_exercise_risk(parq_yes, net_count, known_disease_flag, symptoms_count)
        st.session_state[SESSION_KEYS["exercise_class"]] = exercise_class

        st.markdown("**最終評估結果**")
        st.write(f"- PAR-Q 陽性項目數：{parq_yes}")
        st.write(f"- Tab2 原始陽性因子數：{raw_count}")
        st.write(f"- Tab2 淨陽性因子數（HDL 保護後）：{net_count}")
        if positive_items:
            st.write("- Tab2 標為陽性的項目：")
            for it in positive_items:
                st.write(f"  - {it}")
        if ifgigt_flag or tab2.get("IFG_manual"):
            st.write("- IFG/IGT（前期糖尿病）：是")
            if ifgigt_flag:
                st.caption(f"判定依據：FBG={tab2.get('FBG_mmol')} mmol/L 或 OGTT2hr={tab2.get('OGTT_mmol')} mmol/L 在 IFG/IGT 範圍。")
        if hdl_protect:
            st.write(f"- HDL 保護規則已套用 (HDL={tab2.get('HDL_mg_dl')} mg/dL)。")

        if exercise_class == "Class I":
            st.success(f"運動分級：{exercise_class} — {reason}")
        elif exercise_class == "Class II":
            st.warning(f"運動分級：{exercise_class} — {reason}")
        else:
            st.error(f"運動分級：{exercise_class} — {reason}")

        risk_map = {"Class I": "low", "Class II": "moderate", "Class III": "high"}
        risk_level = risk_map.get(exercise_class, "moderate")
        thr_output, thr_error = calculate_thr(int(age_for_thr), int(rhr_for_thr), risk_level)
        if thr_error:
            st.error(f"THR 計算錯誤：{thr_error}")
        else:
            st.subheader("計算目標心率 (THR)")
            st.text(thr_output)
            st.caption("註：Class I → low；Class II → moderate；Class III → high（高風險僅顯示上限）。")
def tab4_thr_display():
    st.header("4. 運動分級與 THR（綜合）")
    selected_class = st.session_state.get(SESSION_KEYS["exercise_class"], None)
    if selected_class:
        st.info(f"目前儲存的運動分級：{selected_class}")
    else:
        st.info("尚無已儲存的運動分級（請在第3表完成最終送出）。")

    age_thr = st.number_input("年齡（歲）", min_value=1, max_value=120, value=30, key="tab4_age")
    rhr = st.number_input("靜息心率 RHR（bpm）", min_value=30, max_value=150, value=60, key="tab4_rhr")
    if st.button("計算目標心率 (THR)"):
        if selected_class is None:
            st.warning("請先於第3表完成最終評估或手動選擇運動分級。")
        else:
            risk_map = {"Class I": "low", "Class II": "moderate", "Class III": "high"}
            risk_level = risk_map.get(selected_class, "moderate")
            thr_output, thr_error = calculate_thr(int(age_thr), int(rhr), risk_level)
            if thr_error:
                st.error(thr_error)
            else:
                st.subheader("THR 計算結果")
                st.text(thr_output)
                st.caption("註：Class I → low；Class II → moderate；Class III → high（高風險僅顯示上限）。")
def main():
    st.set_page_config(page_title=PAGE_TITLE, layout="centered")
    inject_global_css()
    st.title(PAGE_TITLE)

    tab1, tab2, tab3, tab4 = st.tabs([
        "1. PAR-Q",
        "2. 心血管疾病風險問卷",
        "3. 主要徵狀",
        "4. 運動分級與 THR"
    ])

    with tab1:
        tab_parq()
    with tab2:
        tab_tab2()
    with tab3:
        tab3_final_submit()
    with tab4:
        tab4_thr_display()

    st.markdown("---")
    st.caption("免責聲明：此工具僅為快速篩檢與教育用途，不能替代專業醫療評估。若有異常或疑慮，請諮詢醫療專業人員.")

if __name__ == "__main__":
    main()
