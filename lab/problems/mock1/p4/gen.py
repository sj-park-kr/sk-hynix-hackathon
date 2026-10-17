import json, os, random
from collections import Counter
from datetime import date, datetime

HERE = os.path.dirname(os.path.abspath(__file__))
R = random.Random(20261018)
D = date.fromisoformat
P0, P1 = D("2026-09-01"), D("2026-09-30")          # 9월 정기 감사 대상 기간
EXT = ("EX-TR", "EX-CODE", "EX-CHAT")
TH = 5                                             # 재교육 기준 점수(이상)

# ---------- 인원: key -> (성명, 직책, 등록부서 = 게이트웨이 계정 발급 당시 부서) ----------
PEOPLE = {
 "os1": ("한지석", "팀장", "해외영업팀"), "os2": ("오세린", "책임", "해외영업팀"), "os3": ("문태호", "선임", "해외영업팀"),
 "os4": ("백나연", "매니저", "해외영업팀"), "osF": ("서동민", "책임", "해외영업팀"), "osA": ("류하준", "선임", "해외영업팀"),
 "mk1": ("정유라", "팀장", "마케팅팀"), "mk2": ("남궁별", "선임", "마케팅팀"), "mk3": ("차민서", "매니저", "마케팅팀"), "mkB": ("윤지후", "선임", "마케팅팀"),
 "sw1": ("강도현", "팀장", "SW개발팀"), "sw2": ("임서진", "책임", "SW개발팀"), "sw3": ("조은재", "선임", "SW개발팀"),
 "sw4": ("황보윤", "매니저", "SW개발팀"), "swC": ("신재원", "책임", "SW개발팀"),
 "eq1": ("권태식", "팀장", "설비기술팀"), "eq2": ("배수민", "책임", "설비기술팀"), "eq3": ("노현우", "선임", "설비기술팀"), "eqE": ("진가람", "선임", "설비기술팀"),
 "qa1": ("전하늘", "팀장", "품질보증팀"), "qa2": ("송다온", "책임", "품질보증팀"), "qa3": ("마준혁", "선임", "품질보증팀"), "qaD": ("엄소율", "선임", "품질보증팀"),
 "pu1": ("곽민재", "팀장", "구매팀"), "pu2": ("하윤슬", "책임", "구매팀"), "pu3": ("탁지민", "선임", "품질보증팀"),
 "pe1": ("변상우", "팀장", "공정기술팀"), "pe2": ("석주원", "책임", "공정기술팀"), "pe3": ("우채린", "선임", "인사팀"),
 "hr1": ("피정호", "팀장", "인사팀"), "hr2": ("길소연", "책임", "인사팀"), "hr3": ("연우진", "매니저", "인사팀"),
}
DEPTS = ["해외영업팀", "마케팅팀", "SW개발팀", "설비기술팀", "품질보증팀", "구매팀", "공정기술팀", "인사팀"]
EMP = dict(zip(PEOPLE, (f"E{n}" for n in R.sample(range(2001, 3000), len(PEOPLE)))))
KEY = {v: k for k, v in EMP.items()}
# 인사 발령(발령일 00:00부터 새 부서). 등록부서는 갱신되지 않음, 10/01 발령은 감사 기간 후(현 조직도 함정)
MOVES = [("pe3", "2026-07-13", "인사팀", "공정기술팀"), ("pu3", "2026-07-20", "품질보증팀", "구매팀"),
         ("eqE", "2026-08-17", "설비기술팀", "구매팀"), ("mkB", "2026-09-01", "마케팅팀", "해외영업팀"),
         ("qaD", "2026-09-07", "품질보증팀", "설비기술팀"), ("osA", "2026-09-14", "해외영업팀", "공정기술팀"),
         ("swC", "2026-10-01", "SW개발팀", "인사팀"), ("osF", "2026-10-01", "해외영업팀", "마케팅팀")]


def dept_at(k, d, mode="hr"):
    dep = PEOPLE[k][2]
    if mode == "reg": return dep
    for kk, day, a, b in MOVES:
        if kk == k and (mode == "cur" or D(day) <= d): assert dep == a; dep = b
    return dep


CUR = {k: dept_at(k, None, "cur") for k in PEOPLE}

# ---------- 02 예외 승인 대장 ----------
APPR = [
 dict(id="EX-01", dept="해외영업팀", svc="EX-TR", sens=(), s="2026-07-01", e="2026-09-15", st="승인", note="연 2회 갱신"),
 dict(id="EX-02", dept="해외영업팀", svc="EX-TR", sens=(), s="2026-09-16", e="2026-12-31", st="신청중", note="EX-01 갱신 신청(정보보호팀 검토 중)"),
 dict(id="EX-03", dept="SW개발팀", svc="EX-CODE", sens=("소스코드",), s="2026-08-01", e="2026-10-31", st="승인", note="오픈소스 연계 개발 과제"),
 dict(id="EX-04", dept="SW개발팀", svc="EX-CHAT", sens=(), s="2026-07-01", e="2026-09-10", st="승인", note="기술 문서 초안 작성"),
 dict(id="EX-05", dept="설비기술팀", svc="EX-CHAT", sens=(), s="2026-06-01", e="2026-08-31", st="승인", ext="2026-09-30",
      note="2026-08-27 연장 승인: 종료일 2026-09-30으로 변경"),
 dict(id="EX-06", dept="품질보증팀", svc="EX-TR", sens=(), s="2026-08-01", e="2026-12-31", st="승인", term="2026-09-21",
      note="2026-09-21 조기 종료(보안 점검)"),
 dict(id="EX-07", dept="마케팅팀", svc="EX-CHAT", sens=(), s="2026-09-01", e="2026-11-30", st="반려", note="고객 데이터 입력 우려로 반려"),
 dict(id="EX-08", dept="구매팀", svc="EX-TR", sens=(), s="2026-09-01", e="2026-09-30", st="승인", note="해외 공급사 계약서 번역"),
 dict(id="EX-09", dept="공정기술팀", svc="EX-TR", sens=(), s="2026-09-22", e="2026-12-31", st="승인", note="해외 학회 자료 번역"),
]

