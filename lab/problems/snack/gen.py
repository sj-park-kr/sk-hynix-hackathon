import json, random
from collections import Counter
from datetime import datetime, timedelta

roster = [  # 이름, 학과, 학번
 ("김민지","경영학과",24),("박서준","컴퓨터공학과",23),("장하늘","심리학과",25),("정하늘","경제학과",24),
 ("신우주","기계공학과",25),("최준호","경영학과",23),("이지은","국어국문학과",24),("송구름","시각디자인학과",25),
 ("한빛나","경영학과",26),("강태양","컴퓨터공학과",24),("임바다","기계공학과",23),("오한별","심리학과",24),
 ("윤솔","경제학과",25),("서지호","경영학과",25),("문가람","국어국문학과",23),("배하린","시각디자인학과",24),
 ("조은결","컴퓨터공학과",25),("권나래","경영학과",24),("류시온","기계공학과",26),("남도윤","경제학과",23),
 ("황보람","심리학과",26),("안세린","국어국문학과",25),("전우진","컴퓨터공학과",26),("고은비","시각디자인학과",23),
 ("유하람","경영학과",25),("노을","경제학과",26),
]
# 사람별 신청 순서(마지막이 유효). 류시온(26학번)은 미신청. 홍길동은 부원 아님.
orders = {
 "김민지":["햄버거","햄버거","토스트","햄버거"],
 "박서준":["부리또","떡볶이"],
 "장하늘":["부리또","토스트","컵라면"],
 "정하늘":["컵라면","떡볶이"],
 "신우주":["컵라면","햄버거"],
 "최준호":["토스트","토스트","부리또"],
 "이지은":["햄버거","토스트"],
 "송구름":["떡볶이","햄버거"],
 "한빛나":["햄버거"],
 "강태양":["떡볶이"],
 "임바다":["부리또","햄버거"],
 "오한별":["햄버거"],
 "윤솔":["햄버거","토스트"],
 "서지호":["토스트","토스트"],
 "문가람":["부리또"],
 "배하린":["떡볶이","부리또"],
 "조은결":["햄버거","컵라면"],
 "권나래":["토스트","떡볶이"],
 "남도윤":["부리또","햄버거"],
 "황보람":["컵라면"],
 "안세린":["햄버거","떡볶이","부리또"],
 "전우진":["떡볶이","햄버거"],
 "고은비":["햄버거"],
 "유하람":["토스트","떡볶이","햄버거"],
 "노을":["부리또"],
 "홍길동":["햄버거"],
}
assert sum(map(len,orders.values()))==50, sum(map(len,orders.values()))
# 시간 배치: 각 사람의 주문 순서를 지키며 결정적으로 섞기
rnd = random.Random(7)
queue = {k:list(v) for k,v in orders.items()}
seq = []
while any(queue.values()):
    k = rnd.choice([k for k,v in queue.items() if v])
    seq.append((k, queue[k].pop(0)))
# 장하늘 마지막(컵라면)은 3일차로 보내 함정 강화 — 이미 순서 보장됨
t = datetime(2026,4,3,13,5)
rows = []
for i,(name,menu) in enumerate(seq):
    t += timedelta(minutes=rnd.randint(4,47))
    if t.hour >= 22: t = t.replace(hour=9, minute=rnd.randint(0,30)) + timedelta(days=1)
    rows.append((t.strftime("%Y-%m-%d %H:%M"), name, menu))
# 정답 계산
last = {}
for ts,n,m in rows: last[n] = m
dept = {n:d for n,d,_ in roster}; year = {n:y for n,_,y in roster}
cancel = Counter()
seen = Counter(n for _,n,_ in rows)
cnt = Counter()
for ts,n,m in rows:
    cnt[n]+=1
    if cnt[n] < seen[n]: cancel[m]+=1
