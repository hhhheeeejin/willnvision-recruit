import streamlit as st
from utils.db import (
    get_subway_stations, calculate_distance_km,
    get_site_settings, get_active_jobs
)

st.set_page_config(page_title="출근 거리 확인", page_icon="🚇", layout="centered")

# ============ 설정 ============
settings = get_site_settings()
office_address = settings.get('office_address', '')

try:
    office_lat = float(settings.get('office_latitude', '37.5178'))
    office_lng = float(settings.get('office_longitude', '126.8944'))
except (ValueError, TypeError):
    office_lat = 37.5178
    office_lng = 126.8944

# ============ 히어로 ============
st.markdown("""
<style>
.distance-hero {
    text-align: center;
    padding: 1rem 0 1.5rem;
}
.distance-hero-icon { font-size: 2.8rem; margin-bottom: 0.25rem; }
.distance-hero-title { font-size: 1.4rem; font-weight: 700; margin: 0.25rem 0; }
.distance-hero-sub { font-size: 0.9rem; color: #64748b; }
</style>
<div class="distance-hero">
    <div class="distance-hero-icon">🚇</div>
    <div class="distance-hero-title">출근 거리 확인</div>
    <div class="distance-hero-sub">집에서 사무실까지 얼마나 걸릴지 확인해보세요!</div>
</div>
""", unsafe_allow_html=True)

st.info(f"🏢 **사무실 위치**: {office_address or '서울시 영등포구 문래동'}")

# ============ 출발역 선택 ============
st.markdown("### 🚏 출발 지하철역을 선택하세요")

stations = get_subway_stations()
station_names = sorted(stations.keys())

# 자주 쓰는 역 빠른 선택
st.markdown("**🔥 자주 찾는 역**")
quick_stations = ["강남", "잠실", "홍대입구", "신도림", "구로디지털단지", "서울역", "건대입구", "사당"]
cols = st.columns(4)
for i, s in enumerate(quick_stations):
    with cols[i % 4]:
        if st.button(s, key=f"quick_{s}", use_container_width=True):
            st.session_state['selected_station'] = s

st.markdown("**🔍 전체 역에서 찾기**")
selected = st.selectbox(
    "역 선택",
    options=[""] + station_names,
    index=(station_names.index(st.session_state.get('selected_station', '')) + 1) 
          if st.session_state.get('selected_station') in station_names else 0,
    format_func=lambda x: "역을 선택하세요..." if x == "" else f"🚇 {x}역",
    label_visibility="collapsed",
)

# ============ 거리 계산 ============
if selected:
    start_lat, start_lng = stations[selected]
    distance_km = calculate_distance_km(start_lat, start_lng, office_lat, office_lng)
    
    # 대략 계산: 지하철 평균속도 25km/h, 환승 5분, 도보 10분
    # 직선거리 기반이라 오차 있음 (대략치)
    travel_time = int((distance_km / 25) * 60 + 15)  # 도보/환승 포함 15분 추가
    
    st.divider()
    
    # 결과 카드
    st.markdown(f"""
    <div style="background: linear-gradient(135deg, #ddd6fe 0%, #c7d2fe 100%); 
                padding: 1.5rem; border-radius: 16px; margin: 1rem 0;
                text-align: center;">
        <div style="font-size: 0.9rem; color: #4c1d95; margin-bottom: 0.5rem;">
            🚇 {selected}역 → 🏢 문래역 사무실
        </div>
        <div style="font-size: 2rem; font-weight: 700; color: #312e81; margin: 0.5rem 0;">
            약 {travel_time}분
        </div>
        <div style="font-size: 0.85rem; color: #64748b;">
            📏 직선거리 {distance_km:.1f}km
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    # 예상 정보
    st.markdown("### 📊 참고 정보")
    
    col1, col2 = st.columns(2)
    with col1:
        st.metric("🕐 예상 소요시간", f"{travel_time}분", help="지하철 + 환승 + 도보 포함 예상치")
    with col2:
        # 대략적인 교통비
        if distance_km < 10:
            fare = "약 1,400원"
        elif distance_km < 30:
            fare = "약 1,500~1,700원"
        else:
            fare = "약 1,800~2,200원"
        st.metric("💳 교통비 (편도)", fare, help="일반 성인 기준")
    
    # 카카오맵 링크
    st.markdown("### 🗺️ 정확한 경로 확인")
    kakao_url = f"https://map.kakao.com/link/to/윌앤비전 사무실,{office_lat},{office_lng}/from/{selected}역,{start_lat},{start_lng}"
    st.link_button("🗺️ 카카오맵에서 자세히 보기", kakao_url, type="primary", use_container_width=True)
    
    naver_url = f"https://map.naver.com/p/directions/-/-/-/-/-/-/transit?c=15.00,0,0,0,dh"
    st.link_button("🗺️ 네이버지도로 확인", naver_url, use_container_width=True)
    
    # 추천 공고 (가까운 역 지원자에게)
    jobs = get_active_jobs()
    if jobs:
        st.divider()
        st.markdown("### 💼 이 분에게 추천하는 공고")
        if travel_time <= 30:
            st.success(f"✨ 출근 부담이 적어요! 현재 모집 중인 공고를 확인해보세요.")
        elif travel_time <= 60:
            st.info(f"🚇 출근 시간이 적당해요. 공고를 살펴보세요!")
        else:
            # 재택 공고 우선 추천
            remote_jobs = [j for j in jobs if '재택' in (j.get('features', '') or '') or '재택' in (j.get('location', '') or '')]
            if remote_jobs:
                st.warning(f"⏰ 출퇴근이 조금 부담될 수 있어요. 재택 가능한 공고는 어떠세요?")
                for j in remote_jobs[:2]:
                    st.markdown(f"- **{j['title']}** ({j.get('salary', '')})")
            else:
                st.warning(f"⏰ 출퇴근이 조금 부담될 수 있어요. 아래에서 자세한 근무 조건을 확인해보세요.")

else:
    st.info("👆 위에서 출발할 지하철역을 선택해주세요.")

st.divider()

# ============ 하단 액션 ============
col1, col2 = st.columns(2)
with col1:
    if st.button("💬 AI 상담사에게 물어보기", use_container_width=True):
        st.switch_page("pages/1_AI_상담사.py")
with col2:
    manager_phone = settings.get('manager_phone', '010-9467-6139')
    st.link_button(f"📞 {manager_phone}", f"tel:{manager_phone.replace('-','')}", use_container_width=True)

# 안내
st.caption("💡 예상 시간은 지하철 기준 대략치입니다. 정확한 경로는 카카오맵/네이버지도에서 확인하세요.")
