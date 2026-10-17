# -*- coding: utf-8 -*-
"""모의고사 1회 실기 문제 3: HBM 후공정 불량 판별 (결정적 생성기, 표준 라이브러리만)."""
import csv, io, json, os, random
from datetime import date
from decimal import Decimal, ROUND_HALF_UP
from fractions import Fraction as F

HERE = os.path.dirname(os.path.abspath(__file__))
R = random.Random(20261018)
D = lambda d: date(2026, 10, d)
REV, NOTICE = D(8), D(5)                          # 개정 항목 1 시행일 / 공지일(함정)
CAL_EQ, CAL_FROM, CAL_TO, CAL_OFF = "AOI-2", D(6), D(9), 15   # 크기는 0.1µm 단위 정수
OPTICAL = {"BV", "TC", "PT"}
HDR = "die_id,검사일,장비,구분,결함코드,크기_um,개수,위치"
DIR, SUB = "3_불량판별", "3-검사결과"
tok = lambda s: round(len(s) * 1.1)

# (로트, 1차 검사일, 1차 장비, 샘플 다이 수, 투입 수량, 계획 결함{번호: (코드, 크기x10, 개수, 위치)}, NM 번호, 재검{번호: (일, 코드, 크기x10, 개수, 위치)})
X = lambda c, s, n=1, l="PERI": (c, s, n, l)
OKD = ("-", 0, 0, "-")
LOTS = [
 ("HB01", 1, "AOI-1", 46, 720, {12: X("BH", 33)}, [], {}),
 ("HB02", 1, "AOI-2", 40, 640, {7: X("BV", 76), 29: X("BV", 72)}, [], {}),                                # 개정 소급 함정
 ("HB03", 2, "AOI-3", 45, 800, {5: X("BH", 32), 18: X("PT", 84, 4), 33: X("BV", 61, 1, "TSV")}, [], {}),
 ("HB04", 2, "AOI-1", 50, 720, {22: X("BV", 54), 40: X("PT", 52, 3)}, [], {22: (3, *X("BV", 51))}),
 ("HB05", 3, "AOI-2", 42, 720, {27: X("BB", 36)}, [], {}),                                                # SCRAP
 ("HB06", 5, "AOI-3", 48, 640, {16: X("BH", 30)}, [], {}),
 ("HB07", 5, "AOI-1", 50, 720, {9: X("BV", 83), 38: X("BH", 35)}, [14, 45], {}),                          # NM 제외 → 4.17%
 ("HB08", 5, "AOI-2", 40, 640, {11: X("BV", 84), 30: X("BV", 56, 1, "TSV")}, [], {}),                     # 보정 기간 밖 AOI-2
 ("HB09", 8, "AOI-1", 48, 800, {8: X("BV", 73), 17: X("BB", 28), 33: X("BV", 76), 41: X("BV", 54, 1, "TSV")}, [25], {17: (10, *OKD)}),
 ("HB10", 6, "AOI-2", 50, 720, {21: X("TC", 49, 1, "TSV"), 36: X("BH", 36)}, [], {}),                      # 보정 시 치명 해제
 ("HB11", 7, "AOI-1", 50, 640, {6: X("BV", 73), 24: X("BV", 78), 47: X("BH", 33)}, [], {}),               # 공지일 적용 함정
 ("HB12", 7, "AOI-2", 40, 720, {4: X("BV", 90), 19: X("BV", 62, 1, "TSV"), 35: X("PT", 208)}, [], {}),     # 보정 시 PASS
 ("HB13", 8, "AOI-3", 44, 640, {15: X("TC", 36, 1, "TSV"), 39: X("BH", 31)}, [], {}),                      # AOI-3 보정·TC 3.0 함정
 ("HB14", 8, "AOI-2", 44, 640, {10: X("BH", 34), 23: X("BV", 68, 1, "TSV"), 31: X("BV", 80)}, [], {}),
 ("HB15", 9, "AOI-1", 46, 720, {13: X("TC", 44, 1, "TSV"), 28: X("BH", 32), 42: X("BV", 52, 1, "TSV")}, [], {}),
 ("HB16", 9, "AOI-2", 42, 800, {3: X("BV", 83), 20: X("BV", 86), 37: X("BH", 30)}, [], {}),
 ("HB17", 10, "AOI-1", 48, 640, {26: X("TC", 35, 1, "TSV")}, [], {}),
 ("HB18", 10, "AOI-2", 46, 720, {14: X("BV", 74)}, [9], {9: (11, *OKD)}),
 ("HB19", 10, "AOI-3", 52, 800, {2: X("BV", 72), 30: X("BV", 75), 44: X("PT", 220)}, [], {}),
 ("HB20", 11, "AOI-1", 50, 640, {17: X("BV", 77), 35: X("BH", 38)}, [], {}),                               # 정확히 4.00%
 ("HB21", 11, "AOI-3", 48, 720, {8: X("BV", 66), 27: X("BV", 65), 41: X("BH", 33)}, [], {}),
 ("HB22", 12, "AOI-2", 46, 800, {5: X("BH", 31), 19: X("PT", 60, 3), 38: X("BV", 70)}, [], {}),
 ("HB23", 13, "AOI-1", 52, 640, {11: X("BV", 50, 1, "TSV"), 46: X("PT", 74, 5)}, [], {}),                  # 3.85%
 ("HB24", 13, "AOI-3", 44, 720, {12: X("BV", 55, 1, "TSV"), 31: X("BV", 88), 40: X("BH", 34)}, [], {31: (14, *X("BV", 61)), 40: (14, *X("BH", 26))}),
 ("HB25", 14, "AOI-1", 54, 800, {33: X("PT", 96, 4)}, [], {}),
 ("HB26", 14, "AOI-2", 34, 640, {22: X("BH", 32)}, [5, 19, 27], {19: (15, *X("BV", 60))}),                 # 재검으로 유효 32개
 ("HB27", 15, "AOI-2", 35, 720, {6: X("BV", 79), 24: X("BH", 35)}, [3, 12, 20, 31], {}),                   # 유효 31개 → RETEST
 ("HB28", 16, "AOI-3", 50, 800, {14: X("BB", 41, 2)}, [], {14: (16, *X("BB", 39, 2))}),
]
NOISE = [("BV", 30, 58, "PERI")] * 4 + [("BV", 20, 40, "TSV")] * 2 + [("BH", 8, 22, None)] * 3 + [("PT", 30, 140, None)] * 3 + [("TC", 10, 22, "TSV")]


