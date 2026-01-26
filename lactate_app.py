import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from scipy.interpolate import interp1d
from datetime import datetime

# 1. ตั้งค่าหน้าเว็บ
st.set_page_config(page_title="Lactate Report", layout="centered")

# CSS สำหรับซ่อน Sidebar และปรับสีตอน Print
st.markdown("""
    <style>
    @media print {
        div[data-testid="stSidebar"] { display: none !important; }
        .stActionButton { display: none !important; }
        footer { display: none !important; }
        .block-container { padding-top: 1rem !important; max-width: 100% !important; }
    }
    </style>
""", unsafe_allow_html=True)

def format_pace(decimal_pace):
    if np.isnan(decimal_pace) or np.isinf(decimal_pace): return "--:--"
    minutes = int(decimal_pace)
    seconds = int(round((decimal_pace - minutes) * 60))
    if seconds == 60:
        minutes += 1; seconds = 0
    return f"{minutes}:{seconds:02d}"

# --- Sidebar ---
st.sidebar.header("📝 กรอกข้อมูลที่นี่")
runner_name = st.sidebar.text_input("ชื่อ-นามสกุล:", "Bank_Sattawat")
test_date = st.sidebar.date_input("วันที่ทดสอบ:", datetime.now())
default_data = {'Pace_Entry': [6.0, 5.3, 5.0, 4.3, 4.0], 'Lactate': [1.2, 1.9, 2.8, 4.5, 7.2]}
input_df = st.sidebar.data_editor(pd.DataFrame(default_data), num_rows="dynamic")

# --- ส่วนรายงานหลัก (Main Report) ---
if len(input_df) >= 3:
    try:
        f_pace = interp1d(input_df['Lactate'], input_df['Pace_Entry'], kind='cubic', fill_value="extrapolate")
        t_pace = float(f_pace(4.0))
        
        # คำนวณ Zones
        zones = {
            "Recovery": t_pace * 1.35, 
            "Easy Run": t_pace * 1.28, 
            "Long Run": t_pace * 1.20,
            "Marathon": t_pace * 1.12, 
            "Half Marathon": t_pace * 1.06, 
            "Threshold (4.0)": t_pace
        }

        # แสดงหัวข้อรายงาน
        st.title("📊 Lactate Threshold Analysis Report")
        st.write(f"**นักวิ่ง:** {runner_name} | **วันที่:** {test_date.strftime('%d/%m/%Y')}")
        
        # --- แบ่ง Column สำหรับส่วนบน ---
        col_in, col_out = st.columns(2)
        
        with col_in:
            st.write("### 📥 ข้อมูลการทดสอบ (Input)")
            # ปรับทศนิยมเป็น 2 ตำแหน่งก่อนแสดงผล
            display_input = input_df.copy()
            display_input['Pace_Entry'] = display_input['Pace_Entry'].map('{:.2f}'.format)
            display_input['Lactate'] = display_input['Lactate'].map('{:.1f}'.format)
            st.table(display_input)

        with col_out:
            st.write("### 📋 โซนการซ้อม (Output)")
            zone_df = pd.DataFrame([{"Zone": k, "Pace": format_pace(v)} for k, v in zones.items()])
            st.table(zone_df)

        st.divider()

        # กราฟ
        st.write("### 📈 Lactate Curve Visualization")
        lactate_range = np.linspace(input_df['Lactate'].min(), input_df['Lactate'].max(), 100)
        fig = go.Figure()
        fig.add_trace(go.Scatter(x=f_pace(lactate_range), y=lactate_range, mode='lines', line=dict(color='#FF4B4B', width=3), name='Curve'))
        fig.add_trace(go.Scatter(x=input_df['Pace_Entry'], y=input_df['Lactate'], mode='markers', marker=dict(size=8, color='black'), name='Data'))
        fig.add_hline(y=4.0, line_dash="dash", line_color="green", annotation_text="LT2 (4.0)")
        
        fig.update_layout(
            height=350,
            template="plotly_white",
            xaxis=dict(title="Pace (min/km)", autorange="reversed"),
            yaxis=dict(title="Lactate (mmol/L)"),
            margin=dict(l=0, r=0, t=30, b=0)
        )
        st.plotly_chart(fig, use_container_width=True)

        # สรุปด้านล่าง
        st.divider()
        st.markdown(f"""
        ### 💡 การวิเคราะห์และคำแนะนำ
        จากการทดสอบคุณมีจุด **Threshold Pace อยู่ที่ {format_pace(t_pace)}** นาที/กม.
        * **Easy Run:** วิ่งที่ Pace **{format_pace(zones['Easy Run'])}**
        * **Recovery:** ไม่ควรเร็วกว่า **{format_pace(zones['Recovery'])}**
        """)

    except Exception as e:
        st.error(f"เกิดข้อผิดพลาด: {e}")
else:
    st.warning("กรุณากรอกข้อมูลใน Sidebar อย่างน้อย 3 จุด")
