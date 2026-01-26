import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from scipy.interpolate import interp1d

# 1. ตั้งค่าหน้าเว็บ (ต้องอยู่บรรทัดแรกๆ)
st.set_page_config(page_title="Lactate Pace Pro", layout="wide")

# ฟังก์ชันแปลงเลขทศนิยมเป็นนาที:วินาที (เช่น 5.5 -> 5:30)
def format_pace(decimal_pace):
    if np.isnan(decimal_pace) or np.isinf(decimal_pace):
        return "--:--"
    minutes = int(decimal_pace)
    seconds = int(round((decimal_pace - minutes) * 60))
    if seconds == 60:
        minutes += 1
        seconds = 0
    return f"{minutes}:{seconds:02d}"

# --- ส่วนหัวของแอป ---
st.title("🏃‍♂️ Lactate Threshold & Training Zones by Shin")
st.markdown("วิเคราะห์สมรรถภาพการวิ่งด้วยค่าแลคเตท และออกแบบโซนการซ้อมส่วนบุคคล")

# --- ส่วน Sidebar (กรอกข้อมูล) ---
st.sidebar.header("📥 ข้อมูลการทดสอบ")
st.sidebar.info("ใส่ค่า Pace (นาที.วินาที) เช่น 5.30 และค่า Lactate ที่วัดได้")

# ข้อมูลจำลองสำหรับเริ่มต้น
default_data = {
    'Pace_Entry': [6.00, 5.30, 5.00, 4.30, 4.00],
    'Lactate': [1.2, 1.9, 2.8, 4.5, 7.2]
}
input_df = st.sidebar.data_editor(pd.DataFrame(default_data), num_rows="dynamic")

# --- ส่วนประมวลผล ---
if len(input_df) >= 3:
    # เตรียมข้อมูลสำหรับคำนวณ (แปลง Pace 5.30 -> 5.5 เพื่อใช้คำนวณคณิตศาสตร์)
    # หมายเหตุ: ในโค้ดนี้เราจะอนุมานว่าผู้ใช้กรอกแบบทศนิยมเพื่อความง่ายก่อน
    paces = input_df['Pace_Entry'].values
    lactates = input_df['Lactate'].values

    try:
        # สร้างเส้น Curve (ใช้ Cubic Spline เพื่อความเนียนของเส้น)
        f_pace = interp1d(lactates, paces, kind='cubic', fill_value="extrapolate")
        
        # 1. หา Threshold Pace ที่ 4.0 mmol/L
        t_pace = float(f_pace(4.0))

        # 2. คำนวณ Training Zones ตามที่คุณขอ
        zones = {
            "Recovery": t_pace * 1.35,      # ช้าลงอีกนิดเพื่อให้พักได้จริงๆ
            "Easy Run": t_pace * 1.28,        # เน้นโซน 2 ตอนต้น ไม่ให้ล้าเกินไป
            "Long Run": t_pace * 1.20,      # ปลอดภัยสำหรับการวิ่งระยะไกล
            "Marathon Pace": t_pace * 1.12, # เน้นวิ่งจบแบบไม่บอบช้ำ
            "Half Marathon Pace": t_pace * 1.06, # ความเร็วที่คุมได้อยู่หมัด
            "Threshold Pace": t_pace                 # จุดอ้างอิงหลักที่ 4.0
        }

        # --- ส่วนแสดงผลหลัก ---
        # ส่วนที่ 1: ตาราง Pace
        st.subheader("📋 Your Personalized Training Zones")
        cols = st.columns(len(zones))
        for i, (name, p_val) in enumerate(zones.items()):
            cols[i].metric(label=name, value=format_pace(p_val))

        st.divider()

        # ส่วนที่ 2: กราฟและรายละเอียด
        col_left, col_right = st.columns([2, 1])

        with col_left:
            # วาดกราฟ Lactate Curve
            lactate_range = np.linspace(lactates.min(), lactates.max(), 100)
            pace_range = f_pace(lactate_range)

            fig = go.Figure()
            # เส้น Curve
            fig.add_trace(go.Scatter(x=pace_range, y=lactate_range, mode='lines', name='Lactate Curve', line=dict(color='#FF4B4B', width=4)))
            # จุดข้อมูลจริง
            fig.add_trace(go.Scatter(x=paces, y=lactates, mode='markers', name='Test Data', marker=dict(size=12, color='#31333F')))
            
            # เส้นตัด Threshold 4.0
            fig.add_hline(y=4.0, line_dash="dash", line_color="green", annotation_text="LT2 (4.0 mmol/L)")
            fig.add_vline(x=t_pace, line_dash="dash", line_color="green")

            fig.update_layout(
                title="Lactate Curve Visualization",
                xaxis_title="Pace (min/km)",
                yaxis_title="Lactate (mmol/L)",
                xaxis=dict(autorange="reversed"), # ยิ่งไปขวา ยิ่งเร็ว (เลข Pace น้อยลง)
                template="plotly_white"
            )
            st.plotly_chart(fig, use_container_width=True)

        with col_right:
            st.write("### 💡 การวิเคราะห์")
            st.write(f"จากการทดสอบ จุด Threshold ของคุณอยู่ที่ Pace **{format_pace(t_pace)}**")
            st.write("- **Easy/Recovery:** ควรวิ่งให้หัวใจไม่สูงเพื่อสร้างฐานแอโรบิก")
            st.write("- **Threshold:** คือความเร็วที่คุณควรฝึกเพื่อขยับขีดจำกัดความเหนื่อย")
            
            # ตารางสรุปแบบ List
            st.dataframe(pd.DataFrame([{"Zone": k, "Pace": format_pace(v)} for k, v in zones.items()]), use_container_width=True)

    except Exception as e:
        st.error(f"เกิดข้อผิดพลาดในการคำนวณ: {e}")
        st.info("ลองตรวจสอบว่าค่า Lactate ที่กรอกมีการเรียงลำดับจากน้อยไปมาก")

else:
    st.warning("⚠️ กรุณากรอกข้อมูล Pace และ Lactate อย่างน้อย 3 จุดในแถบด้านซ้าย")

