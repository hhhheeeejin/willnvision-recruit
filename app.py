import streamlit as st
import uuid
import urllib.parse
import json
from openai import OpenAI
from utils.db import (
    get_active_jobs_with_center, get_faq_items, 
    increment_job_view, increment_job_apply, get_site_settings,
    get_active_jobs, get_knowledge_base, save_conversation,
    get_active_centers, get_center_faqs,
)

# 페이지 설정
st.set_page_config(
    page_title="윌앤비전 채용",
    page_icon="📞",
    layout="centered",
    initial_sidebar_state="collapsed",
)

# 세션 초기화
if "session_id" not in st.session_state:
    st.session_state.session_id = str(uuid.uuid4())
if "messages" not in st.session_state:
    st.session_state.messages = []
if "active_tab" not in st.session_state:
    st.session_state.active_tab = "chat"
if "from_job_card" not in st.session_state:
    st.session_state.from_job_card = False
if "messages_history" not in st.session_state:
    st.session_state.messages_history = []  # 이전 대화 백업용

# 사이트 설정
settings = get_site_settings()
hero_title = settings.get('hero_title', '윌앤비전 채용팀')
hero_subtitle = settings.get('hero_subtitle', '수시채용 진행중')
hero_emoji = settings.get('hero_emoji', '🤖')
hero_image = settings.get('hero_image_url', '')
manager_name = settings.get('manager_name', '담당자')
manager_phone = settings.get('manager_phone', '010-9467-6139')
office_address = settings.get('office_address', '')
default_form_url = settings.get('default_google_form_url', '')
openchat_url = settings.get('kakao_openchat_url', '')
tone = settings.get('chatbot_tone', 'friendly')

bot_emoji = settings.get('chatbot_emoji', '🤖')
bot_name = settings.get('chatbot_name', '윌비봇')
bot_greeting = settings.get('chatbot_greeting', "궁금한 건 윌비봇에게 물어보세요")
bot_sub = settings.get('chatbot_sub_greeting', '24시간 친절하게 답변드려요!')
bot_placeholder = settings.get('chatbot_placeholder', '편하게 질문 주세요...')
bot_empty = settings.get('chatbot_empty_msg', '대화를 시작해주세요!')
bot_thinking = settings.get('chatbot_thinking_msg', '윌비가 생각 중이에요...')

# OpenAI
client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])

