import json, os
from decimal import Decimal, ROUND_HALF_UP
from fractions import Fraction as F

HERE = os.path.dirname(os.path.abspath(__file__))
SUP = "ABCDE"
N, YEARS, HOURS, KWH = 4, 5, 6000, 140
FX, FX_T = 1350, 1420                      # 평가 환율 / 회의록 미확정 환율(함정)
BUDGET0, BUDGET1 = 9_600_000_000, 10_000_000_000
W0 = dict(al=15, uph=20, yl=15, price=30, lead=10, svc=10)   # 원안
W1 = dict(al=15, uph=20, yl=15, price=40, lead=5, svc=5)     # 회의록 확정
WH = dict(al=15, uph=25, yl=15, price=25, lead=10, svc=10)   # 회의록 보류 의견(함정)
GEM_OPT = 30_000_000                                         # A사 GEM300 옵션 대당 금액

# 제안서 원천 데이터(제안서에 적힌 통화·단위 그대로)
# cur: KRW|USD, mult: 1(원)|1000(천원), vat: 금액이 VAT 포함인지, price: ('unit'|'total', 금액)
# disc: (할인율, 최소 수량), inst/maint: (금액, 'unit'|'total'|'incl'), cons: 대당 연간, ref: 제안서 임의 환율
P = {
 "A": dict(cur="KRW", mult=1, vat=False, price=("unit", 2_250_000_000), disc=(F(2, 100), 4), inst=(0, "incl"),
           maint=(280_000_000, "total"), war=1, cons=28_000_000, ship=12, ins=3, svc=2, gem="option", ref=None),
 "B": dict(cur="USD", mult=1, vat=False, price=("unit", 1_640_000), disc=(0, 0), inst=(40_000, "unit"),
           maint=(230_000, "total"), war=2, cons=25_000, ship=12, ins=4, svc=4, gem="basic", ref=1300),
 "C": dict(cur="KRW", mult=1000, vat=True, price=("total", 10_340_000), disc=(0, 0), inst=(55_000, "unit"),
           maint=(396_000, "total"), war=1, cons=44_000, ship=10, ins=4, svc=2, gem="basic", ref=None),
 "D": dict(cur="USD", mult=1, vat=False, price=("unit", 1_790_000), disc=(0, 0), inst=(25_000, "unit"),
           maint=(30_000, "unit"), war=2, cons=15_000, ship=15, ins=4, svc=4, gem="basic", ref=1320),
 "E": dict(cur="KRW", mult=1, vat=False, price=("unit", 2_150_000_000), disc=(F(3, 100), 6), inst=(40_000_000, "unit"),
           maint=(300_000_000, "total"), war=2, cons=35_000_000, ship=16, ins=6, svc=4, gem="basic", ref=None),
}
# 카탈로그(제안서 기재) 성능: 정렬 3σ, UPH, 수율, 소비전력 — 평가에는 쓰지 않음(함정)
CLAIM = {"A": ("0.80", 1800, "99.70", "21.0"), "B": ("0.85", 1750, "99.50", "23.0"), "C": ("0.60", 1750, "99.80", "24.0"),
         "D": ("0.50", 1900, "99.70", "18.0"), "E": ("0.70", 1700, "99.60", "22.0")}
# 기술검증 run: (정렬오차 3σ µm, UPH, 본딩수율 %, 평균 소비전력 kW, 유효, 비고)
RUNS = {
 "A": [("0.82", 1650, "99.52", "23.1", 1, ""), ("0.79", 1672, "99.55", "22.8", 1, ""),
       ("1.31", 1120, "96.80", "22.9", 0, "시료 로딩 오류로 무효(공급사 귀책 아님)"), ("0.84", 1661, "99.49", "23.2", 1, "")],
 "B": [("0.91", 1650, "99.22", "25.0", 1, ""), ("1.06", 1630, "99.18", "25.3", 1, ""),
       ("0.95", 1660, "99.25", "24.8", 1, ""), ("0.89", 1645, "99.20", "24.9", 1, "")],
 "C": [("0.64", 1700, "99.58", "26.1", 1, ""), ("0.66", 1690, "99.61", "25.9", 1, ""),
       ("0.69", 1710, "99.55", "26.0", 1, ""), ("0.62", 1705, "99.60", "26.2", 1, "")],
 "D": [("0.66", 1760, "99.52", "20.1", 1, ""), ("0.95", 1390, "98.10", "20.3", 0, "기판 휨 시료 투입으로 무효(시료 불량)"),
       ("0.71", 1745, "99.48", "19.8", 1, ""), ("0.68", 1770, "99.50", "20.0", 1, "")],
 "E": [("0.74", 1620, "99.40", "24.0", 1, ""), ("0.77", 1600, "99.35", "24.2", 1, ""),
       ("0.73", 1615, "99.42", "23.9", 1, ""), ("0.75", 1610, "99.38", "24.1", 1, "")],
}


# ---------- 규칙 엔진 ----------
def rnd(x, q="0.1"): x = F(x); return (Decimal(x.numerator) / Decimal(x.denominator)).quantize(Decimal(q), ROUND_HALF_UP)
def mil(x): return int(rnd(F(x) / 1_000_000, "1"))


def krw(s, x, fx=FX, vat=True, ref=False):
    p = P[s]; v = F(x) * p["mult"]
    if p["cur"] == "USD": v *= p["ref"] if ref and p["ref"] else fx
    if p["vat"] and vat: v /= F(11, 10)
    return v


def metrics(s, invalid=False, claimed=False):
    if claimed:
        a, u, y, k = CLAIM[s]; return dict(al=F(a), al_mean=F(a), uph=F(u), yl=F(y), kw=F(k))
    rs = [r for r in RUNS[s] if r[4] or invalid]
    m = lambda i: sum(F(r[i]) for r in rs) / len(rs)
    return dict(al=max(F(r[0]) for r in rs), al_mean=m(0), uph=m(1), yl=m(2), kw=m(3))


def equip(s, fx=FX, vat=True, ref=False, disc=True, gem_add=False):
    p = P[s]; kind, amt = p["price"]
    v = krw(s, amt, fx, vat, ref) * (N if kind == "unit" else 1)
    r, q = p["disc"]
    if r and (N >= q or not disc): v *= 1 - r
    return v + (GEM_OPT * N if gem_add and p["gem"] == "option" else 0)


