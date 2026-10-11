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
    {**load(P / "hbm/problem.json"), "type": "essay"},
]
for s in load(P / "literacy/sets.json"):
    problems.append({
        "id": "lit-" + s["key"].lower(), "group": "AI 리터러시 문제집", "type": "mcq",
        "title": f"세트 {s['key']} · {s['title']}", "badge": "객관식 10문항", "timeLimitMin": 15,
        "aiLimit": {"count": 10, "chars": 1000}, "pii": [], "files": [], "notices": [],
        "lead": "다음 지문을 읽고 물음에 답하세요.",
        "passage": f"AI 활용·보안·규제 지식을 묻는 시나리오형 객관식입니다. 문항마다 업무 상황을 읽고 가장 적절한 답을 고르세요. (주제: {s['title']})",
        "questions": [{"kind": "choice", **{k: q[k] for k in ("context", "q", "options", "answer", "explain")}} for q in s["questions"]],
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
