import streamlit as st
from utils.db import get_active_jobs

st.set_page_config(
    page_title="윌앤비전 채용",
    page_icon="📞",
    layout="centered",
    initial_sidebar_state="collapsed",
)

st.markdown("""
<style>
    .main-header { text-align: center; padding: 1rem 0; }
    .job-card {
        background: #f0f9f4;
        border-radius: 12px;
        padding: 1.2rem;
        margin-bottom: 0.8rem;
        border-left: 4px solid #1D9E75;
    }
    .job-title {
        font-size: 1.1rem;
        font-weight: 600;
        color: #085041;
        margin-bottom: 0.5rem;
    }
    .job-meta {
        font-size: 0.9rem;
        color: #0F6E56;
        line-height: 1.6;
    }
</style>
""", unsafe_allow_html=True)

st.markdown('<div class="main-header">', unsafe_allow_html=True)
st.markdown("# 🏢 윌앤비전 채용팀")
st.markdown("##### 수시채용 진행중 · 문래역 콜센터")
st.caption("담당자 010-9467-6139")
st.markdown('</div>', unsafe_allow_html=True)

st.divider()

st.markdown("### 📌 모집 중인 공고")

jobs = get_active_jobs()

if not jobs:
    st.info("현재 모집 중인 공고가 없습니다. 곧 새 공고가 오픈될 예정입니다.")
else:
    for job in jobs:
        with st.container():
            st.markdown(f"""
            <div class="job-card">
                <div class="job-title">🟢 {job['title']}</div>
                <div class="job-meta">
                    📍 {job['location']}<br>
                    💰 {job['salary']}<br>
                    ⏰ {job['work_hours']} · {job['work_days']}<br>
                    📅 교육: {job['education_period']}
                </div>
            </div>
            """, unsafe_allow_html=True)
            
            with st.expander("자세히 보기"):
                st.write(f"**특징**: {job['features']}")
                st.write(f"**상세 설명**: {job['description']}")
                col1, col2 = st.columns(2)
                with col1:
                    if st.button("💬 이 공고 문의", key=f"chat_{job['id']}", use_container_width=True):
                        st.session_state['preset_question'] = f"{job['title']} 공고에 대해 알려주세요"
                        st.switch_page("pages/1_AI_상담사.py")
                with col2:
                    if st.button("📝 바로 지원", key=f"apply_{job['id']}", use_container_width=True, type="primary"):
                        st.session_state['preset_job_id'] = job['id']
                        st.switch_page("pages/2_간편지원.py")

st.divider()

st.markdown("### 💬 문의 및 지원")

col1, col2, col3 = st.columns(3)

with col1:
    if st.button("💬\nAI 상담사", use_container_width=True):
        st.switch_page("pages/1_AI_상담사.py")

with col2:
    if st.button("📝\n간편 지원", use_container_width=True, type="primary"):
        st.switch_page("pages/2_간편지원.py")

with col3:
    st.link_button("📞\n전화 문의", "tel:01094676139", use_container_width=True)

st.divider()
st.caption("💡 궁금한 점은 AI 상담사가 24시간 답변해드립니다.")
st.caption("© 윌앤비전 채용팀")