def noise():  # 어떤 함정 조건에서도 불량이 되지 않는 미달 결함
    c, lo, hi, loc = R.choice(NOISE)
    return c, R.randint(lo, hi), R.randint(1, 2) if c == "PT" else 1, loc or R.choice(["PERI", "TSV"])


fmt = lambda s: f"{s // 10}.{s % 10}"
cell = lambda v: [v[0], fmt(v[1]), str(v[2]), v[3]]
CSV, META = {}, {}
for lot, d, eq, n, qty, plan, nm, rt in LOTS:
    rec = {**plan, **{i: ("NM", 0, 0, "-") for i in nm}}
    for i in R.sample([i for i in range(1, n + 1) if i not in rec and i not in rt], R.randint(4, 9)):
        rec[i] = noise()
    rows = [[f"{lot}-{i:03d}", D(d).isoformat(), eq, "1차", *cell(rec.get(i, OKD))] for i in range(1, n + 1)]
    for i, (rd, *v) in sorted(rt.items()):
        assert rd >= d and (D(rd) >= REV) == (D(d) >= REV)  # 재검이 개정 시행일을 가로지르지 않음 → 해석 불변
        rows.append([f"{lot}-{i:03d}", D(rd).isoformat(), "AOI-R", "재검", *cell(v)])
    CSV[lot] = HDR + "\n" + "\n".join(",".join(r) for r in rows) + "\n"
    META[lot] = dict(day=D(d), eq=eq, n=n, qty=qty)


# ---------------- 규칙 엔진 (CSV 텍스트를 다시 읽어 판정) ----------------
def parse(text):
    return [dict(die=r["die_id"], day=date.fromisoformat(r["검사일"]), eq=r["장비"], kind=r["구분"], code=r["결함코드"],
                 s=int(r["크기_um"].replace(".", "")), cnt=int(r["개수"]), loc=r["위치"]) for r in csv.DictReader(io.StringIO(text))]


ROWS = {lot: parse(t) for lot, t in CSV.items()}
for lot, rows in ROWS.items():
    assert len({r["die"] for r in rows}) == META[lot]["n"]
OK = dict(rev="ok", pend=False, cal="ok", rt="replace", nm=True, ge=False, tc=True)


def new_rule(day, o):
    return {"ok": day >= REV, "none": False, "notice": day >= NOTICE, "retro": True, "nextday": day > REV}[o["rev"]]


def size(r, o):
    s, c = r["s"], r["code"]
    if c in OPTICAL or (o["cal"] == "bh" and c == "BH"):
        if o["cal"] != "none" and r["eq"] == CAL_EQ and (o["cal"] == "all" or CAL_FROM <= r["day"] <= CAL_TO):
            s -= CAL_OFF
        if o["cal"] == "aoi3" and r["eq"] == "AOI-3":
            s += 6
    return s


