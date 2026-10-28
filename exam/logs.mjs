#!/usr/bin/env node
// 대화 기록(jsonl) → 응시자 프롬프트, 실무자 대화, 토큰 요약. 숫자는 LLM이 아니라 여기서 센다.
// 응시자는 Codex(~/.codex/sessions), 실무자는 Claude Code(~/.claude/projects) 기록을 읽는다.
// 사용: node logs.mjs <출력 폴더> <응시 폴더> <실무자 폴더>   |   node logs.mjs --self-test
import fs from 'node:fs';
import os from 'node:os';
import path from 'node:path';
import assert from 'node:assert/strict';

// Claude Code는 작업 폴더 경로의 영숫자 외 문자를 '-'로 바꾼 이름으로 기록을 저장한다
const projectDir = (dir) =>
  path.join(os.homedir(), '.claude', 'projects', path.resolve(dir).replace(/[^A-Za-z0-9]/g, '-'));

const jsonlFiles = (dir) =>
  fs.existsSync(dir)
    ? fs.readdirSync(dir, { recursive: true }).filter((f) => f.endsWith('.jsonl')).map((f) => path.join(dir, f))
    : [];

const parse = (file) =>
  fs.readFileSync(file, 'utf8').split('\n').flatMap((l) => {
    try { return l ? [JSON.parse(l)] : []; } catch { return []; }
  });

const isNoise = (t) => /^<(local-command-(stdout|caveat)|system-reminder)/.test(t);

function userText(o) {
  if (o.type !== 'user' || o.isMeta || o.isSidechain) return '';
  const c = o.message?.content;
  const t = typeof c === 'string' ? c
    : Array.isArray(c) ? c.filter((b) => b.type === 'text').map((b) => b.text).join('\n') : '';
  return isNoise(t.trim()) ? '' : t.trim();
}

const blank = () => ({ prompts: 0, promptChars: 0, responses: 0, input: 0, cacheWrite: 0, cacheRead: 0, output: 0 });

export function summarize(dir) {
  const seen = new Set();
  const usage = { main: blank(), sub: blank() };
  const dialogue = [];
  for (const file of jsonlFiles(dir)) {
    const sub = file.split(path.sep).includes('subagents');
    for (const o of parse(file)) {
      if (o.type === 'assistant' && o.message?.id) {
        const m = o.message;
        const text = (m.content || []).filter((b) => b.type === 'text').map((b) => b.text).join('\n').trim();
        if (!sub && text) dialogue.push({ ts: o.timestamp, who: 'AI', text });
        // 한 응답이 블록마다 여러 줄로 기록되고 줄마다 같은 usage가 붙으므로 id당 한 번만 센다
        if (seen.has(m.id)) continue;
        seen.add(m.id);
        const u = usage[sub ? 'sub' : 'main'];
        const g = m.usage || {};
        u.responses++;
        u.input += g.input_tokens || 0;
        u.cacheWrite += g.cache_creation_input_tokens || 0;
        u.cacheRead += g.cache_read_input_tokens || 0;
        u.output += g.output_tokens || 0;
      } else if (!sub) {
        const text = userText(o);
        if (!text) continue;
        dialogue.push({ ts: o.timestamp, who: '응시자', text });
        usage.main.prompts++;
        usage.main.promptChars += text.length;
      }
    }
  }
  dialogue.sort((a, b) => String(a.ts).localeCompare(String(b.ts)));
  return { usage, dialogue };
}

// Codex는 날짜별 폴더에 모든 세션을 쌓으므로 session_meta의 작업 폴더로 응시 세션만 고른다
const codexHome = () => process.env.CODEX_HOME || path.join(os.homedir(), '.codex');
const samePath = (a, b) => path.resolve(a).toLowerCase() === path.resolve(b).toLowerCase();

