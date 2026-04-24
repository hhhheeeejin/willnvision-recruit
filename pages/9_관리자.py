import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
from io import BytesIO
from utils.db import (
    get_all_jobs, get_job, create_job, update_job, delete_job,
    get_all_conversations, get_all_applicants,
    update_job_status, update_applicant_status,
    get_all_knowledge, create_knowledge, update_knowledge, delete_knowledge,
    get_site_settings, update_setting,
    upload_image, delete_image,
    get_stats, get_popular_jobs,
    get_all_centers, create_center, update_center, delete_center, get_active_centers,
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

tab1, tab2, tab3, tab4, tab5, tab6, tab7 = st.tabs([
    "📊 대시보드",
    "📋 공고 관리",
    "🏢 센터 관리",
    "❓ FAQ 관리",
    "⚙️ 사이트 설정",
    "👥 지원자 명단",
    "💬 대화 기록"
])

# =============================================================
# TAB 1: 대시보드
# =============================================================
with tab1:
    st.subheader("📊 전체 통계")
    
    stats = get_stats()
    
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("🟢 모집중 공고", stats['jobs_active'], f"전체 {stats['jobs_total']}개")
    col2.metric("💬 누적 대화", f"{stats['total_conversations']:,}")
    col3.metric("👥 순 방문자", f"{stats['unique_visitors']:,}")
    col4.metric("📝 지원자", f"{stats['applicants_total']:,}")
    
    st.divider()
    
    st.subheader("🏆 공고별 통계")
    st.caption("각 공고가 얼마나 관심받았는지, 실제 지원까지 이어졌는지 확인")
    
    all_jobs_stats = get_all_jobs()
    if all_jobs_stats:
        stats_data = []
        for job in all_jobs_stats:
            view_count = job.get('view_count') or 0
            apply_count = job.get('apply_count') or 0
            conversion = (apply_count / view_count * 100) if view_count > 0 else 0
            stats_data.append({
                "공고": job['title'][:30] + ('...' if len(job['title']) > 30 else ''),
                "상태": job['status'],
                "💬 문의 클릭": view_count,
                "📝 지원 클릭": apply_count,
                "🎯 전환율": f"{conversion:.1f}%"
            })
        
        df_stats = pd.DataFrame(stats_data)
        df_stats = df_stats.sort_values("💬 문의 클릭", ascending=False)
        st.dataframe(df_stats, use_container_width=True, hide_index=True)
        
        st.caption("💡 전환율 = 지원 클릭 ÷ 문의 클릭 × 100 (높을수록 실제 지원까지 잘 이어진 공고)")
    
    st.divider()
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("🔥 인기 공고 TOP 5 (문의 기준)")
        popular = get_popular_jobs(5)
        if popular:
            for i, job in enumerate(popular, 1):
                view_count = job.get('view_count', 0)
                apply_count = job.get('apply_count', 0)
                st.markdown(f"**{i}.** {job['title']}")
                st.caption(f"💬 문의 {view_count}회 · 📝 지원 {apply_count}회 · 상태: {job['status']}")
        else:
            st.info("아직 데이터가 없습니다.")
    
    with col2:
        st.subheader("⚠️ 담당자 연결 필요")
        st.metric("담당자 연결 요청", f"{stats['needs_human_count']:,}건")
        st.caption("AI가 답변 못한 질문들입니다. 💬 대화기록 탭에서 확인하세요.")

# =============================================================
# TAB 2: 공고 관리
# =============================================================
with tab2:
    st.subheader("📋 공고 관리")
    
    with st.expander("➕ 새 공고 추가하기"):
        with st.form("new_job_form", clear_on_submit=True):
            col1, col2 = st.columns(2)
            new_title = col1.text_input("직군명 *", placeholder="예: 인바운드 상담원")
            new_category = col2.selectbox("카테고리", ["IB상담", "OB상담", "채팅상담", "사무직", "기타"])
            
            active_centers = get_active_centers()
            if active_centers:
                center_options = {c['id']: c['name'] for c in active_centers}
                new_center_id = st.selectbox(
                    "근무 센터 *",
                    options=list(center_options.keys()),
                    format_func=lambda x: center_options[x],
                )
            else:
                new_center_id = None
                st.warning("⚠️ 등록된 센터가 없습니다. '🏢 센터 관리' 탭에서 먼저 센터를 추가해주세요.")
            
            col1, col2, col3 = st.columns(3)
            new_subway_line = col1.text_input("지하철 노선", placeholder="예: 2호선")
            new_subway_station = col2.text_input("지하철역", placeholder="예: 문래역")
            new_location = col3.text_input("근무지 상세", placeholder="예: 문래역 인근")
            
            col1, col2 = st.columns(2)
            new_salary = col1.text_input("급여 *", placeholder="예: 월 250만원")
            new_hours = col2.text_input("근무시간", placeholder="예: 09-18시")
            
            col1, col2 = st.columns(2)
            new_days = col1.text_input("근무요일", placeholder="예: 월-금 (주5일)")
            new_education = col2.text_input("교육 일정", placeholder="예: 5/1부터 3일간")
            
            new_features = st.text_input("특징", placeholder="예: 신입가능, 주말휴무")
            new_description = st.text_area("상세 설명", placeholder="업무 내용 등")
            
            col1, col2 = st.columns(2)
            new_form_url = col1.text_input("구글폼 URL", placeholder="https://forms.gle/...")
            new_chat_url = col2.text_input("오픈채팅 URL", placeholder="https://open.kakao.com/...")
            
            st.markdown("**🖼️ 이미지 (선택)**")
            img_method = st.radio("이미지 추가 방식", ["없음", "파일 업로드", "URL 입력"], horizontal=True)
            
            new_image_url = ""
            uploaded_file = None
            if img_method == "파일 업로드":
                uploaded_file = st.file_uploader("이미지 선택", type=["png", "jpg", "jpeg"], key="new_img")
                if uploaded_file:
                    st.image(uploaded_file, width=200)
            elif img_method == "URL 입력":
                new_image_url = st.text_input("이미지 URL", placeholder="https://...")
                if new_image_url:
                    st.image(new_image_url, width=200)
            
            new_status = st.selectbox("상태", ["모집중", "마감", "재오픈예정"])
            new_order = st.number_input("표시 순서 (작을수록 위)", min_value=0, value=99)
            
            submitted = st.form_submit_button("💾 공고 등록", type="primary", use_container_width=True)
            
            if submitted:
                if not new_title or not new_salary:
                    st.error("직군명과 급여는 필수입니다.")
                else:
                    if img_method == "파일 업로드" and uploaded_file:
                        file_bytes = uploaded_file.getvalue()
                        new_image_url = upload_image(file_bytes, uploaded_file.name) or ""
                    
                    data = {
                        "title": new_title,
                        "category": new_category,
                        "center_id": new_center_id,
                        "subway_line": new_subway_line,
                        "subway_station": new_subway_station,
                        "location": new_location or (f"{new_subway_station} 인근" if new_subway_station else ""),
                        "salary": new_salary,
                        "work_hours": new_hours,
                        "work_days": new_days,
                        "education_period": new_education,
                        "features": new_features,
                        "description": new_description,
                        "image_url": new_image_url,
                        "google_form_url": new_form_url,
                        "open_chat_url": new_chat_url,
                        "status": new_status,
                        "display_order": new_order,
                    }
                    try:
                        create_job(data)
                        st.success("✅ 공고가 등록되었습니다!")
                        st.rerun()
                    except Exception as e:
                        st.error(f"등록 실패: {e}")
    
    st.divider()
    
    st.markdown("### 📋 등록된 공고 목록")
    jobs = get_all_jobs()
    
    if not jobs:
        st.info("등록된 공고가 없습니다.")
    else:
        for job in jobs:
            with st.expander(f"**{job['title']}** — {job['status']}", expanded=False):
                if job.get('image_url'):
                    st.image(job['image_url'], width=200)
                
                with st.form(f"edit_job_{job['id']}"):
                    col1, col2 = st.columns(2)
                    ed_title = col1.text_input("직군명", value=job['title'] or "", key=f"job_title_{job['id']}")
                    ed_category = col2.selectbox(
                        "카테고리",
                        ["IB상담", "OB상담", "채팅상담", "사무직", "기타"],
                        index=["IB상담", "OB상담", "채팅상담", "사무직", "기타"].index(job['category']) if job.get('category') in ["IB상담", "OB상담", "채팅상담", "사무직", "기타"] else 0,
                        key=f"job_cat_{job['id']}"
                    )
                    
                    active_centers_list = get_active_centers()
                    if active_centers_list:
                        center_opts = {c['id']: c['name'] for c in active_centers_list}
                        current_center_id = job.get('center_id')
                        current_idx = 0
                        if current_center_id in center_opts:
                            current_idx = list(center_opts.keys()).index(current_center_id)
                        ed_center_id = st.selectbox(
                            "근무 센터",
                            options=list(center_opts.keys()),
                            format_func=lambda x: center_opts[x],
                            index=current_idx,
                            key=f"job_center_{job['id']}",
                        )
                    else:
                        ed_center_id = job.get('center_id')
                    
                    col1, col2, col3 = st.columns(3)
                    ed_subway_line = col1.text_input("노선", value=job.get('subway_line') or "", key=f"job_line_{job['id']}")
                    ed_subway_station = col2.text_input("역", value=job.get('subway_station') or "", key=f"job_stn_{job['id']}")
                    ed_location = col3.text_input("근무지", value=job.get('location') or "", key=f"job_loc_{job['id']}")
                    
                    col1, col2 = st.columns(2)
                    ed_salary = col1.text_input("급여", value=job.get('salary') or "", key=f"job_sal_{job['id']}")
                    ed_hours = col2.text_input("근무시간", value=job.get('work_hours') or "", key=f"job_hrs_{job['id']}")
                    
                    col1, col2 = st.columns(2)
                    ed_days = col1.text_input("근무요일", value=job.get('work_days') or "", key=f"job_days_{job['id']}")
                    ed_education = col2.text_input("교육", value=job.get('education_period') or "", key=f"job_edu_{job['id']}")
                    
                    ed_features = st.text_input("특징", value=job.get('features') or "", key=f"job_feat_{job['id']}")
                    ed_description = st.text_area("설명", value=job.get('description') or "", key=f"job_desc_{job['id']}")
                    
                    col1, col2 = st.columns(2)
                    ed_form_url = col1.text_input("구글폼 URL", value=job.get('google_form_url') or "", key=f"job_form_{job['id']}")
                    ed_chat_url = col2.text_input("오픈채팅 URL", value=job.get('open_chat_url') or "", key=f"job_chat_{job['id']}")
                    
                    st.markdown("**🖼️ 이미지 수정**")
                    img_action = st.radio(
                        "이미지",
                        ["유지", "새 파일 업로드", "URL 변경", "삭제"],
                        horizontal=True,
                        key=f"img_action_{job['id']}"
                    )
                    
                    ed_image_url = job.get('image_url') or ""
                    new_upload = None
                    if img_action == "새 파일 업로드":
                        new_upload = st.file_uploader("새 이미지", type=["png", "jpg", "jpeg"], key=f"upload_{job['id']}")
                    elif img_action == "URL 변경":
                        ed_image_url = st.text_input("새 이미지 URL", value=ed_image_url, key=f"new_url_{job['id']}")
                    
                    col1, col2 = st.columns(2)
                    ed_status = col1.selectbox(
                        "상태",
                        ["모집중", "마감", "재오픈예정"],
                        index=["모집중", "마감", "재오픈예정"].index(job['status']),
                        key=f"job_status_{job['id']}"
                    )
                    ed_order = col2.number_input("순서", min_value=0, value=job.get('display_order') or 0, key=f"job_order_{job['id']}")
                    
                    col1, col2, col3 = st.columns(3)
                    save_btn = col1.form_submit_button("💾 저장", type="primary", use_container_width=True)
                    delete_btn = col3.form_submit_button("🗑️ 삭제", use_container_width=True)
                    
                    if save_btn:
                        final_image_url = ed_image_url
                        if img_action == "새 파일 업로드" and new_upload:
                            final_image_url = upload_image(new_upload.getvalue(), new_upload.name) or ed_image_url
                        elif img_action == "삭제":
                            final_image_url = ""
                        
                        data = {
                            "title": ed_title,
                            "category": ed_category,
                            "center_id": ed_center_id,
                            "subway_line": ed_subway_line,
                            "subway_station": ed_subway_station,
                            "location": ed_location,
                            "salary": ed_salary,
                            "work_hours": ed_hours,
                            "work_days": ed_days,
                            "education_period": ed_education,
                            "features": ed_features,
                            "description": ed_description,
                            "image_url": final_image_url,
                            "google_form_url": ed_form_url,
                            "open_chat_url": ed_chat_url,
                            "status": ed_status,
                            "display_order": ed_order,
                        }
                        try:
                            update_job(job['id'], data)
                            st.success("✅ 수정 완료!")
                            st.rerun()
                        except Exception as e:
                            st.error(f"수정 실패: {e}")
                    
                    if delete_btn:
                        try:
                            delete_job(job['id'])
                            st.success("🗑️ 삭제됨")
                            st.rerun()
                        except Exception as e:
                            st.error(f"삭제 실패: {e}")

# =============================================================
# TAB 3: 센터 관리
# =============================================================
with tab3:
    st.subheader("🏢 센터 관리")
    st.caption("근무지(센터)를 추가/수정합니다. 각 공고는 하나의 센터에 연결됩니다.")
    
    with st.expander("➕ 새 센터 추가"):
        with st.form("new_center_form", clear_on_submit=True):
            col1, col2 = st.columns(2)
            nc_name = col1.text_input("센터 이름 *", placeholder="예: 윌앤비전 강남센터")
            nc_phone = col2.text_input("대표 연락처", placeholder="02-XXX-XXXX")
            
            nc_address = st.text_input("주소 *", placeholder="예: 서울특별시 강남구 테헤란로 123")
            nc_detail = st.text_input("상세 안내", placeholder="예: XX빌딩 5층, 역에서 도보 3분")
            
            col1, col2 = st.columns(2)
            nc_subway = col1.text_input("지하철 정보", placeholder="예: 2호선 강남역 3번 출구")
            nc_bus = col2.text_input("버스 정보", placeholder="예: 강남역 정류장 (간선 143, 362)")
            
            nc_desc = st.text_area("센터 설명", placeholder="이 센터에서 운영하는 업무 등")
            
            col1, col2 = st.columns(2)
            nc_parking = col1.checkbox("🚗 주차 가능")
            nc_active = col2.checkbox("✅ 활성화", value=True)
            
            nc_order = st.number_input("표시 순서 (작을수록 위)", min_value=0, value=99)
            
            submitted = st.form_submit_button("💾 센터 등록", type="primary", use_container_width=True)
            if submitted:
                if not nc_name or not nc_address:
                    st.error("센터 이름과 주소는 필수입니다.")
                else:
                    try:
                        create_center({
                            "name": nc_name,
                            "address": nc_address,
                            "detail_address": nc_detail,
                            "phone": nc_phone,
                            "subway_info": nc_subway,
                            "bus_info": nc_bus,
                            "description": nc_desc,
                            "parking_available": nc_parking,
                            "is_active": nc_active,
                            "display_order": nc_order,
                        })
                        st.success("✅ 센터가 등록되었습니다!")
                        st.rerun()
                    except Exception as e:
                        st.error(f"등록 실패: {e}")
    
    st.divider()
    
    st.markdown("### 📋 등록된 센터")
    centers = get_all_centers()
    
    if not centers:
        st.info("등록된 센터가 없습니다. 위에서 추가해주세요.")
    else:
        for c in centers:
            status_badge = "🟢 활성" if c.get('is_active') else "⚫ 비활성"
            with st.expander(f"**{c['name']}** — {status_badge}", expanded=False):
                with st.form(f"edit_center_{c['id']}"):
                    col1, col2 = st.columns(2)
                    ec_name = col1.text_input("이름", value=c['name'], key=f"ctr_name_{c['id']}")
                    ec_phone = col2.text_input("연락처", value=c.get('phone') or "", key=f"ctr_phone_{c['id']}")
                    
                    ec_address = st.text_input("주소", value=c['address'], key=f"ctr_addr_{c['id']}")
                    ec_detail = st.text_input("상세 안내", value=c.get('detail_address') or "", key=f"ctr_detail_{c['id']}")
                    
                    col1, col2 = st.columns(2)
                    ec_subway = col1.text_input("지하철", value=c.get('subway_info') or "", key=f"ctr_subway_{c['id']}")
                    ec_bus = col2.text_input("버스", value=c.get('bus_info') or "", key=f"ctr_bus_{c['id']}")
                    
                    ec_desc = st.text_area("설명", value=c.get('description') or "", key=f"ctr_desc_{c['id']}")
                    
                    col1, col2, col3 = st.columns(3)
                    ec_parking = col1.checkbox("🚗 주차 가능", value=c.get('parking_available', False), key=f"ctr_parking_{c['id']}")
                    ec_active = col2.checkbox("✅ 활성화", value=c.get('is_active', True), key=f"ctr_active_{c['id']}")
                    ec_order = col3.number_input("순서", min_value=0, value=c.get('display_order') or 0, key=f"ctr_order_{c['id']}")
                    
                    col1, col2 = st.columns(2)
                    save_btn = col1.form_submit_button("💾 저장", type="primary", use_container_width=True)
                    delete_btn = col2.form_submit_button("🗑️ 삭제", use_container_width=True)
                    
                    if save_btn:
                        try:
                            update_center(c['id'], {
                                "name": ec_name,
                                "address": ec_address,
                                "detail_address": ec_detail,
                                "phone": ec_phone,
                                "subway_info": ec_subway,
                                "bus_info": ec_bus,
                                "description": ec_desc,
                                "parking_available": ec_parking,
                                "is_active": ec_active,
                                "display_order": ec_order,
                            })
                            st.success("✅ 수정 완료!")
                            st.rerun()
                        except Exception as e:
                            st.error(f"실패: {e}")
                    
                    if delete_btn:
                        try:
                            delete_center(c['id'])
                            st.success("🗑️ 삭제됨")
                            st.rerun()
                        except Exception as e:
                            st.error(f"실패: {e}. 이 센터에 연결된 공고가 있을 수 있어요.")

# =============================================================
# TAB 4: FAQ 관리
# =============================================================
with tab4:
    st.subheader("❓ FAQ 관리")
    st.caption("자주 묻는 질문을 추가/수정하세요.")
    
    with st.expander("➕ 새 FAQ 추가"):
        with st.form("new_faq_form", clear_on_submit=True):
            col1, col2 = st.columns([1, 2])
            new_category = col1.selectbox("카테고리", ["회사소개", "담당자", "지원방법", "근무조건", "기타"])
            new_order = col2.number_input("표시 순서", min_value=0, value=99)
            
            new_question = st.text_input("질문 *", placeholder="예: 재택근무 가능한가요?")
            new_answer = st.text_area("답변 *", placeholder="답변을 입력하세요")
            
            col1, col2 = st.columns(2)
            new_show_faq = col1.checkbox("메인 FAQ에 표시", value=True)
            new_active = col2.checkbox("활성화", value=True)
            
            submitted = st.form_submit_button("💾 등록", type="primary", use_container_width=True)
            if submitted:
                if not new_question or not new_answer:
                    st.error("질문과 답변은 필수입니다.")
                else:
                    try:
                        create_knowledge({
                            "category": new_category,
                            "question": new_question,
                            "answer": new_answer,
                            "display_order": new_order,
                            "show_in_faq": new_show_faq,
                            "is_active": new_active,
                        })
                        st.success("✅ 등록 완료!")
                        st.rerun()
                    except Exception as e:
                        st.error(f"실패: {e}")
    
    st.divider()
    
    kb_items = get_all_knowledge()
    if not kb_items:
        st.info("등록된 FAQ가 없습니다.")
    else:
        for item in kb_items:
            with st.expander(f"**[{item.get('category', '기타')}]** {item.get('question', '(질문 없음)')[:40]}..."):
                with st.form(f"edit_faq_{item['id']}"):
                    ed_q = st.text_input("질문", value=item.get('question') or "", key=f"faq_q_{item['id']}")
                    ed_a = st.text_area("답변", value=item.get('answer') or "", key=f"faq_a_{item['id']}")
                    
                    col1, col2 = st.columns(2)
                    ed_cat = col1.selectbox(
                        "카테고리",
                        ["회사소개", "담당자", "지원방법", "근무조건", "기타"],
                        index=["회사소개", "담당자", "지원방법", "근무조건", "기타"].index(item.get('category')) if item.get('category') in ["회사소개", "담당자", "지원방법", "근무조건", "기타"] else 4,
                        key=f"faq_cat_{item['id']}"
                    )
                    ed_order = col2.number_input("순서", min_value=0, value=item.get('display_order') or 0, key=f"faq_ord_{item['id']}")
                    
                    col1, col2 = st.columns(2)
                    ed_show = col1.checkbox("FAQ에 표시", value=item.get('show_in_faq', True), key=f"faq_show_{item['id']}")
                    ed_active = col2.checkbox("활성화", value=item.get('is_active', True), key=f"faq_act_{item['id']}")
                    
                    col1, col2 = st.columns(2)
                    save = col1.form_submit_button("💾 저장", type="primary", use_container_width=True)
                    delete = col2.form_submit_button("🗑️ 삭제", use_container_width=True)
                    
                    if save:
                        update_knowledge(item['id'], {
                            "question": ed_q,
                            "answer": ed_a,
                            "category": ed_cat,
                            "display_order": ed_order,
                            "show_in_faq": ed_show,
                            "is_active": ed_active,
                        })
                        st.success("저장됨!")
                        st.rerun()
                    if delete:
                        delete_knowledge(item['id'])
                        st.success("삭제됨")
                        st.rerun()

# =============================================================
# TAB 5: 사이트 설정
# =============================================================
with tab5:
    st.subheader("⚙️ 사이트 설정")
    st.caption("첫화면 문구, 담당자 정보, 연락처 등을 편집합니다.")
    
    settings = get_site_settings()
    
    with st.form("settings_form"):
        st.markdown("### 🎨 메인 페이지")
        col1, col2 = st.columns([1, 3])
        new_emoji = col1.text_input("대표 이모지", value=settings.get('hero_emoji', '🏢'))
        new_title = col2.text_input("헤드라인 제목", value=settings.get('hero_title', ''))
        new_subtitle = st.text_input("서브타이틀", value=settings.get('hero_subtitle', ''))
        new_hero_img = st.text_input("상단 이미지 URL (선택)", value=settings.get('hero_image_url', ''))
        new_intro = st.text_area("회사 소개", value=settings.get('company_intro', ''))
        
        st.divider()
        st.markdown("### 📞 담당자 정보")
        col1, col2 = st.columns(2)
        new_m_name = col1.text_input("담당자 이름", value=settings.get('manager_name', ''))
        new_m_phone = col2.text_input("담당자 전화번호", value=settings.get('manager_phone', ''))
        new_m_email = st.text_input("담당자 이메일 (선택)", value=settings.get('manager_email', ''))
        
        st.divider()
        st.markdown("### 🔗 외부 링크")
        new_default_form = st.text_input(
            "기본 구글폼 URL",
            value=settings.get('default_google_form_url', ''),
            help="공고별 구글폼이 없을 때 사용됩니다."
        )
        new_openchat = st.text_input(
            "카카오 오픈채팅 URL",
            value=settings.get('kakao_openchat_url', ''),
            help="지원자가 담당자와 직접 대화할 수 있는 오픈채팅방"
        )
        
        st.divider()
        st.markdown("### 🗺️ 기본 사무실 위치")
        st.caption("💡 센터별 위치는 '🏢 센터 관리' 탭에서 설정")
        new_address = st.text_input("기본 사무실 주소", value=settings.get('office_address', ''))
        
        st.divider()
st.markdown("### 🤖 챗봇 설정")
st.caption("챗봇 이름, 인사말, 추천 질문 등을 꾸밀 수 있어요!")

col1, col2 = st.columns([1, 3])
new_bot_emoji = col1.text_input("챗봇 이모지", value=settings.get('chatbot_emoji', '🤖'))
new_bot_name = col2.text_input("챗봇 이름", value=settings.get('chatbot_name', '윌비봇'))

new_greeting = st.text_input(
    "메인 인사말",
    value=settings.get('chatbot_greeting', "궁금한 건 윌비봇에게 물어보세요 ●'◡'●"),
    help="챗봇 상단에 큰 글씨로 표시되는 문구"
)
new_sub_greeting = st.text_input(
    "서브 인사말",
    value=settings.get('chatbot_sub_greeting', '24시간 친절하게 답변드려요!'),
    help="인사말 아래 작은 글씨"
)

col1, col2 = st.columns(2)
new_placeholder = col1.text_input(
    "입력창 안내",
    value=settings.get('chatbot_placeholder', '편하게 질문 주세요... 🙌'),
    help="질문 입력란에 나타나는 안내 문구"
)
new_empty_msg = col2.text_input(
    "빈 대화 문구",
    value=settings.get('chatbot_empty_msg', '💬 대화를 시작해주세요!'),
    help="대화가 없을 때 보여줄 문구"
)

new_thinking_msg = st.text_input(
    "답변 대기 문구",
    value=settings.get('chatbot_thinking_msg', '윌비가 생각 중이에요... 💭'),
    help="AI가 답변 만드는 동안 보여줄 문구"
)

st.markdown("**💡 추천 질문 (챗봇 시작 시 표시)**")
col1, col2 = st.columns(2)
new_sug_q1 = col1.text_input("추천 질문 1", value=settings.get('suggested_q_1', '신입도 가능해요?'))
new_sug_q2 = col2.text_input("추천 질문 2", value=settings.get('suggested_q_2', '재택 있나요?'))
col1, col2 = st.columns(2)
new_sug_q3 = col1.text_input("추천 질문 3", value=settings.get('suggested_q_3', '급여 얼마에요?'))
new_sug_q4 = col2.text_input("추천 질문 4", value=settings.get('suggested_q_4', '교육 기간은?'))

st.markdown("**🎭 말투 & 동작**")
new_tone = st.selectbox(
    "말투 스타일",
    ["friendly", "casual", "formal"],
    format_func=lambda x: {"friendly": "😊 친근하게", "casual": "🙌 편하게", "formal": "🎩 격식있게"}[x],
    index=["friendly", "casual", "formal"].index(settings.get('chatbot_tone', 'friendly'))
)
new_auto_apply = st.checkbox(
    "대화 중 자동 지원 유도",
    value=settings.get('chatbot_auto_apply_prompt', 'true') == 'true',
    help="대화가 충분히 오가면 지원서 링크를 표시"
)
        
        submitted = st.form_submit_button("💾 모든 설정 저장", type="primary", use_container_width=True)
        
        if submitted:
    updates = {
        'hero_emoji': new_emoji,
        'hero_title': new_title,
        'hero_subtitle': new_subtitle,
        'hero_image_url': new_hero_img,
        'company_intro': new_intro,
        'manager_name': new_m_name,
        'manager_phone': new_m_phone,
        'manager_email': new_m_email,
        'default_google_form_url': new_default_form,
        'kakao_openchat_url': new_openchat,
        'office_address': new_address,
        # 챗봇 설정
        'chatbot_name': new_bot_name,
        'chatbot_emoji': new_bot_emoji,
        'chatbot_greeting': new_greeting,
        'chatbot_sub_greeting': new_sub_greeting,
        'chatbot_placeholder': new_placeholder,
        'chatbot_empty_msg': new_empty_msg,
        'chatbot_thinking_msg': new_thinking_msg,
        'suggested_q_1': new_sug_q1,
        'suggested_q_2': new_sug_q2,
        'suggested_q_3': new_sug_q3,
        'suggested_q_4': new_sug_q4,
        'chatbot_tone': new_tone,
        'chatbot_auto_apply_prompt': 'true' if new_auto_apply else 'false',
    }
            try:
                for k, v in updates.items():
                    update_setting(k, v)
                st.success("✅ 모든 설정이 저장되었습니다!")
                st.rerun()
            except Exception as e:
                st.error(f"저장 실패: {e}")

# =============================================================
# TAB 6: 지원자 명단
# =============================================================
with tab6:
    st.subheader("👥 지원자 명단")
    
    st.info("💡 **추천**: 지원서는 **구글폼**으로 받는 것이 보안상 안전합니다.")
    
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
    else:
        st.info("아직 Streamlit 내부 지원자가 없습니다. 구글폼 지원자는 구글시트에서 확인하세요.")

# =============================================================
# TAB 7: 대화 기록
# =============================================================
with tab7:
    st.subheader("💬 AI 챗봇 대화 기록")
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
        
        show_only_needs_human = st.checkbox("⚠️ 담당자 연결 필요한 것만 보기")
        if show_only_needs_human:
            df = df[df['담당자필요'] == '✅']
        
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
