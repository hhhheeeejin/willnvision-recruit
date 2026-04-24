import streamlit as st
import urllib.parse
from utils.db import (
    get_active_centers, get_site_settings, get_active_jobs_with_center
)

st.set_page_config(page_title="출근 거리 확인", page_icon="🚇", layout="centered")

# ============ 설정 ============
settings = get_site_settings()

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
    <div class="distance-hero-title">출근 경로 확인</div>
    <div class="distance-hero-sub">출발지와 도착지를 선택하고 카카오맵으로 확인하세요!</div>
</div>
""", unsafe_allow_html=True)

# ============ 출발지 입력 ============
st.markdown("### 🏠 1️⃣ 출발지 (집 주소)")

start_address = st.text_input(
    "출발 주소를 입력하세요",
    placeholder="예: 서울특별시 강남구 테헤란로 123 (또는 '강남역')",
    label_visibility="collapsed",
    key="start_address_input",
)

st.caption("💡 주소, 지하철역, 랜드마크 모두 OK! (예: '강남역', '서울시청', '판교역')")

# 자주 쓰는 위치 빠른 선택
st.caption("🔥 자주 찾는 출발지")
quick_cols = st.columns(4)
quick_locations = [
    "강남역",
    "홍대입구역",
    "서울역",
    "잠실역",
]
for i, loc in enumerate(quick_locations):
    with quick_cols[i]:
        if st.button(loc, key=f"quick_start_{i}", use_container_width=True):
            st.session_state['start_addr_preset'] = loc
            st.rerun()

# Preset 적용
if 'start_addr_preset' in st.session_state:
    start_address = st.session_state.pop('start_addr_preset')
    st.info(f"✅ 선택됨: **{start_address}**")

# ============ 도착지 선택 (센터) ============
st.divider()
st.markdown("### 🏢 2️⃣ 도착지 (센터 선택)")

centers = get_active_centers()

if not centers:
    st.warning("⚠️ 등록된 센터가 없어요. 관리자가 센터를 등록해야 해요.")
    st.stop()

# 센터 선택
if len(centers) == 1:
    selected_center = centers[0]
    st.info(f"🏢 **{selected_center['name']}** — {selected_center['address']}")
else:
    center_options = {c['id']: c['name'] for c in centers}
    selected_center_id = st.radio(
        "어느 센터로 갈지 선택",
        options=list(center_options.keys()),
        format_func=lambda x: f"🏢 {center_options[x]}",
        label_visibility="collapsed",
    )
    selected_center = next(c for c in centers if c['id'] == selected_center_id)

# 선택된 센터 정보 표시
with st.container(border=True):
    st.markdown(f"**📍 {selected_center['name']}**")
    st.caption(f"🏠 {selected_center['address']}")
    if selected_center.get('detail_address'):
        st.caption(f"📌 {selected_center['detail_address']}")
    if selected_center.get('subway_info'):
        st.caption(f"🚇 {selected_center['subway_info']}")
    if selected_center.get('bus_info'):
        st.caption(f"🚌 {selected_center['bus_info']}")
    if selected_center.get('parking_available'):
        st.caption("🚗 주차 가능")

# ============ 교통수단 선택 ============
st.divider()
st.markdown("### 🚏 3️⃣ 교통수단 선택")

transport_options = {
    "publictransit": ("🚇 대중교통", "지하철 + 버스 경로"),
    "car": ("🚗 자동차", "실시간 교통정보 반영"),
    "foot": ("🚶 도보", "걷기 최적 경로"),
    "bicycle": ("🚴 자전거/따릉이", "자전거 도로 우선"),
}

transport_cols = st.columns(4)
selected_transport = st.session_state.get('selected_transport', 'publictransit')

for i, (key, (label, desc)) in enumerate(transport_options.items()):
    with transport_cols[i]:
        is_selected = (key == selected_transport)
        if st.button(
            label,
            key=f"trans_{key}",
            use_container_width=True,
            type="primary" if is_selected else "secondary",
        ):
            st.session_state['selected_transport'] = key
            st.rerun()

st.caption(f"💡 {transport_options[selected_transport][1]}")

# ============ 경로 확인 ============
st.divider()

if not start_address:
    st.info("👆 출발 주소를 입력하거나 자주 찾는 위치를 선택해주세요.")
else:
    st.markdown("### 🗺️ 4️⃣ 경로 확인")
    
    # 카카오맵 & 네이버지도 길찾기 URL 생성
    start_encoded = urllib.parse.quote(start_address)
    end_encoded = urllib.parse.quote(selected_center['address'])
    
    # 카카오맵 길찾기
    kakao_url = f"https://map.kakao.com/?sName={start_encoded}&eName={end_encoded}"
    
    # 네이버지도 이동수단 코드
    naver_transport_map = {
        "publictransit": "transit",
        "car": "car",
        "foot": "walk",
        "bicycle": "bicycle",
    }
    naver_mode = naver_transport_map.get(selected_transport, "transit")
    naver_url = f"https://map.naver.com/p/directions/-/{end_encoded}/{naver_mode}"
    
    # 결과 카드
    display_start = start_address[:25] + ('...' if len(start_address) > 25 else '')
    st.markdown(f"""
    <div style="background: linear-gradient(135deg, #ddd6fe 0%, #c7d2fe 100%); 
                padding: 1.3rem; border-radius: 16px; margin: 1rem 0;
                text-align: center;">
        <div style="font-size: 0.9rem; color: #4c1d95; margin-bottom: 0.3rem;">
            🏠 {display_start}
        </div>
        <div style="font-size: 1.2rem; color: #312e81; margin: 0.3rem 0;">
            ⬇️
        </div>
        <div style="font-size: 1rem; font-weight: 600; color: #312e81; margin-bottom: 0.3rem;">
            🏢 {selected_center['name']}
        </div>
        <div style="font-size: 0.8rem; color: #64748b;">
            {transport_options[selected_transport][0]}
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    # 지도 버튼들
    col1, col2 = st.columns(2)
    with col1:
        st.link_button(
            "🗺️ 카카오맵에서 보기",
            kakao_url,
            type="primary",
            use_container_width=True,
        )
    with col2:
        st.link_button(
            "🗺️ 네이버지도에서 보기",
            naver_url,
            use_container_width=True,
        )
    
    st.caption("💡 버튼을 누르면 정확한 예상 시간, 거리, 환승 정보가 표시됩니다.")
    
    # ============ 참고 정보 ============
    st.divider()
    st.markdown("### 📊 참고 정보")
    
    info_by_transport = {
        "publictransit": {
            "icon": "🚇",
            "info_lines": [
                "💳 교통비: 일반 1,500~2,000원 (편도)",
                "⏰ 평균 대기시간: 지하철 3~7분, 버스 5~15분",
                "🎫 교통카드 사용 시 환승 할인 적용",
            ],
        },
        "car": {
            "icon": "🚗",
            "info_lines": [
                "⛽ 유류비: 거리에 따라 상이 (실시간 확인)",
                "🅿️ 센터 주차: " + ("가능 ✅" if selected_center.get('parking_available') else "제한적 ⚠️"),
                "🚦 출퇴근 시간대 교통 혼잡 유의",
            ],
        },
        "foot": {
            "icon": "🚶",
            "info_lines": [
                "👟 편한 신발 권장",
                "☂️ 비 오는 날 대비 (우산/우비)",
                "⏰ 도보는 교통상황 영향 없음",
            ],
        },
        "bicycle": {
            "icon": "🚴",
            "info_lines": [
                "🚲 따릉이 요금: 1시간 1,000원",
                "🛣️ 자전거 도로 확인 필요",
                "⛈️ 날씨 영향 받음",
            ],
        },
    }
    
    info = info_by_transport[selected_transport]
    for line in info['info_lines']:
        st.caption(line)
    
    # ============ 이 센터 공고 추천 ============
    st.divider()
    st.markdown(f"### 💼 {selected_center['name']}의 모집 중인 공고")
    
    try:
        all_jobs_with_center = get_active_jobs_with_center()
        center_jobs = [j for j in all_jobs_with_center if j.get('center_id') == selected_center['id']]
    except Exception:
        center_jobs = []
    
    if center_jobs:
        for job in center_jobs:
            with st.container(border=True):
                col1, col2 = st.columns([3, 1])
                with col1:
                    st.markdown(f"**{job['title']}**")
                    st.caption(f"💰 {job.get('salary', '')} · ⏰ {job.get('work_hours', '')}")
                with col2:
                    if st.button("자세히", key=f"job_{job['id']}", use_container_width=True):
                        st.session_state['preset_question'] = f"{job['title']} 공고에 대해 알려주세요"
                        st.switch_page("pages/1_AI_상담사.py")
    else:
        st.info("현재 이 센터에서 모집 중인 공고가 없습니다.")

# ============ 하단 액션 ============
st.divider()
col1, col2 = st.columns(2)
with col1:
    if st.button("💬 AI 상담사", use_container_width=True):
        st.switch_page("pages/1_AI_상담사.py")
with col2:
    manager_phone = settings.get('manager_phone', '010-9467-6139')
    st.link_button(f"📞 {manager_phone}", f"tel:{manager_phone.replace('-','')}", use_container_width=True)

st.caption("⚠️ 정확한 예상 시간과 비용은 카카오맵/네이버지도 결과를 기준으로 확인해주세요.")
