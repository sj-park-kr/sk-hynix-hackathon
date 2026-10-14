"""GlobalCart 입점 검수 문제 생성기 (가상 데이터). 규칙 엔진으로 정답을 계산하고 설계값과 대조한다."""
import json, os

HERE = os.path.dirname(os.path.abspath(__file__))

REVIEWERS = {  # INS: (영문, 한글)
    "INS 01": ("Sarah Lee", "이사라"), "INS 02": ("Park Ji-hoon", "박지훈"), "INS 03": ("Kim Min-jun", "김민준"),
    "INS 04": ("Michael Johnson", "마이클 존슨"), "INS 05": ("Kim Min-ju", "김민주"), "INS 06": ("Emily Chen", "에밀리 첸"),
}
BRANDS = [  # 코드, 영문 폴더명 접두, 법인명, 제조국, 슬로건
    ("BWB", "Brentwell_Bio", "Brentwell Bio, Inc.", "미국", "BIOTECH FORMULATION · USA"),
    ("CPL", "Cloudpine", "Cloudpine Labs LLC", "미국", "OUTDOOR SUNCARE · USA"),
    ("DRG", "Doraji", "도라지가든(주)", "한국", "JEJU BOTANICALS · KOREA"),
    ("HNK", "Hanok_Skin", "한옥스킨(주)", "한국", "HERITAGE SKINCARE · KOREA"),
    ("YHC", "Yulhwa", "Yulhwa Cosmetics Co., Ltd.", "한국", "K-BEAUTY LAB · KOREA"),
    ("PYB", "Pyeonbaek", "편백보태닉스(주)", "한국", "FOREST CARE · KOREA"),
    ("MDL", "Maison_Delune", "Maison Delune SAS", "프랑스", "PARIS AROMATICS · FRANCE"),
    ("NVL", "Novelure", "Novelure Inc.", "미국", "ACTIVE SERUMS · USA"),
    ("SKD", "Sakura_Dew", "Sakura Dew K.K.", "일본", "TOKYO ESSENCE · JAPAN"),
    ("AQV", "Aquavine", "Aquavine Corp.", "미국", "HYDRA SCIENCE · USA"),
    ("LMN", "Lumen_Nord", "Lumen Nord AB", "스웨덴", "NORDIC SENSITIVE CARE · SWEDEN"),
    ("ODM", "Oriel_Derm", "Oriel Derm Ltd.", "영국", "DERMA REPAIR · UK"),
    ("TRH", "Terra_Herb", "테라허브뉴트리션(주)", "한국", "HEALTH FUNCTIONAL FOOD · KOREA"),
    ("GNH", "Ginseng_Haus", "인삼하우스(주)", "한국", "RED GINSENG · KOREA"),
    ("BLS", "Bloom_Seoul", "블룸서울(주)", "한국", "SEOUL DAILY BEAUTY · KOREA"),
]
BRAND = {b[0]: b for b in BRANDS}

L, R, I = "씻어내지 않는 제품", "씻어내는 제품", "섭취(건강기능식품)"
F_WR, F_WH, F_UV, GEN, HFF = "기능성 화장품 · 주름 개선", "기능성 화장품 · 미백", "기능성 화장품 · 자외선 차단", "일반 화장품", "건강기능식품"

# 상품: 코드, 영문명, 한글명, 유형, 카테고리, 배송지역, 동물실험, 성분[(이름, 값, 단위, nano표기)], 알레르기[(이름, %, 표기)], 문구, INS, 검수일, 상태, 메모, 용량
P = []
def add(code, en, ko, kind, cat, regions, ingr, claims, ins, date, status, memo="", allergens=(), animal="실시하지 않음", vol="30 mL"):
    P.append(dict(code=code, en=en, ko=ko, kind=kind, cat=cat, regions=regions, ingr=list(ingr), claims=list(claims), ins=ins,
                  date=date, status=status, memo=memo, allergens=list(allergens), animal=animal, vol=vol))

