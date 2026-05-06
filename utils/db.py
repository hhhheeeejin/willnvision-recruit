import streamlit as st
from supabase import create_client, Client
from datetime import datetime
import uuid


# ============ Supabase 클라이언트 ============

def get_supabase() -> Client:
    """일반 사용자용 (anon key)"""
    url = st.secrets["SUPABASE_URL"]
    key = st.secrets["SUPABASE_ANON_KEY"]
    return create_client(url, key)


def get_supabase_admin() -> Client:
    """관리자용 (service key)"""
    url = st.secrets["SUPABASE_URL"]
    key = st.secrets.get("SUPABASE_SERVICE_KEY", st.secrets["SUPABASE_ANON_KEY"])
    return create_client(url, key)


# ============ 사이트 설정 ============

def get_site_settings():
    try:
        sb = get_supabase()
        res = sb.table("site_settings").select("*").execute()
        return {item["key"]: item["value"] for item in res.data}
    except Exception as e:
        print(f"설정 로드 실패: {e}")
        return {}


def update_setting(key, value):
    try:
        sb = get_supabase_admin()
        existing = sb.table("site_settings").select("*").eq("key", key).execute()
        if existing.data:
            sb.table("site_settings").update({"value": value}).eq("key", key).execute()
        else:
            sb.table("site_settings").insert({"key": key, "value": value}).execute()
        return True
    except Exception as e:
        print(f"설정 저장 실패: {e}")
        return False


# ============ 공고 ============

def get_active_jobs():
    try:
        sb = get_supabase()
        res = sb.table("jobs").select("*").eq("status", "모집중").order("display_order").execute()
        return res.data or []
    except Exception as e:
        print(f"공고 로드 실패: {e}")
        return []


def get_active_jobs_with_center():
    try:
        sb = get_supabase()
        res = sb.table("jobs").select("*, centers(*)").in_("status", ["모집중", "재오픈예정"]).order("display_order").execute()
        return res.data or []
    except Exception as e:
        print(f"공고+센터 로드 실패: {e}")
        return []


def get_all_jobs():
    try:
        sb = get_supabase_admin()
        res = sb.table("jobs").select("*, centers(*)").order("display_order").execute()
        return res.data or []
    except Exception as e:
        print(f"전체 공고 로드 실패: {e}")
        return []


def create_job(data):
    sb = get_supabase_admin()
    sb.table("jobs").insert(data).execute()


def update_job(job_id, data):
    sb = get_supabase_admin()
    sb.table("jobs").update(data).eq("id", job_id).execute()


def delete_job(job_id):
    sb = get_supabase_admin()
    sb.table("jobs").delete().eq("id", job_id).execute()


def increment_job_view(job_id, session_id):
    try:
        sb = get_supabase()
        sb.table("job_views").insert({
            "job_id": job_id,
            "session_id": session_id,
        }).execute()
    except Exception as e:
        print(f"view 기록 실패: {e}")
    
    try:
        sb_admin = get_supabase_admin()
        current = sb_admin.table("jobs").select("view_count").eq("id", job_id).execute()
        if current.data:
            new_count = (current.data[0].get("view_count") or 0) + 1
            sb_admin.table("jobs").update({"view_count": new_count}).eq("id", job_id).execute()
    except Exception as e:
        print(f"view 카운트 실패: {e}")


def increment_job_apply(job_id, session_id):
    try:
        sb = get_supabase()
        sb.table("job_apply_clicks").insert({
            "job_id": job_id,
            "session_id": session_id,
        }).execute()
    except Exception as e:
        print(f"apply 기록 실패: {e}")
    
    try:
        sb_admin = get_supabase_admin()
        current = sb_admin.table("jobs").select("apply_count").eq("id", job_id).execute()
        if current.data:
            new_count = (current.data[0].get("apply_count") or 0) + 1
            sb_admin.table("jobs").update({"apply_count": new_count}).eq("id", job_id).execute()
    except Exception as e:
        print(f"apply 카운트 실패: {e}")


# ============ 센터 ============

def get_active_centers():
    try:
        sb = get_supabase()
        res = sb.table("centers").select("*").eq("is_active", True).order("display_order").execute()
        return res.data or []
    except Exception as e:
        print(f"센터 로드 실패: {e}")
        return []


def get_all_centers():
    try:
        sb = get_supabase_admin()
        res = sb.table("centers").select("*").order("display_order").execute()
        return res.data or []
    except Exception as e:
        print(f"전체 센터 로드 실패: {e}")
        return []


