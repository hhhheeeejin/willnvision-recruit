import streamlit as st
import uuid
import urllib.parse
from openai import OpenAI
from utils.db import (
    get_active_jobs_with_center, get_faq_items, 
    increment_job_view, increment_job_apply, get_site_settings,
    get_active_jobs, get_knowledge_base, save_conversation,
    get_active_centers,
)

# ============================================
# 페이지 설정
# ============================================
st.set_page_config(
    page_title="윌앤비전 채용",
    page_icon="📞",
    layout="centered",
    initial_sidebar_state="collapsed",
)

# ============================================
# 세션 초기화
# ============================================
if "session_id" not in st.session_state:
    st.session_state.session_id = str(uuid.uuid4())
if "messages" not in st.session_state:
    st.session_state.messages = []
if "active_tab" not in st.session_state:
    st.session_state.active_tab = "chat"

# ============================================
# 사이트 설정 불러오기
# ============================================
settings = get_site_settings()
hero_title = settings.get('hero_title', '윌앤비전 채용팀')
hero_subtitle = settings.get('hero_subtitle', '수시채용 진행중')
hero_emoji = settings.get('hero_emoji', '🏢')
hero_image = settings.get('hero_image_url', '')
manager_name = settings.get('manager_name', '담당자')
manager_phone = settings.get('manager_phone', '010-9467-6139')
office_address = settings.get('office_address', '')
default_form_url = settings.get('default_google_form_url', '')
openchat_url = settings.get('kakao_openchat_url', '')
tone = settings.get('chatbot_tone', 'friendly')

# ============================================
# OpenAI 클라이언트
# ============================================
client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])

# ============================================
# CSS 스타일
# ============================================
st.markdown("""
<style>
.block-container {
    padding-top: 1rem !important;
    padding-bottom: 3rem !important;
    max-width: 640px !important;
}
.hero-section {
    text-align: center;
    padding: 1.5rem 1rem 1.8rem;
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    border-radius: 20px;
    margin-bottom: 1.2rem;
    color: white;
}
.hero-emoji { font-size: 2.8rem; margin-bottom: 0.3rem; }
.hero-title { font-size: 1.4rem; font-weight: 700; margin: 0.25rem 0; color: white; }
.hero-subtitle { font-size: 0.9rem; opacity: 0.95; margin: 0.25rem 0; }
.hero-phone { font-size: 0.82rem; opacity: 0.85; margin-top: 0.3rem; }
.section-header {
    font-size: 1.05rem;
    font-weight: 600;
    margin: 1.2rem 0 0.6rem;
    padding-left: 0.6rem;
    border-left: 4px solid #764ba2;
}
.job-card {
    background: white;
    border: 1px solid #e8e8ef;
    border-radius: 14px;
    overflow: hidden;
    margin-bottom: 0.8rem;
    box-shadow: 0 2px 6px rgba(0, 0, 0, 0.04);
}
.job-image { width: 100%; height: 130px; object-fit: cover; }
.job-image-placeholder {
    width: 100%;
    height: 100px;
    background: linear-gradient(135deg, #f0f9ff 0%, #e0f2fe 100%);
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 2.2rem;
}
.job-content { padding: 0.8rem 1rem 0.9rem; }
.job-badge {
    display: inline-block;
    background: #dcfce7;
    color: #166534;
    font-size: 0.68rem;
    font-weight: 600;
    padding: 0.15rem 0.55rem;
    border-radius: 8px;
    margin-bottom: 0.4rem;
}
.job-title { font-size: 1rem; font-weight: 700; color: #1e293b; margin: 0.2rem 0 0.5rem; line-height: 1.35; }
.job-meta { font-size: 0.82rem; color: #475569; line-height: 1.7; }
.job-meta-item { display: block; margin: 0.15rem 0; }
.footer {
    text-align: center;
    padding: 1.2rem 0;
    color: #94a3b8;
    font-size: 0.75rem;
}
@media (prefers-color-scheme: dark) {
    .job-card { background: #1e293b; border-color: #334155; }
    .job-title { color: #f1f5f9; }
    .job-meta { color: #cbd5e1; }
}
@media (max-width: 640px) {
    .hero-emoji { font-size: 2.3rem; }
    .hero-title { font-size: 1.2rem; }
}
</style>
""", unsafe_allow_html=True)

