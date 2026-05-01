import streamlit as st
import pandas as pd
from datetime import datetime
from io import BytesIO
from utils.db import (
    get_all_jobs, create_job, update_job, delete_job,
    get_all_conversations,
    get_all_knowledge, create_knowledge, update_knowledge, delete_knowledge,
    get_site_settings, update_setting,
    get_stats, get_popular_jobs,
    get_all_centers, create_center, update_center, delete_center, get_active_centers,
    get_all_center_faqs, create_center_faq, update_center_faq, delete_center_faq,
    upload_image, delete_image,
    get_commute_stats, get_commute_region_stats,
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


# ============ 다음 우편번호 API 컴포넌트 ============
def daum_postcode_widget():
    return """
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="utf-8">
        <style>
            body { font-family: 'Pretendard', sans-serif; margin: 0; padding: 10px; background: white; }
            .search-btn {
                background: #2563EB;
                color: white;
                border: none;
                padding: 12px 20px;
                border-radius: 10px;
                font-weight: 700;
                font-size: 14px;
                cursor: pointer;
                width: 100%;
                margin-bottom: 10px;
            }
            .search-btn:hover { background: #1E40AF; }
            .result-box {
                background: #F1F5F9;
                padding: 12px;
                border-radius: 10px;
                margin-top: 10px;
                font-size: 13px;
                color: #1E293B;
                line-height: 1.6;
                display: none;
            }
            .result-box.show { display: block; }
            .result-label { font-weight: 700; color: #1E40AF; margin-bottom: 4px; }
            .copy-info {
                background: #FEF3C7;
                padding: 10px;
                border-radius: 8px;
                margin-top: 10px;
                font-size: 12px;
                color: #92400E;
                line-height: 1.5;
            }
        </style>
    </head>
    <body>
        <button class="search-btn" onclick="execDaumPostcode()">
            🔍 주소 검색하기 (다음 우편번호 API)
        </button>
        
        <div id="result" class="result-box">
            <div class="result-label">📍 검색 결과</div>
            <div id="postcode"></div>
            <div id="address"></div>
            <div id="extraAddress"></div>
            <div class="copy-info">
                💡 위 주소를 아래 입력 칸에 복사·붙여넣기 하세요!
            </div>
        </div>

        <script src="//t1.daumcdn.net/mapjsapi/bundle/postcode/prod/postcode.v2.js"></script>
        <script>
            function execDaumPostcode() {
                new daum.Postcode({
                    oncomplete: function(data) {
                        var addr = '';
                        var extraAddr = '';
                        
                        if (data.userSelectedType === 'R') {
                            addr = data.roadAddress;
                        } else {
                            addr = data.jibunAddress;
                        }
                        
                        if (data.userSelectedType === 'R') {
                            if (data.bname !== '' && /[동|로|가]$/g.test(data.bname)) {
                                extraAddr += data.bname;
                            }
                            if (data.buildingName !== '' && data.apartment === 'Y') {
                                extraAddr += (extraAddr !== '' ? ', ' + data.buildingName : data.buildingName);
                            }
                            if (extraAddr !== '') {
                                extraAddr = ' (' + extraAddr + ')';
                            }
                        }
                        
                        document.getElementById('postcode').innerHTML = '<b>우편번호:</b> ' + data.zonecode;
                        document.getElementById('address').innerHTML = '<b>주소:</b> ' + addr + extraAddr;
                        document.getElementById('extraAddress').innerHTML = '<b>참고:</b> ' + (data.buildingName || '없음');
                        document.getElementById('result').classList.add('show');
                    }
                }).open();
            }
        </script>
    </body>
    </html>
    """


tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
    "📊 대시보드",
    "📋 공고 관리",
    "🏢 센터 관리",
    "❓ FAQ 관리",
    "⚙️ 사이트 설정",
    "💬 대화 기록"
])

