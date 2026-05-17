import streamlit as st
import streamlit.components.v1 as components

# ---------- 1. Initialization & Config ----------
st.set_page_config(page_title="體能活動風險評估系統", layout="centered")

# --- CUSTOM CSS FOR EXTRA LARGE TEXT, ALL BLACK, BOLD TITLES ONLY ---
def inject_custom_css():
    st.markdown(
        """
        <style>
        /* Global Base Font and Black Color */
        html, body, [data-testid="stMarkdownContainer"] {
            font-size: 20px !important;
            color: #000000 !important;
            font-weight: 400 !important; /* Normal weight for body */
        }

        /* Headers - BOLD */
        h1 { font-size: 40px !important; color: #000000 !important; font-weight: bold !important; }
        h2 { font-size: 34px !important; color: #000000 !important; font-weight: bold !important; border-bottom: 2px solid #000; padding-bottom: 10px; }
        h3 { font-size: 28px !important; color: #000000 !important; font-weight: bold !important; }

        /* Radio Buttons & Checkbox Labels - REGULAR */
        div[data-testid="stRadio"] label p, 
        div[data-testid="stCheckbox"] label p {
            font-size: 22px !important;
            font-weight: 400 !important; /* Regular weight */
            color: #000000 !important;
        }

        /* Standard Text - REGULAR */
        .stMarkdown p {
            font-size: 20px !important;
            color: #000000 !important;
            font-weight: 400 !important;
        }

        /* Input Box Labels - BOLD (treated as titles for fields) */
        label[data-testid="stWidgetLabel"] p {
            font-size: 22px !important;
            font-weight: bold !important;
            color: #000000 !important;
        }

        /* Tabs font size - BOLD */
        button[data-baseweb="tab"] div {
            font-size: 20px !important;
            color: #000000 !important;
            font-weight: bold !important;
        }
        
        /* Clear button styling */
        button[kind="secondary"] {
            margin-top: 5px;
        }
        
        /* Combined Result Box Styling */
        .final-result-box {
            border: 3px solid #000000;
            border-radius: 10px;
            overflow: hidden;
            box-shadow: 2px 2px 10px rgba(0,0,0,0.1);
        }
        .final-thr-part {
            font-size: 32px !important;
            color: #000000 !important;
            font-weight: bold !important;
            line-height: 1.4 !important;
            padding: 25px;
            background-color: #ffffff;
        }
        .final-rec-part {
            background-color: #f8f9fa;
            padding: 25px;
            border-top: 3px dashed #000000;
        }
        .final-rec-part p {
            margin-bottom: 10px !important;
            line-height: 1.5;
        }
        </style>
        """,
        unsafe_allow_html=True
    )

# --- 預先初始化所有選項的 Session State，讓全域計算能順利抓取數值 ---
def init_session_states():
    # Form A
    for i in range(7):
        if f"p{i}" not in st.session_state: st.session_state[f"p{i}"] = "否"
    
    # Form B
    for k in ["age", "fam", "smk", "sed", "obe", "htn", "lip"]:
        if f"r_{k}" not in st.session_state: st.session_state[f"r_{k}"] = "否"
    if "ifg_radio" not in st.session_state: st.session_state["ifg_radio"] = "否"
    if "hdl_radio_val" not in st.session_state: st.session_state["hdl_radio_val"] = None
    
    # Form C
    for k in ["hist_c", "hist_p", "hist_m"]:
        if k not in st.session_state: st.session_state[k] = False
    for i in range(9):
        if f"sy_{i}" not in st.session_state: st.session_state[f"sy_{i}"] = False
        
    # Form C 額外彈出選項 (改為單選方塊的 Boolean 值)
    for i in range(1, 4):
        if f"cramp_loc_{i}" not in st.session_state: st.session_state[f"cramp_loc_{i}"] = False
    for i in range(1, 6):
        if f"cramp_time_{i}" not in st.session_state: st.session_state[f"cramp_time_{i}"] = False
        
    # 控制是否強制顯示所有表單的開關
    if "force_show_all" not in st.session_state:
        st.session_state["force_show_all"] = False

init_session_states()


# ---------- 2. Logic Functions ----------
def parse_val(text):
    t = str(text).strip()
    if not t: return None
    try:
        return float(t)
    except:
        return None