US, KR, JP, EU = "미국", "한국", "일본", "EU"
add("BWB-01", "Bio Retinol Cream", "바이오 레티놀 크림", L, F_WR, [US, KR, JP, EU], [("레티놀", 0.25, "%"), ("아데노신", 0.04, "%"), ("나이아신아마이드", 2.0, "%"), ("글리세린", 5.0, "%")], ["주름 개선에 도움을 주는 레티놀 크림", "피부 결을 매끄럽게 정돈"], "INS 04", "2026.04.18", "Pass", allergens=[("리날룰", 0.0008, "미표기")])
add("BWB-02", "Peptide Booster Serum", "펩타이드 부스터 세럼", L, GEN, [US, KR], [("나이아신아마이드", 4.0, "%"), ("팔미토일트라이펩타이드-1", 0.01, "%"), ("판테놀", 1.0, "%")], ["탄력 있어 보이는 피부결", "하루 종일 보습 지속"], "INS 01", "2026.04.03", "Pass")
add("BWB-03", "Anti-Wrinkle Eye Cream", "안티링클 아이크림", L, F_WR, [US, KR, EU], [("레티놀", 0.30, "%"), ("아데노신", 0.04, "%"), ("카페인", 0.5, "%")], ["눈가 주름 개선에 도움"], "INS 06", "2026.04.21", "Pass", vol="15 mL")
add("CPL-01", "Beach Shield SPF50+", "비치 쉴드 선크림 SPF50+", L, F_UV, [US, KR], [("징크옥사이드", 20.0, "%"), ("옥시벤존", 4.0, "%"), ("에틸헥실메톡시신나메이트", 7.5, "%")], ["강력한 자외선 차단 SPF50+ PA++++", "워터프루프 80분"], "INS 02", "2026.04.07", "Pass", vol="50 mL")
add("CPL-02", "Daily Sun Fluid", "데일리 선 플루이드", L, F_UV, [US, KR, JP], [("징크옥사이드", 15.0, "%"), ("티타늄디옥사이드", 5.0, "%")], ["자외선 차단 SPF50+ PA+++", "햇빛 알레르기 치료 효과까지"], "INS 03", "2026.04.09", "Pass", vol="50 mL")
add("CPL-03", "Surf Sun Stick", "서프 선스틱", L, F_UV, [US, KR, EU], [("옥시벤존", 4.0, "%"), ("징크옥사이드", 10.0, "%"), ("에틸헥실살리실레이트", 5.0, "%")], ["끈적임 없는 자외선 차단 스틱", "땀과 물에 강한 지속력"], "INS 04", "2026.04.10", "Fail", "EU 배송 신청 건: 옥시벤존 EU 허용 한도 초과로 반려", vol="20 g")
add("DRG-01", "Camellia Cleansing Foam", "동백 클렌징 폼", R, GEN, [KR, JP, EU], [("코카미도프로필베타인", 8.0, "%"), ("메틸이소치아졸리논", 0.001, "%"), ("동백나무씨오일", 1.0, "%")], ["촉촉하게 씻기는 동백 폼", "노폐물 세정"], "INS 01", "2026.04.02", "Pass", allergens=[("리모넨", 0.02, "표기")], vol="150 mL")
add("DRG-02", "Green Tea Toner", "녹차 토너", L, GEN, [KR, US], [("나이아신아마이드", 3.0, "%"), ("녹차추출물", 10.0, "%")], ["지친 피부 진정", "속건조 수분 공급"], "INS 05", "2026.04.04", "Pass", vol="200 mL")
add("DRG-03", "Hallabong Vita Serum", "한라봉 비타 세럼", L, F_WH, [KR, EU], [("알부틴", 2.0, "%"), ("아스코빌글루코사이드", 2.0, "%")], ["기미 치료 세럼", "맑고 환한 피부 톤"], "INS 03", "2026.04.14", "Fail", "상세페이지 문구 '기미 치료'가 의학적 효능 표현에 해당하여 반려")
add("HNK-01", "Ginseng Revital Cream", "인삼 리바이탈 크림", L, F_WR, [KR, US, JP], [("레티놀", 0.5, "%"), ("아데노신", 0.04, "%"), ("인삼추출물", 3.0, "%")], ["세포 재생으로 주름 개선", "깊은 영양 공급"], "INS 03", "2026.04.15", "Pass", vol="50 mL")
add("HNK-02", "Rice Bright Essence", "쌀 브라이트 에센스", L, F_WH, [KR, EU], [("나이아신아마이드", 5.0, "%"), ("쌀추출물", 20.0, "%")], ["미백에 도움", "윤기 있는 피부"], "INS 05", "2026.04.08", "Pass", allergens=[("리날룰", 0.0005, "미표기")], vol="100 mL")
add("HNK-03", "Clear Peel Cleanser", "클리어 필 클렌저", R, GEN, [KR, US], [("살리실산", 3.0, "%"), ("소듐코코일글리시네이트", 10.0, "%")], ["각질 정돈 클렌저", "산뜻한 마무리"], "INS 02", "2026.04.11", "Fail", "살리실산 배합 한도 초과로 반려", vol="120 mL")
add("YHC-01", "Retinol Night Cream", "레티놀 나이트 크림", L, F_WR, [KR, US, JP], [("레티놀", 0.5, "%"), ("아데노신", 0.04, "%"), ("세라마이드엔피", 0.5, "%")], ["주름 개선에 도움", "자는 동안 집중 케어"], "INS 04", "2026.04.16", "Pass", vol="50 mL")
add("YHC-02", "Mineral Sun Cushion", "미네랄 선쿠션", L, F_UV, [KR, EU, JP], [("징크옥사이드(나노)", 18.0, "%", "미표기"), ("티타늄디옥사이드", 4.0, "%")], ["자외선 차단 SPF50+ PA++++", "가볍게 톡톡 덧바르는 쿠션"], "INS 06", "2026.04.17", "Pass", vol="15 g")
add("YHC-03", "Acne Spot Gel", "아크네 스팟 젤", L, GEN, [KR, EU], [("살리실산", 0.5, "%"), ("병풀추출물", 5.0, "%")], ["여드름 치료 스팟 젤", "밤사이 집중 케어"], "INS 02", "2026.04.18", "Fail", "'여드름 치료' 문구로 반려", vol="15 mL")
add("PYB-01", "Calming Mist", "편백 진정 미스트", L, GEN, [KR, US], [("편백수", 60.0, "%"), ("판테놀", 1.0, "%")], ["피톤치드 진정 미스트", "언제 어디서나 수분 충전"], "INS 01", "2026.04.06", "Pass", vol="100 mL")
add("PYB-02", "Body Wash", "편백 바디워시", R, GEN, [KR, EU], [("메틸이소치아졸리논", 0.0012, "%"), ("코카미도프로필베타인", 9.0, "%")], ["숲속 향기 바디워시", "산뜻한 세정"], "INS 05", "2026.04.07", "Pass", allergens=[("리모넨", 0.05, "표기")], vol="500 mL")
add("PYB-03", "Spot Brightening Cream", "스팟 브라이트닝 크림", L, F_WH, [KR, US], [("하이드로퀴논", 2.0, "%"), ("나이아신아마이드", 2.0, "%")], ["미백에 도움", "칙칙한 부분 집중 케어"], "INS 06", "2026.04.20", "Pass")
add("MDL-01", "Rose Serum", "로즈 세럼", L, GEN, [KR, EU, US], [("다마스크장미꽃수", 30.0, "%"), ("히알루론산", 0.5, "%")], ["장미 향이 감도는 보습 세럼"], "INS 04", "2026.04.03", "Pass", allergens=[("시트랄", 0.003, "표기"), ("제라니올", 0.002, "표기")])
add("MDL-02", "Night Repair Oil", "나이트 리페어 오일", L, GEN, [KR, EU], [("호호바씨오일", 40.0, "%"), ("토코페롤", 0.5, "%")], ["밤사이 촉촉한 오일 케어", "은은한 시트러스 향"], "INS 01", "2026.04.13", "Pass", allergens=[("리모넨", 0.012, "미표기")])
add("MDL-03", "Hydra Wash-off Mask", "하이드라 워시오프 마스크", R, GEN, [KR, EU], [("카올린", 15.0, "%"), ("글리세린", 8.0, "%")], ["10분 수분 마스크", "사용 후 물로 씻어내기"], "INS 05", "2026.04.12", "Pass", allergens=[("리날룰", 0.005, "미표기")], vol="75 mL")
add("NVL-01", "Retinol 0.5 Serum", "레티놀 0.5 세럼", L, F_WR, [US, KR, EU], [("레티놀", 0.5, "%"), ("아데노신", 0.04, "%")], ["주름 개선에 도움", "고함량 레티놀 0.5%"], "INS 02", "2026.04.09", "Fail", "EU 배송 신청 건: 레티놀 EU 허용 한도 초과로 반려")
add("NVL-02", "Vitamin C 15 Serum", "비타민 C 15 세럼", L, GEN, [US, KR], [("아스코빅애씨드", 15.0, "%"), ("페룰릭애씨드", 0.5, "%")], ["비타민으로 생기 있는 피부"], "INS 06", "2026.04.05", "Pass")
add("NVL-03", "Brightening Lotion", "브라이트닝 로션", L, GEN, [US, KR], [("나이아신아마이드", 2.0, "%"), ("감초추출물", 1.0, "%")], ["미백에 도움", "맑은 피부 표현"], "INS 03", "2026.04.10", "Pass", vol="150 mL")
add("SKD-01", "Sakura Essence", "사쿠라 에센스", L, GEN, [JP, KR, EU], [("벚꽃잎추출물", 10.0, "%"), ("나이아신아마이드", 2.0, "%")], ["벚꽃처럼 화사한 피부결", "가볍게 스며드는 에센스"], "INS 04", "2026.04.14", "Pass", animal="실시(제3국 수출 인증용)", vol="150 mL")
add("SKD-02", "Atopy Balm", "아토피 밤", L, GEN, [JP, KR], [("세라마이드엔피", 1.0, "%"), ("시어버터", 10.0, "%")], ["아토피 피부 개선 밤", "건조한 피부 보호막"], "INS 05", "2026.04.15", "Pass", vol="40 g")
add("SKD-03", "Cleansing Oil", "클렌징 오일", R, GEN, [JP, KR, EU], [("올리브오일", 30.0, "%"), ("폴리솔베이트80", 5.0, "%")], ["메이크업까지 한 번에"], "INS 01", "2026.04.16", "Pass", allergens=[("리날룰", 0.008, "미표기")], vol="200 mL")
add("AQV-01", "Hydro Gel", "하이드로 젤", L, GEN, [US, KR, EU], [("티타늄디옥사이드(나노)", 2.0, "%", "표기"), ("히알루론산", 1.0, "%")], ["72시간 수분 지속"], "INS 02", "2026.04.03", "Pass", vol="50 mL")
add("AQV-02", "Niacinamide 7 Serum", "나이아신아마이드 7 세럼", L, F_WH, [US, KR], [("나이아신아마이드", 7.0, "%"), ("징크피씨에이", 1.0, "%")], ["미백에 도움", "모공이 덜 보이는 피부"], "INS 04", "2026.04.08", "Pass")
add("AQV-03", "Alpha-Arbutin Serum", "알파-알부틴 세럼", L, F_WH, [US, KR, EU], [("알파-알부틴", 3.0, "%"), ("나이아신아마이드", 2.0, "%")], ["미백에 도움"], "INS 06", "2026.04.11", "Pass")
add("LMN-01", "Barrier Cream", "배리어 크림", L, GEN, [EU, KR], [("메틸이소치아졸리논", 0.001, "%"), ("세라마이드엔피", 1.0, "%")], ["민감 피부 보호막 크림"], "INS 01", "2026.04.17", "Pass", vol="50 mL")
add("LMN-02", "Gentle Shampoo", "젠틀 샴푸", R, GEN, [EU, KR], [("메틸이소치아졸리논", 0.0015, "%"), ("데실글루코사이드", 12.0, "%")], ["두피까지 순하게"], "INS 05", "2026.04.19", "Pass", vol="300 mL")
add("LMN-03", "Retinal Cream", "레티날 크림", L, F_WR, [EU, KR, US], [("레티놀", 0.2, "%"), ("아데노신", 0.04, "%")], ["주름 개선에 도움"], "INS 04", "2026.04.20", "Pass")
add("ODM-01", "Repair Cream", "리페어 크림", L, GEN, [US, KR], [("판테놀", 5.0, "%"), ("세라마이드엔피", 0.5, "%")], ["피부 장벽 강화"], "INS 02", "2026.04.04", "Pass", vol="50 mL")
add("ODM-02", "Calming Cream", "카밍 크림", L, GEN, [US, KR], [("덱사메타손", 0.01, "%"), ("병풀추출물", 2.0, "%")], ["즉각적인 진정 케어"], "INS 06", "2026.04.06", "Fail", "금지 원료(덱사메타손) 검출로 반려", vol="50 mL")
add("ODM-03", "Retinol 0.8 Cream", "레티놀 0.8 크림", L, F_WR, [US, KR], [("레티놀", 0.8, "%"), ("아데노신", 0.04, "%")], ["주름 개선에 도움", "고농도 레티놀 0.8%"], "INS 03", "2026.04.19", "Pass")
add("TRH-01", "Green Coffee Slim", "그린커피 슬림", I, HFF, [KR, US], [("카페인", 300, "mg/일"), ("녹차추출물", 500, "mg/일")], ["체지방 감소에 도움을 줄 수 있음"], "INS 02", "2026.04.05", "Pass", vol="60정")
add("TRH-02", "Sleep Well", "슬립웰", I, HFF, [KR, JP], [("L-테아닌", 200, "mg/일"), ("마그네슘", 150, "mg/일")], ["불면증 치료 솔루션", "편안한 밤"], "INS 05", "2026.04.12", "Fail", "'불면증 치료' 문구로 반려", vol="30포")
add("TRH-03", "Energy Shot", "에너지 샷", I, HFF, [KR, EU], [("카페인", 450, "mg/일"), ("타우린", 1000, "mg/일")], ["활력 충전"], "INS 03", "2026.04.13", "Fail", "카페인 1일 섭취량 한도 초과로 반려", vol="10병")
add("GNH-01", "Red Ginseng Stick", "홍삼 스틱", I, HFF, [KR, US, EU], [("진세노사이드 Rg1+Rb1+Rg3", 10, "mg/일")], ["면역력 증진에 도움을 줄 수 있음"], "INS 01", "2026.04.02", "Pass", vol="30포")
add("GNH-02", "Slim Capsule", "슬림 캡슐", I, HFF, [KR, US], [("가르시니아캄보지아추출물", 1000, "mg/일"), ("시부트라민", 5, "mg/일")], ["한 달 만에 체중 감량"], "INS 04", "2026.04.10", "Fail", "시험성적서에서 금지 원료(시부트라민) 검출로 반려", vol="60캡슐")
add("GNH-03", "Kids Vita", "키즈 비타", I, HFF, [KR], [("비타민 C", 100, "mg/일"), ("비타민 D", 10, "μg/일")], ["어린이 성장기 영양 보충"], "INS 06", "2026.04.21", "Pass", vol="60정")
add("BLS-01", "Cica Cream", "시카 크림", L, GEN, [KR, EU], [("병풀추출물", 10.0, "%"), ("마데카소사이드", 0.1, "%")], ["상처 치료 크림", "붉은 기 진정"], "INS 02", "2026.04.15", "Pass", vol="50 mL")
add("BLS-02", "Tone-up Cream", "톤업 크림", L, F_WH, [KR, EU], [("티타늄디옥사이드(나노)", 5.0, "%", "표기"), ("나이아신아마이드", 2.0, "%")], ["미백에 도움", "자연스러운 톤 보정"], "INS 03", "2026.04.16", "Pass", vol="50 mL")
add("BLS-03", "Lip Tint", "립 틴트", L, GEN, [KR, US, EU], [("디메치콘", 10.0, "%"), ("적색 227호", 0.5, "%")], ["선명한 컬러가 오래 지속"], "INS 05", "2026.04.17", "Pass", allergens=[("리모넨", 0.0009, "미표기")], vol="4 g")
assert len(P) == 45 and len({p["code"] for p in P}) == 45