# CSS
CUSTOM_CSS = """
<link href="https://cdn.jsdelivr.net/gh/orioncactus/pretendard/dist/web/variable/pretendardvariable.css" rel="stylesheet">
<style>
html, body, [class*="css"] {
    font-family: 'Pretendard Variable', 'Pretendard', -apple-system, BlinkMacSystemFont, system-ui, sans-serif !important;
    letter-spacing: -0.4px;
}

html { scroll-behavior: smooth; }

.block-container {
    padding-top: 1rem !important;
    padding-bottom: 3rem !important;
    max-width: 640px !important;
    background: white !important;
}

.hero-section {
    text-align: center;
    padding: 2.2rem 1.2rem 2rem;
    background: linear-gradient(160deg, #4285F4 0%, #2563EB 100%);
    border-radius: 28px;
    margin-bottom: 1.3rem;
    color: white;
    box-shadow: 0 8px 28px rgba(66, 133, 244, 0.3);
    position: relative;
    overflow: hidden;
}

.hero-section::before {
    content: "🎁"; position: absolute; top: 20px; right: 20px;
    font-size: 1.5rem; opacity: 0.4; transform: rotate(15deg);
}

.hero-section::after {
    content: "✨"; position: absolute; bottom: 30px; left: 20px;
    font-size: 1.3rem; opacity: 0.4;
}

.hero-emoji { font-size: 3rem; margin-bottom: 0.5rem; position: relative; z-index: 1; }

.hero-title {
    font-size: 1.7rem; font-weight: 900; margin: 0.3rem 0;
    color: white; letter-spacing: -1px; line-height: 1.2;
    position: relative; z-index: 1;
}

.hero-subtitle {
    font-size: 1rem; color: white; opacity: 0.95;
    margin: 0.4rem 0; font-weight: 600;
    position: relative; z-index: 1;
}

.hero-phone {
    display: inline-block; background: rgba(255, 255, 255, 0.22);
    padding: 0.4rem 1rem; border-radius: 20px;
    font-size: 0.82rem; font-weight: 600; margin-top: 0.7rem;
    position: relative; z-index: 1;
}

.section-header {
    font-size: 1.15rem; font-weight: 800;
    margin: 1.5rem 0 0.8rem; padding-left: 0.6rem;
    color: #1E40AF !important;
    letter-spacing: -0.6px; position: relative;
}

.section-header::before {
    content: ""; position: absolute; left: -4px; top: 50%;
    transform: translateY(-50%);
    width: 5px; height: 22px;
    background: linear-gradient(180deg, #4285F4 0%, #1E40AF 100%);
    border-radius: 5px;
}

.compact-header {
    font-size: 0.85rem; font-weight: 700;
    margin: 1.2rem 0 0.4rem;
    color: #94A3B8 !important;
}

[data-testid="stExpander"] {
    background: white !important;
    border: 2px solid #DBEAFE !important;
    border-radius: 14px !important;
    margin-bottom: 0.5rem !important;
    box-shadow: 0 2px 8px rgba(66, 133, 244, 0.06) !important;
    transition: all 0.2s;
}

[data-testid="stExpander"]:hover {
    transform: translateY(-1px);
    border-color: #93C5FD !important;
}

[data-testid="stExpander"] summary {
    padding: 0.7rem 1rem !important;
    font-weight: 800 !important;
    color: #1E3A8A !important;
    font-size: 0.95rem !important;
    list-style: none !important;
    cursor: pointer; position: relative;
    display: flex !important;
    align-items: center;
    justify-content: space-between;
}

[data-testid="stExpander"] summary::-webkit-details-marker { display: none !important; }
[data-testid="stExpander"] summary::marker { display: none !important; }

[data-testid="stExpander"] summary::after {
    content: "▼"; font-size: 0.7rem; color: #4285F4;
    transition: transform 0.25s ease;
    margin-left: 0.5rem; display: inline-block; flex-shrink: 0;
}

[data-testid="stExpander"][open] summary::after {
    transform: rotate(180deg);
}

[data-testid="stExpander"] summary p {
    color: #1E3A8A !important;
    font-weight: 800 !important;
    margin: 0 !important;
    flex: 1;
}

[data-testid="stExpander"] [data-testid="stMarkdownContainer"] p,
[data-testid="stExpander"] [data-testid="stMarkdownContainer"] li,
[data-testid="stExpander"] [data-testid="stMarkdownContainer"] span {
    color: #1E293B !important;
    line-height: 1.7 !important;
}

[data-testid="stExpander"] img {
    border-radius: 12px !important; margin: 8px 0 !important;
}

.compact-faq [data-testid="stExpander"] {
    border: 1px solid #E2E8F0 !important;
    box-shadow: none !important;
    margin-bottom: 0.3rem !important;
}

.compact-faq [data-testid="stExpander"] summary {
    padding: 0.5rem 0.8rem !important;
    font-size: 0.82rem !important;
    color: #64748B !important;
}

.compact-faq [data-testid="stExpander"] summary p {
    color: #64748B !important;
    font-weight: 600 !important;
}

.stButton > button {
    border-radius: 14px !important;
    font-weight: 700 !important;
    border: 2px solid transparent !important;
    transition: all 0.2s !important;
    letter-spacing: -0.4px !important;
    padding: 0.55rem 1rem !important;
}

.stButton > button[kind="primary"] {
    background: linear-gradient(135deg, #4285F4 0%, #2563EB 100%) !important;
    color: white !important;
    box-shadow: 0 3px 10px rgba(66, 133, 244, 0.3) !important;
}

.stButton > button[kind="primary"]:hover {
    background: linear-gradient(135deg, #2563EB 0%, #1E40AF 100%) !important;
    transform: translateY(-2px);
}

.stButton > button[kind="secondary"] {
    background: white !important;
    color: #1E40AF !important;
    border: 2px solid #DBEAFE !important;
}

.stButton > button[kind="secondary"]:hover {
    background: #EFF6FF !important;
    border-color: #93C5FD !important;
}

.stLinkButton > a > button {
    border-radius: 14px !important;
    font-weight: 700 !important;
}

.stLinkButton > a > button[kind="primary"] {
    background: linear-gradient(135deg, #10B981 0%, #059669 100%) !important;
    color: white !important;
    border: none !important;
}

.stTextInput > div > div > input,
.stTextArea > div > div > textarea {
    border-radius: 14px !important;
    border: 2px solid #DBEAFE !important;
    background: white !important;
    color: #1E293B !important;
}

.cute-greeting {
    background: linear-gradient(135deg, #EFF6FF 0%, #DBEAFE 100%);
    border-radius: 22px;
    padding: 1.4rem 1rem;
    text-align: center;
    margin: 0.5rem 0;
    border: 2px solid rgba(66, 133, 244, 0.15);
}

.cute-greeting-emoji { font-size: 2.5rem; margin-bottom: 0.4rem; }

.cute-greeting-title {
    font-size: 1.1rem; font-weight: 800;
    color: #1E40AF !important;
    letter-spacing: -0.5px; line-height: 1.4;
}

.cute-greeting-sub {
    font-size: 0.88rem; color: #3B82F6 !important;
    margin-top: 0.3rem; font-weight: 600;
}

[data-testid="stChatMessage"] {
    background: #F8FAFC !important;
    border-radius: 16px !important;
    padding: 0.8rem !important;
}

[data-testid="stChatMessage"] [data-testid="stMarkdownContainer"] p {
    color: #1E293B !important;
    line-height: 1.7 !important;
}

.footer {
    text-align: center;
    padding: 1rem 0 0.5rem;
    color: #94A3B8 !important;
    font-size: 0.7rem;
    font-weight: 400;
    line-height: 1.6;
}

.stMarkdown p, .stMarkdown li, .stMarkdown span,
[data-testid="stMarkdownContainer"] p,
[data-testid="stMarkdownContainer"] li,
[data-testid="stMarkdownContainer"] span {
    color: #1E293B !important;
    line-height: 1.7 !important;
}

[data-testid="stCaptionContainer"] p,
[data-testid="stCaptionContainer"] {
    color: #475569 !important;
}

@media (max-width: 640px) {
    .hero-emoji { font-size: 2.6rem; }
    .hero-title { font-size: 1.5rem; }
    .section-header { font-size: 1.05rem; }
}

@media (prefers-color-scheme: dark) {
    .stApp { background: white !important; }
    .block-container { background: white !important; }
    [data-testid="stExpander"] { background: white !important; }
    [data-testid="stExpander"] summary,
    [data-testid="stExpander"] summary p { color: #1E3A8A !important; }
    .compact-faq [data-testid="stExpander"] summary,
    .compact-faq [data-testid="stExpander"] summary p { color: #64748B !important; }
    .stMarkdown p, .stMarkdown li,
    [data-testid="stMarkdownContainer"] p,
    [data-testid="stMarkdownContainer"] li,
    [data-testid="stMarkdownContainer"] span { color: #1E293B !important; }
    .section-header { color: #1E40AF !important; }
    .compact-header { color: #94A3B8 !important; }
    .cute-greeting-title { color: #1E40AF !important; }
    .cute-greeting-sub { color: #3B82F6 !important; }
    [data-testid="stCaptionContainer"],
    [data-testid="stCaptionContainer"] p { color: #475569 !important; }
    [data-testid="stChatMessage"] { background: #F8FAFC !important; }
    [data-testid="stChatMessage"] [data-testid="stMarkdownContainer"] p { color: #1E293B !important; }
    .stTextInput > div > div > input,
    .stTextArea > div > div > textarea { background: white !important; color: #1E293B !important; }
    .footer { color: #94A3B8 !important; }
}
</style>

<script>
window.addEventListener('load', function() {
    setTimeout(function() {
        const main = window.parent.document.querySelector('section.main');
        if (main) main.scrollTo({top: 0, behavior: 'auto'});
    }, 50);
});
</script>
"""

