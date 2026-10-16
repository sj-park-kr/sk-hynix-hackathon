# SK하이닉스 해커톤(AI 역량 검사) 대비 — 1차 예선

AI 역량 검사 형식(자료 기반 문제 + AI 사용 횟수·글자수 제한 + 결과·과정 평가)을 연습하는 저장소입니다. 문제의 회사·인물·수치는 모두 가상 데이터입니다.

## 구성

| 경로 | 내용 |
|---|---|
| `index.html` | 연습실 페이지(빌드 결과, GitHub Pages가 이 파일을 띄움) |
| `lab/build.py` | `lab/src` + `lab/problems` → `index.html` 빌드 |
| `lab/src/` | 페이지 소스(`head.html`: 스타일, `body.html`: 화면·스크립트) |
| `lab/problems/` | 문제 데이터와 생성기(`snack`, `fai`, `hbm`, `literacy`) |
| `playbook/` | 시험 중 참고용 실전 플레이북 |
| `prompts/templates.md` | 문항형 풀이·검증, 보고서형 계획 프롬프트 템플릿 |

## 연습 문제

- **실전 과제**: 간식 행사 메뉴 집계(객관식 4), FAI 라이선스 운영 분석(객관식 1 · 주관식 3), GlobalCart 입점 검수 감사(주관식 4), 해외 출장비 정산 감사(객관식 1 · 주관식 3), HBM 수율 원인 분석(서술형)
- **AI 리터러시 문제집**: 세트 A(RAG·프롬프트), B(보안·개인정보), C(규제·윤리·운영), D(에이전트·자동화), E(데이터 분석·검증), F(업무 활용 실전) 각 10문항 × 2세트(A~F, A-2~F-2)

## AI 기능

AI 질문(10회·1,000자 제한)과 서술형 채점은 claude.ai 아티팩트 버전에서만 동작합니다.
GitHub Pages 버전에서는 문제 풀이, 파일 보기, 객관식·주관식 채점만 됩니다.

- claude.ai 버전: https://claude.ai/artifact/GHXmjKkiBTeCn27xj9poNN

## 빌드

```bash
python3 lab/build.py            # index.html 갱신
python3 lab/problems/fai/gen.py # 문제 데이터 재생성(결정적, 같은 결과)
```

## GitHub Pages

Settings → Pages → Build and deployment → Source: **Deploy from a branch**, Branch: **1차예선** / **(root)** 선택.
