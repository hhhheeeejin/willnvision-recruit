import streamlit as st
from openai import OpenAI
import uuid
import json
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

if "user_context" not in st.session_state:
    # 지원자 관심사 추적 (대화 맥락)
    st.session_state.user_context = {
        "interested_job_id": None,
        "experience_level": None,  # "신입" / "경력"
        "concerns": [],  # ["재택", "급여", "거리" 등]
        "apply_suggested": False,  # 지원 유도 한 번 했는지
    }

# ============ 설정 ============
settings = get_site_settings()
manager_phone = settings.get('manager_phone', '010-9467-6139')
manager_name = settings.get('manager_name', '담당자')
tone = settings.get('chatbot_tone', 'friendly')
auto_apply_prompt = settings.get('chatbot_auto_apply_prompt', 'true') == 'true'
default_form_url = settings.get('default_google_form_url', '')
openchat_url = settings.get('kakao_openchat_url', '')
office_address = settings.get('office_address', '')

# ============ OpenAI ============
client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])


# ============ 지원자 맥락 분석 (AI로 추출) ============
def analyze_user_intent(user_input, messages_history):
    """지원자 메시지에서 관심사, 경력 등을 AI로 추출"""
    try:
        analysis_prompt = f"""
지원자 메시지에서 다음 정보를 JSON으로 추출해주세요:
- experience_level: "신입" / "경력" / null
- concerns: ["재택", "급여", "거리", "교육", "업무", "시간"] 중 해당하는 것들 (배열)
- interest_signal: 지원 관심도 (0-5점): 0=단순문의, 5=당장지원
- wants_human: 담당자 직접 연결 원하는지 (true/false)

대화 맥락:
{chr(10).join([f"{m['role']}: {m['content'][:100]}" for m in messages_history[-4:]])}

현재 메시지: "{user_input}"

JSON만 반환, 다른 설명 금지:"""

        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": analysis_prompt}],
            temperature=0.2,
            max_tokens=150,
        )
        
        text = response.choices[0].message.content.strip()
        # JSON 마크다운 제거
        if text.startswith("```"):
            text = text.split("```")[1].replace("json", "").strip()
        
        return json.loads(text)
    except Exception:
        return {
            "experience_level": None,
            "concerns": [],
            "interest_signal": 2,
            "wants_human": False
        }