st.html(CUSTOM_CSS)

# 히어로
if hero_image:
    st.image(hero_image, use_container_width=True)

HERO_HTML = (
    '<div class="hero-section">'
    f'<div class="hero-emoji">{hero_emoji}</div>'
    f'<div class="hero-title">{hero_title}</div>'
    f'<div class="hero-subtitle">{hero_subtitle}</div>'
    f'<div class="hero-phone">📞 {manager_name} · {manager_phone}</div>'
    '</div>'
)
st.html(HERO_HTML)

# 모집 공고
st.html('<div class="section-header">📌 모집 중인 공고</div>')

jobs = get_active_jobs_with_center()

if not jobs:
    st.info("현재 모집 중인 공고가 없습니다.")
else:
    for job in jobs:
        status_emoji = "🟢" if job['status'] == '모집중' else ("🟡" if job['status'] == '재오픈예정' else "⚫")
        
        with st.expander(f"{status_emoji} **{job['title']}**", expanded=False):
            if job.get('image_url'):
                st.image(job['image_url'], use_container_width=True)
                st.markdown("<br>", unsafe_allow_html=True)
            
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
            
            if job.get('description'):
                st.markdown("---")
                st.caption(job['description'])
            
            ext_url = job.get('external_url')
            ext_site = job.get('external_site_name') or '외부 사이트'
            if ext_url:
                EXT_LINK_HTML = (
                    f'<a href="{ext_url}" target="_blank" style="text-decoration: none;">'
                    '<div style="margin-top: 12px; padding: 12px 14px; '
                    'background: linear-gradient(135deg, #FFF7ED 0%, #FED7AA 100%); '
                    'border-radius: 12px; border-left: 4px solid #F97316; '
                    'cursor: pointer;">'
                    '<div style="font-size: 0.88rem; font-weight: 700; color: #9A3412; '
                    'display: flex; align-items: center; justify-content: space-between;">'
                    f'<span>📋 {ext_site}에서 자세한 공고 확인하러 가기</span>'
                    '<span style="font-size: 1rem;">→</span>'
                    '</div></div></a>'
                )
                st.html(EXT_LINK_HTML)
            
            st.markdown("<br>", unsafe_allow_html=True)
            
            col1, col2 = st.columns(2)
            with col1:
                if st.button("💬 이 공고 문의", key=f"chat_{job['id']}", use_container_width=True):
                    st.session_state['preset_question'] = f"{job['title']} 공고에 대해 알려주세요"
                    st.session_state['preset_job_id'] = job['id']
                    st.session_state.active_tab = "chat"
                    st.session_state.from_job_card = True  # 공고에서 진입 표시
                    increment_job_view(job['id'], st.session_state.session_id)
                    st.rerun()
            with col2:
                apply_url = job.get('google_form_url') or default_form_url
                if apply_url:
                    if st.button("📝 지원하기", key=f"apply_{job['id']}", use_container_width=True, type="primary"):
                        increment_job_apply(job['id'], st.session_state.session_id)
                        st.markdown(f'<meta http-equiv="refresh" content="0; url={apply_url}">', unsafe_allow_html=True)
                        st.success("지원 페이지로 이동 중...")
                        st.markdown(f"자동 이동 안 되면 [여기 클릭]({apply_url})")
                else:
                    st.button("📝 지원 준비중", key=f"apply_{job['id']}", use_container_width=True, disabled=True)

