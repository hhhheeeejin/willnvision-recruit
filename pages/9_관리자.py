import streamlit as st
import pandas as pd
from datetime import datetime
from io import BytesIO
from utils.db import (
    get_all_jobs, get_all_conversations, get_all_applicants,
    update_job_status, update_applicant_status
)

st.set_page_config(page_title="관리자", page_icon="🔐", layout="wide")


def check_password():
    def password_entered():
        if st.session_state["password"] == st.secrets["ADMIN_PASSWORD"]:
            st.session_state["authenticated"] = True
            del st.session_state["password"]
        else:
            st.session_state["authenticated"] = False

    if "authenticated" not in st.session_state:
        st.session_state["authenticated"] = False

    if not st.session_state["authenticated"]:
        st.title("🔐 관리자 로그인")
        st.text_input("비밀번호", type="password", on_change=password_entered, key="password")
        if "password" in st.session_state:
            st.error("비밀번호가 올바르지 않습니다.")
        st.stop()


check_password()

st.title("🔐 윌앤비전 채용 관리자")
st.caption(f"마지막 업데이트: {datetime.now().strftime('%Y-%m-%d %H:%M')}")

tab1, tab2, tab3 = st.tabs(["📋 공고 관리", "👥 지원자 명단", "💬 대화 기록"])

with tab1:
    st.subheader("공고 목록")
    jobs = get_all_jobs()
    
    if jobs:
        for job in jobs:
            with st.container(border=True):
                col1, col2, col3 = st.columns([4, 2, 1])
                with col1:
                    st.markdown(f"**{job['title']}**")
                    st.caption(f"{job['location']} · {job['salary']} · {job['work_hours']}")
                with col2:
                    new_status = st.selectbox(
                        "상태",
                        options=["모집중", "마감", "재오픈예정"],
                        index=["모집중", "마감", "재오픈예정"].index(job['status']),
                        key=f"status_{job['id']}",
                        label_visibility="collapsed",
                    )
                with col3:
                    if st.button("저장", key=f"save_{job['id']}"):
                        update_job_status(job['id'], new_status)
                        st.success("저장됨!")
                        st.rerun()

with tab2:
    st.subheader("지원자 명단")
    applicants = get_all_applicants()
    
    if applicants:
        df = pd.DataFrame([{
            "지원일": a['created_at'][:10],
            "이름": a['name'],
            "연락처": a['phone'],
            "지원공고": a['job_title_snapshot'],
            "경력": a['experience'],
            "상태": a['status'],
            "자기소개": a['introduction'] or "",
            "메모": a['memo'] or "",
        } for a in applicants])
        
        st.dataframe(df, use_container_width=True, hide_index=True)
        
        output = BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            df.to_excel(writer, index=False, sheet_name='지원자명단')
        
        st.download_button(
            "📥 엑셀 다운로드",
            data=output.getvalue(),
            file_name=f"applicants_{datetime.now().strftime('%Y%m%d')}.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            type="primary",
        )
        
        st.divider()
        st.subheader("지원자 상태 변경")
        selected_id = st.selectbox(
            "지원자 선택",
            options=[a['id'] for a in applicants],
            format_func=lambda x: next(f"{a['name']} ({a['phone']}) - {a['job_title_snapshot']}" 
                                       for a in applicants if a['id'] == x),
        )
        col1, col2 = st.columns([1, 3])
        with col1:
            new_status = st.selectbox("상태", ["신규", "연락완료", "면접예정", "합격", "불합격", "보류"])
        with col2:
            memo = st.text_input("메모", placeholder="예: 4/30 면접 예정")
        if st.button("상태 업데이트"):
            update_applicant_status(selected_id, new_status, memo)
            st.success("업데이트 완료!")
            st.rerun()
    else:
        st.info("아직 지원자가 없습니다.")

with tab3:
    st.subheader("AI 챗봇 대화 기록")
    conversations = get_all_conversations()
    
    if conversations:
        total = len(conversations)
        needs_human = sum(1 for c in conversations if c['needs_human'])
        unique_sessions = len(set(c['session_id'] for c in conversations))
        
        col1, col2, col3 = st.columns(3)
        col1.metric("총 대화 수", f"{total:,}")
        col2.metric("순 방문자 수", f"{unique_sessions:,}")
        col3.metric("담당자 연결 필요", f"{needs_human:,}")
        
        st.divider()
        
        df = pd.DataFrame([{
            "시간": c['created_at'][:19].replace('T', ' '),
            "세션": c['session_id'][:8],
            "질문": c['user_question'],
            "답변": c['ai_answer'],
            "관련공고": c['jobs']['title'] if c.get('jobs') else "",
            "담당자필요": "✅" if c['needs_human'] else "",
        } for c in conversations])
        
        st.dataframe(df, use_container_width=True, hide_index=True)
        
        output = BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            df.to_excel(writer, index=False, sheet_name='대화기록')
        
        st.download_button(
            "📥 엑셀 다운로드",
            data=output.getvalue(),
            file_name=f"conversations_{datetime.now().strftime('%Y%m%d')}.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        )
    else:
        st.info("아직 대화 기록이 없습니다.")
