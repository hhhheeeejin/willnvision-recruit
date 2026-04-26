import streamlit as st
from supabase import create_client
from datetime import datetime
import uuid


@st.cache_resource
def get_supabase():
    """일반 사용자용 (anon key)"""
    url = st.secrets["SUPABASE_URL"]
    key = st.secrets["SUPABASE_ANON_KEY"]
    return create_client(url, key)


@st.cache_resource
def get_supabase_admin():
    """관리자용 (service key)"""
    url = st.secrets["SUPABASE_URL"]
    key = st.secrets["SUPABASE_SERVICE_KEY"]
    return create_client(url, key)


# ============ 공고 (Jobs) ============

def get_active_jobs():
    sb = get_supabase()
    res = sb.table("jobs").select("*").eq("status", "모집중").order("display_order").execute()
    return res.data


def get_active_jobs_with_center():
    """공고 + 연결된 센터 정보까지"""
    sb = get_supabase()
    res = sb.table("jobs").select("*, centers(*)").eq("status", "모집중").order("display_order").execute()
    return res.data


def get_all_jobs():
    sb = get_supabase_admin()
    res = sb.table("jobs").select("*").order("display_order").execute()
    return res.data


def get_job(job_id):
    sb = get_supabase()
    res = sb.table("jobs").select("*").eq("id", job_id).single().execute()
    return res.data


def create_job(data):
    sb = get_supabase_admin()
    sb.table("jobs").insert(data).execute()


def update_job(job_id, data):
    sb = get_supabase_admin()
    sb.table("jobs").update(data).eq("id", job_id).execute()


def delete_job(job_id):
    sb = get_supabase_admin()
    sb.table("jobs").delete().eq("id", job_id).execute()


def update_job_status(job_id, status):
    sb = get_supabase_admin()
    sb.table("jobs").update({"status": status}).eq("id", job_id).execute()


# ============ 조회/지원 추적 ============

def increment_job_view(job_id, session_id=None):
    """공고 문의 클릭 추적"""
    try:
        sb = get_supabase()
        if session_id:
            sb.table("job_views").insert({
                "job_id": job_id,
                "session_id": session_id
            }).execute()
        job = get_job(job_id)
        if job:
            new_count = (job.get('view_count') or 0) + 1
            sb.table("jobs").update({"view_count": new_count}).eq("id", job_id).execute()
    except Exception:
        pass


def increment_job_apply(job_id, session_id=None):
    """공고 지원 클릭 추적"""
    try:
        sb = get_supabase()
        if session_id:
            sb.table("job_apply_clicks").insert({
                "job_id": job_id,
                "session_id": session_id
            }).execute()
        job = get_job(job_id)
        if job:
            new_count = (job.get('apply_count') or 0) + 1
            sb.table("jobs").update({"apply_count": new_count}).eq("id", job_id).execute()
    except Exception:
        pass


def get_popular_jobs(limit=5):
    sb = get_supabase_admin()
    res = sb.table("jobs").select("*").order("view_count", desc=True).limit(limit).execute()
    return res.data


# ============ 센터 (Centers) ============

def get_active_centers():
    sb = get_supabase()
    res = sb.table("centers").select("*").eq("is_active", True).order("display_order").execute()
    return res.data


def get_all_centers():
    sb = get_supabase_admin()
    res = sb.table("centers").select("*").order("display_order").execute()
    return res.data


def get_center(center_id):
    sb = get_supabase()
    res = sb.table("centers").select("*").eq("id", center_id).single().execute()
    return res.data


def create_center(data):
    sb = get_supabase_admin()
    sb.table("centers").insert(data).execute()


def update_center(center_id, data):
    sb = get_supabase_admin()
    sb.table("centers").update(data).eq("id", center_id).execute()


def delete_center(center_id):
    sb = get_supabase_admin()
    sb.table("centers").delete().eq("id", center_id).execute()


# ============ 센터별 FAQ ============

def get_center_faqs(center_id):
    """특정 센터의 활성 FAQ만 조회 (챗봇용)"""
    sb = get_supabase()
    res = sb.table("center_faqs").select("*").eq("center_id", center_id).eq("is_active", True).order("display_order").execute()
    return res.data


def get_all_center_faqs(center_id):
    """관리자용 - 전체 조회 (비활성 포함)"""
    sb = get_supabase_admin()
    res = sb.table("center_faqs").select("*").eq("center_id", center_id).order("display_order").execute()
    return res.data


def create_center_faq(data):
    sb = get_supabase_admin()
    sb.table("center_faqs").insert(data).execute()


def update_center_faq(faq_id, data):
    sb = get_supabase_admin()
    sb.table("center_faqs").update(data).eq("id", faq_id).execute()