# 기능 탭
st.html('<div class="section-header">⚡ 기능 선택</div>')

tab_cols = st.columns(4)

with tab_cols[0]:
    if st.button("💬 AI 상담", key="tab_chat", use_container_width=True,
                 type="primary" if st.session_state.active_tab == "chat" else "secondary"):
        st.session_state.active_tab = "chat"
        st.session_state.from_job_card = False  # 직접 클릭은 공고에서 온 것 아님
        st.rerun()

with tab_cols[1]:
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
    
    # 🔙 시나리오 1: 공고에서 진입했을 때 뒤로가기 버튼
    if st.session_state.get('from_job_card'):
        if st.button("← 공고 목록으로 돌아가기", use_container_width=True, key="back_to_jobs"):
            st.session_state.from_job_card = False
            st.session_state.messages = []
            # 페이지 최상단으로 스크롤하면서 공고 섹션으로
            st.html('<script>window.parent.document.querySelector("section.main").scrollTo({top: 0, behavior: "smooth"});</script>')
            st.rerun()
        st.markdown("<br>", unsafe_allow_html=True)
    
    def build_system_prompt():
        active_jobs_list = get_active_jobs()
        kb = get_knowledge_base()
        centers_list = get_active_centers()
        
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
        
        center_info_lines = []
        for c in centers_list:
            ci = f"\n━━━━━ [{c['name']}] ━━━━━\n"
            ci += f"주소: {c.get('address', '')}\n"
            if c.get('detail_address'):
                ci += f"상세: {c['detail_address']}\n"
            if c.get('subway_info'):
                ci += f"지하철: {c['subway_info']}\n"
            if c.get('bus_info'):
                ci += f"버스: {c['bus_info']}\n"
            if c.get('parking_available'):
                ci += "주차: 가능\n"
            if c.get('info_note'):
                ci += f"\n[센터 고유 정보]\n{c['info_note']}\n"
            
            try:
                c_faqs = get_center_faqs(c['id'])
                if c_faqs:
                    ci += f"\n[{c['name']} 자주 묻는 질문]\n"
                    for cf in c_faqs:
                        ci += f"Q: {cf['question']}\nA: {cf['answer']}\n"
            except Exception:
                pass
            
            center_info_lines.append(ci)
        
        centers_text = "\n".join(center_info_lines)
        
        tone_guide = {
            'friendly': '말투: 친근하고 따뜻하게.',
            'casual': '말투: 편하고 짧게.',
            'formal': '말투: 정중하고 격식있게.'
        }.get(tone, '친근한 말투')
        
        return (
            f"당신은 윌앤비전 채용팀 AI 상담사 '{bot_name}'입니다.\n"
            f"{tone_guide}\n\n"
            f"[모집 공고]\n{job_info}\n\n"
            f"[공통 FAQ]\n{kb_info}\n\n"
            f"[센터 정보]\n{centers_text}\n\n"
            f"[담당자]\n- {manager_name} / {manager_phone}\n\n"
            f"[규칙]\n"
            f"1. 위 정보 안에서만 답변\n"
            f"2. 답변 끝에 '더 궁금한 점 있으세요? 😊'\n"
            f"3. 짧고 모바일 친화적으로\n"
            f"4. 개인정보 수집 금지"
        )
    
    GREETING_HTML = (
        '<div class="cute-greeting">'
        f'<div class="cute-greeting-emoji">{bot_emoji}</div>'
        f'<div class="cute-greeting-title">{bot_greeting}</div>'
        f'<div class="cute-greeting-sub">{bot_sub}</div>'
        '</div>'
    )
    st.html(GREETING_HTML)
    
    # 🔙 시나리오 3: 새 대화 후 이전 대화 복원 가능 표시
    if not st.session_state.messages and st.session_state.messages_history:
        col_restore1, col_restore2 = st.columns([3, 2])
        with col_restore1:
            st.caption(f"💬 이전 대화 {len(st.session_state.messages_history)}개 메시지가 있어요")
        with col_restore2:
            if st.button("↶ 이전 대화 보기", use_container_width=True, key="restore_chat"):
                st.session_state.messages = st.session_state.messages_history.copy()
                st.rerun()
    
    if not st.session_state.messages:
        st.markdown("<br>", unsafe_allow_html=True)
        st.caption("🔥 이런 걸 많이 물어봐요")
        sug_col1, sug_col2 = st.columns(2)
        suggested_questions = [
            settings.get('suggested_q_1', '신입도 가능해요?'),
            settings.get('suggested_q_2', '나에게 맞는 채용은?'),
            settings.get('suggested_q_3', '급여 얼마에요?'),
            settings.get('suggested_q_4', '교육 기간은?'),
        ]
        for idx, q in enumerate(suggested_questions):
            with sug_col1 if idx % 2 == 0 else sug_col2:
                if st.button(q, key=f"sug_{idx}", use_container_width=True):
                    st.session_state.preset_question = q
                    st.rerun()
    
    chat_container = st.container(border=True, height=350)
    with chat_container:
        if not st.session_state.messages:
            st.caption(bot_empty)
        for msg in st.session_state.messages:
            avatar = bot_emoji if msg["role"] == "assistant" else None
            with st.chat_message(msg["role"], avatar=avatar):
                st.markdown(msg["content"])
    
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
    
    # 🔙 대화 중 버튼: 이전 대화 / 지원 / 새 대화
    if st.session_state.messages:
        col1, col2, col3 = st.columns(3)
        
        with col1:
            # 이전 대화 백업이 있으면 복원 버튼
            if st.session_state.messages_history and st.session_state.messages_history != st.session_state.messages:
                if st.button("↶ 이전 대화", use_container_width=True, key="restore_during"):
                    st.session_state.messages = st.session_state.messages_history.copy()
                    st.rerun()
            else:
                st.empty()
        
        with col2:
            if default_form_url:
                st.link_button("📝 지원하기", default_form_url, use_container_width=True, type="primary")
        
        with col3:
            if st.button("🔄 새 대화", use_container_width=True):
                # 새 대화 시작 전 현재 대화 백업
                if st.session_state.messages:
                    st.session_state.messages_history = st.session_state.messages.copy()
                st.session_state.messages = []
                st.rerun()


