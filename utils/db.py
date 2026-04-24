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
    # ============ 지하철 역 정보 (거리 계산용) ============

def get_subway_stations():
    """
    서울 2호선 주요 역 좌표 (대표 역들만)
    실제 서비스에선 공공 API 쓰면 좋지만, 간단히 내장 데이터로.
    """
    return {
        # 2호선 (본선)
        "시청": (37.5637, 126.9754),
        "을지로입구": (37.5660, 126.9826),
        "을지로3가": (37.5660, 126.9918),
        "을지로4가": (37.5664, 126.9984),
        "동대문역사문화공원": (37.5652, 127.0084),
        "신당": (37.5654, 127.0177),
        "상왕십리": (37.5643, 127.0290),
        "왕십리": (37.5614, 127.0374),
        "한양대": (37.5554, 127.0435),
        "뚝섬": (37.5472, 127.0473),
        "성수": (37.5446, 127.0557),
        "건대입구": (37.5403, 127.0698),
        "구의": (37.5373, 127.0856),
        "강변": (37.5353, 127.0948),
        "잠실나루": (37.5201, 127.1036),
        "잠실": (37.5133, 127.1000),
        "잠실새내": (37.5114, 127.0862),
        "종합운동장": (37.5109, 127.0733),
        "삼성": (37.5087, 127.0631),
        "선릉": (37.5044, 127.0489),
        "역삼": (37.5003, 127.0367),
        "강남": (37.4979, 127.0275),
        "교대": (37.4935, 127.0142),
        "서초": (37.4914, 127.0079),
        "방배": (37.4811, 126.9975),
        "사당": (37.4765, 126.9814),
        "낙성대": (37.4764, 126.9638),
        "서울대입구": (37.4812, 126.9529),
        "봉천": (37.4826, 126.9419),
        "신림": (37.4843, 126.9294),
        "신대방": (37.4873, 126.9131),
        "구로디지털단지": (37.4851, 126.9016),
        "대림": (37.4925, 126.8953),
        "신도림": (37.5088, 126.8916),
        "문래": (37.5178, 126.8944),
        "영등포구청": (37.5247, 126.8962),
        "당산": (37.5344, 126.9020),
        "합정": (37.5497, 126.9140),
        "홍대입구": (37.5571, 126.9240),
        "신촌": (37.5551, 126.9368),
        "이대": (37.5568, 126.9458),
        "아현": (37.5574, 126.9559),
        "충정로": (37.5598, 126.9638),
        # 1호선 주요
        "서울역": (37.5546, 126.9706),
        "종각": (37.5702, 126.9828),
        "종로3가": (37.5714, 126.9918),
        "종로5가": (37.5707, 127.0020),
        "동대문": (37.5714, 127.0098),
        "청량리": (37.5803, 127.0465),
        "용산": (37.5297, 126.9647),
        "노량진": (37.5143, 126.9421),
        "영등포": (37.5159, 126.9076),
        "구로": (37.5031, 126.8820),
        # 3호선 주요
        "고속터미널": (37.5045, 127.0049),
        "경복궁": (37.5759, 126.9736),
        "안국": (37.5764, 126.9852),
        "옥수": (37.5404, 127.0177),
        # 4호선 주요
        "혜화": (37.5824, 127.0018),
        "명동": (37.5635, 126.9863),
        "삼각지": (37.5345, 126.9732),
        "숙대입구": (37.5446, 126.9714),
        # 5호선 주요
        "광화문": (37.5718, 126.9766),
        "여의도": (37.5217, 126.9240),
        # 7호선 주요
        "상봉": (37.5961, 127.0858),
        "건대입구": (37.5403, 127.0698),
        "반포": (37.5064, 127.0118),
        "남구로": (37.4867, 126.8878),
        # 9호선 주요
        "국회의사당": (37.5287, 126.9179),
        "여의도": (37.5217, 126.9240),
    }


def calculate_distance_km(lat1, lng1, lat2, lng2):
    """두 좌표 사이 직선거리 (km) - Haversine 공식"""
    from math import radians, sin, cos, sqrt, atan2
    
    R = 6371  # 지구 반지름 (km)
    lat1, lng1, lat2, lng2 = map(radians, [lat1, lng1, lat2, lng2])
    
    dlat = lat2 - lat1
    dlng = lng2 - lng1
    
    a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlng/2)**2
    c = 2 * atan2(sqrt(a), sqrt(1-a))
    
    return R * c
# ============ 센터 관리 ============

def get_active_centers():
    """활성 센터 목록"""
    sb = get_supabase()
    res = sb.table("centers").select("*").eq("is_active", True).order("display_order").execute()
    return res.data


def get_all_centers():
    """전체 센터 (관리자용)"""
    sb = get_supabase_admin()
    res = sb.table("centers").select("*").order("display_order").execute()
    return res.data


def get_center(center_id):
    """단일 센터 조회"""
    sb = get_supabase()
    res = sb.table("centers").select("*").eq("id", center_id).execute()
    return res.data[0] if res.data else None


def create_center(data):
    sb = get_supabase_admin()
    sb.table("centers").insert(data).execute()


def update_center(center_id, data):
    sb = get_supabase_admin()
    sb.table("centers").update(data).eq("id", center_id).execute()


def delete_center(center_id):
    sb = get_supabase_admin()
    sb.table("centers").delete().eq("id", center_id).execute()


def get_jobs_by_center(center_id):
    """특정 센터의 공고 조회"""
    sb = get_supabase()
    res = sb.table("jobs").select("*").eq("center_id", center_id).eq("status", "모집중").execute()
    return res.data


def get_active_jobs_with_center():
    """공고 + 센터 정보 조인"""
    sb = get_supabase()
    res = sb.table("jobs").select("*, centers(id, name, address, subway_info)").eq("status", "모집중").order("display_order").execute()
    return res.data
# ============ 지원 클릭 추적 ============

def increment_job_apply(job_id, session_id=None):
    """지원하기 버튼 클릭 기록"""
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