# ---------- 03 게이트웨이 로그: 의도적 배치(키, 일시, 서비스, 입력등급, 민감정보, 차단) ----------
EV = [
 # 해외영업팀(EX-01 9/15 종료, EX-02 신청중)
 ("os1", "09-02", "EX-TR", "내부", "없음", "N"), ("os1", "09-09", "EX-TR", "내부", "없음", "N"),
 ("os1", "09-15 23:10", "EX-TR", "내부", "없음", "N"),                                   # 종료일 당일 → 유효
 ("os1", "09-25", "IN-LLM", "대외비", "고객사정보", "W"),                                  # W지만 위반 아님
 ("os2", "09-04", "EX-TR", "내부", "없음", "N"), ("os2", "09-17", "EX-TR", "내부", "없음", "N"),  # 만료 후
 ("os2", "09-11", "CL-LLM", "대외비", "없음", "W"),
 ("os3", "09-03", "EX-TR", "내부", "없음", "N"), ("os3", "09-10", "EX-TR", "내부", "없음", "N"),
 ("os3", "09-24", "EX-TR", "내부", "개인정보", "Y"),                                     # 만료 후지만 승인 있어도 V2
 ("os3", "09-16", "CL-LLM", "내부", "고객사정보", "W"),
 ("os4", "08-31 16:40", "CL-LLM", "대외비", "없음", "W"), ("os4", "09-08", "EX-TR", "내부", "없음", "N"),
 ("os4", "09-24 22:50", "CL-LLM", "대외비", "없음", "W"), ("os4", "10-01 09:12", "EX-TR", "내부", "없음", "N"),  # 기간 외
 ("osF", "09-05", "EX-TR", "내부", "없음", "N"), ("osF", "09-12", "EX-TR", "내부", "없음", "N"),
 ("osF", "09-19", "CL-LLM", "대외비", "없음", "W"), ("osF", "09-26", "CL-LLM", "내부", "개인정보", "W"),
 ("osA", "09-07", "EX-TR", "내부", "없음", "N"), ("osA", "09-14", "EX-TR", "내부", "없음", "N"),  # 9/14 공정기술팀 이동
 ("osA", "09-15", "EX-TR", "내부", "없음", "N"), ("osA", "09-18 23:30", "EX-TR", "내부", "없음", "N"),
 ("osA", "09-24", "EX-TR", "내부", "없음", "N"),                                         # EX-09(9/22~) 유효
 # 마케팅팀(EX-07 반려) / mkB는 9/1 해외영업팀 이동
 ("mkB", "09-03", "EX-TR", "내부", "없음", "N"), ("mkB", "09-17", "EX-TR", "내부", "없음", "N"),
 ("mkB", "09-23", "EX-TR", "내부", "없음", "N"), ("mkB", "09-28", "EX-TR", "내부", "없음", "N"),
 ("mkB", "09-21", "CL-LLM", "대외비", "없음", "W"),
 ("mk1", "09-02", "EX-CHAT", "내부", "없음", "Y"), ("mk1", "09-15", "EX-CHAT", "공개", "개인정보", "N"),
 ("mk2", "09-08", "EX-CHAT", "내부", "개인정보", "Y"), ("mk2", "09-19", "EX-CHAT", "공개", "고객사정보", "Y"),
 ("mk2", "09-25", "EX-CHAT", "내부", "없음", "N"),
 ("mk3", "09-10", "EX-CHAT", "공개", "없음", "Y"), ("mk3", "09-29", "CL-LLM", "대외비", "없음", "W"),
 ("hr3", "09-15", "EX-CHAT", "내부", "없음", "W"),
 # SW개발팀(EX-03 EX-CODE 소스코드, EX-04 EX-CHAT 9/10 종료) / swC는 10/1 인사팀 이동
 ("sw1", "09-03", "EX-CODE", "내부", "소스코드", "N"), ("sw1", "09-15", "EX-CODE", "내부", "소스코드", "N"),
 ("sw1", "09-24", "EX-CODE", "공개", "소스코드", "N"), ("sw1", "09-17", "EX-CODE", "대외비", "소스코드", "W"),  # V3+V4
 ("sw2", "09-04", "EX-CHAT", "내부", "없음", "N"), ("sw2", "09-12 23:41", "EX-CHAT", "내부", "없음", "Y"),  # 파일 경계 중복
 ("sw2", "09-22", "CL-LLM", "대외비", "없음", "W"),
 ("sw3", "09-05", "EX-CHAT", "내부", "소스코드", "W"), ("sw3", "09-20", "EX-TR", "공개", "소스코드", "W"),
 ("sw4", "09-09", "EX-CODE", "공개", "소스코드", "N"), ("sw4", "09-16", "CL-LLM", "내부", "소스코드", "W"),
 ("sw4", "09-26", "IN-LLM", "극비", "없음", "N"), ("sw4", "09-29", "EX-TR", "내부", "없음", "N"),
 ("swC", "09-06", "EX-CHAT", "내부", "없음", "N"), ("swC", "09-14", "EX-CHAT", "내부", "없음", "N"),
 ("swC", "09-18", "EX-CHAT", "내부", "없음", "N"), ("swC", "09-25", "CL-LLM", "대외비", "없음", "W"),
 # 설비기술팀(EX-05 연장 9/30) / qaD 9/7 전입, eqE 8/17 구매팀 전출
 ("eq1", "09-02", "EX-CHAT", "내부", "없음", "N"), ("eq1", "09-16", "EX-CHAT", "내부", "없음", "N"),
 ("eq1", "09-28", "EX-CHAT", "내부", "없음", "N"), ("eq1", "09-09", "CL-LLM", "대외비", "없음", "W"),
 ("eq2", "09-11", "CL-LLM", "대외비", "없음", "W"), ("eq2", "09-20", "CL-LLM", "대외비", "없음", "W"),  # 9/20 재전송 중복
 ("eq2", "09-29", "EX-TR", "내부", "없음", "W"),
 ("eq3", "09-13", "CL-LLM", "대외비", "고객사정보", "Y"), ("eq3", "09-23", "CL-LLM", "대외비", "없음", "W"),
 ("eq3", "09-30", "EX-TR", "내부", "없음", "W"),
 ("eqE", "09-08", "EX-TR", "내부", "없음", "N"), ("eqE", "09-19", "EX-CHAT", "내부", "없음", "N"),
 ("qaD", "09-15", "EX-CHAT", "내부", "없음", "N"), ("qaD", "09-25", "EX-CHAT", "내부", "없음", "N"),
 ("qaD", "09-22", "EX-TR", "내부", "없음", "N"),
 # 품질보증팀(EX-06 9/21 조기 종료)
 ("qa1", "09-10", "EX-TR", "내부", "없음", "N"), ("qa1", "09-20", "EX-TR", "내부", "없음", "N"),
 ("qa1", "09-21 08:20", "EX-TR", "내부", "없음", "N"),
 ("qa2", "09-15", "EX-TR", "내부", "없음", "N"), ("qa2", "09-24", "CL-LLM", "공개", "개인정보", "W"),
 ("qa3", "09-03", "CL-LLM", "대외비", "없음", "W"), ("qa3", "09-17", "EX-CHAT", "극비", "없음", "Y"),
 ("qa3", "09-27", "CL-LLM", "내부", "없음", "Y"),                                        # 오탐 차단
 ("qa2", "09-18", "EX-CHAT", "내부", "없음", "W"),
 # 구매팀(EX-08 EX-TR 9월)
 ("pu1", "09-04", "EX-TR", "내부", "없음", "N"), ("pu1", "09-18", "EX-TR", "내부", "없음", "N"),
 ("pu1", "09-10", "EX-CHAT", "내부", "없음", "N"), ("pu1", "09-24", "CL-LLM", "대외비", "없음", "W"),
 ("pu2", "09-07", "CL-LLM", "대외비", "없음", "W"), ("pu2", "09-21", "CL-LLM", "공개", "소스코드", "W"),
 ("pu3", "09-30 23:20", "EX-TR", "내부", "없음", "N"), ("pu3", "09-14", "IN-LLM", "내부", "없음", "Y"),
 ("pu2", "09-28", "EX-CODE", "내부", "없음", "W"),
 # 공정기술팀(EX-09 9/22 시작)
 ("pe1", "09-17", "EX-TR", "내부", "없음", "N"), ("pe1", "09-23", "EX-TR", "내부", "없음", "N"),
 ("pe2", "09-14", "CL-LLM", "대외비", "없음", "W"), ("pe2", "09-21", "IN-LLM", "대외비", "고객사정보", "W"),
 ("pe3", "09-09", "IN-LLM", "극비", "없음", "N"),
 # 인사팀
 ("hr1", "09-05", "CL-LLM", "내부", "개인정보", "Y"), ("hr1", "09-18", "CL-LLM", "내부", "개인정보", "W"),
 ("hr2", "09-11", "EX-CHAT", "공개", "개인정보", "Y"), ("hr2", "09-12", "EX-CHAT", "내부", "없음", "Y"),
 ("hr3", "09-08", "IN-LLM", "대외비", "개인정보", "W"), ("hr3", "09-29", "CL-LLM", "대외비", "없음", "W"),
]


