import streamlit as st
from utils.db import get_active_jobs, save_applicant

st.set_page_config(page_title="간편 지원", page_icon="📝", layout="centered")

st.title("📝 윌앤비전 간편 지원")
st.caption("1분이면 끝나요. 영업일 기준 2~3일 내 연락드립니다.")

jobs = get_active_jobs()

if not jobs:
    st.warning("현재 모집 중인 공고가 없습니다.")
    st.stop()

job_options = {j['id']: j['title'] for j in jobs}
preset_job_id = st.session_state.pop("preset_job_id", None)
default_index = list(job_options.keys()).index(preset_job_id) if preset_job_id in job_options else 0

with st.form("apply_form"):
    name = st.text_input("이름 *", placeholder="홍길동")
    phone = st.text_input("연락처 *", placeholder="010-0000-0000")
    
    selected_job_id = st.selectbox(
        "지원 공고 *",
        options=list(job_options.keys()),
        format_func=lambda x: job_options[x],
        index=default_index,
    )
    
    experience = st.radio(
        "콜센터 경력 *",
        options=["신입", "1년 미만", "1-3년", "3년 이상"],
        horizontal=True,
    )
    
    introduction = st.text_area(
        "간단 자기소개 (선택)",
        placeholder="자유롭게 본인을 소개해 주세요",
        height=100,
    )
    
    submitted = st.form_submit_button("제출하기", type="primary", use_container_width=True)
    
    if submitted:
        if not name or not phone:
            st.error("이름과 연락처는 필수입니다.")
        elif len(phone.replace("-", "")) < 10:
            st.error("올바른 연락처를 입력해주세요.")
        else:
            try:
                save_applicant(
                    name=name,
                    phone=phone,
                    job_id=selected_job_id,
                    job_title=job_options[selected_job_id],
                    experience=experience,
                    introduction=introduction,
                )
                st.success("✅ 지원이 접수되었습니다!\n\n2~3일 내 010-9467-6139로 연락드릴게요. 감사합니다 😊")
                st.balloons()
            except Exception as e:
                st.error(f"제출 중 오류가 발생했습니다. 담당자에게 직접 연락 주세요.")
                st.caption(f"에러: {str(e)}")

st.divider()
st.caption("문의: 010-9467-6139")
