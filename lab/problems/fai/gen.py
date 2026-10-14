import json, random, re
from datetime import date, timedelta
R = random.Random(2605)

# ---------- 플랜 정책 ----------
FEATS = ["텍스트 생성","이미지 생성(저해상도)","이미지 생성(고해상도)","문서 요약","코드 어시스턴트","데이터 분석","워크플로 자동화","외부 API 연동","컴플라이언스/감사 로그"]
# 코드, 이름, 인당 월 구독료($), 인당 월 기본 크레딧, 최소 계약 인원, 초과 1,000크레딧당 단가($), 지원 기능 수(앞에서부터 누적)
PLANS = [
 ("S1","Starter Lite",12,5000,1,3.0,1), ("S2","Starter",20,10000,1,3.0,2), ("S3","Starter Plus",28,15000,5,3.0,3),
 ("A1","Advanced Lite",40,20000,3,2.5,4), ("A2","Advanced",50,30000,5,2.5,5), ("A3","Advanced Pro",65,45000,8,2.5,6),
 ("E1","Enterprise Lite",80,60000,10,2.0,7), ("E2","Enterprise",110,90000,30,2.0,8), ("E3","Enterprise Max",140,120000,20,2.0,9),
]
PL = {p[0]: dict(code=p[0],name=p[1],price=p[2],credit=p[3],min=p[4],over=p[5],feats=set(FEATS[:p[6]])) for p in PLANS}

T, I, IH, SUM, CODE, DATA, WF, API = FEATS[:8]
# 팀코드, 팀명, 플랜, 계약 라이선스, 사용 기능, 실제 사용 크레딧, 유휴 상태 목록, 4월 퇴사자 수
TEAMS = [
 ("T-01","AI리서치팀","A2",10,[T,IH,SUM,CODE],220000,["휴직"],0),
 ("T-02","UX·디자인팀","S3",7,[T,I,IH],88000,[],0),
 ("T-03","법무·컴플라이언스팀","A1",6,[T,SUM],23000,[],0),
 ("T-04","PR·홍보팀","A3",10,[T,IH,SUM,DATA],380000,["군복무","재직"],1),
 ("T-05","글로벌사업팀","E1",16,[T,IH,SUM,CODE,DATA,WF],720000,["재직"],0),
 ("T-06","데이터·분석팀","A2",11,[T,IH,SUM,CODE],954000,["재직","휴직"],0),
 ("T-07","영업운영팀","A2",17,[T,IH,SUM,CODE],728000,["재직","휴직","재직"],1),
 ("T-08","제품개발팀","E3",25,[T,IH,SUM,CODE,DATA,WF,API],2150000,[],0),
 ("T-09","마케팅·브랜드팀","A3",12,[T,IH,SUM],1240000,["재직","휴직"],0),
 ("T-10","내부감사팀","A3",10,[T,SUM],85000,["재직","재직"],0),
 ("T-11","국내영업팀","A3",13,[T,IH,SUM,DATA],520000,["군복무","재직"],0),
 ("T-12","교육·연수팀","A1",9,[T,IH,SUM],95000,[],0),
 ("T-13","재무·회계팀","A1",8,[T,SUM],61000,["휴직"],0),
 ("T-14","인사팀","S2",10,[T],42000,["재직","재직"],0),
 ("T-15","고객지원팀","S3",15,[T,I],185000,[],0),
]
for t in TEAMS: assert set(t[4]) <= PL[t[2]]["feats"], t[0]

# ---------- 인원 ----------
SUR = list("김이박최정강조윤장임한오서신권황안송류전홍고문양손배백허유남심노하곽성차주우구민진나지엄채원천방공현함변염여추도소석선설마길연위표명기반왕금옥육인맹제모")
GIV = ["민준","서연","지호","하은","도윤","수아","시우","지유","예준","채원","주원","다은","하준","윤서","지훈","서윤","현우","지민","건우","소율","우진","예린","선우","가은","연우","나연","유준","수빈","정우","하린","승현","유나","민재","시은","준혁","은서","지환","다인","승민","아린","태윤","서진","은우","채은","재원","하윤","민성","서아","동현","지안","준영","예서","성민","혜원","영훈","보람","상우","미래","재희","소희"]
names, used = [], set()
while len(names) < 181:
    n = R.choice(SUR) + R.choice(GIV)
    if n not in used: used.add(n); names.append(n)
