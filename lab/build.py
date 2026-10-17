"""연습실 페이지 빌드: lab/src + lab/problems → 저장소 루트 index.html"""
import json
from pathlib import Path

LAB = Path(__file__).parent
ROOT = LAB.parent
P = LAB / "problems"


def load(path):
    return json.loads(path.read_text(encoding="utf-8"))


problems = [
    load(P / "snack/problem.json"),
    load(P / "fai/problem.json"),
    load(P / "globalcart/problem.json"),
    load(P / "expense/problem.json"),
    {**load(P / "hbm/problem.json"), "type": "essay"},
]
for s in load(P / "literacy/sets.json"):
    problems.append({
        "id": "lit-" + s["key"].lower(), "group": "AI 리터러시 문제집", "type": "mcq",
        "title": f"세트 {s['key']} · {s['title']}", "badge": f"객관식 {len(s['questions'])}문항", "timeLimitMin": 15,
        "aiLimit": {"count": 10, "chars": 1000}, "pii": [], "files": [], "notices": [],
        "lead": "다음 지문을 읽고 물음에 답하세요.",
        "passage": f"AI 활용·보안·규제 지식을 묻는 시나리오형 객관식입니다. 문항마다 업무 상황을 읽고 가장 적절한 답을 고르세요. (주제: {s['title']})",
        "questions": [{"kind": "choice", **{k: q[k] for k in ("context", "q", "options", "answer", "explain")}} for q in s["questions"]],
    })

M = P / "mock1"
GROUP = "실전 모의고사 (10/18 대비)"
READY = all((M / f).exists() for f in ("theory/theory.json", *(f"p{i}/part.json" for i in range(1, 5))))
if READY: problems.append({
    "id": "mock1-theory", "group": GROUP, "type": "mcq", "title": "1회 · 1교시 이론", "badge": "객관식 20문항", "timeLimitMin": 30,
    "aiLimit": {"count": 0, "chars": 1000}, "pii": [], "files": [],
    "lead": "다음 지문을 읽고 물음에 답하세요.",
    "passage": "기업 환경에서 AI를 안전하고 효율적으로 쓰는 판단력을 묻는 객관식입니다. 지식보다 **지문을 빨리 정확히 읽는 것**이 관건입니다(문항당 약 90초).\n\n- 조합형: ㄱ~ㄹ 진술 중 옳은 것만 고르기\n- 빈칸형: (A)(B)(C)에 들어갈 말의 짝 고르기\n- 상황판단형·순서형",
    "notices": ["AI 없이 풉니다.", "모든 회사·인물·수치는 가상입니다.", "모르는 문항은 표시(⚑)하고 넘어간 뒤 마지막에 돌아오세요."],
    "questions": [{"kind": "choice", **{k: q[k] for k in ("context", "q", "options", "answer", "explain")}} for q in load(M / "theory/theory.json")["questions"]],
})
parts = [load(M / f"p{i}/part.json") for i in range(1, 5)] if READY else []
if READY: problems.append({
    "id": "mock1-practice", "group": GROUP, "type": "mcq", "title": "1회 · 2교시 실기", "badge": f"4문제 · {sum(len(x['questions']) for x in parts)}문항", "timeLimitMin": 90,
    "aiLimit": {"count": 40, "chars": 1000, "cooldownSec": 30}, "liteDefault": True, "pii": [],
    "lead": "자료를 보고 문제 1~4의 소문항에 답하세요.",
    "passage": "실제 시험처럼 **경량(구형) 모델**이 기본이고, 질문은 **30초 간격**으로만 보낼 수 있으며 매 질문은 새 대화입니다. 첨부 한도를 넘기면 보낼 수 없고, 한도 가까이 채우면 모델이 틀리기 쉽습니다. 작게 나눠 묻고, 중간 결과는 메모장에 표로 저장해 다음 질문에 붙여 넣으세요.\n\n"
        + "\n\n".join(f"### 문제 {i}. {x['title']}\n{x['summary']}" for i, x in enumerate(parts, 1)),
    "notices": ["AI 질문은 문제 1~4 합계 40회(문제당 약 10회 가정), 1회 1,000자 이내입니다.", "모든 회사·인물·수치는 가상입니다.", "시간 배분: 문제당 약 20분, 막히면 다음 문제로 넘어가세요."],
    "files": [f for x in parts for f in x["files"]],
    "questions": [q for x in parts for q in x["questions"]],
})

data = json.dumps(problems, ensure_ascii=False).replace("</", "<\\/")
head = (LAB / "src/head.html").read_text(encoding="utf-8")
body = (LAB / "src/body.html").read_text(encoding="utf-8").replace("__PROBLEMS__", data)
html = f"""<!doctype html>
<html lang="ko">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1,viewport-fit=cover">
<style>:root{{color-scheme:light}}body{{margin:0}}img{{max-width:100%}}[hidden]{{display:none!important}}</style>
{head}
</head>
<body>
{body}
</body>
</html>
"""
(ROOT / "index.html").write_text(html, encoding="utf-8")
print(f"index.html {len(html):,}자, 문제 {len(problems)}개")