def calculate_thr(age, rhr, risk_level):
    mhr = 220 - age
    if rhr >= mhr: return None, "Abnormal Resting Heart Rate"
    hrr = mhr - rhr

    details_html = f'<div style="font-size: 18px; font-weight: normal; margin-top: 10px; color: #444;">Maximum HR: {mhr} | Resting HR: {rhr} | HR Reserve: {hrr}</div>'

    if risk_level == "Class III":
        limit = int((hrr * 0.40) + rhr)
        thr_main = f"Target Heart Rate: < {limit} bpm (< 40% HRR)"
        return thr_main + details_html, None
    else:
        rates = {"Class I": (0.40, 0.84), "Class II": (0.40, 0.60)}
        lp, up = rates.get(risk_level)
        lower = int((hrr * lp) + rhr)
        upper = int((hrr * up) + rhr)
        thr_main = f"Target Heart Rate: {lower} - {upper} bpm"
        return thr_main + details_html, None

def get_risk_score():
    risk_keys = ["r_age", "r_fam", "r_smk", "r_sed", "r_obe", "r_htn", "r_lip"]
    score = sum(1 for k in risk_keys if st.session_state.get(k) == "是")
    if st.session_state.get("ifg_radio") == "是": score += 1
    if st.session_state.get("hdl_radio_val") == "是": score -= 1
    return max(0, score)

# --- 全域即時計算當前風險分級 ---
def calculate_current_class():
    # 1. 優先檢查 Form C (Symptoms & History) -> Class III
    history = any([st.session_state.get("hist_c"), st.session_state.get("hist_p"), st.session_state.get("hist_m")])
    symptoms = any([st.session_state.get(f"sy_{i}") for i in range(9)])
    if history or symptoms:
        return "Class III"

    # 2. 檢查 Form A 與 Form B -> Class II
    parq_score = sum(1 for i in range(7) if st.session_state.get(f"p{i}") == "有")
    risk_score = get_risk_score()
    
    if parq_score > 0 or risk_score >= 2:
        return "Class II"
    else:
        return "Class I"


# ---------- 3. Callbacks & Helpers ----------
def clear_hdl_callback():
    st.session_state["hdl_radio_val"] = None

def enable_all_tabs_callback():
    st.session_state["force_show_all"] = True

# 使用 JavaScript 自動切換分頁的輔助函式
def switch_tab(tab_index):
    js = f"""
    <script>
        var tabs = window.parent.document.querySelectorAll('button[data-baseweb="tab"]');
        if (tabs.length > {tab_index}) {{
            tabs[{tab_index}].click();
        }}
    </script>
    """
    components.html(js, height=0)


# ---------- 4. Tab Functions ----------
def tab_c_symptoms(is_class_3, show_all_tabs):
    st.header("Form C: 心血管疾病症狀")
    st.subheader("已知病史")
    st.checkbox("已知心臟疾病：心肌梗塞、心臟手術、導管/支架、瓣膜病、心衰竭、先天性心臟病等", key="hist_c")
    st.checkbox("已知肺部疾病：慢性阻塞性肺病、哮喘、間質性肺病、囊性纖維化等", key="hist_p")
    st.checkbox("已知代謝疾病：1型或2型糖尿病、腎臟疾病等", key="hist_m")

    st.markdown("---")
    st.subheader("主要徵狀")
    s_items = [
        "1. 因心臟缺血而引致的胸口、頸、下顎、上臂或其他部位痛楚或不適",
        "2. 靜止或輕鬆活動時感到氣喘",
        "3. 暈眩或失去知覺",
        "4. 平臥時或晚間不時氣喘",
        "5. 腳踝腫",
        "6. 心悸或心率過快",
        "7. 間歇肌肉疼痛、抽筋",
        "8. 心雜音",
        "9. 一般活動感到不尋常的疲勞或氣喘"
    ]
    
    for i, label in enumerate(s_items):
        st.checkbox(label, key=f"sy_{i}")
        
        # 當第 7 項 (index 6) 被勾選時，顯示多選核取方塊 (Checkboxes)
        if i == 6 and st.session_state.get(f"sy_6"):
            col_space, col_content = st.columns([0.5, 9.5])
            with col_content:
                st.markdown("<p style='font-size: 18px; color: #555; margin-bottom: 5px;'><b>📍 位置 (可多選)：</b></p>", unsafe_allow_html=True)
                lc1, lc2, lc3 = st.columns(3)
                lc1.checkbox("小腿", key="cramp_loc_1")
                lc2.checkbox("大腿", key="cramp_loc_2")
                lc3.checkbox("其他", key="cramp_loc_3")
                
                st.markdown("<p style='font-size: 18px; color: #555; margin-top: 10px; margin-bottom: 5px;'><b>⏱️ 發生時間 (可多選)：</b></p>", unsafe_allow_html=True)
                tc1, tc2, tc3 = st.columns(3)
                tc1.checkbox("睡覺時", key="cramp_time_1")
                tc2.checkbox("走路時", key="cramp_time_2")
                tc3.checkbox("上樓梯時", key="cramp_time_3")
                tc4, tc5, _ = st.columns(3)
                tc4.checkbox("上斜路時", key="cramp_time_4")
                tc5.checkbox("其他", key="cramp_time_5")
                st.write("") # 增加一點底部間距

    st.markdown("---")
    
    if is_class_3:
        if not show_all_tabs:
            st.warning("🚨 根據已知病史或症狀，病患已判定為 **Class III**。系統已自動隱藏 Form B 與 Form A。")
            if st.button("➡️ 直接跳至心率計算 (Skip to Target Heart Rate)", type="primary", key="skip_to_thr_c"):
                switch_tab(1)  # 隱藏狀態下，心率計算是第 2 個分頁 (index 1)
            st.button("📝 顯示隱藏的表單 (Show Form B & A)", on_click=enable_all_tabs_callback, key="show_all_c")
        else:
            st.warning("🚨 根據已知病史或症狀，病患已判定為 **Class III**。您選擇繼續填寫後續表單。")
            if st.button("➡️ 下一步：前往 Form B (Next Step: Form B)", type="primary"):
                switch_tab(1)  # 全顯示狀態下，Form B 是第 2 個分頁 (index 1)
    else:
        if st.button("➡️ 下一步：前往 Form B (Next Step: Form B)", type="primary"):
            switch_tab(1)


