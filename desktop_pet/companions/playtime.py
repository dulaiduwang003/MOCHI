# author: bdth
# email: 2074055628@qq.com
# 玩耍伴生 抓虫投球蹲守脚印物理反馈渔获

from __future__ import annotations

import random
from datetime import datetime

from PySide6.QtCore import QObject, QPoint, QTimer, Slot

from desktop_pet import i18n, journal, occasions, somatic, stats
from desktop_pet.agent import prompts as agent_prompts
from desktop_pet.emotion.state import emotion
from desktop_pet.pet.behavior import selector


class Playtime(QObject):

    def __init__(self, host) -> None:
        super().__init__()
        self._host = host
        from desktop_pet.pet.footprints import FootprintLayer
        self._paws = FootprintLayer()
        self._paw_last = QPoint()
        self._host._pet.moved.connect(self._on_pet_moved_paws)
        self._ball = None  # 玩具球
        self._host._pet.bind_activity_done(self._on_activity_done)
        self._host._pet.tossed.connect(self._on_tossed)
        self._host._pet.tickled.connect(self._on_tickled)

    def start(self) -> None:
        pass

    def stop(self) -> None:
        """退出前关掉玩耍小窗"""
        if self._ball is not None:
            try:
                self._ball._timer.stop()
                self._ball.close()
            except Exception:
                pass
        self._ball = None
        try:
            self._paws._timer.stop()
            self._paws.hide()
        except Exception:
            pass

    @Slot(float)
    def _on_tossed(self, impact: float) -> None:
        """被重摔了 疼一下还要哄"""
        emotion.apply("hurt")
        selector.set_emotion(*emotion.snapshot())
        self._host._pet.set_expression("sad")
        somatic.note(agent_prompts.SOMA_TOSSED)
        somatic.set_state("grudge", agent_prompts.SOMA_GRUDGE)
        QTimer.singleShot(30 * 60 * 1000, lambda: somatic.set_state("grudge", None))
        self._host._feed_pop(i18n.t("toss_ouch"))

    @Slot()
    def _on_tickled(self) -> None:
        """被挠痒 开心计入互动"""
        emotion.apply("praised")
        selector.set_emotion(*emotion.snapshot())
        stats.bump_interactions()
        somatic.note(agent_prompts.SOMA_TICKLED)

    def _on_pet_moved_paws(self) -> None:
        """走动时心情好就留脚印 节日换花样"""
        try:
            _val, _aro, _r = emotion.snapshot()
            if _val < 0.25:
                return
            pos = self._host._pet.frameGeometry().center()
            d = pos - self._paw_last
            if (d.x() * d.x() + d.y() * d.y()) < 70 * 70:
                return
            import math as _m
            heading = _m.atan2(d.y(), d.x()) if self._paw_last != QPoint() else 0.0
            self._paw_last = QPoint(pos)
            kind = "paw"
            okey = occasions.today_key(datetime.now()) or ""
            if "spring" in okey or "newyear" in okey:
                kind = "flower"
            elif "christmas" in okey or "winter" in okey:
                kind = "snow"
            self._paws.add(pos.x(), pos.y() + self._host._pet.height() // 4, heading, kind)
        except Exception:
            pass

    def _on_activity_done(self, name: str) -> None:
        """小品演完的彩蛋 钓鱼有渔获"""
        if name != "fish":
            return
        catch = ""
        try:
            today_lines = [str(it.get("text", "")) for it in journal.recent(6)]
            if today_lines:
                catch = random.choice(today_lines)[:46]
        except Exception:
            pass
        if catch:
            QTimer.singleShot(1200, lambda: self._host._feed_pop(i18n.t("fish_catch").format(thing=catch)))

    def throw_ball(self) -> None:
        """丢颗球给它玩"""
        if self._ball is not None or not self._host._pet.isVisible() or self._host._pet.is_asleep:
            return
        from desktop_pet.pet.ball import BallWindow
        from desktop_pet.eyes import capture
        ball = BallWindow()
        capture.register_own_window(int(ball.winId()))
        ball.caught.connect(self._on_ball_caught)
        ball.stopped.connect(self._on_ball_stopped)
        scr = self._host._app.primaryScreen().availableGeometry()
        ball.throw_from_top(scr, self._host._pet.frameGeometry())
        self._ball = ball
        self._host._feed_react("perk_up")

    @Slot()
    def _on_ball_caught(self) -> None:
        self._ball = None
        self._host._feed_react("jump_spin")
        emotion.apply("praised")
        selector.set_emotion(*emotion.snapshot())
        somatic.note(agent_prompts.SOMA_BALL)
        QTimer.singleShot(900, lambda: self._host._feed_pop(i18n.t("ball_caught")))

    @Slot()
    def _on_ball_stopped(self) -> None:
        self._ball = None
        self._host._feed_react("peek")