# ============================================
# 히어로 영역
# ============================================
if hero_image:
    st.image(hero_image, use_container_width=True)

st.markdown(
    '<div class="hero-section">'
    f'<div class="hero-emoji">{hero_emoji}</div>'
    f'<div class="hero-title">{hero_title}</div>'
    f'<div class="hero-subtitle">{hero_subtitle}</div>'
    f'<div class="hero-phone">📞 {manager_name} · {manager_phone}</div>'
    '</div>',
    unsafe_allow_html=True
)

# ============================================
# 모집 공고 목록 (드롭다운)
# ============================================
st.markdown('<div class="section-header">📌 모집 중인 공고</div>', unsafe_allow_html=True)

jobs = get_active_jobs_with_center()

if not jobs:
    st.info("현재 모집 중인 공고가 없습니다.")
else:
    for job in jobs:
        # 상태 배지
        status_emoji = "🟢" if job['status'] == '모집중' else ("🟡" if job['status'] == '재오픈예정' else "⚫")
        
        # 드롭다운 (expander)
        with st.expander(f"{status_emoji} **{job['title']}**", expanded=False):
            
            # 이미지 표시
            if job.get('image_url'):
                st.image(job['image_url'], use_container_width=True)
            
            # 상세 정보
            detail_lines = []
            if job.get('centers'):
                detail_lines.append(f"🏢 **{job['centers']['name']}**")
            if job.get('location'):
                detail_lines.append(f"📍 {job.get('location')}")
            if job.get('salary'):
                detail_lines.append(f"💰 {job.get('salary')}")
            if job.get('work_hours') or job.get('work_days'):
                detail_lines.append(f"⏰ {job.get('work_hours', '')} · {job.get('work_days', '')}")
            if job.get('education_period'):
                detail_lines.append(f"📅 교육 {job['education_period']}")
            if job.get('subway_station'):
                detail_lines.append(f"🚇 {job.get('subway_line', '')} {job['subway_station']}")
            elif job.get('centers') and job['centers'].get('subway_info'):
                detail_lines.append(f"🚇 {job['centers']['subway_info']}")
            if job.get('features'):
                detail_lines.append(f"✨ {job['features']}")
            
            for line in detail_lines:
                st.markdown(line)
            
            # 설명 (있으면)
            if job.get('description'):
                st.markdown("---")
                st.caption(job['description'])
            
            st.markdown("<br>", unsafe_allow_html=True)
            
            # 액션 버튼
            col1, col2 = st.columns(2)
            with col1:
                if st.button("💬 이 공고 문의", key=f"chat_{job['id']}", use_container_width=True):
                    st.session_state['preset_question'] = f"{job['title']} 공고에 대해 알려주세요"
                    st.session_state['preset_job_id'] = job['id']
                    st.session_state.active_tab = "chat"
                    increment_job_view(job['id'], st.session_state.session_id)
                    st.rerun()
            with col2:
                apply_url = job.get('google_form_url') or default_form_url
                if apply_url:
                    # 지원 버튼 클릭 시 카운트 증가 후 링크 열기
                    if st.button("📝 지원하기", key=f"apply_{job['id']}", use_container_width=True, type="primary"):
                        increment_job_apply(job['id'], st.session_state.session_id)
                        # JavaScript로 새 탭에서 열기
                        st.markdown(f'<meta http-equiv="refresh" content="0; url={apply_url}">', unsafe_allow_html=True)
                        st.success(f"지원 페이지로 이동 중...")
                        st.markdown(f"자동 이동 안 되면 [여기 클릭]({apply_url})")
                else:
                    st.button("📝 지원 준비중", key=f"apply_{job['id']}", use_container_width=True, disabled=True)

# ============================================
# 기능 탭 선택 (4개)
# ============================================
st.markdown('<div class="section-header">⚡ 기능 선택</div>', unsafe_allow_html=True)

tab_cols = st.columns(4)

with tab_cols[0]:
    if st.button("💬 AI 상담", key="tab_chat", use_container_width=True,
                 type="primary" if st.session_state.active_tab == "chat" else "secondary"):
        st.session_state.active_tab = "chat"
        st.rerun()

with tab_cols[1]:
    # 간편 지원 - 구글폼으로 바로 이동 (외부 링크)
    if default_form_url:
        st.link_button("📝 간편지원", default_form_url, use_container_width=True, type="secondary")
    else:
        st.button("📝 간편지원", key="btn_apply_disabled", use_container_width=True, disabled=True)