def rtime(): return f"{R.randint(8, 19):02d}:{R.randint(0, 59):02d}"


def mk(k, md, sv, g, s, b):
    day, _, hm = md.partition(" ")
    return dict(k=k, dt=datetime.fromisoformat(f"2026-{day} {hm or rtime()}"), svc=sv, g=g, s=s, b=b)


def filler(k, dt):
    dep = dept_at(k, dt.date())
    sv = R.choices(["IN-LLM", "CL-LLM", "EXT"], [45, 35, 20])[0]
    if sv == "IN-LLM":
        g = R.choices(["공개", "내부", "대외비"], [2, 5, 3])[0]
        sp = {"SW개발팀": "소스코드", "인사팀": "개인정보", "해외영업팀": "고객사정보", "품질보증팀": "고객사정보", "마케팅팀": "고객사정보"}.get(dep, "없음")
        s = R.choices(["없음", sp], [7, 3])[0]
    elif sv == "CL-LLM":
        g = R.choices(["공개", "내부"], [4, 6])[0]
        s = R.choices(["없음", "소스코드"], [9, 4 if dep == "SW개발팀" else 1])[0]
    else:
        sv = R.choices(EXT, [3, 4 if dep == "SW개발팀" else 1, 3])[0]; g, s = "공개", "없음"
    return dict(k=k, dt=dt, svc=sv, g=g, s=s, b="N")


ROWS = [mk(*e) for e in EV]
for d in range(32):
    day = date.fromordinal(D("2026-08-31").toordinal() + d)
    n = 6 if day.month != 9 else (R.randint(14, 18) if day.weekday() < 5 else R.randint(4, 6))
    for _ in range(n): ROWS.append(filler(R.choice(list(PEOPLE)), datetime.fromisoformat(f"{day} {rtime()}")))
ROWS.sort(key=lambda r: r["dt"])
for i, r in enumerate(ROWS): r.update(id=f"R{10001 + i}", d=r["dt"].date())

# 5개 파일로 분할: 경계에서 앞 파일 마지막 행 일부 중복 수록 + 재전송 중복 1건
CUT = [("08-31", "09-06"), ("09-07", "09-12"), ("09-13", "09-18"), ("09-19", "09-24"), ("09-25", "10-01")]
PARTS = [[r for r in ROWS if D(f"2026-{a}") <= r["d"] <= D(f"2026-{b}")] for a, b in CUT]
assert sum(map(len, PARTS)) == len(ROWS)
OVL = [2, 2, 3, 2]
FILES = [PARTS[0]] + [PARTS[i - 1][-OVL[i - 1]:] + PARTS[i] for i in range(1, 5)]
re_i = next(i for i, r in enumerate(FILES[3]) if r["k"] == "eq2" and r["d"] == D("2026-09-20"))
FILES[3].insert(re_i + 4, FILES[3][re_i])
LOG = [r for f in FILES for r in f]
assert any(r["k"] == "sw2" for r in PARTS[1][-2:]) and any(r["k"] == "osA" for r in PARTS[2][-3:])


# ---------- 규칙 엔진 ----------
O = dict(dept="hr", noext=False, noterm=False, termincl=False, pending=False, endexcl=False, dup=False, oop=False,
         wblk=False, allw=False, bfull=False, ball=False, summ=False, gt=False, blkx=False, anyv=False, scope=False)


def opt(**kw): return {**O, **kw}


def window(a, o):
    e = a.get("ext") if a.get("ext") and not o["noext"] else a["e"]
    t = a.get("term") if a.get("term") and not o["noterm"] else None
    return D(a["s"]), D(e), D(t) if t else None


def after_end(a, d, o):
    s, e, t = window(a, o)
    return d > e or (o["endexcl"] and d == e) or (t is not None and (d > t if o["termincl"] else d >= t))


