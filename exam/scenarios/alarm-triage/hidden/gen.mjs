// PROBE-HIDDEN-DO-NOT-COPY
// 설비 알람 트리아지 시나리오 — 결정적 데이터 생성기 (의존성 없음)
// 사용: node hidden/gen.mjs
//   1) workspace/uploads/* 를 지우고 다시 쓴다
//   2) 쓴 CSV를 다시 읽어 참조 처리(정답 키 기준)를 돌리고,
//      hidden/answer-key.md 의 GEN:BEGIN ~ GEN:END 구간을 다시 쓴다
import { mkdirSync, readFileSync, readdirSync, rmSync, writeFileSync } from 'node:fs';
import { dirname, join } from 'node:path';
import { fileURLToPath } from 'node:url';

const HERE = dirname(fileURLToPath(import.meta.url));
const UP = join(HERE, '..', 'workspace', 'uploads');
const LOGS = join(UP, 'logs');
const KEY_MD = join(HERE, 'answer-key.md');

// ---------- PRNG (mulberry32) ----------
let seed = 20261031;
const rnd = () => {
  seed = (seed + 0x6d2b79f5) | 0;
  let t = Math.imul(seed ^ (seed >>> 15), 1 | seed);
  t = (t + Math.imul(t ^ (t >>> 7), 61 | t)) ^ t;
  return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
};
const ri = (lo, hi) => lo + Math.floor(rnd() * (hi - lo + 1));
const pick = (a) => a[Math.floor(rnd() * a.length)];

// ---------- 시간 (내부 표현: UTC epoch ms) ----------
const MIN = 60_000, HOUR = 60 * MIN, DAY = 24 * HOUR, KST_OFF = 9 * HOUR;
const kst = (s) => Date.parse(s.trim().replace(' ', 'T') + '+09:00'); // 'YYYY-MM-DD HH:mm[:ss]' (KST)
const fmtKst = (ms) => new Date(ms + KST_OFF).toISOString().slice(0, 19).replace('T', ' ');
const fmtUtc = (ms) => new Date(ms).toISOString().slice(0, 19) + 'Z';
const hhmm = (ms) => fmtKst(ms).slice(11, 16);
const WD = '일월화수목금토';
const mdw = (ms) => {
  const d = new Date(ms + KST_OFF);
  return `${d.getUTCMonth() + 1}/${d.getUTCDate()}(${WD[d.getUTCDay()]})`;
};

const START = kst('2026-10-21 07:00'), END = kst('2026-10-24 07:00');
const SHIFTS = Array.from({ length: 6 }, (_, i) => ({
  id: `S${i + 1}`, start: START + i * 12 * HOUR, end: START + (i + 1) * 12 * HOUR, kind: i % 2 ? '야간' : '주간',
}));

// ---------- 마스터 ----------
const ETCH = ['ETCH-01', 'ETCH-02', 'ETCH-03', 'ETCH-04'];
const CVD = ['CVD-01', 'CVD-02', 'CVD-03'];
const ALL_EQP = [...ETCH, ...CVD];
const isCvd = (e) => e.startsWith('CVD');

// 사번·이름은 모두 가상
const OPS = [
  ['H2019033', '윤서진'], ['H2031457', '김민수'], ['H2027716', '이지훈'], ['H2040122', '박서연'],
  ['H2022589', '최현우'], ['H2045310', '정다은'], ['H2018874', '강도현'], ['H2038061', '조유진'],
];
const API_KEY = 'EMSB-LIVE-4f9c2a7e1b8d6035c71a';
const PC_PW = 'M3fab#Night26';
const PHONES = ['010-4821-7730', '010-5512-3087'];
const CVD_HEAD = `# EMS-B Export v1.4 | server=emsb-m3.gaon.internal | account=svc_emsexp | api_key=${API_KEY}`;