def tab_b_risk(is_class_2_b, show_all_tabs):
    st.header("表格 B 心血管疾病風險因素")
    st.markdown("請在適當項目選擇 **是(1)** 或 **否(0)**")
    
    items = [
        ("age", "年齡", "*男性 45 歲或以上、女性 55 歲或以上"),
        ("fam", "遺傳病因素", "*父親或男性近親在 55 歲前患有心肌梗塞，或接受冠狀動脈血管重建手術，或突然去世，或<br>*母親或女性近親在 65 歲前患有心肌梗塞，或接受冠狀動脈血管重建手術，或突然去世"),
        ("smk", "吸煙習慣", "*吸煙人士，或戒煙少於 6 個月，或置身吸煙場所"),
        ("sed", "靜態生活方式", "*沒有定期運動習慣 (每週至少三天有 30 分鐘或以上中度運動，並連續三個月以上)"),
        ("obe", "肥胖", "*BMI ≥30kg/m²，或<br>*男士腰圍>102cm (40 吋)；女士腰圍>88cm (35 吋)"),
        ("htn", "血壓高", "*正服用降血壓藥物，或<br>*上壓或下壓分別在兩次測試中≥140mmHg 或 ≥90 mmHg"),
        ("lip", "高膽固醇", "*正服用降膽固醇藥物，或 TC>5.18mmol/L，或 HDL<1.04mmol/L，或 LDL >3.37mmol/L")
    ]
    
    for key, label, desc in items:
        col_l, col_r = st.columns([6, 2])
        with col_l:
            st.markdown(f"<div style='font-size: 22px; line-height: 1.5; margin-bottom: 10px;'><b>{label}</b><br>{desc}</div>", unsafe_allow_html=True) 
        col_r.radio("", ("否", "是"), key=f"r_{key}", horizontal=True, label_visibility="collapsed")

    col_l8, col_r8 = st.columns([6, 2])
    with col_l8:
        st.markdown("<div style='font-size: 22px; line-height: 1.5; margin-bottom: 10px;'><b>前期糖尿病</b><br>*所有確診 IFG/IGT 的人仕<br>血糖分別在兩次測試中大過或等於<br>空腹血糖值：5.55 - 6.94mmol/L;<br>葡萄糖失耐值：7.77 - 11.04mmol/L</div>", unsafe_allow_html=True)
    st.radio("", ("否", "是"), key="ifg_radio", horizontal=True, label_visibility="collapsed")

    st.markdown("---")
    
    col_l9, col_r9, col_btn = st.columns([5, 2, 1])
    with col_l9:
        st.markdown("<div style='font-size: 22px;'><b>注意: 如 HDL ≥1.55mmol/L 可減 1 分。</b></div>", unsafe_allow_html=True)
        
    st.radio("", ("否", "是"), key="hdl_radio_val", horizontal=True, label_visibility="collapsed", index=None)

    with col_btn:
        st.button("清除", key="clear_hdl", on_click=clear_hdl_callback)

    st.markdown("---")

    risk_score = get_risk_score()
    st.markdown(f"### 運動風險因素評估: 總分 {risk_score} / 8 分")

    if is_class_2_b:
        if not show_all_tabs:
            st.warning("🚨 根據風險因素總分 (≥ 2分)，病患已判定為 **Class II**。系統已自動隱藏 Form A。")
            if st.button("➡️ 直接跳至心率計算 (Skip to Target Heart Rate)", type="primary", key="skip_to_thr_b"):
                switch_tab(2)  # C(0), B(1), THR(2)
            st.button("📝 顯示隱藏的表單 (Show Form A)", on_click=enable_all_tabs_callback, key="show_all_b")
        else:
            st.warning("🚨 根據風險因素總分 (≥ 2分)，病患已判定為 **Class II**。您選擇繼續填寫 Form A。")
            if st.button("➡️ 下一步：前往 Form A (Next Step: Form A)", type="primary", key="next_a_show"):
                switch_tab(2)  # C(0), B(1), A(2), THR(3)
    else:
        if st.button("➡️ 下一步：前往 Form A (Next Step: Form A)", type="primary", key="next_a_normal"):
            switch_tab(2)