def grade(r, o):
    c, s = r["code"], size(r, o)
    if c == "BB": return "C"
    if c == "TC": return "C" if o["tc"] and s >= (30 if o["pend"] else 40) else None
    if c == "BV": return "M" if s >= (50 if r["loc"] == "TSV" else 70 if new_rule(r["day"], o) else 80) else None
    if c == "BH": return "M" if s >= 30 else None
    if c == "PT": return "m" if r["cnt"] >= 3 or s >= 200 else None
    return None


def judge(rows, o):
    if o["rt"] == "replace":
        fin = {}
        for r in rows:
            if r["kind"] == "재검" or r["die"] not in fin: fin[r["die"]] = r
        dice = list(fin.values())
    else:
        dice = [r for r in rows if r["kind"] == "1차"] if o["rt"] == "first" else rows
    valid = [r for r in dice if not (o["nm"] and r["code"] == "NM")]
    bad = [r for r in valid if grade(r, o)]
    crit = [r for r in bad if grade(r, o) == "C"]
    ratio, lim = F(len(bad), len(valid)), F(3 if o["pend"] else 4, 100)
    j = "SCRAP" if crit else "RETEST" if len(valid) < 32 else "HOLD" if (ratio >= lim if o["ge"] else ratio > lim) else "PASS"
    return dict(j=j, bad=bad, crit=crit, n=len(valid), ratio=ratio)


def run(**kw):
    o = {**OK, **kw}
    return {lot: judge(rows, o) for lot, rows in ROWS.items()}


pct = lambda x: str((Decimal(x.numerator * 100) / Decimal(x.denominator)).quantize(Decimal("0.1"), ROUND_HALF_UP))
pct2 = lambda x: str((Decimal(x.numerator * 100) / Decimal(x.denominator)).quantize(Decimal("0.01"), ROUND_HALF_UP))
TRAPS = {
 "개정 공지 미반영": dict(rev="none"), "개정을 공지일(10-05)부터 적용": dict(rev="notice"), "개정 소급 적용": dict(rev="retro"),
 "시행일 당일 검사분 제외": dict(rev="nextday"), "시행 예정·미확정 항목 적용": dict(pend=True), "장비 보정 누락": dict(cal="none"),
 "AOI-2 전 기간 보정": dict(cal="all"), "BH까지 보정": dict(cal="bh"), "AOI-3 허용 오차 이내 오프셋 보정": dict(cal="aoi3"),
 "재검 대체 누락(1차 결과 사용)": dict(rt="first"), "재검 행을 별도 다이로 중복 집계": dict(rt="both"),
 "NM 유효 샘플 미제외": dict(nm=False), "HOLD 경계 4.0%를 '이상'으로 해석": dict(ge=True), "TC를 치명에서 누락": dict(tc=False),
}
J = run()
JUD = {lot: v["j"] for lot, v in J.items()}
assert JUD == {"HB01": "PASS", "HB02": "PASS", "HB03": "HOLD", "HB04": "PASS", "HB05": "SCRAP", "HB06": "PASS", "HB07": "HOLD",
               "HB08": "HOLD", "HB09": "HOLD", "HB10": "PASS", "HB11": "PASS", "HB12": "PASS", "HB13": "PASS", "HB14": "HOLD",
               "HB15": "SCRAP", "HB16": "HOLD", "HB17": "PASS", "HB18": "PASS", "HB19": "HOLD", "HB20": "PASS", "HB21": "PASS",
               "HB22": "HOLD", "HB23": "PASS", "HB24": "PASS", "HB25": "PASS", "HB26": "PASS", "HB27": "RETEST", "HB28": "SCRAP"}, JUD
assert J["HB20"]["ratio"] == F(4, 100) and J["HB26"]["n"] == 32 and J["HB27"]["n"] == 31 and J["HB07"]["n"] == 48

# ---------------- 3-1 HB09 판정 ----------------
L1 = "HB09"
h = {k: run(**kw)[L1] for k, kw in {"ok": {}, "none": dict(rev="none"), "next": dict(rev="nextday"), "nm": dict(nm=False),
                                    "first": dict(rt="first"), "both": dict(rt="both")}.items()}
