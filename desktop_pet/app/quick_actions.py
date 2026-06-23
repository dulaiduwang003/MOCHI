# author: bdth
# email: 2074055628@qq.com
# 顺手功能mixin 划词提问 快捷润色 剪贴板搭把手

from __future__ import annotations

from PySide6.QtCore import QTimer

from desktop_pet import i18n


class QuickActionsMixin:
    """划词和剪贴板相关的快捷动作"""

    def _ask_selection(self) -> None:
        if not self._shown:
            self._power_on()
        # 原剪贴板用闭包贯穿整条链不放共享属性 交错触发时共享 _saved_clip 会互相覆盖弄丢
        saved = self._app.clipboard().text()
        try:
            import pyautogui
            # 先松开残留的修饰键再模拟复制
            for mod in ("alt", "ctrl", "shift"):
                pyautogui.keyUp(mod)
        except Exception:
            self._summon()
            return
        QTimer.singleShot(70, lambda: self._copy_selection(saved))

    def _copy_selection(self, saved: str) -> None:
        try:
            import pyautogui
            pyautogui.hotkey("ctrl", "c")
        except Exception:
            self._summon()
            return
        QTimer.singleShot(200, lambda: self._after_copy(saved))

    def _after_copy(self, saved: str) -> None:
        text = self._app.clipboard().text().strip()
        self._summon()
        if not text or text == saved.strip():   # 剪贴板没变当作无选区
            return
        self._app.clipboard().setText(saved)     # 还回原剪贴板
        snippet = text if len(text) <= 500 else text[:500] + "…"
        self._input.setText(f"关于这个：{snippet}")
        self._input.setFocus()

    def _quick_rewrite(self) -> None:
        if not self._shown:
            self._power_on()
        saved = self._app.clipboard().text()
        try:
            import pyautogui
            for mod in ("alt", "ctrl", "shift"):
                pyautogui.keyUp(mod)
        except Exception:
            return
        QTimer.singleShot(70, lambda: self._quick_copy(saved))

    def _quick_copy(self, saved: str) -> None:
        try:
            import pyautogui
            pyautogui.hotkey("ctrl", "c")
        except Exception:
            return
        QTimer.singleShot(200, lambda: self._quick_after_copy(saved))

    def _quick_after_copy(self, saved: str) -> None:
        text = self._app.clipboard().text().strip()
        if not self._pet.isVisible():
            self._pet.setVisible(True)
        self._pet.wake()
        if not text or text == saved.strip():
            self._thought.pop(i18n.t("quick_noselect"), self._pet)
            return
        self._thought.show_step(i18n.t("quick_working"), self._pet)
        self.request_rewrite.emit(text)

    def _on_rewrite_done(self, result: str) -> None:
        if not result.strip():
            self._thought.pop(i18n.t("quick_failed"), self._pet)
            return
        self._app.clipboard().setText(result)
        if self._settings.quick_paste_back:
            try:
                import pyautogui
                QTimer.singleShot(60, lambda: pyautogui.hotkey("ctrl", "v"))
            except Exception:
                pass
        self._thought.pop(i18n.t("quick_done"), self._pet)