q1 = last["장하늘"]
q2 = sum(1 for n,m in last.items() if dept.get(n)=="경영학과" and m=="토스트")
q3 = cancel.most_common()
q4 = sorted({year[n] for n in dept if n not in last})
total = Counter(m for _,_,m in rows)
print("Q1",q1,"Q2",q2,"Q3",q3,"Q4",q4,"전체주문",total.most_common())
assert q1=="컵라면" and q2==1 and q3[0][0]=="토스트" and q3[0][1]>q3[1][1] and q4==[26]
assert total.most_common(1)[0][0]=="햄버거"
menus=["떡볶이","부리또","햄버거","컵라면","토스트"]
P = {
 "id":"snack-mcq-01","type":"mcq","title":"간식 행사 메뉴 집계","badge":"객관식 4문항","timeLimitMin":20,
 "aiLimit":{"count":10,"chars":1000},"pii":[],
 "passage":"중앙동아리 \"오름\"에서 시험기간 동아리원들을 응원하기 위해 간식 행사를 기획중입니다. 학생들에게 나눠줄 간식을 주문하기 위해 설문조사를 진행해 개인이 먹고 싶은 메뉴를 신청받았습니다. 설문 결과를 담은 `간식메뉴.pdf` 파일과 학생들의 학과 정보를 담은 `오름.png` 파일을 확인하고 아래 질문에 답해주세요.",
 "notices":["한 명당 하나의 메뉴만 선택 가능합니다. 한 사람이 여러 번 메뉴를 주문한 경우, 가장 마지막 주문 이외에는 모두 취소됩니다. 예) `김민지:햄버거`, `김민지:햄버거`, `김민지:토스트`, `박서준:햄버거`, `김민지:햄버거` 순서로 신청 시 앞의 세 주문(`김민지:햄버거`, `김민지:햄버거`, `김민지:토스트`)은 취소됨"],
 "files":[
  {"name":"간식메뉴.pdf","kind":"image","tokens":1644,
   "image":{"title":"간식 메뉴 설문 기록","subtitle":"총 응답 수: 50건","columns":["응답 시간","응답자 명","메뉴"],"rows":[list(r) for r in rows],"split":2},
   "content":"응답 시간,응답자 명,메뉴\n"+"\n".join(",".join(r) for r in rows)},
  {"name":"오름.png","kind":"image","tokens":698,
   "image":{"title":"중앙동아리 오름 부원 명단","subtitle":"2026학년도 1학기 · 총 %d명"%len(roster),"columns":["이름","학과","학번"],"rows":[[n,d,str(y)] for n,d,y in roster],"split":1},
   "content":"이름,학과,학번\n"+"\n".join(f"{n},{d},{y}" for n,d,y in roster)},
 ],
 "questions":[
  {"q":"장하늘 학생은 어떤 메뉴를 신청했나요?","options":menus,"answer":4,
   "explain":"장하늘의 주문은 부리또 → 토스트 → 컵라면 순서이며 마지막 주문인 컵라면만 유효합니다. 이름이 비슷한 정하늘(최종 떡볶이)과 혼동하지 않아야 합니다."},
  {"q":"경영학과에서 토스트를 신청한 사람은 총 몇 명인가요?","options":["1명","2명","3명","4명","없다"],"answer":1,
   "explain":"경영학과 부원 중 최종 주문이 토스트인 사람은 서지호 1명입니다(토스트 2회 신청은 1명). 김민지·최준호·권나래·유하람은 토스트를 신청했다가 다른 메뉴로 바꿨고, 경제학과 윤솔은 학과가 다릅니다."},
  {"q":"가장 많이 취소된 메뉴는 무엇인가요?","options":menus,"answer":5,
   "explain":"취소 건수(최종 주문을 제외한 주문): "+", ".join(f"{m} {c}건" for m,c in q3)+". 전체 주문 수 1위는 햄버거("+str(total["햄버거"])+"건)지만 취소 1위는 토스트입니다."},
  {"q":"메뉴를 신청하지 않은 사람은 몇 학번인가요?","options":["23","24","25","26","모두가 신청했다"],"answer":4,
   "explain":"부원 명단 26명 중 설문에 없는 사람은 류시온(기계공학과 26학번) 1명입니다. 설문의 홍길동은 부원 명단에 없는 사람입니다."},
 ],
}
json.dump(P, open(__import__("os").path.join(__import__("os").path.dirname(__file__), "problem.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
print(len(rows), rows[:3], rows[-2:])