# =============================================================
# TAB 1: 대시보드
# =============================================================
with tab1:
    st.subheader("📊 전체 통계")
    
    stats = get_stats()
    
    col1, col2, col3 = st.columns(3)
    col1.metric("🟢 모집중 공고", stats['jobs_active'], f"전체 {stats['jobs_total']}개")
    col2.metric("💬 누적 대화", f"{stats['total_conversations']:,}")
    col3.metric("👥 순 방문자", f"{stats['unique_visitors']:,}")
    
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
        st.caption("💡 전환율 = 지원 클릭 ÷ 문의 클릭 × 100")
    
    st.divider()
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("🔥 인기 공고 TOP 5")
        popular = get_popular_jobs(5)
        if popular:
            for i, job in enumerate(popular, 1):
                view_count = job.get('view_count', 0)
                apply_count = job.get('apply_count', 0)
                st.markdown(f"**{i}.** {job['title']}")
                st.caption(f"💬 문의 {view_count}회 · 📝 지원 {apply_count}회 · {job['status']}")
        else:
            st.info("아직 데이터가 없습니다.")
    
    with col2:
        st.subheader("⚠️ 담당자 연결 필요")
        st.metric("담당자 연결 요청", f"{stats['needs_human_count']:,}건")
        st.caption("AI가 답변 못한 질문들. 💬 대화기록 탭에서 확인하세요.")
    
    st.divider()
    
    # 출근거리 지역 통계
    st.subheader("🚇 출근거리 검색 지역 통계")
    st.caption("어느 지역에서 채용 문의가 많은지 추정 가능")
    
    region_stats = get_commute_region_stats()
    
    if region_stats:
        col1, col2 = st.columns([2, 1])
        
        with col1:
            st.markdown("**📊 지역별 검색 수 (TOP 10)**")
            total = sum(c for _, c in region_stats)
            for i, (region, count) in enumerate(region_stats[:10], 1):
                pct = (count / total * 100) if total > 0 else 0
                bar_width = min(pct * 3, 100)
                BAR_HTML = (
                    f'<div style="margin-bottom: 8px;">'
                    f'<div style="display: flex; justify-content: space-between; font-size: 0.85rem; margin-bottom: 4px;">'
                    f'<span style="font-weight: 600;">{i}. {region}</span>'
                    f'<span style="color: #475569;">{count}회 ({pct:.1f}%)</span>'
                    f'</div>'
                    f'<div style="background: #E2E8F0; border-radius: 6px; height: 8px; overflow: hidden;">'
                    f'<div style="background: #2563EB; '
                    f'width: {bar_width}%; height: 100%; border-radius: 6px;"></div>'
                    f'</div></div>'
                )
                st.html(BAR_HTML)
        
        with col2:
            st.metric("총 검색 수", f"{total:,}건")
            st.metric("지역 수", f"{len(region_stats)}개")
            
            if region_stats:
                top_region, top_count = region_stats[0]
                st.metric("🏆 1위 지역", top_region, f"{top_count}회")
        
        with st.expander("📋 상세 검색 기록 보기"):
            commute_data = get_commute_stats()
            if commute_data:
                df_commute = pd.DataFrame([{
                    "시간": c['created_at'][:19].replace('T', ' '),
                    "출발지": c['start_address'],
                    "지역": c.get('region', '기타'),
                    "도착 센터": c.get('center_name', ''),
                    "교통수단": c.get('transport_type', ''),
                } for c in commute_data])
                st.dataframe(df_commute, use_container_width=True, hide_index=True)
    else:
        st.info("아직 출근거리 검색 기록이 없습니다.")