POS = ["사원","주임","대리","과장","차장"]
purposes = {T:["회의록 작성","이메일 작성","보고서 초안","공지문 작성","자료 정리"], I:["배너 이미지","아이콘 초안","안내 이미지"], IH:["홍보 이미지 생성","프레젠테이션 이미지","시안 이미지"],
            SUM:["문서 요약","보고서 요약","회의 자료 요약"], CODE:["코드 리뷰","스크립트 작성","테스트 코드 작성"], DATA:["데이터 분석","지표 분석","설문 분석"],
            WF:["워크플로 설계","업무 자동화"], API:["API 연동 테스트","외부 시스템 연동"]}
roster, reports, ans = [], [], {}
emp = 0; ni = iter(names)
def sabun():
    global emp; emp += 1; return f"OS{2014 + emp % 12}{emp:03d}"
for code, tname, plan, L, feats, actual, idle, apr in TEAMS:
    idle_n = len(idle); users_n = L - idle_n
    members = []
    for k in range(users_n): members.append(dict(team=tname, code=code, sabun=sabun(), name=next(ni), status="재직", eff="-", user=True))
    for st in idle:
        members.append(dict(team=tname, code=code, sabun=sabun(), name=next(ni), status=st, eff=(f"2026-0{R.choice([2,3,4])}-{R.randint(1,28):02d}" if st != "재직" else "-"), user=False))
    for k in range(apr):
        members.append(dict(team=tname, code=code, sabun=sabun(), name=next(ni), status="퇴사", eff="2026-04-30", user=False, april=True))
    # 사용자 중 일부: 5월 중 휴직·퇴사(사용 후)로 상태 변경
    if users_n >= 8:
        m = members[R.randrange(1, users_n)]; R.choice(["휴직","퇴사"]); m["status"] = "휴직"; m["eff"] = f"2026-05-{R.randint(18,28):02d}"
    leader = members[0]
    # 사용 내역: 사용자별 1~4행, 합계 = actual (1,000 단위)
    rows = []
    users = [m for m in members if m["user"]]
    units = actual // 1000
    cnt = [R.randint(1, 4) for _ in users]
    total_rows = sum(cnt)
    w = [R.random() + 0.3 for _ in range(total_rows)]
    alloc = [max(1, int(units * x / sum(w))) for x in w]
    alloc[-1] += units - sum(alloc)
    assert alloc[-1] > 0
    i = 0
    for m, c in zip(users, cnt):
        lim = int(m["eff"][-2:]) - 1 if m["eff"] != "-" and m["eff"].startswith("2026-05") else 31
        for _ in range(c):
            f = R.choice(feats); d = date(2026, 5, R.randint(1, lim))
            rows.append((d.isoformat(), m["sabun"], m["name"], f, R.choice(purposes[f]), alloc[i] * 1000)); i += 1
    rows.sort()
    assert sum(r[5] for r in rows) == actual
    p = PL[plan]
    rep = dict(code=code, team=tname, plan=plan, L=L, feats=feats, actual=actual, rows=rows, leader=leader["name"])
    reports.append(rep); roster += members
assert len(roster) == 181, len(roster)

# ---------- 정답 계산 ----------
def cost(plan, L, actual):
    p = PL[plan]; base = p["credit"] * L
    return p["price"] * L + max(0, actual - base) / 1000 * p["over"]
over = {r["code"]: max(0, r["actual"] - PL[r["plan"]]["credit"] * r["L"]) / 1000 * PL[r["plan"]]["over"] for r in reports}
q2 = max((r for r in reports if r["plan"] == "A2"), key=lambda r: over[r["code"]])["code"]
order = [p[0] for p in PLANS]
best = {}
for r in reports:
    cur = cost(r["plan"], r["L"], r["actual"])
    for np in order[:order.index(r["plan"])]:
        q = PL[np]
        if set(r["feats"]) <= q["feats"] and r["L"] >= q["min"] and cost(np, r["L"], r["actual"]) < cur:
            s = cur - cost(np, r["L"], r["actual"])
            if s > best.get(r["code"], (0,))[0]: best[r["code"]] = (s, np)
q3 = max(best, key=lambda k: best[k][0])
idle = {r["code"]: r["L"] - len({x[1] for x in r["rows"]}) for r in reports}
q4 = sum(idle[r["code"]] * PL[r["plan"]]["price"] for r in reports)
naive4 = sum((sum(1 for m in roster if m["code"] == r["code"]) - len({x[1] for x in r["rows"]})) * PL[r["plan"]]["price"] for r in reports)
print("over", over); print("downgrade", best); print("Q2", q2, "Q3", q3, "Q4", q4, "naive Q4", naive4)
assert q2 == "T-06" and q3 == "T-10"