def active(a, d, o):
    if a["st"] != "승인" and not (o["pending"] and a["st"] == "신청중"): return False
    return D(a["s"]) <= d and not after_end(a, d, o)


def appr(r, o):
    dep = dept_at(r["k"], r["d"], o["dept"])
    return next((a for a in APPR if a["dept"] == dep and a["svc"] == r["svc"] and active(a, r["d"], o)), None)


NO = object()


def viol(r, o, a=NO):
    sv, g, s = r["svc"], r["g"], r["s"]; ext = sv in EXT
    if a is NO: a = appr(r, o) if ext else None
    if a and g in ("대외비", "극비") and not o["scope"]: a = None   # 7.4 최대등급(내부) 초과 로그에는 승인 미적용
    v = []
    if g == "극비": v.append(("V1", 5))
    if s in ("개인정보", "고객사정보") and sv != "IN-LLM": v.append(("V2", 5))
    if g == "대외비" and sv != "IN-LLM": v.append(("V3", 3))
    if s == "소스코드" and ext and not (a and "소스코드" in a["sens"]): v.append(("V4", 3))
    if g == "내부" and ext and not a: v.append(("V5", 1))
    return v


def pts(r, o):
    v = [p for _, p in viol(r, o)]
    return (sum(v) if o["summ"] else max(v)) if v else 0


def rows(o):
    seen, out = set(), []
    for r in LOG:
        if not o["dup"]:
            if r["id"] in seen: continue
            seen.add(r["id"])
        if o["oop"] or P0 <= r["d"] <= P1: out.append(r)
    return out


def unblk(o):
    return [r for r in rows(o) if (viol(r, o) or (o["allw"] and r["b"] == "W")) and not (r["b"] == "Y" or (o["wblk"] and r["b"] == "W"))]


def q1(**kw): return len(unblk(opt(**kw)))


def by_dept(o): return Counter(dept_at(r["k"], r["d"], o["dept"]) for r in unblk(o))


def q2(**kw):
    c = by_dept(opt(**kw)).most_common(); top = [d for d, n in c if n == c[0][1]]
    assert kw or len(top) == 1, c
    return f"{'·'.join(top)}/{c[0][1]}"


def expired(r, o):
    if r["svc"] not in EXT or not viol(r, o): return False
    dep = dept_at(r["k"], r["d"], o["dept"])
    return any(a["dept"] == dep and a["svc"] == r["svc"] and a["st"] == "승인" and D(a["s"]) <= r["d"] and after_end(a, r["d"], o)
               and (o["anyv"] or not viol(r, o, a)) for a in APPR)


def q3_keys(o): return sorted({r["k"] for r in rows(o) if expired(r, o) and not (o["blkx"] and r["b"] == "Y")}, key=EMP.get)
def q3(**kw): return "-".join(EMP[k] for k in q3_keys(opt(**kw))) or "없음"


def scores(o):
    sc = Counter({k: 0 for k in PEOPLE})
    for r in rows(o):
        v = viol(r, o)
        if r["b"] == "Y": sc[r["k"]] += (pts(r, o) if o["bfull"] else 1) if v else (1 if o["ball"] else 0)
        else: sc[r["k"]] += pts(r, o)
    return sc


def targets(**kw):
    o = opt(**kw); return sorted((k for k, v in scores(o).items() if (v > TH if o["gt"] else v >= TH)), key=EMP.get)


def share(o, f):
    u = unblk(o); return sum(map(f, u)), len(u)


# ---------- 정답 계산·함정 고정 ----------
a1 = q1()
t1 = {"요청ID 중복(파일 경계·재전송) 미제거": q1(dup=True), "기간 외(8/31·10/1) 로그 포함": q1(oop=True),
      "W(경고 후 진행)를 차단으로 봄": q1(wblk=True), "W 로그를 모두 위반으로 봄": q1(allw=True),
      "로그 등록부서로 예외 승인 판정": q1(dept="reg"), "현 조직도(10/05) 부서로 예외 승인 판정": q1(dept="cur"),
      "EX-05 연장 미반영": q1(noext=True), "EX-06 조기 종료 미반영": q1(noterm=True), "EX-02(신청중)를 유효로 봄": q1(pending=True)}
for k, v in t1.items(): assert v != a1, k

a2 = q2()
t2 = {"로그 등록부서로 귀속": q2(dept="reg"), "현 조직도(10/05) 부서로 귀속": q2(dept="cur"), "요청ID 중복 미제거": q2(dup=True)}
for k, v in t2.items(): assert v != a2, k

a3 = q3()
t3 = {"로그 등록부서 기준": q3(dept="reg"), "현 조직도 기준": q3(dept="cur"), "EX-05 연장 미반영": q3(noext=True),
      "EX-06 조기 종료 미반영": q3(noterm=True), "조기 종료일 당일까지 유효로 봄": q3(termincl=True),
      "EX-02(신청중)를 유효로 봄": q3(pending=True), "차단(Y) 로그 제외": q3(blkx=True), "기간 외 로그 포함": q3(oop=True),
      "종료일 당일을 무효로 봄": q3(endexcl=True), "승인이 있어도 위반인 로그 포함": q3(anyv=True)}
for k, v in t3.items(): assert v != a3, k

N = len(targets())
TN = {"차단 위반에도 등급 점수 전액": len(targets(bfull=True)), "위반 항목 점수 합산": len(targets(summ=True)),
      "오탐 차단도 1점": len(targets(ball=True)), "요청ID 중복 미제거": len(targets(dup=True)),
      "기간 외 로그 포함": len(targets(oop=True)), "5점 초과만 대상": len(targets(gt=True))}
for k, v in TN.items(): assert v != N, k
N_bf, N_sum = TN["차단 위반에도 등급 점수 전액"], TN["위반 항목 점수 합산"]
assert len({N, N_bf, N_sum}) == 3

W, U = share(O, lambda r: r["b"] == "W")
L1, _ = share(O, lambda r: pts(r, O) == 1)
L5, _ = share(O, lambda r: pts(r, O) == 5)
assert U == a1 and 2 * W > U and 2 * L1 < U and 2 * L5 < U and W / U >= 0.58
ow = opt(wblk=True); L1w, Uw = share(ow, lambda r: pts(r, ow) == 1)
assert 2 * L1w > Uw   # W를 차단으로 보면 '1점 위반 과반'이 참처럼 보임
truth = [False, False, True, False, False]   # 보기 1~5 근거의 참·거짓(아래 문구와 1:1)
prem = [N_bf == N, 2 * L1 > U, 2 * W > U, N_sum == N and 2 * W > U, 2 * L5 > U]
assert prem == truth
a4 = truth.index(True) + 1