assert h["ok"]["j"] == "HOLD" and h["none"]["j"] == h["next"]["j"] == "PASS" and h["nm"]["j"] == "HOLD"
assert h["first"]["j"] == h["both"]["j"] == "SCRAP" and len(h["first"]["crit"]) == 1 and h["first"]["crit"][0]["code"] == "BB"
desc = lambda v: f"치명 불량 없음, 불량 다이 {len(v['bad'])}개 / 유효 샘플 {v['n']}개(약 {pct(v['ratio'])}%)"
OPT1 = [f"PASS — {desc(h['none'])}, HOLD 기준 미해당", f"SCRAP — 치명 불량(BB) 다이 1개({h['first']['crit'][0]['die']})",
        f"HOLD — {desc(h['ok'])}, 4.0% 초과", f"HOLD — {desc(h['nm'])}, 4.0% 초과",
        "RETEST — 1차 검사에서 치명 결함(BB)이 검출되어 로트 재검사 필요"]
assert len(set(OPT1)) == 5 and pct(h["ok"]["ratio"]) != pct(h["nm"]["ratio"])
a1 = OPT1.index(f"HOLD — {desc(h['ok'])}, 4.0% 초과") + 1
assert a1 == 3 and [r["die"] for r in h["ok"]["bad"]] == ["HB09-008", "HB09-033", "HB09-041"]

# ---------------- 3-2 HOLD 로트 목록 ----------------
holds = lambda res: "/".join(l for l, v in res.items() if v["j"] == "HOLD")
a2 = holds(J)
assert a2 == "HB03/HB07/HB08/HB09/HB14/HB16/HB19/HB22", a2
t2 = {k: holds(run(**kw)) for k, kw in TRAPS.items()}
for k, v in t2.items(): assert v != a2, k

# ---------------- 3-3 보정 전후 판정 변화 ----------------
def changed(**kw):
    a, b = run(**kw), run(**{**kw, "cal": "none"})
    return "/".join(l for l in a if a[l]["j"] != b[l]["j"])


a3 = changed()
CAL_LOTS = [l for l, m in META.items() if m["eq"] == CAL_EQ and CAL_FROM <= m["day"] <= CAL_TO]
J0 = run(cal="none")
assert a3 == "HB10/HB12" and CAL_LOTS == ["HB10", "HB12", "HB14", "HB16"]
assert (J0["HB10"]["j"], J0["HB12"]["j"], J0["HB14"]["j"], J0["HB16"]["j"]) == ("SCRAP", "HOLD", "HOLD", "HOLD")
t3 = {"보정 대상 로트 전부 기재": "/".join(CAL_LOTS), **{k: changed(**TRAPS[k]) for k in
      ("AOI-2 전 기간 보정", "BH까지 보정", "AOI-3 허용 오차 이내 오프셋 보정", "개정 공지 미반영", "시행 예정·미확정 항목 적용")}}
for k, v in t3.items(): assert v != a3, k

# ---------------- 3-4 SCRAP 로트 수·투입 수량 ----------------
def scrap(res):
    ls = [l for l, v in res.items() if v["j"] == "SCRAP"]
    return f"{len(ls)}/{sum(META[l]['qty'] for l in ls)}", ls


a4, S4 = scrap(J)
assert a4 == "3/2240" and S4 == ["HB05", "HB15", "HB28"]
t4 = {k: scrap(run(**TRAPS[k]))[0] for k in ("재검 대체 누락(1차 결과 사용)", "재검 행을 별도 다이로 중복 집계", "장비 보정 누락",
                                              "시행 예정·미확정 항목 적용", "AOI-3 허용 오차 이내 오프셋 보정", "TC를 치명에서 누락")}
for k, v in t4.items(): assert v != a4, k