with tab_cols[2]:
    if st.button("🚇 출근거리", key="tab_distance", use_container_width=True,
                 type="primary" if st.session_state.active_tab == "distance" else "secondary"):
        st.session_state.active_tab = "distance"
        st.rerun()

with tab_cols[3]:
    if st.button("🙋 지원문의", key="tab_contact", use_container_width=True,
                 type="primary" if st.session_state.active_tab == "contact" else "secondary"):
        st.session_state.active_tab = "contact"
        st.rerun()

st.markdown("<br>", unsafe_allow_html=True)
# ============================================
# 탭 1: AI 상담사
# ============================================
if st.session_state.active_tab == "chat":
    
    def build_system_prompt():
        active_jobs_list = get_active_jobs()
        kb = get_knowledge_base()
        
        job_lines = []
        for j in active_jobs_list:
            job_lines.append(
                f"[공고 {j['id']}] {j['title']}\n"
                f"- 근무지: {j.get('location', '')}\n"
                f"- 급여: {j.get('salary', '')}\n"
                f"- 시간: {j.get('work_hours', '')} ({j.get('work_days', '')})\n"
                f"- 교육: {j.get('education_period', '')}\n"
                f"- 특징: {j.get('features', '')}\n"
                f"- 설명: {j.get('description', '')}"
            )
        job_info = "\n\n".join(job_lines)
        
        kb_lines = [f"Q: {k.get('question', '')}\nA: {k.get('answer', '')}" for k in kb]
        kb_info = "\n".join(kb_lines)
        
        tone_guide = {
            'friendly': '말투: 친근하고 따뜻하게. 공감 먼저, 정보 나중. 이모지 자연스럽게.',
            'casual': '말투: 편하고 짧게.',
            'formal': '말투: 정중하고 격식있게.'
        }.get(tone, '친근한 말투')
        
        return (
            f"당신은 윌앤비전 채용팀 AI 상담사 '윌비'입니다.\n"
            f"{tone_guide}\n\n"
            f"[모집 공고]\n{job_info}\n\n"
            f"[FAQ]\n{kb_info}\n\n"
            f"[담당자]\n- {manager_name} / {manager_phone}\n\n"
            f"[규칙]\n"
            f"1. 위 정보 안에서만 답변\n"
            f"2. 답변 끝에 '더 궁금한 점 있으세요? 😊'\n"
            f"3. 지원 의사 보이면 지원서 안내\n"
            f"4. 공고 밖 질문은 담당자 연결 안내\n"
            f"5. 짧고 모바일 친화적으로\n"
            f"6. 개인정보 수집 금지 - '개인정보는 지원서에서 받아요'"
        )
    
    # 챗봇 설정 가져오기
bot_emoji = settings.get('chatbot_emoji', '🤖')
bot_name = settings.get('chatbot_name', '윌비봇')
bot_greeting = settings.get('chatbot_greeting', "궁금한 건 윌비봇에게 물어보세요 ●'◡'●")
bot_sub = settings.get('chatbot_sub_greeting', '24시간 친절하게 답변드려요!')
bot_placeholder = settings.get('chatbot_placeholder', '편하게 질문 주세요... 🙌')
bot_empty = settings.get('chatbot_empty_msg', '💬 대화를 시작해주세요!')
bot_thinking = settings.get('chatbot_thinking_msg', '윌비가 생각 중이에요... 💭')

# 귀여운 인사말 (크게)
st.markdown(f"""
<div style="text-align: center; padding: 0.8rem 0 0.5rem;">
    <div style="font-size: 2rem; margin-bottom: 0.3rem;">{bot_emoji}</div>
    <div style="font-size: 1.05rem; font-weight: 600; color: #4c1d95;">{bot_greeting}</div>
    <div style="font-size: 0.85rem; color: #64748b; margin-top: 0.2rem;">{bot_sub}</div>
</div>
""", unsafe_allow_html=True)