# ---------- 파일 텍스트 ----------
POLICY = """[p.1]
ㅇㅇ반도체 사내 생성형 AI 이용 보안 정책
문서번호 SEC-AI-003 | 개정 4판 | 시행 2026-07-01 | 주관 정보보호팀 | 보안등급 내부

1. 목적
본 정책은 임직원이 업무에 생성형 AI를 이용할 때 회사 정보자산의 유출을 막고, 사내 AI 게이트웨이(이하 '게이트웨이') 이용 기록을 근거로 위반을 판정·조치하는 기준을 정한다.

2. 적용 범위
2.1 모든 임직원(파견·협력사 상주 인력 포함)이 회사 단말 또는 회사망에서 이용하는 생성형 AI 서비스에 적용한다.
2.2 회사망에서 AI 서비스 접속은 게이트웨이를 경유해야 한다. 게이트웨이를 우회한 접속은 네트워크 보안 규정(SEC-NW-011)으로 처리하며 본 정책의 감사 범위가 아니다.
2.3 AI가 생성한 결과물의 저작권·품질 책임은 이용자에게 있다(10장 참고).

3. 데이터 등급
| 등급 | 정의 | 예시 |
| 공개 | 대외 공개되었거나 공개해도 무방한 정보 | 보도자료, 공개 논문, 홈페이지 게시물 |
| 내부 | 임직원에게만 공개되는 정보 | 사내 공지, 일반 회의록, 업무 메일 |
| 대외비 | 관련 부서·인원에게만 공개, 유출 시 경영상 손실 | 공정 조건, 수율 데이터, 원가, 고객 견적 |
| 극비 | 지정 인원만 열람, 유출 시 회복 불가 | 차세대 제품 설계, 핵심 공정 레시피, 미공개 투자 계획 |
3.1 입력 등급은 게이트웨이가 문서 보안 라벨과 입력 내용을 분석해 자동으로 태그하며, 로그의 '입력등급'에 기록한다.
3.2 이용자가 등급을 낮춰 표시하더라도 위반 판정은 로그의 '입력등급' 태그를 따른다.

4. AI 서비스 구분
| 코드 | 서비스 | 구분 |
| IN-LLM | 사내 구축형 LLM(사내 데이터센터 운영) | 사내 |
| CL-LLM | 계약형 클라우드 LLM(데이터 미학습·국내 리전 계약) | 계약 |
| EX-TR | 외부 번역 서비스 | 외부 |
| EX-CODE | 외부 코딩 보조 서비스 | 외부 |
| EX-CHAT | 외부 범용 대화형 AI | 외부 |
4.1 코드가 'EX-'로 시작하는 서비스를 '외부 서비스'라 한다.
4.2 신규 서비스 도입은 정보보호팀 보안성 검토와 CIO 승인을 거쳐 본 표에 등재한 뒤 게이트웨이에 연결한다.

[p.2]
5. 등급별 허용 서비스
| 입력등급 | IN-LLM | CL-LLM | 외부 서비스(EX-*) |
| 공개 | 허용 | 허용 | 허용 |
| 내부 | 허용 | 허용 | 금지(유효한 예외 승인이 있으면 허용, 7장) |
| 대외비 | 허용 | 금지 | 금지(예외 승인 불가) |
| 극비 | 금지 | 금지 | 금지 |
5.1 극비는 사내 구축형 LLM(IN-LLM)을 포함한 모든 AI 서비스에 입력할 수 없다.

6. 민감정보 입력 규칙
6.1 게이트웨이는 입력 내용에서 민감정보를 탐지해 로그의 '민감정보'에 기록한다(없음/개인정보/고객사정보/소스코드).
6.2 민감정보 규칙은 입력등급과 별개로 적용한다. 입력등급이 '공개'로 태그되었더라도 민감정보가 탐지되면 아래 표를 따른다.
| 민감정보 | IN-LLM | CL-LLM | 외부 서비스(EX-*) |
| 개인정보(주민번호·연락처·계좌·사번+성명 등) | 허용 | 금지 | 금지(예외 승인 불가) |
| 고객사정보(고객사명과 제품·물량·단가가 함께 있는 정보) | 허용 | 금지 | 금지(예외 승인 불가) |
| 소스코드 | 허용 | 허용 | 금지(유효한 예외 승인의 '허용민감정보'에 소스코드가 있으면 허용) |
6.3 프롬프트 작성 시 유의사항(권고, 위반 판정 대상 아님)
- 고객 응대 초안은 고객 실명·연락처 대신 '고객 A'처럼 가명을 쓰고, 발송 전 담당자가 사실관계를 확인한다.
- 사내 가이드·규정을 요약시킬 때는 원문 조항 번호를 함께 출력하게 해 근거를 대조한다.
- 수치 계산·집계는 AI 답변을 그대로 쓰지 말고 원자료로 검산한다.
- 긴 자료는 필요한 부분만 잘라 입력하고, 중간 결과는 표로 정리해 다음 질문에 사용한다.

[p.3]
7. 외부 서비스 예외 승인
7.1 절차: 부서장 신청 → 정보보호팀 보안성 검토 → 승인 또는 반려. 02 예외 승인 대장에 등재된 건만 효력이 있다.
7.2 상태: '승인'인 건만 효력이 있다. '신청중'(검토 중)과 '반려'는 효력이 없다.
7.3 대상: 예외 승인은 부서 단위로 부여하며, 사용 일시 기준으로 그 부서에 소속된 임직원에게만 적용한다. 부서를 옮긴 임직원에게는 발령일부터 이전 부서의 승인이 적용되지 않고, 새 부서의 승인이 적용된다.
7.4 범위: 승인은 대장에 적힌 서비스 1개에만 효력이 있다. 입력등급은 '최대등급'까지만 허용하며, 입력등급이 최대등급을 넘는 로그에는 그 승인이 적용되지 않는다(그 로그의 민감정보 허용도 인정되지 않는다). 민감정보는 '허용민감정보'에 적힌 유형만 허용하며 '없음'은 민감정보 허용이 없다는 뜻이다.
7.5 유효기간: 시작일 00:00부터 종료일 23:59까지다. 비고에 '연장 승인'이 기재되면 변경된 종료일을 적용한다. 비고에 '조기 종료'가 기재되면 그 날짜 00:00부터 효력을 잃는다.
7.6 갱신: 종료일 14일 전까지 갱신을 신청해야 한다. 갱신 신청 건은 '승인' 처리 전까지 효력이 없으며, 기존 승인 종료일 다음 날부터의 사용은 승인 없는 사용이다.
7.7 예외 승인 부서는 분기별로 사용 내역을 정보보호팀에 보고한다.

8. 위반 판정과 점수
8.1 로그 1건(요청ID 기준)마다 아래 항목을 각각 판정하고, 하나 이상 해당하면 '위반'이다.
| 코드 | 위반 내용 | 위반 등급 | 점수 |
| V1 | 극비 입력(모든 서비스) | 심각 | 5 |
| V2 | 개인정보·고객사정보를 IN-LLM 외 서비스에 입력 | 심각 | 5 |
| V3 | 대외비를 IN-LLM 외 서비스에 입력 | 중대 | 3 |
| V4 | 소스코드를 외부 서비스에 입력(유효한 예외 승인의 허용민감정보에 소스코드가 없는 경우) | 중대 | 3 |
| V5 | 내부 등급을 외부 서비스에 입력(그 서비스에 유효한 예외 승인이 없는 경우) | 경미 | 1 |
8.2 한 로그가 여러 항목에 해당해도 위반은 1건이며, 그 로그의 점수는 해당 항목 중 가장 높은 점수 하나만 적용한다(합산하지 않는다).
8.3 '유효한 예외 승인'은 7장의 상태·대상·범위·유효기간을 모두 충족하는 승인을 말한다.

[p.4]
9. 감사 집계 기준
9.1 대상 기간: 감사 차수별로 정한다. 2026년 9월 정기 감사는 일시가 2026-09-01 00:00부터 2026-09-30 23:59까지인 로그만 집계한다.
9.2 중복: 로그 내보내기 분할 경계나 게이트웨이 재전송으로 같은 요청ID가 여러 행에 기록될 수 있다. 같은 요청ID는 1건으로 본다.
9.3 차단: 로그의 '차단' 값은 Y(게이트웨이가 전송을 막음), W(경고를 표시했으나 이용자가 사유를 입력하고 전송함), N(전송함) 중 하나다. W와 N은 차단되지 않은 것으로 본다.
9.4 미차단 위반: 위반이면서 차단 값이 W 또는 N인 로그. 감사 보고서의 '위반 건수'는 미차단 위반 건수를 말한다.
9.5 부서 귀속: 위반은 사용 일시 기준 인사상 소속 부서에 귀속한다. 소속 부서는 04 조직도의 인사 발령 이력으로 판정하며 발령일 00:00부터 새 부서 소속이다. 로그의 '등록부서'는 게이트웨이 계정 발급 당시 부서로, 인사 발령이 반영되지 않는다. 예외 승인 적용(7.3)도 같은 기준을 따른다.

10. 재교육과 조치
10.1 개인별 위반 점수: 감사 대상 기간 로그(9.1·9.2 적용)의 점수를 개인별로 합산한다.
- 미차단 위반: 8장의 점수
- 차단(Y)된 위반: 위반 등급과 관계없이 1점(시도 점수)
- 차단(Y)되었으나 위반이 아닌 로그(오탐): 0점
10.2 개인별 위반 점수가 5점 이상이면 재교육 대상이다(정보보호 교육 4시간, 감사 결과 통보 다음 달 15일까지 이수).
10.3 재교육 대상자의 부서장에게 결과를 통보하며, 2개 분기 연속 대상자는 인사위원회에 회부할 수 있다.
10.4 AI 결과물을 사실 확인 없이 대외 발송해 문제가 생긴 경우 별도 징계 기준을 따른다.

11. 개정 이력
| 판 | 시행일 | 주요 내용 |
| 4판 | 2026-07-01 | '경고 후 진행(W)' 도입: 대외비·민감정보 탐지 시 즉시 차단 대신 경고 후 사유를 입력하면 전송 허용(업무 연속성 확보, 분기 감사로 사후 통제) |
| 3판 | 2026-01-02 | 외부 서비스 예외 승인을 개인 단위에서 부서 단위로 변경 |
| 2판 | 2025-07-01 | 계약형 클라우드 LLM(CL-LLM) 도입 |
문의: 정보보호팀 AI보안파트(내선 4410)"""

