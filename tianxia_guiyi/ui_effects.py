# -*- coding: utf-8 -*-
"""音效、提示与掷骰动画"""
from __future__ import annotations

import os
import random
import sys
import tkinter as tk
from typing import Callable, List, Optional, Tuple

from constants import DIE_FACES, PATTERN_SYMBOL


class SoundManager:
    """优先 pygame.mixer 合成短音；Windows 回退 winsound；其余平台静音"""

    def __init__(self, enabled: bool = True):
        self.enabled = enabled
        self._winsound = None
        self._mixer = None
        self._cache: dict = {}
        if not enabled:
            return
        try:
            os.environ.setdefault("SDL_AUDIODRIVER", "pulse")
            import pygame
            pygame.mixer.pre_init(22050, -16, 1, 256)
            pygame.mixer.init()
            self._mixer = pygame
            self._build_cache()
        except Exception:
            self._mixer = None
            if sys.platform == "win32":
                try:
                    import winsound
                    self._winsound = winsound
                except ImportError:
                    pass

    def _make_tone(self, freq: int, ms: int, vol: float = 0.35):
        if not self._mixer:
            return None
        import math
        try:
            import numpy as np
            rate = 22050
            n = int(rate * ms / 1000)
            t = np.arange(n) / rate
            wave = np.sin(2 * math.pi * freq * t)
            env = np.minimum(1.0, np.minimum(t * 80.0, (ms / 1000.0 - t) * 80.0))
            env = np.clip(env, 0.0, 1.0)
            data = (wave * env * vol * 32767).astype(np.int16)
            return self._mixer.sndarray.make_sound(data)
        except Exception:
            try:
                rate = 22050
                n = int(rate * ms / 1000)
                buf = bytearray()
                amp = int(vol * 32767)
                for i in range(n):
                    v = int(amp * math.sin(2 * math.pi * freq * i / rate))
                    buf += int(v).to_bytes(2, "little", signed=True)
                return self._mixer.mixer.Sound(buffer=bytes(buf))
            except Exception:
                return None

    def _build_cache(self) -> None:
        for key, parts in {
            "roll": [(520, 40)],
            "success": [(660, 80), (880, 120)],
            "fail": [(280, 150)],
            "lock": [(550, 60), (750, 60), (950, 140)],
            "over": [(600, 80), (500, 80), (700, 200)],
        }.items():
            self._cache[key] = [self._make_tone(f, ms) for f, ms in parts]

    def toggle(self) -> bool:
        self.enabled = not self.enabled
        return self.enabled

    def _play(self, key: str, win_seq: List[Tuple[int, int]]) -> None:
        if not self.enabled:
            return
        if self._mixer and key in self._cache:
            for s in self._cache[key]:
                if s is None:
                    continue
                try:
                    s.play()
                except Exception:
                    pass
            return
        if self._winsound:
            for f, ms in win_seq:
                try:
                    self._winsound.Beep(f, ms)
                except Exception:
                    pass

    def roll(self) -> None:
        self._play("roll", [(520, 40)])

    def success(self) -> None:
        self._play("success", [(660, 80), (880, 120)])

    def fail(self) -> None:
        self._play("fail", [(280, 150)])

    def lock_color(self) -> None:
        self._play("lock", [(550, 60), (750, 60), (950, 100)])

    def game_over(self) -> None:
        self._play("over", [(600, 80), (500, 80), (700, 150)])


class ToastBar(tk.Label):
    """顶部浮动提示；连续消息排队，互不覆盖"""

    KIND_COLOR = {
        "info": "#2d6a4f",
        "warn": "#9a6b2f",
        "error": "#8b3a3a",
        "success": "#3a6b8b",
        "epic": "#6b4a8b",
    }

    def __init__(self, parent: tk.Misc, **kw):
        super().__init__(
            parent,
            font=kw.pop("font", None),
            fg="#fff",
            bg="#2d6a4f",
            padx=18,
            pady=8,
            wraplength=900,
        )
        self._queue: List[Tuple[str, str, int]] = []
        self._showing = False
        self._after_id: Optional[str] = None
        self.place_forget()

    def show(self, text: str, kind: str = "info", ms: int = 2200) -> None:
        self._queue.append((text, kind, ms))
        if not self._showing:
            self._pop()

    def _pop(self) -> None:
        if not self._queue:
            self._showing = False
            self.place_forget()
            return
        self._showing = True
        text, kind, ms = self._queue.pop(0)
        self.config(text=text, bg=self.KIND_COLOR.get(kind, self.KIND_COLOR["info"]))
        self.place(relx=0.5, rely=0.06, anchor="n")
        if self._after_id:
            try:
                self.after_cancel(self._after_id)
            except Exception:
                pass
        self._after_id = self.after(ms, self._pop)