def create_center(data):
    sb = get_supabase_admin()
    sb.table("centers").insert(data).execute()


def update_center(center_id, data):
    sb = get_supabase_admin()
    sb.table("centers").update(data).eq("id", center_id).execute()


def delete_center(center_id):
    sb = get_supabase_admin()
    sb.table("centers").delete().eq("id", center_id).execute()


# ============ 센터 FAQ ============

def get_center_faqs(center_id):
    try:
        sb = get_supabase()
        res = sb.table("center_faqs").select("*").eq("center_id", center_id).eq("is_active", True).order("display_order").execute()
        return res.data or []
    except Exception as e:
        print(f"센터 FAQ 로드 실패: {e}")
        return []


def get_all_center_faqs(center_id):
    try:
        sb = get_supabase_admin()
        res = sb.table("center_faqs").select("*").eq("center_id", center_id).order("display_order").execute()
        return res.data or []
    except Exception as e:
        return []


def create_center_faq(data):
    sb = get_supabase_admin()
    sb.table("center_faqs").insert(data).execute()


def update_center_faq(faq_id, data):
    sb = get_supabase_admin()
    sb.table("center_faqs").update(data).eq("id", faq_id).execute()


def delete_center_faq(faq_id):
    sb = get_supabase_admin()
    sb.table("center_faqs").delete().eq("id", faq_id).execute()


# ============ 공통 FAQ ============

def get_knowledge_base():
    try:
        sb = get_supabase()
        res = sb.table("knowledge_base").select("*").eq("is_active", True).order("display_order").execute()
        return res.data or []
    except Exception as e:
        return []


def get_faq_items():
    try:
        sb = get_supabase()
        res = sb.table("knowledge_base").select("*").eq("is_active", True).eq("show_in_faq", True).order("display_order").execute()
        return res.data or []
    except Exception as e:
        return []


def get_all_knowledge():
    try:
        sb = get_supabase_admin()
        res = sb.table("knowledge_base").select("*").order("display_order").execute()
        return res.data or []
    except Exception as e:
        return []


def create_knowledge(data):
    sb = get_supabase_admin()
    sb.table("knowledge_base").insert(data).execute()


def update_knowledge(item_id, data):
    sb = get_supabase_admin()
    sb.table("knowledge_base").update(data).eq("id", item_id).execute()


def delete_knowledge(item_id):
    sb = get_supabase_admin()
    sb.table("knowledge_base").delete().eq("id", item_id).execute()


# ============ 대화 기록 ============

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
        return True
    except Exception as e:
        print(f"대화 저장 실패: {e}")
        return False


def get_all_conversations():
    try:
        sb = get_supabase_admin()
        res = sb.table("conversations").select("*, jobs(title)").order("created_at", desc=True).execute()
        return res.data or []
    except Exception as e:
        return []


# ============ 통계 ============

def get_stats():
    try:
        sb = get_supabase_admin()
        
        all_jobs = sb.table("jobs").select("id, status").execute()
        jobs_total = len(all_jobs.data) if all_jobs.data else 0
        jobs_active = sum(1 for j in (all_jobs.data or []) if j.get("status") == "모집중")
        
        convs = sb.table("conversations").select("session_id, needs_human").execute()
        total_conv = len(convs.data) if convs.data else 0
        unique_sessions = len(set(c["session_id"] for c in (convs.data or [])))
        needs_human = sum(1 for c in (convs.data or []) if c.get("needs_human"))
        
        return {
            "jobs_total": jobs_total,
            "jobs_active": jobs_active,
            "total_conversations": total_conv,
            "unique_visitors": unique_sessions,
            "needs_human_count": needs_human,
        }
    except Exception as e:
        print(f"통계 실패: {e}")
        return {
            "jobs_total": 0, "jobs_active": 0,
            "total_conversations": 0, "unique_visitors": 0,
            "needs_human_count": 0,
        }


def get_popular_jobs(limit=5):
    try:
        sb = get_supabase_admin()
        res = sb.table("jobs").select("*").order("view_count", desc=True).limit(limit).execute()
        return res.data or []
    except Exception as e:
        return []


# ============ 이미지 업로드 ============

