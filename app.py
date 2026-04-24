import streamlit as st
import uuid
import urllib.parse
from utils.db import (
    get_active_jobs_with_center, get_setting, get_faq_items, 
    increment_job_view, get_site_settings
)

# ============ 페이지 설정 ============
st.set_page_config(
    page_title="윌앤비전 채용",
    page_icon="📞",
    layout="centered",
    initial_sidebar_state="collapsed",
)

# ============ 세션 ============
if "session_id" not in st.session_state:
    st.session_state.session_id = str(uuid.uuid4())

# ============ 설정 불러오기 ============
settings = get_site_settings()
hero_title = settings.get('hero_title', '윌앤비전 채용팀')
hero_subtitle = settings.get('hero_subtitle', '수시채용 진행중')
hero_emoji = settings.get('hero_emoji', '🏢')
hero_image = settings.get('hero_image_url', '')
manager_name = settings.get('manager_name', '담당자')
manager_phone = settings.get('manager_phone', '010-9467-6139')
office_address = settings.get('office_address', '')

# ============ 커스텀 CSS ============
st.markdown("""
<style>
    /* 모바일 최적화 */
    .block-container {
        padding-top: 1.5rem !important;
        padding-bottom: 3rem !important;
        max-width: 640px !important;
    }
    
    /* 헤더 영역 */
    .hero-section {
        text-align: center;
        padding: 1.5rem 1rem 2rem;
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        border-radius: 20px;
        margin-bottom: 1.5rem;
        color: white;
    }
    .hero-emoji {
        font-size: 3rem;
        margin-bottom: 0.5rem;
    }
    .hero-title {
        font-size: 1.5rem;
        font-weight: 700;
        margin: 0.25rem 0;
        color: white;
    }
    .hero-subtitle {
        font-size: 0.95rem;
        opacity: 0.95;
        margin: 0.25rem 0;
    }
    .hero-phone {
        font-size: 0.85rem;
        opacity: 0.85;
        margin-top: 0.5rem;
    }
    
    /* 섹션 헤더 */
    .section-header {
        font-size: 1.15rem;
        font-weight: 600;
        margin: 1.5rem 0 0.75rem;
        padding-left: 0.75rem;
        border-left: 4px solid #764ba2;
    }
    
    /* 공고 카드 */
    .job-card {
        background: white;
        border: 1px solid #e8e8ef;
        border-radius: 16px;
        overflow: hidden;
        margin-bottom: 1rem;
        box-shadow: 0 2px 8px rgba(0, 0, 0, 0.04);
        transition: transform 0.2s, box-shadow 0.2s;
    }
    .job-card:hover {
        transform: translateY(-2px);
        box-shadow: 0 4px 16px rgba(118, 75, 162, 0.12);
    }
    .job-image {
        width: 100%;
        height: 160px;
        object-fit: cover;
        background: linear-gradient(135deg, #f0f9ff 0%, #e0f2fe 100%);
    }
    .job-image-placeholder {
        width: 100%;
        height: 120px;
        background: linear-gradient(135deg, #f0f9ff 0%, #e0f2fe 100%);
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 2.5rem;
    }
    .job-content {
        padding: 1rem 1.2rem 1.2rem;
    }
    .job-badge {
        display: inline-block;
        background: #dcfce7;
        color: #166534;
        font-size: 0.7rem;
        font-weight: 600;
        padding: 0.2rem 0.6rem;
        border-radius: 10px;
        margin-bottom: 0.5rem;
    }
    .job-badge-closed {
        background: #f1f5f9;
        color: #64748b;
    }
    .job-title {
        font-size: 1.05rem;
        font-weight: 700;
        color: #1e293b;
        margin: 0.25rem 0 0.75rem;
        line-height: 1.4;
    }
    .job-meta {
        font-size: 0.85rem;
        color: #475569;
        line-height: 1.8;
    }
    .job-meta-item {
        display: flex;
        align-items: center;
        gap: 0.5rem;
    }
    
    /* FAQ */
    .faq-item {
        background: #f8fafc;
        border-radius: 12px;
        padding: 0.9rem 1.1rem;
        margin-bottom: 0.5rem;
        border: 1px solid #e2e8f0;
    }
    
    /* 푸터 */
    .footer {
        text-align: center;
        padding: 1.5rem 0;
        color: #94a3b8;
        font-size: 0.8rem;
    }
    
    /* 어두운 모드 대응 */
    @media (prefers-color-scheme: dark) {
        .job-card {
            background: #1e293b;
            border-color: #334155;
        }
        .job-title { color: #f1f5f9; }
        .job-meta { color: #cbd5e1; }
        .faq-item {
            background: #1e293b;
            border-color: #334155;
        }
    }
    
    /* 모바일에서 더 예쁘게 */
    @media (max-width: 640px) {
        .hero-section { padding: 1.2rem 0.8rem 1.5rem; }
        .hero-emoji { font-size: 2.5rem; }
        .hero-title { font-size: 1.3rem; }
        .job-content { padding: 0.9rem 1rem 1rem; }
        .job-title { font-size: 1rem; }
    }
</style>
""", unsafe_allow_html=True)

