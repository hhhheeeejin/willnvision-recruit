import streamlit as st
from openai import OpenAI
import uuid
from utils.db import (
    get_active_jobs, get_knowledge_base, save_conversation,
    get_setting, get_site_settings
)

st.set_page_config(page_title="AI 채용 상담사", page_icon="💬", layout="centered")

# ============ 세션 ============
if "session_id" not in st.session_state:
    st.session_state.session_id = str(uuid.uuid4())

if "messages" not in st.session_state:
    st.session_state.messages = []

if "message_count" not in st.session_state:
    st.session_state.message_count = 0

# ============ 설정 ============
settings = get_site_settings()
manager_phone = settings.get('manager_phone', '010-9467-6139')
tone = settings.get('chatbot_tone', 'friendly')
auto_apply_prompt = settings.get('chatbot_auto_apply_prompt', 'true') == 'true'
default_form_url = settings.get('default_google_form_url', '')
openchat_url = settings.get('kakao_openchat_url', '')

# ============ OpenAI ============
client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])

# ============ 프롬프트 생성 ============
@st.cache_data(ttl=60)
def build_system_prompt():
    jobs = get_active_jobs()
    kb = get_knowledge_base()
    
    job_info = "\n\n".join([
        f"""[공고 ID: {j['id']}] {j['title']}
- 근무지: {j.get('location', '')}
- 급여: {j.get('salary', '')}
- 시간: {j.get('work_hours', '')} ({j.get('work_days', '')})
- 교육: {j.get('education_period', '')}
- 특징: {j.get('features', '')}
- 지하철: {j.get('subway_line', '')} {j.get('subway_station', '')}
- 설명: {j.get('description', '')}"""
        for j in jobs
    ])
    
    kb_info = "\n".join([f"Q: {k.get('question', '')}\nA: {k.get('answer', '')}" for k in kb])
    
    tone_instruction = {
        'friendly': """말투: 친근하고 따뜻하게. 이모지 적절히 사용. 
예: "와~ 좋은 질문이에요! 😊", "아이고, 그 부분이 궁금하셨군요!", "제가 아는 만큼 알려드릴게요 🙌" """,
        'casual': """말투: 편하고 친구같이. 짧고 직관적으로.""",
        'formal': """말투: 정중하고 격식있게. 존댓말 철저히."""
    }.get(tone, "친근한 말투")
    
    return f"""당신은 윌앤비전 채용팀의 AI 상담사 '윌비'입니다.
지원자들에게 한국어로 답변하며, 채용 공고 정보를 정확하게 전달합니다.

{tone_instruction}

[현재 모집 중인 공고]
{job_info}

[회사 관련 정보]
{kb_info}

[담당자 연락처]
- 전화: {manager_phone}
- 카카오 오픈채팅: {openchat_url if openchat_url else '(준비 중)'}

[답변 규칙]
1. 위 공고 정보 범위 안에서만 답변할 것
2. 지원자의 감정에 공감하며 답변 (예: "재택 가능한 곳 찾기 힘드셨죠?")
3. 답변은 짧고 모바일에서 보기 편하게 (3-5줄 이내)
4. 이모지를 자연스럽게 사용
5. 답변 끝에 다음 질문을 유도: "또 궁금한 점 있으세요? 😊"
6. 두 개 이상 공고 비교할 때는 표로 정리
7. 지원자가 이름/전화번호/개인정보를 말하려고 하면: 
   "개인정보는 공식 지원서에서 안전하게 접수됩니다! 여기서는 자유롭게 궁금한 점만 물어봐 주세요 🔒"

[금지]
- 공고 정보에 없는 내용 추측하지 않기
- 면접 일정/급여 협상/개인 처우 등 개인적 사항 답변 금지 → "{manager_phone}로 직접 문의 부탁드려요"
- 지원자의 개인정보(이름, 연락처 등)를 받거나 저장하지 않기"""


# ============ 히어로 ============
st.markdown("""
<style>
.chat-hero {
    text-align: center;
    padding: 1rem 0 1.5rem;
}
.chat-hero-icon { font-size: 2.5rem; margin-bottom: 0.25rem; }
.chat-hero-title { font-size: 1.3rem; font-weight: 700; margin: 0.25rem 0; }
.chat-hero-subtitle { font-size: 0.9rem; color: #64748b; }
</style>
<div class="chat-hero">
    <div class="chat-hero-icon">💬</div>
    <div class="chat-hero-title">AI 채용 상담사 '윌비'</div>
    <div class="chat-hero-subtitle">24시간 언제든 편하게 물어보세요!</div>
</div>
""", unsafe_allow_html=True)

# ============ 추천 질문 (처음 진입 시) ============
if not st.session_state.messages:
    st.markdown("##### 🔍 이런 걸 물어볼 수 있어요")
    col1, col2 = st.columns(2)
    suggested = [
        "신입도 지원 가능해요?",
        "두 공고 차이가 뭐예요?",
        "급여가 어떻게 되나요?",
        "교육은 얼마나 해요?",
        "재택도 가능한가요?",
        "문래역에서 가까운가요?",
    ]
    for i, q in enumerate(suggested):
        with col1 if i % 2 == 0 else col2:
            if st.button(q, key=f"suggest_{i}", use_container_width=True):
                st.session_state.preset_question = q
                st.rerun()

# ============ 대화 표시 ============
for msg in st.session_state.messages:
    with st.chat_message(msg["role"], avatar="🤖" i