def tco(s, fx=FX, vat=True, ref=False, disc=True, war=True, munit=True, invalid=False, claimed=False, gem_add=False):
    p = P[s]; k = lambda x: krw(s, x, fx, vat, ref)
    ia, ik = p["inst"]; ma, mk = p["maint"]
    t = dict(equip=equip(s, fx, vat, ref, disc, gem_add),
             inst=0 if ik == "incl" else k(ia) * (N if ik == "unit" else 1),
             maint=k(ma) * (N if mk == "unit" and munit else 1) * (YEARS - (p["war"] if war else 0)),
             cons=k(p["cons"]) * N * YEARS,
             power=metrics(s, invalid, claimed)["kw"] * HOURS * YEARS * N * KWH)
    t["total"] = sum(t.values())
    return t


def lead(s, headline=False, e_verbal=False):
    p = P[s]
    return p["ship"] if headline else p["ship"] + (4 if s == "E" and e_verbal else p["ins"])


def evaluate(fx=FX, budget=BUDGET0, W=W0, gem=False, lead_max=20, invalid=False, claimed=False, align_mean=False, vat=True,
             ref=False, disc=True, war=True, munit=True, b_retest=False, e_verbal=False, headline=False, rel_all=False, gem_add=False):
    out = {}
    for s in SUP:
        mt = metrics(s, invalid, claimed)
        al = F("0.93") if s == "B" and b_retest else mt["al_mean"] if align_mean else mt["al"]
        ld = lead(s, headline, e_verbal); eq = equip(s, fx, vat, ref, disc, gem_add)
        ko = [k for k, bad in (("K1", al > 1), ("K2", mt["uph"] < 1500), ("K3", ld > lead_max), ("K4", eq > budget),
                               ("K5", P[s]["svc"] > 4), ("K6", gem and not gem_add and P[s]["gem"] != "basic")) if bad]
        out[s] = dict(mt=mt, al=al, lead=ld, equip=eq, ko=ko, tco=tco(s, fx, vat, ref, disc, war, munit, invalid, claimed, gem_add)["total"])
    ok = [s for s in SUP if not out[s]["ko"]]
    base = SUP if rel_all else ok
    mu = max(out[s]["mt"]["uph"] for s in base); mt_ = min(out[s]["tco"] for s in base)
    for s in ok:
        o = out[s]; m = o["mt"]
        o["sc"] = sc = dict(al=100 if o["al"] <= F("0.70") else 90 if o["al"] <= F("0.85") else 80,
                            uph=m["uph"] / mu * 100,
                            yl=100 if m["yl"] >= F("99.50") else 90 if m["yl"] >= F("99.20") else 80 if m["yl"] >= F("98.80") else 60,
                            price=mt_ / o["tco"] * 100,
                            lead=100 if o["lead"] <= 14 else 90 if o["lead"] <= 17 else 80,
                            svc=100 if P[s]["svc"] <= 2 else 85)
        o["raw"] = sum(sc[k] * W[k] for k in W) / 100; o["tot"] = rnd(o["raw"])
    rank = sorted(ok, key=lambda s: (-out[s]["tot"], out[s]["tco"], -(sum(out[s]["sc"].values()) - out[s]["sc"]["price"])))
    return out, ok, rank


def ko_ans(**kw): return "-".join(s for s in SUP if evaluate(**kw)[0][s]["ko"]) or "없음"


def tco_ans(**kw):
    t = {s: tco(s, **kw)["total"] for s in SUP}; s = min(t, key=t.get)
    assert sorted(t.values())[0] != sorted(t.values())[1]
    return f"{s}/{mil(t[s])}"


def top_ans(**kw):
    out, ok, rank = evaluate(**kw)
    assert len(rank) == 1 or out[rank[0]]["tot"] != out[rank[1]]["tot"], kw
    return f"{rank[0]}/{out[rank[0]]['tot']}"


def final(**kw):
    out, ok, rank = evaluate(**{**dict(budget=BUDGET1, W=W1, gem=True), **kw})
    assert len(rank) == 1 or out[rank[0]]["tot"] != out[rank[1]]["tot"], kw
    return rank[0]


# ---------- 2-1 원안 Knock-out ----------
a1 = ko_ans()
t1 = {"정렬 정밀도를 run 평균으로 판정": ko_ans(align_mean=True), "E사 '납기 16주'(출하 기준) 문구만 사용": ko_ans(headline=True),
      "D사 제안서 임의 환율(1,320원) 사용": ko_ans(ref=True), "C사 VAT 포함 금액으로 예산 비교": ko_ans(vat=False),
      "무효 run 포함": ko_ans(invalid=True), "카탈로그 성능값 사용": ko_ans(claimed=True),
      "회의록 B사 자체 재시험(0.93µm) 반영": ko_ans(b_retest=True), "회의록 E사 구두 납기 단축 반영": ko_ans(e_verbal=True),
      "회의록 확정 사항(예산 100억·K6)을 원안에 반영": ko_ans(budget=BUDGET1, gem=True)}
assert a1 == "B-D-E", a1
assert t1["정렬 정밀도를 run 평균으로 판정"] == "D-E" and t1["E사 '납기 16주'(출하 기준) 문구만 사용"] == "B-D"
assert t1["D사 제안서 임의 환율(1,320원) 사용"] == "B-E" and t1["C사 VAT 포함 금액으로 예산 비교"] == "B-C-D-E"
assert t1["무효 run 포함"] == "A-B-D-E" and t1["회의록 확정 사항(예산 100억·K6)을 원안에 반영"] == "A-B-E"
for k, v in t1.items(): assert v != a1, k

# ---------- 2-2 5년 TCO 최소 ----------
T = {s: tco(s) for s in SUP}
a2 = tco_ans()
t2 = {"B·D 제안서 임의 환율 사용": tco_ans(ref=True), "무상보증 기간에도 유지보수비 계상": tco_ans(war=False),
      "D사 대당 유지보수비를 4대 전체로 오독": tco_ans(munit=False), "E사 6대 이상 할인 적용": tco_ans(disc=False),
      "카탈로그 소비전력 사용": tco_ans(claimed=True)}
assert a2 == "E/10764", a2
assert t2["B·D 제안서 임의 환율 사용"].startswith("B/") and t2["무상보증 기간에도 유지보수비 계상"].startswith("A/")
assert t2["D사 대당 유지보수비를 4대 전체로 오독"].startswith("D/")
for k, v in t2.items(): assert v != a2, k

# ---------- 2-3 원안 가중 총점 1위 ----------
O0, OK0, R0 = evaluate()
a3 = top_ans()
t3 = {"상대평가 기준값에 탈락 공급사 포함": top_ans(rel_all=True), "무효 run 포함(A사 K1 탈락)": top_ans(invalid=True),
      "회의록 확정 가중치를 원안에 적용": top_ans(W=W1), "C사 VAT 포함 금액 사용(C사 K4 탈락)": top_ans(vat=False),
      "D사 임의 환율로 D사 통과": top_ans(ref=True), "카탈로그 성능값 사용": top_ans(claimed=True)}
