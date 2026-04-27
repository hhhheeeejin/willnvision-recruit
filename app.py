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

html {
    scroll-behavior: smooth;
}

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
    content: "🎁";
    position: absolute;
    top: 20px;
    right: 20px;
    font-size: 1.5rem;
    opacity: 0.4;
    transform: rotate(15deg);
}

.hero-section::after {
    content: "✨";
    position: absolute;
    bottom: 30px;
    left: 20px;
    font-size: 1.3rem;
    opacity: 0.4;
}

.hero-emoji {
    font-size: 3rem;
    margin-bottom: 0.5rem;
    position: relative;
    z-index: 1;
}

.hero-title {
    font-size: 1.7rem;
    font-weight: 900;
    margin: 0.3rem 0;
    color: white;
    letter-spacing: -1px;
    line-height: 1.2;
    position: relative;
    z-index: 1;
}

.hero-subtitle {
    font-size: 1rem;
    color: white;
    opacity: 0.95;
    margin: 0.4rem 0;
    font-weight: 600;
    position: relative;
    z-index: 1;
}

.hero-phone {
    display: inline-block;
    background: rgba(255, 255, 255, 0.22);
    padding: 0.4rem 1rem;
    border-radius: 20px;
    font-size: 0.82rem;
    font-weight: 600;
    margin-top: 0.7rem;
    position: relative;
    z-index: 1;
}

.section-header {
    font-size: 1.15rem;
    font-weight: 800;
    margin: 1.5rem 0 0.8rem;
    padding-left: 0.6rem;
    color: #1E40AF !important;
    letter-spacing: -0.6px;
    position: relative;
}