def delete_center_faq(faq_id):
    sb = get_supabase_admin()
    sb.table("center_faqs").delete().eq("id", faq_id).execute()


# ============ 지원자 (Applicants) - 사용 안함, 구글폼 대체 ============

def get_all_applicants():
    sb = get_supabase_admin()
    res = sb.table("applicants").select("*").order("created_at", desc=True).execute()
    return res.data


def update_applicant_status(applicant_id, status):
    sb = get_supabase_admin()
    sb.table("applicants").update({"status": status}).eq("id", applicant_id).execute()


# ============ 대화 기록 (Conversations) ============

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
    except Exception:
        pass


def get_all_conversations():
    sb = get_supabase_admin()
    res = sb.table("conversations").select("*, jobs(title)").order("created_at", desc=True).execute()
    return res.data


# ============ FAQ / 지식 베이스 (Knowledge Base) ============

def get_knowledge_base():
    """챗봇이 참조하는 전체 지식"""
    sb = get_supabase()
    res = sb.table("knowledge_base").select("*").eq("is_active", True).order("display_order").execute()
    return res.data


def get_faq_items():
    """메인 페이지에 표시되는 FAQ"""
    sb = get_supabase()
    res = sb.table("knowledge_base").select("*").eq("is_active", True).eq("show_in_faq", True).order("display_order").execute()
    return res.data


def get_all_knowledge():
    sb = get_supabase_admin()
    res = sb.table("knowledge_base").select("*").order("display_order").execute()
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


# ============ 사이트 설정 (Site Settings) ============

def get_site_settings():
    sb = get_supabase()
    res = sb.table("site_settings").select("*").execute()
    return {item['key']: item['value'] for item in res.data}


def update_setting(key, value):
    sb = get_supabase_admin()
    existing = sb.table("site_settings").select("*").eq("key", key).execute()
    if existing.data:
        sb.table("site_settings").update({"value": value}).eq("key", key).execute()
    else:
        sb.table("site_settings").insert({"key": key, "value": value}).execute()


# ============ 이미지 업로드 (Storage) ============

def upload_image(file_bytes, filename):
    try:
        sb = get_supabase_admin()
        ext = filename.split('.')[-1]
        unique_name = f"{uuid.uuid4()}.{ext}"
        sb.storage.from_("job-images").upload(unique_name, file_bytes)
        url = sb.storage.from_("job-images").get_public_url(unique_name)
        return url
    except Exception as e:
        print(f"Upload error: {e}")
        return None


def delete_image(url):
    try:
        sb = get_supabase_admin()
        filename = url.split('/')[-1].split('?')[0]
        sb.storage.from_("job-images").remove([filename])
    except Exception:
        pass


# ============ 통계 (Stats) ============

def get_stats():
    sb = get_supabase_admin()
    
    jobs_total = sb.table("jobs").select("id", count="exact").execute()
    jobs_active = sb.table("jobs").select("id", count="exact").eq("status", "모집중").execute()
    
    conversations = sb.table("conversations").select("session_id, needs_human").execute()
    total_conv = len(conversations.data)
    unique_sess = len(set(c['session_id'] for c in conversations.data))
    needs_human = sum(1 for c in conversations.data if c['needs_human'])
    
    try:
        applicants = sb.table("applicants").select("id", count="exact").execute()
        applicants_total = applicants.count
    except Exception:
        applicants_total = 0
    
    return {
        'jobs_total': jobs_total.count,
        'jobs_active': jobs_active.count,
        'total_conversations': total_conv,
        'unique_visitors': unique_sess,
        'needs_human_count': needs_human,
        'applicants_total': applicants_total,
    }

# ============ 이미지 업로드 (Supabase Storage) ============

def upload_image(file_bytes, filename):
    """
    이미지 파일을 Supabase Storage의 job-images 버킷에 업로드
    """
    try:
        sb = get_supabase_admin()
        ext = filename.rsplit('.', 1)[-1].lower() if '.' in filename else 'jpg'
        unique_name = f"{uuid.uuid4()}.{ext}"
        
        sb.storage.from_("job-images").upload(
            unique_name, 
            file_bytes,
            file_options={"content-type": f"image/{ext}"}
        )
        
        url = sb.storage.from_("job-images").get_public_url(unique_name)
        return url
    
    except Exception as e:
        print(f"❌ 이미지 업로드 실패: {e}")
        return None


def delete_image(url):
    """이미지 삭제"""
    try:
        sb = get_supabase_admin()
        filename = url.split('/')[-1].split('?')[0]
        sb.storage.from_("job-images").remove([filename])
        return True
    except Exception:
        return False
