import streamlit as st
from openai import OpenAI
import uuid
from utils.db import get_active_jobs, get_knowledge_base, save_conversation

st.set_page_config(page_title="AI 채용 상담사", page_icon="💬", layout="centered")

if "session_id" not in st.session_state:
    st.session_state.session_id = str(uuid.uuid4())

if "messages" not in st.session_state:
    st.session_state.messages = []

client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])


@st.cache_data(ttl=60)
def build_system_prompt():
    jobs = get_active_jobs()
    kb = get_knowledge_base()
    
    job_info = "\n\n".join([
        f"""[공고 ID: {j['id']}] {j['title']}
- 근무지: {j['location']}
- 급여: {j['salary']}
- 시간: {j['work_hours']} ({j['work_days']})
- 교육: {j['education_period']}
- 특징: {j['features']}
- 설명: {j['description']}"""
        for j in jobs
    ])
    
    kb_info = "\n".join([f"Q: {k['question']}\nA: {k['answer']}" for k in kb])
    
    return f"""당신은 윌앤비전 채용팀의 친절한 채용 상담 AI입니다.
지원자에게 따뜻하고 정중한 한국어로 답변하세요.

[현재 모집 중인 공고]
{job_info}

[회사 관련 정보]
{kb_info}

[답변 규칙]
1. 위 정보 안에서만 답변할 것
2. 답변 끝에 "더 궁금한 점 있으세요? 😊" 붙이기
3. 모르는 정보는 "담당자에게 010-9467-6139로 문의 부탁드립니다 🙇‍♀️"
4. 지원 의사를 보이면 "왼쪽 메뉴의 📝 간편지원을 이용해주세요!" 안내
5. 답변은 짧고 모바일에서 보기 편하게
6. 두 공고 비교 요청시 표로 정리

[금지]
- 위 정보에 없는 내용 추측 금지
- 면접 일정/급여 협상 등 개인적인 사항 답변 금지 → 담당자 안내"""


st.title("💬 윌앤비전 채용 AI 상담사")
st.caption("궁금한 점을 자유롭게 물어보세요. 24시간 답변해드립니다.")

if not st.session_state.messages:
    st.markdown("##### 자주 묻는 질문")
    col1, col2 = st.columns(2)
    suggested = [
        "신입도 지원 가능한가요?",
        "두 공고 차이가 뭐예요?",
        "급여가 어떻게 되나요?",
        "교육 기간은 어떻게 되나요?",
    ]
    for i, q in enumerate(suggested):
        with col1 if i % 2 == 0 else col2:
            if st.button(q, key=f"suggest_{i}", use_container_width=True):
                st.session_state.preset_question = q
                st.rerun()

for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

preset = st.session_state.pop("preset_question", None)
user_input = preset or st.chat_input("질문을 입력하세요...")

if user_input:
    st.session_state.messages.append({"role": "user", "content": user_input})
    with st.chat_message("user"):
        st.markdown(user_input)
    
    with st.chat_message("assistant"):
        with st.spinner("답변 작성 중..."):
            try:
                system_prompt = build_system_prompt()
                
                history = [{"role": "system", "content": system_prompt}]
                history.extend(st.session_state.messages[-6:])
                
                response = client.chat.completions.create(
                    model="gpt-4o-mini",
                    messages=history,
                    temperature=0.5,
                    max_tokens=500,
                )
                
                answer = response.choices[0].message.content
                st.markdown(answer)
                
                st.session_state.messages.append({"role": "assistant", "content": answer})
                
                needs_human = "담당자" in answer or "010-9467" in answer
                save_conversation(
                    session_id=st.session_state.session_id,
                    question=user_input,
                    answer=answer,
                    needs_human=needs_human,
                )
                
            except Exception as e:
                error_msg = f"오류가 발생했습니다. 담당자(010-9467-6139)에게 직접 문의해주세요."
                st.error(error_msg)
                st.caption(f"에러: {str(e)}")

st.divider()
col1, col2 = st.columns(2)
with col1:
    if st.button("📝 간편 지원하기", use_container_width=True, type="primary"):
        st.switch_page("pages/2_간편지원.py")
with col2:
    if st.button("🔄 새 대화 시작", use_container_width=True):
        st.session_state.messages = []
        st.session_state.session_id = str(uuid.uuid4())
        st.rerun()
