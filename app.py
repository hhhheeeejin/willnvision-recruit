import streamlit as st
import uuid
import urllib.parse
import json
from openai import OpenAI
from utils.db import (
    get_active_jobs_with_center, 
    increment_job_view, increment_job_apply, get_site_settings,
    get_active_jobs, get_knowledge_base, save_conversation,
    get_active_centers, get_center_faqs,
    save_commute_search,
)

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
    st.session_state.messages_history = []

# 🚀 강화된 캐싱 (30분)
@st.cache_data(ttl=1800)  # 30분
def load_settings():
    return get_site_settings()

@st.cache_data(ttl=600)   # 10분 (공고는 더 자주 업데이트)
def load_active_jobs_with_center():
    return get_active_jobs_with_center()

@st.cache_data(ttl=1800)  # 30분
def load_active_centers():
    return get_active_centers()

@st.cache_data(ttl=1800)  # 30분
def load_active_jobs():
    return get_active_jobs()

@st.cache_data(ttl=1800)  # 30분
def load_knowledge_base():
    return get_knowledge_base()

@st.cache_data(ttl=1800)  # 30분
def load_center_faqs(center_id):
    return get_center_faqs(center_id)

# 🚀 시스템 프롬프트 캐싱 (30분)
@st.cache_data(ttl=1800)
def build_cached_system_prompt(bot_name, manager_name, manager_phone, tone):
    """시스템 프롬프트를 캐시하여 매번 DB 안 부르게"""
    active_jobs_list = load_active_jobs()
    kb = load_knowledge_base()
    centers_list = load_active_centers()
    
    # 압축된 공고 정보
    job_lines = []
    for j in active_jobs_list:
        job_lines.append(
            f"[{j['title']}] "
            f"{j.get('location', '')} | "
            f"{j.get('salary', '')} | "
            f"{j.get('work_hours', '')} {j.get('work_days', '')} | "
            f"교육 {j.get('education_period', '')} | "
            f"{j.get('features', '')}"
        )
    job_info = "\n".join(job_lines)
    
    # 압축된 FAQ
    kb_info = "\n".join([f"Q:{k.get('question','')} A:{k.get('answer','')}" for k in kb])
    
    # 압축된 센터 정보
    center_info_lines = []
    for c in centers_list:
        ci = f"[{c['name']}] {c.get('address', '')}"
        if c.get('subway_info'):
            ci += f" | {c['subway_info']}"
        if c.get('parking_available'):
            ci += " | 주차O"
        if c.get('info_note'):
            ci += f"\n  정보: {c['info_note'][:200]}"  # 200자로 제한
        
        try:
            c_faqs = load_center_faqs(c['id'])
            if c_faqs:
                for cf in c_faqs[:5]:  # 센터당 5개로 제한
                    ci += f"\n  Q:{cf['question']} A:{cf['answer']}"
        except Exception:
            pass
        
        center_info_lines.append(ci)
    
    centers_text = "\n".join(center_info_lines)
    
    tone_guide = {
        'friendly': '친근하고 따뜻하게',
        'casual': '편하고 짧게',
        'formal': '정중하고 격식있게'
    }.get(tone, '친근하게')
    
    return (
        f"당신은 윌앤비전 채용팀 AI 상담사 '{bot_name}'. {tone_guide}.\n\n"
        f"[공고]\n{job_info}\n\n"
        f"[FAQ]\n{kb_info}\n\n"
        f"[센터]\n{centers_text}\n\n"
        f"[담당자] {manager_name} / {manager_phone}\n\n"
        f"[규칙]\n"
        f"1. 위 정보로만 답변\n"
        f"2. 답변 끝에 '더 궁금한 점 있으세요? 😊'\n"
        f"3. 짧게, 모바일 친화적으로 (3~5줄)\n"
        f"4. 출퇴근 질문은 4가지 교통수단 대략 시간 안내 + '정확한 건 카카오맵·네이버지도, 하단 출근거리 메뉴에서 확인 가능'\n"
        f"5. 개인정보 수집 금지"
    )

# 설정 로드
settings = load_settings()
hero_title = settings.get('hero_title', '윌앤비전 채용팀')
hero_subtitle = settings.get('hero_subtitle', '수시채용 진행중')
hero_emoji = settings.get('hero_emoji', '🤖')
hero_image = settings.get('hero_image_url', '')
manager_name = settings.get('manager_name', '담당자')
manager_phone = settings.get('manager_phone', '010-9467-6139')
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

