import streamlit as st
from supabase import create_client, Client
from datetime import datetime
import uuid


# ============ Supabase 연결 ============

@st.cache_resource
def get_supabase() -> Client:
    url = st.secrets["SUPABASE_URL"]
    key = st.secrets["SUPABASE_ANON_KEY"]
    return create_client(url, key)


@st.cache_resource
def get_supabase_admin() -> Client:
    url = st.secrets["SUPABASE_URL"]
    key = st.secrets["SUPABASE_SERVICE_KEY"]
    return create_client(url, key)


# ============ 사이트 설정 (site_settings) ============

@st.cache_data(ttl=60)
def get_site_settings():
    """모든 사이트 설정을 dict로 반환"""
    sb = get_supabase()
    res = sb.table("site_settings").select("*").execute()
    return {row['key']: row['value'] for row in res.data}


def get_setting(key, default=""):
    """개별 설정값 조회"""
    settings = get_site_settings()
    return settings.get(key, default)


def update_setting(key, value):
    """설정값 업데이트 (관리자)"""
    sb = get_supabase_admin()
    sb.table("site_settings").update({
        "value": value,
        "updated_at": datetime.now().isoformat()
    }).eq("key", key).execute()
    st.cache_data.clear()


# ============ 공고 (jobs) ============

def get_active_jobs():
    """모집중인 공고 조회"""
    sb = get_supabase()
    res = sb.table("jobs").select("*").eq("status", "모집중").order("display_order").execute()
    return res.data


def get_all_jobs():
    """전체 공고 조회 (관리자)"""
    sb = get_supabase_admin()
    res = sb.table("jobs").select("*").order("display_order").execute()
    return res.data


def get_job(job_id):
    """단일 공고 조회"""
    sb = get_supabase()
    res = sb.table("jobs").select("*").eq("id", job_id).execute()
    return res.data[0] if res.data else None


def create_job(data):
    """새 공고 추가 (관리자)"""
    sb = get_supabase_admin()
    sb.table("jobs").insert(data).execute()


def update_job(job_id, data):
    """공고 수정 (관리자)"""
    sb = get_supabase_admin()
    sb.table("jobs").update(data).eq("id", job_id).execute()


def delete_job(job_id):
    """공고 삭제 (관리자)"""
    sb = get_supabase_admin()
    sb.table("jobs").delete().eq("id", job_id).execute()


def update_job_status(job_id, new_status):
    sb = get_supabase_admin()
    sb.table("jobs").update({"status": new_status}).eq("id", job_id).execute()


def increment_job_view(job_id, session_id=None):
    """공고 조회수 증가"""
    try:
        sb = get_supabase()
        if session_id:
            sb.table("job_views").insert({
                "job_id": job_id,
                "session_id": session_id
            }).execute()
        # view_count 증가는 별도 쿼리
        job = get_job(job_id)
        if job:
            new_count = (job.get('view_count') or 0) + 1
            sb.table("jobs").update({"view_count": new_count}).eq("id", job_id).execute()
    except Exception:
        pass  # 조회수 실패는 무시


# ============ FAQ / Knowledge Base ============

def get_knowledge_base():
    sb = get_supabase()
    res = sb.table("knowledge_base").select("*").eq("is_active", True).order("display_order").execute()
    return res.data


def get_all_knowledge():
    """관리자용"""
    sb = get_supabase_admin()
    res = sb.table("knowledge_base").select("*").order("display_order").execute()
    return res.data


def get_faq_items():
    """FAQ에 보여줄 항목만"""
    sb = get_supabase()
    res = sb.table("knowledge_base").select("*").eq("is_active", True).eq("show_in_faq", True).order("display_order").execute()
    return res.data


def create_knowledge(data):
    sb = get_supabase_admin()
    sb.table("knowledge_base").insert(data).execute()


def update_knowledge(kb_id, data):
    sb = get_supabase_admin()
    sb.table("knowledge_base").update(data).eq("id", kb_id).execute()


