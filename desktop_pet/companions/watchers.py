# author: bdth
# email: 2074055628@qq.com
# 守望伴生 后台shell跑完播报

from __future__ import annotations

import time

from PySide6.QtCore import QObject, QTimer

from desktop_pet import i18n
from desktop_pet.agent import prompts as agent_prompts
from desktop_pet.emotion.state import emotion
from desktop_pet.executor import shell as shell_exec
from desktop_pet.pet.behavior import selector

_BGWATCH_POLL_MS = 5_000
_BGWATCH_MIN_RUNTIME_S = 10.0  # 秒退的任务agent当场看到 不播报


class Watchers(QObject):

    def __init__(self, host) -> None:
        super().__init__()
        self._host = host
        self._bgwatch_timer = QTimer(self)
        self._bgwatch_timer.timeout.connect(self._scan_background_shells)
        self._bg_announced: set[int] = set()

    def start(self) -> None:
        self._bgwatch_timer.start(_BGWATCH_POLL_MS)

    def stop(self) -> None:
        try:
            self._bgwatch_timer.stop()
        except Exception:
            pass

    def _scan_background_shells(self) -> None:
        """守望后台shell 跑完庆祝 挂了安慰并叫agent看"""
        try:
            snap = shell_exec.background_snapshot()
        except Exception:
            return
        for t in snap:
            if t["running"] or t["id"] in self._bg_announced:
                continue
            self._bg_announced.add(t["id"])
            if time.time() - t["started"] < _BGWATCH_MIN_RUNTIME_S:
                continue
            if t["returncode"] == 0:
                self._host._feed_react("celebrate")
                self._host._feed_pop(i18n.t("bgwatch_ok").format(id=t["id"]))
                emotion.apply("task_done")
                selector.set_emotion(*emotion.snapshot())
            else:
                self._host._feed_react("droop")
                self._host._feed_pop(i18n.t("bgwatch_fail").format(id=t["id"], code=t["returncode"]))
                if not self._host._worker.is_running:
                    self._host.request_message.emit(agent_prompts.BGWATCH_ANALYZE_MSG.format(
                        id=t["id"], command=t["command"][:80], code=t["returncode"],
                        tail=t["tail"][-1200:]))