export function summarizeCodex(workDir, sessionsDir = path.join(codexHome(), 'sessions')) {
  const usage = { main: blank(), sub: blank() };
  const dialogue = [];
  const models = new Set();
  for (const file of jsonlFiles(sessionsDir)) {
    const lines = parse(file);
    const meta = lines.find((o) => o.type === 'session_meta')?.payload;
    if (!meta?.cwd || !samePath(meta.cwd, workDir)) continue;
    const sub = meta.thread_source === 'subagent';
    const u = usage[sub ? 'sub' : 'main'];
    for (const { type, timestamp: ts, payload: p } of lines) {
      if (type === 'turn_context' && p.model) models.add(p.model);
      else if (type === 'token_usage_record') {
        const g = p.usage || {};
        u.responses++;
        u.input += (g.input_tokens || 0) - (g.cached_input_tokens || 0);
        u.cacheWrite += g.cache_write_input_tokens || 0;
        u.cacheRead += g.cached_input_tokens || 0;
        u.output += g.output_tokens || 0;
      } else if (type === 'event_msg' && p.type === 'item_completed' && !sub) {
        const it = p.item;
        const text = (it.content || []).map((b) => b.text || '').join('\n').trim();
        if (!text) continue;
        if (it.type === 'UserMessage') {
          dialogue.push({ ts, who: '응시자', text });
          u.prompts++;
          u.promptChars += text.length;
        } else if (it.type === 'AgentMessage') dialogue.push({ ts, who: 'AI', text });
      }
    }
  }
  dialogue.sort((a, b) => String(a.ts).localeCompare(String(b.ts)));
  return { usage, dialogue, models: [...models] };
}

// 시험에서 쓰면 안 되는 모델
export const BANNED_MODEL = /astra/i;

const time = (ts) => (ts ? new Date(ts).toLocaleTimeString('ko-KR', { hour12: false }) : '--:--:--');
// shortcut: 한 발화가 4,000자를 넘으면 자름(붙여넣은 긴 자료), 채점에 전문이 필요해지면 늘릴 것
const clip = (t) => (t.length > 4000 ? `${t.slice(0, 4000)}\n…(${t.length - 4000}자 생략)` : t);
const render = (rows, names) =>
  rows.map((r) => `### [${time(r.ts)}] ${names[r.who] || r.who}\n\n${clip(r.text)}\n`).join('\n') || '(기록 없음)\n';

function usageTable(work, agent) {
  const row = (name, u) =>
    `| ${name} | ${u.prompts} | ${u.promptChars} | ${u.responses} | ${u.input} | ${u.cacheWrite} | ${u.cacheRead} | ${u.output} |`;
  return [
    '| 구분 | 프롬프트 수 | 프롬프트 글자 | AI 응답 수 | 입력 | 캐시 생성 | 캐시 읽기 | 출력 |',
    '|---|---|---|---|---|---|---|---|',
    row('응시자 AI(메인)', work.usage.main),
    row('응시자 AI(서브에이전트)', work.usage.sub),
    row('실무자 대화', agent.usage.main),
  ].join('\n');
}

function main([out, workDir, agentDir]) {
  const work = summarizeCodex(workDir);
  const agent = summarize(projectDir(agentDir));
  const banned = work.models.filter((m) => BANNED_MODEL.test(m));
  const modelLine = `응시자 Codex 모델: ${work.models.join(', ') || '(기록 없음)'}`
    + (banned.length ? ` — **금지 모델 사용: ${banned.join(', ')}**` : '');
  fs.mkdirSync(out, { recursive: true });
  fs.writeFileSync(path.join(out, 'prompts.md'),
    `# 응시자 ↔ AI 코딩 도구 대화\n\n${render(work.dialogue, {})}`);
  fs.writeFileSync(path.join(out, 'agent-chat.md'),
    `# 응시자 ↔ 실무자 대화\n\n${render(agent.dialogue, { AI: '실무자' })}`);
  fs.writeFileSync(path.join(out, 'usage.md'), `# 토큰·대화 사용량\n\n${modelLine}\n\n${usageTable(work, agent)}\n`);
  console.log(`${modelLine}\n${usageTable(work, agent)}`);
}