def tab_a_parq():
    st.header("表格 A 體能活動適應能力問卷 (PAR-Q)")
    
    qs = [
        "1. 過往醫生有否說你有心臟病，而只應進行醫生建議的運動？",
        "2. 當你做運動時有否感覺胸口痛？",
        "3. 在過去數個月內，你有否在不做運動時也感到胸口痛？",
        "4. 你有否因頭暈而跌倒或失去知覺？",
        "5. 做運動有否加重你骨胳或關節的痛楚？",
        "6. 醫生有否開藥給你的血壓或心臟病？",
        "7. 有否其他原因令你不能做運動？"
    ]
    
    for i, q in enumerate(qs):
        st.radio(q, ("否", "有"), key=f"p{i}", horizontal=True)

    st.markdown("---")
    if st.button("➡️ 下一步：前往心率計算 (Next Step: Target Heart Rate)", type="primary"):
        switch_tab(3)


def tab_d_thr(current_class):
    st.header("目標心率與臨床運動建議")
    
    # --- 手動選擇覆蓋 (Manual Override) ---
    st.subheader("⚙️ 選擇運動分級 (Select Risk Class)")
    st.markdown(f"💡 系統表單目前判定為 **{current_class}**。若病患已知分級，您可直接在下方手動更改：")
    
    options = ["Class I", "Class II", "Class III"]
    default_idx = options.index(current_class) if current_class in options else 0
    
    # 讓治療師可以手動切換 Class
    selected_class = st.radio("手動選擇分級", options, index=default_idx, horizontal=True, label_visibility="collapsed")
    
    # 用來放置報告結果的容器，設定在輸入框的上方
    result_container = st.container()
    
    st.markdown("---")
    st.subheader("🎯 輸入數據 (Input Data)")

    c1, c2 = st.columns(2)
    age = c1.number_input("年齡 (Age)", min_value=10, max_value=120, value=None, step=1, key="thr_age")
    rhr = c2.number_input("靜息心率 (RHR)", min_value=30, max_value=220, value=None, step=1, key="thr_rhr")

    # --- 新增：手動點擊計算按鈕 ---
    if st.button("計算 (Calculate)", type="primary"):
        if age is not None and rhr is not None:
            # 依據治療師手動選擇的 selected_class 來計算
            thr_string, err = calculate_thr(int(age), int(rhr), selected_class)
            
            if not err:
                recs = {
                    "Class I": {
                        "intensity": "✅ Moderate | ✅ Vigorous",
                        "hrr": "40 – 84% HRR",
                        "rpe": "< 17",
                        "test": "Not required",
                        "supervision": "Not required",
                        "monitor": "Monitor heart rate in first session to facilitate teaching but it is not compulsory."
                    },
                    "Class II": {
                        "intensity": "✅ Moderate | ❌ Vigorous",
                        "hrr": "40 – 60% HRR",
                        "rpe": "< 14",
                        "test": "Not required unless patient is working for vigorous exercise.",
                        "supervision": "Not required unless patient is working for vigorous exercise.",
                        "monitor": "Continuous heart rate or RPE monitoring."
                    },
                    "Class III": {
                        "intensity": "❌ Moderate | ❌ Vigorous",
                        "hrr": "< 40% HRR",
                        "rpe": "< 12",
                        "test": "Required for both moderate and vigorous exercise.",
                        "supervision": "Required for both moderate and vigorous exercise.",
                        "monitor": "Continuous heart rate and RPE monitoring together with close supervision."
                    }
                }
                rec = recs[selected_class]
                
                # 將計算結果塞進上方的 result_container 中
                result_container.markdown(f"""
                <div class="final-result-box" style="margin-bottom: 20px;">
                    <div class="final-thr-part">
                        {thr_string}
                    </div>
                    <div class="final-rec-part">
                        <h3 style="margin-top: 0; border-bottom: 2px solid #ccc; padding-bottom: 10px;">📋 {selected_class} Clinical Guidelines</h3>
                        <p><b>Recommended Exercise Intensity:</b> {rec['intensity']}</p>
                        <p><b>Safe exercise zone:</b> {rec['hrr']}</p>
                        <p><b>RPE during Exercise:</b> {rec['rpe']}</p>
                        <p><b>Submaximal Stress Test (3-min step test):</b><br>{rec['test']}</p>
                        <p><b>Supervision:</b><br>{rec['supervision']}</p>
                        <p><b>Monitoring:</b><br>{rec['monitor']}</p>
                    </div>
                </div>
                """, unsafe_allow_html=True)
            else:
                result_container.error(err)
        else:
            result_container.warning("⚠️ 請先在下方輸入有效的年齡與靜息心率數值，再按下「計算」。")
    else:
        # 如果還沒按下計算按鈕，顯示友善的提示
        result_container.info("💡 請在下方輸入您的 **年齡 (Age)** 與 **靜息心率 (RHR)**，並按下「計算 (Calculate)」以產生報告。")