# ---------------- 문서 ----------------
STD = """[p.1]
ㅇㅇ반도체 HBM 후공정 불량 판정 기준서
문서번호 QS-HBM-0412 | Rev.4 | 시행 2026-09-01 | 주관 품질보증팀

1. 목적 및 적용 범위
HBM 코어 다이의 TSV·마이크로 범프 외관 검사(AOI) 결과로 다이 판정과 로트 판정을 내리는 기준을 정한다. 후공정 검사 라인에서 샘플링 검사한 모든 로트에 적용한다.

2. 검사 결과 파일 구성
- 로트 1개당 CSV 파일 1개이며, 한 행은 다이 1개에 대한 검사 1회의 결과이다.
- die_id: 로트ID-일련번호 / 검사일: 해당 행의 검사를 수행한 날짜 / 장비: 검사 장비 ID
- 구분: '1차'(샘플링 최초 검사) 또는 '재검'(재검사)
- 결함코드: 3장의 코드. 결함이 없으면 '-', 측정 불가이면 'NM'
- 크기_um: 결함 크기(µm, 소수 첫째 자리). BV·PT는 직경, TC는 크랙 길이, BH는 기준 높이 대비 편차, BB는 브릿지 길이
- 개수: 해당 결함의 검출 개수 / 위치: TSV(TSV 직상부 범프) 또는 PERI(주변부 범프)
- 한 다이에서 결함이 여러 개 검출되면 장비가 가장 심각한 결함 1건을 대표로 기록한다(다이 1개당 1행).

3. 결함 유형 코드와 다이 판정 기준
| 코드 | 명칭 | 등급 | 불량 판정 조건 |
| BB | 범프 브릿지 | 치명 | 크기·개수와 관계없이 검출되면 불량 |
| TC | TSV 크랙 | 치명 | 크랙 길이 4.0 µm 이상이면 불량 (4.0 µm 미만은 판정 대상 아님) |
| BV | 범프 보이드 | 주요 | 위치 TSV: 직경 5.0 µm 이상 / 위치 PERI: 직경 8.0 µm 이상 |
| BH | 범프 높이 편차 | 주요 | 편차 3.0 µm 이상 |
| PT | 파티클 | 경미 | 개수 3개 이상 또는 크기 20.0 µm 이상 |
- 불량 조건에 해당하지 않는 결함이 기록된 다이는 양품으로 본다.
- 임계값과 같은 값은 불량이다('이상'은 임계값 포함).
- 치명 불량 다이: BB 또는 TC로 불량 판정된 다이. 불량 다이: 등급과 관계없이 불량 판정된 모든 다이.

[p.2]
4. 재검사 및 측정 불가 처리
4.1 1차 검사에서 경계값 근처이거나 오검출이 의심되는 다이는 재검 전용 장비(AOI-R)로 재검사할 수 있다. 재검 결과는 같은 파일 끝에 '구분=재검' 행으로 추가된다.
4.2 같은 die_id에 '재검' 행이 있으면 그 다이는 재검 행의 결과로만 판정하고 1차 행은 무시한다(재검 결과로 대체). 다이 수는 die_id 기준으로 센다.
4.3 최종 결과가 NM(측정 불가)인 다이는 유효 샘플에서 제외한다. 1차 NM이라도 재검 행이 있으면 4.2에 따라 재검 결과를 따른다.
4.4 유효 샘플 다이 수 = 고유 die_id 수 − 최종 결과가 NM인 다이 수

5. 로트 판정 기준
불량 다이 비율(%) = 불량 다이 수 ÷ 유효 샘플 다이 수 × 100 (반올림하지 않고 기준과 비교)
아래 순서로 적용해 먼저 해당하는 판정 하나만 부여한다.
① SCRAP(폐기): 치명 불량 다이가 1개 이상
② RETEST(재검사): 유효 샘플 다이 수가 32개 미만 (샘플 재채취 후 재검사)
③ HOLD(출하 보류): 불량 다이 비율이 4.0% 초과
④ PASS(출하): ①~③에 해당하지 않음

6. 기준 적용 원칙
- 기준 개정은 품질보증팀 공지를 따르며, 시행일 해당 여부는 각 행의 '검사일'로 판단한다.
- 장비 교정 이상 기간의 측정값은 설비 교정 이력의 보정 규칙을 적용한 뒤 3장 기준과 비교한다.

[p.3]
7. 개정 이력
Rev.1 2024-02-15 최초 제정
Rev.2 2024-11-04 PT 개수 기준 신설
Rev.3 2025-06-20 BV 위치별 기준 분리(TSV/PERI)
Rev.4 2026-09-01 RETEST 기준(유효 샘플 32개) 신설, 재검 결과 대체 원칙 명확화
작성 품질보증팀 HBM품질파트 | 검토 품질보증팀장 | 승인 후공정 품질담당 임원"""