assert OK0 == ["A", "C"] and a3 == "A/97.0", a3
assert t3["무효 run 포함(A사 K1 탈락)"].startswith("C/")
for k, v in t3.items(): assert v != a3, k

# ---------- 2-4 회의록 확정 사항 반영 후 최종 선정 ----------
O1, OK1, R1 = evaluate(budget=BUDGET1, W=W1, gem=True)
a4c = R1[0]; a4 = SUP.index(a4c) + 1
t4 = {"예산 상향(확정) 미반영": final(budget=BUDGET0), "가중치 조정(확정) 미반영": final(W=W0),
      "K6 GEM300(확정) 미반영": final(gem=False), "A사 GEM300 옵션비만 가산하고 A사 유지": final(gem_add=True),
      "미확정 환율 1,420원 적용": final(fx=FX_T), "미확정 납기 16주 적용": final(lead_max=16), "보류된 가중치(UPH 25·가격 25) 적용": final(W=WH)}
assert OK1 == ["C", "D"] and a4c == "D" and O1["A"]["ko"] == ["K6"] and O1["D"]["equip"] <= BUDGET1 < O1["D"]["equip"] * FX_T / FX
assert t4["K6 GEM300(확정) 미반영"] == "A" and t4["가중치 조정(확정) 미반영"] == "C" and t4["미확정 환율 1,420원 적용"] == "C"
for k, v in t4.items(): assert v != a4c, k
assert final(b_retest=True) == final(e_verbal=True) == "D"  # 미인정 사항은 반영해도 결과 불변(참고)

# ---------- 파일 ----------
def won(x): return f"{int(x):,}"
def won_m(x): return f"{mil(x):,}"


STD = f"""[p.1]
ㅇㅇ반도체 패키징제조센터 구매팀 | 평가기준서 PUR-EV-2611 (원안) | 작성 2026-09-25 | 보안 등급: 사내 한정(대외비)
P3 패키징 라인 TC 본더(열압착 본딩 장비) 공급사 선정 평가기준서

1. 개요
- 구매 대상: HBM 적층용 TC 본더(Thermo-Compression Bonder) 4대, 동일 모델 일괄 발주
- 설치 장소: ㅇㅇ반도체 P3 패키징 라인(클린룸 2층 본딩 베이)
- 평가 대상: 1차 서류 심사를 통과한 5개사(A사·B사·C사·D사·E사)의 최종 제안서(제출 마감 2026-10-02 18:00)
- 평가 기준일: 2026-10-16
- 평가 절차: ① 필수 요건(Knock-out) 판정 → ② 통과 공급사 대상 가중 총점 평가 → ③ 가중 총점 1위 공급사를 최종 선정(우선협상대상)한다.

2. 공통 적용 규칙
2.1 금액 기준: 모든 금액은 원화(KRW), 부가가치세(VAT) 별도 기준으로 비교한다. VAT 포함 금액으로 제시된 경우 1.1로 나누어 VAT 별도 금액으로 환산한다.
2.2 환율: 외화 금액은 평가 적용 환율 USD 1 = {FX:,}원(2026-09-30 매매기준율)으로 환산하며, 평가 기간 중 고정한다. 공급사가 제안서에 임의로 기재한 환율·원화 환산 금액은 사용하지 않는다.
2.3 단위: 제안서마다 금액 단위(원·천원·USD)와 기준(대당·4대 합계·연간)이 다르므로, 반드시 '원 단위·4대 기준'으로 통일한 뒤 비교한다.
2.4 할인: 제안서에 명시된 할인은 그 적용 조건(수량 등)을 이번 발주(4대)가 충족하는 경우에만 반영한다.
2.5 성능 값: 정렬 정밀도·UPH·본딩 수율·소비전력은 제안서의 카탈로그(사양) 값이 아니라 '03 기술검증 결과'의 실측값만 사용한다.
 - 결과표의 유효여부가 N(무효)인 run은 모든 계산에서 제외한다.
 - 정렬 정밀도(정렬오차 3σ) = 유효 run 값 중 최댓값(가장 나쁜 값)
 - UPH·본딩 수율·소비전력 = 유효 run 값의 산술 평균
2.6 납기: 발주일부터 설치·셋업 완료(SAT 합격)까지의 기간(주)을 말한다. 제안서에 출하(선적)까지의 기간과 설치·셋업 기간이 나뉘어 있으면 합산한다.
2.7 제안 내용 변경: 제출 마감 이후의 제안 변경은 공문(서면)으로 제출되어 선정위원회가 승인한 경우에만 인정한다. 전화·메일·구두 언급은 인정하지 않는다.
2.8 평가 기준 변경: 선정위원회 회의록 '결정 사항'에서 상태가 '확정'인 항목만 반영한다. '검토', '보류', '미인정', '미반영' 등 확정되지 않은 항목은 반영하지 않는다.

[p.2]
3. 필수 요건(Knock-out) — 하나라도 충족하지 못하면 평가 대상에서 제외한다.
K1 정렬 정밀도: 정렬오차(3σ) 1.00µm 이하
K2 생산성: UPH 1,500 이상
K3 납기: 20주 이내
K4 예산: 장비 구매가 합계(본체 4대, 할인 반영, VAT 별도) 96억 원 이하
    ※ 설치·셋업비, 유지보수비, 소모품비, 옵션 금액은 K4 금액에 포함하지 않는다.
K5 A/S: 국내 기술지원 거점 보유 및 장애 접수 후 4시간 이내 현장 출동

4. 5년 TCO(총소유비용) 산정 — 4대 기준, 원 단위
TCO = ① 장비 구매가 + ② 설치·셋업비 + ③ 유지보수비 + ④ 소모품비 + ⑤ 전력비
① 장비 구매가: K4와 같은 기준(본체 4대, 할인 반영)
② 설치·셋업비: 제안서 기재 금액의 4대분(본체 가격에 포함된 경우 0원)
③ 유지보수비: 연간 유지보수 계약금(4대 전체 기준) × (5 − 무상보증 연수). 무상보증 기간에는 유지보수 계약금이 발생하지 않는다.
④ 소모품비: 대당 연간 소모품비 × 4대 × 5년
⑤ 전력비: 실측 평균 소비전력(kW, 대당) × 연 {HOURS:,}시간 × 5년 × 4대 × {KWH}원/kWh
- TCO는 중간 반올림 없이 원 단위까지 계산하여 가격 점수에 사용한다.

5. 가중 총점 평가 — Knock-out 통과 공급사 대상
항목 | 가중치 | 항목 점수(100점 만점)
정렬 정밀도 | {W0['al']} | 0.70µm 이하 100 / 0.85µm 이하 90 / 1.00µm 이하 80
UPH | {W0['uph']} | 해당 공급사 UPH ÷ 평가 대상 중 최고 UPH × 100
본딩 수율 | {W0['yl']} | 99.50% 이상 100 / 99.20% 이상 90 / 98.80% 이상 80 / 그 미만 60
가격(5년 TCO) | {W0['price']} | 평가 대상 중 최저 TCO ÷ 해당 공급사 TCO × 100
납기 | {W0['lead']} | 14주 이내 100 / 17주 이내 90 / 20주 이내 80
서비스(A/S) | {W0['svc']} | 현장 출동 2시간 이내 100 / 4시간 이내 85
- '평가 대상'은 Knock-out을 통과한 공급사만을 말한다. 상대평가 기준값(최고 UPH·최저 TCO)에 탈락 공급사를 포함하지 않는다.
- 가중 총점 = Σ(항목 점수 × 가중치) ÷ 100. 항목 점수는 반올림하지 않으며, 가중 총점만 소수 둘째 자리에서 반올림하여 소수 첫째 자리까지 산출한다.
- 동점 처리: 가중 총점이 같으면 5년 TCO가 낮은 공급사를, TCO도 같으면 가격을 제외한 항목 점수 합계가 높은 공급사를 상위로 한다.

[p.3]
6. 보고
- 평가 결과 보고서에는 공급사별 Knock-out 판정 근거(해당 요건 번호), 5년 TCO 산출 내역, 항목 점수를 포함한다.
- 개정 이력: 원안 2026-09-25 작성(구매팀), 검토(패키징생산기술팀·품질팀·재무팀·자동화팀)
작성 구매팀 | 검토 패키징생산기술팀장 | 승인 패키징제조센터장"""