# ---------- 파일 텍스트 ----------
def money(x): return f"USD ${x:,.0f}" if x == int(x) else f"USD ${x:,.2f}"
feat_tbl = "기능 | " + " | ".join(order) + "\n" + "\n".join(f + " | " + " | ".join("●" if f in PL[c]["feats"] else "–" for c in order) for f in FEATS)
policy = f"""[p.1]
FAI Technologies, Inc.
FAI 요금제 및 크레딧 정책 안내서 (2026년 개정판)
문서번호 FAI-POL-2026-01 · 시행일 2026-01-01

1. 개요
본 안내서는 FAI 생성형 AI 서비스의 9개 구독 플랜(S1~S3, A1~A3, E1~E3)에 대한 요금, 크레딧, 기능 제공 범위와 라이선스 운영 정책을 설명합니다.

2. 용어
- 라이선스: 서비스 이용 권한 1석. 구독료는 계약 라이선스 수 기준으로 매월 청구됩니다.
- 크레딧: 기능 사용량 단위. 팀 월 기본 제공 크레딧 = 인당 월 기본 크레딧 × 계약 라이선스 수
- 추가 과금: 팀의 월 실제 사용 크레딧이 팀 월 기본 제공 크레딧을 초과한 경우 청구되는 금액
- 월 총 비용 = 월 기본 구독료 합계 + 추가 과금액

[p.2]
3. 플랜별 요금표 (USD, 월 기준)
플랜 코드 | 플랜명 | 인당 월 구독료 | 인당 월 기본 크레딧 | 최소 계약 인원 | 초과 1,000크레딧당 단가
""" + "\n".join(f"{c} | {PL[c]['name']} | ${PL[c]['price']} | {PL[c]['credit']:,} | {PL[c]['min']}명 | ${PL[c]['over']:.2f}" for c in order) + """
※ E2(Enterprise)는 대규모 계약 전용 플랜으로 최소 계약 인원이 30명입니다.
※ 미사용 크레딧은 다음 달로 이월되지 않습니다.

[p.3]
4. 플랜별 사용 가능 기능 (● 제공, – 미제공)
""" + feat_tbl + """
※ 상위 플랜은 하위 플랜의 기능을 모두 포함합니다.

[p.4]
5. 운영 정책
제1조(추가 과금) 추가 과금액 = (팀 월 실제 사용 크레딧 − 팀 월 기본 제공 크레딧) ÷ 1,000 × 플랜별 초과 단가. 초과분이 없으면 0으로 한다.
제2조(플랜 변경) ① 플랜 변경은 팀 단위로 신청하며 다음 달 1일부터 적용한다. ② 변경 후 플랜은 팀이 사용 중인 기능을 모두 제공해야 하며, 계약 라이선스 수가 변경 후 플랜의 최소 계약 인원 이상이어야 한다.
제3조(라이선스 회수) ① 퇴사자의 라이선스는 퇴사 발효일이 속한 달의 말일에 자동 회수되며 다음 달부터 계약 라이선스 수에서 제외된다. ② 휴직자·군복무자의 라이선스에 대한 별도 회수 규정은 없다. ③ 회사는 월말 기준으로 라이선스를 회수할 수 있으며, 회수된 라이선스는 다음 달부터 구독료가 청구되지 않는다. ④ 제3조에 따른 라이선스 회수에는 최소 계약 인원 요건을 적용하지 않는다.
제4조(청구) 구독료와 추가 과금은 매월 말일 기준으로 정산하여 다음 달 5일에 청구한다.
"""
files = [{"name": "01_FAI_요금제_및_크레딧_정책_안내서.pdf", "kind": "pdf", "tokens": 2310, "content": policy.strip()}]
WRITER, REVIEWER = "안지오", "편지솔"
# 실제 시험 화면의 토큰 표시값(01~11), 12~15는 비슷한 수준으로 지정
REPORT_TOKENS = [2022, 1594, 1524, 1967, 2191, 2092, 2277, 2874, 2091, 1997, 2101, 1886, 1742, 1655, 2318]
for k, r in enumerate(reports, 1):
    p = PL[r["plan"]]
    rows = r["rows"]; half = (len(rows) + 1) // 2
    fmt = lambda rr: "\n".join(f"{d} | {s} | {n} | {f} | {pu} | {c:,}" for d, s, n, f, pu, c in rr)
    body = f"""[p.1]
ㅇㅇ솔루션 | IT 운영팀 정기 보고서 · 문서번호 OOS-IT-RPT-2026-05-{r['code']}
{r['team']} FAI 이용 현황 보고서 (보고 기준월: 2026년 5월)
작성일 2026. 06. 03. | 보고 기간 2026년 5월 1일 ~ 5월 31일
작성자 IT 운영팀 {WRITER} 차장 | 검토자 IT 운영팀장 {REVIEWER} 부장
보고 대상 재무·회계팀, 인사팀 | 보안 등급 대외비(Confidential)

1. 팀 및 구독 플랜 정보
팀 코드 {r['code']} | 팀명 {r['team']}
팀장 {r['leader']} 부장 | 플랜 코드 {r['plan']} ({p['name']})
인당 월 구독료 USD ${p['price']} | 인당 월 기본 크레딧 {p['credit']:,} 크레딧
계약 라이선스 {r['L']} 개 | 월 기본 구독료 합계 USD ${p['price'] * r['L']:,}
팀 월 기본 제공 크레딧 {p['credit'] * r['L']:,} 크레딧 | 실제 사용 크레딧 {r['actual']:,} 크레딧

2. 5월 중 사용 중인 기능
{' · '.join(r['feats'])}

3. 팀원별 사용 내역
일자 | 사번 | 성명 | 기능 | 사용 목적 | 사용 크레딧
{fmt(rows[:half])}

[p.2]
3. 팀원별 사용 내역 (계속)
일자 | 사번 | 성명 | 기능 | 사용 목적 | 사용 크레딧
{fmt(rows[half:])}
합계 | | | | | {r['actual']:,}

※ 본 보고서는 FAI 관리자 콘솔의 사용 로그를 기준으로 작성되었으며, 사용 내역이 없는 라이선스는 표에 나타나지 않습니다."""
    files.append({"name": f"{k:02d}_{r['team']}_FAI_이용현황_2026년5월.pdf", "folder": "02_팀별_FAI_이용현황", "kind": "pdf", "tokens": REPORT_TOKENS[k - 1], "content": body})