# ---------- 규칙 (01 가이드 + 02 업데이트) ----------
MED_TERMS = ["치료", "완치", "처방", "세포 재생", "염증", "질병 예방"]
DISEASE_IMPROVE = ["아토피", "여드름", "습진", "건선", "탈모", "기미", "불면증"]
LIMIT_KR = {"레티놀": 1.0, "나이아신아마이드": 5.0, "살리실산": 2.0, "알부틴": 5.0, "알파-알부틴": 5.0, "징크옥사이드": 25.0, "티타늄디옥사이드": 25.0, "옥시벤존": 6.0}
LIMIT_HFF = {"카페인": 400}
BANNED = ["하이드로퀴논", "수은", "덱사메타손", "트레티노인", "시부트라민"]
LIMIT_EU = {"레티놀": 0.3, "옥시벤존": 2.2}
ALLERGENS = ["리모넨", "리날룰", "시트랄", "제라니올"]

def base(n): return n.replace("(나노)", "")
def med_violation(p):
    for c in p["claims"]:
        if any(t in c for t in MED_TERMS): return True
        if any(d in c for d in DISEASE_IMPROVE) and any(v in c for v in ("개선", "완화", "치료")): return True
    return False
def func_scope_violation(p):  # 제6조: 기능성 미인증 상품의 기능성 표방
    if p["cat"] == GEN: return any(k in c for c in p["claims"] for k in ("미백에 도움", "주름 개선에 도움"))
    return False
