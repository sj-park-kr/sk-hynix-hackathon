#!/usr/bin/env bash
# Cofa Probe 데모 시험 실행기 (Git Bash)
# 사용: bash exam/probe.sh [분=200]   (시작→응시→Q&A→채점 한 번에)
#       단계별: start [분] | agent | qa | grade
#       시나리오 고르기: SCENARIO=<exam/scenarios 아래 폴더 이름> bash exam/probe.sh  (기본 alarm-triage)
set -euo pipefail

HERE=$(cd "$(dirname "$0")" && pwd)
SCENARIO=${SCENARIO:-alarm-triage}
RUNS="$HOME/probe-runs"
SENTINEL=PROBE-HIDDEN-DO-NOT-COPY
# 개인 훅·플러그인·스킬을 빼야 실무자·채점 세션이 오염되지 않음(기본값이면 SessionStart 훅이 주입됨)
CLEAN=(--setting-sources project --disable-slash-commands)
READ_TOOLS=(Read Grep Glob "Bash(git log:*)" "Bash(git show:*)" "Bash(git diff:*)" "Bash(git status:*)")

win() { cygpath -w "$1" 2>/dev/null || echo "$1"; }
hm() { date -d "@$1" +%H:%M; }
ai() { env -u CLAUDECODE claude "$@"; }  # Claude Code 안에서 실행해도 중첩 실행이 막히지 않게
# 응시자·실무자는 Codex. gpt-6-astra는 시험에서 금지라 다른 모델로 고정하고, 세션 중 /model로 바꿨는지는 logs.mjs가 기록에서 잡는다
CANDIDATE_MODEL=gpt-6.1-sol
candidate() { codex -m "$CANDIDATE_MODEL" "$@"; }
current() {
  [ -f "$RUNS/current" ] || { echo "진행 중인 응시가 없습니다. 먼저: bash exam/probe.sh start" >&2; exit 1; }
  cat "$RUNS/current"
}
# 응시 중인 시나리오 폴더 (start가 응시 폴더에 이름을 남김. 기록이 없는 예전 응시는 alarm-triage)
scn() { echo "$HERE/scenarios/$(cat "$1/probe/scenario" 2>/dev/null || echo alarm-triage)"; }

start() {
  local min=${1:-200} run now
  [ -d "$HERE/scenarios/$SCENARIO/workspace" ] ||
    { echo "시나리오가 없습니다: $SCENARIO (있는 것: $(ls "$HERE/scenarios" | tr '\n' ' '))" >&2; exit 1; }
  run="$RUNS/$SCENARIO-$(date +%Y%m%d-%H%M%S)"
  mkdir -p "$run/probe/agent"
  echo "$SCENARIO" > "$run/probe/scenario"
  cp -r "$HERE/scenarios/$SCENARIO/workspace" "$run/work"
  if grep -rq "$SENTINEL" "$run/work"; then
    rm -rf "$run"; echo "숨김 파일이 응시 폴더에 섞여 중단합니다." >&2; exit 1
  fi
  git -C "$run/work" init -q -b main
  git -C "$run/work" config core.autocrlf false  # 제공 데이터를 바이트 그대로 유지
  git -C "$run/work" add -A
  git -C "$run/work" -c user.name=probe -c user.email=probe@local commit -qm "과제 초기 상태"
  now=$(date +%s)
  echo "$now" > "$run/probe/start"
  echo $((now + min * 60)) > "$run/probe/deadline"
  echo "$run" > "$RUNS/current"
  cat <<EOF
응시 시작 $(hm "$now") · 마감 $(hm $((now + min * 60))) (${min}분)
응시 폴더: $(win "$run/work")

1) VS Code로 응시 폴더 열기:  code "$(win "$run/work")"
2) Git Bash 터미널:          cd "$run/work" && codex -m $CANDIDATE_MODEL
                             (gpt-6-astra 사용 금지. /model로 바꾸면 채점 기록에 표시됨)
3) 터미널 분할(실무자 채팅):  bash "$HERE/probe.sh" agent
4) 마감 후:                  bash "$HERE/probe.sh" qa
EOF
}