function selfTest() {
  const dir = fs.mkdtempSync(path.join(os.tmpdir(), 'probe-logs-'));
  const line = (o) => JSON.stringify(o);
  const ai = (id, block, usage) => ({ type: 'assistant', timestamp: '2026-10-31T01:01:00Z', message: { id, content: [block], usage } });
  fs.writeFileSync(path.join(dir, 'main.jsonl'), [
    line({ type: 'user', timestamp: '2026-10-31T01:00:00Z', message: { content: '첫 질문' } }),
    line({ type: 'user', isMeta: true, message: { content: '메타' } }),
    line({ type: 'user', message: { content: [{ type: 'tool_result', content: 'x' }] } }),
    line(ai('m1', { type: 'text', text: '답1' }, { input_tokens: 10, output_tokens: 5, cache_read_input_tokens: 100 })),
    line(ai('m1', { type: 'tool_use', name: 'Bash' }, { input_tokens: 10, output_tokens: 5, cache_read_input_tokens: 100 })),
    line({ type: 'user', message: { content: '<local-command-stdout>x</local-command-stdout>' } }),
    '{깨진 줄',
  ].join('\n'));
  fs.mkdirSync(path.join(dir, 's1', 'subagents'), { recursive: true });
  fs.writeFileSync(path.join(dir, 's1', 'subagents', 'agent-1.jsonl'), [
    line({ type: 'user', message: { content: '서브 지시' } }),
    line(ai('s1', { type: 'text', text: '서브 답' }, { input_tokens: 1, output_tokens: 2 })),
  ].join('\n'));
  const { usage, dialogue } = summarize(dir);
  assert.deepEqual(dialogue.map((d) => `${d.who}:${d.text}`), ['응시자:첫 질문', 'AI:답1']);
  assert.deepEqual(usage.main, { prompts: 1, promptChars: 4, responses: 1, input: 10, cacheWrite: 0, cacheRead: 100, output: 5 });
  assert.equal(usage.sub.responses, 1);
  assert.equal(usage.sub.output, 2);
  assert.equal(usage.sub.prompts, 0);
  assert.equal(projectDir('C:\\Users\\a\\probe-runs\\x-1\\work').endsWith('C--Users-a-probe-runs-x-1-work'), process.platform === 'win32');

  // Codex: 다른 폴더 세션은 무시, 서브에이전트는 토큰만, 모델 기록
  const cx = path.join(dir, 'codex', '2026', '10', '31');
  const work = path.join(dir, 'work');
  const ev = (ts, item) => ({ type: 'event_msg', timestamp: ts, payload: { type: 'item_completed', item } });
  const tok = { type: 'token_usage_record', payload: { usage: { input_tokens: 100, cached_input_tokens: 60, output_tokens: 7 } } };
  const session = (name, cwd, threadSource, rows) => {
    fs.mkdirSync(cx, { recursive: true });
    fs.writeFileSync(path.join(cx, name),
      [{ type: 'session_meta', payload: { cwd, thread_source: threadSource } }, ...rows].map(line).join('\n'));
  };
  session('a.jsonl', work.toUpperCase(), 'user', [
    { type: 'turn_context', payload: { model: 'gpt-6-astra' } },
    ev('2026-10-31T01:00:00Z', { type: 'UserMessage', content: [{ type: 'text', text: '구현해줘' }] }),
    ev('2026-10-31T01:00:05Z', { type: 'AgentMessage', content: [{ type: 'Text', text: '했습니다' }] }),
    ev('2026-10-31T01:00:03Z', { type: 'CommandExecution', command: ['ls'] }),
    tok, tok,
  ]);
  session('b.jsonl', work, 'subagent', [ev('2026-10-31T01:00:01Z', { type: 'UserMessage', content: [{ type: 'text', text: '서브 지시' }] }), tok]);
  session('c.jsonl', path.join(dir, 'other'), 'user', [ev('2026-10-31T01:00:02Z', { type: 'UserMessage', content: [{ type: 'text', text: '남의 세션' }] })]);
  const c = summarizeCodex(work, path.join(dir, 'codex'));
  assert.deepEqual(c.dialogue.map((d) => `${d.who}:${d.text}`), ['응시자:구현해줘', 'AI:했습니다']);
  assert.deepEqual(c.usage.main, { prompts: 1, promptChars: 4, responses: 2, input: 80, cacheWrite: 0, cacheRead: 120, output: 14 });
  assert.equal(c.usage.sub.responses, 1);
  assert.deepEqual(c.models, ['gpt-6-astra']);
  assert.ok(BANNED_MODEL.test(c.models[0]) && !BANNED_MODEL.test('gpt-6.1-sol'));
  fs.rmSync(dir, { recursive: true });
  console.log('self-test ok');
}

if (process.argv[2] === '--self-test') selfTest();
else if (process.argv.length === 5) main(process.argv.slice(2));
else { console.error('사용: node logs.mjs <출력 폴더> <응시 폴더> <실무자 폴더> | --self-test'); process.exit(1); }