def ingr_violation(p):
    for n, v, u, *_ in p["ingr"]:
        b = base(n)
        if any(x in b for x in BANNED): return True
        if p["kind"] != I and b in LIMIT_KR and v > LIMIT_KR[b]: return True
        if p["kind"] == I and b in LIMIT_HFF and v > LIMIT_HFF[b]: return True
        if b == "메틸이소치아졸리논" and (p["kind"] == L or v > 0.0015): return True  # 02 업데이트 KR
    return False
def kr_ok(p): return not (med_violation(p) or func_scope_violation(p) or ingr_violation(p))
def eu_violation(p):
    if EU not in p["regions"] or p["kind"] == I: return False
    if p["animal"].startswith("실시("): return True
    for n, v, u, *nano in p["ingr"]:
        b = base(n)
        if b in LIMIT_EU and v > LIMIT_EU[b]: return True
        if "(나노)" in n and (nano[0] if nano else "미표기") != "표기": return True
    th = 0.001 if p["kind"] == L else 0.01
    return any(a in ALLERGENS and pct > th and lab != "표기" for a, pct, lab in p["allergens"])

name = lambda ins: REVIEWERS[ins][0]
q1 = [p["code"] for p in P if p["code"].startswith("YHC") and kr_ok(p) and eu_violation(p)]
q2 = sorted(p["code"] for p in P if p["ins"] == "INS 03" and p["status"] == "Pass" and med_violation(p))
q3 = sorted(p["code"] for p in P if p["status"] == "Pass" and ingr_violation(p))
q4 = sorted(p["code"] for p in P if kr_ok(p) and eu_violation(p))
print("Q1", q1, "Q2", q2, "Q3", q3, "Q4", q4)
assert q1 == ["YHC-02"] and q2 == ["CPL-02", "HNK-01"] and q3 == ["AQV-02", "LMN-01", "PYB-03"]
assert q4 == ["CPL-03", "MDL-02", "NVL-01", "SKD-01", "YHC-02"]