# =============================================================
# TAB 2: 공고 관리
# =============================================================
with tab2:
    st.subheader("📋 공고 관리")
    
    with st.expander("➕ 새 공고 추가하기"):
        active_centers = get_active_centers()
        if active_centers:
            center_options = {c['id']: c['name'] for c in active_centers}
            new_center_id = st.selectbox(
                "🏢 근무 센터 선택 *",
                options=list(center_options.keys()),
                format_func=lambda x: center_options[x],
                key="new_job_center_select",
            )
            
            selected_center = next((c for c in active_centers if c['id'] == new_center_id), None)
            if selected_center:
                info_text = f"**{selected_center['name']}**\n\n"
                info_text += f"📍 주소: {selected_center.get('address', '')}\n\n"
                if selected_center.get('subway_info'):
                    info_text += f"🚇 지하철: {selected_center.get('subway_info', '')}\n\n"
                if selected_center.get('phone'):
                    info_text += f"📞 연락처: {selected_center.get('phone', '')}"
                st.info(info_text)
        else:
            new_center_id = None
            selected_center = None
            st.warning("⚠️ 등록된 센터가 없습니다. '🏢 센터 관리' 탭에서 먼저 추가하세요.")
        
        st.markdown("**🖼️ 공고 이미지 (선택)**")
        st.caption("공고 카드 펼치면 상단에 표시됩니다. 1MB 이하 권장")
        
        img_method = st.radio(
            "이미지 추가 방식",
            ["없음", "📁 파일 업로드", "🔗 URL 입력"],
            horizontal=True,
            key="new_img_method"
        )
        
        new_image_url_temp = ""
        uploaded_file_temp = None
        
        if img_method == "📁 파일 업로드":
            uploaded_file_temp = st.file_uploader(
                "이미지 선택",
                type=["png", "jpg", "jpeg", "gif", "webp"],
                key="new_img_upload",
            )
            if uploaded_file_temp:
                st.image(uploaded_file_temp, width=300, caption="✅ 미리보기")
        elif img_method == "🔗 URL 입력":
            new_image_url_temp = st.text_input(
                "이미지 URL",
                placeholder="https://...",
                key="new_img_url"
            )
            if new_image_url_temp:
                try:
                    st.image(new_image_url_temp, width=300, caption="✅ 미리보기")
                except Exception:
                    st.warning("⚠️ URL 오류")
        
        with st.form("new_job_form", clear_on_submit=True):
            col1, col2 = st.columns(2)
            new_title = col1.text_input("직군명 *", placeholder="예: 인바운드 상담원")
            new_category = col2.selectbox("카테고리", ["IB상담", "OB상담", "채팅상담", "사무직", "기타"])
            
            default_subway_line = ""
            default_subway_station = ""
            default_location = ""
            
            if selected_center:
                subway_info = selected_center.get('subway_info', '') or ""
                if '호선' in subway_info:
                    parts = subway_info.split(' ', 1)
                    if len(parts) >= 1:
                        default_subway_line = parts[0]
                    if len(parts) >= 2:
                        rest = parts[1]
                        if '역' in rest:
                            default_subway_station = rest.split('역')[0] + '역'
                
                default_location = f"{default_subway_station} 인근" if default_subway_station else selected_center.get('address', '')[:20]
            
            st.caption("💡 센터 기반 자동 채워짐")
            
            col1, col2, col3 = st.columns(3)
            new_subway_line = col1.text_input("지하철 노선", value=default_subway_line)
            new_subway_station = col2.text_input("지하철역", value=default_subway_station)
            new_location = col3.text_input("근무지 상세", value=default_location)
            
            col1, col2 = st.columns(2)
            new_salary = col1.text_input("급여 *", placeholder="예: 월 250만원")
            new_hours = col2.text_input("근무시간", placeholder="예: 09-18시")
            
            col1, col2 = st.columns(2)
            new_days = col1.text_input("근무요일", placeholder="예: 월-금")
            new_education = col2.text_input("교육 일정", placeholder="예: 5/1부터 5일")
            
            new_features = st.text_input("특징", placeholder="예: 신입가능")
            new_description = st.text_area("상세 설명")
            
            col1, col2 = st.columns(2)
            new_form_url = col1.text_input("구글폼 URL")
            new_chat_url = col2.text_input("오픈채팅 URL")
            
            st.markdown("**🌐 외부 채용 사이트 (선택)**")
            col1, col2 = st.columns([1, 2])
            new_external_site = col1.text_input("사이트명", placeholder="예: 알바몬")
            new_external_url = col2.text_input("URL", placeholder="https://...")
            
            new_status = st.selectbox("상태", ["모집중", "마감", "재오픈예정"])
            new_order = st.number_input("표시 순서", min_value=0, value=99)
            
            submitted = st.form_submit_button("💾 공고 등록", type="primary", use_container_width=True)
            
            if submitted:
                if not new_title or not new_salary:
                    st.error("직군명과 급여는 필수입니다.")
                elif not new_center_id:
                    st.error("근무 센터를 선택해주세요.")
                else:
                    final_image_url = ""
                    if img_method == "📁 파일 업로드" and uploaded_file_temp:
                        with st.spinner("이미지 업로드 중..."):
                            file_bytes = uploaded_file_temp.getvalue()
                            uploaded_url = upload_image(file_bytes, uploaded_file_temp.name)
                            if uploaded_url:
                                final_image_url = uploaded_url
                    elif img_method == "🔗 URL 입력" and new_image_url_temp:
                        final_image_url = new_image_url_temp
                    
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
                        "google_form_url": new_form_url,
                        "open_chat_url": new_chat_url,
                        "external_url": new_external_url,
                        "external_site_name": new_external_site,
                        "image_url": final_image_url,
                        "status": new_status,
                        "display_order": new_order,
                    }
                    try:
                        create_job(data)
                        st.success("✅ 공고가 등록되었습니다!")
                        st.cache_data.clear()
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
                
                current_image = job.get('image_url') or ""
                if current_image:
                    st.markdown("**🖼️ 현재 이미지**")
                    st.image(current_image, width=200)
                
                st.markdown("**🖼️ 이미지 작업**")
                img_action = st.radio(
                    "이미지 작업",
                    ["유지", "📁 새 파일 업로드", "🔗 URL 변경", "🗑️ 삭제"],
                    horizontal=True,
                    key=f"img_action_{job['id']}",
                    label_visibility="collapsed"
                )
                
                new_upload_file = None
                new_image_url_input = current_image
                
                if img_action == "📁 새 파일 업로드":
                    new_upload_file = st.file_uploader(
                        "새 이미지 선택",
                        type=["png", "jpg", "jpeg", "gif", "webp"],
                        key=f"upload_{job['id']}"
                    )
                    if new_upload_file:
                        st.image(new_upload_file, width=200)
                elif img_action == "🔗 URL 변경":
                    new_image_url_input = st.text_input(
                        "새 이미지 URL",
                        value=current_image,
                        key=f"new_url_{job['id']}"
                    )
                
                with st.form(f"edit_job_{job['id']}"):
                    col1, col2 = st.columns(2)
                    ed_title = col1.text_input("직군명", value=job['title'] or "", key=f"job_title_{job['id']}")
                    cat_options = ["IB상담", "OB상담", "채팅상담", "사무직", "기타"]
                    ed_category = col2.selectbox(
                        "카테고리",
                        cat_options,
                        index=cat_options.index(job['category']) if job.get('category') in cat_options else 0,
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
                            "🏢 근무 센터",
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
                    
                    st.markdown("**🌐 외부 채용 사이트 (선택)**")
                    col1, col2 = st.columns([1, 2])
                    ed_external_site = col1.text_input(
                        "사이트명",
                        value=job.get('external_site_name') or "",
                        key=f"job_ext_site_{job['id']}"
                    )
                    ed_external_url = col2.text_input(
                        "URL",
                        value=job.get('external_url') or "",
                        key=f"job_ext_url_{job['id']}"
                    )
                    
                    col1, col2 = st.columns(2)
                    status_options = ["모집중", "마감", "재오픈예정"]
                    ed_status = col1.selectbox(
                        "상태",
                        status_options,
                        index=status_options.index(job['status']) if job['status'] in status_options else 0,
                        key=f"job_status_{job['id']}"
                    )
                    ed_order = col2.number_input("순서", min_value=0, value=job.get('display_order') or 0, key=f"job_order_{job['id']}")
                    
                    col1, col2, col3 = st.columns(3)
                    save_btn = col1.form_submit_button("💾 저장", type="primary", use_container_width=True)
                    delete_btn = col3.form_submit_button("🗑️ 삭제", use_container_width=True)
                    
                    if save_btn:
                        final_image = current_image
                        if img_action == "📁 새 파일 업로드" and new_upload_file:
                            with st.spinner("이미지 업로드 중..."):
                                uploaded_url = upload_image(new_upload_file.getvalue(), new_upload_file.name)
                                if uploaded_url:
                                    final_image = uploaded_url
                        elif img_action == "🔗 URL 변경":
                            final_image = new_image_url_input
                        elif img_action == "🗑️ 삭제":
                            final_image = ""
                        
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
                            "google_form_url": ed_form_url,
                            "open_chat_url": ed_chat_url,
                            "external_url": ed_external_url,
                            "external_site_name": ed_external_site,
                            "image_url": final_image,
                            "status": ed_status,
                            "display_order": ed_order,
                        }
                        try:
                            update_job(job['id'], data)
                            st.success("✅ 수정 완료!")
                            st.cache_data.clear()
                            st.rerun()
                        except Exception as e:
                            st.error(f"수정 실패: {e}")
                    
                    if delete_btn:
                        try:
                            delete_job(job['id'])
                            st.success("🗑️ 삭제됨")
                            st.cache_data.clear()
                            st.rerun()
                        except Exception as e:
                            st.error(f"삭제 실패: {e}")

