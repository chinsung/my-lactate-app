import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from scipy.interpolate import interp1d

# ตั้งค่าหน้าเว็บ
st.set_page_config(page_title="Lactate Pace Pro", layout="wide")

st.title("🏃‍♂️ Lactate Threshold Analyzer")
st.markdown("โปรแกรมวิเคราะห์ค่าแลคเตทเป็น Pace วิ่ง (Modern Web App)")

# --- ส่วนข้อมูล (Input) ---
st.sidebar.header("กรอกข้อมูลการทดสอบ")
# สมมติข้อมูลเริ่มต้น (Pace หน่วยเป็นวินาทีต่อกิโลเมตร เพื่อให้คำนวณง่าย)
default_data = {
    'Pace_min_km': [6.0, 5.5, 5.0, 4.5, 4.0],
    'Lactate': [1.1, 1.8, 2.7, 4.2, 7.5]
}
df = pd.DataFrame(default_data)

st.sidebar.write("ใส่ค่า Pace และ Lactate ที่วัดได้:")
edited_df = st.sidebar.data_editor(df, num_rows="dynamic")

# --- ส่วนคำนวณ Logic ---
if len(edited_df) >= 3:
    # สร้างเส้น Curve ด้วย Linear Interpolation (หรือเปลี่ยนเป็น Polynomial ได้)
    # เราจะหา Pace ที่ Lactate = 4.0
    f = interp1d(edited_df['Lactate'], edited_df['Pace_min_km'], kind='cubic', fill_value="extrapolate")
    threshold_pace_raw = f(4.0)
    
    # แปลงเลขทศนิยมกลับเป็นนาที:วินาที
    minutes = int(threshold_pace_raw)
    seconds = int((threshold_pace_raw - minutes) * 60)
    pace_str = f"{minutes}:{seconds:02d}"

    # --- ส่วนการแสดงผล (UI) ---
    col1, col2 = st.columns([1, 2])

    with col1:
        st.metric(label="Threshold Pace (@4.0 mmol/L)", value=f"{pace_str} min/km")
        st.success(f"Pace แนะนำสำหรับการซ้อม Threshold คือ {pace_str}")
        
        st.write("### สรุปโซนการซ้อม (ตัวอย่าง)")
        st.table(pd.DataFrame({
            "Zone": ["Z1 (Easy)", "Z2 (Aerobic)", "Z3 (Tempo)", "Z4 (Threshold)"],
            "Pace": ["> 6:30", "5:50 - 6:30", "5:10 - 5:50", pace_str]
        }))

    with col2:
        # วาดกราฟด้วย Plotly
        fig = go.Figure()

        # เส้นกราฟหลัก
        x_new = np.linspace(edited_df['Lactate'].min(), edited_df['Lactate'].max(), 100)
        y_new = f(x_new)

        fig.add_trace(go.Scatter(x=y_new, y=x_new, mode='lines', name='Lactate Curve', line=dict(color='#FF4B4B', width=4)))
        fig.add_trace(go.Scatter(x=edited_df['Pace_min_km'], y=edited_df['Lactate'], mode='markers', name='Data Points', marker=dict(size=12, color='#31333F')))

        # เส้นประบอกจุด 4.0
        fig.add_hline(y=4.0, line_dash="dash", line_color="green", annotation_text="Threshold (4.0)")
        fig.add_vline(x=threshold_pace_raw, line_dash="dash", line_color="green")

        fig.update_layout(
            title="Lactate Curve Analysis",
            xaxis_title="Pace (min/km)",
            yaxis_title="Lactate Concentration (mmol/L)",
            xaxis=dict(autorange="reversed"), # วิ่งเร็วขึ้น Pace จะน้อยลง
            hovermode="x unified"
        )

        st.plotly_chart(fig, use_container_width=True)
else:
    st.warning("กรุณากรอกข้อมูลอย่างน้อย 3 จุดเพื่อให้สร้างกราฟได้ครับ")