def delete_knowledge(kb_id):
    sb = get_supabase_admin()
    sb.table("knowledge_base").delete().eq("id", kb_id).execute()


# ============ 대화 기록 (conversations) ============

def save_conversation(session_id, question, answer, related_job_id=None, needs_human=False):
    try:
        sb = get_supabase()
        sb.table("conversations").insert({
            "session_id": session_id,
            "user_question": question,
            "ai_answer": answer,
            "related_job_id": related_job_id,
            "needs_human": needs_human,
        }).execute()
    except Exception as e:
        print(f"대화 저장 실패: {e}")


def get_all_conversations():
    sb = get_supabase_admin()
    res = sb.table("conversations").select("*, jobs(title)").order("created_at", desc=True).execute()
    return res.data


# ============ 지원자 (applicants) — 호환성 유지 ============

def save_applicant(name, phone, job_id, job_title, experience, introduction):
    sb = get_supabase()
    sb.table("applicants").insert({
        "name": name,
        "phone": phone,
        "job_id": job_id,
        "job_title_snapshot": job_title,
        "experience": experience,
        "introduction": introduction,
    }).execute()


def get_all_applicants():
    sb = get_supabase_admin()
    res = sb.table("applicants").select("*, jobs(title)").order("created_at", desc=True).execute()
    return res.data


def update_applicant_status(applicant_id, new_status, memo=""):
    sb = get_supabase_admin()
    update_data = {"status": new_status}
    if memo:
        update_data["memo"] = memo
    sb.table("applicants").update(update_data).eq("id", applicant_id).execute()


# ============ 이미지 업로드 (Supabase Storage) ============

def upload_image(file_bytes, filename):
    """이미지 파일을 Supabase Storage에 업로드 → URL 반환"""
    try:
        sb = get_supabase()
        # 파일명에 UUID 붙여서 중복 방지
        unique_name = f"{uuid.uuid4().hex[:8]}_{filename}"
        sb.storage.from_("job-images").upload(
            unique_name,
            file_bytes,
            file_options={"content-type": "image/jpeg"}
        )
        # Public URL 생성
        public_url = sb.storage.from_("job-images").get_public_url(unique_name)
        return public_url
    except Exception as e:
        st.error(f"이미지 업로드 실패: {e}")
        return None


def delete_image(image_url):
    """이미지 삭제"""
    try:
        sb = get_supabase()
        # URL에서 파일명 추출
        filename = image_url.split("/")[-1].split("?")[0]
        sb.storage.from_("job-images").remove([filename])
        return True
    except Exception as e:
        print(f"이미지 삭제 실패: {e}")
        return False


# ============ 통계 (관리자 대시보드용) ============

def get_stats():
    """전체 통계"""
    sb = get_supabase_admin()
    
    # 공고 수
    jobs_active = len([j for j in sb.table("jobs").select("id").eq("status", "모집중").execute().data])
    jobs_total = len(sb.table("jobs").select("id").execute().data)
    
    # 대화 수
    conversations = sb.table("conversations").select("session_id, needs_human").execute().data
    total_conversations = len(conversations)
    unique_visitors = len(set(c['session_id'] for c in conversations))
    needs_human_count = sum(1 for c in conversations if c['needs_human'])
    
    # 지원자 수
    applicants_total = len(sb.table("applicants").select("id").execute().data)
    
    return {
        "jobs_active": jobs_active,
        "jobs_total": jobs_total,
        "total_conversations": total_conversations,
        "unique_visitors": unique_visitors,
        "needs_human_count": needs_human_count,
        "applicants_total": applicants_total,
    }


def get_popular_jobs(limit=5):
    """인기 공고 (조회수 순)"""
    sb = get_supabase_admin()
    res = sb.table("jobs").select("*").order("view_count", desc=True).limit(limit).execute()
    return res.data