def main():
    inject_custom_css()
    
    current_class = calculate_current_class()
    risk_score = get_risk_score()
    
    class_colors = {
        "Class I": {"bg": "#e8f5e9", "border": "#2e7d32", "text": "#1b5e20"},
        "Class II": {"bg": "#fff3e0", "border": "#ef6c00", "text": "#e65100"},
        "Class III": {"bg": "#ffebee", "border": "#c62828", "text": "#b71c1c"}
    }
    theme = class_colors[current_class]
    
    st.markdown(f"""
    <div style="background-color: {theme['bg']}; border: 2px solid {theme['border']}; border-radius: 8px; padding: 10px; text-align: center; margin-bottom: 15px;">
        <span style="margin: 0; color: {theme['text']}; font-size: 24px; font-weight: bold;">Risk Stratification: {current_class}</span>
    </div>
    """, unsafe_allow_html=True)
    
    st.title("體能活動風險與強度評估系統")
    
    # 決定隱藏邏輯
    history_or_symptoms = any([st.session_state.get("hist_c"), st.session_state.get("hist_p"), st.session_state.get("hist_m")]) or \
                          any([st.session_state.get(f"sy_{i}") for i in range(9)])
    is_class_2_from_b = (risk_score >= 2)
    show_all_tabs = st.session_state.get("force_show_all", False)
    
    if history_or_symptoms and not show_all_tabs:
        # C + THR 模式 (隱藏 B 和 A)
        t1, t4 = st.tabs(["Form C: 疾病症狀", "心率計算"])
        with t1: tab_c_symptoms(is_class_3=True, show_all_tabs=False)
        with t4: tab_d_thr(current_class)
        
    elif is_class_2_from_b and not show_all_tabs:
        # C + B + THR 模式 (隱藏 A)
        t1, t2, t4 = st.tabs(["Form C: 疾病症狀", "Form B: 風險因素", "心率計算"])
        with t1: tab_c_symptoms(is_class_3=False, show_all_tabs=False)
        with t2: tab_b_risk(is_class_2_b=True, show_all_tabs=False)
        with t4: tab_d_thr(current_class)
        
    else:
        # 全部顯示模式 (C + B + A + THR)
        t1, t2, t3, t4 = st.tabs(["Form C: 疾病症狀", "Form B: 風險因素", "Form A: 適應能力問卷", "心率計算"])
        with t1: tab_c_symptoms(is_class_3=history_or_symptoms, show_all_tabs=show_all_tabs)
        with t2: tab_b_risk(is_class_2_b=is_class_2_from_b, show_all_tabs=show_all_tabs)
        with t3: tab_a_parq()
        with t4: tab_d_thr(current_class)

if __name__ == "__main__":
    main()
