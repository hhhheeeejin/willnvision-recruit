import streamlit as st
from utils.db import get_site_settings, get_active_jobs

st.set_page_config(page_title="담당자 연결", page_icon="💬", layout="centered")

# ============ 설정 ============
settings = get_site_settings()
manager_name = settings.get('manager_name', '담당자')
manager_phone = settings.get('manager_phone', '010-9467-6139')
openchat_url = settings.get('kakao_openchat_url', '')

# ============ 세션에서 AI 대화 맥락 가져오기 ============
user_context = st.session_state.get('user_context', {})
interested_job_id = user_context.get('interested_job_id')
experience_level = user_context.get('experience_level')
concerns = user_context.get('concerns', [])

# 관심 공고 정보
interested_job_title = None
if interested_job_id:
    jobs = get_active_jobs()
    job = next((j for j in jobs if j['id'] == interested_job_id), None)
    if job:
        interested_job_title = job['title']

# ============ 히어로 ============
st.markdown("""
<style>
.handoff-hero {
    text-align: center;
    padding: 1rem 0 1.5rem;
}
.handoff-icon { font-size: 2.8rem; margin-bottom: 0.25rem; }
.handoff-title { font-size: 1.4rem; font-weight: 700; margin: 0.25rem 0; }
.handoff-sub { font-size: 0.9rem; color: #64748b; }
</style>
<div class="handoff-hero">
    <div class="handoff-icon">🙋</div>
    <div class="handoff-title">담당자와 직접 대화하기</div>
    <div class="handoff-sub">{manager_name}님이 빠르게 답변드려요!</div>
</div>
""".replace("{manager_name}", manager_name), unsafe_allow_html=True)

# ============ 연락 방법 선택 ============
st.markdown("### 📱 편한 방법으로 연락하세요")

col1, col2 = st.columns(2)

with col1:
    st.markdown("""
    <div style="background: #fef3c7; padding: 1rem; border-radius: 12px; text-align: center;">
        <div style="font-size: 2rem;">💬</div>
        <div style="font-weight: 600; margin-top: 0.3rem;">카카오톡</div>
        <div style="font-size: 0.75rem; color: #92400e; margin-top: 0.2rem;">빠른 답변</div>
    </div>
    """, unsafe_allow_html=True)
    if openchat_url:
        st.link_button("오픈채팅 열기 →", openchat_url, type="primary", use_container_width=True)
    else:
        st.button("준비중", disabled=True, use_container_width=True)

with col2:
    st.markdown(f"""
    <div style="background: #dbeafe; padding: 1rem; border-radius: 12px; text-align: center;">
        <div style="font-size: 2rem;">📞</div>
        <div style="font-weight: 600; margin-top: 0.3rem;">전화</div>
        <div style="font-size: 0.75rem; color: #1e40af; margin-top: 0.2rem;">즉시 상담</div>
    </div>
    """, unsafe_allow_html=True)
    st.link_button(f"{manager_phone}", f"tel:{manager_phone.replace('-','')}", use_container_width=True)

# ============ 메시지 템플릿 (AI가 파악한 맥락 활용) ============
st.divider()
st.markdown("### ✉️ 메시지 템플릿")
st.caption("아래 템플릿을 복사해서 보내시면 빠른 답변을 받을 수 있어요!")

# 맥락 기반 메시지 자동 생성
template_parts = [f"안녕하세요, {manager_name}님!"]

if interested_job_title:
    template_parts.append(f"\n'{interested_job_title}' 공고에 대해 문의드립니다.")

if experience_level:
    if experience_level == "신입":
        template_parts.append(f"저는 이 분야 신입입니다.")
    elif experience_level == "경력":
        template_parts.append(f"저는 이 분야 경력자입니다.")

if concerns:
    concern_text = ", ".join(concerns)
    template_parts.append(f"특히 {concern_text} 관련해서 더 자세히 알고 싶습니다.")

template_parts.append("\n편하실 때 연락 부탁드립니다. 감사합니다!")