def random_face_label() -> str:
    face = random.choice(DIE_FACES)
    k, n = next(iter(face.items()))
    sym = PATTERN_SYMBOL.get(k, k[0])
    return f"{sym}×{n}" if n > 1 else sym


def animate_dice_roll(
    root: tk.Misc,
    label_widgets: List[tk.Label],
    on_done: Callable[[], None],
    steps: int = 18,
    base_ms: int = 28,
    interval_ms: Optional[int] = None,
) -> None:
    """掷骰动画：ease-out，前快后慢。interval_ms 为兼容旧调用的别名。"""
    if interval_ms is not None:
        base_ms = interval_ms

    palette = ["#f0d080", "#f6c050", "#ffb060", "#ffd890"]

    def tick(step: int = 0) -> None:
        if step < steps:
            alive = False
            for lw in label_widgets:
                try:
                    if lw.winfo_exists():
                        lw.config(text=random_face_label(), fg=random.choice(palette))
                        alive = True
                except tk.TclError:
                    pass
            if not alive:
                on_done()
                return
            ratio = step / max(1, steps - 1)
            delay = int(base_ms + (ratio ** 2) * 140)
            root.after(delay, lambda s=step + 1: tick(s))
        else:
            on_done()

    tick()


def shake_window(root: tk.Tk, intensity: int = 8, times: int = 8, interval: int = 28) -> None:
    """窗口左右抖动，用于失败 / 惩罚反馈"""
    try:
        x0, y0 = root.winfo_x(), root.winfo_y()
    except Exception:
        return

    def tick(i: int = 0) -> None:
        if i >= times:
            try:
                root.geometry(f"+{x0}+{y0}")
            except Exception:
                pass
            return
        decay = max(1, intensity - i)
        dx = decay if i % 2 == 0 else -decay
        try:
            root.geometry(f"+{x0 + dx}+{y0}")
        except Exception:
            return
        root.after(interval, lambda: tick(i + 1))

    tick()


def celebrate_lock(
    root: tk.Tk,
    color_hex: str,
    title: str,
    subtitle: str = "",
    duration_ms: int = 1600,
) -> None:
    """集齐颜色：覆盖透明层闪烁 + 大字 banner + 星辰飞散"""
    try:
        x = root.winfo_rootx()
        y = root.winfo_rooty()
        w = root.winfo_width()
        h = root.winfo_height()
    except Exception:
        return
    if w < 50 or h < 50:
        return

    overlay = tk.Toplevel(root)
    overlay.overrideredirect(True)
    overlay.transient(root)
    try:
        overlay.attributes("-topmost", True)
        overlay.attributes("-alpha", 0.0)
    except Exception:
        pass
    overlay.configure(bg=color_hex)
    overlay.geometry(f"{w}x{h}+{x}+{y}")

    canvas = tk.Canvas(overlay, bg=color_hex, highlightthickness=0, width=w, height=h)
    canvas.pack(fill=tk.BOTH, expand=True)

    canvas.create_text(
        w // 2, h // 2 - 20,
        text=title,
        font=("Microsoft YaHei", 56, "bold"),
        fill="#ffffff",
        tags="title",
    )
    if subtitle:
        canvas.create_text(
            w // 2, h // 2 + 50,
            text=subtitle,
            font=("Microsoft YaHei", 20),
            fill="#fff8e0",
            tags="sub",
        )

    import math
    star_count = 24
    cx, cy = w // 2, h // 2
    stars = []
    for _ in range(star_count):
        ang = random.uniform(0, 6.283)
        dist = random.uniform(120, 320)
        tx = int(cx + math.cos(ang) * dist)
        ty = int(cy + math.sin(ang) * dist)
        sid = canvas.create_text(
            cx, cy, text="★",
            font=("Microsoft YaHei", random.randint(14, 28), "bold"),
            fill="#fff8c0",
        )
        stars.append((sid, tx, ty))

    total_steps = 28
    fade_in = 6
    hold = 16
    fade_out = total_steps - fade_in - hold

    def step(i: int = 0) -> None:
        try:
            if i < fade_in:
                alpha = 0.55 * (i + 1) / fade_in
            elif i < fade_in + hold:
                alpha = 0.55
            else:
                k = i - fade_in - hold
                alpha = max(0.0, 0.55 * (1 - k / max(1, fade_out)))
            try:
                overlay.attributes("-alpha", alpha)
            except Exception:
                pass
            prog = min(1.0, i / max(1, fade_in + hold))
            for sid, tx, ty in stars:
                px = cx + (tx - cx) * prog
                py = cy + (ty - cy) * prog
                canvas.coords(sid, px, py)
            if i < total_steps:
                overlay.after(duration_ms // total_steps, lambda: step(i + 1))
            else:
                overlay.destroy()
        except tk.TclError:
            return

    step()