NOTE = """[p.1]
품질보증팀 공지 QA-N-2610-03
제목: HBM 후공정 불량 판정 기준 일부 개정 및 개정 예정 사항 안내
공지일 2026-10-05 | 수신 후공정 검사·품질 담당 | 발신 품질보증팀

1. 배경
고객사 HBM 신뢰성 평가에서 주변부(PERI) 범프 보이드 기인 불량이 보고되어 해당 기준을 강화한다. 추가 강화 항목은 고객사 협의 일정에 따라 순차 시행한다.

2. 개정 내용
| No | 항목 | 현행(Rev.4) | 변경 | 시행 | 상태 |
| 1 | BV(위치 PERI) 불량 기준 | 직경 8.0 µm 이상 | 직경 7.0 µm 이상 | 2026-10-08 검사분부터 | 시행 확정 |
| 2 | 로트 HOLD 기준 | 불량 다이 비율 4.0% 초과 | 3.0% 초과 | 2026-11-02 검사분부터 | 시행 예정 |
| 3 | TC 치명 기준 | 길이 4.0 µm 이상 | 길이 3.0 µm 이상 | 고객사 승인 후 별도 공지 | 미확정 |
| 4 | BV(위치 TSV) 불량 기준 | 직경 5.0 µm 이상 | 변경 없음 | - | 유지 |

3. 적용 원칙
- 시행일은 공지일이 아니라 각 검사 행의 '검사일'로 판단하며, 시행일 당일 검사분부터 변경 기준을 적용한다.
- 시행일 이전 검사분에는 소급 적용하지 않는다.
- '시행 예정'·'미확정' 항목은 시행일이 도래하거나 별도 공지가 나오기 전까지 적용하지 않고 현행 기준을 유지한다.
- 본 공지에 없는 사항은 기준서 Rev.4를 따른다.

[p.2]
4. 문의: 품질보증팀 HBM품질파트 (내선 4127)
※ 본 공지 내용은 기준서 Rev.5 정식 개정 시 통합한다."""

TABLE = "\n".join(f"| {l} | {m['day'].isoformat()} | {m['eq']} | {m['n']} | {m['qty']} |" for l, m in META.items())
CALDOC = f"""[p.1]
후공정 검사 설비 교정 이력 및 로트 대응표 (2026-10-01 ~ 10-16 검사분)
작성 설비기술팀 | 확인 품질보증팀

1. 검사 장비
| 장비 | 용도 | 측정 방식 |
| AOI-1, AOI-2, AOI-3 | 1차 검사 | BV·TC·PT 크기: 광학 / BH 편차: 레이저 높이 센서 |
| AOI-R | 재검 전용(고배율) | 위와 동일 |

2. 교정 이력 (광학 오프셋 허용 오차 ±1.0 µm)
| 장비 | 교정일 | 결과 | 조치 |
| AOI-1 | 2026-09-28 | 광학 오프셋 +0.2 µm (허용 이내) | 정상, 보정 없음 |
| AOI-2 | 2026-10-05 | 정상 | - |
| AOI-2 | 2026-10-10 | 광학 오프셋 +1.5 µm (허용 초과, 실제보다 크게 측정). 로그 분석 결과 10-06부터 이탈 | 10-10 첫 검사 전 재교정 완료, 이탈 기간 측정값 보정 |
| AOI-3 | 2026-10-12 | 광학 오프셋 −0.6 µm (허용 이내) | 정상, 보정 없음 |
| AOI-R | 2026-10-01 | 정상 | - |

3. 보정 규칙
- 대상: 장비가 AOI-2이고 검사일이 2026-10-06 ~ 2026-10-09(양 끝 날짜 포함)인 행의 BV·TC·PT 크기_um
- 방법: 기록된 크기에서 1.5 µm를 뺀 값으로 기준서 3장 기준과 비교한다. (예: 8.4 → 6.9)
- BH 편차는 레이저 높이 센서 값으로 광학 오프셋의 영향을 받지 않으므로 보정하지 않는다. 개수도 보정하지 않는다.
- 허용 오차 이내 오프셋(AOI-1, AOI-3)과 AOI-R 재검 행은 보정하지 않는다.

[p.2]
4. 로트 대응표 (1차 검사 기준)
| 로트 | 1차 검사일 | 1차 장비 | 샘플 다이 수 | 투입 수량(스택) |
{TABLE}
※ 샘플 다이 수는 고유 die_id 수이며 NM 다이를 포함한다. 투입 수량은 로트 전체 HBM 스택 수이다."""

files = [{"name": "01_HBM_불량판정기준서.pdf", "folder": DIR, "kind": "pdf", "tokens": tok(STD), "content": STD},
         {"name": "02_HBM_판정기준_개정공지.pdf", "folder": DIR, "kind": "pdf", "tokens": tok(NOTE), "content": NOTE},
         {"name": "03_HBM_설비교정_로트대응표.pdf", "folder": DIR, "kind": "pdf", "tokens": tok(CALDOC), "content": CALDOC}]
files += [{"name": f"{l}_검사결과.csv", "folder": SUB, "kind": "csv", "tokens": tok(t), "content": t} for l, t in CSV.items()]
DOC_T, LOT_T = sum(f["tokens"] for f in files[:3]), [f["tokens"] for f in files[3:]]
assert DOC_T <= 6000 and all(1500 <= t <= 2500 for t in LOT_T) and sum(LOT_T) >= 50000, (DOC_T, min(LOT_T), max(LOT_T), sum(LOT_T))
assert 24 <= len(CSV) <= 30 and all(30 <= len(r) <= 60 for r in ROWS.values())