client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])

# 🎨 단순화된 CSS (그라디언트 최소화, 박스섀도우 줄임)
CUSTOM_CSS = """
<link href="https://cdn.jsdelivr.net/gh/orioncactus/pretendard/dist/web/static/pretendard.css" rel="stylesheet">
<style>
html, body, [class*="css"] {
    font-family: 'Pretendard', -apple-system, BlinkMacSystemFont, system-ui, sans-serif !important;
    letter-spacing: -0.4px;
}

section.main { scroll-behavior: auto !important; }

.block-container {
    padding-top: 0.8rem !important;
    padding-bottom: 2rem !important;
    max-width: 640px !important;
    background: white !important;
}

/* 히어로 - 단색으로 변경 (그라디언트 제거) */
.hero-section {
    text-align: center;
    padding: 1.5rem 1.2rem 1.3rem;
    background: #2563EB;
    border-radius: 18px;
    margin-bottom: 1rem;
    color: white;
}

.hero-emoji { font-size: 2.2rem; margin-bottom: 0.3rem; }

.hero-title {
    font-size: 1.4rem; font-weight: 800; margin: 0.2rem 0;
    color: white; letter-spacing: -1px; line-height: 1.2;
}

.hero-subtitle {
    font-size: 0.85rem; color: white; opacity: 0.9;
    margin: 0.3rem 0; font-weight: 600;
}

.hero-phone {
    display: inline-block; background: rgba(255, 255, 255, 0.2);
    padding: 0.3rem 0.85rem; border-radius: 14px;
    font-size: 0.75rem; font-weight: 600; margin-top: 0.5rem;
}

.section-header {
    font-size: 1rem; font-weight: 800;
    margin: 1.1rem 0 0.5rem; padding-left: 0.6rem;
    color: #1E40AF !important;
    letter-spacing: -0.5px;
    border-left: 4px solid #2563EB;
}

[data-testid="stExpander"] {
    background: white !important;
    border: 1px solid #DBEAFE !important;
    border-radius: 10px !important;
    margin-bottom: 0.4rem !important;
    box-shadow: none !important;
}

[data-testid="stExpander"]:hover {
    border-color: #93C5FD !important;
}

[data-testid="stExpander"] summary {
    padding: 0.6rem 0.9rem !important;
    font-weight: 700 !important;
    color: #1E3A8A !important;
    font-size: 0.92rem !important;
    list-style: none !important;
    cursor: pointer;
    display: flex !important;
    align-items: center;
    justify-content: space-between;
}

[data-testid="stExpander"] summary::-webkit-details-marker { display: none !important; }
[data-testid="stExpander"] summary::marker { display: none !important; }

[data-testid="stExpander"] summary::after {
    content: "▼"; font-size: 0.65rem; color: #4285F4;
    transition: transform 0.2s ease;
    margin-left: 0.5rem;
}

[data-testid="stExpander"][open] summary::after {
    transform: rotate(180deg);
}

[data-testid="stExpander"] summary p {
    color: #1E3A8A !important;
    font-weight: 700 !important;
    margin: 0 !important;
    flex: 1;
}

[data-testid="stExpander"] [data-testid="stMarkdownContainer"] p,
[data-testid="stExpander"] [data-testid="stMarkdownContainer"] li,
[data-testid="stExpander"] [data-testid="stMarkdownContainer"] span {
    color: #1E293B !important;
    line-height: 1.6 !important;
}

[data-testid="stExpander"] img {
    border-radius: 8px !important; margin: 6px 0 !important;
}

/* 🎯 모든 버튼 크기 통일 (그라디언트 제거, 단순화) */
.stButton, .stLinkButton {
    height: 44px !important;
}

.stButton > button,
.stLinkButton > a,
.stLinkButton > a > button {
    border-radius: 10px !important;
    font-weight: 700 !important;
    border: 2px solid transparent !important;
    transition: background 0.15s !important;
    letter-spacing: -0.3px !important;
    padding: 0 0.5rem !important;
    font-size: 0.88rem !important;
    height: 44px !important;
    min-height: 44px !important;
    max-height: 44px !important;
    width: 100% !important;
    white-space: nowrap !important;
    overflow: hidden !important;
    text-overflow: ellipsis !important;
    display: flex !important;
    align-items: center !important;
    justify-content: center !important;
    box-sizing: border-box !important;
    line-height: 1 !important;
}

.stLinkButton > a {
    text-decoration: none !important;
    display: block !important;
}

.stButton > button[kind="primary"],
.stLinkButton > a > button[kind="primary"] {
    background: #2563EB !important;
    color: white !important;
    border: 2px solid #2563EB !important;
}

.stButton > button[kind="primary"]:hover,
.stLinkButton > a > button[kind="primary"]:hover {
    background: #1E40AF !important;
}

.stButton > button[kind="secondary"],
.stLinkButton > a > button[kind="secondary"] {
    background: white !important;
    color: #1E40AF !important;
    border: 2px solid #BFDBFE !important;
}

.stButton > button[kind="secondary"]:hover,
.stLinkButton > a > button[kind="secondary"]:hover {
    background: #EFF6FF !important;
    border-color: #4285F4 !important;
}

.stButton > button > div,
.stLinkButton > a > button > div,
.stButton > button p,
.stLinkButton > a > button p {
    margin: 0 !important;
    padding: 0 !important;
    line-height: 1 !important;
}

.stTextInput > div > div > input,
.stTextArea > div > div > textarea {
    border-radius: 10px !important;
    border: 2px solid #DBEAFE !important;
    background: white !important;
    color: #1E293B !important;
}

.cute-greeting {
    background: #EFF6FF;
    border-radius: 14px;
    padding: 1rem 0.8rem;
    text-align: center;
    margin: 0.4rem 0;
    border: 1px solid #DBEAFE;
}

.cute-greeting-emoji { font-size: 2rem; margin-bottom: 0.2rem; }

.cute-greeting-title {
    font-size: 1rem; font-weight: 800;
    color: #1E40AF !important;
    line-height: 1.4;
}

.cute-greeting-sub {
    font-size: 0.8rem; color: #3B82F6 !important;
    margin-top: 0.2rem; font-weight: 600;
}

[data-testid="stChatMessage"] {
    background: #F8FAFC !important;
    border-radius: 12px !important;
    padding: 0.7rem !important;
}

[data-testid="stChatMessage"] [data-testid="stMarkdownContainer"] p {
    color: #1E293B !important;
    line-height: 1.6 !important;
}

.footer {
    text-align: center;
    padding: 0.8rem 0 0.3rem;
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
    line-height: 1.6 !important;
}

[data-testid="stCaptionContainer"] p,
[data-testid="stCaptionContainer"] {
    color: #475569 !important;
}

@media (max-width: 640px) {
    .hero-emoji { font-size: 2rem; }
    .hero-title { font-size: 1.25rem; }
    .section-header { font-size: 0.95rem; }
    
    .stButton, .stLinkButton {
        height: 42px !important;
    }
    
    .stButton > button,
    .stLinkButton > a,
    .stLinkButton > a > button { 
        font-size: 0.78rem !important; 
        padding: 0 0.4rem !important;
        height: 42px !important;
        min-height: 42px !important;
        max-height: 42px !important;
    }
}

@media (prefers-color-scheme: dark) {
    .stApp { background: white !important; }
    .block-container { background: white !important; }
    [data-testid="stExpander"] { background: white !important; }
    [data-testid="stExpander"] summary,
    [data-testid="stExpander"] summary p { color: #1E3A8A !important; }
    .stMarkdown p, .stMarkdown li,
    [data-testid="stMarkdownContainer"] p,
    [data-testid="stMarkdownContainer"] li,
    [data-testid="stMarkdownContainer"] span { color: #1E293B !important; }
    .section-header { color: #1E40AF !important; }
    .cute-greeting-title { color: #1E40AF !important; }
    .cute-greeting-sub { color: #3B82F6 !important; }
    [data-testid="stCaptionContainer"],
    [data-testid="stCaptionContainer"] p { color: #475569 !important; }
    [data-testid="stChatMessage"] { background: #F8FAFC !important; }
    [data-testid="stChatMessage"] [data-testid="stMarkdownContainer"] p { color: #1E293B !important; }
    .stTextInput > div > div > input,
    .stTextArea > div > div > textarea {
        background: white !important; color: #1E293B !important;
    }
    .stButton > button[kind="secondary"],
    .stLinkButton > a > button[kind="secondary"] {
        background: white !important;
        color: #1E40AF !important;
        border: 2px solid #BFDBFE !important;
    }
    .footer { color: #94A3B8 !important; }
}
</style>
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
st.html('<div class="section-header">모집 중인 공고</div>')

jobs = load_active_jobs_with_center()

if not jobs:
    st.info("현재 모집 중인 공고가 없습니다.")
else:
    for idx, job in enumerate(jobs):
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
                    '<div style="margin-top: 10px; padding: 10px 12px; '
                    'background: #FFF7ED; '
                    'border-radius: 10px; border-left: 3px solid #F97316;">'
                    '<div style="font-size: 0.85rem; font-weight: 700; color: #9A3412; '
                    'display: flex; align-items: center; justify-content: space-between;">'
                    f'<span>📋 {ext_site}에서 자세한 공고 확인하러 가기</span>'
                    '<span>→</span>'
                    '</div></div></a>'
                )
                st.html(EXT_LINK_HTML)
            
            st.markdown("<br>", unsafe_allow_html=True)
            
            col1, col2 = st.columns(2)
            with col1:
                if st.button("이 공고 문의", key=f"chat_{job['id']}", use_container_width=True):
                    st.session_state['preset_question'] = f"{job['title']} 공고에 대해 알려주세요"
                    st.session_state['preset_job_id'] = job['id']
                    st.session_state.active_tab = "chat"
                    st.session_state.from_job_card = True
                    increment_job_view(job['id'], st.session_state.session_id)
                    st.rerun()
            with col2:
                apply_url = job.get('google_form_url') or default_form_url
                if apply_url:
                    if st.button("지원하기", key=f"apply_{job['id']}", use_container_width=True, type="primary"):
                        increment_job_apply(job['id'], st.session_state.session_id)
                        st.markdown(f'<meta http-equiv="refresh" content="0; url={apply_url}">', unsafe_allow_html=True)
                        st.success("지원 페이지로 이동 중...")
                        st.markdown(f"자동 이동 안 되면 [여기 클릭]({apply_url})")
                else:
                    st.button("지원 준비중", key=f"apply_{job['id']}", use_container_width=True, disabled=True)

# 기능 탭
st.html('<div class="section-header">기능 선택</div>')

tab_cols = st.columns(4)

with tab_cols[0]:
    if st.button("AI 상담", key="tab_chat", use_container_width=True,
                 type="primary" if st.session_state.active_tab == "chat" else "secondary"):
        st.session_state.active_tab = "chat"
        st.session_state.from_job_card = False
        st.rerun()

with tab_cols[1]:
    if default_form_url:
        st.link_button("간편지원", default_form_url, use_container_width=True, type="secondary")
    else:
        st.button("간편지원", key="btn_apply_disabled", use_container_width=True, disabled=True)

with tab_cols[2]:
    if st.button("출근거리", key="tab_distance", use_container_width=True,
                 type="primary" if st.session_state.active_tab == "distance" else "secondary"):
        st.session_state.active_tab = "distance"
        st.rerun()

with tab_cols[3]:
    if st.button("지원문의", key="tab_contact", use_container_width=True,
                 type="primary" if st.session_state.active_tab == "contact" else "secondary"):
        st.session_state.active_tab = "contact"
        st.rerun()

st.markdown("<br>", unsafe_allow_html=True)

# ============================================
# 탭 1: AI 상담사
# ============================================
if st.session_state.active_tab == "chat":
    
    if st.session_state.get('from_job_card'):
        if st.button("← 공고 목록으로 돌아가기", use_container_width=True, key="back_to_jobs"):
            st.session_state.from_job_card = False
            st.session_state.messages = []
            st.rerun()
        st.markdown("<br>", unsafe_allow_html=True)
    
    GREETING_HTML = (
        '<div class="cute-greeting">'
        f'<div class="cute-greeting-emoji">{bot_emoji}</div>'
        f'<div class="cute-greeting-title">{bot_greeting}</div>'
        f'<div class="cute-greeting-sub">{bot_sub}</div>'
        '</div>'
    )
    st.html(GREETING_HTML)
    
    if not st.session_state.messages and st.session_state.messages_history:
        col_restore1, col_restore2 = st.columns([3, 2])
        with col_restore1:
            st.caption(f"💬 이전 대화 {len(st.session_state.messages_history)}개")
        with col_restore2:
            if st.button("↶ 이전 대화", use_container_width=True, key="restore_chat"):
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
    
    chat_container = st.container(border=True, height=280)
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
            # 🚀 캐시된 시스템 프롬프트 사용 (DB 안 부름)
            system_prompt = build_cached_system_prompt(bot_name, manager_name, manager_phone, tone)
            chat_history = [{"role": "system", "content": system_prompt}]
            chat_history.extend(st.session_state.messages[-6:])  # 8 → 6 (토큰 절약)
            
            with st.spinner(bot_thinking):
                response = client.chat.completions.create(
                    model="gpt-4o-mini",
                    messages=chat_history,
                    temperature=0.7,
                    max_tokens=400,  # 🚀 600 → 400 (비용 30% 절감)
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
    
    if st.session_state.messages:
        col1, col2, col3 = st.columns(3)
        with col1:
            if st.session_state.messages_history and st.session_state.messages_history != st.session_state.messages:
                if st.button("↶ 이전", use_container_width=True, key="restore_during"):
                    st.session_state.messages = st.session_state.messages_history.copy()
                    st.rerun()
            else:
                st.empty()
        with col2:
            if default_form_url:
                st.link_button("지원하기", default_form_url, use_container_width=True, type="primary")
        with col3:
            if st.button("새 대화", use_container_width=True):
                if st.session_state.messages:
                    st.session_state.messages_history = st.session_state.messages.copy()
                st.session_state.messages = []
                st.rerun()


# ============================================
# 탭 2: 출근 거리
# ============================================
elif st.session_state.active_tab == "distance":
    st.markdown("#### 🚇 출근 경로 확인")
    
    GUIDE_BOX = (
        '<div style="background: #EFF6FF; '
        'padding: 0.8rem 1rem; border-radius: 10px; margin-bottom: 0.8rem; '
        'border: 1px solid #DBEAFE;">'
        '<div style="font-size: 0.8rem; color: #1E40AF; font-weight: 600; line-height: 1.6;">'
        '✨ <b>3단계로 출퇴근 정보 확인</b><br>'
        '1️⃣ 집 주소 입력 → 2️⃣ 도착지 선택 → 3️⃣ 시간 확인 클릭!'
        '</div></div>'
    )
    st.html(GUIDE_BOX)
    
    st.markdown("**출발지 입력**")
    start_address = st.text_input(
        "출발지",
        placeholder="예: 고양시 호수로 336, 강남역",
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
                if 'commute_analysis' in st.session_state:
                    del st.session_state['commute_analysis']
                st.rerun()
    
    st.markdown("<br>", unsafe_allow_html=True)
    
    centers = load_active_centers()
    if not centers:
        st.warning("등록된 센터가 없어요.")
    else:
        st.markdown("**도착지 센터 선택**")
        c_opts = {c['id']: c['name'] for c in centers}
        if len(centers) == 1:
            selected_center = centers[0]
            st.info(f"🏢 **{selected_center['name']}** — {selected_center['address']}")
            sel_id = selected_center['id']
        else:
            prev_sel_id = st.session_state.get('dest_center')
            sel_id = st.radio(
                "도착지 센터",
                options=list(c_opts.keys()),
                format_func=lambda x: f"🏢 {c_opts[x]}",
                key="dest_center",
                label_visibility="collapsed"
            )
            if prev_sel_id != sel_id and 'commute_analysis' in st.session_state:
                del st.session_state['commute_analysis']
            
            selected_center = next(c for c in centers if c['id'] == sel_id)
        
        if start_address:
            st.markdown("<br>", unsafe_allow_html=True)
            
            ROUTE_HEADER = (
                '<div style="background: #EFF6FF; '
                'padding: 0.9rem; border-radius: 10px; text-align: center; '
                'border: 1px solid #DBEAFE; margin-bottom: 10px;">'
                f'<div style="font-size: 0.82rem; color: #1E40AF; font-weight: 600;">🏠 {start_address}</div>'
                '<div style="margin: 0.2rem 0; color: #4285F4;">⬇️</div>'
                f'<div style="font-weight: 700; color: #1E3A8A; font-size: 0.95rem;">🏢 {selected_center["name"]}</div>'
                '</div>'
            )
            st.html(ROUTE_HEADER)
            
            st.markdown("**교통수단 선택**")
            
            sel_transport = st.session_state.get('sel_transport', 'transit')
            
            t_cols = st.columns(4)
            transport_labels = [
                ("car", "자동차"),
                ("transit", "대중교통"),
                ("bicycle", "자전거"),
                ("walk", "도보"),
            ]
            for idx, (key, label) in enumerate(transport_labels):
                with t_cols[idx]:
                    is_active = (key == sel_transport)
                    if st.button(label, key=f"tr_{key}", use_container_width=True,
                                 type="primary" if is_active else "secondary"):
                        st.session_state['sel_transport'] = key
                        st.rerun()
            
            st.markdown("<br>", unsafe_allow_html=True)
            
            if st.button("⏱️ 시간 확인하기", 
                         type="primary", 
                         use_container_width=True, 
                         key="check_time_btn"):
                with st.spinner("분석 중... 🔍"):
                    try:
                        save_commute_search(
                            session_id=st.session_state.session_id,
                            start_address=start_address,
                            center_id=selected_center['id'],
                            center_name=selected_center['name'],
                            transport_type=sel_transport,
                        )
                        
                        # 🚀 짧은 프롬프트로 비용 절감
                        time_prompt = (
                            f"출발: {start_address} → 도착: {selected_center['name']} ({selected_center.get('address', '')})\n"
                            "한국 지리 기반으로 4가지 교통수단 시간 추정.\n"
                            "JSON만 응답:\n"
                            '{"car": "약 X분", "transit": "약 X분", "bicycle": "약 X시간", '
                            '"walk": "약 X시간", "tip": "꿀팁 한 문장(50자)"}'
                        )
                        
                        response = client.chat.completions.create(
                            model="gpt-4o-mini",
                            messages=[
                                {"role": "system", "content": "한국 출퇴근 안내 전문가. JSON만 응답."},
                                {"role": "user", "content": time_prompt}
                            ],
                            temperature=0.5,
                            max_tokens=200,  # 🚀 300 → 200
                            response_format={"type": "json_object"},
                        )
                        
                        st.session_state['commute_analysis'] = response.choices[0].message.content
                        st.rerun()
                        
                    except Exception as e:
                        st.error(f"분석 오류: {e}")
            
            if st.session_state.get('commute_analysis'):
                try:
                    result = json.loads(st.session_state['commute_analysis'])
                    
                    st.markdown("<br>", unsafe_allow_html=True)
                    st.markdown("##### ⏱️ 예상 소요시간")
                    
                    def time_card(key, emoji, label, time_text):
                        is_selected = (key == sel_transport)
                        if is_selected:
                            return (
                                '<div style="background: #2563EB; '
                                'border-radius: 10px; padding: 10px; text-align: center;">'
                                f'<div style="font-size: 1.3rem;">{emoji}</div>'
                                f'<div style="font-size: 0.7rem; color: rgba(255,255,255,0.9); font-weight: 600; margin-top: 2px;">{label}</div>'
                                f'<div style="font-size: 0.95rem; font-weight: 800; color: white; margin-top: 3px;">{time_text}</div>'
                                '</div>'
                            )
                        else:
                            return (
                                '<div style="background: white; border: 2px solid #DBEAFE; '
                                'border-radius: 10px; padding: 10px; text-align: center;">'
                                f'<div style="font-size: 1.3rem;">{emoji}</div>'
                                f'<div style="font-size: 0.7rem; color: #475569; font-weight: 600; margin-top: 2px;">{label}</div>'
                                f'<div style="font-size: 0.95rem; font-weight: 800; color: #2563EB; margin-top: 3px;">{time_text}</div>'
                                '</div>'
                            )
                    
                    TIMES_HTML = (
                        '<div style="display: grid; grid-template-columns: repeat(2, 1fr); gap: 6px; margin-bottom: 10px;">'
                        + time_card("car", "🚗", "자동차", result.get("car", "-"))
                        + time_card("transit", "🚇", "대중교통", result.get("transit", "-"))
                        + time_card("bicycle", "🚴", "자전거", result.get("bicycle", "-"))
                        + time_card("walk", "🚶", "도보", result.get("walk", "-"))
                        + '</div>'
                    )
                    st.html(TIMES_HTML)
                    
                    tip = result.get('tip', '')
                    if tip:
                        TIP_HTML = (
                            '<div style="background: #FEF3C7; '
                            'padding: 9px 12px; border-radius: 10px; '
                            'border-left: 3px solid #F59E0B; margin-bottom: 10px;">'
                            f'<div style="font-size: 0.78rem; color: #78350F; line-height: 1.5;">'
                            f'💡 {tip}</div></div>'
                        )
                        st.html(TIP_HTML)
                    
                    NOTICE_HTML = (
                        '<div style="background: #DCFCE7; '
                        'padding: 8px 11px; border-radius: 10px; '
                        'font-size: 0.72rem; color: #166534; margin-bottom: 10px; line-height: 1.5;">'
                        '✅ 정확한 정보는 카카오맵·네이버지도에서 확인하세요!'
                        '</div>'
                    )
                    st.html(NOTICE_HTML)
                    
                except json.JSONDecodeError:
                    st.error("결과 오류")
            
            start_enc = urllib.parse.quote(start_address)
            end_enc = urllib.parse.quote(selected_center['address'])
            kakao_url = f"https://map.kakao.com/?sName={start_enc}&eName={end_enc}"
            
            naver_modes = {"car": "car", "transit": "transit", "bicycle": "bicycle", "walk": "walk"}
            naver_mode = naver_modes.get(sel_transport, "transit")
            naver_url = f"https://map.naver.com/p/directions/-/{end_enc}/{naver_mode}"
            
            col1, col2 = st.columns(2)
            with col1:
                st.link_button("🗺️ 카카오맵", kakao_url, type="primary", use_container_width=True)
            with col2:
                st.link_button("🗺️ 네이버지도", naver_url, use_container_width=True)
            
            if st.session_state.get('commute_analysis'):
                st.markdown("<br>", unsafe_allow_html=True)
                if st.button("🔄 다시 분석하기", use_container_width=True, key="reanalyze_btn"):
                    del st.session_state['commute_analysis']
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
            '<div style="background: #FEF3C7; '
            'padding: 1.1rem; border-radius: 12px; text-align: center; '
            'border: 1px solid #FCD34D;">'
            '<div style="font-size: 2.2rem;">💬</div>'
            '<div style="font-weight: 700; margin-top: 0.2rem; color: #92400E;">카카오톡</div>'
            '<div style="font-size: 0.72rem; color: #B45309; font-weight: 500;">빠른 답변</div>'
            '</div>'
        )
        st.html(KAKAO_CARD)
        if openchat_url:
            st.link_button("오픈채팅 →", openchat_url, type="primary", use_container_width=True)
        else:
            st.button("준비중", disabled=True, use_container_width=True, key="kakao_disabled")
    
    with col2:
        PHONE_CARD = (
            '<div style="background: #DBEAFE; '
            'padding: 1.1rem; border-radius: 12px; text-align: center; '
            'border: 1px solid #93C5FD;">'
            '<div style="font-size: 2.2rem;">📞</div>'
            '<div style="font-weight: 700; margin-top: 0.2rem; color: #1E40AF;">전화</div>'
            '<div style="font-size: 0.72rem; color: #2563EB; font-weight: 500;">즉시 상담</div>'
            '</div>'
        )
        st.html(PHONE_CARD)
        phone_clean = manager_phone.replace('-', '')
        st.link_button(f"{manager_phone}", f"tel:{phone_clean}", use_container_width=True)

# 채용 안내
notice_text = settings.get('notice_text', '')
if notice_text:
    formatted_notice = notice_text.replace('※ ', '<br>※ ').replace('• ', '<br>• ').strip()
    if formatted_notice.startswith('<br>'):
        formatted_notice = formatted_notice[4:]
    
    NOTICE_HTML = (
        '<div style="background: transparent; border-top: 1px solid #F1F5F9; '
        'padding: 0.7rem 0.4rem 0.2rem; margin: 0.8rem 0 0.2rem; '
        'color: #CBD5E1; font-size: 0.62rem; line-height: 1.5; font-weight: 400;">'
        '<div style="font-weight: 600; font-size: 0.65rem; color: #CBD5E1; margin-bottom: 0.3rem;">'
        '채용 안내</div>'
        f'<div style="color: #CBD5E1;">{formatted_notice}</div>'
        '</div>'
    )
    st.html(NOTICE_HTML)

FOOTER_HTML = (
    '<div class="footer">'
    f'📞 {manager_name} · {manager_phone} · © 윌앤비전 채용팀'
    '</div>'
)
st.html(FOOTER_HTML)