def upload_image(file_bytes, filename):
    try:
        sb = get_supabase_admin()
        clean_filename = "".join(c if c.isalnum() or c in "._-" else "_" for c in filename)
        unique_filename = f"{datetime.now().strftime('%Y%m%d%H%M%S')}_{uuid.uuid4().hex[:8]}_{clean_filename}"
        
        sb.storage.from_("job-images").upload(
            unique_filename,
            file_bytes,
            file_options={"content-type": "image/jpeg"}
        )
        
        public_url = sb.storage.from_("job-images").get_public_url(unique_filename)
        return public_url
    except Exception as e:
        print(f"이미지 업로드 실패: {e}")
        return None


def delete_image(image_url):
    try:
        if not image_url or "job-images" not in image_url:
            return False
        filename = image_url.split("job-images/")[-1].split("?")[0]
        sb = get_supabase_admin()
        sb.storage.from_("job-images").remove([filename])
        return True
    except Exception as e:
        print(f"이미지 삭제 실패: {e}")
        return False


# ============ 출근거리 검색 기록 ============

def save_commute_search(session_id, start_address, center_id, center_name, transport_type):
    try:
        region = extract_region(start_address)
        sb = get_supabase()
        sb.table("commute_searches").insert({
            "session_id": session_id,
            "start_address": start_address,
            "center_id": center_id,
            "center_name": center_name,
            "transport_type": transport_type,
            "region": region,
        }).execute()
        return True
    except Exception as e:
        print(f"출근거리 기록 실패: {e}")
        return False


def extract_region(address):
    if not address:
        return "기타"
    
    addr = address.strip()
    
    region_map = {
        '서울': ['서울', '강남', '강북', '마포', '용산', '종로', '성동', '광진', '동대문',
                '중랑', '성북', '도봉', '노원', '은평', '서대문', '양천', '강서', '구로',
                '금천', '영등포', '동작', '관악', '서초', '송파', '강동',
                '홍대', '신촌', '잠실', '여의도', '문래', '당산'],
        '경기': ['경기', '고양', '성남', '수원', '용인', '안양', '안산', '부천', '광명',
                '평택', '시흥', '김포', '의정부', '하남', '구리', '남양주', '오산',
                '이천', '안성', '의왕', '양주', '동두천', '과천', '여주', '포천',
                '가평', '양평', '화성', '파주', '군포'],
        '인천': ['인천', '부평', '계양', '연수', '남동', '강화', '옹진'],
        '부산': ['부산', '해운대', '수영', '동래', '연제', '부산진', '사하', '사상',
                '금정', '기장'],
        '대구': ['대구', '달서', '달성', '수성'],
        '광주': ['광주광역시'],
        '대전': ['대전', '유성', '대덕'],
        '울산': ['울산', '울주'],
        '세종': ['세종'],
        '강원': ['강원', '춘천', '원주', '강릉', '동해', '태백', '속초', '삼척'],
        '충청': ['충청', '천안', '청주', '아산', '서산', '당진', '공주', '보령'],
        '전라': ['전라', '전주', '익산', '군산', '목포', '여수', '순천'],
        '경상': ['경상', '포항', '경주', '안동', '구미', '영주', '경산', '진주', '통영'],
        '제주': ['제주'],
    }
    
    for region, keywords in region_map.items():
        for kw in keywords:
            if kw in addr:
                return region
    
    return "기타"


def get_commute_stats():
    try:
        sb = get_supabase_admin()
        res = sb.table("commute_searches").select("*").order("created_at", desc=True).execute()
        return res.data or []
    except Exception as e:
        return []


def get_commute_region_stats():
    try:
        searches = get_commute_stats()
        region_count = {}
        for s in searches:
            region = s.get('region', '기타')
            region_count[region] = region_count.get(region, 0) + 1
        sorted_regions = sorted(region_count.items(), key=lambda x: x[1], reverse=True)
        return sorted_regions
    except Exception as e:
        return []

# ============ FAQ 매칭 (비용 절감) ============

