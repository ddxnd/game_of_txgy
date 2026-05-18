# -*- coding: utf-8 -*-
"""音效、提示与掷骰动画（无额外依赖）"""
from __future__ import annotations

import random
import sys
import tkinter as tk
from typing import Callable, Optional

from constants import DIE_FACES, PATTERN_SYMBOL


class SoundManager:
    """Windows 使用 winsound；其他系统静默跳过"""

    def __init__(self, enabled: bool = True):
        self.enabled = enabled
        self._winsound = None
        if enabled and sys.platform == "win32":
            try:
                import winsound
                self._winsound = winsound
            except ImportError:
                pass

    def toggle(self) -> bool:
        self.enabled = not self.enabled
        return self.enabled

    def _beep(self, freq: int, ms: int) -> None:
        if not self.enabled or not self._winsound:
            return
        try:
            self._winsound.Beep(freq, ms)
        except Exception:
            pass

    def roll(self) -> None:
        self._beep(520, 40)

    def success(self) -> None:
        self._beep(660, 80)
        self._beep(880, 120)

    def fail(self) -> None:
        self._beep(280, 150)

    def lock_color(self) -> None:
        self._beep(550, 60)
        self._beep(750, 60)
        self._beep(950, 100)

    def game_over(self) -> None:
        self._beep(600, 80)
        self._beep(500, 80)
        self._beep(700, 150)


class ToastBar(tk.Label):
    """底部浮动提示，不阻塞操作"""

    def __init__(self, parent: tk.Misc, **kw):
        super().__init__(
            parent,
            font=kw.pop("font", None),
            fg="#fff",
            bg="#2d6a4f",
            padx=16,
            pady=8,
            wraplength=800,
        )
        self._after_id: Optional[str] = None
        self.place_forget()

    def show(self, text: str, kind: str = "info", ms: int = 3200) -> None:
        colors = {
            "info": "#2d6a4f",
            "warn": "#9a6b2f",
            "error": "#8b3a3a",
            "success": "#3a6b8b",
            "epic": "#6b4a8b",
        }
        self.config(text=text, bg=colors.get(kind, colors["info"]))
        self.place(relx=0.5, rely=0.92, anchor="center")
        if self._after_id:
            self.after_cancel(self._after_id)
        self._after_id = self.after(ms, self.place_forget)


def random_face_label() -> str:
    face = random.choice(DIE_FACES)
    k, n = next(iter(face.items()))
    sym = PATTERN_SYMBOL.get(k, k[0])
    return f"{sym}×{n}" if n > 1 else sym


def animate_dice_roll(
    root: tk.Misc,
    label_widgets: list[tk.Label],
    on_done: Callable[[], None],
    steps: int = 10,
    interval_ms: int = 70,
) -> None:
    """掷骰前滚动闪烁，结束后执行 on_done（内部应真正 roll）"""

    def tick(step: int = 0) -> None:
        if step < steps:
            for lw in label_widgets:
                lw.config(text=random_face_label(), fg="#f0d080")
            root.after(interval_ms, lambda: tick(step + 1))
        else:
            on_done()

    tick()
