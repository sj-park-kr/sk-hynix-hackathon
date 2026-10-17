import json, os, random
from decimal import Decimal, ROUND_HALF_UP
from fractions import Fraction as F

HERE = os.path.dirname(os.path.abspath(__file__))
R = random.Random(20261018)
NR, NC = 16, 12
WAFERS = ["W01", "W02", "W03"]
SPLIT = {"W01": 2, "W02": 3, "W03": 3}
FAIL, GOOD = set("357"), set("12")
IN = {(r, c) for r in range(1, NR + 1) for c in range(1, NC + 1) if ((r - 8.5) / 8.4) ** 2 + ((c - 6.5) / 6.4) ** 2 <= 1}


def cid(p): return f"R{p[0]:02d}C{p[1]:02d}"
def pos(s): return int(s[1:3]), int(s[4:6])
def nb4(p): r, c = p; return [(r - 1, c), (r + 1, c), (r, c - 1), (r, c + 1)]
def nb8(p): r, c = p; return [(r + a, c + b) for a in (-1, 0, 1) for b in (-1, 0, 1) if a or b]


EDGE = {p for p in IN if any(q not in IN for q in nb4(p))}
RING = {p for p in IN if p[0] in (1, NR) or p[1] in (1, NC)}  # 함정: 격자 테두리만 edge로 보는 해석

# ---------- 웨이퍼 맵: 의도적 배치 ----------
PLANT = {
 "W01": {"R07C08": "3", "R08C08": "3", "R09C08": "5", "R09C09": "3",   # R08|R09 블록 경계를 가로지르는 4다이 클러스터
         "R09C04": "2", "R08C04": "7",                                  # 1-1 판독 좌표(+ 한 행 위 함정)
         "R04C09": "3", "R11C06": "5", "R14C05": "7",                   # 내부 반복 불량
         "R01C06": "3", "R12C12": "5",                                  # edge 반복 불량
         "R10C10": "9", "R12C08": "2"},                                 # bin 9 / bin 2 함정
 "W02": {"R05C05": "3", "R06C04": "3", "R06C05": "3", "R06C06": "7", "R07C05": "3", "R07C06": "3", "R08C06": "5",  # 최대 클러스터(R06|R07 경계)
         "R09C07": "3", "R10C07": "3", "R10C08": "7",                   # 대각선으로만 붙은 3다이
         "R10C03": "7", "R11C02": "7", "R11C03": "7", "R12C03": "7", "R12C04": "3",  # 한 블록 안의 5다이 클러스터
         "R13C09": "5", "R12C09": "3",                                  # 1-1 판독 좌표(+ 한 행 위 함정)
         "R04C09": "3", "R14C05": "3", "R01C06": "3", "R03C02": "7", "R10C10": "3"},
 "W03": {"R04C09": "3", "R11C06": "7", "R06C04": "7", "R01C06": "3", "R03C02": "7", "R12C12": "3", "R12C08": "7",
         "R12C07": "9", "R13C07": "2",                                  # 1-1 판독 좌표(+ 한 행 아래 함정)
         "R02C03": "7", "R02C10": "3", "R03C11": "7", "R04C11": "3", "R14C02": "5", "R15C03": "7", "R15C10": "3", "R14C11": "7"},
}
BG = {"W01": [("2", 3), ("3", 3), ("5", 2), ("7", 2), ("9", 1)],
      "W02": [("2", 11), ("3", 2), ("5", 1), ("7", 1), ("9", 2)],
      "W03": [("2", 2), ("3", 6), ("5", 3), ("7", 3), ("9", 2)]}
G = {w: {p: ("1" if p in IN else "·") for p in [(r, c) for r in range(1, NR + 1) for c in range(1, NC + 1)]} for w in WAFERS}
for w in WAFERS:
    for k, v in PLANT[w].items():
        assert pos(k) in IN, k
        G[w][pos(k)] = v
for w in WAFERS:  # 배경: 서로·계획 셀과 8방향으로 떨어진 단독 셀, 다른 웨이퍼 불량 좌표와 겹치지 않음
    pool = sorted(IN)
    for b, n in BG[w]:
        k = 0
        while k < n:
            p = R.choice(pool)
            if G[w][p] != "1" or any(G[w].get(q, "·") not in "1·" for q in nb8(p)): continue
            if b in FAIL and any(G[o][p] in FAIL for o in WAFERS if o != w): continue
            G[w][p] = b; k += 1


