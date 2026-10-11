# -*- coding: utf-8 -*-
"""problem.json 검증: CSV로 keyNumbers 재계산, 글자수, pii, 형식."""
import csv, io, json, os, re
from decimal import Decimal as D, ROUND_HALF_UP

HERE = os.path.dirname(os.path.abspath(__file__))
P = json.load(open(os.path.join(HERE, "problem.json"), encoding="utf-8"))
F = {f["name"][:2]: f for f in P["files"]}
ok_all = True


def chk(name, cond, info=""):
    global ok_all
    ok_all &= bool(cond)
    print(f"[{'PASS' if cond else 'FAIL'}] {name} {info}")


def q(x, nd=2):
    return str(D(x).quantize(D(1).scaleb(-nd), ROUND_HALF_UP))


def pc(a, b, nd=2):
    return q(D(a) * 100 / D(b), nd)


def rows(k):
    txt = "\n".join(l for l in F[k]["content"].splitlines() if not l.startswith("#"))
    return list(csv.DictReader(io.StringIO(txt)))


R01, R02, R04, R05, R11 = rows("01"), rows("02"), rows("04"), rows("05"), F["11"]["content"]
R12 = {r["안번호"]: r for r in rows("12")}
T = ["보이드", "미접합", "다이크랙", "정렬불량", "기타"]


def s01(lo, hi):
    rs = [r for r in R01 if lo <= r["일자"] <= hi]
    a = {k: sum(int(r[k]) for r in rs) for k in ["투입수", "양품수"] + T}
    return a


A0, AP, RR = s01("2026-08-03", "2026-08-30"), s01("2026-08-31", "2026-09-27"), s01("2026-09-14", "2026-09-27")
W = [s01(f"2026-{m:02d}-{d:02d}", f"2026-{m2:02d}-{d2:02d}") for (m, d, m2, d2) in
     [(8, 31, 9, 6), (9, 7, 9, 13), (9, 14, 9, 20), (9, 21, 9, 27)]]
y = lambda a: pc(a["양품수"], a["투입수"])
y0, yp, yr = y(A0), y(AP), y(RR)


def seg(sg, b, sh=None):
    rs = [r for r in R04 if r["구간"] == sg and r["본더"] == b and (sh is None or r["조"] == sh)]
    return pc(sum(int(r["양품"]) for r in rs), sum(int(r["투입"]) for r in rs))


def sh5(sh, ncf=None, per=("P1", "P2")):
    rs = [r for r in R05 if r["기간"][:2] in per and r["조"] == sh and (ncf is None or r["NCF"] == ncf)]
    return pc(sum(int(r["양품"]) for r in rs), sum(int(r["투입"]) for r in rs))


def r5(per, sh, ncf):
    return D(next(r["수율(%)"] for r in R05 if r["기간"][:2] == per and r["조"] == sh and r["NCF"] == ncf))