default_template = "\n".join(template_parts)

# 템플릿 종류 선택
template_type = st.radio(
    "어떤 문의이신가요?",
    ["맞춤 템플릿 (AI 대화 기반)", "지원 문의", "조건 상세 문의", "면접 일정 문의", "기타 문의"],
    horizontal=False,
)

templates = {
    "맞춤 템플릿 (AI 대화 기반)": default_template,
    "지원 문의": f"""안녕하세요, {manager_name}님!
윌앤비전 채용 공고 보고 연락드립니다.

{'[' + interested_job_title + '] ' if interested_job_title else ''}공고에 관심이 있어서, 
지원 절차 및 자격 요건을 자세히 여쭤보고 싶습니다.

답변 부탁드립니다. 감사합니다!""",
    
    "조건 상세 문의": f"""안녕하세요, {manager_name}님!

{'[' + interested_job_title + '] ' if interested_job_title else ''}공고 관련해서 
몇 가지 자세한 조건을 여쭤보고 싶어요.

- 급여 (기본급 외 추가 수당)
- 근무 환경
- 복리후생

시간 되실 때 답변 부탁드립니다!""",
    
    "면접 일정 문의": f"""안녕하세요, {manager_name}님!

{'[' + interested_job_title + '] ' if interested_job_title else ''}공고 지원을 검토 중인데,
면접 일정이 어떻게 되는지 여쭤보고 싶습니다.

제 가능 시간과 맞춰서 조율 가능할까요?
답변 부탁드립니다!""",
    
    "기타 문의": f"""안녕하세요, {manager_name}님!

윌앤비전 채용에 대해 문의드립니다.
(여기에 질문을 적어주세요)

답변 부탁드립니다. 감사합니다!"""
}

selected_template = templates[template_type]

# 템플릿 표시 + 복사
st.text_area(
    "📋 복사해서 쓰실 메시지",
    value=selected_template,
    height=200,
    help="텍스트 박스 내용을 복사(Ctrl+C)해서 카톡이나 문자로 보내주세요.",
)

# 복사 버튼 (JavaScript)
st.markdown(f"""
<div style="text-align: center; margin: 0.5rem 0;">
    <button onclick="navigator.clipboard.writeText(`{selected_template.replace('`', "\\`")}`); 
                     this.innerText='✅ 복사됨!'; 
                     setTimeout(() => this.innerText='📋 메시지 복사하기', 2000);"
            style="background: #6366f1; color: white; border: none; 
                   padding: 0.5rem 1.5rem; border-radius: 8px; cursor: pointer;
                   font-size: 0.9rem; font-weight: 500;">
        📋 메시지 복사하기
    </button>
</div>
""", unsafe_allow_html=True)

# ============ 빠른 질문 버튼 ============
st.divider()
st.markdown("### ⚡ 빠른 질문")
st.caption("자주 묻는 질문은 AI 상담사에게 물어보는 게 더 빨라요!")

quick_questions = [
    ("💰 급여 궁금해요", "급여가 어떻게 되나요?"),
    ("🏠 재택 가능한가요?", "재택근무 가능한 공고 있나요?"),
    ("📅 언제 시작해요?", "언제부터 근무 시작하나요?"),
    ("🎓 신입도 돼요?", "신입도 지원 가능한가요?"),
]

col1, col2 = st.columns(2)
for i, (label, question) in enumerate(quick_questions):
    with col1 if i % 2 == 0 else col2:
        if st.button(label, key=f"quick_q_{i}", use_container_width=True):
            st.session_state['preset_question'] = question
            st.switch_page("pages/1_AI_상담사.py")

# ============ 안내 ============
st.divider()

st.info(f"""
📌 **담당자 응답 시간**  
- 카카오톡 오픈채팅: 평일 09:00-18:00 (평균 30분 내)  
- 전화: 평일 09:00-18:00 즉시 응대  
- 주말/공휴일은 다음 영업일에 회신드립니다.
""")