PROP = {
"A": f"""[p.1]
A사 | TC 본더 공급 제안서(최종) | 제출일 2026-10-01 | 수신: ㅇㅇ반도체 패키징제조센터 구매팀
1. 회사 개요
- 국내 본딩 장비 전문 제조사. 본사·공장 충남 천안, 국내 서비스 인력 42명(천안 본사 서비스센터 상주 28명).
- 최근 3년 국내 메모리 후공정 라인 TC 본더 누적 납품 61대.
2. 제안 장비: TCB-7A (HBM 12단 적층 대응 열압착 본더)
- 정렬 정밀도 ±{CLAIM['A'][0]}µm(3σ, 당사 표준 시료 기준)
- UPH 최대 {CLAIM['A'][1]:,}ea/h(다이 10×11mm, 단일 헤드 기준)
- 본딩 수율 {CLAIM['A'][2]}% 이상(당사 고객 양산 라인 실적)
- 정격 소비전력 {CLAIM['A'][3]}kW, 본딩 하중 최대 500N, 헤드 온도 최대 450℃
- 장비 통신: SECS/GEM(HSMS) 기본 통신 표준 제공

[p.2]
3. 가격 제안 (단위: 원, VAT 별도)
항목 | 금액 | 비고
TCB-7A 본체 | 대당 {won(P['A']['price'][1])} |
일괄 발주 할인 | 본체 가격의 2% | 동일 모델 4대 이상 동시 발주 시
설치·셋업(SAT 포함) | 본체 가격에 포함 | 별도 청구 없음
GEM300 표준 패키지(E40·E87·E90·E94) | 대당 {won(GEM_OPT)} | 선택 옵션(본체 미포함)
4. 납기
- 발주 후 {P['A']['ship']}주 이내 출하, 출하 후 설치·셋업(SAT) {P['A']['ins']}주
5. 보증 및 유지보수
- 무상 보증: SAT 합격일로부터 {P['A']['war']}년
- 보증 종료 후 연간 유지보수 계약(정기 PM 분기 1회, 부품 15% 할인 포함): 4대 일괄 연 {won(P['A']['maint'][0])}원
6. 소모품
- 본딩 툴·콜릿·스테이지 보호 필름 등: 대당 연간 약 {won(P['A']['cons'])}원(월 25일·일 20시간 가동 가정)
7. A/S
- 천안 본사 서비스센터, 24시간 장애 접수, 접수 후 {P['A']['svc']}시간 이내 현장 도착(P3 라인 기준)
8. 결제 및 기타
- 선급 30% / 출하 50% / SAT 합격 후 20%, 견적 유효기간 2026-12-31
- 본 제안서의 사양 값은 당사 표준 조건 기준이며, 고객사 시료 조건에 따라 달라질 수 있습니다.

[p.3]
9. 설치 요건(대당)
- 전원 3상 380V 60Hz 50kVA, CDA 0.5MPa 이상, N2 순도 99.999% 200L/min, 배기 15m³/min
- 설치 면적 2.1m × 1.8m(유지보수 공간 별도), 바닥 하중 1,200kg/m² 이상
10. 교육 및 기술 지원
- 운영자 교육 3일(최대 12명), 설비 엔지니어 교육 10일(최대 6명) 무상
- 양산 안정화 기간(SAT 후 4주) 당사 엔지니어 2명 상주 지원
11. 예비 부품 단가(참고, 2026년 기준)
- 본딩 헤드 어셈블리 38,000,000원 / 비전 카메라 모듈 12,500,000원 / 스테이지 히터 4,200,000원
12. 납품 실적(최근 3년)
- 국내 메모리 고객 P1·P2 라인 TCB-6 시리즈 49대, TCB-7A 12대 가동 중""",
"B": f"""[p.1]
B사 Korea | Proposal for TC Bonder (Final Rev.) | 제출일 2026-09-30 | To: ㅇㅇ반도체 구매팀
1. Company Overview
- 글로벌 반도체 후공정 장비 제조사의 한국 지사(경기 이천). 국내 상주 서비스 엔지니어 18명, 부품 창고 이천 운영.
- 해외 메모리 고객 TC 본더 설치 실적 200대 이상.
2. Proposed Model: BX-1650 TC Bonder
- Alignment accuracy ±{CLAIM['B'][0]}µm(3σ)
- Throughput {CLAIM['B'][1]:,} UPH(nominal)
- Bonding yield {CLAIM['B'][2]}%(field average)
- Power consumption {CLAIM['B'][3]}kW(rated)
- Host interface: SECS/GEM 및 GEM300(E40/E87/E90/E94) 기본 포함(Standard)

[p.2]
3. Price Proposal (Currency: USD, VAT excluded)
Item | Price | Remark
BX-1650 unit price | USD {won(P['B']['price'][1])} / unit |
Installation & setup(SAT 포함) | USD {won(P['B']['inst'][0])} / unit |
Warranty | {P['B']['war'] * 12} months from SAT | 무상
Service contract(보증 종료 후) | USD {won(P['B']['maint'][0])} / year | 4 units total
Consumables(bond tool, collet) | USD {won(P['B']['cons'])} / unit / year |
※ 참고: 본체 4대 합계 USD {won(P['B']['price'][1] * N)} — 원화 환산 약 {won(P['B']['price'][1] * N * P['B']['ref'])}원(당사 적용 환율 1 USD = {P['B']['ref']:,}원)
4. Delivery
- 발주 후 {P['B']['ship']}주 내 귀사 P3 라인 반입(DDP 조건, 해상 운송·통관 포함), 반입 후 설치·셋업 {P['B']['ins']}주
5. Service
- 이천 지사 24/7 hotline, 장애 접수 후 {P['B']['svc']}시간 이내 현장 출동
6. Payment Terms
- T/T, 선급 20% / 선적 70% / SAT 10%, 제안 유효기간 제출일로부터 90일

[p.3]
7. Facility Requirements(per unit)
- Power 3-phase 380V 60Hz 55kVA, CDA 0.6MPa, N2 250L/min, Exhaust 18m³/min
- Footprint 2.3m × 1.9m, 설치 전 바닥 진동 측정(VC-C 등급) 필요
8. Training & Support
- Operator training 5 days, Maintenance training 2 weeks(본사 교육센터 또는 이천 지사)
- 원격 진단(Remote Diagnostics) 포털 계정 4개 무상 제공
9. Export & Logistics
- 전략물자 해당 여부 사전 판정 완료(비해당), 통관·내륙 운송은 당사 부담
- 장비 반입 일정은 선적 2주 전 확정 통보
10. Notes
- 본 제안 가격은 4대 동시 발주 기준이며, 부분 발주 시 재견적합니다.""",
"C": f"""[p.1]
C사 | TC 본더 납품 견적 및 기술 제안서 | 제출일 2026-10-02 | 수신: ㅇㅇ반도체 구매팀 귀중
1. 회사 소개
- 국내 정밀 장비 제조사, 경기 화성 본사·공장. P3 라인에서 차량 30분 거리 서비스센터 운영(엔지니어 15명).
2. 제안 장비: HC-900T
- 정렬 정밀도 ±{CLAIM['C'][0]}µm(3σ) / UPH {CLAIM['C'][1]:,} / 본딩 수율 {CLAIM['C'][2]}% / 소비전력 {CLAIM['C'][3]}kW
- 듀얼 스테이지, 실시간 휨(warpage) 보정, GEM300 표준 인터페이스 기본 탑재

[p.2]
3. 견적 (단위: 천원)
※ 본 견적서의 모든 금액은 부가가치세(10%)가 포함된 금액입니다.
항목 | 금액(천원) | 비고
HC-900T 본체 4대 일괄 공급가 | {won(P['C']['price'][1])} | 4대 합계
설치·셋업(SAT 포함) | 대당 {won(P['C']['inst'][0])} |
유지보수 계약(보증 종료 후) | 연 {won(P['C']['maint'][0])} | 4대 일괄
소모품(본딩 툴·콜릿) | 대당 연 {won(P['C']['cons'])} | 예상 사용량 기준
GEM300 인터페이스 | 0 | 기본 포함
4. 납기
- 발주 후 {P['C']['ship']}주 출하, 설치·셋업 {P['C']['ins']}주(총 {P['C']['ship'] + P['C']['ins']}주)
5. 보증
- SAT 합격 후 {P['C']['war']}년 무상 보증(소모품 제외)
6. A/S
- 화성 서비스센터, 장애 접수 후 {P['C']['svc']}시간 이내 현장 출동, 상주 엔지니어 파견은 별도 협의
7. 결제
- 계약금 10% / 납품 70% / SAT 합격 후 20%, 견적 유효기간 2026-12-15

[p.3]
8. 설치 및 유틸리티 요건(대당)
- 전원 3상 380V 45kVA / CDA 0.5MPa / N2 180L/min / 배기 12m³/min, 설치 면적 2.0m × 1.7m
9. 교육·기술 지원
- 운영·정비 교육 각 5일, 양산 초기 3개월간 주 1회 정기 방문 점검
- 공정 레시피 최적화 지원(고객사 시료 기준, 최대 2회)
10. 품질 보증
- 납품 장비는 출하 전 FAT(공장 인수 시험) 100% 실시, FAT 결과서 제출
11. 특기 사항
- 견적 금액은 4대 일괄 발주 기준이며, 부분 발주 시 재견적합니다.""",
"D": f"""[p.1]
D사 | TC Bonder 공급 제안서 | 제출일 2026-10-02 | 수신: ㅇㅇ반도체 패키징제조센터 구매팀
1. 회사 개요
- 해외 본사 장비 제조사의 국내 법인(충북 청주). 국내 엔지니어 12명, 청주 부품 센터 운영.
2. 제안 장비: DX-Prime
- 정렬 정밀도 ±{CLAIM['D'][0]}µm(3σ) / UPH {CLAIM['D'][1]:,} / 본딩 수율 {CLAIM['D'][2]}%
- 에너지 절감형 펄스 히터 적용, 소비전력 {CLAIM['D'][3]}kW
- GEM300(E40·E87·E90·E94) Standard(기본 포함)

[p.2]
3. 가격 (USD, VAT 별도)
항목 | 금액 | 비고
DX-Prime 본체 | USD {won(P['D']['price'][1])} / 대 |
설치·셋업(SAT 포함) | USD {won(P['D']['inst'][0])} / 대 |
무상 보증 | SAT 후 {P['D']['war']}년 |
유지보수 계약(보증 종료 후) | USD {won(P['D']['maint'][0])} / 대 / 년 | 대당 단가
소모품 | USD {won(P['D']['cons'])} / 대 / 년 |
※ 원화 참고가: 본체 4대 합계 약 {won_m(P['D']['price'][1] * N * P['D']['ref'])}백만 원(2026-09 견적 시점 환율 {P['D']['ref']:,}원 적용) — 귀사 예산 상한 이내
4. 납기
- 발주 후 {P['D']['ship']}주 출하(항공 운송), 설치·셋업 {P['D']['ins']}주
5. A/S
- 청주 법인 서비스팀, 장애 접수 후 {P['D']['svc']}시간 이내 현장 출동, 원격 진단 24시간
6. 결제
- 선급 30% / 선적 60% / SAT 10%, 제안 유효기간 2026-12-31

[p.3]
7. 유틸리티 요건(대당)
- 전원 3상 380V 40kVA, CDA 0.5MPa, N2 150L/min, 배기 10m³/min, 설치 면적 2.2m × 1.6m
8. 에너지 절감
- 펄스 히터 및 대기 모드 자동 전환으로 동급 장비 대비 소비전력 약 20% 절감(당사 내부 시험 기준)
9. 교육·지원
- 운영자 교육 3일, 정비 교육 8일(청주 법인 교육장), 다국어 매뉴얼(국문·영문) 제공
- SAT 후 6개월간 월 1회 예방 점검 무상
10. 비고
- 유지보수 계약은 4대 일괄 체결 시에도 상기 대당 단가가 적용됩니다.
- 항공 운송 지연 등 불가항력 사유 발생 시 납기는 상호 협의합니다.""",
"E": f"""[p.1]
E사 | P3 라인 TC 본더 제안서 | 제출일 2026-09-29 | 수신: ㅇㅇ반도체 구매팀
★ 업계 최단 납기 {P['E']['ship']}주 보장 ★
1. 회사 개요
- 국내 후공정 장비 제조사, 경기 평택 본사. 서비스 인력 20명.
2. 제안 장비: EB-500
- 정렬 정밀도 ±{CLAIM['E'][0]}µm(3σ) / UPH {CLAIM['E'][1]:,} / 본딩 수율 {CLAIM['E'][2]}% / 소비전력 {CLAIM['E'][3]}kW
- GEM300 표준 인터페이스 기본 제공

[p.2]
3. 가격 (단위: 원, VAT 별도)
항목 | 금액 | 비고
EB-500 본체 | 대당 {won(P['E']['price'][1])} |
볼륨 할인 | 본체 가격의 3% | 동일 모델 6대 이상 일괄 발주 시(향후 증설 물량 포함 계약 시 협의)
설치·셋업 | 대당 {won(P['E']['inst'][0])} |
무상 보증 | SAT 후 {P['E']['war']}년 |
유지보수 계약(보증 종료 후) | 연 {won(P['E']['maint'][0])} | 4대 일괄
소모품 | 대당 연 {won(P['E']['cons'])} |
4. 납기
- 납기 {P['E']['ship']}주(발주 후 출하 기준)
- 설치·셋업 및 공정 안정화(SAT 포함) {P['E']['ins']}주 별도
5. A/S
- 평택 서비스센터, 장애 접수 후 {P['E']['svc']}시간 이내 현장 출동
6. 결제
- 선급 20% / 출하 60% / SAT 20%, 제안 유효기간 2026-11-30

[p.3]
7. 설치 요건(대당)
- 전원 3상 380V 50kVA, CDA 0.5MPa, N2 200L/min, 배기 14m³/min, 설치 면적 2.0m × 1.9m
8. 교육 및 지원
- 운영자 교육 2일, 정비 교육 5일, 매뉴얼 국문 제공
- 공정 안정화 기간 동안 당사 엔지니어 1명 상주
9. 당사 강점
- 국내 생산으로 부품 수급이 빠르며, 주요 부품 국내 재고 상시 보유(평택 창고)
- 고객 요청 시 장비 커스터마이징(로더·언로더 사양 변경) 대응 가능(별도 견적)
10. 비고
- '납기 16주'는 발주 후 당사 공장 출하 시점 기준입니다.""",
}