# ============================================
# 탭 2: 출근 거리 (실제 지도 임베드)
# ============================================
elif st.session_state.active_tab == "distance":
    st.markdown("#### 🚇 출근 경로 확인")
    
    GUIDE_BOX = (
        '<div style="background: linear-gradient(135deg, #EFF6FF 0%, #DBEAFE 100%); '
        'padding: 0.9rem 1rem; border-radius: 12px; margin-bottom: 1rem; '
        'border: 1px solid rgba(66, 133, 244, 0.15);">'
        '<div style="font-size: 0.82rem; color: #1E40AF; font-weight: 600; line-height: 1.7;">'
        '✨ <b>3단계로 정확한 출퇴근 정보 확인하기</b><br>'
        '1️⃣ 집 주소 입력 (또는 빠른 선택)<br>'
        '2️⃣ 도착지 센터 선택<br>'
        '3️⃣ 길찾기 버튼 클릭 → 카카오맵/네이버지도에서 정확한 시간 확인!'
        '</div></div>'
    )
    st.html(GUIDE_BOX)
    
    st.markdown("**🏠 출발지 입력**")
    start_address = st.text_input(
        "출발지",
        placeholder="예: 고양시 호수로 336, 강남역, 서울역",
        label_visibility="collapsed",
        key="start_addr",
    )
    
    st.caption("👇 자주 찾는 출발지")
    quick_cols = st.columns(4)
    quick_stations = ["강남역", "홍대입구역", "서울역", "잠실역"]
    for idx, loc in enumerate(quick_stations):
        with quick_cols[idx]:
            if st.button(loc, key=f"qa_{idx}", use_container_width=True):
                st.session_state['start_addr'] = loc
                st.rerun()
    
    st.markdown("<br>", unsafe_allow_html=True)
    
    centers = get_active_centers()
    if not centers:
        st.warning("등록된 센터가 없어요. 관리자 페이지에서 추가해주세요.")
    else:
        st.markdown("**🏢 도착지 센터 선택**")
        c_opts = {c['id']: c['name'] for c in centers}
        if len(centers) == 1:
            selected_center = centers[0]
            st.info(f"🏢 **{selected_center['name']}** — {selected_center['address']}")
            sel_id = selected_center['id']
        else:
            sel_id = st.radio(
                "도착지 센터",
                options=list(c_opts.keys()),
                format_func=lambda x: f"🏢 {c_opts[x]}",
                key="dest_center",
                label_visibility="collapsed"
            )
            selected_center = next(c for c in centers if c['id'] == sel_id)
        
        if start_address:
            st.markdown("<br>", unsafe_allow_html=True)
            
            ROUTE_HEADER = (
                '<div style="background: linear-gradient(135deg, #EFF6FF 0%, #DBEAFE 100%); '
                'padding: 1rem; border-radius: 14px; text-align: center; '
                'border: 1px solid rgba(66, 133, 244, 0.15); margin-bottom: 12px;">'
                f'<div style="font-size: 0.85rem; color: #1E40AF; font-weight: 600;">🏠 {start_address}</div>'
                '<div style="margin: 0.3rem 0; color: #4285F4;">⬇️</div>'
                f'<div style="font-weight: 700; color: #1E3A8A; font-size: 1rem;">🏢 {selected_center["name"]}</div>'
                '</div>'
            )
            st.html(ROUTE_HEADER)
            
            st.markdown("**🚏 교통수단 선택**")
            
            sel_transport = st.session_state.get('sel_transport', 'transit')
            
            t_cols = st.columns(4)
            transport_labels = [
                ("car", "🚗 자동차"),
                ("transit", "🚇 대중교통"),
                ("bicycle", "🚴 자전거"),
                ("walk", "🚶 도보"),
            ]
            for idx, (key, label) in enumerate(transport_labels):
                with t_cols[idx]:
                    is_active = (key == sel_transport)
                    if st.button(label, key=f"tr_{key}", use_container_width=True,
                                 type="primary" if is_active else "secondary"):
                        st.session_state['sel_transport'] = key
                        st.rerun()
            
            st.markdown("<br>", unsafe_allow_html=True)
            
            start_enc = urllib.parse.quote(start_address)
            end_enc = urllib.parse.quote(selected_center['address'])
            
            kakao_url = f"https://map.kakao.com/?sName={start_enc}&eName={end_enc}"
            
            naver_modes = {
                "car": "car",
                "transit": "transit",
                "bicycle": "bicycle",
                "walk": "walk"
            }
            naver_mode = naver_modes.get(sel_transport, "transit")
            naver_url = f"https://map.naver.com/p/directions/-/{end_enc}/{naver_mode}"
            
            BIG_BUTTON_INFO = (
                '<div style="background: linear-gradient(135deg, #DCFCE7 0%, #BBF7D0 100%); '
                'padding: 14px 16px; border-radius: 14px; '
                'border: 1px solid rgba(34, 197, 94, 0.3); margin-bottom: 12px;">'
                '<div style="font-size: 0.85rem; font-weight: 700; color: #166534; margin-bottom: 4px;">'
                '🗺️ 정확한 길찾기 결과 확인'
                '</div>'
                '<div style="font-size: 0.78rem; color: #166534; line-height: 1.6;">'
                '아래 버튼을 누르면 실시간 교통상황이 반영된 정확한 시간·거리·경로를 확인할 수 있어요!'
                '</div></div>'
            )
            st.html(BIG_BUTTON_INFO)
            
            col1, col2 = st.columns(2)
            with col1:
                st.link_button("🗺️ 카카오맵 길찾기", kakao_url, type="primary", use_container_width=True)
            with col2:
                st.link_button("🗺️ 네이버지도 길찾기", naver_url, use_container_width=True)
            
            st.markdown("<br>", unsafe_allow_html=True)
            
            st.markdown("---")
            st.markdown("##### 🤖 AI에게 추가 정보 물어보기")
            st.caption("주차·환승·꿀팁 등 실용 정보를 AI가 알려드려요")
            
            transport_kr_map = {"car": "자동차", "transit": "대중교통", "bicycle": "자전거", "walk": "도보"}
            transport_kr = transport_kr_map.get(sel_transport, "교통수단")
            
            if st.button(f"💡 {transport_kr} 출퇴근 꿀팁 보기", 
                         use_container_width=True, key="ask_ai_tip"):
                with st.spinner("AI가 꿀팁을 정리 중이에요... 🔍"):
                    try:
                        center_info = (
                            f"센터명: {selected_center['name']}\n"
                            f"주소: {selected_center.get('address', '')}\n"
                            f"지하철: {selected_center.get('subway_info', '')}\n"
                            f"버스: {selected_center.get('bus_info', '')}\n"
                            f"주차: {'가능' if selected_center.get('parking_available') else '확인 필요'}\n"
                        )
                        
                        tip_prompt = f"""
출발지: {start_address}
도착지: {selected_center['name']}
센터 정보:
{center_info}
선택 교통수단: {transport_kr}

위 정보 기반으로 이 교통수단으로 출퇴근할 때의 꿀팁을 정리해주세요.
정확한 시간이나 거리는 언급하지 마세요.

[작성 형식]
🎯 {transport_kr} 출퇴근 꿀팁

✨ 추천 포인트
- (장점/매력 포인트 2-3가지, 긍정적으로)

💡 실용 팁
- (주차/환승/준비물 등 실용 정보)

⚠️ 알아두면 좋은 점
- (러시아워 회피, 날씨 영향 등)

[규칙]
- 정확한 시간이나 거리 언급 절대 금지
- 긍정적이고 응원하는 톤
- 짧고 핵심만
- 마크다운 사용
"""
                        
                        response = client.chat.completions.create(
                            model="gpt-4o-mini",
                            messages=[
                                {"role": "system", "content": "당신은 친근한 출퇴근 꿀팁 전문가입니다."},
                                {"role": "user", "content": tip_prompt}
                            ],
                            temperature=0.6,
                            max_tokens=400,
                        )
                        
                        st.session_state['commute_tip'] = response.choices[0].message.content
                        st.rerun()
                        
                    except Exception as e:
                        st.error(f"오류: {e}")
            
            if st.session_state.get('commute_tip'):
                st.markdown(st.session_state['commute_tip'])
                
                if st.button("🔄 다시 보기", use_container_width=True, key="reset_tip"):
                    del st.session_state['commute_tip']
                    st.rerun()
        else:
            st.info("👆 출발지를 먼저 입력해주세요!")