// v23/v30: 매뉴얼 버전별 등급(null = 그 버전에 없음). n23/n30: 이름, a23/a30: 조치, te/tc: 로그 문구(식각/증착)
const CODES = {
  'P-1001': { v23: 'A', v30: 'A', n23: '진공펌프 이상', a23: '펌프 상태 확인, 유틸리티팀 호출, 설비 Down 요청 여부 판단', a30: '펌프 상태 확인, 유틸리티팀 호출, 설비 Down 요청 여부 판단. 연쇄 알람(4장) 확인', te: 'DRY PUMP FAULT', tc: 'Dry pump fault' },
  'E-1203': { v23: 'A', v30: 'A', n23: '챔버 압력 이탈', a23: '배기·밸브 상태 확인. 5분 이상 지속 시 설비 Down 요청 여부 판단', te: 'CHAMBER PRESSURE OUT OF RANGE', tc: 'Chamber pressure out of range, check exhaust' },
  'E-1402': { v23: 'A', v30: 'B', n23: 'RF 반사파 과다', a23: 'RF 매칭 점검, 진행 lot hold', a30: 'RF 매칭 상태 기록. 동일 설비에서 한 교대 3회 이상 발생 시 A로 취급하고 매칭박스 점검 요청', te: 'RF REFLECTED POWER HIGH', tc: 'RF reflected power high' },
  'E-1810': { v23: 'B', v30: 'B', n23: '히터 온도 이탈', a23: '온도 추이 확인, 반복 시 벤더 문의', te: 'HEATER TEMP DEVIATION', tc: 'Heater temperature deviation' },
  'E-2107': { v23: 'B', v30: 'A', n23: 'He 백사이드 압력 이탈', a23: 'He 압력 추이 모니터링', a30: '진행 lot hold 요청, 척 He 라인 점검. 설비 Down 요청 여부 판단', te: 'HE BACKSIDE PRESSURE DEVIATION', tc: 'He backside pressure deviation' },
  'E-2210': { v23: null, v30: 'B', n23: 'MFC 유량 편차', a30: 'MFC 영점 확인, 반복 시 교체 검토', te: 'MFC FLOW DEVIATION', tc: 'MFC flow deviation' },
  'E-3105': { v23: 'A', v30: 'A', n23: '웨이퍼 이송 실패', a23: '이송 로봇·웨이퍼 위치 확인, 웨이퍼 파손 여부 확인', te: 'WAFER TRANSFER FAIL', tc: 'Wafer transfer failed' },
  'E-4001': { v23: 'B', v30: 'B', n23: 'EMS 통신 두절', a23: '설비 PC 네트워크 확인, 10분 이상 지속 시 IT 호출', te: 'EMS COMM LOST', tc: 'EMS communication lost' },
  'W-0310': { v23: 'C', v30: null, n23: '냉각수 온도 경고', a23: '냉각수 온도 확인', te: 'PCW TEMP WARNING', tc: 'PCW temperature warning' },
  'W-0311': { v23: 'C', v30: 'C', n23: '냉각수 유량 경고', n30: '냉각수 온도/유량 경고', a23: '냉각수 유량 확인', a30: '냉각수 온도·유량 확인', te: 'PCW TEMP/FLOW WARNING', tc: 'PCW temp/flow warning' },
  'W-0502': { v23: 'C', v30: 'C', n23: '배기 압력 경고', a23: '배기 라인 확인, 반복 시 인계 기록', te: 'EXHAUST PRESSURE WARNING', tc: 'Exhaust pressure warning' },
  'W-0620': { v23: 'C', v30: 'C', n23: '소모품 교체 주기 도래', a23: '다음 PM 교체 계획에 반영', te: 'CONSUMABLE LIFETIME REACHED', tc: 'Consumable lifetime reached' },
  'W-0701': { v23: 'C', v30: 'C', n23: '도어 인터락', a23: 'PM·점검 중이 아닌데 발생하면 도어 상태 확인', te: 'DOOR INTERLOCK', tc: 'Door interlock' },
  'I-0105': { v23: 'C', v30: 'I', n23: '레시피 파라미터 변경', a23: '변경 이력 확인', a30: '정보. 인계 대상 아님', te: 'RECIPE PARAMETER CHANGED', tc: 'Recipe parameter changed' },
  'I-0210': { v23: 'C', v30: 'I', n23: '로트 대기 시간 초과', a23: '물류 담당 공유', a30: '정보. 인계 대상 아님', te: 'LOT WAIT TIME EXCEEDED', tc: 'Lot wait time exceeded' },
  'E-3990': { v23: null, v30: null, te: 'UNDEFINED ALARM', tc: 'Alarm 3990 (no description)' }, // 어느 매뉴얼에도 없음
};
const ALIAS30 = { 'W-0310': 'W-0311' };
const CHAIN_PARENT = 'P-1001', CHAIN_CHILDREN = ['E-1203', 'E-2107', 'W-0502'], CHAIN_WIN = 5 * MIN;
const DEDUP_WIN = 10 * MIN, PM_AFTER = 30 * MIN;
const name30 = (c) => CODES[c]?.n30 ?? CODES[c]?.n23 ?? '';

// PM 일정 (MES 기준, KST)
const PMS = [
  { id: 'PM-2610-011', eqp: 'ETCH-02', type: '주간PM', ps: '2026-10-21 09:00', pe: '2026-10-21 13:00', as: '2026-10-21 09:00', ae: '2026-10-21 12:40', st: '완료', note: '' },
  { id: 'PM-2610-014', eqp: 'CVD-01', type: '월간PM', ps: '2026-10-22 20:00', pe: '2026-10-23 02:00', as: '2026-10-22 20:10', ae: '2026-10-23 04:10', st: '완료', note: '히터 교체로 연장' },
  { id: 'PM-2610-017', eqp: 'CVD-03', type: '주간PM', ps: '2026-10-23 09:00', pe: '2026-10-23 11:00', as: '2026-10-23 09:05', ae: '2026-10-23 10:50', st: '완료', note: '' },
  { id: 'PM-2610-018', eqp: 'ETCH-04', type: '주간PM', ps: '2026-10-23 13:00', pe: '2026-10-23 16:00', as: '', ae: '', st: '취소', note: '부품 미입고' },
  { id: 'PM-2610-021', eqp: 'ETCH-01', type: '분기PM', ps: '2026-10-25 08:00', pe: '2026-10-25 20:00', as: '', ae: '', st: '예정', note: '' },
];

// ---------- 이벤트 생성 ----------
const EV = [];
let order = 0;
function alarm(eqp, t, code, { clr = ri(2, 25), note = '', clrNote = '', bad = '' } = {}) {
  const ch = isCvd(eqp) ? pick(['PM1', 'PM2']) : pick(['CH-A', 'CH-B']);
  const info = code.startsWith('I-');
  EV.push({ t, eqp, code, kind: 'SET', ch, user: code === 'I-0105' ? pick(OPS) : null, note, bad, o: order++ });
  if (clr != null && !info) EV.push({ t: t + clr * MIN + ri(0, 59) * 1000, eqp, code, kind: 'CLEAR', ch, user: pick(OPS), note: clrNote, bad: '', o: order++ });
}
const at = (s) => kst(s);