# =============================================================
# TAB 3: 센터 관리
# =============================================================
with tab3:
    st.subheader("🏢 센터 관리")
    st.caption("근무지(센터) 정보를 관리하고, 센터별 FAQ를 등록하세요.")
    
    with st.expander("➕ 새 센터 추가"):
        st.markdown("**🔍 주소 검색 (다음 우편번호 API)**")
        st.caption("정확한 주소를 검색해서 아래 입력 칸에 복사·붙여넣기 하세요!")
        
        st.components.v1.html(daum_postcode_widget(), height=350)
        
        st.markdown("---")
        
        with st.form("new_center_form", clear_on_submit=True):
            col1, col2 = st.columns(2)
            nc_name = col1.text_input("센터 이름 *", placeholder="예: 윌앤비전 강남센터")
            nc_phone = col2.text_input("대표 연락처", placeholder="02-XXX-XXXX")
            
            col1, col2 = st.columns([2, 1])
            nc_address = col1.text_input(
                "주소 *",
                placeholder="예: 서울특별시 강남구 강남대로 123",
                help="🔍 위 '주소 검색하기' 버튼으로 검색 후 복사해서 붙여넣기"
            )
            nc_zonecode = col2.text_input("우편번호", placeholder="12345")
            
            nc_detail = st.text_input("상세 안내", placeholder="예: XX빌딩 5층, 역에서 도보 3분")
            
            col1, col2 = st.columns(2)
            nc_subway = col1.text_input("지하철 정보", placeholder="예: 2호선 강남역 3번 출구")
            nc_bus = col2.text_input("버스 정보", placeholder="예: 강남역 정류장")
            
            nc_desc = st.text_area("센터 설명", placeholder="이 센터에서 운영하는 업무 등")
            
            nc_info_note = st.text_area(
                "📝 센터 고유 정보 (AI 챗봇 참조용)",
                placeholder="휴게실 위치, 주차 정보, 분위기, 복리후생 등",
                height=120,
            )
            
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
                        full_address = nc_address
                        if nc_zonecode:
                            full_address = f"[{nc_zonecode}] {nc_address}"
                        
                        create_center({
                            "name": nc_name,
                            "address": full_address,
                            "detail_address": nc_detail,
                            "phone": nc_phone,
                            "subway_info": nc_subway,
                            "bus_info": nc_bus,
                            "description": nc_desc,
                            "info_note": nc_info_note,
                            "parking_available": nc_parking,
                            "is_active": nc_active,
                            "display_order": nc_order,
                        })
                        st.success("✅ 센터가 등록되었습니다!")
                        st.cache_data.clear()
                        st.rerun()
                    except Exception as e:
                        st.error(f"등록 실패: {e}")
    
    st.divider()
    
    st.markdown("### 📋 등록된 센터")
    centers = get_all_centers()
    
    if not centers:
        st.info("등록된 센터가 없습니다.")
    else:
        for c in centers:
            status_badge = "🟢 활성" if c.get('is_active') else "⚫ 비활성"
            with st.expander(f"**{c['name']}** — {status_badge}", expanded=False):
                
                with st.expander("🗺️ 주소 검색 열기"):
                    st.components.v1.html(daum_postcode_widget(), height=350)
                
                with st.form(f"edit_center_{c['id']}"):
                    col1, col2 = st.columns(2)
                    ec_name = col1.text_input("이름", value=c['name'], key=f"ctr_name_{c['id']}")
                    ec_phone = col2.text_input("연락처", value=c.get('phone') or "", key=f"ctr_phone_{c['id']}")
                    
                    ec_address = st.text_input(
                        "주소",
                        value=c['address'],
                        help="🔍 위 '주소 검색 열기'에서 검색 후 복사해서 붙여넣기",
                        key=f"ctr_addr_{c['id']}"
                    )
                    ec_detail = st.text_input("상세 안내", value=c.get('detail_address') or "", key=f"ctr_detail_{c['id']}")
                    
                    col1, col2 = st.columns(2)
                    ec_subway = col1.text_input("지하철", value=c.get('subway_info') or "", key=f"ctr_subway_{c['id']}")
                    ec_bus = col2.text_input("버스", value=c.get('bus_info') or "", key=f"ctr_bus_{c['id']}")
                    
                    ec_desc = st.text_area("설명", value=c.get('description') or "", key=f"ctr_desc_{c['id']}")
                    
                    ec_info_note = st.text_area(
                        "📝 센터 고유 정보 (AI 챗봇 참조용)",
                        value=c.get('info_note') or "",
                        height=180,
                        key=f"ctr_info_{c['id']}"
                    )
                    
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
                                "info_note": ec_info_note,
                                "parking_available": ec_parking,
                                "is_active": ec_active,
                                "display_order": ec_order,
                            })
                            st.success("✅ 수정 완료!")
                            st.cache_data.clear()
                            st.rerun()
                        except Exception as e:
                            st.error(f"실패: {e}")
                    
                    if delete_btn:
                        try:
                            delete_center(c['id'])
                            st.success("🗑️ 삭제됨")
                            st.cache_data.clear()
                            st.rerun()
                        except Exception as e:
                            st.error(f"실패: {e}")
                
                # 센터별 FAQ
                st.markdown("---")
                st.markdown(f"#### ❓ {c['name']} 전용 FAQ")
                st.caption("이 센터에만 해당하는 질문-답변을 등록하세요")
                
                with st.expander("➕ FAQ 추가"):
                    with st.form(f"new_cfaq_{c['id']}", clear_on_submit=True):
                        cfaq_q = st.text_input("질문", placeholder="예: 주차 가능해요?", key=f"ncf_q_{c['id']}")
                        cfaq_a = st.text_area("답변", placeholder="예: 건물 뒤쪽에 3대 가능", key=f"ncf_a_{c['id']}")
                        cfaq_order = st.number_input("표시 순서", min_value=0, value=99, key=f"ncf_ord_{c['id']}")
                        
                        if st.form_submit_button("💾 등록", type="primary", use_container_width=True):
                            if cfaq_q and cfaq_a:
                                try:
                                    create_center_faq({
                                        "center_id": c['id'],
                                        "question": cfaq_q,
                                        "answer": cfaq_a,
                                        "display_order": cfaq_order,
                                        "is_active": True,
                                    })
                                    st.success("✅ FAQ 등록!")
                                    st.cache_data.clear()
                                    st.rerun()
                                except Exception as e:
                                    st.error(f"실패: {e}")
                
                center_faqs_list = get_all_center_faqs(c['id'])
                if center_faqs_list:
                    for cfaq in center_faqs_list:
                        active_badge = "🟢" if cfaq.get('is_active') else "⚫"
                        with st.container(border=True):
                            st.markdown(f"{active_badge} **Q:** {cfaq['question']}")
                            st.caption(f"**A:** {cfaq['answer']}")
                            
                            col1, col2, col3 = st.columns([1, 1, 4])
                            with col1:
                                if st.button("✏️ 수정", key=f"cf_edit_{cfaq['id']}"):
                                    st.session_state[f"edit_cfaq_{cfaq['id']}"] = True
                                    st.rerun()
                            with col2:
                                if st.button("🗑️", key=f"cf_del_{cfaq['id']}"):
                                    delete_center_faq(cfaq['id'])
                                    st.cache_data.clear()
                                    st.rerun()
                            
                            if st.session_state.get(f"edit_cfaq_{cfaq['id']}"):
                                with st.form(f"edit_cfaq_form_{cfaq['id']}"):
                                    new_q = st.text_input("질문", value=cfaq['question'], key=f"ecf_q_{cfaq['id']}")
                                    new_a = st.text_area("답변", value=cfaq['answer'], key=f"ecf_a_{cfaq['id']}")
                                    new_order = st.number_input("순서", value=cfaq.get('display_order', 0), key=f"ecf_ord_{cfaq['id']}")
                                    new_active = st.checkbox("활성화", value=cfaq.get('is_active', True), key=f"ecf_act_{cfaq['id']}")
                                    
                                    sc1, sc2 = st.columns(2)
                                    if sc1.form_submit_button("💾 저장", type="primary", use_container_width=True):
                                        update_center_faq(cfaq['id'], {
                                            "question": new_q,
                                            "answer": new_a,
                                            "display_order": new_order,
                                            "is_active": new_active,
                                        })
                                        st.session_state[f"edit_cfaq_{cfaq['id']}"] = False
                                        st.cache_data.clear()
                                        st.rerun()
                                    if sc2.form_submit_button("취소", use_container_width=True):
                                        st.session_state[f"edit_cfaq_{cfaq['id']}"] = False
                                        st.rerun()
                else:
                    st.caption("💡 등록된 FAQ가 없습니다.")

