import streamlit as st
from supabase import create_client, Client


@st.cache_resource
def get_supabase() -> Client:
    """일반 사용자용 (anon key)"""
    url = st.secrets["SUPABASE_URL"]
    key = st.secrets["SUPABASE_ANON_KEY"]
    return create_client(url, key)


@st.cache_resource
def get_supabase_admin() -> Client:
    """관리자용 (service_role key)"""
    url = st.secrets["SUPABASE_URL"]
    key = st.secrets["SUPABASE_SERVICE_KEY"]
    return create_client(url, key)


def get_active_jobs():
    sb = get_supabase()
    res = sb.table("jobs").select("*").eq("status", "모집중").order("display_order").execute()
    return res.data


def get_all_jobs():
    sb = get_supabase_admin()
    res = sb.table("jobs").select("*").order("display_order").execute()
    return res.data


def get_knowledge_base():
    sb = get_supabase()
    res = sb.table("knowledge_base").select("*").eq("is_active", True).execute()
    return res.data


def save_conversation(session_id, question, answer, related_job_id=None, needs_human=False):
    sb = get_supabase()
    sb.table("conversations").insert({
        "session_id": session_id,
        "user_question": question,
        "ai_answer": answer,
        "related_job_id": related_job_id,
        "needs_human": needs_human,
    }).execute()


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


def get_all_conversations():
    sb = get_supabase_admin()
    res = sb.table("conversations").select("*, jobs(title)").order("created_at", desc=True).execute()
    return res.data


def get_all_applicants():
    sb = get_supabase_admin()
    res = sb.table("applicants").select("*, jobs(title)").order("created_at", desc=True).execute()
    return res.data


def update_job_status(job_id, new_status):
    sb = get_supabase_admin()
    sb.table("jobs").update({"status": new_status}).eq("id", job_id).execute()


def update_applicant_status(applicant_id, new_status, memo=""):
    sb = get_supabase_admin()
    update_data = {"status": new_status}
    if memo:
        update_data["memo"] = memo
    sb.table("applicants").update(update_data).eq("id", applicant_id).execute()