# ============================================
# 탭 3: 지원 문의
# ============================================
elif st.session_state.active_tab == "contact":
    st.markdown("#### 🙋 지원 문의")
    st.caption(f"{manager_name}님께 직접 문의하세요!")
    
    col1, col2 = st.columns(2)
    
    with col1:
        KAKAO_CARD = (
            '<div style="background: linear-gradient(135deg, #FEF3C7 0%, #FDE68A 100%); '
            'padding: 1.3rem; border-radius: 16px; text-align: center; '
            'border: 2px solid rgba(251, 191, 36, 0.3);">'
            '<div style="font-size: 2.5rem;">💬</div>'
            '<div style="font-weight: 700; margin-top: 0.3rem; color: #92400E;">카카오톡</div>'
            '<div style="font-size: 0.75rem; color: #B45309; font-weight: 500;">빠른 답변</div>'
            '</div>'
        )
        st.html(KAKAO_CARD)
        if openchat_url:
            st.link_button("오픈채팅 →", openchat_url, type="primary", use_container_width=True)
        else:
            st.button("준비중", disabled=True, use_container_width=True, key="kakao_disabled")
    
    with col2:
        PHONE_CARD = (
            '<div style="background: linear-gradient(135deg, #DBEAFE 0%, #BFDBFE 100%); '
            'padding: 1.3rem; border-radius: 16px; text-align: center; '
            'border: 2px solid rgba(66, 133, 244, 0.2);">'
            '<div style="font-size: 2.5rem;">📞</div>'
            '<div style="font-weight: 700; margin-top: 0.3rem; color: #1E40AF;">전화</div>'
            '<div style="font-size: 0.75rem; color: #2563EB; font-weight: 500;">즉시 상담</div>'
            '</div>'
        )
        st.html(PHONE_CARD)
        phone_clean = manager_phone.replace('-', '')
        st.link_button(f"{manager_phone}", f"tel:{phone_clean}", use_container_width=True)