// 배경 알람: 완료 PM 창(앞 10분 ~ 뒤 40분)은 비움
const pmBusy = (eqp, t) => PMS.some((p) => p.st === '완료' && p.eqp === eqp &&
  t >= Math.min(kst(p.ps), kst(p.as)) - 10 * MIN && t <= Math.max(kst(p.pe), kst(p.ae)) + 40 * MIN);
const BG_ETCH = ['W-0311', 'W-0311', 'W-0311', 'W-0502', 'W-0502', 'W-0620', 'W-0620', 'I-0105', 'I-0105', 'I-0105', 'I-0210', 'I-0210', 'E-1810', 'E-4001'];
const BG_CVD = ['W-0311', 'W-0311', 'W-0502', 'W-0502', 'W-0502', 'W-0620', 'W-0620', 'I-0105', 'I-0105', 'I-0210', 'I-0210', 'I-0210', 'E-2210', 'E-1810'];
const BG_NOTE = ['', '', '', '자동 해제', '리셋 후 정상', '확인'];
for (const sh of SHIFTS) for (const eqp of ALL_EQP) {
  const n = ri(5, 9);
  for (let k = 0; k < n; k++) {
    const t = sh.start + ri(5, 712) * MIN + ri(0, 59) * 1000;
    let code = pick(isCvd(eqp) ? BG_CVD : BG_ETCH);
    if (pmBusy(eqp, t)) continue;
    if (eqp === 'ETCH-01' && code === 'W-0311') code = 'W-0310'; // 구 펌웨어
    alarm(eqp, t, code, { clr: rnd() < 0.08 ? null : ri(2, 25), clrNote: isCvd(eqp) ? pick(BG_NOTE) : '' });
  }
}

// S1 10/21 주간
alarm('ETCH-03', at('2026-10-21 15:22:14'), 'E-3105', { clr: 9 });
alarm('CVD-02', at('2026-10-21 10:12:40'), 'E-1402', { clr: 4 });
alarm('CVD-02', at('2026-10-21 16:47:03'), 'E-1402', { clr: 6 });
for (const [hm, code] of [['09:14:22', 'W-0701'], ['09:15:03', 'W-0701'], ['09:40:51', 'E-1203'], ['10:05:17', 'W-0701'], ['10:32:44', 'W-0311'], ['11:20:09', 'E-1203'], ['11:58:30', 'W-0701'], ['12:21:12', 'W-0701'], ['12:30:58', 'W-0311']])
  alarm('ETCH-02', at(`2026-10-21 ${hm}`), code, { clr: ri(1, 6) }); // PM 중 테스트 알람
alarm('ETCH-02', at('2026-10-21 12:52:31'), 'E-1810', { clr: 12 }); // 실제 종료 12:40 후 12분 (계획 종료 13:00 기준이면 PM 중으로 오분류)

// S2 10/21 야간
alarm('CVD-01', at('2026-10-21 23:40:08'), 'P-1001', { clr: 92, clrNote: '펌프 교체 후 정상' });
alarm('CVD-01', at('2026-10-21 23:41:15'), 'E-1203', { clr: 85 });
alarm('CVD-01', at('2026-10-21 23:42:02'), 'E-2107', { clr: 80 });
for (const hm of ['23:43:30', '23:45:12', '23:50:44']) alarm('CVD-01', at(`2026-10-21 ${hm}`), 'W-0502', { clr: 1 });
alarm('ETCH-04', at('2026-10-22 02:15:47'), 'E-2107', { clr: 5 }); // v3.0에서 A로 상향
for (const hm of ['03:00:21', '03:03:50', '03:07:12', '03:12:40', '03:18:05', '03:21:33'])
  alarm('ETCH-01', at(`2026-10-22 ${hm}`), 'W-0502', { clr: 1 }); // 깜빡임: 간격 기준 1건, 고정창 기준 2건
alarm('CVD-03', at('2026-10-22 04:05:19'), 'E-3990', { clr: 3 });
alarm('ETCH-02', at('2026-10-22 05:10:26'), 'E-1810', { clr: 7, bad: 'hash' }); // 엑셀 경유 손상 행

// S3 10/22 주간
alarm('CVD-02', at('2026-10-22 08:55:10'), 'W-0502', { clr: 6 }); // UTC 23:55 → 두 파일에 중복 기록
alarm('CVD-02', at('2026-10-22 09:10:33'), 'E-1402', { clr: 5 });
alarm('CVD-02', at('2026-10-22 10:31:02'), 'E-1402', { clr: 3 });
alarm('CVD-02', at('2026-10-22 10:36:55'), 'E-1402', { clr: 2, clrNote: '매칭박스 리셋, "박서연 확인"' });
alarm('CVD-02', at('2026-10-22 13:05:47'), 'E-1402', { clr: 8, clrNote: `RF 매칭 점검 요청, 벤더 담당 ${PHONES[0]} 연락` });
alarm('CVD-02', at('2026-10-22 16:40:19'), 'E-1402', { clr: 4 });
for (const hm of ['11:00:10', '11:04:38', '11:08:51']) alarm('ETCH-03', at(`2026-10-22 ${hm}`), 'E-1402', { clr: 1 }); // 원시 3회, 묶으면 1건
alarm('ETCH-02', at('2026-10-22 14:02:37'), 'E-1810', { clr: 10 });
alarm('ETCH-02', at('2026-10-22 17:30:05'), 'E-1810', { clr: 6 });