# =============================================================
# TAB 4: FAQ 관리
# =============================================================
with tab4:
    st.subheader("❓ 공통 FAQ 관리")
    st.caption("모든 센터에 해당하는 공통 질문-답변. 센터별 FAQ는 '🏢 센터 관리'에서!")
    
    with st.expander("➕ 새 FAQ 추가"):
        with st.form("new_faq_form", clear_on_submit=True):
            col1, col2 = st.columns([1, 2])
            new_category = col1.selectbox("카테고리", ["회사소개", "담당자", "지원방법", "근무조건", "기타"])
            new_order = col2.number_input("표시 순서", min_value=0, value=99)
            
            new_question = st.text_input("질문 *", placeholder="예: 재택근무 가능?")
            new_answer = st.text_area("답변 *")
            
            col1, col2 = st.columns(2)
            new_show_faq = col1.checkbox("메인 FAQ에 표시", value=False, help="메인 페이지에 자주 묻는 질문으로 표시")
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
                        st.cache_data.clear()
                        st.rerun()
                    except Exception as e:
                        st.error(f"실패: {e}")
    
    st.divider()
    
    kb_items = get_all_knowledge()
    if not kb_items:
        st.info("등록된 FAQ가 없습니다.")
    else:
        for item in kb_items:
            with st.expander(f"**[{item.get('category', '기타')}]** {item.get('question', '')[:40]}..."):
                with st.form(f"edit_faq_{item['id']}"):
                    ed_q = st.text_input("질문", value=item.get('question') or "", key=f"faq_q_{item['id']}")
                    ed_a = st.text_area("답변", value=item.get('answer') or "", key=f"faq_a_{item['id']}")
                    
                    col1, col2 = st.columns(2)
                    cat_options = ["회사소개", "담당자", "지원방법", "근무조건", "기타"]
                    ed_cat = col1.selectbox(
                        "카테고리",
                        cat_options,
                        index=cat_options.index(item.get('category')) if item.get('category') in cat_options else 4,
                        key=f"faq_cat_{item['id']}"
                    )
                    ed_order = col2.number_input("순서", min_value=0, value=item.get('display_order') or 0, key=f"faq_ord_{item['id']}")
                    
                    col1, col2 = st.columns(2)
                    ed_show = col1.checkbox("FAQ에 표시", value=item.get('show_in_faq', False), key=f"faq_show_{item['id']}")
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
                        st.cache_data.clear()
                        st.rerun()
                    if delete:
                        delete_knowledge(item['id'])
                        st.cache_data.clear()
                        st.rerun()