LEDGER = "승인번호,부서,서비스,최대등급,허용민감정보,시작일,종료일,상태,비고\n" + "\n".join(
    f"{a['id']},{a['dept']},{a['svc']},내부,{'/'.join(a['sens']) or '없음'},{a['s']},{a['e']},{a['st']},{a['note']}" for a in APPR)
assert all("," not in a["note"] for a in APPR)


def org_text():
    p1 = ["[p.1]", "ㅇㅇ반도체 조직도(2026-10-05 기준, 인사팀 발행)", "※ 2026-10-05 현재 소속 기준이며 과거 소속은 다음 쪽 인사 발령 이력을 확인할 것", ""]
    for dep in DEPTS:
        ms = sorted((k for k in PEOPLE if CUR[k] == dep), key=lambda k: (PEOPLE[k][1] != "팀장", EMP[k]))
        p1 += [f"■ {dep} ({len(ms)}명)", "| 사번 | 성명 | 직책 |"] + [f"| {EMP[k]} | {PEOPLE[k][0]} | {PEOPLE[k][1]} |" for k in ms] + [""]
    p2 = ["[p.2]", "인사 발령 이력(2026-07-01 ~ 2026-10-05)", "※ 발령일 00:00부터 새 부서 소속으로 본다.",
          "| 발령일 | 사번 | 성명 | 이전 부서 | 이후 부서 | 사유 |"]
    why = {"pe3": "직무 전환", "pu3": "조직 개편", "eqE": "직무 전환", "mkB": "해외 마케팅 통합", "qaD": "설비 품질 협업 강화",
           "osA": "공정 연계 영업 지원", "swC": "HR 시스템 구축 TF", "osF": "글로벌 브랜드 TF"}
    p2 += [f"| {day} | {EMP[k]} | {PEOPLE[k][0]} | {a} | {b} | {why[k]} |" for k, day, a, b in MOVES]
    return "\n".join(p1 + p2)