def find_matching_faq(user_question, threshold=0.4):
    """
    사용자 질문과 FAQ를 매칭해서 답변 찾기
    매칭되면 답변 반환, 없으면 None
    
    threshold: 0.0~1.0 (높을수록 엄격)
    - 0.3: 느슨 (자주 매칭됨, 잘못 매칭될 수 있음)
    - 0.4: 균형 ⭐ 기본값
    - 0.5: 엄격 (확실한 것만 매칭)
    """
    if not user_question:
        return None
    
    try:
        all_faqs = []
        sb = get_supabase()
        
        # 공통 FAQ
        try:
            kb_res = sb.table("knowledge_base").select("question, answer").eq("is_active", True).execute()
            for kb in (kb_res.data or []):
                all_faqs.append({
                    "question": kb.get("question", ""),
                    "answer": kb.get("answer", ""),
                    "source": "FAQ"
                })
        except Exception as e:
            print(f"공통 FAQ 로드 실패: {e}")
        
        # 센터별 FAQ
        try:
            cf_res = sb.table("center_faqs").select("question, answer").eq("is_active", True).execute()
            for cf in (cf_res.data or []):
                all_faqs.append({
                    "question": cf.get("question", ""),
                    "answer": cf.get("answer", ""),
                    "source": "센터FAQ"
                })
        except Exception as e:
            print(f"센터 FAQ 로드 실패: {e}")
        
        if not all_faqs:
            return None
        
        # 사용자 질문 정규화
        user_q_normalized = normalize_text(user_question)
        if not user_q_normalized or len(user_q_normalized) < 2:
            return None
        
        # 각 FAQ와 유사도 계산
        best_match = None
        best_score = 0
        
        for faq in all_faqs:
            faq_q = normalize_text(faq["question"])
            if not faq_q:
                continue
            
            score = calculate_similarity(user_q_normalized, faq_q)
            
            if score > best_score:
                best_score = score
                best_match = faq
        
        # 임계값 이상이면 매칭 성공
        if best_score >= threshold and best_match:
            return {
                "question": best_match["question"],
                "answer": best_match["answer"],
                "score": round(best_score, 2),
                "source": best_match["source"]
            }
        
        return None
        
    except Exception as e:
        print(f"FAQ 매칭 실패: {e}")
        return None


def normalize_text(text):
    """텍스트 정규화 - 공백/특수문자 제거 + 소문자"""
    if not text:
        return ""
    import re
    text = re.sub(r'[^\w가-힣]', ' ', text)
    text = re.sub(r'\s+', ' ', text).strip().lower()
    return text


def calculate_similarity(text1, text2):
    """두 텍스트의 유사도 계산 (0.0 ~ 1.0)"""
    if not text1 or not text2:
        return 0
    
    # 한국어 동의어 매핑
    synonyms = {
        '급여': ['월급', '연봉', '돈', '페이', '시급'],
        '월급': ['급여', '연봉', '돈', '페이'],
        '신입': ['신규', '경력없음', '미경험'],
        '교육': ['훈련', '연수', '트레이닝', 'OJT', '오제이티'],
        '근무시간': ['일하는시간', '업무시간', '시간'],
        '근무': ['일', '업무', '근로'],
        '주차': ['파킹', '차'],
        '재택': ['홈', '집', '원격'],
        '복지': ['혜택', '베네핏', '복리후생'],
        '면접': ['인터뷰'],
        '지원': ['신청', '응모'],
        '나이': ['연령'],
        '학력': ['학벌', '졸업'],
        '인센티브': ['수당', '보너스', '성과급'],
        '휴게실': ['쉴공간', '쉬는곳'],
        '점심': ['식사', '런치'],
        '교통': ['출퇴근', '거리'],
        '센터': ['사무실', '회사', '근무지'],
        '연락처': ['번호', '전화', '담당자'],
        '경력': ['이력', '경험'],
        '분위기': ['문화', '동료', '사람들'],
        '간식': ['음료', '커피', '다과'],
    }
    
    words1 = set(text1.split())
    words2 = set(text2.split())
    
    if not words1 or not words2:
        return 0
    
    # 직접 일치
    direct_match = len(words1 & words2)
    
    # 동의어 + 부분 일치
    synonym_match = 0
    for w1 in words1:
        if w1 in words2:
            continue
        # 동의어 사전 확인
        for key, syns in synonyms.items():
            if w1 == key or w1 in syns:
                check_words = [key] + syns
                for w2 in words2:
                    if w2 in check_words:
                        synonym_match += 0.7
                        break
        # 부분 일치 (포함 관계)
        for w2 in words2:
            if w1 != w2 and (w1 in w2 or w2 in w1) and len(w1) >= 2:
                synonym_match += 0.5
    
    total_match = direct_match + synonym_match
    union_size = len(words1 | words2)
    
    if union_size == 0:
        return 0
    
    similarity = total_match / union_size
    return min(similarity, 1.0)