# ============ 히어로 영역 ============
if hero_image:
    st.image(hero_image, use_container_width=True)

st.markdown(f"""
<div class="hero-section">
    <div class="hero-emoji">{hero_emoji}</div>
    <div class="hero-title">{hero_title}</div>
    <div class="hero-subtitle">{hero_subtitle}</div>
    <div class="hero-phone">📞 {manager_name} · {manager_phone}</div>
</div>
""", unsafe_allow_html=True)

# ============ 모집 공고 ============
st.markdown('<div class="section-header">📌 모집 중인 공고</div>', unsafe_allow_html=True)

jobs = get_active_jobs_with_center()

if not jobs:
    st.info("현재 모집 중인 공고가 없습니다. 곧 새 공고가 오픈될 예정입니다.")
else:
    for job in jobs:
        # 카드 이미지 부분
        if job.get('image_url'):
            image_html = f'<img src="{job["image_url"]}" class="job-image" alt="{job["title"]}">'
        else:
            emoji = '📞' if job.get('category') == 'OB상담' else '📱'
            image_html = f'<div class="job-image-placeholder">{emoji}</div>'
        
        # 센터 정보
        center_info = ""
        if job.get('centers'):
            center_info = f"🏢 {job['centers']['name']}"
        
        # 지하철 정보
        subway_info = ""
        if job.get('subway_station'):
            subway_info = f"🚇 {job.get('subway_line', '')} {job['subway_station']}"
        elif job.get('centers') and job['centers'].get('subway_info'):
            subway_info = f"🚇 {job['centers']['subway_info']}"
        
        # 카드 HTML
        st.markdown(f"""
        <div class="job-card">
            {image_html}
            <div class="job-content">
                <span class="job-badge">● {job['status']}</span>
                <div class="job-title">{job['title']}</div>
                <div class="job-meta">
                    {f'<div class="job-meta-item">{center_info}</div>' if center_info else ''}
                    <div class="job-meta-item">📍 {job.get('location', '')}</div>
                    <div class="job-meta-item">💰 {job.get('salary', '')}</div>
                    <div class="job-meta-item">⏰ {job.get('work_hours', '')} · {job.get('work_days', '')}</div>
                    {f'<div class="job-meta-item">📅 교육 {job["education_period"]}</div>' if job.get('education_period') else ''}
                    {f'<div class="job-meta-item">{subway_info}</div>' if subway_info else ''}
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        # 액션 버튼
        col1, col2 = st.columns(2)
        with col1:
            if st.button("💬 문의하기", key=f"chat_{job['id']}", use_container_width=True):
                st.session_state['preset_question'] = f"{job['title']} 공고에 대해 알려주세요"
                st.session_state['preset_job_id'] = job['id']
                increment_job_view(job['id'], st.session_state.session_id)
                st.switch_page("pages/1_AI_상담사.py")
        with col2:
            apply_url = job.get('google_form_url') or settings.get('default_google_form_url', '')
            if apply_url:
                st.link_button("📝 지원하기", apply_url, use_container_width=True, type="primary")
            else:
                st.button("📝 지원 준비중", key=f"apply_{job['id']}", use_container_width=True, disabled=True)

# ============ 빠른 메뉴 ============
st.markdown('<div class="section-header">⚡ 빠른 메뉴</div>', unsafe_allow_html=True)

col1, col2 = st.columns(2)
with col1:
    if st.button("💬 AI 상담사", use_container_width=True, type="primary"):
        st.switch_page("pages/1_AI_상담사.py")
with col2:
    if st.button("🙋 담당자 연결", use_container_width=True):
        st.switch_page("pages/4_담당자연결.py")

col1, col2 = st.columns(2)
with col1:
    if st.button("🚇 출근 거리 확인", use_container_width=True):
        st.switch_page("pages/3_출근거리.py")
with col2:
    if office_address:
        encoded_address = urllib.parse.quote(office_address)
        map_url = f"https://map.kakao.com/?q={encoded_address}"
        st.link_button("🗺️ 오시는 길", map_url, use_container_width=True)
    else:
        st.link_button("🗺️ 오시는 길", "https://map.kakao.com/", use_container_width=True)

# ============ FAQ ============
faqs = get_faq_items()
if faqs:
    st.markdown('<div class="section-header">💡 자주 묻는 질문</div>', unsafe_allow_html=True)
    
    for faq in faqs[:5]:  # 최대 5개만
        with st.expander(f"❓ {faq.get('question', '')}"):
            st.write(faq.get('answer', ''))

# ============ 푸터 ============
st.markdown(f"""
<div class="footer">
    💬 궁금한 점은 AI 상담사가 24시간 답변해드립니다<br>
    📞 {manager_name} · {manager_phone}<br>
    <br>
    © 윌앤비전 채용팀
</div>
""", unsafe_allow_html=True)