# ---------- 문서 ----------
guide = """[p.1]
GlobalCart Compliance Guide v3 · 입점 상품 준법 감시 기준 (가상 문서)
시행 2026-01-01 · 문서번호 GC-CMP-003 · 대외비

제1조(목적) 이 기준은 GlobalCart 입점 상품(화장품·건강기능식품)의 등록 가부 판정 기준과 검수 절차를 정한다.
제2조(적용 범위·판정 원칙) ① 모든 상품에는 이 기준(한국 기준)을 적용한다. ② 배송 신청 지역에 해외 국가가 포함되면 '02_Country_Import_Update_2026'의 해당 국가 추가 규제를 함께 적용한다. ③ 이 기준과 국가별 업데이트가 다르면 시행일이 늦은 규정을 우선하되, 시행일이 도래하지 않은 규정은 적용하지 않는다. ④ 검수일 기준으로 시행 중인 규정만 판정에 쓴다.
제3조(용어) ① '씻어내지 않는 제품'은 크림·세럼·에센스·로션·오일·쿠션·스틱·틴트 등 피부에 남는 제품을, '씻어내는 제품'은 클렌저·바디워시·샴푸·워시오프 마스크 등 사용 후 물로 씻어내는 제품을 말한다. ② 배합 농도는 사양서의 '주요 성분 및 배합 농도' 표에 기재된 값을 기준으로 한다.
제4조(필수 기재 항목) 사양서에는 브랜드명, 제조국, 상품 코드, 신청 카테고리, 배송 신청 지역, 용량, 제품 유형, 동물실험 여부, 성분·배합 농도를 기재한다.

[p.2]
제5조(의학적 효능 표현 금지) ① 상세페이지·포장 문구에 질병의 예방·치료 효능을 표방하는 다음 표현을 쓸 수 없다: '치료', '완치', '처방', '세포 재생', '염증' 관련 효능, '질병 예방'. ② 특정 질병명(아토피, 여드름, 습진, 건선, 탈모, 기미, 불면증 등)과 '개선', '완화', '치료'를 결합한 표현도 금지한다. ③ '진정', '보습', '피부 결 정돈', '피부 장벽 강화' 등 피부 상태 표현은 의학적 효능 표현으로 보지 않는다.
제6조(기능성 표시 범위) ① '주름 개선에 도움', '미백에 도움', '자외선 차단' 표현은 해당 기능성 카테고리로 신청한 상품만 쓸 수 있다. ② 일반 화장품이 기능성 효능을 표방하면 등록할 수 없다.
제7조(성분 배합 한도) 다음 성분은 아래 한도를 넘을 수 없다(화장품, 배합 농도 기준).
성분 | 한도
레티놀 | 1.0%
나이아신아마이드 | 5.0%
살리실산 | 2.0%
알부틴·알파-알부틴 | 5.0%
징크옥사이드 | 25%
티타늄디옥사이드 | 25%
옥시벤존 | 6.0%
※ 한도와 같은 값은 허용한다. 나노 원료는 같은 성분의 한도를 따른다.

[p.3]
제8조(금지 원료) 다음 원료가 배합되거나 시험성적서에서 검출된 상품은 등록할 수 없다: 하이드로퀴논, 수은 및 그 화합물, 덱사메타손 등 스테로이드, 트레티노인, 시부트라민.
제9조(건강기능식품 특칙) ① 1일 섭취량 기준 카페인은 400mg을 넘을 수 없다. ② '~에 도움을 줄 수 있음' 형식의 기능성 표현은 허용하되, 질병의 예방·치료 표현은 제5조를 따른다.
제10조(검수 절차) ① 검수자는 제5조~제9조와 국가별 추가 규제를 모두 확인하고 'Pass(승인)' 또는 'Fail(반려)'로 판정한다. ② 하나라도 위반하면 반려해야 한다. ③ 사양서에는 검수자의 영문 성명과 검수자 번호(INS)를 기재한다.

부록 A. 검수자 명단
검수자 번호 | 성명 | 영문 성명
""" + "\n".join(f"{k} | {v[1]} | {v[0]}" for k, v in REVIEWERS.items()) + """
※ 김민준(INS 03)과 김민주(INS 05)는 동명이인이 아니라 다른 검수자이다."""