DATES = dict(A="2026-10-06", B="2026-10-07", C="2026-10-08", D="2026-10-09", E="2026-10-10")
CSV = "\n".join(["공급사,Run,시험일,시료Lot,정렬오차3σ(µm),UPH(ea/h),본딩수율(%),평균소비전력(kW),유효여부,비고"] + [
    f"{s},R{i},{DATES[s]},DV26{10 + SUP.index(s)}-{i:02d},{r[0]},{r[1]},{r[2]},{r[3]},{'Y' if r[4] else 'N'},{r[5]}"
    for s in SUP for i, r in enumerate(RUNS[s], 1)])

MIN = f"""P3 TC 본더 공급사 선정위원회 2차 회의록
- 일시: 2026-10-14(수) 14:00~15:40 / 장소: 패키징제조센터 3층 대회의실
- 참석: 패키징생산기술팀장(위원장), 구매팀 과장(간사), 재무팀 차장, 품질팀 책임, 패키징생산기술팀 책임, 자동화팀 책임
- 안건: (1) 투자 예산 (2) 평가 가중치 (3) 필수 요건 추가 (4) 공급사 이슈

1. 투자 예산
- 재무팀 차장: 10/12 투자심의위원회에서 P3 TC 본더 투자 예산 증액이 승인됐다. K4 예산 상한을 96억 원에서 100억 원(본체 4대, VAT 별도)으로 올린다.
- 위원장: K4에 바로 반영한다. → 결정 1
- 재무팀 차장: 최근 원/달러 환율이 {FX_T:,}원 수준까지 올랐다. {FX_T:,}원으로 다시 계산하면 D사 본체 합계가 100억 원을 넘는다. 평가 환율을 갱신해야 하지 않나.
- 구매팀 과장: 기준서 2.2는 평가 기간 중 환율 고정이고, 중간에 바꾸면 공급사 간 형평성 문제가 생긴다.
- 위원장: 환율 갱신 여부는 재무팀이 법무 검토를 받아 차기 회의에서 결정한다. 그 전까지는 원안 환율을 유지한다. → 결정 4

2. 평가 가중치
- 재무팀 차장: 원가 절감 기조를 반영해 가격 30→40, 납기 10→5, 서비스 10→5로 조정하자. 나머지 항목은 유지.
- 패키징생산기술팀 책임: 양산 생산성이 더 중요하다. UPH 20→25로 올리고 가격은 25로 낮추는 안을 제안한다.
- 품질팀 책임: UPH 상향 안은 추가 기술검증 데이터를 보고 판단하는 게 맞다.
- 위원장: 재무팀 안을 채택한다. UPH 상향 안은 보류한다. → 결정 2, 결정 6

3. 필수 요건 추가
- 자동화팀 책임: P3 라인 EAP·MES 자동 반송 연동에는 GEM300 표준(E40·E87·E90·E94) 대응이 반드시 필요하다. SECS/GEM 기본 통신만으로는 연동이 안 된다.
- 위원장: 필수 요건 K6 'GEM300 표준 인터페이스를 장비 기본 사양(본체 가격 포함)으로 제공할 것'을 추가한다. 유상 옵션으로만 제공하면 미충족으로 본다. → 결정 3
- 패키징생산기술팀 책임: 고객사 양산 일정을 감안하면 K3 납기 기준을 20주에서 16주로 줄여야 한다.
- 위원장: 10/20 생산계획 확정 후 차기 회의에서 결정한다. → 결정 5

4. 공급사 이슈
- 품질팀 책임: B사가 10/13 자사 데모룸에서 재시험한 성적서(정렬오차 0.93µm)를 메일로 보내왔다. 당사 입회 없이 진행된 시험이라 기술검증 결과로 인정할 수 없다. 입회 재시험 여부는 차기 회의에서 논의한다. → 결정 7
- 구매팀 과장: E사 영업 담당이 통화 중 '설치·안정화 기간을 4주로 줄일 수 있다'고 했으나 서면 제출은 없었다. → 결정 8
- 구매팀 과장: A사도 'GEM300 패키지를 본체 가격에 무상 포함해 줄 수 있다'고 구두로 전해 왔다. 공문은 아직 없다. → 결정 9
- 위원장: 제출 마감 이후의 구두 변경은 기준서 2.7에 따라 인정하지 않는다.

5. 결정 사항
No | 내용 | 상태
1 | K4 예산 상한 96억 원 → 100억 원(본체 4대, VAT 별도) | 확정
2 | 가중치 조정: 정렬 15 · UPH 20 · 수율 15 · 가격 40 · 납기 5 · 서비스 5 | 확정
3 | 필수 요건 K6 추가: GEM300 표준 인터페이스 기본 사양 제공(유상 옵션 불인정) | 확정
4 | 평가 환율 {FX_T:,}원으로 갱신 | 검토(차기 회의 결정)
5 | K3 납기 기준 20주 → 16주 | 검토(차기 회의 결정)
6 | 가중치 UPH 25 · 가격 25 조정 | 보류
7 | B사 자체 재시험 결과(0.93µm) 반영 | 미인정
8 | E사 설치·안정화 기간 4주 단축(구두) | 미반영
9 | A사 GEM300 무상 포함(구두) | 미반영
- 차기 회의: 2026-10-21(수) 14:00, 최종 선정 결과는 결정 1~3을 반영해 보고한다.
- 작성: 구매팀 과장 / 확인: 위원장"""