# 실무자도 Codex. persona로 기본 지시를 바꾸고, 셸을 꺼서 숨김 정답 파일을 못 읽게 함
agent() {
  local run args SCN
  run=$(current); SCN=$(scn "$run")
  cd "$run/probe/agent"
  args=(-m "$CANDIDATE_MODEL" -s read-only --disable shell_tool --disable unified_exec
    -c "model_instructions_file='$(cygpath -m "$SCN/hidden/persona.md")'")
  # 실무자 창을 닫았다 다시 열어도 앞 대화를 이어감(resume --last는 현재 폴더 세션만 고름)
  if [ -f .started ]; then codex resume --last "${args[@]}"; else touch .started; codex "${args[@]}"; fi
}

# 기록 수집·시간 기록 (채점 전 필수)
finish() {
  local run p start deadline end
  run=$(current); p="$run/probe"
  [ -f "$p/end" ] || date +%s > "$p/end"
  start=$(cat "$p/start"); deadline=$(cat "$p/deadline"); end=$(cat "$p/end")
  node "$HERE/logs.mjs" "$p" "$run/work" "$p/agent"
  {
    echo "# 시간 기록"; echo
    echo "- 시작 $(hm "$start") · 마감 $(hm "$deadline") · 종료 $(hm "$end") (응시 $(( (end - start) / 60 ))분)"
    if [ "$end" -gt "$deadline" ]; then echo "- 마감 초과 $(( (end - deadline) / 60 ))분"; fi
  } > "$p/time.md"
}

# (선택) 사후 질문. 기본 흐름에서는 쓰지 않음
qa() {
  local run p
  run=$(current); p="$run/probe"
  finish
  # 다시 실행해도 이미 쓴 답변(answers.md)을 덮어쓰지 않음
  if [ ! -s "$p/qa.md" ]; then
    echo "사후 질문을 만드는 중..."
    (cd "$run" && ai -p --allowedTools "${READ_TOOLS[@]}" "${CLEAN[@]}" < "$HERE/grader/qa.md") > "$p/qa.md"
    cp "$p/qa.md" "$p/answers.md"
  fi
  cat "$p/qa.md"
  cat <<EOF

AI 없이, 문항당 3분(총 15분) 안에 각 질문 아래에 답을 쓰세요: $(win "$p/answers.md")
다 쓰면: bash "$HERE/probe.sh" grade
EOF
}

# shortcut: 축별 합계는 채점 LLM이 rubric 배점으로 더함. 점수가 흔들리면 항목 판정을 JSON으로 받아 코드로 합산할 것
grade() {
  local run p SCN
  run=$(current); p="$run/probe"; SCN=$(scn "$run")
  [ -f "$p/time.md" ] || finish
  echo "채점 중(빌드·테스트 실행 포함, 몇 분 걸림)..."
  { cat "$HERE/grader/grade.md"; printf '\n채점 기준·정답 키 폴더: %s\n' "$(win "$SCN/hidden")"; } |
    (cd "$run" && ai -p --add-dir "$(win "$SCN/hidden")" \
      --allowedTools "${READ_TOOLS[@]}" "Bash(npm install:*)" "Bash(npm run:*)" "Bash(npm test:*)" "Bash(node:*)" \
      "${CLEAN[@]}") > "$p/report.md"
  echo "채점 리포트: $(win "$p/report.md")"
}

# 한 번에: 응시 시작 → 실무자 창 → 응시자 codex → (종료 후) 기록 수집 → 채점
run() {
  local run
  start "${1:-200}" > /dev/null
  run=$(current)
  echo "응시 시작. 마감 $(hm "$(cat "$run/probe/deadline")"). 응시 폴더: $(win "$run/work")"
  command -v code > /dev/null && code "$(win "$run/work")"
  # 실무자 채팅은 새 창에서 (끄면 같은 대화를 이어서 다시 열 수 있음)
  mintty -t 실무자 -o FontHeight=14 -o Columns=110 -o Rows=40 -e bash "$HERE/probe.sh" agent &
  echo "이 창에서 응시자 codex($CANDIDATE_MODEL)를 시작합니다. gpt-6-astra는 쓰지 마세요. 끝내려면 /exit."
  (cd "$run/work" && candidate) || true
  read -r -p "응시를 끝내고 채점합니다. [Enter] " _
  finish
  grade
}

case "${1:-}" in
  "" | [0-9]*) run "${1:-200}" ;;
  start) start "${2:-200}" ;;
  agent | qa | grade) "$1" ;;
  *) echo "사용: bash exam/probe.sh [분=200] | start | agent | qa | grade" >&2; exit 1 ;;
esac