ORG = org_text()
HDR = "요청ID,일시,사번,등록부서,서비스,입력등급,민감정보,차단"
LOGS = [HDR + "\n" + "\n".join(f"{r['id']},{r['dt']:%Y-%m-%d %H:%M},{EMP[r['k']]},{PEOPLE[r['k']][2]},{r['svc']},{r['g']},{r['s']},{r['b']}" for r in f)
        for f in FILES]

F1, F2 = "4_AI보안감사", "4-게이트웨이로그"


def tok(t): return int(round(len(t) * 1.15, -1))


files = [{"name": "01_사내AI_이용보안정책.pdf", "folder": F1, "kind": "pdf", "tokens": tok(POLICY), "content": POLICY},
         {"name": "02_외부AI_예외승인대장.csv", "folder": F1, "kind": "csv", "tokens": tok(LEDGER) + 120, "content": LEDGER}]
files += [{"name": f"03_GW로그_{i}.csv", "folder": F2, "kind": "csv", "tokens": tok(t), "content": t} for i, t in enumerate(LOGS, 1)]
files += [{"name": "04_조직도_인사발령.pdf", "folder": F1, "kind": "pdf", "tokens": tok(ORG), "content": ORG}]
TOT = sum(f["tokens"] for f in files)
NROW = len(LOG)
assert TOT >= 20000 and 400 <= NROW <= 700 and all(f["tokens"] < 10000 for f in files), (TOT, NROW)

summary = f"""ㅇㅇ반도체 정보보호팀 과장인 당신은 사내 생성형 AI 게이트웨이의 **2026년 9월 정기 감사**(대상 기간 2026-09-01 00:00 ~ 2026-09-30 23:59)를 맡았습니다. 보안 정책, 외부 AI 예외 승인 대장, 게이트웨이 사용 로그, 조직도를 대조해 위반을 판정하고 보안위원회 보고 자료를 만들어야 합니다.

- `01_사내AI_이용보안정책.pdf`는 데이터 등급(공개/내부/대외비/극비)별 허용 서비스, 민감정보(개인정보·고객사정보·소스코드) 입력 규칙, 외부 서비스 예외 승인의 효력·범위·유효기간, 위반 항목(V1~V5)과 점수, 감사 집계 기준, 재교육 기준이 담긴 정책 원문입니다.
- `02_외부AI_예외승인대장.csv`는 부서별 외부 서비스(EX-*) 예외 승인 내역(서비스·최대등급·허용민감정보·기간·상태·비고)입니다. 상태와 비고(연장·조기 종료)를 함께 봐야 합니다.
- `{F2}` 폴더의 `03_GW로그_1.csv` ~ `03_GW로그_5.csv`는 게이트웨이 사용 로그(요청ID·일시·사번·등록부서·서비스·입력등급·민감정보·차단)를 내보내기 용량 제한 때문에 기간별로 나눈 파일입니다(합계 약 {round(NROW, -1)}행).
- `04_조직도_인사발령.pdf`는 현재 조직도(2026-10-05 기준)와 2026년 7월 이후 인사 발령 이력입니다.

모든 소문항은 01 정책의 판정(5~8장)·집계(9장)·재교육(10장) 기준을 따릅니다."""


def nm(k): return f"{EMP[k]}({PEOPLE[k][0]})"


def keys(s): return [KEY[x] for x in s.split("-")] if s != "없음" else []


def diff(t):
    a, b = set(keys(a3)), set(keys(t)); return " ".join([*(f"+{EMP[k]}" for k in sorted(b - a, key=EMP.get)), *(f"-{EMP[k]}" for k in sorted(a - b, key=EMP.get))])


DC = by_dept(O).most_common()
dc_s = " / ".join(f"{d} {n}" for d, n in DC)
SC = scores(O); TG = targets()
tg_s = ", ".join(f"{nm(k)} {SC[k]}점" for k in TG)
pct = lambda x: f"{x / U * 100:.1f}%"
mv = {k: (day, a, b) for k, day, a, b in MOVES}

opts = [
 f"재교육 대상은 {N_bf}명이며, 이 중 다수는 차단(Y)된 시도의 위험이 큰데도 1점만 부과되어 실제 위험이 축소 반영되고 있다. → 10.1을 개정해 차단된 위반에도 위반 등급 점수를 그대로 부과한다.",
 f"재교육 대상은 {N}명이며, 미차단 위반의 과반이 점수 1점(경미, V5만 해당) 위반이다. → 02 예외 승인 대장을 인사 발령·게이트웨이와 연동해 사용 시점의 소속 부서와 유효기간을 자동 검증한다.",
 f"재교육 대상은 {N}명이며, 미차단 위반의 과반이 '경고 후 진행(W)' 로그다. → 4판에서 도입한 경고 후 진행을 축소해 대외비·개인정보·고객사정보·소스코드 위반 탐지 시 W 대신 차단(Y)한다.",
 f"재교육 대상은 {N_sum}명이며, 미차단 위반의 과반이 '경고 후 진행(W)' 로그다. → 4판에서 도입한 경고 후 진행을 축소해 대외비·개인정보·고객사정보·소스코드 위반 탐지 시 W 대신 차단(Y)한다.",
 f"재교육 대상은 {N}명이며, 미차단 위반의 과반이 점수 5점(심각) 위반이다. → 개인정보·고객사정보 탐지 패턴을 고도화하고 CL-LLM 이용을 전면 중단한다.",
]