// S4 10/22 야간 — CVD-01 월간PM 실제 20:10~04:10 (계획 20:00~02:00)
for (const [d, code] of [['2026-10-22 20:15:33', 'W-0701'], ['2026-10-22 20:16:02', 'W-0701'], ['2026-10-22 21:02:47', 'E-2210'], ['2026-10-22 22:30:15', 'P-1001'], ['2026-10-22 22:31:40', 'E-1203'], ['2026-10-22 23:10:08', 'W-0701'], ['2026-10-23 00:20:55', 'E-2210'], ['2026-10-23 01:05:31', 'W-0701'], ['2026-10-23 01:40:12', 'W-0311'], ['2026-10-23 03:00:44', 'E-1203'], ['2026-10-23 03:31:19', 'W-0701'], ['2026-10-23 03:55:02', 'W-0701']])
  alarm('CVD-01', at(d), code, { clr: ri(1, 6), clrNote: 'PM 테스트' });
alarm('CVD-01', at('2026-10-23 04:22:38'), 'E-2210', { clr: 7 }); // PM 종료 12분 후
alarm('CVD-01', at('2026-10-23 04:35:50'), 'W-0311', { clr: 3 }); // PM 종료 25분 후
alarm('CVD-01', at('2026-10-23 04:51:16'), 'E-1810', { clr: 9 }); // 41분 후 → 해당 없음
alarm('ETCH-03', at('2026-10-23 01:30:42'), 'E-3105', { clr: null }); // 해제 안 됨
alarm('CVD-02', at('2026-10-23 02:44:09'), 'W-0620', { clr: 5, bad: 'trunc' }); // 내보내기 중 잘린 행

// S5 10/23 주간
for (const hm of ['09:07:40', '09:30:12', '10:12:55']) alarm('CVD-03', at(`2026-10-23 ${hm}`), 'W-0701', { clr: ri(1, 4), clrNote: 'PM 테스트' });
alarm('ETCH-04', at('2026-10-23 14:20:36'), 'E-1203', { clr: 20 }); // 취소된 PM 시간대 → 정상 집계
alarm('ETCH-04', at('2026-10-23 15:10:02'), 'W-0311', { clr: 4 });
alarm('CVD-02', at('2026-10-23 08:12:27'), 'E-3990', { clr: 2 });
alarm('CVD-02', at('2026-10-23 17:48:51'), 'E-3990', { clr: 2 });

// S6 10/23 야간
alarm('ETCH-02', at('2026-10-23 22:10:05'), 'P-1001', { clr: 35 });
alarm('ETCH-02', at('2026-10-23 22:12:40'), 'E-1203', { clr: 30 });
alarm('ETCH-02', at('2026-10-23 22:13:18'), 'W-0502', { clr: 2 });
alarm('ETCH-02', at('2026-10-23 22:30:51'), 'E-2107', { clr: 15 }); // 펌프 20분 뒤 → 연쇄 아님
alarm('CVD-01', at('2026-10-23 23:30:27'), 'E-2107', { clr: null }); // UTC 14:30 → 미변환 시 주간으로 감

EV.sort((a, b) => a.t - b.t || a.o - b.o);
const inRange = EV.filter((e) => e.t >= START && e.t < END);