by_team = {}
for m in roster: by_team.setdefault(m["code"], []).append(m)
summary = "\n".join(f"{c} | {t[1]} | {len(by_team[c])}명" for c, t in zip([x[0] for x in TEAMS], TEAMS))
lines = [f"{m['team']} | {m['sabun']} | {m['name']} | {m['status']} | {m['eff']}" for m in roster]
pages = ["[p.1]\nㅇㅇ솔루션 전사 임직원 명부 (기준일: 2026-05-31) · 인사팀 · 대외비\n총 인원 181명 (재직·휴직·군복무·퇴사 포함, 2026년 1월 이후 퇴사자 포함)\n\n팀별 인원 분포\n팀 코드 | 팀명 | 인원\n" + summary]
for s in range(0, len(lines), 50):
    pages.append(f"[p.{len(pages) + 1}]\n임직원 명단 ({s + 1}~{min(s + 50, len(lines))})\n소속 팀 | 사번 | 성명 | 재직 상태 | 발효일\n" + "\n".join(lines[s:s + 50]))
files.append({"name": "03_전사_임직원_명부_2026년5월.pdf", "kind": "pdf", "tokens": 4380, "content": "\n\n".join(pages)})

P = {
 "id": "fai-license-01", "type": "mcq", "title": "FAI 라이선스 운영 분석", "badge": "객관식 1 · 주관식 3", "timeLimitMin": 30,
 "aiLimit": {"count": 10, "chars": 1000}, "pii": [],
 "passage": "2026년 5월 한 달 동안 FAI Technologies, Inc.(이하 FAI)의 생성형 AI 서비스를 이용한 ㅇㅇ솔루션 사내 15개 팀의 라이선스 운영 현황과 관련 정책, 전사 임직원 명부가 주어집니다.\n\n- `01_FAI_요금제_및_크레딧_정책_안내서.pdf`는 FAI에서 제공하는 9개 플랜의 정책이 정리된 공식 안내 문서입니다.\n- `02_팀별_FAI_이용현황` 폴더 안에는 2026년 5월 한 달 동안 ㅇㅇ솔루션 사내 15개 팀의 FAI 크레딧 사용 내역이 팀별 1개 파일씩 총 15개 파일로 나뉘어 정리되어 있습니다.\n- `03_전사_임직원_명부_2026년5월.pdf`는 ㅇㅇ솔루션 전체 임직원 181명의 소속 팀, 사번, 성명, 재직 상태(재직 / 휴직 / 군복무 / 퇴사) 및 휴직·군복무·퇴사 발효일이 정리된 인사 기준 문서입니다.\n\n퇴사자·휴직자·군복무자의 라이선스는 별도 회수 정책이 명시되지 않은 한 유지되는 것으로 간주합니다.\n\n주어진 자료를 보고 아래 질문들에 답해주세요.",
 "notices": [],
 "files": files,
 "questions": [
  {"kind": "choice", "q": "내부감사팀(T-10)이 S1~S3로 다운그레이드할 수 없는 가장 직접적인 기능 미지원 사유 1가지로 옳은 것은 무엇인가요?",
   "options": ["텍스트 생성","이미지 생성(저해상도)","이미지 생성(고해상도)","문서 요약","코드 어시스턴트"], "answer": 4,
   "explain": "T-10 보고서의 사용 기능은 텍스트 생성·문서 요약 두 가지입니다(T-10 보고서 p.1). 정책 안내서 p.3 기능표에서 문서 요약은 A1 이상에서만 제공되고 S1~S3는 미제공입니다. 이미지·코드 기능은 T-10이 쓰지 않으므로 사유가 아닙니다."},
  {"kind": "short", "q": "2026년 5월 기준, A2 플랜을 사용 중인 팀 가운데 추가 과금액이 가장 큰 팀의 팀 코드를 입력해 주세요. (예: `T-01`)", "answer": "T-06", "accept": ["T-06","T06","T-6"],
   "explain": "A2 팀은 T-01·T-06·T-07입니다. 추가 과금(정책 p.4 제1조) = (실제 − 기본 제공) ÷ 1,000 × $2.50. T-06: (954,000 − 330,000) → $" + f"{over['T-06']:,.0f}" + ", T-07: (728,000 − 510,000) → $" + f"{over['T-07']:,.0f}" + ", T-01: 초과 없음. 전체 팀 중 최대는 A3인 T-09($" + f"{over['T-09']:,.0f}" + ")이지만 A2가 아니므로 제외합니다. T-07의 계약 라이선스는 명부 인원(18명)이 아니라 보고서의 17개입니다."},
  {"kind": "short", "q": "플랜 다운그레이드 시 가장 큰 월 비용 절감 효과를 얻을 수 있는 팀의 코드를 입력해 주세요. (단, 다운그레이드 후에도 기능 지원 및 최소 계약 인원 요건을 모두 충족해야 하며, 초과 과금까지 포함한 월 총 비용이 현재보다 낮아야 합니다.) (예: `T-01`)", "answer": "T-10", "accept": ["T-10","T10"],
   "explain": "조건을 만족하는 다운그레이드: " + ", ".join(f"{k}→{v[1]} ${v[0]:,.0f} 절감" for k, v in sorted(best.items(), key=lambda kv: -kv[1][0])) + ". 최대는 T-10(A3→A1: $650 → $400). 함정: T-08(E3→E2)은 구독료만 보면 $750 절감이지만 E2 최소 계약 인원 30명 미달(25개)로 불가, T-09(A3→A1/A2)는 구독료는 줄지만 추가 과금 증가로 월 총 비용이 오히려 늘어 불가합니다. 다운그레이드 대상을 S 플랜으로만 한정하면 T-10을 놓칩니다."},
  {"kind": "short", "q": "2026년 5월 한 달 동안 팀의 이용 현황 보고서에 한 번도 사용 내역이 등장하지 않은 라이선스를 유휴 라이선스라고 합니다. 회사가 5월 말 기준으로 모든 유휴 라이선스를 회수한다고 가정할 때, 6월부터 회사 전체가 매월 절약할 수 있는 월 구독료의 총합은 얼마인가요? (달러 기호와 쉼표 없이 정수로 입력해 주세요. 예: `1234`)", "answer": str(q4), "accept": [str(q4)],
   "explain": "유휴 라이선스 = 보고서의 계약 라이선스 수 − 사용 내역에 등장한 고유 사번 수. 팀별: " + ", ".join(f"{r['code']} {idle[r['code']]}개×${PL[r['plan']]['price']}" for r in reports if idle[r['code']]) + f" → 합계 ${q4:,}. 함정: 명부 인원으로 계산하면 4월 퇴사자(T-04·T-07 각 1명, 정책 제3조①로 이미 회수되어 5월 계약 라이선스에 없음)가 섞여 ${naive4:,}가 됩니다. 휴직·군복무자 라이선스는 회수 규정이 없어 유지되므로(지문·제3조②) 사용 내역이 없으면 유휴에 포함합니다."},
 ],
}
json.dump(P, open(__import__("os").path.join(__import__("os").path.dirname(__file__), "problem.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
print("files", len(files), "chars", sum(len(f["content"]) for f in files))