.section-header::before {
    content: "";
    position: absolute;
    left: -4px;
    top: 50%;
    transform: translateY(-50%);
    width: 5px;
    height: 22px;
    background: linear-gradient(180deg, #4285F4 0%, #1E40AF 100%);
    border-radius: 5px;
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
    box-shadow: 0 4px 14px rgba(66, 133, 244, 0.15) !important;
}

[data-testid="stExpander"] summary {
    padding: 0.7rem 1rem !important;
    font-weight: 800 !important;
    color: #1E3A8A !important;
    font-size: 0.95rem !important;
    letter-spacing: -0.4px;
    list-style: none !important;
    cursor: pointer;
    position: relative;
    display: flex !important;
    align-items: center;
    justify-content: space-between;
}

[data-testid="stExpander"] summary::-webkit-details-marker {
    display: none !important;
}

[data-testid="stExpander"] summary::marker {
    display: none !important;
}

[data-testid="stExpander"] summary::after {
    content: "▼";
    font-size: 0.7rem;
    color: #4285F4;
    transition: transform 0.25s ease;
    margin-left: 0.5rem;
    display: inline-block;
    flex-shrink: 0;
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
    border-radius: 12px !important;
    margin: 8px 0 !important;
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
    box-shadow: 0 5px 16px rgba(66, 133, 244, 0.4) !important;
}

.stButton > button[kind="secondary"] {
    background: white !important;
    color: #1E40AF !important;
    border: 2px solid #DBEAFE !important;
}

.stButton > button[kind="secondary"]:hover {
    background: #EFF6FF !important;
    border-color: #93C5FD !important;
    color: #1D4ED8 !important;
}

.stLinkButton > a > button {
    border-radius: 14px !important;
    font-weight: 700 !important;
    letter-spacing: -0.4px !important;
}

.stLinkButton > a > button[kind="primary"] {
    background: linear-gradient(135deg, #10B981 0%, #059669 100%) !important;
    color: white !important;
    border: none !important;
    box-shadow: 0 3px 10px rgba(16, 185, 129, 0.3) !important;
}

.stTextInput > div > div > input,
.stTextArea > div > div > textarea {
    border-radius: 14px !important;
    border: 2px solid #DBEAFE !important;
    background: white !important;
    color: #1E293B !important;
    font-weight: 500 !important;
}

.cute-greeting {
    background: linear-gradient(135deg, #EFF6FF 0%, #DBEAFE 100%);
    border-radius: 22px;
    padding: 1.4rem 1rem;
    text-align: center;
    margin: 0.5rem 0;
    border: 2px solid rgba(66, 133, 244, 0.15);
}

.cute-greeting-emoji {
    font-size: 2.5rem;
    margin-bottom: 0.4rem;
}

.cute-greeting-title {
    font-size: 1.1rem;
    font-weight: 800;
    color: #1E40AF !important;
    letter-spacing: -0.5px;
    line-height: 1.4;
}

.cute-greeting-sub {
    font-size: 0.88rem;
    color: #3B82F6 !important;
    margin-top: 0.3rem;
    font-weight: 600;
    line-height: 1.5;
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
    padding: 1.5rem 0 1rem;
    color: #64748B !important;
    font-size: 0.8rem;
    font-weight: 500;
    line-height: 1.7;
}

.stMarkdown p,
.stMarkdown li,
.stMarkdown span,
[data-testid="stMarkdownContainer"] p,
[data-testid="stMarkdownContainer"] li,
[data-testid="stMarkdownContainer"] span {
    color: #1E293B !important;
    line-height: 1.7 !important;
}

[data-testid="stCaptionContainer"] p,
[data-testid="stCaptionContainer"] {
    color: #475569 !important;
    line-height: 1.6 !important;
}

[data-testid="stAlert"] p,
[data-testid="stAlert"] div {
    color: #1E293B !important;
    line-height: 1.7 !important;
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
    [data-testid="stExpander"] summary p {
        color: #1E3A8A !important;
    }
    .stMarkdown p, .stMarkdown li,
    [data-testid="stMarkdownContainer"] p,
    [data-testid="stMarkdownContainer"] li,
    [data-testid="stMarkdownContainer"] span {
        color: #1E293B !important;
    }
    .section-header { color: #1E40AF !important; }
    .cute-greeting-title { color: #1E40AF !important; }
    .cute-greeting-sub { color: #3B82F6 !important; }
    [data-testid="stCaptionContainer"],
    [data-testid="stCaptionContainer"] p {
        color: #475569 !important;
    }
    [data-testid="stChatMessage"] { background: #F8FAFC !important; }
    [data-testid="stChatMessage"] [data-testid="stMarkdownContainer"] p {
        color: #1E293B !important;
    }
    .stTextInput > div > div > input,
    .stTextArea > div > div > textarea {
        background: white !important;
        color: #1E293B !important;
    }
    [data-testid="stAlert"] p, [data-testid="stAlert"] div {
        color: #1E293B !important;
    }
    .footer { color: #64748B !important; }
}
</style>
"""

st.html(CUSTOM_CSS)

# 페이지 최상단 앵커
st.html('<div id="page-top"></div>')

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
                    'cursor: pointer; transition: transform 0.2s; '
                    'box-shadow: 0 2px 6px rgba(249, 115, 22, 0.15);">'
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
            'friendly': '말투: 친근하고 따뜻하게. 공감 먼저, 정보 나중. 이모지 자연스럽게.',
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
            f"3. 센터 관련 질문 → 해당 센터 정보 정확히 답변\n"
            f"4. 지원 의사 보이면 지원서 안내\n"
            f"5. 공고 밖 질문은 담당자 연결 안내\n"
            f"6. 짧고 모바일 친화적으로\n"
            f"7. 개인정보 수집 금지"
        )
    
    GREETING_HTML = (
        '<div class="cute-greeting">'
        f'<div class="cute-greeting-emoji">{bot_emoji}</div>'
        f'<div class="cute-greeting-title">{bot_greeting}</div>'
        f'<div class="cute-greeting-sub">{bot_sub}</div>'
        '</div>'
    )
    st.html(GREETING_HTML)
    
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
    
    chat_container = st.container(border=True, height=300)
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
            
            # 답변 후 페이지 최상단으로 자동 스크롤
            st.html('''
                <script>
                    setTimeout(function() {
                        window.parent.document.querySelector('section.main').scrollTo({top: 0, behavior: 'smooth'});
                    }, 100);
                </script>
            ''')
            
            st.rerun()
        except Exception as e:
            st.error(f"오류 발생. {manager_phone}로 문의해주세요.")
            st.caption(f"에러: {str(e)[:100]}")
    
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
# 탭 2: 출근 거리 (AI 분석)
# ============================================
elif st.session_state.active_tab == "distance":
    st.markdown("#### 🚇 출근 경로 분석")
    
    # 안내 박스
    GUIDE_BOX = (
        '<div style="background: linear-gradient(135deg, #EFF6FF 0%, #DBEAFE 100%); '
        'padding: 0.9rem 1rem; border-radius: 12px; margin-bottom: 1rem; '
        'border: 1px solid rgba(66, 133, 244, 0.15);">'
        '<div style="font-size: 0.82rem; color: #1E40AF; font-weight: 600; line-height: 1.7;">'
        '✨ <b>3단계로 출퇴근 정보 알아보기</b><br>'
        '1️⃣ 집 주소 입력 (또는 빠른 선택)<br>'
        '2️⃣ 도착지 센터 선택<br>'
        '3️⃣ 교통수단 선택 후 <b>분석 버튼 클릭!</b>'
        '</div></div>'
    )
    st.html(GUIDE_BOX)
    
    st.markdown("**🏠 출발지 입력**")
    start_address = st.text_input(
        "출발지",
        placeholder="예: 고양시 호수로 336, 강남역, 서울역",
        label_visibility="collapsed",
        key="start_addr",
        help="주소를 입력하고 엔터를 누르면 자동 저장됩니다"
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
        
        st.markdown("<br>", unsafe_allow_html=True)
        
        # 교통수단 선택
        st.markdown("**🚏 교통수단 선택**")
        st.caption("관심있는 교통수단을 골라주세요")
        
        sel_transport = st.session_state.get('sel_transport', 'car')
        
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
        
        # 분석 버튼
        if start_address:
            if st.button("🤖 AI로 출퇴근 정보 분석하기", type="primary", use_container_width=True, key="analyze_btn"):
                with st.spinner("윌비가 출퇴근 정보 분석 중이에요... 🔍"):
                    try:
                        center_info = (
                            f"센터명: {selected_center['name']}\n"
                            f"주소: {selected_center.get('address', '')}\n"
                            f"지하철: {selected_center.get('subway_info', '')}\n"
                            f"버스: {selected_center.get('bus_info', '')}\n"
                            f"주차: {'가능' if selected_center.get('parking_available') else '확인 필요'}\n"
                        )
                        
                        active_jobs = get_active_jobs()
                        center_jobs = [j for j in active_jobs if j.get('center_id') == sel_id]
                        work_hours_info = ""
                        if center_jobs:
                            work_hours_info = "\n\n[이 센터의 근무 시간]\n"
                            for j in center_jobs:
                                if j.get('work_hours'):
                                    work_hours_info += f"- {j['title']}: {j.get('work_hours', '')}\n"
                        
                        commute_prompt = f"""
당신은 한국 출퇴근 경로 안내 전문가입니다.
4가지 교통수단별 출퇴근 가이드를 작성하세요.

[출발지] {start_address}
[도착지 센터]
{center_info}
{work_hours_info}

[중요: 반드시 아래 JSON 형식으로만 응답하세요]

{{
  "summary": {{
    "car_time": "약 45분",
    "transit_time": "약 1시간 10분",
    "bicycle_time": "약 2시간",
    "walk_time": "약 5시간"
  }},
  "car": {{
    "duration": "약 45분 (교통상황에 따라 다름)",
    "route": "주요 경로 설명",
    "parking": "주차 정보 (긍정적으로)"
  }},
  "transit": {{
    "duration": "약 1시간 10분",
    "departure": "출발지에서 정류장까지 안내",
    "route": "환승 경로 자세히"
  }},
  "bicycle": {{
    "duration": "약 2시간",
    "route": "자전거 경로 또는 한강 자전거도로 활용 안내",
    "note": "긍정적인 참고사항 (운동 효과, 경치 좋은 코스 등)"
  }},
  "walk": {{
    "duration": "약 5시간 30분",
    "route": "도보 경로",
    "note": "긍정적인 안내 (걷기 좋은 구간 등)"
  }},
  "recommended_departure": "출발 권장 시간 안내 (근무시간 정보 없으면 빈 문자열)"
}}

[매우 중요한 규칙]
- "비추천", "어렵다", "힘들다" 같은 부정적인 표현 절대 금지
- 거리가 멀어도 긍정적이고 지지하는 톤으로 작성
- 예: "장거리지만 운동 삼아 도전해보면 색다른 경험!", "한강 자전거도로로 멋진 출근길 가능!", "건강한 라이프스타일에 도움" 등
- 응원하고 지원하는 따뜻한 어투
- 모든 시간은 "약 X분" 또는 "약 X시간 X분" 형식
- JSON 외 다른 텍스트 절대 금지
"""
                        
                        response = client.chat.completions.create(
                            model="gpt-4o-mini",
                            messages=[
                                {"role": "system", "content": "당신은 친절하고 긍정적인 출퇴근 경로 안내 전문가입니다. 항상 응원하는 톤으로 답변하며 JSON으로만 응답합니다."},
                                {"role": "user", "content": commute_prompt}
                            ],
                            temperature=0.6,
                            max_tokens=800,
                            response_format={"type": "json_object"},
                        )
                        
                        ai_answer = response.choices[0].message.content
                        st.session_state['commute_result'] = ai_answer
                        st.session_state['commute_start'] = start_address
                        st.session_state['commute_center'] = selected_center
                        st.rerun()
                        
                    except Exception as e:
                        st.error(f"분석 중 오류가 발생했어요: {e}")
        else:
            st.info("👆 출발지를 먼저 입력해주세요!")
        
        # 결과 표시
        if st.session_state.get('commute_result'):
            try:
                result = json.loads(st.session_state['commute_result'])
                saved_start = st.session_state.get('commute_start', start_address)
                saved_center = st.session_state.get('commute_center', selected_center)
                
                st.markdown("---")
                
                # 출발/도착 카드
                ROUTE_HEADER = (
                    '<div style="background: linear-gradient(135deg, #EFF6FF 0%, #DBEAFE 100%); '
                    'padding: 1rem; border-radius: 14px; text-align: center; '
                    'border: 1px solid rgba(66, 133, 244, 0.15); margin-bottom: 12px;">'
                    f'<div style="font-size: 0.85rem; color: #1E40AF; font-weight: 600;">🏠 {saved_start}</div>'
                    '<div style="margin: 0.3rem 0; color: #4285F4;">⬇️</div>'
                    f'<div style="font-weight: 700; color: #1E3A8A; font-size: 1rem;">🏢 {saved_center["name"]}</div>'
                    '</div>'
                )
                st.html(ROUTE_HEADER)
                
                # 4가지 교통수단 그리드 (요약 - 항상 표시)
                summary = result.get('summary', {})
                
                # 선택된 교통수단 강조
                def grid_item(key, emoji, label, time_text):
                    is_selected = (key == sel_transport)
                    if is_selected:
                        return (
                            '<div style="background: white; border: 2px solid #4285F4; border-radius: 12px; '
                            'padding: 10px 4px; text-align: center; box-shadow: 0 3px 8px rgba(66, 133, 244, 0.2);">'
                            f'<div style="font-size: 1.4rem;">{emoji}</div>'
                            f'<div style="font-size: 0.7rem; color: #1E40AF; font-weight: 700; margin-top: 2px;">{label}</div>'
                            f'<div style="font-size: 0.78rem; font-weight: 800; color: #2563EB; margin-top: 2px;">{time_text}</div>'
                            '</div>'
                        )
                    else:
                        return (
                            '<div style="background: white; border: 2px solid #DBEAFE; border-radius: 12px; '
                            'padding: 10px 4px; text-align: center;">'
                            f'<div style="font-size: 1.4rem;">{emoji}</div>'
                            f'<div style="font-size: 0.7rem; color: #475569; font-weight: 600; margin-top: 2px;">{label}</div>'
                            f'<div style="font-size: 0.78rem; font-weight: 700; color: #475569; margin-top: 2px;">{time_text}</div>'
                            '</div>'
                        )
                
                SUMMARY_HTML = (
                    '<div style="display: grid; grid-template-columns: repeat(4, 1fr); gap: 6px; margin-bottom: 14px;">'
                    + grid_item("car", "🚗", "자동차", summary.get("car_time", "-"))
                    + grid_item("transit", "🚇", "대중교통", summary.get("transit_time", "-"))
                    + grid_item("bicycle", "🚴", "자전거", summary.get("bicycle_time", "-"))
                    + grid_item("walk", "🚶", "도보", summary.get("walk_time", "-"))
                    + '</div>'
                )
                st.html(SUMMARY_HTML)
                
                # 선택된 교통수단만 상세 카드 표시
                if sel_transport == "car":
                    car = result.get('car', {})
                    CAR_CARD = (
                        '<div style="background: white; padding: 14px 16px; border-radius: 14px; '
                        'border: 2px solid #DBEAFE; margin-bottom: 8px; box-shadow: 0 3px 10px rgba(66, 133, 244, 0.1);">'
                        '<div style="display: flex; align-items: center; gap: 8px; margin-bottom: 12px;">'
                        '<span style="font-size: 1.5rem;">🚗</span>'
                        '<span style="font-size: 1.05rem; font-weight: 800; color: #1E3A8A;">자동차로 출근하기</span>'
                        f'<span style="background: #DBEAFE; color: #1E40AF; font-size: 0.72rem; '
                        'padding: 3px 10px; border-radius: 10px; font-weight: 700; margin-left: auto;">'
                        f'{car.get("duration", "")}</span>'
                        '</div>'
                        '<div style="font-size: 0.85rem; color: #475569; line-height: 1.9;">'
                        f'<b style="color: #1E3A8A;">📍 경로:</b><br>{car.get("route", "")}<br><br>'
                        f'<b style="color: #1E3A8A;">🅿️ 주차:</b><br>{car.get("parking", "")}'
                        '</div></div>'
                    )
                    st.html(CAR_CARD)
                
                elif sel_transport == "transit":
                    transit = result.get('transit', {})
                    TRANSIT_CARD = (
                        '<div style="background: white; padding: 14px 16px; border-radius: 14px; '
                        'border: 2px solid #BBF7D0; margin-bottom: 8px; box-shadow: 0 3px 10px rgba(34, 197, 94, 0.1);">'
                        '<div style="display: flex; align-items: center; gap: 8px; margin-bottom: 12px;">'
                        '<span style="font-size: 1.5rem;">🚇</span>'
                        '<span style="font-size: 1.05rem; font-weight: 800; color: #166534;">대중교통으로 출근하기</span>'
                        f'<span style="background: #DCFCE7; color: #166534; font-size: 0.72rem; '
                        'padding: 3px 10px; border-radius: 10px; font-weight: 700; margin-left: auto;">'
                        f'{transit.get("duration", "")}</span>'
                        '</div>'
                        '<div style="font-size: 0.85rem; color: #475569; line-height: 1.9;">'
                        f'<b style="color: #166534;">🚏 출발:</b><br>{transit.get("departure", "")}<br><br>'
                        f'<b style="color: #166534;">🚌 경로:</b><br>{transit.get("route", "")}'
                        '</div></div>'
                    )
                    st.html(TRANSIT_CARD)
                
                elif sel_transport == "bicycle":
                    bicycle = result.get('bicycle', {})
                    BICYCLE_CARD = (
                        '<div style="background: white; padding: 14px 16px; border-radius: 14px; '
                        'border: 2px solid #FCD34D; margin-bottom: 8px; box-shadow: 0 3px 10px rgba(245, 158, 11, 0.1);">'
                        '<div style="display: flex; align-items: center; gap: 8px; margin-bottom: 12px;">'
                        '<span style="font-size: 1.5rem;">🚴</span>'
                        '<span style="font-size: 1.05rem; font-weight: 800; color: #92400E;">자전거로 출근하기</span>'
                        f'<span style="background: #FEF3C7; color: #92400E; font-size: 0.72rem; '
                        'padding: 3px 10px; border-radius: 10px; font-weight: 700; margin-left: auto;">'
                        f'{bicycle.get("duration", "")}</span>'
                        '</div>'
                        '<div style="font-size: 0.85rem; color: #475569; line-height: 1.9;">'
                        f'<b style="color: #92400E;">🚲 경로:</b><br>{bicycle.get("route", "")}<br><br>'
                        f'<b style="color: #92400E;">💡 안내:</b><br>{bicycle.get("note", "")}'
                        '</div></div>'
                    )
                    st.html(BICYCLE_CARD)
                
                elif sel_transport == "walk":
                    walk = result.get('walk', {})
                    WALK_CARD = (
                        '<div style="background: white; padding: 14px 16px; border-radius: 14px; '
                        'border: 2px solid #F9A8D4; margin-bottom: 8px; box-shadow: 0 3px 10px rgba(236, 72, 153, 0.1);">'
                        '<div style="display: flex; align-items: center; gap: 8px; margin-bottom: 12px;">'
                        '<span style="font-size: 1.5rem;">🚶</span>'
                        '<span style="font-size: 1.05rem; font-weight: 800; color: #831843;">도보로 출근하기</span>'
                        f'<span style="background: #FCE7F3; color: #831843; font-size: 0.72rem; '
                        'padding: 3px 10px; border-radius: 10px; font-weight: 700; margin-left: auto;">'
                        f'{walk.get("duration", "")}</span>'
                        '</div>'
                        '<div style="font-size: 0.85rem; color: #475569; line-height: 1.9;">'
                        f'<b style="color: #831843;">👣 경로:</b><br>{walk.get("route", "")}<br><br>'
                        f'<b style="color: #831843;">💡 안내:</b><br>{walk.get("note", "")}'
                        '</div></div>'
                    )
                    st.html(WALK_CARD)
                
                # 권장 출발 시간
                recommended = result.get('recommended_departure', '')
                if recommended:
                    REC_CARD = (
                        '<div style="background: linear-gradient(135deg, #FEF3C7 0%, #FDE68A 100%); '
                        'padding: 14px 16px; border-radius: 14px; '
                        'border: 1px solid rgba(251, 191, 36, 0.3); margin-top: 12px;">'
                        '<div style="font-size: 0.85rem; font-weight: 700; color: #92400E; margin-bottom: 6px;">⏰ 출근 권장 출발 시간</div>'
                        f'<div style="font-size: 0.85rem; color: #78350F; line-height: 1.7;">{recommended}</div>'
                        '</div>'
                    )
                    st.html(REC_CARD)
                
                st.markdown("<br>", unsafe_allow_html=True)
                st.caption("💡 더 정확한 실시간 정보는 네이버 지도에서 확인하세요")
                
                # 네이버지도 링크만
                end_enc = urllib.parse.quote(saved_center['address'])
                naver_modes = {
                    "car": "car",
                    "transit": "transit",
                    "bicycle": "bicycle",
                    "walk": "walk"
                }
                naver_mode = naver_modes.get(sel_transport, "transit")
                naver_url = f"https://map.naver.com/p/directions/-/{end_enc}/{naver_mode}"
                
                st.link_button("🗺️ 네이버지도에서 길찾기", naver_url, use_container_width=True, type="primary")
                
                if st.button("🔄 새로 분석하기", use_container_width=True, key="reanalyze"):
                    del st.session_state['commute_result']
                    st.rerun()
            
            except json.JSONDecodeError:
                st.error("결과를 불러오는 중 오류가 발생했어요. 다시 시도해주세요.")
                if st.button("🔄 다시 시도", use_container_width=True):
                    del st.session_state['commute_result']
                    st.rerun()


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

# FAQ
faqs = get_faq_items()
if faqs:
    st.html('<div class="section-header">💡 자주 묻는 질문</div>')
    for faq in faqs[:5]:
        with st.expander(f"❓ {faq.get('question', '')}"):
            st.write(faq.get('answer', ''))

# 주의사항
notice_text = settings.get('notice_text', '')
if notice_text:
    formatted_notice = notice_text.replace('※ ', '<br>※ ').replace('• ', '<br>• ').strip()
    if formatted_notice.startswith('<br>'):
        formatted_notice = formatted_notice[4:]
    
    NOTICE_HTML = (
        '<div style="background: transparent; border-top: 1px solid #F1F5F9; '
        'padding: 1rem 0.5rem 0.5rem; margin: 1.5rem 0 0.5rem; '
        'color: #94A3B8; font-size: 0.7rem; line-height: 1.7; font-weight: 400;">'
        '<div style="font-weight: 600; font-size: 0.72rem; color: #94A3B8; margin-bottom: 0.5rem;">'
        '채용 안내</div>'
        f'<div style="color: #94A3B8;">{formatted_notice}</div>'
        '</div>'
    )
    st.html(NOTICE_HTML)

# 푸터
FOOTER_HTML = (
    '<div class="footer">'
    '💬 궁금한 점은 AI 상담사가 24시간 답변해드립니다<br>'
    f'📞 {manager_name} · {manager_phone}<br>'
    '<br>'
    '© 윌앤비전 채용팀'
    '</div>'
)
st.html(FOOTER_HTML)
