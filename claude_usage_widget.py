"""
Claude Code Usage Widget 🤖
Windows 데스크톱 위젯 - 로컬 기반 Claude 사용량 모니터링
- 항상 상단 표시 (ㄹㅇ 진짜 항상)
- 시작 프로그램 자동 등록
- 30초마다 갱신 (딱 화장실 다녀올 시간)
"""

import json
import os
import sys
import tkinter as tk
from tkinter import ttk, messagebox
from datetime import datetime, timedelta, timezone
from pathlib import Path
import winreg
import ctypes
import random


class ClaudeUsageWidget:
    # 플랜별 5시간 세션 한도 (input + output tokens 기준)
    PLAN_LIMITS = {
        "pro": 55000,       # ~55K
        "max": 110000,      # ~110K
        "max_5x": 110000,   # ~110K
        "max_20x": 275000,  # ~275K
    }

    # 플랜별 주간 한도 (input + output tokens 기준)
    WEEKLY_LIMITS = {
        "pro": 190000,      # ~190K
        "max": 380000,      # ~380K
        "max_5x": 380000,   # ~380K
        "max_20x": 950000,  # ~950K
    }

    # MZ스러운 상태 메시지들
    STATUS_MESSAGES = {
        "low": [
            "여유롭네요 ☕",
            "아직 괜찮아요 😎",
            "토큰 부자 💰",
            "맘껏 쓰세요 🚀",
            "Claude가 기다리는 중 🙋",
        ],
        "medium": [
            "슬슬 아껴야 할 듯? 🤔",
            "절반 왔어요 ⚡",
            "반타작 완료 📊",
            "적당히 쓰는 중 👍",
            "아직은 괜찮... 아마도? 😅",
        ],
        "high": [
            "토큰이 녹고 있어요 🫠",
            "거의 다 썼어요! 😱",
            "Claude 쉬고 싶대요 😴",
            "지갑이 울고 있어요 💸",
            "잠시 쉬어가는 건 어떨까요? 🧘",
        ],
        "critical": [
            "🚨 비상! 비상! 🚨",
            "토큰 바닥났어요 💀",
            "Claude: ㅂㅂ 나 간다 👋",
            "리셋까지 버텨야 해요 😤",
            "개발자의 눈물 한 방울 🥲",
        ]
    }

    APP_NAME = "ClaudeUsageWidget"

    def __init__(self):
        self.claude_dir = Path.home() / ".claude"
        self.projects_dir = self.claude_dir / "projects"

        # 플랜 정보 로드
        self.plan_type, self.rate_tier = self.get_plan_info()
        self.session_limit = self.get_session_limit()
        self.weekly_limit = self.get_weekly_limit()

        # UI 초기화
        self.root = tk.Tk()
        self.is_visible = True
        self.setup_window()
        self.create_widgets()
        self.create_context_menu()

        # 시작 프로그램 등록 확인
        if not self.is_startup_registered():
            self.register_startup()

        # 초기 업데이트 및 자동 갱신 시작
        self.update_usage()
        self.schedule_update()

    def get_plan_info(self):
        """credentials.json에서 플랜 정보 읽기"""
        credentials_path = self.claude_dir / ".credentials.json"
        try:
            with open(credentials_path, "r", encoding="utf-8") as f:
                data = json.load(f)
                oauth = data.get("claudeAiOauth", {})
                plan_type = oauth.get("subscriptionType", "pro")
                rate_tier = oauth.get("rateLimitTier", "")
                return plan_type, rate_tier
        except Exception:
            return "pro", ""

    def get_session_limit(self):
        """플랜에 따른 5시간 세션 한도 반환"""
        if "max_20" in self.rate_tier or "20x" in self.rate_tier:
            return self.PLAN_LIMITS["max_20x"]
        elif "max_5" in self.rate_tier or "5x" in self.rate_tier or self.plan_type == "max":
            return self.PLAN_LIMITS["max_5x"]
        return self.PLAN_LIMITS["pro"]

    def get_weekly_limit(self):
        """플랜에 따른 주간 한도 반환"""
        if "max_20" in self.rate_tier or "20x" in self.rate_tier:
            return self.WEEKLY_LIMITS["max_20x"]
        elif "max_5" in self.rate_tier or "5x" in self.rate_tier or self.plan_type == "max":
            return self.WEEKLY_LIMITS["max_5x"]
        return self.WEEKLY_LIMITS["pro"]

    def get_plan_display_name(self):
        """표시용 플랜 이름"""
        if "max_20" in self.rate_tier or "20x" in self.rate_tier:
            return "MAX20 🔥"
        elif "max_5" in self.rate_tier or "5x" in self.rate_tier or self.plan_type == "max":
            return "MAX5 ⚡"
        return "PRO ✨"

    def get_status_message(self, percent):
        """퍼센트에 따른 상태 메시지 반환"""
        if percent >= 90:
            return random.choice(self.STATUS_MESSAGES["critical"])
        elif percent >= 70:
            return random.choice(self.STATUS_MESSAGES["high"])
        elif percent >= 40:
            return random.choice(self.STATUS_MESSAGES["medium"])
        else:
            return random.choice(self.STATUS_MESSAGES["low"])

    def setup_window(self):
        """윈도우 설정"""
        self.root.title("Claude Usage")
        self.root.attributes("-topmost", True)
        self.root.resizable(False, False)
        self.root.overrideredirect(True)

        # 창 크기 및 위치 (우측 상단)
        width, height = 280, 200
        screen_width = self.root.winfo_screenwidth()
        x = screen_width - width - 20
        y = 20
        self.root.geometry(f"{width}x{height}+{x}+{y}")

        # 스타일
        self.root.configure(bg="#1a1b26")

        # 투명도
        self.root.attributes("-alpha", 0.95)

        # 드래그로 이동 가능하게
        self.root.bind("<Button-1>", self.start_move)
        self.root.bind("<B1-Motion>", self.on_move)
        self.root.bind("<Button-3>", self.show_context_menu)
        self.root.bind("<Double-Button-1>", lambda e: self.update_usage())  # 더블클릭으로 새로고침

    def start_move(self, event):
        self.x = event.x
        self.y = event.y

    def on_move(self, event):
        deltax = event.x - self.x
        deltay = event.y - self.y
        x = self.root.winfo_x() + deltax
        y = self.root.winfo_y() + deltay
        self.root.geometry(f"+{x}+{y}")

    def create_context_menu(self):
        """우클릭 컨텍스트 메뉴"""
        self.context_menu = tk.Menu(self.root, tearoff=0, bg="#1a1b26", fg="#c0caf5")
        self.context_menu.add_command(label="🔄 새로고침", command=self.update_usage)
        self.context_menu.add_separator()
        self.context_menu.add_command(label="🚀 시작프로그램 등록", command=self.register_startup)
        self.context_menu.add_command(label="🗑️ 시작프로그램 해제", command=self.unregister_startup)
        self.context_menu.add_separator()
        self.context_menu.add_command(label="👋 종료", command=self.quit_app)

    def show_context_menu(self, event):
        """우클릭 메뉴 표시"""
        self.context_menu.tk_popup(event.x_root, event.y_root)

    def create_widgets(self):
        """UI 위젯 생성"""
        main_frame = tk.Frame(self.root, bg="#1a1b26", padx=14, pady=12)
        main_frame.pack(fill="both", expand=True)

        # 타이틀 바
        title_frame = tk.Frame(main_frame, bg="#1a1b26")
        title_frame.pack(fill="x", pady=(0, 6))

        title = tk.Label(
            title_frame,
            text=f"🤖 Claude {self.get_plan_display_name()}",
            font=("Segoe UI Emoji", 11, "bold"),
            fg="#c0caf5",
            bg="#1a1b26"
        )
        title.pack(side="left")

        # 닫기 버튼
        close_btn = tk.Label(
            title_frame,
            text="✕",
            font=("Segoe UI", 10),
            fg="#565f89",
            bg="#1a1b26",
            cursor="hand2"
        )
        close_btn.pack(side="right", padx=(5, 0))
        close_btn.bind("<Button-1>", lambda e: self.quit_app())
        close_btn.bind("<Enter>", lambda e: close_btn.config(fg="#f7768e"))
        close_btn.bind("<Leave>", lambda e: close_btn.config(fg="#565f89"))

        # 상태 메시지
        self.status_label = tk.Label(
            main_frame,
            text="로딩 중... 🔄",
            font=("Segoe UI Emoji", 9),
            fg="#7aa2f7",
            bg="#1a1b26"
        )
        self.status_label.pack(anchor="w", pady=(0, 8))

        # 현재 세션 (5시간)
        self.session_frame = self.create_usage_section(
            main_frame,
            "⏱️ Session",
            "5시간 롤링"
        )

        # 주간 한도
        self.weekly_frame = self.create_usage_section(
            main_frame,
            "📅 Weekly",
            "주간 사용량"
        )

        # 마지막 업데이트 시간
        self.update_label = tk.Label(
            main_frame,
            text="",
            font=("Segoe UI", 7),
            fg="#414868",
            bg="#1a1b26"
        )
        self.update_label.pack(pady=(6, 0))

    def create_usage_section(self, parent, title, subtitle):
        """사용량 섹션 생성"""
        frame = tk.Frame(parent, bg="#1a1b26")
        frame.pack(fill="x", pady=3)

        # 타이틀 행
        title_row = tk.Frame(frame, bg="#1a1b26")
        title_row.pack(fill="x")

        title_label = tk.Label(
            title_row,
            text=title,
            font=("Segoe UI Emoji", 9),
            fg="#a9b1d6",
            bg="#1a1b26"
        )
        title_label.pack(side="left")

        percent_label = tk.Label(
            title_row,
            text="0%",
            font=("Segoe UI", 9, "bold"),
            fg="#9ece6a",
            bg="#1a1b26"
        )
        percent_label.pack(side="right")

        # 서브타이틀
        subtitle_label = tk.Label(
            frame,
            text=subtitle,
            font=("Segoe UI", 7),
            fg="#414868",
            bg="#1a1b26"
        )
        subtitle_label.pack(anchor="w")

        # 프로그레스 바 컨테이너 (둥근 모서리 효과)
        progress_container = tk.Frame(frame, bg="#24283b", height=8)
        progress_container.pack(fill="x", pady=(3, 0))
        progress_container.pack_propagate(False)

        # 프로그레스 바
        progress_bar = tk.Frame(progress_container, bg="#9ece6a", height=8)
        progress_bar.place(relwidth=0, relheight=1)

        return {
            "percent_label": percent_label,
            "subtitle_label": subtitle_label,
            "progress_bar": progress_bar
        }

    def get_tokens_from_jsonl(self, filepath, since_time=None, msg_tokens=None):
        """JSONL 파일에서 토큰 사용량 추출 (메시지 ID 기준 중복 제거)"""
        if msg_tokens is None:
            msg_tokens = {}

        try:
            with open(filepath, "r", encoding="utf-8") as f:
                for line in f:
                    try:
                        data = json.loads(line.strip())

                        # 타임스탬프 필터링
                        if since_time:
                            timestamp_str = data.get("timestamp", "")
                            if timestamp_str:
                                try:
                                    ts = datetime.fromisoformat(timestamp_str.replace("Z", "+00:00"))
                                    if ts.replace(tzinfo=None) < since_time:
                                        continue
                                except:
                                    pass

                        # 메시지에서 usage 추출
                        message = data.get("message", {})
                        usage = message.get("usage", {})

                        if usage:
                            # Claude Code 사용량 = input + output tokens
                            output_tokens = usage.get("output_tokens", 0)
                            input_tokens = usage.get("input_tokens", 0)
                            total_tokens = output_tokens + input_tokens
                            msg_id = message.get("id", "")

                            # 메시지 ID가 있으면 중복 제거 (최대값만 저장)
                            if msg_id:
                                if msg_id not in msg_tokens or msg_tokens[msg_id] < total_tokens:
                                    msg_tokens[msg_id] = total_tokens
                            else:
                                # ID 없는 메시지는 고유 키 생성
                                unique_key = f"{filepath}_{data.get('uuid', '')}"
                                if unique_key not in msg_tokens:
                                    msg_tokens[unique_key] = total_tokens
                    except json.JSONDecodeError:
                        continue
        except Exception:
            pass
        return msg_tokens

    def get_usage_since(self, hours=5):
        """특정 시간 이후의 사용량 계산 (중복 제거)"""
        # UTC 기준으로 계산 (jsonl 타임스탬프가 UTC)
        since_time = datetime.now(timezone.utc).replace(tzinfo=None) - timedelta(hours=hours)
        msg_tokens = {}  # 전체 파일에서 메시지 ID 중복 제거

        if not self.projects_dir.exists():
            return 0

        for jsonl_file in self.projects_dir.rglob("*.jsonl"):
            try:
                mtime = datetime.fromtimestamp(jsonl_file.stat().st_mtime)
                if mtime < since_time:
                    continue
                msg_tokens = self.get_tokens_from_jsonl(jsonl_file, since_time, msg_tokens)
            except:
                continue

        return sum(msg_tokens.values())

    def get_weekly_usage(self):
        """이번 주 월요일부터의 사용량 계산 (중복 제거)"""
        # UTC 기준으로 계산 (jsonl 타임스탬프가 UTC)
        now = datetime.now(timezone.utc).replace(tzinfo=None)
        monday = now - timedelta(days=now.weekday())
        monday = monday.replace(hour=0, minute=0, second=0, microsecond=0)

        msg_tokens = {}  # 전체 파일에서 메시지 ID 중복 제거

        if not self.projects_dir.exists():
            return 0

        for jsonl_file in self.projects_dir.rglob("*.jsonl"):
            try:
                mtime = datetime.fromtimestamp(jsonl_file.stat().st_mtime)
                if mtime < monday:
                    continue
                msg_tokens = self.get_tokens_from_jsonl(jsonl_file, monday, msg_tokens)
            except:
                continue

        return sum(msg_tokens.values())

    def get_first_message_time(self):
        """최근 5시간 내 첫 번째 메시지 시간 찾기"""
        five_hours_ago = datetime.now(timezone.utc).replace(tzinfo=None) - timedelta(hours=5)
        first_time = None

        if not self.projects_dir.exists():
            return None

        for jsonl_file in self.projects_dir.rglob("*.jsonl"):
            try:
                mtime = datetime.fromtimestamp(jsonl_file.stat().st_mtime)
                if mtime < five_hours_ago:
                    continue

                with open(jsonl_file, "r", encoding="utf-8") as f:
                    for line in f:
                        try:
                            data = json.loads(line.strip())
                            timestamp_str = data.get("timestamp", "")
                            if timestamp_str:
                                ts = datetime.fromisoformat(timestamp_str.replace("Z", "+00:00")).replace(tzinfo=None)
                                if ts >= five_hours_ago:
                                    if first_time is None or ts < first_time:
                                        first_time = ts
                                    break  # 파일 내 첫 번째만 확인
                        except:
                            continue
            except:
                continue

        return first_time

    def get_session_reset_str(self):
        """5시간 롤링 윈도우 리셋 시간"""
        first_time = self.get_first_message_time()
        if first_time is None:
            return "🔄 세션 없음"

        # 첫 메시지 + 5시간 = 리셋 시간
        reset_time = first_time + timedelta(hours=5)
        now = datetime.now(timezone.utc).replace(tzinfo=None)
        delta = reset_time - now

        if delta.total_seconds() <= 0:
            return "🔄 곧 리셋"

        hours = int(delta.total_seconds() // 3600)
        minutes = int((delta.total_seconds() % 3600) // 60)

        return f"🔄 {hours}시간 {minutes}분 후 리셋"

    def get_weekly_reset_str(self):
        """주간 리셋 시간 문자열"""
        now = datetime.now()
        days_until_monday = (7 - now.weekday()) % 7
        if days_until_monday == 0 and now.hour >= 0:
            days_until_monday = 7
        next_monday = now + timedelta(days=days_until_monday)
        next_monday = next_monday.replace(hour=0, minute=0, second=0, microsecond=0)

        delta = next_monday - now
        days = delta.days
        hours = delta.seconds // 3600

        if days > 0:
            return f"🗓️ {days}일 {hours}시간 후 리셋"
        else:
            return f"🗓️ {hours}시간 후 리셋 (곧이다!)"

    def update_usage(self):
        """사용량 업데이트"""
        try:
            # 5시간 세션 사용량
            session_tokens = self.get_usage_since(5)
            session_percent = min(100, (session_tokens / self.session_limit) * 100)

            # 주간 사용량
            weekly_tokens = self.get_weekly_usage()
            weekly_percent = min(100, (weekly_tokens / self.weekly_limit) * 100)

            # 상태 메시지 업데이트 (더 높은 퍼센트 기준)
            max_percent = max(session_percent, weekly_percent)
            self.status_label.config(text=self.get_status_message(max_percent))

            # UI 업데이트 - 세션
            self.update_section(
                self.session_frame,
                session_percent,
                self.get_session_reset_str()
            )

            # UI 업데이트 - 주간
            self.update_section(
                self.weekly_frame,
                weekly_percent,
                self.get_weekly_reset_str()
            )

            # 마지막 업데이트 시간
            now = datetime.now()
            self.update_label.config(
                text=f"마지막 업데이트: {now.strftime('%H:%M:%S')} | 더블클릭하면 새로고침 👆"
            )
        except Exception as e:
            self.status_label.config(text=f"앗! 에러 발생 😵: {str(e)[:15]}")

    def update_section(self, section, percent, subtitle):
        """섹션 UI 업데이트"""
        # 퍼센트에 따른 색상 (Tokyo Night 테마)
        if percent < 40:
            color = "#9ece6a"  # 초록
        elif percent < 70:
            color = "#e0af68"  # 주황
        elif percent < 90:
            color = "#f7768e"  # 빨강
        else:
            color = "#ff007c"  # 핫핑크 (위험!)

        section["percent_label"].config(text=f"{percent:.1f}%", fg=color)
        section["subtitle_label"].config(text=subtitle)
        section["progress_bar"].config(bg=color)
        section["progress_bar"].place(relwidth=percent/100, relheight=1)

    def schedule_update(self):
        """30초마다 자동 업데이트"""
        self.root.after(30000, self.auto_update)

    def auto_update(self):
        """자동 업데이트 실행"""
        self.update_usage()
        self.schedule_update()

    def is_startup_registered(self):
        """시작 프로그램 등록 여부 확인"""
        try:
            key = winreg.OpenKey(
                winreg.HKEY_CURRENT_USER,
                r"Software\Microsoft\Windows\CurrentVersion\Run",
                0, winreg.KEY_READ
            )
            try:
                winreg.QueryValueEx(key, self.APP_NAME)
                return True
            except WindowsError:
                return False
            finally:
                winreg.CloseKey(key)
        except:
            return False

    def register_startup(self):
        """시작 프로그램에 등록"""
        try:
            key = winreg.OpenKey(
                winreg.HKEY_CURRENT_USER,
                r"Software\Microsoft\Windows\CurrentVersion\Run",
                0, winreg.KEY_SET_VALUE
            )

            # exe로 실행 중이면 exe 경로 사용, 아니면 pythonw + script
            if getattr(sys, 'frozen', False):
                # PyInstaller exe로 실행 중
                command = f'"{sys.executable}"'
            else:
                # Python 스크립트로 실행 중
                python_path = sys.executable
                if python_path.endswith("python.exe"):
                    pythonw_path = python_path.replace("python.exe", "pythonw.exe")
                    if os.path.exists(pythonw_path):
                        python_path = pythonw_path
                script_path = os.path.abspath(__file__)
                command = f'"{python_path}" "{script_path}"'

            winreg.SetValueEx(key, self.APP_NAME, 0, winreg.REG_SZ, command)
            winreg.CloseKey(key)

            self.status_label.config(text="✅ 시작프로그램 등록 완료!")
        except Exception as e:
            self.status_label.config(text=f"❌ 등록 실패: {str(e)[:15]}")

    def unregister_startup(self):
        """시작 프로그램에서 제거"""
        try:
            key = winreg.OpenKey(
                winreg.HKEY_CURRENT_USER,
                r"Software\Microsoft\Windows\CurrentVersion\Run",
                0, winreg.KEY_SET_VALUE
            )
            winreg.DeleteValue(key, self.APP_NAME)
            winreg.CloseKey(key)

            self.status_label.config(text="🗑️ 시작프로그램 해제 완료!")
        except Exception as e:
            self.status_label.config(text=f"❌ 해제 실패: {str(e)[:15]}")

    def quit_app(self):
        """앱 종료"""
        self.root.destroy()

    def run(self):
        """위젯 실행"""
        self.root.mainloop()


if __name__ == "__main__":
    widget = ClaudeUsageWidget()
    widget.run()