update = """[p.1]
Country Import Update 2026 · 국가별 수입 규제 업데이트 (가상 문서)
발효 2026-03-01 · GlobalCart 준법감시팀

1. 개요
이 문서는 2026년 3월 1일 자로 발효된 국가별 추가 규제와 향후 시행 예정 사항을 정리한다. 배송 신청 지역에 해당 국가가 포함된 상품에만 해당 국가 규정을 적용한다(Compliance Guide v3 제2조).

2. 한국(전 상품 공통, 2026-03-01 시행)
① 메틸이소치아졸리논(MIT)은 씻어내지 않는 제품에 사용할 수 없다. 씻어내는 제품은 0.0015% 이하로만 허용한다.
② [시행 예정 2026-07-01] 레티놀 배합 한도를 1.0%에서 0.5%로 낮춘다. 시행일 전 검수에는 적용하지 않는다.

[p.2]
3. EU 추가 규제(EU 배송 신청 화장품, 2026-03-01 시행)
① 레티놀: 0.3% 이하
② 옥시벤존: 2.2% 이하
③ 동물실험을 실시한(제3국 인증 목적 포함) 화장품은 EU에 판매할 수 없다.
④ 알레르기 유발 향료(리모넨, 리날룰, 시트랄, 제라니올)는 씻어내지 않는 제품 0.001%, 씻어내는 제품 0.01%를 넘으면 성분표에 개별 표기해야 한다. 미표기 시 판매할 수 없다.
⑤ 나노 원료는 성분명 뒤에 [nano]를 표기해야 한다. 미표기 시 판매할 수 없다.
⑥ [시행 예정 2026-09-01] 알파-알부틴 배합 한도를 2.0%로 정한다. 시행일 전 검수에는 적용하지 않는다.

4. 미국·일본(참고)
① 미국: 자외선 차단 제품은 SPF와 Broad Spectrum 표기를 권고한다(등록 가부와 무관).
② 일본: 의약부외품 표시는 일본 내 허가 번호가 있는 경우에만 쓸 수 있다(이번 검수 대상 없음).
5. 건강기능식품은 이번 업데이트의 EU 추가 규제(3절) 대상이 아니다."""