# ---------- 규칙 엔진 ----------
def cutrows(w):
    per = -(-NR // SPLIT[w]); return {per * i for i in range(1, SPLIT[w])}


def comps(w, fails=FAIL, conn=4, cut=False):
    cells = {p for p in IN if G[w][p] in fails}
    cr, seen, out = cutrows(w) if cut else set(), set(), []
    for p in sorted(cells):
        if p in seen: continue
        st, comp = [p], []; seen.add(p)
        while st:
            q = st.pop(); comp.append(q)
            for n in (nb8 if conn == 8 else nb4)(q):
                if n in cells and n not in seen and not (q[0] != n[0] and min(q[0], n[0]) in cr):
                    seen.add(n); st.append(n)
        out.append(sorted(comp))
    return sorted(out, key=lambda c: (-len(c), c))


def pct(x): return (Decimal(x.numerator * 100) / Decimal(x.denominator)).quantize(Decimal("0.1"), ROUND_HALF_UP)


def analyze(w, conn=4, edge=EDGE, fails=FAIL, excl9=True, cut=False):
    g = G[w]; good = set("1") if "2" in fails else GOOD
    meas = [p for p in IN if not (excl9 and g[p] == "9")]
    yx = F(sum(g[p] in good for p in meas), len(meas))
    cl = [c for c in comps(w, fails, conn, cut) if len(c) >= 4]
    rate = lambda S: F(sum(g[p] in fails for p in S), len(S))
    em, im = [p for p in meas if p in edge], [p for p in meas if p not in edge]
    er, ir = rate(em), rate(im)
    y = pct(yx)
    judge = "HOLD" if y < 80 or any(len(c) >= 8 for c in cl) else "REVIEW" if cl or er >= 2 * ir else "PASS"
    return dict(y=y, yx=yx, cl=cl, er=er, ir=ir, edge_ok=er >= 2 * ir, judge=judge, ne=len(em), ni=len(im),
                fe=sum(g[p] in fails for p in em), fi=sum(g[p] in fails for p in im))


def repeaters(edge=EDGE, fails=FAIL, need=2, drop_edge=True):
    return [cid(p) for p in sorted(IN) if sum(G[w][p] in fails for w in WAFERS) >= need and not (drop_edge and p in edge)]


def box(c): return f"{len(c)}/{cid((min(p[0] for p in c), min(p[1] for p in c)))}/{cid((max(p[0] for p in c), max(p[1] for p in c)))}"


# ---------- 1-1 좌표 판독 ----------
Q1 = [("W01", "R09C04"), ("W02", "R13C09"), ("W03", "R12C07")]
a1 = "-".join(G[w][pos(s)] for w, s in Q1)
mis1 = set()
for i, (w, s) in enumerate(Q1):
    r, c = pos(s); per = -(-NR // SPLIT[w]); o = (r - 1) % per
    alt = [(r - 1, c), (r + 1, c), (r, c - 1), (r, c + 1)] + [(b * per + o + 1, c) for b in range(SPLIT[w]) if b * per + o + 1 not in (r,) and b * per + o + 1 <= NR]
    for q in alt:
        v = G[w].get(q, "·"); assert v != G[w][(r, c)], (w, s, q)
        mis1.add("-".join(v if j == i else G[x][pos(t)] for j, (x, t) in enumerate(Q1)))
assert a1 == "2-5-9" and a1 not in mis1 and {"7-5-9", "2-3-9", "2-5-2"} <= mis1

# ---------- 1-2 W02 최대 클러스터 ----------
c2 = comps("W02"); a2 = box(c2[0])
t2_diag = box(comps("W02", conn=8)[0])
t2_cut = box(comps("W02", cut=True)[0])
t2_with2 = box(comps("W02", fails=FAIL | {"2"})[0])
t2_with9 = box(comps("W02", fails=FAIL | {"9"})[0])
assert a2 == "7/R05C04/R08C06" and len(c2[0]) > len(c2[1]) >= 4
assert t2_diag == "10/R05C04/R10C08" and t2_cut == "5/R10C02/R12C04"
assert len({a2, t2_diag, t2_cut}) == 3

# ---------- 1-3 내부 반복 불량 좌표 ----------
a3 = "-".join(repeaters())
t3 = {"edge 포함": repeaters(drop_edge=False), "테두리만 edge": repeaters(edge=RING), "3장 모두": repeaters(need=3),
      "bin 9 불량 취급": repeaters(fails=FAIL | {"9"}), "bin 2 불량 취급": repeaters(fails=FAIL | {"2"})}
assert a3 == "R04C09-R06C04-R11C06-R14C05", a3
for k, v in t3.items(): assert "-".join(v) != a3, k
assert "-".join(t3["edge 포함"]) == "R01C06-R03C02-R04C09-R06C04-R11C06-R12C12-R14C05" and "-".join(t3["테두리만 edge"]) == "R03C02-" + a3

# ---------- 1-4 판정 (ㄱㄴㄷㄹ) ----------
OPTS = ["ㄱ, ㄴ", "ㄴ, ㄷ", "ㄷ, ㄹ", "ㄱ, ㄷ, ㄹ", "ㄴ, ㄷ, ㄹ"]


def truth(**kw):
    A = {w: analyze(w, **kw) for w in WAFERS}
    low = min(WAFERS, key=lambda w: A[w]["yx"])
    assert sorted(A[w]["yx"] for w in WAFERS)[0] != sorted(A[w]["yx"] for w in WAFERS)[1]
    t = {"ㄱ": A["W01"]["judge"] == "PASS", "ㄴ": A["W02"]["judge"] == "HOLD",
         "ㄷ": A["W03"]["judge"] == "REVIEW" and not A["W03"]["cl"], "ㄹ": low == "W03"}
    s = ", ".join(k for k in "ㄱㄴㄷㄹ" if t[k])
    return A, s, (OPTS.index(s) + 1 if s in OPTS else None)


A, s4, a4 = truth()
assert s4 == "ㄷ, ㄹ" and a4 == 3
assert [A[w]["judge"] for w in WAFERS] == ["REVIEW", "REVIEW", "REVIEW"]
assert A["W01"]["cl"] and len(A["W01"]["cl"][0]) == 4 and not A["W01"]["edge_ok"] and A["W01"]["y"] >= 80
assert A["W02"]["y"] >= 80 and A["W03"]["y"] >= 80 and A["W03"]["edge_ok"] and not A["W03"]["cl"]
T4 = {"블록 경계에서 끊어 읽음": truth(cut=True), "대각선 연결 포함": truth(conn=8), "bin 2 불량 취급": truth(fails=FAIL | {"2"}),
      "테두리만 edge": truth(edge=RING)}
assert T4["블록 경계에서 끊어 읽음"][2] == 4 and T4["대각선 연결 포함"][2] == 5
for k, v in T4.items(): assert v[2] != a4, k
assert T4["bin 2 불량 취급"][0]["W02"]["judge"] == "HOLD" and not T4["테두리만 edge"][0]["W03"]["edge_ok"]

# ---------- 파일 ----------
COLS = ["행"] + [f"C{c:02d}" for c in range(1, NC + 1)]
TOK = {"W01": 3120, "W02": 3380, "W03": 2960}
LOT = "QA2610-17"
files = []
STD = f"""[p.1]
ㅇㅇ반도체 M2팹 품질보증팀 | 사내 기준서 QA-STD-0412 (Rev.3) | 시행일 2026-09-01 | 보안 등급: 사내 한정
웨이퍼 맵 판독 및 웨이퍼 판정 기준서

1. 목적
본 기준서는 프로브 테스트와 외관 검사(AVI) 통합 결과를 웨이퍼 맵으로 판독하고, 웨이퍼 단위 출하 판정을 표준화하기 위해 작성되었다. 판정 결과는 주간 출하 판정 회의 자료의 근거로 사용한다.

2. 웨이퍼 맵 구성
- 웨이퍼 맵 1장은 16행(R01~R16) × 12열(C01~C12) 격자다. 행 번호는 위에서 아래로, 열 번호는 왼쪽에서 오른쪽으로 증가한다.
- 좌표는 'R + 행 번호 2자리 + C + 열 번호 2자리'로 표기한다. 예) R05C11 = 5행 11열의 다이.
- 출력물은 지면 제약으로 표를 행 방향으로 2~3개 블록으로 나누어 좌우로 이어 붙여 인쇄할 수 있다. 이때 각 줄의 행 번호는 그 블록 첫 열(행)에 인쇄된 값이며, 모든 블록의 열 체계(C01~C12)는 같다.
- 동일 Lot의 웨이퍼는 같은 마스크를 사용하므로 웨이퍼 밖('·') 위치는 모든 웨이퍼에서 동일하다.

3. bin 코드 정의
코드 | 구분 | 내용 | 집계 분류
1 | 양품 | 전 항목 Pass (정격 속도) | 양품
2 | 양품(하위 등급) | 기능 Pass, 속도 등급 하향 | 양품
3 | 전기 불량 | Open/Short, 기능 Fail | 불량
5 | 파라메트릭 불량 | 누설전류·Vth 규격 초과 | 불량
7 | 외관 불량 | AVI 스크래치·파티클 | 불량
9 | 미측정 | 프로브 접촉 불량으로 측정값 없음(재측정 대상) | 집계 제외
· | 웨이퍼 밖 | 다이 없음 | 다이 아님
※ bin 2는 출하 가능한 양품이며 불량으로 집계하지 않는다.
※ bin 9는 양품도 불량도 아니다. 모든 비율 계산의 분자·분모에서 제외한다.

[p.2]
4. 용어 정의
4.1 유효 다이: '·'이 아닌 모든 셀. 측정 다이: 유효 다이 중 bin 9를 제외한 다이.
4.2 불량 다이: bin 3·5·7 다이(불량 유형 무관).
4.3 수율(%) = 양품 다이 수(bin 1·2) ÷ 측정 다이 수 × 100. 소수 둘째 자리에서 반올림하여 소수 첫째 자리까지 산출한다.
4.4 클러스터: 불량 다이가 상·하·좌·우로 맞닿아 이어진 집합 중 다이 수가 4개 이상인 것. 대각선으로만 맞닿은 다이는 연결된 것으로 보지 않으며, bin 1·2·9 다이는 연결을 끊는다.
4.5 가장자리(edge) 다이: 유효 다이 중 상·하·좌·우 이웃 4칸 가운데 하나 이상이 '·'이거나 격자 밖인 다이. 대각선 이웃은 고려하지 않는다. 유효 다이 중 edge 다이가 아닌 다이를 내부 다이라 한다.
4.6 edge 불량률 = edge 측정 다이 중 불량 다이 수 ÷ edge 측정 다이 수. 내부 불량률 = 내부 측정 다이 중 불량 다이 수 ÷ 내부 측정 다이 수.
4.7 반복 불량 좌표: 분석 대상 웨이퍼(W01~W03) 중 2장 이상에서 불량 다이인 좌표. 웨이퍼별 불량 유형(3·5·7)은 달라도 된다.

5. 웨이퍼 판정 기준
아래 순서대로 적용하며, 먼저 해당하는 판정 하나만 부여한다.
① HOLD(출하 보류): 수율 80.0% 미만이거나, 다이 수 8개 이상인 클러스터가 1개 이상 있는 경우
② REVIEW(엔지니어 검토): ①에 해당하지 않으면서 다음 중 하나 이상에 해당하는 경우
   (a) 클러스터가 1개 이상 있음
   (b) edge 불량률 ≥ 내부 불량률 × 2 (두 비율은 반올림하지 않고 비교)
③ PASS(출하): ①, ②에 해당하지 않는 경우

6. 보고 양식
- 좌표 목록은 행 번호 오름차순, 같은 행이면 열 번호 오름차순으로 적는다.
- 판정 근거에는 해당 조항 번호(예: 5-②(b))를 함께 적는다.

[p.3]
7. 개정 이력
Rev.1 2025-03-02 최초 제정
Rev.2 2025-11-14 bin 2(하위 속도 등급) 양품 집계 명확화
Rev.3 2026-09-01 클러스터 기준을 '대각선 미포함, 4개 이상'으로 변경, HOLD 기준 수율 80.0%로 조정
작성 품질보증팀 웨이퍼품질파트 | 검토 품질보증팀장 | 승인 M2팹 품질담당 임원"""
files.append({"name": "01_웨이퍼맵_판독기준서.pdf", "folder": "1_웨이퍼맵", "kind": "pdf", "tokens": 2140, "content": STD})
for k, w in enumerate(WAFERS, 2):
    rows = [[f"R{r:02d}"] + [G[w][(r, c)] for c in range(1, NC + 1)] for r in range(1, NR + 1)]
    files.append({"name": f"0{k}_{w}_웨이퍼맵.pdf", "folder": "1_웨이퍼맵", "kind": "image", "tokens": TOK[w],
                  "image": {"title": f"Lot {LOT} · {w} 웨이퍼 맵 (다이 판정 bin)",
                            "subtitle": f"ㅇㅇ반도체 M2팹 · 프로브/AVI 통합 결과 · 16행 × 12열 · 출력 2026-10-16 · 표 분할 인쇄",
                            "columns": COLS, "rows": rows, "split": SPLIT[w]},
                  "content": "\n".join(",".join(x) for x in [COLS] + rows)})

summary = f"""ㅇㅇ반도체 M2팹 품질보증팀 과장인 당신은 Lot `{LOT}`의 웨이퍼 3장(W01~W03) 검사 결과를 판독해 내일 출하 판정 회의 자료를 준비해야 합니다.

- `01_웨이퍼맵_판독기준서.pdf`는 bin 코드 정의, 좌표 표기 규칙, 클러스터·가장자리(edge) 다이·반복 불량 좌표의 정의, 수율 계산식과 웨이퍼 판정 기준(HOLD/REVIEW/PASS)이 정리된 사내 기준 문서입니다.
- `02_W01_웨이퍼맵.pdf`, `03_W02_웨이퍼맵.pdf`, `04_W03_웨이퍼맵.pdf`는 웨이퍼별 다이 판정 결과(16행 × 12열, 셀 값은 bin 코드)를 표로 출력한 스캔 이미지입니다. 지면 제약으로 표가 행 방향으로 여러 블록으로 잘려 좌우로 붙어 있으며, 웨이퍼마다 분할 블록 수가 다를 수 있습니다.

모든 계산과 판정은 판독기준서를 따릅니다. 주어진 자료를 보고 아래 질문에 답해주세요."""


def ex_judge(w):
    a = A[w]; cl = ", ".join(f"{len(c)}다이" for c in a["cl"]) or "없음"
    return (f"{w}: 수율 {a['y']}%, 클러스터 {cl}, edge 불량률 {a['fe']}/{a['ne']} vs 내부 불량률 {a['fi']}/{a['ni']}"
            f"({'2배 이상' if a['edge_ok'] else '2배 미만'}) → {a['judge']}")


Y = {w: A[w]["y"] for w in WAFERS}
questions = [
 {"kind": "short",
  "q": "[1-1] 웨이퍼 맵 이미지에서 다음 세 좌표의 bin 코드를 읽어 순서대로 `-`로 연결해 입력하세요.\n\n① W01의 `R09C04` ② W02의 `R13C09` ③ W03의 `R12C07`\n\n(bin 코드 숫자만 입력. 예: `1-3-7`)",
  "answer": a1, "accept": [a1, a1.replace("-", "/"), a1.replace("-", "")],
  "explain": f"각 블록 첫 열의 행 번호로 위치를 찾아야 합니다. W01은 2블록(R01~R08 | R09~R16)이라 R09는 오른쪽 블록 첫 줄, W02·W03은 3블록(R01~R06 | R07~R12 | R13~R16)이라 R13은 오른쪽 블록 첫 줄, R12는 가운데 블록 마지막 줄입니다. 정답 {a1}. 한 행만 밀려 읽으면 W01 R08C04=7, W02 R12C09=3, W03 R13C07=2가 섞여 `7-5-9`, `2-3-9`, `2-5-2` 같은 오답이 나옵니다."},
 {"kind": "short",
  "q": "[1-2] W02에서 판독기준서 4.4의 '클러스터' 중 다이 수가 가장 많은 클러스터의 다이 수와, 그 클러스터를 둘러싸는 최소 직사각형의 좌상단 좌표(최소 행·최소 열)와 우하단 좌표(최대 행·최대 열)를 `다이수/좌상단/우하단` 형식으로 입력하세요. (예: `6/R03C02/R05C04`)",
  "answer": a2, "accept": [a2, a2.replace("/", "-"), "7/R05C04-R08C06", "7/R05C04~R08C06", "7개/R05C04/R08C06"],
  "explain": f"W02의 최대 클러스터는 {', '.join(cid(p) for p in c2[0])}의 7다이(상하좌우 연결)로 범위 R05C04~R08C06입니다. 이 클러스터는 R06|R07 블록 경계에 걸쳐 이미지에서는 왼쪽 블록 아래(4다이)와 가운데 블록 위(3다이)로 갈라져 보입니다. 경계에서 끊어 읽으면 한 블록 안의 5다이 클러스터({t2_cut})를 최대로 오판하고, R09C07·R10C07·R10C08(R08C06과 대각선으로만 접함)을 연결로 보면 {t2_diag}가 됩니다(4.4 대각선 미포함)."},
 {"kind": "short",
  "q": "[1-3] 판독기준서 4.7의 '반복 불량 좌표' 중 4.5의 가장자리(edge) 다이에 해당하는 좌표를 제외한 나머지 좌표를 모두 입력하세요. 행 번호 오름차순(같은 행이면 열 번호 오름차순)으로 정렬해 `-`로 연결합니다. (예: `R02C05-R07C11`)",
  "answer": a3, "accept": [a3, a3.replace("-", "/"), a3.replace("-", "")],
  "explain": f"2장 이상 불량(bin 3·5·7)인 좌표는 {', '.join(t3['edge 포함'])}입니다. 이 중 R01C06·R12C12(격자 테두리)와 R03C02(왼쪽 이웃 R03C01이 '·')는 edge 다이라 제외 → {a3}. 함정: 격자 테두리만 edge로 보면 R03C02가 남고, bin 9(미측정, 집계 제외)를 불량으로 보면 {"·".join(sorted(set(t3["bin 9 불량 취급"]) - set(repeaters())))}이 추가되며, 3장 모두 불량인 좌표만 고르면 R04C09 하나만 남습니다. R06C04는 W02 최대 클러스터의 일부(3)이자 W03의 외관 불량(7)입니다."},
 {"kind": "choice",
  "context": "내일 출하 판정 회의에서 품질보증팀이 보고할 웨이퍼별 판정 결과를 최종 검토하고 있습니다.",
  "q": "[1-4] 판독기준서 5장의 웨이퍼 판정 기준을 W01~W03에 적용했을 때, 다음 보기 중 옳은 것만을 모두 고른 것은?\n\nㄱ. W01의 판정은 PASS이다.\nㄴ. W02의 판정은 HOLD이다.\nㄷ. W03의 판정은 REVIEW이며, 5-②(a) 클러스터 조건에는 해당하지 않는다.\nㄹ. W01~W03 중 수율(4.3)이 가장 낮은 웨이퍼는 W03이다.",
  "options": OPTS, "answer": a4,
  "explain": " / ".join(ex_judge(w) for w in WAFERS) + f". 따라서 ㄷ·ㄹ만 옳습니다. ㄱ: W01의 R07C08·R08C08·R09C08·R09C09는 R08|R09 블록 경계에 걸친 4다이 클러스터라 REVIEW(경계에서 끊어 읽으면 PASS로 오판 → ④). ㄴ: W02 최대 클러스터는 7다이로 8개 미만이고 수율 {Y['W02']}%로 HOLD가 아님(대각선까지 연결하면 10다이 HOLD로 오판 → ⑤, bin 2를 불량으로 보면 W02 수율이 80% 미만으로 떨어져 HOLD로 오판 → ②). ㄷ: W03는 원호 모양 가장자리 불량이 많아 edge 불량률이 내부의 2배 이상(격자 테두리만 edge로 보면 2배 미만으로 오판). ㄹ: 수율 W01 {Y['W01']}% > W02 {Y['W02']}% > W03 {Y['W03']}%."},
]
part = {"title": "웨이퍼 맵 판독과 출하 판정", "summary": summary, "files": files, "questions": questions}
blind = {**part, "questions": [{k: v for k, v in q.items() if k not in ("answer", "accept", "explain")} for q in questions]}
for n, d in (("part.json", part), ("blind.json", blind)):
    with open(os.path.join(HERE, n), "w", encoding="utf-8") as f: json.dump(d, f, ensure_ascii=False, indent=1)

for w in WAFERS:
    print(w, SPLIT[w], A[w]["y"], A[w]["judge"], [len(c) for c in A[w]["cl"]], f"edge {A[w]['fe']}/{A[w]['ne']} in {A[w]['fi']}/{A[w]['ni']}")
    for r in range(1, NR + 1): print("  ", f"R{r:02d}", " ".join(G[w][(r, c)] for c in range(1, NC + 1)))
print("Q1", a1, "Q2", a2, "Q3", a3, "Q4", a4, s4)
print("traps", t2_diag, t2_cut, t2_with2, t2_with9, {k: "-".join(v) for k, v in t3.items()}, {k: (v[1], v[2]) for k, v in T4.items()})
print("files", len(files), "tokens", sum(f["tokens"] for f in files))