summary = f"""ㅇㅇ반도체 HBM 후공정 품질보증팀 과장인 당신은 2026년 10월 1일~16일에 TSV·범프 외관 검사를 마친 {len(CSV)}개 로트의 판정을 확정해 내일 고객사 출하 회의에 보고해야 합니다.

- `01_HBM_불량판정기준서.pdf`는 결함 유형 코드와 유형별 다이 불량 판정 기준(크기·개수·위치), 재검사·측정 불가(NM) 처리, 로트 판정 규칙(SCRAP/RETEST/HOLD/PASS)이 정리된 사내 기준서(Rev.4)입니다.
- `02_HBM_판정기준_개정공지.pdf`는 일부 판정 기준의 개정 내용과 항목별 시행일·시행 상태를 안내하는 품질보증팀 공지입니다.
- `03_HBM_설비교정_로트대응표.pdf`는 검사 장비별 교정 이력과 측정값 보정 규칙, 로트별 1차 검사일·1차 장비·샘플 다이 수·투입 수량(스택)이 정리된 설비기술팀 자료입니다.
- `{SUB}` 폴더 안에는 로트별 검사 결과가 로트 1개당 CSV 1개씩 총 {len(CSV)}개 파일(`HB01_검사결과.csv` ~ `HB{len(CSV)}_검사결과.csv`)로 나뉘어 있습니다. 한 행은 다이 1개에 대한 검사 1회의 결과(die_id, 검사일, 장비, 구분, 결함코드, 크기, 개수, 위치)입니다.

모든 판정은 01~03 문서를 함께 반영해야 합니다. 주어진 자료를 보고 아래 질문에 답해주세요."""