F1, F2 = "2_공급사선정", "2-공급사제안서"


def tok(t): return int(round(len(t) * 1.18, -1))


files = [{"name": "01_공급사_평가기준서.pdf", "folder": F1, "kind": "pdf", "tokens": tok(STD), "content": STD}]
files += [{"name": f"02_{s}사_제안서.pdf", "folder": F2, "kind": "pdf", "tokens": tok(PROP[s]), "content": PROP[s]} for s in SUP]
files += [{"name": "03_기술검증_결과.csv", "folder": F1, "kind": "csv", "tokens": tok(CSV) + 300, "content": CSV},
          {"name": "04_선정위원회_2차_회의록.txt", "folder": F1, "kind": "text", "tokens": tok(MIN), "content": MIN}]
TOT = sum(f["tokens"] for f in files)
assert 12000 <= TOT <= 18000, TOT

summary = f"""ㅇㅇ반도체 패키징제조센터 구매팀 과장인 당신은 P3 패키징 라인에 설치할 TC 본더(열압착 본딩 장비) 4대의 공급사를 선정해 경영진 보고서를 써야 합니다. 5개 공급사(A~E사)의 최종 제안서, 당사 입회 기술검증 결과, 10/14 선정위원회 회의록을 바탕으로 평가하세요.

- `01_공급사_평가기준서.pdf`는 금액 환산(환율·VAT·단위·할인) 규칙, 필수 요건(Knock-out) K1~K5, 5년 TCO 산식, 항목별 가중치·배점과 동점 처리 규칙이 담긴 평가 기준 **원안**입니다.
- `{F2}` 폴더의 `02_A사_제안서.pdf` ~ `02_E사_제안서.pdf`는 공급사별 가격·납기·보증·유지보수·A/S 조건입니다. 통화(원·천원·USD), VAT 포함 여부, 대당/4대 합계 기준이 공급사마다 다릅니다.
- `03_기술검증_결과.csv`는 공급사별 데모 시험 run의 실측값(정렬오차 3σ·UPH·본딩 수율·평균 소비전력)과 유효 여부입니다.
- `04_선정위원회_2차_회의록.txt`는 평가 기준 변경 논의와 결정 사항입니다. 결정 상태(확정·검토·보류·미인정·미반영)를 구분해 읽어야 합니다.

[2-1]~[2-3]은 평가기준서 원안 기준, [2-4]는 회의록의 '확정' 사항을 반영한 기준으로 답하세요."""