def sheet(p):
    b = BRAND[p["code"][:3]]
    rev = REVIEWERS[p["ins"]][0]
    ingr = "\n".join(f"{n.replace('(나노)', ' (나노 입자)')} | {v:g}{'' if u == '%' else ' '}{u} | " + (f"나노 원료, 성분표 [nano] {x[0]}" if x else "-") for n, v, u, *x in p["ingr"])
    allg = "\n".join(f"{a} | {pct:g}% | {lab}" for a, pct, lab in p["allergens"]) or "해당 없음 | - | -"
    claims = "\n".join(f"- \"{c}\"" for c in p["claims"])
    st = "Pass 승인" if p["status"] == "Pass" else "Fail 반려"
    return f"""[p.1]
{b[1].replace('_', ' ').upper()} · {b[4]}
{b[1].replace('_', ' ')} {p['en']} ({p['ko']}) · PRODUCT {p['code'].replace('-', ' ')}
REVIEW STATUS: {st}
검수 담당자: {rev} · {p['ins']} · 검수일: {p['date']}

브랜드명 | {b[2]} | 제조국 | {b[3]}
상품 코드 | {p['code']} | 신청 카테고리 | {p['cat']}
배송 신청 지역 | {', '.join(p['regions'])} | 용량 | {p['vol']}
제품 유형 | {p['kind']} | 동물실험 | {p['animal']}
판매 채널 | GlobalCart {'USA' if b[3] == '미국' else 'Korea'} | 검수 메모 | {p['memo'] or '-'}

[p.2]
1. 주요 성분 및 배합 농도
성분 | 배합 농도(또는 1일 섭취량) | 비고
{ingr}

2. 알레르기 유발 향료
성분 | 함량 | 성분표 개별 표기
{allg}

3. 상세페이지·포장 문구
{claims}"""

files = [
    {"name": "01_GlobalCart_Compliance_Guide_v3.pdf", "kind": "pdf", "tokens": 3412, "content": guide},
    {"name": "02_Country_Import_Update_2026.pdf", "kind": "pdf", "tokens": 2186, "content": update},
]
for code, pre, *_ in BRANDS:
    for i, p in enumerate([x for x in P if x["code"][:3] == code], 1):
        files.append({"name": f"{i:02d}_{pre}_{p['en'].replace(' ', '_').replace('+', '')}_KR.pdf", "folder": code, "kind": "pdf", "tokens": 2200 + sum(map(ord, p["code"] + p["en"])) % 140, "content": sheet(p)})

