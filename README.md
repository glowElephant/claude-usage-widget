# Claude Usage Widget 🤖

Windows 데스크톱 위젯 - 로컬 기반 Claude Code 사용량 모니터링

![Python](https://img.shields.io/badge/Python-3.8+-blue.svg)
![Platform](https://img.shields.io/badge/Platform-Windows-lightgrey.svg)
![License](https://img.shields.io/badge/License-MIT-green.svg)

## ✨ 기능

- **5시간 세션 사용량** - 롤링 윈도우 기준 토큰 사용량 표시
- **주간 사용량** - 이번 주 월요일부터의 총 사용량
- **플랜 자동 인식** - Pro / Max5 / Max20 자동 감지
- **항상 위에 표시** - 다른 창 위에 떠있는 위젯
- **드래그 이동** - 원하는 위치로 이동 가능
- **자동 갱신** - 30초마다 자동 업데이트
- **시작 프로그램 등록** - 부팅 시 자동 실행

## 📸 스크린샷

```
┌─────────────────────────────┐
│ 🤖 Claude MAX5 ⚡         ✕ │
│ 여유롭네요 ☕               │
│                             │
│ ⏱️ Session          12.5%  │
│ 🔄 롤링 5시간 윈도우        │
│ ████░░░░░░░░░░░░░░░░░░░░░  │
│                             │
│ 📅 Weekly            8.2%  │
│ 🗓️ 5일 12시간 후 리셋      │
│ ██░░░░░░░░░░░░░░░░░░░░░░░  │
│                             │
│ 마지막 업데이트: 09:15:30   │
└─────────────────────────────┘
```

## 🚀 설치 및 실행

```bash
# Python 3.8+ 필요 (tkinter 포함)
git clone https://github.com/yourusername/claude-usage-widget.git
cd claude-usage-widget

# 실행
python claude_usage_widget.py

# 콘솔 창 없이 실행
pythonw claude_usage_widget.py
```

## 🖱️ 사용법

- **드래그** - 위젯을 원하는 위치로 이동
- **더블클릭** - 사용량 새로고침
- **우클릭** - 컨텍스트 메뉴 (시작프로그램 등록/해제, 종료)

## ⚠️ 주의사항

- **로컬 데이터 기반**: `~/.claude/projects/` 폴더의 JSONL 파일을 분석합니다
- **다중 PC 사용 시**: 각 PC의 로컬 데이터만 계산되므로 실제 서버 사용량과 다를 수 있습니다
- **한도 추정치**: 플랜별 한도는 공식 발표 기준 추정치입니다

## 📊 플랜별 한도 (추정)

| 플랜 | 5시간 세션 | 주간 한도 |
|------|-----------|----------|
| Pro | ~44,000 | ~300,000 |
| Max5 | ~88,000 | ~600,000 |
| Max20 | ~220,000 | ~1,500,000 |

## 🎨 상태별 색상

| 사용량 | 색상 | 상태 |
|--------|------|------|
| 0-40% | 🟢 초록 | 여유 |
| 40-70% | 🟠 주황 | 보통 |
| 70-90% | 🔴 빨강 | 주의 |
| 90-100% | 💗 핑크 | 위험 |

## 📁 파일 구조

```
claude-usage-widget/
├── claude_usage_widget.py  # 메인 위젯 코드
├── README.md               # 이 파일
├── LICENSE                 # MIT 라이선스
└── .gitignore
```

## 🔧 설정 경로

- 플랜 정보: `~/.claude/.credentials.json`
- 사용량 데이터: `~/.claude/projects/**/*.jsonl`

## 📜 라이선스

MIT License

---

Made with ☕ by Claude & Human