# 컴팩트 FAQ
faqs = get_faq_items()
if faqs:
    st.html('<div class="compact-header">💡 자주 묻는 질문</div>')
    st.html('<div class="compact-faq">')
    for faq in faqs[:3]:
        with st.expander(f"❓ {faq.get('question', '')}"):
            st.caption(faq.get('answer', ''))
    st.html('</div>')

# 채용 안내 (작고 연하게)
notice_text = settings.get('notice_text', '')
if notice_text:
    formatted_notice = notice_text.replace('※ ', '<br>※ ').replace('• ', '<br>• ').strip()
    if formatted_notice.startswith('<br>'):
        formatted_notice = formatted_notice[4:]
    
    NOTICE_HTML = (
        '<div style="background: transparent; border-top: 1px solid #F1F5F9; '
        'padding: 0.8rem 0.5rem 0.3rem; margin: 1rem 0 0.3rem; '
        'color: #CBD5E1; font-size: 0.62rem; line-height: 1.5; font-weight: 400;">'
        '<div style="font-weight: 600; font-size: 0.65rem; color: #CBD5E1; margin-bottom: 0.3rem;">'
        '채용 안내</div>'
        f'<div style="color: #CBD5E1;">{formatted_notice}</div>'
        '</div>'
    )
    st.html(NOTICE_HTML)

# 푸터
FOOTER_HTML = (
    '<div class="footer">'
    f'📞 {manager_name} · {manager_phone} · © 윌앤비전 채용팀'
    '</div>'
)
st.html(FOOTER_HTML)