ex_v, ex_n = AP["보이드"] - A0["보이드"], AP["미접합"] - A0["미접합"]
rr_v = RR["보이드"] - A0["보이드"] * RR["투입수"] // A0["투입수"]
rr_n = RR["미접합"] - A0["미접합"] * RR["투입수"] // A0["투입수"]
rv, rn = D(rr_v) * 100 / RR["투입수"], D(rr_n) * 100 / RR["투입수"]
loss = A0["양품수"] * AP["투입수"] // A0["투입수"] - AP["양품수"]
did_d = (D(seg("S3", "TCB-02", "주간")) - D(seg("S2", "TCB-02", "주간"))) - (D(seg("S3", "TCB-03", "주간")) - D(seg("S2", "TCB-03", "주간")))
ctl = lambda s: (D(seg(s, "TCB-01", "야간")) + D(seg(s, "TCB-03", "야간"))) / 2
did_n = (D(seg("S3", "TCB-02", "야간")) - D(seg("S2", "TCB-02", "야간"))) - (ctl("S3") - ctl("S2"))
ml = [r for r in R02 if r["lot_id"].startswith("MR-2608")]
xs, ys = [float(r["수분함량(%)"]) for r in ml], [float(r["보이드율(%)"]) for r in ml]
mx, my = sum(xs) / len(xs), sum(ys) / len(ys)
corr = sum((a - mx) * (b - my) for a, b in zip(xs, ys)) / (sum((a - mx) ** 2 for a in xs) * sum((b - my) ** 2 for b in ys)) ** .5
m = re.search(r"([\d,]+)스택/일 × 365일.*?20만원", R11, re.S)
val1 = D(int(m.group(1).replace(",", "")) * 365) * D("0.01") * 200000 / D(10 ** 8)
pkg = sum(D(R12[k]["12개월총비용(억)"]) for k in ("O2", "O4", "O7", "O8"))
eff = rv + rn
effv = eff * val1
o3 = D(R12["O3"]["제안부서주장_수율효과(%p)"])
mg = sum(int(r["양품"]) for r in R05 if r["NCF"] == "SUP-M")
ship, hold = [int(x.replace(",", "")) for x in re.search(r"출하 완료 ([\d,]+)개, 창고 보류 ([\d,]+)개", R11).groups()]
chk("출하+보류=M양품", ship + hold == mg, f"{ship}+{hold} vs {mg}")
tot = ex_v + ex_n
EXP = {
    "8월(W32~W35) 라인 수율": f"{y0}%",
    "9월(W36~W39) 라인 수율": f"{yp}%",
    "목표 대비 갭": f"{q(D('92.0') - D(yp))}%p",
    "8월 대비 손실": f"{q(D(y0) - D(yp))}%p",
    "주차별 수율 W36/W37/W38/W39": "/".join(y(w) for w in W) + "%",
    "런레이트(W38~W39) 수율": f"{yr}%",
    "9월 불량유형별 손실(보이드/미접합/크랙/정렬/기타)": "/".join(pc(AP[t], AP["투입수"]) for t in T) + f"%p (합 {pc(sum(AP[t] for t in T), AP['투입수'])})",
    "9월 초과손실 스택·금액": f"{loss:,}스택 / {q(D(loss) * 200000 / 10 ** 8)}억",
    "SUP-M(보이드 초과) 기여도-9월 기간": f"{pc(ex_v, AP['투입수'])}%p ({pc(ex_v, tot, 1)}%)",
    "ECN-0914(미접합 초과) 기여도-9월 기간": f"{pc(ex_n, AP['투입수'])}%p ({pc(ex_n, tot, 1)}%)",
    "런레이트 기여도 SUP-M/ECN": f"{q(rv)}%p ({pc(rr_v, rr_v + rr_n, 1)}%) / {q(rn)}%p ({pc(rr_n, rr_v + rr_n, 1)}%)",
    "셀 단위 효과 SUP-M/R275": f"{q(r5('P1', '주간', 'SUP-M') - r5('P1', '주간', 'SUP-C'))}%p / {q(r5('P2', '주간', 'SUP-C') - r5('P1', '주간', 'SUP-C'))}%p",
    "TCB-02 구간 수율 S1/S2/S3": "/".join(seg(s, "TCB-02") for s in ("S1", "S2", "S3")) + "%",
    "TCB-02 PM 이중차분(주간·야간)": f"{q(did_d)}%p / {q(did_n)}%p",
    "조별 단순 vs 동일 NCF(M) 비교": f"주간 {sh5('주간')} vs 야간 {sh5('야간')} / 주간 {sh5('주간', 'SUP-M')} vs 야간 {sh5('야간', 'SUP-M')}",
    "SUP-M 4 lot 수분-보이드율 상관계수": q(corr),
    "수율 1%p 연간 가치": f"{val1}억",
    "투자 패키지(O2+O4+O7+O8) 12개월 총비용": f"{q(pkg)}억",
    "패키지 효과": f"+{q(eff)}%p / 연 {q(effv)}억 / 기대수율 {q(D(yr) + eff)}%",
    "순효과·ROI·회수기간": f"{q(effv - pkg)}억 / {q((effv - pkg) / pkg * 100, 1)}% / {q(pkg / effv * 12)}개월",
    "O3+O4 대안 기대수율": f"{q(D(yr) + rn + o3)}%",
    "SUP-M 적용 양품(출하+보류)": f"{mg:,} ({ship:,} + {hold:,})",
}
print("== keyNumbers ==")
kn = {k["label"]: k["value"] for k in P["answerKey"]["keyNumbers"]}
chk("keyNumbers 라벨 집합 일치", set(kn) == set(EXP))
for k, v in EXP.items():
    chk(k, kn.get(k) == v, f"json={kn.get(k)} | 재계산={v}")