# ============ 시스템 프롬프트 생성 ============
@st.cache_data(ttl=60)
def build_system_prompt(user_context_json=""):
    jobs = get_active_jobs()
    kb = get_knowledge_base()
    
    job_info = "\n\n".join([
        f"""━━━━━━━━━━━━━━━━━━━━
[공고 ID: {j['id']}] {j['title']}
- 카테고리: {j.get('category', '')}
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
    
    tone_guide = {
        'friendly': """💚 말투 가이드 (친근하게):
- "아~ 그 부분이 궁금하셨군요! 😊"
- "좋은 질문이에요! 제가 아는 만큼 알려드릴게요 🙌"
- "오~ 관심 가져주셔서 감사해요!"
- 감탄사, 공감, 이모지 자연스럽게 사용
- 지원자의 걱정에 먼저 공감한 후 정보 제공""",
        'casual': """💛 말투 가이드 (편하게):
- 친구에게 말하듯 가볍고 직관적으로
- "아 그거? OO이에요!"
- "이거 꿀팁인데..."
- 짧고 핵심만""",
        'formal': """🤵 말투 가이드 (격식있게):
- "안내드리겠습니다"
- "~해주시기 바랍니다"
- 존댓말 철저히, 정중하게"""
    }.get(tone, "")
    
    return f"""당신은 윌앤비전 채용팀의 AI 상담사 '윌비'입니다. 
지원자와 따뜻하게 대화하며 회사의 공고를 안내합니다.

{tone_guide}

# 대화 원칙

## 1. 공감 먼저, 정보 나중
지원자의 질문에는 감정이 담겨 있어요. 정보만 던지지 말고 먼저 공감하세요.

❌ 안좋은 예: "재택은 2번 공고만 가능합니다."
✅ 좋은 예: "재택 가능한 곳 찾기 진짜 힘드셨죠? 😢 마침 2번 '부재콜 인바운드'가 재택 가능해요!"

## 2. 상황별 맞춤 답변
- 신입: 교육기간, 지원자격, 필요한 태도 강조
- 경력자: 인센티브 구조, 성장 가능성, 업무 디테일 강조
- 지원자가 드러낸 관심사에 맞춰 강조점 바꾸기

## 3. 자연스러운 지원 유도
지원자가 이런 신호를 보이면 → 자연스럽게 지원 링크 제시:
- "더 알고 싶어요" / "자세히 알려주세요"
- "괜찮네요" / "좋아요"
- 구체적 질문 3개 이상 (이미 관심 높음)
- 조건 확인 중 ("월급이 맞으면...")

지원 유도 문구 예시:
"혹시 관심 있으시면, 1분이면 끝나는 간단 지원서 있어요! [지원하기](링크)
제출하시면 {manager_name}님이 2~3일 내 연락드립니다 😊"

## 4. 질문 역으로 던지기
일방적 답변보다 지원자를 알아가며 맞춤 답변하세요.
"경력 있으신가요, 아니면 이 분야 신입이신가요?"
"거주지가 어디세요? 제가 출근 거리도 알려드릴게요!"

## 5. 개인정보 보호
지원자가 이름/전화번호 알려주려 하면:
"개인정보는 공식 지원서에서 안전하게 받아요! 여기서는 편하게 궁금한 것만 물어봐 주세요 🔒"

# 현재 모집 공고
{job_info}

# 회사 FAQ
{kb_info}

# 담당자 정보
- 이름: {manager_name}
- 전화: {manager_phone}
- 오픈채팅: {openchat_url if openchat_url else '준비 중'}
- 사무실: {office_address}

# 지원자 맥락 (지금까지 파악한 정보)
{user_context_json if user_context_json else '아직 정보 없음 — 대화하며 파악하세요'}

# 답변 형식 규칙
- 3-5줄 이내, 모바일 친화적
- 이모지 자연스럽게 (남발 X)
- 답변 끝: 다음 대화 유도하는 질문
- 공고 밖 질문은: "그건 {manager_phone}로 직접 문의 부탁드려요!"
"""


# ============ 지원 유도 버튼 표시 함수 ============
def show_apply_cta(job_id=None):
    """지원 유도 카드 + 버튼"""
    target_job = None
    if job_id:
        jobs = get_active_jobs()
        target_job = next((j for j in jobs if j['id'] == job_id), None)
    
    job_title = target_job['title'] if target_job else "윌앤비전 채용"
    apply_url = (target_job.get('google_form_url') if target_job else None) or default_form_url
    
    st.markdown(f"""
    <div style="background: linear-gradient(135deg, #fff7ed 0%, #fed7aa 100%); 
                padding: 1.2rem; border-radius: 16px; margin: 1rem 0;
                border-left: 4px solid #ea580c;
                box-shadow: 0 2px 8px rgba(234,88,12,0.1);">
        <div style="font-weight: 700; margin-bottom: 0.5rem; font-size: 1rem;">
            🎯 관심 가져주셔서 감사해요!
        </div>
        <div style="font-size: 0.9rem; color: #475569; line-height: 1.6;">
            <b>{job_title}</b><br>
            1분이면 끝나는 간단 지원서 작성하시겠어요?<br>
            {manager_name}님이 2~3일 내 연락드려요 📞
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    if apply_url:
        st.link_button("📝 지원서 작성하러 가기 →", apply_url, type="primary", use_container_width=True)
    else:
        st.warning("⚠️ 지원서 URL이 설정되지 않았습니다. 관리자 페이지에서 설정해주세요.")


# ============ 담당자 연결 유도 함수 ============
def show_human_handoff():
    """담당자 연결 카드"""
    st.markdown(f"""
    <div style="background: linear-gradient(135deg, #fef3c7 0%, #fde68a 100%); 
                padding: 1.2rem; border-radius: 16px; margin: 1rem 0;
                border-left: 4px solid #d97706;">
        <div style="font-weight: 700; margin-bottom: 0.5rem;">
            🙋 담당자에게 직접 물어보세요!
        </div>
        <div style="font-size: 0.9rem; color: #475569; line-height: 1.6;">
            {manager_name}님이 정확하게 답변드릴 수 있어요.
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    col1, col2 = st.columns(2)
    with col1:
        if openchat_url:
            st.link_button("💬 오픈채팅으로 문의", openchat_url, type="primary", use_container_width=True)
    with col2:
        st.link_button(f"📞 {manager_phone}", f"tel:{manager_phone.replace('-','')}", use_container_width=True)


# ============ 히어로 ============
st.markdown("""
<style>
.chat-hero {
    text-align: center;
    padding: 1rem 0 1.5rem;
}
.chat-hero-icon { font-size: 2.8rem; margin-bottom: 0.25rem; }
.chat-hero-title { font-size: 1.4rem; font-weight: 700; margin: 0.25rem 0; }
.chat-hero-subtitle { font-size: 0.9rem; color: #64748b; }
</style>
<div class="chat-hero">
    <div class="chat-hero-icon">🤖</div>
    <div class="chat-hero-title">AI 채용 상담사 '윌비'</div>
    <div class="chat-hero-subtitle">24시간 친근하게 답변드려요 · 편하게 물어보세요!</div>
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
        "재택도 가능한가요?",
        "교육 기간이 어떻게 돼요?",
        "문래역에서 걸어갈 수 있어요?",
    ]
    for i, q in enumerate(suggested):
        with col1 if i % 2 == 0 else col2:
            if st.button(q, key=f"suggest_{i}", use_container_width=True):
                st.session_state.preset_question = q
                st.rerun()

# ============ 대화 표시 ============
for msg in st.session_state.messages:
    with st.chat_message(msg["role"], avatar="🤖" if msg["role"] == "assistant" else None):
        st.markdown(msg["content"])
        # 특수 카드들 표시
        if msg.get("show_apply"):
            show_apply_cta(msg.get("job_id"))
        if msg.get("show_human"):
            show_human_handoff()

# ============ 입력 처리 ============
preset = st.session_state.pop("preset_question", None)
user_input = preset or st.chat_input("편하게 질문 주세요... 🙌")

if user_input:
    # 사용자 메시지 추가
    st.session_state.messages.append({"role": "user", "content": user_input})
    
    with st.chat_message("user"):
        st.markdown(user_input)
    
    # 🧠 지원자 맥락 분석 (비동기적으로 컨텍스트 업데이트)
    with st.chat_message("assistant", avatar="🤖"):
        with st.spinner("윌비가 생각 중이에요... 💭"):
            try:
                # 1. 지원자 의도 분석
                intent = analyze_user_intent(user_input, st.session_state.messages)
                
                # 2. 컨텍스트 업데이트
                if intent.get("experience_level"):
                    st.session_state.user_context["experience_level"] = intent["experience_level"]
                
                for c in intent.get("concerns", []):
                    if c not in st.session_state.user_context["concerns"]:
                        st.session_state.user_context["concerns"].append(c)
                
                interest_signal = intent.get("interest_signal", 2)
                wants_human = intent.get("wants_human", False)
                
                # 3. 시스템 프롬프트 생성 (맥락 포함)
                context_str = json.dumps(st.session_state.user_context, ensure_ascii=False)
                system_prompt = build_system_prompt(context_str)
                
                # 4. 답변 생성
                history = [{"role": "system", "content": system_prompt}]
                history.extend([
                    {"role": m["role"], "content": m["content"]} 
                    for m in st.session_state.messages[-8:]
                ])
                
                response = client.chat.completions.create(
                    model="gpt-4o-mini",
                    messages=history,
                    temperature=0.75,
                    max_tokens=500,
                )
                
                answer = response.choices[0].message.content
                st.markdown(answer)
                
                # 5. 판단: 지원 유도 표시할지?
                should_show_apply = False
                should_show_human = False
                preset_job_id = st.session_state.get('preset_job_id')
                
                # 관심도 높으면 (4점 이상) 또는 대화 5번 이상 & 아직 유도 안 했으면
                if not st.session_state.user_context["apply_suggested"]:
                    if interest_signal >= 4:
                        should_show_apply = True
                    elif len(st.session_state.messages) >= 10 and auto_apply_prompt:
                        should_show_apply = True
                
                # 담당자 연결이 필요하면
                if wants_human or "담당자" in answer or manager_phone in answer:
                    should_show_human = True
                
                # 카드 표시
                if should_show_apply:
                    show_apply_cta(preset_job_id)
                    st.session_state.user_context["apply_suggested"] = True
                
                if should_show_human:
                    show_human_handoff()
                
                # 메시지 저장 (카드 표시 정보도 함께)
                st.session_state.messages.append({
                    "role": "assistant",
                    "content": answer,
                    "show_apply": should_show_apply,
                    "show_human": should_show_human,
                    "job_id": preset_job_id,
                })
                
                # DB에 저장
                save_conversation(
                    session_id=st.session_state.session_id,
                    question=user_input,
                    answer=answer,
                    related_job_id=preset_job_id,
                    needs_human=should_show_human,
                )
                
            except Exception as e:
                st.error(f"⚠️ 일시적 오류가 발생했어요. {manager_phone}로 직접 문의해주세요.")
                st.caption(f"에러: {str(e)}")

# ============ 하단 액션 ============
st.divider()

col1, col2 = st.columns(2)
with col1:
    if default_form_url:
        st.link_button("📝 간편 지원", default_form_url, use_container_width=True, type="primary")
    if openchat_url:
        st.link_button("💬 담당자 오픈채팅", openchat_url, use_container_width=True)

with col2:
    st.link_button(f"📞 {manager_phone}", f"tel:{manager_phone.replace('-','')}", use_container_width=True)
    if st.button("🔄 새 대화 시작", use_container_width=True):
        st.session_state.messages = []
        st.session_state.user_context = {
            "interested_job_id": None,
            "experience_level": None,
            "concerns": [],
            "apply_suggested": False,
        }
        st.session_state.session_id = str(uuid.uuid4())
        st.rerun()

# ============ 개발자용: 현재 파악된 지원자 맥락 표시 (숨김, 디버그용) ============
# 관리자 페이지에서 확인 가능하므로 여기선 숨김