questions = [
 {"kind": "short",
  "q": "[4-1] 9월 정기 감사 대상 기간(2026-09-01 00:00 ~ 2026-09-30 23:59)의 로그를 01 정책 5~8장으로 판정하고 9장 집계 기준(같은 요청ID는 1건, 차단 값 정의)을 적용할 때, **미차단 위반** 건수는 몇 건입니까? 숫자만 정수로 입력하세요. (예: `57`)",
  "answer": str(a1), "accept": [str(a1), f"{a1}건"],
  "explain": f"5개 로그 파일 {NROW}행 중 파일 경계 중복·재전송 중복을 요청ID로 제거하고 8/31·10/1 로그를 빼면 {len(rows(O))}건입니다. 이 중 위반이면서 차단 값이 W·N인 로그가 {a1}건(W {W}건, N {U - W}건)입니다. "
             f"핵심: 예외 승인은 로그의 등록부서가 아니라 사용일 기준 소속 부서로 적용하고(9.5·7.3), EX-01은 9/15까지(EX-02는 신청중이라 무효), EX-05는 연장으로 9/30까지, EX-06은 9/21 00:00부터 무효, EX-09는 9/22부터 유효입니다. "
             f"입력등급이 '공개'여도 개인정보·고객사정보가 탐지되면 V2, IN-LLM이어도 극비는 V1입니다. "
             f"함정 값: " + ", ".join(f"{k} {v}" for k, v in t1.items()) + "."},
 {"kind": "short",
  "q": "[4-2] [4-1]의 미차단 위반을 01 정책 9.5의 부서 귀속 기준으로 부서별로 집계할 때, 건수가 **가장 많은 부서**와 그 건수를 `부서명/건수` 형식으로 입력하세요. 부서명은 04 조직도 표기 그대로, 건수는 정수로 적습니다. (예: `구매팀/7`)",
  "answer": a2, "accept": [a2, a2.replace("/", "-"), a2.replace("/", ""), a2.replace("팀/", "/"), a2.replace("팀/", ""), a2 + "건"],
  "explain": f"사용일 기준 소속 부서별 미차단 위반: {dc_s}. 정답 {a2}. "
             f"{nm('mkB')}는 {mv['mkB'][0]} 마케팅팀→해외영업팀 발령이라 9월 위반은 해외영업팀 소속이고, {nm('osA')}는 {mv['osA'][0]}부터 공정기술팀입니다. "
             f"{nm('swC')}·{nm('osF')}의 이동은 10/01 발령이라 9월 로그는 이전 부서(SW개발팀·해외영업팀)에 귀속합니다. "
             f"함정: 로그 '등록부서'로 귀속하면 {t2['로그 등록부서로 귀속']}, 현 조직도(10/05)로 귀속하면 {t2['현 조직도(10/05) 부서로 귀속']}, 중복을 제거하지 않으면 {t2['요청ID 중복 미제거']}."},
 {"kind": "short",
  "q": "[4-3] 감사 대상 기간의 로그(같은 요청ID는 1건, **차단 여부 무관**) 중 다음 ①~③을 모두 만족하는 로그가 1건 이상 있는 사번을 모두 입력하세요.\n\n"
       "① 외부 서비스(EX-*) 로그이며 01 정책상 위반이다.\n② 사용 일시 기준 소속 부서(9.5)에 그 서비스에 대한 02 대장의 상태 '승인' 건이 있으나, 사용 일시가 그 승인의 유효기간(7.5, 연장·조기 종료 반영)이 **끝난 뒤**다.\n③ 그 승인이 유효했다면 위반이 아니었다.\n\n"
       "사번을 오름차순으로 `-`로 연결해 입력합니다. 해당자가 없으면 `없음`. (예: `E2001-E2350`)",
  "answer": a3, "accept": [a3, a3.replace("-", "/"), a3.replace("-", "")],
  "explain": f"해당 로그: " + "; ".join(f"{nm(k)} " + ", ".join(f"{r['dt']:%m/%d} {r['svc']}{'(차단)' if r['b'] == 'Y' else ''}" for r in rows(O) if r['k'] == k and expired(r, O)) for k in q3_keys(O))
             + f". EX-01(9/15 종료, 갱신 EX-02는 신청중)·EX-04(9/10 종료)·EX-06(9/21 조기 종료) 이후 사용입니다. 정답 {a3}. "
             f"제외: {nm('osA')}·{nm('pe1')}는 공정기술팀 EX-09 시작(9/22) 전 사용이라 '끝난 뒤'가 아니고, {nm('os3')}의 9/24 로그는 개인정보(V2)라 승인이 있어도 위반, {nm('os1')}의 9/15 23:10은 종료일 당일이라 유효, {nm('os4')}의 10/01 로그는 기간 외, 설비기술팀 EX-CHAT은 연장(9/30)으로 유효입니다. "
             f"함정(정답 대비 추가+/누락-): " + ", ".join(f"{k} {diff(v)}" for k, v in t3.items()) + "."},
 {"kind": "choice",
  "context": "정보보호팀은 9월 감사 결과(재교육 대상자 명단 포함)를 보안위원회에 보고하면서 정책 개정안 1건을 함께 올려야 합니다.",
  "q": "[4-4] 01 정책 기준으로 9월 감사 결과를 산정했을 때, **수치 근거가 사실이고** 그 근거에 맞는 개정 방향을 제시한 것은? (재교육 대상은 10장 기준, '과반'은 [4-1] 미차단 위반 건수의 50% 초과를 뜻합니다.)",
  "options": opts, "answer": a4,
  "explain": f"재교육 대상(10.1~10.2, 5점 이상) {N}명: {tg_s}. 미차단 위반 {U}건 중 W {W}건({pct(W)}), 1점 위반 {L1}건({pct(L1)}), 5점 위반 {L5}건({pct(L5)}) → W가 과반이므로 4판 '경고 후 진행' 축소가 근거에 맞습니다(정답 {a4}). "
             f"함정: 차단 위반에 등급 점수 전액을 매기면 {N_bf}명(보기 1), 위반 항목 점수를 합산하면 {N_sum}명(보기 4), W를 차단으로 잘못 보면 미차단 위반이 {Uw}건만 남고 그중 1점 위반이 {L1w}건으로 과반처럼 보여 보기 2를 고르게 됩니다. "
             f"그 밖에 오탐 차단에도 1점을 주면 {TN['오탐 차단도 1점']}명, 중복 미제거 {TN['요청ID 중복 미제거']}명, 기간 외 포함 {TN['기간 외 로그 포함']}명, 5점 초과만 세면 {TN['5점 초과만 대상']}명입니다."},
]

part = {"title": "사내 AI 게이트웨이 보안 감사", "summary": summary, "files": files, "questions": questions}
blind = {**part, "questions": [{k: v for k, v in q.items() if k not in ("answer", "accept", "explain")} for q in questions]}
for n, d in (("part.json", part), ("blind.json", blind)):
    with open(os.path.join(HERE, n), "w", encoding="utf-8") as f: json.dump(d, f, ensure_ascii=False, indent=1)

print("Q1", a1, "| Q2", a2, "| Q3", a3, "| Q4", a4, f"(N={N}, W={W}/{U})")
print("t1", t1); print("t2", t2); print("t3", t3); print("TN", TN)
print("dept", dc_s); print("targets", tg_s)
print("rows", NROW, "files", len(files), "tokens", TOT, [f["tokens"] for f in files])