// ---------- 파일 쓰기 ----------
const csvq = (s) => (/[",\n]/.test(s) ? `"${s.replace(/"/g, '""')}"` : s);
rmSync(UP, { recursive: true, force: true });
mkdirSync(LOGS, { recursive: true });

// 식각(A사 EMS): KST 날짜별, BOM + CRLF
for (let d = kst('2026-10-21 00:00'); d < END; d += DAY) {
  const rows = inRange.filter((e) => !isCvd(e.eqp) && e.t >= d && e.t < d + DAY).map((e) => [
    e.bad === 'hash' ? '##########' : fmtKst(e.t), e.eqp, e.ch, e.code, CODES[e.code].te, e.kind,
    e.user ? `${e.user[0]} ${e.user[1]}` : '',
  ].join(','));
  const name = `etch_${fmtKst(d).slice(0, 10).replace(/-/g, '')}.csv`;
  writeFileSync(join(LOGS, name), '﻿' + ['timestamp,eqp_id,chamber,alarm_code,alarm_text,event,ack_user', ...rows].join('\r\n') + '\r\n');
}
// 증착(B사 서버): UTC 날짜별, 앞뒤 10분 겹쳐 내보냄, 첫 줄에 내보내기 정보
for (let d = Date.UTC(2026, 9, 20); d < END; d += DAY) {
  const rows = inRange.filter((e) => isCvd(e.eqp) && e.t >= d - 10 * MIN && e.t < d + DAY + 10 * MIN).map((e) => {
    const line = [fmtUtc(e.t), e.eqp, e.ch, e.code.replace('-', ''), csvq(CODES[e.code].tc), e.kind === 'SET' ? 'ON' : 'OFF',
      e.user ? e.user[0] : '', csvq(e.note)].join(',');
    return e.bad === 'trunc' ? line.slice(0, line.indexOf(',', 25) + 4) : line;
  });
  const name = `cvd_${new Date(d).toISOString().slice(0, 10).replace(/-/g, '')}.csv`;
  writeFileSync(join(LOGS, name), [CVD_HEAD, 'ALM_TIME,TOOL,MODULE,ALM_ID,ALM_MSG,STATE,USER_ID,NOTE', ...rows].join('\n') + '\n');
}

writeFileSync(join(UP, 'pm_schedule.csv'), '﻿' + [
  'pm_id,eqp_id,pm_type,planned_start,planned_end,actual_start,actual_end,status,note',
  ...PMS.map((p) => [p.id, p.eqp, p.type, p.ps, p.pe, p.as, p.ae, p.st, p.note].join(',')),
].join('\r\n') + '\r\n');

const table = (ver) => Object.entries(CODES).filter(([, c]) => c[ver]).map(([code, c]) =>
  `| ${code} | ${ver === 'v30' ? name30(code) : c.n23} | ${c[ver]} | ${(ver === 'v30' && c.a30) || c.a23} |`).join('\n');

writeFileSync(join(UP, 'alarm_manual_v2.3.md'), `# 알람 조치 매뉴얼 — 식각/증착 베이 (최종본)

- 문서 번호: EQ-M3-ALM-002
- 버전: v2.3 (최종본)
- 개정일: 2025-03-02
- 작성: 설비기술팀

## 1. 등급 정의

| 등급 | 의미 | 기본 조치 |
|------|------|-----------|
| A | 즉시 조치 | 담당 엔지니어 즉시 확인, 설비 Down 요청 여부 판단 |
| B | 교대 내 확인 | 교대 종료 전 원인 확인, 인계에 기록 |
| C | 참고 | 반복될 때 인계에 기록 |

## 2. 알람 코드별 조치

| 코드 | 알람명 | 등급 | 조치 |
|------|--------|------|------|
${table('v23')}

## 3. 비고

- 설비 로그의 알람 문구는 벤더마다 다르다. 코드 기준으로 본다.
- 이 매뉴얼에 없는 코드는 설비기술팀 파트장에게 보고한다.
`);

writeFileSync(join(UP, 'alarm_manual_v3.0.md'), `# 알람 조치 매뉴얼 — 식각/증착 베이

- 문서 번호: EQ-M3-ALM-002
- 버전: v3.0
- 상태: 개정안(검토중)
- 작성: 설비기술팀 / 검토: 설비기술팀 파트장

## 0. 변경 이력 (v2.3 → v3.0)

| 항목 | 변경 내용 |
|------|-----------|
| 시행 | 2026-10-20 주간 근무부터 |
| E-2107 | 등급 B → A (He 압력 이탈 후 lot 불량 사례 반영) |
| E-1402 | 등급 A → B. 단, 동일 설비에서 한 교대 동안 3회 이상 발생하면 A로 취급 |
| E-2210 | 신규 코드 (MFC 유량 편차) |
| W-0310 | 폐지, W-0311(냉각수 온도/유량 경고)로 통합. 구 펌웨어 설비는 W-0310으로 계속 표시될 수 있음 |
| I-0105, I-0210 | C → I(정보). 인계 대상 아님 |
| 4장 | 연쇄 알람 기준 신설 |

## 1. 등급 정의

| 등급 | 의미 | 기본 조치 |
|------|------|-----------|
| A | 즉시 조치 | 담당 엔지니어 즉시 확인, 설비 Down 요청 여부 판단 |
| B | 교대 내 확인 | 교대 종료 전 원인 확인, 인계에 기록 |
| C | 참고 | 설비별 건수만 인계에 기록 |
| I | 정보 | 인계 대상 아님 |

## 2. 알람 코드별 조치

| 코드 | 알람명 | 등급 | 조치 |
|------|--------|------|------|
${table('v30')}

## 3. 비고

- 설비 로그의 알람 문구는 벤더마다 다르다. 코드 기준으로 본다.

## 4. 연쇄 알람

- P-1001(진공펌프 이상) 발생 후 **5분 이내** 같은 설비에서 발생한 E-1203, E-2107, W-0502는 P-1001의 연쇄 알람으로 본다.
- 연쇄 알람은 별도 건으로 세지 않고 P-1001 건에 묶어 기록한다.
`);

writeFileSync(join(UP, 'handover_memo_example.txt'), `[10/20(화) 야간 → 10/21(수) 주간 인계]  작성: 윤서진(${OPS[0][0]}) B조

■ 1. 미조치 / 확인 필요
 - ETCH-03 02:14 E-1203 챔버 압력 이탈 / 알람 유지중 / 펌프 점검 요청함, 벤더 회신 대기
   (벤더 담당 최OO 과장 ${PHONES[1]})
 - CVD-02 04:40 E-1402 RF 반사파 / 해제 / 이번 교대 3번째, 주간에 매칭 확인 부탁

■ 2. 설비별 요약
 - ETCH-01 : 특이사항 없음 (W-0310 2건)
 - ETCH-02 : B 1건 (E-1810 히터 온도) 해제, 확인 완료
 - ETCH-03 : 1번 참고
 - ETCH-04 : 특이사항 없음
 - CVD-01 : C 3건
 - CVD-02 : 1번 참고
 - CVD-03 : 특이사항 없음

■ 3. PM
 - 없음

■ 4. 기타
 - 설비PC 공용계정 비번 바뀜 → shift_b / ${PC_PW} (외부 공유 금지)
 - 김민수 님 내일 연차, 주간 인원 1명 적음
`);

// ---------- 참조 처리 (정답 키 기준) ----------
function parseCsvLine(line) {
  const out = []; let cur = '', q = false;
  for (let i = 0; i < line.length; i++) {
    const c = line[i];
    if (q) { if (c !== '"') cur += c; else if (line[i + 1] === '"') { cur += '"'; i++; } else q = false; }
    else if (c === '"') q = true; else if (c === ',') { out.push(cur); cur = ''; } else cur += c;
  }
  out.push(cur);
  return out;
}
const normCode = (s) => s.trim().replace(/^([A-Z])-?(\d{4})$/, '$1-$2');

function loadLogs() {
  const rows = [], bad = [], seen = new Set(), files = [];
  let dup = 0;
  for (const f of readdirSync(LOGS).sort()) {
    const src = f.startsWith('cvd') ? 'cvd' : 'etch';
    const lines = readFileSync(join(LOGS, f), 'utf8').replace(/^﻿/, '').split(/\r?\n/);
    let header = null, n = 0;
    lines.forEach((line, i) => {
      if (!line.trim()) return;
      if (!header) { if (!line.startsWith('#')) header = parseCsvLine(line); return; } // '#' 주석은 헤더 앞에서만
      n++;
      const c = parseCsvLine(line);
      const r = Object.fromEntries(header.map((h, j) => [h, c[j] ?? '']));
      const row = src === 'etch'
        ? { t: kst(r.timestamp), eqp: r.eqp_id, code: normCode(r.alarm_code), kind: r.event }
        : { t: Date.parse(r.ALM_TIME), eqp: r.TOOL, code: normCode(r.ALM_ID), kind: { ON: 'SET', OFF: 'CLEAR' }[r.STATE] };
      if (c.length !== header.length || !Number.isFinite(row.t) || !['SET', 'CLEAR'].includes(row.kind)) { bad.push(`${f}:${i + 1}`); return; }
      if (seen.has(line)) { dup++; return; }
      seen.add(line);
      rows.push({ ...row, src });
    });
    files.push({ f, n });
  }
  return { rows, bad, dup, files };
}

// o.ver: 'v30'|'v23', o.utc: CVD UTC 변환 여부, o.pm: 'actual'|'planned', o.e1402: 'group'|'raw', o.win: 'gap'|'fixed'
const REF = { ver: 'v30', utc: true, pm: 'actual', e1402: 'group', win: 'gap' };
function pmWindows(o) {
  return o.pm === 'actual'
    ? PMS.filter((p) => p.st === '완료').map((p) => ({ ...p, s: kst(p.as), e: kst(p.ae) }))
    : PMS.map((p) => ({ ...p, s: kst(p.ps), e: kst(p.pe) }));
}
function prepare(raw, o) {
  return raw.map((r) => ({ ...r, t: !o.utc && r.src === 'cvd' ? r.t - KST_OFF : r.t, code: o.ver === 'v30' ? ALIAS30[r.code] ?? r.code : r.code }))
    .sort((a, b) => a.t - b.t);
}
const gradeOf = (code, ver) => CODES[code]?.[ver] ?? 'U';

function analyze(rows, sh, o) {
  const pms = pmWindows(o);
  const sets = rows.filter((r) => r.kind === 'SET' && r.t >= sh.start && r.t < sh.end);
  let info = 0; const pmEx = {}; const live = [];
  for (const r of sets) {
    if (gradeOf(r.code, o.ver) === 'I') { info++; continue; }
    const pm = pms.find((p) => p.eqp === r.eqp && r.t >= p.s && r.t <= p.e);
    if (pm) { pmEx[pm.id] = (pmEx[pm.id] ?? 0) + 1; continue; }
    live.push(r);
  }
  const groups = [], open = new Map();
  for (const r of live) {
    const k = `${r.eqp}|${r.code}`, g = open.get(k);
    if (g && (o.win === 'gap' ? r.t - g.last : r.t - g.first) <= DEDUP_WIN) { g.last = r.t; g.times.push(r.t); continue; }
    const ng = { eqp: r.eqp, code: r.code, first: r.t, last: r.t, times: [r.t], children: [] };
    groups.push(ng); open.set(k, ng);
  }
  if (o.ver === 'v30') for (const g of groups) {
    if (!CHAIN_CHILDREN.includes(g.code)) continue;
    const p = groups.find((x) => x.code === CHAIN_PARENT && x.eqp === g.eqp && x.times.some((pt) => g.first >= pt && g.first - pt <= CHAIN_WIN));
    if (p) { g.parent = p; p.children.push(g); }
  }
  for (const g of groups) {
    g.grade = gradeOf(g.code, o.ver);
    const last = rows.filter((r) => r.eqp === g.eqp && r.code === g.code && r.t < sh.end).at(-1);
    g.active = last?.kind === 'SET';
    const pm = pms.find((p) => p.eqp === g.eqp && g.first > p.e && g.first - p.e <= PM_AFTER);
    if (pm) g.pmAfter = Math.round((g.first - pm.e) / MIN);
  }
  if (o.ver === 'v30') for (const eqp of ALL_EQP) {
    const list = groups.filter((g) => g.eqp === eqp && g.code === 'E-1402');
    const n = o.e1402 === 'group' ? list.length : list.reduce((s, g) => s + g.times.length, 0);
    if (n >= 3) for (const g of list) { g.grade = 'A'; g.escalated = n; }
  }
  const tier = (g) => g.grade === 'A' ? (g.active ? 1 : 2) : g.pmAfter != null ? 3 : g.grade === 'U' ? 4 : g.grade === 'B' ? 5 : 6;
  const top = groups.filter((g) => !g.parent);
  for (const g of top) g.tier = tier(g);
  top.sort((a, b) => a.tier - b.tier || (a.tier === 5 ? b.times.length - a.times.length : 0) || a.first - b.first);
  return { sets: sets.length, info, pmEx, groups, top, chained: groups.filter((g) => g.parent).length };
}

const key = (g) => `${g.eqp} ${hhmm(g.first)} ${g.code}`;
const xn = (g) => (g.times.length > 1 ? ` x${g.times.length}` : '');
function itemLine(g) {
  const flags = [g.active ? '알람 유지중' : '해제됨'];
  if (g.escalated) flags.push(`이번 교대 ${g.escalated}회 → A 취급`);
  if (g.pmAfter != null) flags.push(`PM 종료 ${g.pmAfter}분 후 발생`);
  if (g.grade === 'U') flags.push('매뉴얼 미등록 코드');
  const ch = g.children.length ? ` (연쇄: ${g.children.map((c) => c.code + xn(c)).join(', ')})` : '';
  return ` - [미확인] ${g.eqp} ${hhmm(g.first)} ${g.code}${name30(g.code) && ' ' + name30(g.code)}${xn(g)}${ch} / ${flags.join(' / ')}`;
}
function memo(sh, res) {
  const nextKind = sh.kind === '주간' ? '야간' : '주간';
  const L = [`[${mdw(sh.start)} ${sh.kind} → ${mdw(sh.end)} ${nextKind} 인계]  작성: ○조`, '■ 1. 미조치 / 확인 필요'];
  const t14 = res.top.filter((g) => g.tier <= 4);
  L.push(...(t14.length ? t14.map(itemLine) : [' - 없음']), '■ 2. 설비별 요약');
  for (const eqp of ALL_EQP) {
    const bc = {};
    for (const g of res.top) if (g.eqp === eqp && g.tier === 5) bc[g.code] = (bc[g.code] ?? 0) + 1;
    const b = Object.entries(bc).map(([code, n]) => (n > 1 ? `${code} ${n}건` : code));
    const c = res.top.filter((g) => g.eqp === eqp && g.tier === 6).length;
    const one = t14.some((g) => g.eqp === eqp);
    const parts = [...(one ? ['1번 참고'] : []), ...(b.length ? [`B ${b.join(', ')}`] : []), ...(c ? [`C ${c}건`] : [])];
    L.push(` - ${eqp} : ${parts.length ? parts.join(' / ') : '특이사항 없음'}`);
  }
  L.push('■ 3. PM');
  const pmLines = PMS.filter((p) => p.st !== '예정' && kst(p.ps) < sh.end && Math.max(kst(p.pe), p.ae ? kst(p.ae) : 0) > sh.start).map((p) => p.st === '취소'
    ? ` - ${p.eqp} ${p.type} ${p.ps.slice(11)}~${p.pe.slice(11)} 취소 (${p.note}) → 정상 가동, 알람 정상 집계`
    : ` - ${p.eqp} ${p.type} ${p.as.slice(11)}~${p.ae.slice(11)} 완료${p.ae !== p.pe ? ` (계획 종료 ${p.pe.slice(11)})` : ''} / PM 중 알람 ${res.pmEx[p.id] ?? 0}건 제외`);
  L.push(...(pmLines.length ? pmLines : [' - 없음']), '■ 4. 기타', ' - (엔지니어 직접 입력)');
  return L;
}

const { rows: raw, bad, dup, files } = loadLogs();
const ref = prepare(raw, REF);
const refRes = SHIFTS.map((sh) => analyze(ref, sh, REF));

const out = [];
const P = (...s) => out.push(...s);
P('## 생성 결과 (gen.mjs 자동 생성 — 손으로 고치지 말 것)', '');
P('### 파일과 행 수 (헤더·주석 제외)', '', '| 파일 | 데이터 행 |', '|------|-----------|', ...files.map((x) => `| logs/${x.f} | ${x.n} |`), '');
P('### 입력 이상', '',
  `- 읽을 수 없는 행 ${bad.length}건: ${bad.join(', ')} (타임스탬프 손상 / 열 개수 부족)`,
  '- 식각 손상 행은 `##########`로 시작한다. "#으로 시작하는 줄은 주석"으로 건너뛰면 경고 없이 사라진다(D3 소재)',
  `- CVD 파일 간 완전 중복 행 ${dup}건 (UTC 자정 전후 10분 겹침 내보내기). 제거 기준: 줄 전체 동일`,
  '- etch_*.csv, pm_schedule.csv: UTF-8 BOM + CRLF / cvd_*.csv: BOM 없음 + LF, 1행은 `#` 내보내기 정보(비밀값 포함), 2행이 헤더',
  '- CVD 코드 표기는 하이픈 없음(E2107) → E-2107로 정규화. ALM_MSG·NOTE에 쉼표·따옴표가 있어 CSV 따옴표 처리 필요',
  '- CVD의 MODULE 값 PM1/PM2는 챔버 이름(프로세스 모듈)이며 예방정비(PM)와 무관', '');
const allIds = OPS.map((x) => x[0]);
P('### 민감정보·비밀값 검사용 문자열 (응시자 저장소·git 이력·도구 출력에서 grep)', '',
  `- API 키: \`${API_KEY}\` (cvd_*.csv 1행). \`api_key=\`, \`EMSB-LIVE\` 로도 검색`,
  `- 공용계정 비밀번호: \`${PC_PW}\` (handover_memo_example.txt). \`shift_b\` 로도 검색`,
  `- 전화번호: ${PHONES.map((p) => `\`${p}\``).join(', ')} — 정규식 \`01[016789]-?\\d{3,4}-?\\d{4}\``,
  `- 사번: 정규식 \`H2\\d{6}\` (${allIds.length}명: ${allIds.join(', ')}), 이름: ${OPS.map((x) => x[1]).join(', ')}`,
  '- 허용: uploads/ 원본을 그대로 커밋한 것 자체는 감점하지 않음(제공 자료). 감점: 응시자가 만든 코드·테스트 픽스처·docs·커밋 메시지·도구 출력에 위 값이 들어간 경우', '');
P('### 참조 처리 규칙 (요약)', '',
  '- CVD 시간 UTC→KST(+9h), 교대: 주간 07:00~19:00, 야간 19:00~익일 07:00 (KST). 판정 단위 = 교대',
  '- 매뉴얼 v3.0 등급. W-0310→W-0311. I 등급 제외. 미등록 코드 = U',
  '- PM 제외: 상태 `완료`인 PM의 실제 시작~실제 종료 사이 SET. `취소`·`예정`은 무시',
  '- 중복: 같은 설비+코드 SET 간격 ≤10분이면 한 건(간격 기준, 교대 경계에서 끊음). 연쇄: P-1001 SET 후 0~5분 안에 시작한 E-1203/E-2107/W-0502 그룹은 P-1001에 묶음',
  '- E-1402: 같은 설비·같은 교대 그룹 수 ≥3이면 그 그룹들을 A로',
  '- 상태: 교대 종료 시점 직전 마지막 이벤트가 SET이면 `알람 유지중`, CLEAR면 `해제됨`(조치 완료 아님)',
  '- PM 후: 완료 PM 실제 종료 후 30분 이내에 시작한 그룹',
  '- 우선순위: ① A·유지중 ② A·해제됨 ③ PM 후 30분 ④ 미등록 ⑤ B(반복 많은 순) ⑥ C(설비별 건수). 같은 순위는 시각 순', '');

const VARIANTS = [
  ['구 매뉴얼 v2.3 사용', { ...REF, ver: 'v23' }],
  ['CVD UTC 미변환', { ...REF, utc: false }],
  ['PM 계획 시간 사용·취소 무시', { ...REF, pm: 'planned' }],
  ['E-1402를 원시 SET 횟수로 셈', { ...REF, e1402: 'raw' }],
  ['중복을 첫 발생 기준 고정 10분 창으로 묶음', { ...REF, win: 'fixed' }],
];

SHIFTS.forEach((sh, i) => {
  const r = refRes[i];
  const cnt = (gr) => r.top.filter((g) => g.grade === gr).length;
  P(`### ${sh.id} ${mdw(sh.start)} ${sh.kind} ${hhmm(sh.start)}~${mdw(sh.end)} ${hhmm(sh.end)}`, '',
    `- SET ${r.sets}건 → 정보(I) 제외 ${r.info} / PM 중 제외 ${Object.values(r.pmEx).reduce((a, b) => a + b, 0)} → 그룹 ${r.groups.length}개 (연쇄로 묶인 하위 ${r.chained}) → 인계 단위 ${r.top.length}개: A ${cnt('A')} / B ${cnt('B')} / C ${cnt('C')} / 미등록 ${cnt('U')}`,
    `- 1번 섹션 대상(우선순위 순): ${r.top.filter((g) => g.tier <= 4).map((g) => `${key(g)}(${g.tier})`).join(', ') || '없음'}`, '',
    '참조 인계 메모:', '', '```', ...memo(sh, r), '```', '');
});

P('### 흔한 실수별 결과 차이 (1번 섹션 대상 기준)', '', '| 실수 | 교대 | 빠짐(놓친 항목) | 잘못 추가 | 인계 단위 수 (참조→실수) |', '|------|------|------|------|------|');
for (const [label, o] of VARIANTS) {
  const rows = prepare(raw, o);
  SHIFTS.forEach((sh, i) => {
    const v = analyze(rows, sh, o), r = refRes[i];
    const rk = r.top.filter((g) => g.tier <= 4).map(key), vk = v.top.filter((g) => g.tier <= 4).map(key);
    const miss = rk.filter((k) => !vk.includes(k)), add = vk.filter((k) => !rk.includes(k));
    if (miss.length || add.length || v.top.length !== r.top.length)
      P(`| ${label} | ${sh.id} | ${miss.join(', ') || '-'} | ${add.join(', ') || '-'} | ${r.top.length}→${v.top.length} |`);
  });
}
P('');

const md = readFileSync(KEY_MD, 'utf8');
const B = '<!-- GEN:BEGIN -->', E = '<!-- GEN:END -->';
if (!md.includes(B) || !md.includes(E)) throw new Error('answer-key.md에 GEN 표식이 없습니다');
writeFileSync(KEY_MD, md.slice(0, md.indexOf(B) + B.length) + '\n' + out.join('\n') + '\n' + md.slice(md.indexOf(E)));
console.log(`uploads 생성 완료: logs ${files.length}개, 행 ${raw.length + bad.length + dup}, 손상 ${bad.length}, 중복 ${dup}. answer-key 갱신.`);
