# author: bdth
# email: 2074055628@qq.com
# 自主行为mixin 在场感知 提醒 远程信箱 定时看屏 窗台蹲守

from __future__ import annotations

import threading
from datetime import datetime


from desktop_pet import i18n, presence
from desktop_pet.reminders import reminders


_AWAY_S = 150.0
_AWAY_NIGHT_S = 75.0


class AutonomyMixin:
    """不靠用户输入也会动起来的那部分"""

    def _on_presence(self) -> None:
        try:
            self._drain_pending_bg()
            self._poll_presence()
        except Exception:
            pass

    def _poll_presence(self) -> None:
        if self._engaged() or not self._pet.isVisible():   # 忙时不准睡
            return
        away = _AWAY_NIGHT_S if self._is_night() else _AWAY_S
        if presence.idle_seconds() >= away:
            if not self._pet.is_asleep:
                self._pet.fall_asleep()
        elif self._pet.is_asleep and not self._pet.is_catnapping:
            self._wake()

    def _check_reminders(self) -> None:
        try:
            self._drain_reminders()
        except Exception:
            pass

    @staticmethod
    def _foreground_is_fullscreen() -> bool:
        try:
            import win32api
            import win32gui
            hwnd = win32gui.GetForegroundWindow()
            if not hwnd:
                return False
            cls = win32gui.GetClassName(hwnd)
            if cls in ("Progman", "WorkerW", "Shell_TrayWnd", "Button"):
                return False   # 桌面任务栏不算全屏应用
            left, top, right, bottom = win32gui.GetWindowRect(hwnd)
            sw = win32api.GetSystemMetrics(0)
            sh = win32api.GetSystemMetrics(1)
            return (right - left) >= sw - 2 and (bottom - top) >= sh - 2   # 留2px容差
        except Exception:
            return False

    def _in_scene(self) -> bool:
        return (self._shown and self._pet.isVisible()
                and not self._pet.is_asleep and not self._foreground_is_fullscreen())

    def _drain_reminders(self) -> None:
        # 不在场时只取提醒 do类任务压着等在场再领
        in_scene = self._in_scene()
        due = reminders.due(datetime.now(), take_do=in_scene)
        if not due:
            return
        says = [r.what for r in due if r.kind != "do"]
        tasks = [r.what for r in due if r.kind == "do"]
        if says:
            text = "；".join(says)
            if not self._shown or not self._pet.isVisible() or self._foreground_is_fullscreen():
                self._tray.notify(i18n.t("tray_tooltip"), text)
            else:
                self._pet.wake()
                self.request_reminder.emit(text)
        if tasks:
            self._timed_queue.extend(tasks)
            self._drain_timed()

    def _drain_timed(self) -> None:
        if self._timed_inflight or not self._timed_queue:
            return
        if self._engaged() or self._cancelling or not self._in_scene():
            return
        task = self._timed_queue.pop(0)
        self._timed_inflight = True
        self._inflight_timed = task
        self._pet.wake()
        self.request_timed_task.emit(task)

    def _requeue_timed(self) -> None:
        """没跑完的定时任务塞回reminders"""
        now = datetime.now()
        pending = list(self._timed_queue)
        if self._inflight_timed:   # 正在跑的排最前
            pending.insert(0, self._inflight_timed)
        for task in pending:
            try:
                reminders.add(now, task, kind="do")
            except Exception:
                pass
        self._timed_queue.clear()
        self._inflight_timed = None
        self._timed_inflight = False

    def _on_wants_travel(self) -> None:
        """虫洞穿越前的全局闸门"""
        if self._engaged() or not self._pet.isVisible() or self._pet.is_asleep:
            return
        self._pet.start_wormhole()

    def _check_watch(self) -> None:
        try:
            self._maybe_watch()
        except Exception:
            pass

    def _maybe_watch(self) -> None:
        from desktop_pet.watcher import watcher
        if not self._settings.allow_control:
            return
        if not self._shown or not self._pet.isVisible() or self._pet.is_asleep:
            return
        if self._watch_inflight or self._engaged():
            return
        focus = watcher.due(datetime.now())
        if not focus:
            return
        self._watch_inflight = True
        self._pet.wake()
        self.request_analyze.emit(focus)

    def _on_analysis(self, text: str) -> None:
        self._watch_inflight = False
        from desktop_pet.watcher import watcher, WATCH_FAIL
        if text == WATCH_FAIL:
            watcher.retry_soon()
            return
        if not text or not text.strip():
            return
        if (not watcher.enabled or not self._shown or not self._pet.isVisible()
                or self._pet.is_asleep or self._foreground_busy()):
            return
        self._on_reply(text)

    @staticmethod
    def _is_night() -> bool:
        hour = datetime.now().hour
        return hour >= 23 or hour < 6