lst_accept = lambda a: [a.replace("/", s) for s in ("/", "-", "·", "", " ")]
rt = lambda k: ", ".join(f"{l} {v['j']}" for l, v in run(**TRAPS[k]).items() if v["j"] != JUD[l])
hold_ex = ", ".join(f"{l}({len(v['bad'])}/{v['n']}={pct2(v['ratio'])}%)" for l, v in J.items() if v["j"] == "HOLD")
questions = [
 {"kind": "choice", "context": "내일 고객사 출하 회의를 앞두고 영업팀이 로트 HB09의 출하 가능 여부를 문의해 왔습니다.",
  "q": "[3-1] 01~03 문서를 모두 반영했을 때 로트 `HB09`의 최종 로트 판정과 그 근거로 옳은 것은? (비율은 % 단위 소수 첫째 자리까지 반올림해 표시)",
  "options": OPT1, "answer": a1,
  "explain": f"HB09(1차 10-08, AOI-1)는 개정 항목 1의 시행일 당일 검사분이라 PERI 보이드 기준 7.0 µm가 적용됩니다. HB09-017의 1차 BB는 재검(10-10, AOI-R)에서 결함 없음('-')으로 대체되어 치명 불량이 없고, NM 1개(HB09-025)를 뺀 유효 샘플 {h['ok']['n']}개 중 불량은 HB09-008(BV 7.3 PERI)·HB09-033(BV 7.6 PERI)·HB09-041(BV 5.4 TSV) 3개 → {pct2(h['ok']['ratio'])}% > 4.0% → HOLD. 함정: 재검 대체를 놓치면 SCRAP, 개정을 빠뜨리거나 시행일 당일을 제외하면 불량 1개로 PASS, NM을 분모에 넣으면 3/48로 비율이 달라집니다. RETEST는 유효 샘플 32개 미만일 때만 해당합니다."},
 {"kind": "short",
  "q": f"[3-2] `{SUB}` 폴더의 {len(CSV)}개 로트 전체에 01~03 문서를 모두 반영했을 때, 최종 로트 판정이 **HOLD**인 로트를 모두 입력하세요. (SCRAP·RETEST 판정 로트는 제외)\n\n로트 ID 오름차순, `/`로 구분해 입력합니다. (예: `HB02/HB15`)",
  "answer": a2, "accept": lst_accept(a2),
  "explain": f"최종 HOLD는 {hold_ex}입니다. HB27은 비율이 4.0%를 넘지만 유효 샘플이 31개(NM 4개 제외)라 RETEST가 우선이고, HB20은 2/50=4.00%로 '초과'가 아니라 PASS입니다. 함정별 오답 변화: 개정 미반영 시 {rt('개정 공지 미반영')} / 공지일(10-05)부터 적용 시 {rt('개정을 공지일(10-05)부터 적용')} / 시행 예정·미확정 항목 적용 시 {rt('시행 예정·미확정 항목 적용')} / 장비 보정 누락 시 {rt('장비 보정 누락')} / BH까지 보정 시 {rt('BH까지 보정')} / AOI-3 보정 시 {rt('AOI-3 허용 오차 이내 오프셋 보정')} / 재검 대체 누락 시 {rt('재검 대체 누락(1차 결과 사용)')} / NM 미제외 시 {rt('NM 유효 샘플 미제외')}."},
 {"kind": "short",
  "q": "[3-3] 03의 장비 보정 규칙을 적용해 판정한 결과와, 보정을 전혀 적용하지 않고(그 밖의 기준은 3-2와 동일하게 적용) 판정한 결과를 비교할 때 **최종 로트 판정이 달라지는 로트**를 모두 입력하세요.\n\n로트 ID 오름차순, `/`로 구분해 입력합니다. (예: `HB04/HB21`)",
  "answer": a3, "accept": lst_accept(a3),
  "explain": f"보정 대상은 1차 장비 AOI-2이면서 검사일이 10-06~10-09인 {'·'.join(CAL_LOTS)}입니다. HB10은 TC 4.9→3.4로 치명 기준 미달(보정 시 PASS, 미보정 시 SCRAP), HB12는 BV 9.0→7.5(10-07 검사라 PERI 8.0 기준)·BV 6.2→4.7(TSV)·PT 20.8→19.3으로 불량 0개(보정 시 PASS, 미보정 시 HOLD). HB14·HB16은 BH(보정 제외)와 보정 후에도 기준 이상인 BV가 남아 보정 전후 모두 HOLD입니다. 함정: 보정 대상 로트를 모두 적으면 {t3['보정 대상 로트 전부 기재']}, BH까지 보정하면 {t3['BH까지 보정']}, 기간 밖 AOI-2(10-05 HB08 등)까지 보정하면 {t3['AOI-2 전 기간 보정']}, 허용 오차 이내인 AOI-3까지 보정하면 {t3['AOI-3 허용 오차 이내 오프셋 보정']}, 개정 미반영 시 {t3['개정 공지 미반영']}."},
 {"kind": "short",
  "q": "[3-4] 01~03 문서를 모두 반영했을 때 최종 로트 판정이 **SCRAP**인 로트의 수와, 03 로트 대응표 기준 그 로트들의 투입 수량(스택) 합계를 `로트수/수량합계` 형식으로 입력하세요.\n\n숫자만, 쉼표 없이 입력합니다. (예: `2/1360`)",
  "answer": a4, "accept": [a4, a4.replace("/", "-"), a4.replace("/", "개/"), a4.replace("/", "개/") + "스택"],
  "explain": f"SCRAP은 HB05(BB), HB15(TC 4.4 µm, AOI-1이라 보정 없음), HB28(1차 BB, 재검에서도 BB 확인) 3개이고 투입 수량은 {'+'.join(str(META[l]['qty']) for l in S4)}={a4.split('/')[1]}입니다. HB09의 BB는 재검에서 해제, HB10의 TC 4.9는 보정 후 3.4, HB13(TC 3.6)·HB17(TC 3.5)은 4.0 미만입니다. 함정: 재검 대체 누락 {t4['재검 대체 누락(1차 결과 사용)']}, 보정 누락 {t4['장비 보정 누락']}, 미확정 TC 3.0 기준 적용 {t4['시행 예정·미확정 항목 적용']}, AOI-3 보정 {t4['AOI-3 허용 오차 이내 오프셋 보정']}, TC 치명 누락 {t4['TC를 치명에서 누락']}."},
]
part = {"title": "HBM 후공정 불량 판별", "summary": summary, "files": files, "questions": questions}
blind = {**part, "questions": [{k: v for k, v in q.items() if k not in ("answer", "accept", "explain")} for q in questions]}
for n, d in (("part.json", part), ("blind.json", blind)):
    with open(os.path.join(HERE, n), "w", encoding="utf-8") as f:
        json.dump(d, f, ensure_ascii=False, indent=1)

print("판정", JUD)
print("Q1", a1, OPT1[a1 - 1], "| Q2", a2, "| Q3", a3, "| Q4", a4)
print("traps2", t2)
print("traps3", t3)
print("traps4", t4)
print("files", len(files), "docs", DOC_T, "lots", min(LOT_T), max(LOT_T), sum(LOT_T), "total", DOC_T + sum(LOT_T))
