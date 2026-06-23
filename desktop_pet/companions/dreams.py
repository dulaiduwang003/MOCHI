# author: bdth
# email: 2074055628@qq.com
# 夜间整理伴生 主人离开它睡着够久 后台把同主题零碎记忆揉成高阶概括 不出声

from __future__ import annotations

import time

from PySide6.QtCore import QObject, QTimer

from desktop_pet.emotion.state import emotion

_POLL_MS = 60_000
_DREAM_AFTER_S = 8 * 60    # 睡着满这么久才做一个梦
_RAPPORT_GATE = 0.4        # 还不熟就不做关于你的梦


class Dreams(QObject):
    """睡着够久就让worker后台做一次记忆整理 不出声 只触发"""

    def __init__(self, host) -> None:
        super().__init__()
        self._host = host
        self._timer = QTimer(self)
        self._timer.timeout.connect(self._tick)
        self._asleep_since = 0.0
        self._dreamed_this_sleep = False

    def start(self) -> None:
        self._timer.start(_POLL_MS)

    def stop(self) -> None:
        try:
            self._timer.stop()
        except Exception:
            pass

    def _tick(self) -> None:
        pet = self._host._pet
        if not pet.isVisible() or not pet.is_asleep:
            # 醒着或不在场景 重置这觉的计时
            self._asleep_since = 0.0
            self._dreamed_this_sleep = False
            return
        now = time.monotonic()
        if self._asleep_since == 0.0:
            self._asleep_since = now
            return
        if self._dreamed_this_sleep or self._host._worker.is_running:
            return
        if now - self._asleep_since < _DREAM_AFTER_S:
            return
        _val, _aro, rapport = emotion.snapshot()
        if rapport < _RAPPORT_GATE:
            return
        self._dreamed_this_sleep = True
        # 同一觉里做记忆合并 把这阵子攒的同主题零碎揉成高阶概括
        # 自限的 揉过的标记掉 要等新的相关记忆攒够才再成簇 没簇就静默
        self._host.request_consolidate.emit()