def why(codes): return ", ".join(codes)
problem = {
    "id": "globalcart-01", "type": "mcq", "title": "GlobalCart 입점 검수 감사", "badge": "주관식 4문항", "timeLimitMin": 30,
    "aiLimit": {"count": 10, "chars": 1000}, "pii": [], "notices": [], "files": files,
    "passage": "2026년 4월 한 달 동안 글로벌 이커머스 플랫폼 GlobalCart의 한국·미국 입점 심사 과정을 거친 15개 브랜드의 화장품·건강기능식품 45개 상품에 대한 검수 기록과 관련 규정 문서가 주어집니다.\n\n- `01_GlobalCart_Compliance_Guide_v3.pdf`는 GlobalCart가 입점 상품의 등록 가부를 판정할 때 적용하는 공식 준법 감시 기준 문서입니다.\n- `02_Country_Import_Update_2026.pdf`는 2026년 3월 1일 자로 발효된 국가별 수입 규제 업데이트 문서입니다.\n- 영문 3자로 된 폴더들에는 15개 브랜드의 상품별 기술 사양서가 들어있습니다.\n\n주어진 자료를 보고 아래 질문들에 답해주세요.",
    "questions": [
        {"kind": "short", "q": "Yulhwa Cosmetics(YHC) 브랜드의 3개 상품 중, 한국 기준으로는 등록 가능하지만 EU 추가 규제를 통과하지 못하는 상품의 상품 코드를 입력해 주세요. (상품 코드만 입력해 주세요. 예: `YHC-01`)",
         "answer": "YHC-02", "accept": ["YHC-02", "YHC02"],
         "explain": "YHC-02는 한국 기준을 모두 충족하지만 EU 배송 신청 상품이면서 나노 징크옥사이드에 [nano] 표기가 없어 EU 3절⑤ 위반입니다. YHC-01은 레티놀 0.5%로 EU 한도(0.3%)를 넘지만 배송 신청 지역에 EU가 없어 EU 규제 대상이 아니고, YHC-03은 '여드름 치료' 문구로 한국 기준(제5조②)부터 위반입니다."},
        {"kind": "short", "q": "김민준(Kim Min-jun)이 검수한 상품 중 의학적 효능 표현 규정을 위반했음에도 Pass(승인) 처리된 상품의 상품 코드를 오름차순으로 나열해 주세요. (띄어쓰기 없이 ,로 구분해 입력해 주세요. 예: `MDL-03,PYB-01`)",
         "answer": "CPL-02,HNK-01", "accept": ["CPL-02,HNK-01"],
         "explain": "김민준은 INS 03(부록 A)이며 사양서에는 영문 'Kim Min-jun · INS 03'으로 기재됩니다. CPL-02('햇빛 알레르기 치료')와 HNK-01('세포 재생')이 제5조 위반인데 Pass입니다. 함정: DRG-03은 위반이지만 Fail, NVL-03은 일반 화장품의 '미백에 도움'으로 제6조(기능성 표시 범위) 위반이지 제5조가 아니며, SKD-02('아토피 피부 개선')는 Pass이지만 검수자가 김민주(Kim Min-ju, INS 05)입니다."},
        {"kind": "short", "q": "성분 배합 한도 또는 금지 원료 규정을 위반하여 등록이 거부되어야 함에도 불구하고, 검수자가 잘못 승인으로 처리한 상품의 상품 코드를 오름차순으로 나열해 주세요. (띄어쓰기 없이 ,로 구분해 입력해 주세요. 예: `MDL-03,PYB-01`)",
         "answer": "AQV-02,LMN-01,PYB-03", "accept": ["AQV-02,LMN-01,PYB-03"],
         "explain": "AQV-02(나이아신아마이드 7.0% > 5.0%, 제7조), LMN-01(씻어내지 않는 제품에 MIT, 02 업데이트 2절①), PYB-03(금지 원료 하이드로퀴논, 제8조)이 Pass입니다. 함정: ODM-03 레티놀 0.8%는 현행 한도 1.0% 이내이고 0.5% 하향은 2026-07-01 시행 예정이라 4월 검수에 적용하지 않습니다. DRG-01·PYB-02·LMN-02의 MIT는 씻어내는 제품의 0.0015% 이하라 허용, HNK-03·ODM-02·TRH-03·GNH-02는 위반이지만 Fail입니다."},
        {"kind": "short", "q": "한국 기준으로는 등록 가능하지만 EU 추가 규제를 통과하지 못하는 상품들의 상품 코드를 오름차순으로 나열해 주세요. (띄어쓰기 없이 ,로 구분해 입력해 주세요. 예: `MDL-03,PYB-01`)",
         "answer": ",".join(q4), "accept": [",".join(q4)],
         "explain": "CPL-03(옥시벤존 4.0% > EU 2.2%), MDL-02(씻어내지 않는 제품 리모넨 0.012% 미표기), NVL-01(레티놀 0.5% > EU 0.3%), SKD-01(동물실험 실시), YHC-02(나노 원료 [nano] 미표기). 검수 상태(Pass/Fail)와 무관하게 규정으로 판정합니다. 함정: EU 미배송 상품(CPL-01·YHC-01), 한국 기준부터 위반인 상품(DRG-03·YHC-03·BLS-01·LMN-01), 기준 이하 향료(BWB-01·HNK-02·BLS-03)·씻어내는 제품 기준(MDL-03·SKD-03), 시행 예정인 알파-알부틴 한도(AQV-03), 한도와 같은 값(BWB-03 레티놀 0.30%)은 제외입니다."},
    ],
}
json.dump(problem, open(os.path.join(HERE, "problem.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
print("files", len(files), "chars", sum(len(f["content"]) for f in files))