# 추천 질문
if not st.session_state.messages:
    st.markdown("<br>", unsafe_allow_html=True)
    st.caption("🔥 이런 걸 많이 물어봐요")
    sug_col1, sug_col2 = st.columns(2)
    suggested_questions = [
        settings.get('suggested_q_1', '신입도 가능해요?'),
        settings.get('suggested_q_2', '재택 있나요?'),
        settings.get('suggested_q_3', '급여 얼마에요?'),
        settings.get('suggested_q_4', '교육 기간은?'),
    ]
    for idx, q in enumerate(suggested_questions):
        with sug_col1 if idx % 2 == 0 else sug_col2:
            if st.button(q, key=f"sug_{idx}", use_container_width=True):
                st.session_state.preset_question = q
                st.rerun()

# 대화 화면
chat_container = st.container(border=True, height=350)
with chat_container:
    if not st.session_state.messages:
        st.caption(bot_empty)
    for msg in st.session_state.messages:
        avatar = bot_emoji if msg["role"] == "assistant" else None
        with st.chat_message(msg["role"], avatar=avatar):
            st.markdown(msg["content"])

# 메시지 입력
preset = st.session_state.pop("preset_question", None)
user_input = preset or st.chat_input(bot_placeholder)
    
    if user_input:
        st.session_state.messages.append({"role": "user", "content": user_input})
        
        try:
            system_prompt = build_system_prompt()
            chat_history = [{"role": "system", "content": system_prompt}]
            chat_history.extend(st.session_state.messages[-8:])
            
            with st.spinner(bot_thinking):
    response = client.chat.completions.create(
                    model="gpt-4o-mini",
                    messages=chat_history,
                    temperature=0.7,
                    max_tokens=500,
                )
            
            answer = response.choices[0].message.content
            st.session_state.messages.append({"role": "assistant", "content": answer})
            
            needs_human = "담당자" in answer or manager_phone in answer
            save_conversation(
                session_id=st.session_state.session_id,
                question=user_input,
                answer=answer,
                related_job_id=st.session_state.get('preset_job_id'),
                needs_human=needs_human,
            )
            st.rerun()
        except Exception as e:
            st.error(f"오류 발생. {manager_phone}로 문의해주세요.")
            st.caption(f"에러: {str(e)[:100]}")
    
    # 하단 액션
    if st.session_state.messages:
        col1, col2 = st.columns(2)
        with col1:
            if default_form_url:
                st.link_button("📝 지원하기", default_form_url, use_container_width=True, type="primary")
        with col2:
            if st.button("🔄 새 대화", use_container_width=True):
                st.session_state.messages = []
                st.rerun()


