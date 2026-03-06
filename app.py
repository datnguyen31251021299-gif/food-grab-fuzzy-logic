import streamlit as st
import numpy as np
import skfuzzy as fuzzy
from skfuzzy import control as ctrl
import folium
from streamlit_folium import st_folium
from math import radians, cos, sin, asin, sqrt

# --- CẤU HÌNH TRANG ---
st.set_page_config(page_title="App Đánh Giá Tài Xế Food Grab", layout="wide")
st.title("🚚 Hệ Thống Đánh Giá & Quản Lý Giao Hàng (Fuzzy Logic)")

# --- 1. XÂY DỰNG HỆ THỐNG LOGIC MỜ (FUZZY SYSTEM) ---

# Khai báo các biến đầu vào (Antecedents)
traffic = ctrl.Antecedent(np.arange(0, 11, 1), 'traffic')  # 0-10: Thấp -> Cao
distance_input = ctrl.Antecedent(np.arange(0, 16, 1), 'distance') # 0-15km
weather = ctrl.Antecedent(np.arange(0, 11, 1), 'weather') # 0-10: Đẹp -> Bão
fatigue = ctrl.Antecedent(np.arange(0, 11, 1), 'fatigue') # 0-10: Khỏe -> Mệt

# Khai báo các biến đầu ra (Consequents)
edt = ctrl.Consequent(np.arange(0, 61, 1), 'edt') # Thời gian giao: 0-60p
bonus = ctrl.Consequent(np.arange(0, 101, 1), 'bonus') # Tiền thưởng %: 0-100%
rating = ctrl.Consequent(np.arange(1, 6, 1), 'rating') # Xếp hạng: 1-5 sao

# Định nghĩa các tập mờ (Membership Functions) theo tài liệu
traffic['L'] = fuzzy.trimf(traffic.universe, [0, 0, 5])
traffic['M'] = fuzzy.trimf(traffic.universe, [2, 5, 8])
traffic['H'] = fuzzy.trimf(traffic.universe, [5, 10, 10])

distance_input['S'] = fuzzy.trimf(distance_input.universe, [0, 0, 3])
distance_input['M'] = fuzzy.trimf(distance_input.universe, [2, 5, 8])
distance_input['L'] = fuzzy.trimf(distance_input.universe, [7, 15, 15])

weather['C'] = fuzzy.trimf(weather.universe, [0, 0, 4])
weather['R'] = fuzzy.trimf(weather.universe, [3, 6, 8])
weather['S'] = fuzzy.trimf(weather.universe, [7, 10, 10])

fatigue['L'] = fuzzy.trimf(fatigue.universe, [0, 0, 5])
fatigue['M'] = fuzzy.trimf(fatigue.universe, [3, 5, 7])
fatigue['H'] = fuzzy.trimf(fatigue.universe, [6, 10, 10])

# Định nghĩa đầu ra
edt['S'] = fuzzy.trimf(edt.universe, [0, 0, 15])
edt['M'] = fuzzy.trimf(edt.universe, [10, 25, 40])
edt['L'] = fuzzy.trimf(edt.universe, [35, 60, 60])

bonus['L'] = fuzzy.trimf(bonus.universe, [0, 0, 30])
bonus['M'] = fuzzy.trimf(bonus.universe, [20, 50, 80])
bonus['H'] = fuzzy.trimf(bonus.universe, [70, 100, 100])

rating['P'] = fuzzy.trimf(rating.universe, [1, 1, 3])
rating['A'] = fuzzy.trimf(rating.universe, [2, 3, 4])
rating['E'] = fuzzy.trimf(rating.universe, [4, 5, 5])

# Định nghĩa các luật mờ (Fuzzy Rules) - Dựa theo Hình 2 & 3 của bạn
rule1 = ctrl.Rule(traffic['L'] & distance_input['S'], edt['S'])
rule2 = ctrl.Rule(traffic['H'] | weather['S'], bonus['H'])
rule3 = ctrl.Rule(fatigue['L'], rating['E'])
rule4 = ctrl.Rule(fatigue['H'] & traffic['H'], rating['P'])
rule5 = ctrl.Rule(distance_input['L'] & weather['S'], [edt['L'], bonus['H']])

delivery_ctrl = ctrl.ControlSystem([rule1, rule2, rule3, rule4, rule5])
delivery_sim = ctrl.ControlSystemSimulation(delivery_ctrl)

# --- 2. GIAO DIỆN & BẢN ĐỒ (MAP) ---
col1, col2 = st.columns([1, 1])

with col1:
    st.subheader("📍 Chọn địa điểm trên Bản đồ")
    m = folium.Map(location=[10.762622, 106.660172], zoom_start=13) # Tọa độ TP.HCM
    m.add_child(folium.LatLngPopup())
    map_data = st_folium(m, height=400, width=500)

    # Logic tính khoảng cách Haversine
    def haversine(lon1, lat1, lon2, lat2):
        lon1, lat1, lon2, lat2 = map(radians, [lon1, lat1, lon2, lat2])
        dlon = lon2 - lon1 
        dlat = lat2 - lat1 
        a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlon/2)**2
        return 6371 * 2 * asin(sqrt(a))

    # Giả lập điểm nhận (A) và điểm giao (B)
    if 'points' not in st.session_state: st.session_state.points = []
    
    if map_data and map_data['last_clicked']:
        st.session_state.points.append(map_data['last_clicked'])
        if len(st.session_state.points) > 2: st.session_state.points = st.session_state.points[-2:]

    dist = 0.0
    if len(st.session_state.points) == 2:
        p1, p2 = st.session_state.points
        dist = haversine(p1['lng'], p1['lat'], p2['lng'], p2['lat'])
        st.success(f"Khoảng cách tính toán: {dist:.2f} km")

with col2:
    st.subheader("⚙️ Thông số đầu vào")
    traffic_val = st.slider("Tình trạng giao thông (0: Thoáng, 10: Tắc)", 0, 10, 5)
    weather_val = st.select_slider("Thời tiết", options=["Quang đãng", "Mưa", "Bão"], value="Quang đãng")
    fatigue_val = st.slider("Độ mệt mỏi tài xế (0: Khỏe, 10: Kiệt sức)", 0, 10, 2)
    
    weather_map = {"Quang đãng": 2, "Mưa": 6, "Bão": 9}
    
    if st.button("Tính toán kết quả"):
        # Gán giá trị vào hệ thống mờ
        delivery_sim.input['traffic'] = traffic_val
        delivery_sim.input['distance'] = min(dist, 15)
        delivery_sim.input['weather'] = weather_map[weather_val]
        delivery_sim.input['fatigue'] = fatigue_val
        
        # Thực thi giải mờ
        delivery_sim.compute()
        
        res_edt = delivery_sim.output['edt']
        res_bonus = delivery_sim.output['bonus']
        res_rating = delivery_sim.output['rating']
        
        # --- 3. HIỂN THỊ KẾT QUẢ ---
        st.divider()
        c1, c2, c3 = st.columns(3)
        
        # Tính giá tiền (Giả định: 15k cơ bản + 5k/km)
        price = 15000 + (dist * 5000)
        
        c1.metric("💰 Tổng tiền", f"{price:,.0f} VNĐ")
        c2.metric("⏱️ Thời gian ước tính", f"{res_edt:.1f} phút")
        c3.metric("🎁 Tiền thưởng thêm", f"{res_bonus:.1f} %")
        
        st.subheader(f"⭐ Xếp hạng hiệu suất: {res_rating:.1f} / 5")
        st.progress(res_rating / 5)