print("== 교차 일치 ==")
lot_sum = lambda t, per: sum(int(r[t]) for r in R02 if r[t] and r["투입시작"] >= "2026-08-03" and (r["투입시작"] >= "2026-08-31") == per)
chk("02 lot 보이드 합 = 01 (P0/P)", (lot_sum("보이드", False), lot_sum("보이드", True)) == (A0["보이드"], AP["보이드"]))
chk("02 lot 미접합 합 = 01 (P0/P)", (lot_sum("미접합", False), lot_sum("미접합", True)) == (A0["미접합"], AP["미접합"]))
chk("04 합계 = 01 P", sum(int(r["양품"]) for r in R04 if r["구간"] != "S1") == AP["양품수"])
chk("05 합계 = 01 전체", sum(int(r["양품"]) for r in R05) == A0["양품수"] + AP["양품수"])
sit = P["situation"]
chk("situation 수치", all(f"**{v}%**" in sit for v in ("92.0", yp, y0)))
t09, t10, t07 = F["09"]["content"], F["10"]["content"], F["07"]["content"]
chk("09 TCB-02 89.25→88.55", f"{seg('S2', 'TCB-02')}%에서 {seg('S3', 'TCB-02')}%로" in t09)
pre = s01("2026-08-31", "2026-09-20")
R01d = {r["일자"]: r for r in R01}
night = lambda: None
chk("09 회의 잠정수율(08/31~09/20)", f"{y(pre)}%" in t09)
chk("10 야간/주간 83.75/88.75", f"야간 {sh5('야간')}% vs 주간 {sh5('주간')}%" in t10)
vr0, vr1 = pc(A0["보이드"], A0["투입수"]), pc(pre["보이드"], pre["투입수"])
chk("07 보이드율", f"= {vr0}%" in t07 and f"= {vr1}%" in t07, f"{vr0}→{vr1}")
chk("09 보이드 배수", f"약 {q(D(vr1) / D(vr0), 1)}배" in t09)
chk("01 행수 56", len(R01) == 56)
chk("01 음수 없음", all(int(r[t]) >= 0 for r in R01 for t in T))
chk("04 행수 24 / 05 행수 8 / 06 행수 24", (len(R04), len(R05), len(rows("06"))) == (24, 8, 24))

print("== 파일 ==")
for f in P["files"]:
    n = len(f["content"])
    disk = open(os.path.join(HERE, "files", f["name"]), encoding="utf-8").read()
    chk(f"{f['name']}", n <= 6000 and disk == f["content"], f"{n}자")
    if f["kind"] == "pdf":
        chk("  pdf [p.N]·조항", re.search(r"^\[p\.1\]", f["content"], re.M) and re.search(r"\d+\.\d|제\d+조", f["content"]))
    if f["kind"] == "txt":
        bad = [l for l in f["content"].splitlines() if l and not re.match(r"^\[2026-\d\d-\d\d \d\d:\d\d\]", l)]
        chk("  txt 모든 줄 타임스탬프", not bad, bad[:1])
chk("파일 수 10~12", 10 <= len(P["files"]) <= 12)

print("== PII ==")
alltxt = "\n".join(f["content"] for f in P["files"])
miss = [p for p in P["pii"] if p not in alltxt]
chk(f"pii {len(P['pii'])}개 모두 파일에 존재", not miss, miss)
phones = re.findall(r"01\d-\d{3,4}-\d{4}", alltxt)
chk("전화번호 010-0000-xxxx만", all(p.startswith("010-0000-") for p in phones), len(phones))
chk("전화번호 모두 pii 포함", set(phones) <= set(P["pii"]))
emails = set(re.findall(r"[\w.]+@[\w.-]+", alltxt))
chk("이메일 도메인 .example만", all(e.endswith(".example") for e in emails))
chk("개인 이메일 pii 포함", {e for e in emails if not e.startswith("privacy@")} <= set(P["pii"]))

print("== 루브릭 ==")
chk("결과 60 / 과정 40", (sum(x["points"] for x in P["rubric"]["result"]), sum(x["points"] for x in P["rubric"]["process"])) == (60, 40))
chk("섹션 6개", len(P["sections"]) == 6)
print("\nALL PASS" if ok_all else "\nSOME FAILED")