# ============================================
# 탭 2: 출근 거리
# ============================================
elif st.session_state.active_tab == "distance":
    st.markdown("#### 🚇 출근 경로 확인")
    st.caption("집 주소 / 역 이름을 입력하세요")
    
    start_address = st.text_input(
        "출발지",
        placeholder="예: 강남역, 서울역, 홍대입구역",
        label_visibility="collapsed",
        key="start_addr"
    )
    
    # 빠른 선택
    quick_cols = st.columns(4)
    quick_stations = ["강남역", "홍대입구역", "서울역", "잠실역"]
    for idx, loc in enumerate(quick_stations):
        with quick_cols[idx]:
            if st.button(loc, key=f"qa_{idx}", use_container_width=True):
                st.session_state['start_addr'] = loc
                st.rerun()
    
    st.markdown("<br>", unsafe_allow_html=True)
    
    # 센터 선택
    centers = get_active_centers()
    if not centers:
        st.warning("등록된 센터가 없어요. 관리자 페이지에서 추가해주세요.")
    else:
        if len(centers) == 1:
            selected_center = centers[0]
            st.info(f"🏢 **{selected_center['name']}** — {selected_center['address']}")
        else:
            c_opts = {c['id']: c['name'] for c in centers}
            sel_id = st.radio(
                "도착지 센터",
                options=list(c_opts.keys()),
                format_func=lambda x: f"🏢 {c_opts[x]}",
                horizontal=True,
                key="dest_center"
            )
            selected_center = next(c for c in centers if c['id'] == sel_id)
        
        # 교통수단 선택
        st.markdown("**🚏 교통수단**")
        t_cols = st.columns(4)
        transport_labels = [
            ("publictransit", "🚇 대중"),
            ("car", "🚗 자동차"),
            ("foot", "🚶 도보"),
            ("bicycle", "🚴 자전거"),
        ]
        sel_transport = st.session_state.get('sel_transport', 'publictransit')
        for idx, (key, label) in enumerate(transport_labels):
            with t_cols[idx]:
                is_active = (key == sel_transport)
                if st.button(label, key=f"tr_{key}", use_container_width=True,
                             type="primary" if is_active else "secondary"):
                    st.session_state['sel_transport'] = key
                    st.rerun()
        
        # 경로 확인
        if start_address:
            st.markdown("<br>", unsafe_allow_html=True)
            start_enc = urllib.parse.quote(start_address)
            end_enc = urllib.parse.quote(selected_center['address'])
            kakao_url = f"https://map.kakao.com/?sName={start_enc}&eName={end_enc}"
            
            naver_map = {
                "publictransit": "transit",
                "car": "car",
                "foot": "walk",
                "bicycle": "bicycle"
            }
            naver_mode = naver_map.get(sel_transport, "transit")
            naver_url = f"https://map.naver.com/p/directions/-/{end_enc}/{naver_mode}"
            
            result_html = (
                '<div style="background: linear-gradient(135deg, #ddd6fe 0%, #c7d2fe 100%); '
                'padding: 1rem; border-radius: 12px; text-align: center; margin: 0.5rem 0;">'
                f'<div style="font-size: 0.85rem; color: #4c1d95;">🏠 {start_address}</div>'
                '<div style="margin: 0.3rem 0;">⬇️</div>'
                f'<div style="font-weight: 600; color: #312e81;">🏢 {selected_center["name"]}</div>'
                '</div>'
            )
            st.markdown(result_html, unsafe_allow_html=True)
            
            col1, col2 = st.columns(2)
            with col1:
                st.link_button("🗺️ 카카오맵", kakao_url, type="primary", use_container_width=True)
            with col2:
                st.link_button("🗺️ 네이버지도", naver_url, use_container_width=True)
            
            st.caption("💡 버튼을 누르면 정확한 예상 시간·거리·비용이 표시됩니다.")
        else:
            st.caption("👆 출발지를 입력하거나 선택해주세요.")


# ============================================
# 탭 3: 지원 문의
# ============================================
elif st.session_state.active_tab == "contact":
    st.markdown("#### 🙋 지원 문의")
    st.caption(f"{manager_name}님께 직접 문의하세요!")
    
    col1, col2 = st.columns(2)
    
    with col1:
        kakao_card = (
            '<div style="background: #fef3c7; padding: 1.2rem; border-radius: 12px; text-align: center;">'
            '<div style="font-size: 2.5rem;">💬</div>'
            '<div style="font-weight: 600; margin-top: 0.3rem;">카카오톡</div>'
            '<div style="font-size: 0.72rem; color: #92400e;">빠른 답변</div>'
            '</div>'
        )
        st.markdown(kakao_card, unsafe_allow_html=True)
        if openchat_url:
            st.link_button("오픈채팅 →", openchat_url, type="primary", use_container_width=True)
        else:
            st.button("준비중", disabled=True, use_container_width=True, key="kakao_disabled")
    
    with col2:
        phone_card = (
            '<div style="background: #dbeafe; padding: 1.2rem; border-radius: 12px; text-align: center;">'
            '<div style="font-size: 2.5rem;">📞</div>'
            '<div style="font-weight: 600; margin-top: 0.3rem;">전화</div>'
            '<div style="font-size: 0.72rem; color: #1e40af;">즉시 상담</div>'
            '</div>'
        )
        st.markdown(phone_card, unsafe_allow_html=True)
        phone_clean = manager_phone.replace('-', '')
        st.link_button(f"{manager_phone}", f"tel:{phone_clean}", use_container_width=True)

# ============================================
# FAQ
# ============================================
faqs = get_faq_items()
if faqs:
    st.markdown('<div class="section-header">💡 자주 묻는 질문</div>', unsafe_allow_html=True)
    for faq in faqs[:5]:
        with st.expander(f"❓ {faq.get('question', '')}"):
            st.write(faq.get('answer', ''))

# ============================================
# 푸터
# ============================================
footer_html = (
    '<div class="footer">'
    '💬 궁금한 점은 AI 상담사가 24시간 답변해드립니다<br>'
    f'📞 {manager_name} · {manager_phone}<br>'
    '<br>'
    '© 윌앤비전 채용팀'
    '</div>'
)
st.markdown(footer_html, unsafe_allow_html=True)