# =============================================================
# TAB 5: 사이트 설정
# =============================================================
with tab5:
    st.subheader("⚙️ 사이트 설정")
    
    settings = get_site_settings()
    
    with st.form("settings_form"):
        st.markdown("### 🎨 메인 페이지")
        col1, col2 = st.columns([1, 3])
        new_emoji = col1.text_input("대표 이모지", value=settings.get('hero_emoji', '🤖'))
        new_title = col2.text_input("헤드라인", value=settings.get('hero_title', ''))
        new_subtitle = st.text_input("서브타이틀", value=settings.get('hero_subtitle', ''))
        new_hero_img = st.text_input("상단 이미지 URL", value=settings.get('hero_image_url', ''))
        new_intro = st.text_area("회사 소개", value=settings.get('company_intro', ''))
        
        st.divider()
        st.markdown("### 📞 담당자 정보")
        col1, col2 = st.columns(2)
        new_m_name = col1.text_input("담당자 이름", value=settings.get('manager_name', ''))
        new_m_phone = col2.text_input("담당자 전화번호", value=settings.get('manager_phone', ''))
        new_m_email = st.text_input("담당자 이메일", value=settings.get('manager_email', ''))
        
        st.divider()
        st.markdown("### 🔗 외부 링크")
        new_default_form = st.text_input("기본 구글폼 URL", value=settings.get('default_google_form_url', ''))
        new_openchat = st.text_input("카카오 오픈채팅 URL", value=settings.get('kakao_openchat_url', ''))
        
        st.divider()
        st.markdown("### 🗺️ 기본 사무실 위치")
        new_address = st.text_input("기본 사무실 주소", value=settings.get('office_address', ''))
        
        st.divider()
        st.markdown("### 🛡️ 채용 주의사항")
        new_notice = st.text_area(
            "주의사항 문구",
            value=settings.get('notice_text', ''),
            height=120,
        )
        
        st.divider()
        st.markdown("### 🤖 챗봇 설정")
        
        col1, col2 = st.columns([1, 3])
        new_bot_emoji = col1.text_input("챗봇 이모지", value=settings.get('chatbot_emoji', '🤖'))
        new_bot_name = col2.text_input("챗봇 이름", value=settings.get('chatbot_name', '윌비봇'))
        
        new_greeting = st.text_input("메인 인사말", value=settings.get('chatbot_greeting', ''))
        new_sub_greeting = st.text_input("서브 인사말", value=settings.get('chatbot_sub_greeting', ''))
        
        col1, col2 = st.columns(2)
        new_placeholder = col1.text_input("입력창 안내", value=settings.get('chatbot_placeholder', ''))
        new_empty_msg = col2.text_input("빈 대화 문구", value=settings.get('chatbot_empty_msg', ''))
        
        new_thinking_msg = st.text_input("답변 대기 문구", value=settings.get('chatbot_thinking_msg', ''))
        
        st.markdown("**💡 추천 질문**")
        col1, col2 = st.columns(2)
        new_sug_q1 = col1.text_input("추천 질문 1", value=settings.get('suggested_q_1', ''))
        new_sug_q2 = col2.text_input("추천 질문 2", value=settings.get('suggested_q_2', ''))
        col1, col2 = st.columns(2)
        new_sug_q3 = col1.text_input("추천 질문 3", value=settings.get('suggested_q_3', ''))
        new_sug_q4 = col2.text_input("추천 질문 4", value=settings.get('suggested_q_4', ''))
        
        tone_options = ["friendly", "casual", "formal"]
        new_tone = st.selectbox(
            "말투 스타일",
            tone_options,
            format_func=lambda x: {"friendly": "😊 친근하게", "casual": "🙌 편하게", "formal": "🎩 격식있게"}[x],
            index=tone_options.index(settings.get('chatbot_tone', 'friendly')) if settings.get('chatbot_tone', 'friendly') in tone_options else 0
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
                'notice_text': new_notice,
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
            }
            try:
                for k, v in updates.items():
                    update_setting(k, v)
                st.success("✅ 모든 설정이 저장되었습니다!")
                st.cache_data.clear()
                st.rerun()
            except Exception as e:
                st.error(f"저장 실패: {e}")

# =============================================================
# TAB 6: 대화 기록
# =============================================================
with tab6:
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
        
        show_only_needs_human = st.checkbox("⚠️ 담당자 연결 필요한 것만")
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