def fx_detail(s):
    t = T[s]; return f"{s} {won_m(t['total'])}(장비 {won_m(t['equip'])}·설치 {won_m(t['inst'])}·유지보수 {won_m(t['maint'])}·소모품 {won_m(t['cons'])}·전력 {won_m(t['power'])})"


def sc_line(o, s): return f"{s}사 {o[s]['tot']}점"


questions = [
 {"kind": "short",
  "q": "[2-1] 평가기준서 **원안**(04 회의록 반영 전) 기준으로, 필수 요건 K1~K5 중 하나라도 충족하지 못해 **탈락하는 공급사를 모두** 입력하세요. 공급사 기호(A~E)를 알파벳순으로 `-`로 연결합니다. 탈락 공급사가 없으면 `없음`을 입력합니다. (예: `A-C`)",
  "answer": a1, "accept": [a1, a1.replace("-", "/"), a1.replace("-", ""), "B사-D사-E사", "B사D사E사", "B사/D사/E사"],
  "explain": f"B사: 유효 run 정렬오차 최댓값 {float(O0['B']['al']):.2f}µm > 1.00 → K1 탈락(평균 {float(O0['B']['mt']['al_mean']):.4f}µm로 보면 통과로 오판). "
             f"D사: 본체 USD {won(P['D']['price'][1])}×4×{FX:,}원 = {won(O0['D']['equip'])}원 > 96억 → K4 탈락(제안서의 임의 환율 {P['D']['ref']:,}원이면 {won_m(P['D']['price'][1] * N * P['D']['ref'])}백만 원으로 통과처럼 보임). "
             f"E사: 출하 {P['E']['ship']}주 + 설치·안정화 {P['E']['ins']}주 = {lead('E')}주 > 20주 → K3 탈락('납기 {P['E']['ship']}주' 문구는 출하 기준). "
             f"A사는 무효 run(1.31µm)을 빼면 최댓값 {float(O0['A']['al']):.2f}µm로 통과, C사는 VAT 포함 {won(P['C']['price'][1])}천원 ÷ 1.1 = {won(O0['C']['equip'])}원으로 96억 이하라 통과. 정답 {a1}."},
 {"kind": "short",
  "q": "[2-2] 5개 공급사 **전체**(Knock-out 탈락 여부와 무관)의 5년 TCO를 평가기준서 원안 4장 산식으로 계산할 때, TCO가 **가장 낮은** 공급사와 그 금액을 `공급사/금액` 형식으로 입력하세요. 금액은 원화 **백만 원** 단위로, 백만 원 미만에서 반올림한 정수를 쉼표 없이 적습니다. (예: `B/10350`)",
  "answer": a2, "accept": [a2, a2.replace("/", "-"), a2.replace("/", ""), a2.replace("/", "사/"), a2 + "백만원"],
  "explain": "5년 TCO(백만 원): " + " / ".join(fx_detail(s) for s in SUP) + f". 최소는 {a2}. "
             f"함정: B·D사 제안서의 임의 환율을 쓰면 {t2['B·D 제안서 임의 환율 사용']}, 무상보증 기간에도 유지보수비를 넣으면 {t2['무상보증 기간에도 유지보수비 계상']}, "
             f"D사 유지보수 'USD {won(P['D']['maint'][0])}/대/년'을 4대 전체로 읽으면 {t2['D사 대당 유지보수비를 4대 전체로 오독']}, "
             f"E사의 '6대 이상' 할인을 적용하면 {t2['E사 6대 이상 할인 적용']}, 카탈로그 소비전력을 쓰면 {t2['카탈로그 소비전력 사용']}. C사는 천원 단위·VAT 포함이라 ×1,000 ÷ 1.1 해야 합니다."},
 {"kind": "short",
  "q": "[2-3] 평가기준서 원안 기준으로 Knock-out을 통과한 공급사만을 평가 대상으로 하여 5장 방법으로 가중 총점을 계산할 때, **1위** 공급사와 그 가중 총점을 `공급사/총점` 형식으로 입력하세요. 총점은 소수 둘째 자리에서 반올림하여 소수 첫째 자리까지 적습니다. (예: `C/88.5`)",
  "answer": a3, "accept": [a3, a3.replace("/", "-"), a3.replace("/", ""), a3.replace("/", "사/"), a3 + "점", "A/97"],
  "explain": f"평가 대상은 A·C사. A사: 정렬 {float(O0['A']['al']):.2f}µm→{O0['A']['sc']['al']}, UPH {float(O0['A']['mt']['uph']):.1f}/{float(O0['C']['mt']['uph']):.2f}×100={float(O0['A']['sc']['uph']):.2f}, "
             f"수율 {float(O0['A']['mt']['yl']):.2f}%→{O0['A']['sc']['yl']}, 가격 100(최저 TCO), 납기 {lead('A')}주→{O0['A']['sc']['lead']}, 서비스 2시간→100 ⇒ {O0['A']['tot']}점. "
             f"C사: 정렬·UPH·수율·납기·서비스 100, 가격 {float(O0['C']['sc']['price']):.2f} ⇒ {O0['C']['tot']}점. 정답 {a3}. "
             f"함정: 상대평가 기준값(최고 UPH·최저 TCO)에 탈락한 D·E사를 넣으면 {t3['상대평가 기준값에 탈락 공급사 포함']}, 무효 run을 넣으면 A사가 K1 탈락해 {t3['무효 run 포함(A사 K1 탈락)']}, "
             f"회의록 가중치를 원안에 적용하면 {t3['회의록 확정 가중치를 원안에 적용']}, 카탈로그 값을 쓰면 {t3['카탈로그 성능값 사용']}."},
 {"kind": "choice",
  "context": "10/14 선정위원회 2차 회의 이후, 구매팀은 차기 회의에 올릴 최종 선정 결과를 확정해야 합니다.",
  "q": "[2-4] 04 회의록 '결정 사항' 중 상태가 **확정**인 항목만 평가기준서 원안에 반영하여 Knock-out 판정과 가중 총점 평가를 다시 수행했을 때, 최종 선정되는 공급사(가중 총점 1위)는?",
  "options": [f"{s}사" for s in SUP], "answer": a4,
  "explain": f"확정 사항은 ① 예산 상한 100억 원 ② 가중치(가격 40·납기 5·서비스 5) ③ K6 GEM300 기본 사양. A사는 GEM300이 유상 옵션이라 K6 탈락(구두 무상 포함 제안은 미반영), "
             f"B사 K1·E사 K3 탈락은 그대로(재시험·구두 단축은 미인정/미반영), D사는 본체 {won_m(O1['D']['equip'])}백만 원으로 100억 이하라 재진입. "
             f"평가 대상 C·D사: {sc_line(O1, 'D')}, {sc_line(O1, 'C')} → D사. "
             f"함정: 미확정 환율 {FX_T:,}원을 적용하면 D사 본체 {won_m(O1['D']['equip'] * FX_T / FX)}백만 원으로 K4 탈락 → C사, 미확정 납기 16주 적용 시 D사({lead('D')}주) 탈락 → C사, "
             f"가중치 조정 미반영 시 → {t4['가중치 조정(확정) 미반영']}사, 보류된 UPH 25·가격 25 적용 시 → {t4['보류된 가중치(UPH 25·가격 25) 적용']}사, "
             f"K6 미반영(또는 A사 옵션비만 가산) 시 A사가 남아 → {t4['K6 GEM300(확정) 미반영']}사."},
]

part = {"title": "패키징 설비 공급사 선정", "summary": summary, "files": files, "questions": questions}
blind = {**part, "questions": [{k: v for k, v in q.items() if k not in ("answer", "accept", "explain")} for q in questions]}
for n, d in (("part.json", part), ("blind.json", blind)):
    with open(os.path.join(HERE, n), "w", encoding="utf-8") as f: json.dump(d, f, ensure_ascii=False, indent=1)

print("Q1", a1, "| Q2", a2, "| Q3", a3, "| Q4", a4, a4c)
print("traps1", t1); print("traps2", t2); print("traps3", t3); print("traps4", t4)
for s in SUP: print(fx_detail(s), "equip", won(O0[s]["equip"]))
for nm, O in (("원안", O0), ("확정", O1)):
    print(nm, {s: (O[s]["ko"] or str(O[s]["tot"]), float(O[s].get("raw", 0))) for s in SUP})
print("files", len(files), "tokens", TOT, [f["tokens"] for f in files])
