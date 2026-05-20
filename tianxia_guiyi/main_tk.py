# -*- coding: utf-8 -*-
"""天下归一 - 增强体验版（左 | 中 | 右）"""
from __future__ import annotations

import tkinter as tk
from tkinter import font as tkfont
from tkinter import messagebox, ttk

from constants import COLORS as COLOR_INFO, COLOR_LABEL, PATTERN_SYMBOL
from game_logic import GameState, Phase, Card
from themes import THEMES, THEME_NAMES
from ui_effects import (
    SoundManager,
    ToastBar,
    animate_dice_roll,
    celebrate_lock,
    shake_window,
)


def _lighten(hex_c: str, factor: float = 0.22) -> str:
    r = int(hex_c[1:3], 16)
    g = int(hex_c[3:5], 16)
    b = int(hex_c[5:7], 16)
    r = min(255, int(r + (255 - r) * factor))
    g = min(255, int(g + (255 - g) * factor))
    b = min(255, int(b + (255 - b) * factor))
    return f"#{r:02x}{g:02x}{b:02x}"

RULES_TEXT = """《天下归一》规则摘要

【目标】占领卡牌、集齐同色，积分高者胜。

【先手】双方各掷 1d6，大者先行；相同则重掷。

【回合】选公共区卡或抢对手手牌（需多 1 虎符）→ 掷 6 枚图案骰 → 选骰放置（公共区卡最多约 5 枚骰可完成）→ 可随时点「跳过本回合」放弃。

【积分】仅当集齐某颜色全部卡牌时，获得该色难度分（赤12/青10/墨8/金6），并锁定该色不让对手再抢。

【提示】放置阶段可用「智能选骰」；顶部可切换深色/浅色背景与音效。"""


class TianXiaApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("天下归一")
        self.geometry("1320x800")
        self.minsize(1150, 720)
        self.theme_name = "dark"
        self.theme = THEMES[self.theme_name]
        self.configure(bg=self.t("center"))

        self.state = GameState()
        self.selecting_opponent = False
        self.die_vars: list[tk.BooleanVar] = []
        self._dice_anim_labels: list[tk.Label] = []
        self._rolling = False

        self.sound = SoundManager(True)
        self.font_title = tkfont.Font(family="Microsoft YaHei", size=22, weight="bold")
        self.font = tkfont.Font(family="Microsoft YaHei", size=11)
        self.font_sm = tkfont.Font(family="Microsoft YaHei", size=9)
        self.font_btn = tkfont.Font(family="Microsoft YaHei", size=11, weight="bold")
        self.font_dice = tkfont.Font(family="Microsoft YaHei", size=14, weight="bold")

        self.msg_var = tk.StringVar(value=self.state.message)
        self.player_panels: list[dict] = []

        self._build_ui()
        self.toast = ToastBar(self, font=self.font)
        self.after(300, self._show_start_dialog)
        self.refresh()

    def t(self, key: str) -> str:
        return self.theme[key]

    def _toggle_theme(self):
        self.theme_name = "light" if self.theme_name == "dark" else "dark"
        self.theme = THEMES[self.theme_name]
        self.theme_btn.config(text=f"🎨 {THEME_NAMES[self.theme_name]}")
        self._apply_shell_theme()
        self.toast.show(f"已切换为「{THEME_NAMES[self.theme_name]}」界面", "info")
        self.refresh()

    def _apply_shell_theme(self):
        """刷新顶部/底部等固定容器的配色"""
        self.configure(bg=self.t("center"))
        self._top_bar.configure(bg=self.t("center"))
        self._title_label.configure(bg=self.t("center"), fg=self.t("accent"))
        self._main_frame.configure(bg=self.t("center"))
        self._bottom_bar.configure(bg=self.t("bottom"))
        self._msg_label.configure(bg=self.t("bottom"), fg=self.t("text"))
        for panel in self.player_panels:
            panel["frame"].configure(bg=self.t("side"), fg=self.t("panel_title"))
            panel["order_box"].configure(bg=self.t("side"), fg=self.t("accent"))
            panel["order_val"].configure(bg=self.t("side"), fg=self.t("text"))
            panel["order_btn"].configure(bg=self.t("order_btn"))
            panel["hand_canvas"].configure(bg=self.t("side"))
        if hasattr(self, "center_col"):
            cc = self.center_col
            for key in ("dice_canvas",):
                if key in cc:
                    cc[key].configure(bg=self.t("side"))

    def _show_start_dialog(self):
        dlg = tk.Toplevel(self)
        dlg.title("开局设置")
        dlg.configure(bg=self.t("side"))
        dlg.transient(self)
        dlg.grab_set()
        tk.Label(dlg, text="天下归一 · 新局", font=self.font_title, fg=self.t("accent"), bg=self.t("side")).pack(pady=12)
        f = tk.Frame(dlg, bg=self.t("side"))
        f.pack(padx=20, pady=8)
        e0 = tk.Entry(f, font=self.font, width=16)
        e1 = tk.Entry(f, font=self.font, width=16)
        e0.insert(0, "玩家一")
        e1.insert(0, "玩家二")
        tk.Label(f, text="左侧：", fg=self.t("text_dim"), bg=self.t("side"), font=self.font).grid(row=0, column=0, sticky="e")
        e0.grid(row=0, column=1, padx=6, pady=4)
        tk.Label(f, text="右侧：", fg=self.t("text_dim"), bg=self.t("side"), font=self.font).grid(row=1, column=0, sticky="e")
        e1.grid(row=1, column=1, padx=6, pady=4)

        def ok():
            self.state.player_names[0] = e0.get().strip() or "玩家一"
            self.state.player_names[1] = e1.get().strip() or "玩家二"
            dlg.destroy()
            self.refresh()
            self.toast.show("祝两位征战顺利！", "success")

        tk.Button(dlg, text="开始征战", font=self.font_btn, bg="#4a7a5a", fg="white", command=ok).pack(pady=16)
        dlg.update_idletasks()
        self.update_idletasks()
        dw = dlg.winfo_reqwidth()
        dh = dlg.winfo_reqheight()
        rw = self.winfo_width() or self.winfo_screenwidth()
        rh = self.winfo_height() or self.winfo_screenheight()
        rx = self.winfo_rootx() if self.winfo_rootx() > 0 else 0
        ry = self.winfo_rooty() if self.winfo_rooty() > 0 else 0
        dlg.geometry(f"+{rx + (rw - dw) // 2}+{ry + (rh - dh) // 2}")

    def _build_ui(self):
        self._top_bar = tk.Frame(self, bg=self.t("center"))
        self._top_bar.pack(fill=tk.X, padx=10, pady=6)
        self._title_label = tk.Label(
            self._top_bar, text="天下归一", font=self.font_title, fg=self.t("accent"), bg=self.t("center"),
        )
        self._title_label.pack(side=tk.LEFT)
        tk.Button(self._top_bar, text="📜 规则", font=self.font_sm, command=self._show_rules).pack(side=tk.RIGHT, padx=4)
        self.theme_btn = tk.Button(
            self._top_bar, text=f"🎨 {THEME_NAMES[self.theme_name]}",
            font=self.font_sm, command=self._toggle_theme,
        )
        self.theme_btn.pack(side=tk.RIGHT, padx=4)
        self.sound_btn = tk.Button(self._top_bar, text="🔊 音效", font=self.font_sm, command=self._toggle_sound)
        self.sound_btn.pack(side=tk.RIGHT, padx=4)

        self._main_frame = tk.Frame(self, bg=self.t("center"))
        self._main_frame.pack(fill=tk.BOTH, expand=True, padx=8, pady=4)
        main = self._main_frame
        main.columnconfigure(0, weight=1, uniform="c")
        main.columnconfigure(1, weight=2, uniform="c")
        main.columnconfigure(2, weight=1, uniform="c")
        main.rowconfigure(0, weight=1)

        self._build_player_column(main, 0, 0)
        self.center_col = self._build_center_column(main, 1)
        self._build_player_column(main, 2, 1)

        self._bottom_bar = tk.Frame(self, bg=self.t("bottom"))
        self._bottom_bar.pack(fill=tk.X, side=tk.BOTTOM, padx=8, pady=6)
        self._msg_label = tk.Label(
            self._bottom_bar, textvariable=self.msg_var, font=self.font,
            fg=self.t("text"), bg=self.t("bottom"), wraplength=1050,
        )
        self._msg_label.pack(fill=tk.X, padx=10, pady=4)

    def _build_player_column(self, parent, grid_col: int, player_idx: int):
        outer = tk.Frame(parent, bg=self.t("center"))
        outer.grid(row=0, column=grid_col, sticky="nsew", padx=4)
        name = self.state.pname(player_idx) if player_idx < len(self.state.player_names) else f"P{player_idx}"
        lf = tk.LabelFrame(outer, text=name, font=self.font_btn, fg=self.t("panel_title"), bg=self.t("side"), labelanchor="n")
        lf.pack(fill=tk.BOTH, expand=True)

        info = tk.Label(lf, text="", font=self.font_sm, fg=self.t("text_dim"), bg=self.t("side"), justify=tk.LEFT, wraplength=280)
        info.pack(anchor="w", padx=10, pady=6)

        color_prog = tk.Frame(lf, bg=self.t("side"))
        color_prog.pack(fill=tk.X, padx=8)

        order_box = tk.LabelFrame(lf, text="定先手", font=self.font_sm, fg=self.t("accent"), bg=self.t("side"))
        order_val = tk.Label(order_box, text="—", font=self.font_dice, fg=self.t("text"), bg=self.t("side"))
        order_val.pack(pady=4)
        order_btn = tk.Button(
            order_box, text="掷先手骰", font=self.font_sm, width=14, height=2,
            bg=self.t("order_btn"), fg="white", command=lambda p=player_idx: self._order_roll(p),
        )
        order_btn.pack(pady=(0, 8), padx=8)

        hand_lf = tk.LabelFrame(lf, text="手牌（可滚动）", font=self.font_sm, fg=self.t("text_muted"), bg=self.t("side"))
        hand_lf.pack(fill=tk.BOTH, expand=True, padx=8, pady=4)
        hand_canvas = tk.Canvas(hand_lf, bg=self.t("side"), highlightthickness=0, height=200)
        hand_vsb = ttk.Scrollbar(hand_lf, orient=tk.VERTICAL, command=hand_canvas.yview)
        hand_canvas.configure(yscrollcommand=hand_vsb.set)
        hand_canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(4, 0), pady=4)
        hand_vsb.pack(side=tk.RIGHT, fill=tk.Y, pady=4, padx=(0, 4))
        hand_inner = tk.Frame(hand_canvas, bg=self.t("side"))
        hand_win_id = hand_canvas.create_window((0, 0), window=hand_inner, anchor="nw")

        def _hand_scroll_configure(_e=None, c=hand_canvas, w=hand_win_id, inner=hand_inner):
            c.configure(scrollregion=c.bbox("all"))
            c.itemconfig(w, width=max(c.winfo_width(), 1))

        hand_inner.bind("<Configure>", _hand_scroll_configure)
        hand_canvas.bind("<Configure>", _hand_scroll_configure)

        def _hand_wheel(e, c=hand_canvas):
            c.yview_scroll(int(-1 * (e.delta / 120)), "units")

        hand_canvas.bind("<MouseWheel>", _hand_wheel)

        action_box = tk.LabelFrame(lf, text="回合操作", font=self.font_sm, fg=self.t("text_hint"), bg=self.t("side"))
        action_box.pack(side=tk.BOTTOM, fill=tk.X, padx=8, pady=8)
        action_inner = tk.Frame(action_box, bg=self.t("side"))
        action_inner.pack(fill=tk.X, padx=6, pady=6)

        self.player_panels.append({
            "player": player_idx, "frame": lf, "info": info, "color_prog": color_prog,
            "order_box": order_box, "order_val": order_val, "order_btn": order_btn,
            "action_inner": action_inner, "hand_inner": hand_inner,
            "hand_canvas": hand_canvas,
        })

    def _build_center_column(self, parent, grid_col: int) -> dict:
        center = tk.Frame(parent, bg=self.t("center"))
        center.grid(row=0, column=grid_col, sticky="nsew", padx=4)

        pub = tk.LabelFrame(center, text="公共区", font=self.font, fg=self.t("text"), bg=self.t("public"))
        pub.pack(fill=tk.BOTH, expand=True, pady=(0, 4))
        public_inner = tk.Frame(pub, bg=self.t("public"))
        public_inner.pack(fill=tk.BOTH, expand=True, padx=6, pady=6)

        mid = tk.Frame(center, bg=self.t("center"))
        mid.pack(fill=tk.X, pady=4)

        target_frame = tk.LabelFrame(mid, text="攻占目标", font=self.font, fg=self.t("accent"), bg=self.t("target"))
        target_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 4))
        target_labels = tk.Label(target_frame, text="", font=self.font, fg=self.t("target_text"), bg=self.t("target"), justify=tk.LEFT)
        target_labels.pack(anchor="w", padx=8, pady=4)
        progress_frame = tk.Frame(target_frame, bg=self.t("progress_bg"))
        progress_frame.pack(fill=tk.X, padx=8, pady=(0, 8))

        dice_frame = tk.LabelFrame(mid, text="本回合骰子（可左右滑动）", font=self.font, fg=self.t("text"), bg=self.t("side"))
        dice_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(4, 0))
        dice_outer = tk.Frame(dice_frame, bg=self.t("side"))
        dice_outer.pack(fill=tk.X, padx=4, pady=(6, 0))
        dice_canvas = tk.Canvas(dice_outer, bg=self.t("side"), height=88, highlightthickness=0)
        dice_hsb = ttk.Scrollbar(dice_outer, orient=tk.HORIZONTAL, command=dice_canvas.xview)
        dice_canvas.configure(xscrollcommand=dice_hsb.set)
        dice_hsb.pack(side=tk.BOTTOM, fill=tk.X)
        dice_canvas.pack(side=tk.TOP, fill=tk.X, expand=True)
        dice_inner = tk.Frame(dice_canvas, bg=self.t("side"))
        dice_win_id = dice_canvas.create_window((0, 0), window=dice_inner, anchor="nw")

        def _dice_scroll_configure(_e=None, c=dice_canvas, w=dice_win_id, inner=dice_inner):
            c.configure(scrollregion=c.bbox("all"))
            c.itemconfig(w, height=inner.winfo_reqheight())

        dice_inner.bind("<Configure>", _dice_scroll_configure)

        def _dice_wheel(e, c=dice_canvas):
            c.xview_scroll(int(-1 * (e.delta / 120)), "units")

        dice_canvas.bind("<MouseWheel>", _dice_wheel)
        dice_canvas.bind("<Shift-MouseWheel>", _dice_wheel)

        dice_actions = tk.Frame(dice_frame, bg=self.t("side"))
        dice_actions.pack(fill=tk.X, padx=8, pady=(0, 10))

        center_actions = tk.Frame(center, bg=self.t("center"))
        center_actions.pack(fill=tk.X, pady=4)

        log_frame = tk.LabelFrame(center, text="战报", font=self.font_sm, fg=self.t("text_muted"), bg=self.t("log_panel"))
        log_frame.pack(fill=tk.X, pady=4)
        log_text = tk.Text(log_frame, height=10, font=self.font_sm, bg=self.t("log_bg"), fg=self.t("log_fg"), wrap=tk.WORD, state=tk.DISABLED)
        log_scroll = ttk.Scrollbar(log_frame, command=log_text.yview)
        log_text.configure(yscrollcommand=log_scroll.set)
        log_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=4, pady=4)
        log_scroll.pack(side=tk.RIGHT, fill=tk.Y, pady=4)

        return {
            "public_inner": public_inner, "target_labels": target_labels,
            "progress_frame": progress_frame, "dice_inner": dice_inner,
            "dice_canvas": dice_canvas, "dice_actions": dice_actions,
            "center_actions": center_actions, "log_text": log_text,
        }

    def _clear(self, w):
        for c in w.winfo_children():
            c.destroy()

    def _toggle_sound(self):
        on = self.sound.toggle()
        self.sound_btn.config(text="🔊 音效" if on else "🔇 静音")

    def _show_rules(self):
        w = tk.Toplevel(self)
        w.title("游戏规则")
        w.configure(bg=self.t("side"))
        t = tk.Text(w, font=self.font, wrap=tk.WORD, bg=self.t("rules_bg"), fg=self.t("rules_fg"), padx=12, pady=12)
        t.pack(fill=tk.BOTH, expand=True, padx=8, pady=8)
        t.insert("1.0", RULES_TEXT)
        t.config(state=tk.DISABLED)

    def _toast_for_event(self):
        ev = self.state.last_event
        if ev == "success":
            self.toast.show(self.state.message.split("→")[0].strip(), "success")
            self.sound.success()
        elif ev == "lock":
            self.toast.show(self.state.message.split("→")[0].strip(), "epic")
            self.sound.lock_color()
            color = self.state.last_locked_color
            if color and color in COLOR_INFO:
                rgb = COLOR_INFO[color]["rgb"]
                hex_c = "#%02x%02x%02x" % rgb
                title = f"集齐「{COLOR_LABEL.get(color, color)}」"
                subtitle = f"+{COLOR_INFO[color]['score']} 分 · 该色锁定"
                celebrate_lock(self, hex_c, title, subtitle)
        elif ev == "fail":
            self.toast.show(self.state.message.split("→")[0].strip(), "warn")
            self.sound.fail()
            shake_window(self)
        elif ev == "game_over":
            self.sound.game_over()

    def refresh(self):
        skipped = self.state.maybe_auto_pass()
        if skipped:
            self.toast.show(skipped, "warn")
        for i, panel in enumerate(self.player_panels):
            panel["frame"].config(text=self.state.pname(i))
        self.msg_var.set(self.state.message)
        self._refresh_players()
        self._refresh_public()
        self._refresh_target()
        self._refresh_dice()
        self._refresh_dice_actions()
        self._refresh_center_actions()
        self._refresh_log()
        if self.state.phase == Phase.GAME_OVER and not getattr(self, "_game_over_shown", False):
            self._game_over_shown = True
            self._toast_for_event()
            self.after(500, lambda: messagebox.showinfo("天下归一 · 终局", self.state.final_summary()))

    def _refresh_log(self):
        t = self.center_col["log_text"]
        t.config(state=tk.NORMAL)
        t.delete("1.0", tk.END)
        for line in self.state.log[-30:]:
            t.insert(tk.END, line + "\n")
        t.see(tk.END)
        t.config(state=tk.DISABLED)

    def _is_active_player(self, pi: int) -> bool:
        s = self.state
        if s.phase == Phase.GAME_OVER:
            return False
        if s.phase == Phase.ROLL_ORDER:
            return s.order_roll_whose_turn() == pi
        return s.current == pi

    def _refresh_players(self):
        s = self.state
        for panel in self.player_panels:
            pi = panel["player"]
            p = s.players[pi]
            active = self._is_active_player(pi)
            is_turn = s.current == pi and s.phase not in (Phase.GAME_OVER, Phase.ROLL_ORDER)

            panel["frame"].config(
                highlightbackground=self.t("accent") if (active or is_turn) else self.t("side"),
                highlightthickness=3 if (active or is_turn) else 0,
            )
            lines = [f"🏆 积分 {p.score}", f"🃏 手牌 {len(p.hand)} 张"]
            if is_turn and s.phase != Phase.ROLL_ORDER:
                lines.append(f"▶ 第 {s.turn_number} 回合")
            panel["info"].config(text="\n".join(lines))

            self._clear(panel["color_prog"])
            for color, (owned, total, pts) in s.color_progress(pi).items():
                rgb = COLOR_INFO[color]["rgb"]
                hex_c = "#%02x%02x%02x" % rgb
                locked = color in p.locked_colors
                mark = "🔒" if locked else ""
                row = tk.Frame(panel["color_prog"], bg=self.t("side"))
                row.pack(fill=tk.X, pady=1)
                tk.Label(row, text=f"{COLOR_LABEL.get(color, color)}{mark}", font=self.font_sm, fg=hex_c, bg=self.t("side"), width=6).pack(side=tk.LEFT)
                pb = ttk.Progressbar(row, length=120, maximum=max(total, 1), value=owned)
                pb.pack(side=tk.LEFT, padx=4)
                tk.Label(row, text=f"{owned}/{total}", font=self.font_sm, fg=self.t("text_faint"), bg=self.t("side")).pack(side=tk.LEFT)

            if s.phase == Phase.ROLL_ORDER:
                panel["order_box"].pack(fill=tk.X, padx=8, pady=4)
                r = s.order_rolls[pi]
                panel["order_val"].config(text=str(r) if r is not None else "—")
                panel["order_btn"].config(state=tk.NORMAL if s.order_roll_whose_turn() == pi else tk.DISABLED)
            else:
                panel["order_box"].pack_forget()

            self._clear(panel["action_inner"])
            self._fill_player_actions(panel)

            self._clear(panel["hand_inner"])
            hand_inner = panel["hand_inner"]
            if not p.hand:
                tk.Label(hand_inner, text="（无）", font=self.font_sm, fg=self.t("text_faint"), bg=self.t("side")).pack()
            else:
                row: tk.Frame | None = None
                for i, card in enumerate(p.hand):
                    if i % 2 == 0:
                        row = tk.Frame(hand_inner, bg=self.t("side"))
                        row.pack(fill=tk.X, pady=2)
                    self._card_button(
                        row, card, small=True,
                        enabled=s.phase == Phase.CHOOSE_TARGET
                        and self.selecting_opponent
                        and card.owner == 1 - s.current,
                    )
                hand_inner.update_idletasks()
                if "hand_canvas" in panel:
                    panel["hand_canvas"].configure(scrollregion=panel["hand_canvas"].bbox("all"))

    def _fill_player_actions(self, panel: dict):
        s, pi, inner = self.state, panel["player"], panel["action_inner"]
        is_turn = s.current == pi

        def side_btn(text, cmd, enabled=True, color="#4a7a5a"):
            tk.Button(
                inner, text=text, font=self.font_sm, width=16,
                bg=color if enabled else self.t("btn_disabled_bg"), fg="white",
                state=tk.NORMAL if enabled else tk.DISABLED, command=cmd,
            ).pack(pady=3, fill=tk.X)

        if s.phase == Phase.ROLL_ORDER:
            return
        if s.phase == Phase.CHOOSE_TARGET and is_turn:
            side_btn("🎯 公共区", lambda: self._set_mode(False))
            side_btn("⚔ 抢对手牌", lambda: self._set_mode(True), color="#7a4a4a")
            side_btn("⊘ 跳过本回合", self._skip_turn, color="#6a5a4a")
            return
        if s.phase == Phase.ROLL_DICE and is_turn:
            side_btn("🎲 掷图案骰", self._roll, enabled=not self._rolling)
            side_btn("⊘ 跳过本回合", self._skip_turn, color="#6a5a4a")
            return
        if s.phase == Phase.PLACE_DICE and is_turn:
            side_btn("✓ 确认放置", self._confirm)
            side_btn("🤖 智能选骰", self._smart_pick, color="#4a5a8a")
            side_btn("✗ 无法放置", self._penalty, color="#6a4a4a")
            side_btn("⊘ 跳过本回合", self._skip_turn, color="#6a5a4a")
            side_btn("清空选择", lambda: (s.selected_dice.clear(), self.refresh()))
            return
        if not is_turn and s.phase in (Phase.ROLL_DICE, Phase.PLACE_DICE, Phase.CHOOSE_TARGET):
            tk.Label(inner, text="⏳ 等待对手", font=self.font_sm, fg=self.t("text_faint"), bg=self.t("side")).pack(pady=10)

    def _refresh_center_actions(self):
        self._clear(self.center_col["center_actions"])
        s = self.state
        if s.phase == Phase.ROLL_ORDER:
            r0, r1 = s.order_rolls
            tk.Label(
                self.center_col["center_actions"],
                text=f"⚔ 定先手  {s.pname(0)}:{r0 or '—'}  VS  {s.pname(1)}:{r1 or '—'}"
                     + (f"  （平局×{s.order_tie_count}）" if s.order_tie_count else ""),
                font=self.font, fg=self.t("accent"), bg=self.t("center"),
            ).pack()
        elif s.phase == Phase.GAME_OVER:
            tk.Button(self.center_col["center_actions"], text="🔄 再来一局", font=self.font_btn,
                      bg="#8a6040", fg="white", command=self._restart).pack(pady=4)
        elif s.phase == Phase.CHOOSE_TARGET:
            mode = "抢对手手牌" if self.selecting_opponent else "攻占公共区"
            tk.Label(
                self.center_col["center_actions"],
                text=f"模式：{mode}  ·  点击公共区卡牌；抢牌请用侧栏「抢对手牌」",
                font=self.font, fg=self.t("text_hint"), bg=self.t("center"),
            ).pack()
            if not self.selecting_opponent:
                row = tk.Frame(self.center_col["center_actions"], bg=self.t("center"))
                row.pack(pady=4)
                tk.Button(row, text="🎯 选公共区", font=self.font_sm, bg="#4a6a8a", fg="white",
                          command=lambda: self._set_mode(False)).pack(side=tk.LEFT, padx=4)
                tk.Button(row, text="⚔ 抢对手牌", font=self.font_sm, bg="#8a4a4a", fg="white",
                          command=lambda: self._set_mode(True)).pack(side=tk.LEFT, padx=4)

    def _refresh_public(self):
        self._clear(self.center_col["public_inner"])
        public = self.state.public_cards()
        inner = self.center_col["public_inner"]
        if not public:
            tk.Label(inner, text="（公共区已空）", font=self.font, fg=self.t("text_faint"), bg=self.t("public")).pack(pady=20)
            return
        cols = 5
        row = tk.Frame(inner, bg=self.t("public"))
        row.pack(anchor="center", pady=2)
        for i, card in enumerate(public):
            if i and i % cols == 0:
                row = tk.Frame(inner, bg=self.t("public"))
                row.pack(anchor="center", pady=2)
            locked = self.state.is_color_locked_by_opponent(self.state.current, card.color)
            self._card_button(row, card, enabled=self.state.phase == Phase.CHOOSE_TARGET and not self.selecting_opponent and not locked, locked=locked)

    def _card_button(self, parent, card: Card, small=False, enabled=True, locked=False):
        rgb = COLOR_INFO[card.color]["rgb"]
        hex_c = "#%02x%02x%02x" % rgb
        score = COLOR_INFO[card.color]["score"]
        diff = sum(card.req.values())
        stars = "★" * max(1, min((diff - 1) // 3, 3))
        req_txt = "  ".join(f"{PATTERN_SYMBOL.get(k, k[0])}×{v}" for k, v in card.req.items())

        bg = hex_c if not locked else self.t("card_locked")
        cw_px = 96 if small else 132
        ch_px = 90 if small else 132

        wrap = tk.Frame(parent, bg=parent.cget("bg") if hasattr(parent, "cget") else self.t("center"))
        wrap.pack(side=tk.LEFT, padx=4, pady=3)

        card_frame = tk.Frame(
            wrap, bg=bg, width=cw_px, height=ch_px,
            relief=tk.RAISED, bd=2,
            highlightthickness=0,
            cursor="hand2" if (enabled and not locked) else "",
        )
        card_frame.pack()
        card_frame.pack_propagate(False)

        title_fg = self.t("text_on_card") if not locked else self.t("text_on_card_locked")
        sub_fg = self.t("text_on_card_sub") if not locked else self.t("text_muted")

        top = tk.Frame(card_frame, bg=bg)
        top.pack(fill=tk.X, padx=6, pady=(4, 0))
        tk.Label(top, text=card.display_id, font=self.font_sm, fg=title_fg, bg=bg).pack(side=tk.LEFT)
        tk.Label(top, text=f"+{score}", font=self.font_sm, fg=sub_fg, bg=bg).pack(side=tk.RIGHT)

        tk.Label(card_frame, text=f"{card.color}  {stars}", font=self.font_sm, fg=title_fg, bg=bg).pack(pady=(2, 2))

        req_lbl = tk.Label(card_frame, text=req_txt, font=self.font_sm, fg=title_fg, bg=bg, wraplength=cw_px - 12, justify=tk.CENTER)
        req_lbl.pack(pady=(0, 2))

        if locked:
            tk.Label(card_frame, text="🔒 锁定", font=self.font_sm, fg=self.t("text_on_card_locked"), bg=bg).pack()

        widgets = [card_frame] + list(card_frame.winfo_children())
        for w in widgets:
            for c in (w.winfo_children() if w is not card_frame else []):
                widgets.append(c) if c not in widgets else None

        if enabled and not locked:
            hover_bg = _lighten(bg)
            normal_bd = 2

            def fire(_e=None, c=card):
                self._pick_target(c)

            def on_enter(_e=None):
                card_frame.config(bd=4, relief=tk.RIDGE, bg=hover_bg)
                for w in card_frame.winfo_children():
                    self._recursive_bg(w, hover_bg)

            def on_leave(_e=None):
                card_frame.config(bd=normal_bd, relief=tk.RAISED, bg=bg)
                for w in card_frame.winfo_children():
                    self._recursive_bg(w, bg)

            for w in [card_frame] + self._all_descendants(card_frame):
                w.bind("<Button-1>", fire)
                w.bind("<Enter>", on_enter)
                w.bind("<Leave>", on_leave)

    @staticmethod
    def _all_descendants(w):
        out = []
        for c in w.winfo_children():
            out.append(c)
            out.extend(TianXiaApp._all_descendants(c))
        return out

    @staticmethod
    def _recursive_bg(w, bg):
        try:
            w.config(bg=bg)
        except tk.TclError:
            pass
        for c in w.winfo_children():
            TianXiaApp._recursive_bg(c, bg)

    def _pick_target(self, card: Card):
        ok, msg = self.state.start_assault(card, self.selecting_opponent)
        if not ok:
            self.toast.show(msg, "error")
        else:
            self.selecting_opponent = False
            self.toast.show(self.state.message, "info")
        self.refresh()

    def _refresh_target(self):
        s = self.state
        self._clear(self.center_col["progress_frame"])
        if s.target and s.phase in (Phase.ROLL_DICE, Phase.PLACE_DICE):
            score = COLOR_INFO[s.target.color]["score"]
            lines = [f"🎯 {s.target.display_id}（{s.target.color} · +{score}分）"]
            if s.target_from_opponent:
                lines.append("⚔ 抢牌 +1 虎符")
            self.center_col["target_labels"].config(text="\n".join(lines))
            for pat, (have, need) in s.progress_display().items():
                row = tk.Frame(self.center_col["progress_frame"], bg=self.t("progress_bg"))
                row.pack(fill=tk.X, pady=2)
                done = have >= need
                tk.Label(
                    row, text=f"{'✓' if done else '○'} {pat}",
                    font=self.font_sm,
                    fg=self.t("progress_ok") if done else self.t("progress_pending"),
                    bg=self.t("progress_bg"),
                    width=8, anchor="w",
                ).pack(side=tk.LEFT)
                pb = ttk.Progressbar(row, length=140, maximum=max(need, 1), value=min(have, need))
                pb.pack(side=tk.LEFT, padx=4)
                tk.Label(
                    row, text=f"{have}/{need}",
                    font=self.font_sm, fg=self.t("progress_label"), bg=self.t("progress_bg"),
                ).pack(side=tk.LEFT)
        else:
            who = s.pname(s.current) if s.phase == Phase.CHOOSE_TARGET else "—"
            self.center_col["target_labels"].config(text=f"（{who} 请选择攻占目标）")

    def _refresh_dice_actions(self):
        """中央骰子区下方的主操作按钮（最醒目）"""
        self._clear(self.center_col["dice_actions"])
        bar = self.center_col["dice_actions"]
        s = self.state

        def big_btn(text, cmd, color="#3d8b5a", enabled=True):
            tk.Button(
                bar, text=text, font=self.font_btn, fg="white", bg=color if enabled else self.t("btn_disabled_bar"),
                activebackground=color, width=18, height=2, state=tk.NORMAL if enabled else tk.DISABLED,
                command=cmd, cursor="hand2",
            ).pack(pady=4)

        if s.phase == Phase.ROLL_DICE and s.dice:
            n = len(s.dice)
            big_btn(
                f"🎲  掷骰（{n} 枚）",
                self._roll,
                color="#2d8a4e",
                enabled=not self._rolling,
            )
            tk.Label(
                bar, text="↑ 掷骰  ·  Shift+滚轮 可横向滑动骰子", font=self.font_sm, fg=self.t("accent"), bg=self.t("side"),
            ).pack()
            big_btn("⊘ 跳过本回合", self._skip_turn, color="#6a5a4a")
        elif s.phase == Phase.PLACE_DICE and s.dice:
            row = tk.Frame(bar, bg=self.t("side"))
            row.pack()
            for text, cmd, color in [
                ("✓ 确认放置", self._confirm, "#2d7a8a"),
                ("🤖 智能选骰", self._smart_pick, "#4a5a8a"),
                ("✗ 无法放置", self._penalty, "#8a4a4a"),
                ("⊘ 跳过", self._skip_turn, "#6a5a4a"),
            ]:
                tk.Button(
                    row, text=text, font=self.font_sm, fg="white", bg=color, width=9, height=2, command=cmd,
                ).pack(side=tk.LEFT, padx=3, pady=4)
        elif s.phase == Phase.CHOOSE_TARGET:
            big_btn("⊘ 跳过本回合", self._skip_turn, color="#6a5a4a")

    def _refresh_dice(self):
        self._clear(self.center_col["dice_inner"])
        self.die_vars = []
        self._dice_anim_labels = []
        s, inner = self.state, self.center_col["dice_inner"]
        if s.phase not in (Phase.ROLL_DICE, Phase.PLACE_DICE) or not s.dice:
            tk.Label(inner, text="—", font=self.font, fg=self.t("text_faint"), bg=self.t("side")).pack()
            return
        n = len(s.dice)
        compact = n > 4
        dice_font = tkfont.Font(family="Microsoft YaHei", size=10 if compact else 13, weight="bold")
        pad = 2 if compact else 5
        cell_w = 3 if compact else 4

        hint = "点击下方绿色按钮掷骰" if s.phase == Phase.ROLL_DICE else "勾选后点「确认放置」"
        tk.Label(inner, text=f"⚡ {s.pname(s.current)}  ·  {hint}", font=self.font_sm, fg=self.t("accent"), bg=self.t("side")).pack(anchor="w")
        row = tk.Frame(inner, bg=self.t("side"))
        row.pack(fill=tk.X, pady=4)
        for i, die in enumerate(s.dice):
            cell = tk.Frame(row, bg=self.t("dice_cell"), relief=tk.RAISED, bd=1 if compact else 2)
            cell.pack(side=tk.LEFT, padx=pad)
            txt = die.pattern_key() if die.face_idx >= 0 else "?"
            lbl = tk.Label(
                cell, text=txt, font=dice_font,
                fg=self.t("accent") if die.face_idx >= 0 else self.t("text_faint"),
                bg=self.t("dice_cell"), width=cell_w, height=1 if compact else 2,
            )
            lbl.pack(padx=3 if compact else 6, pady=3 if compact else 6)
            self._dice_anim_labels.append(lbl)
            if s.phase == Phase.PLACE_DICE:
                var = tk.BooleanVar(value=i in s.selected_dice)
                self.die_vars.append(var)
                def toggle(idx=i, v=var, lb=lbl):
                    if v.get():
                        s.selected_dice.add(idx)
                        lb.config(bg=self.t("dice_selected"))
                    else:
                        s.selected_dice.discard(idx)
                        lb.config(bg=self.t("dice_cell"))
                cb = tk.Checkbutton(cell, variable=var, bg=self.t("dice_cell"), selectcolor=self.t("dice_selected"), command=toggle)
                if i in s.selected_dice:
                    lbl.config(bg=self.t("dice_selected"))
                cb.pack()

        inner.update_idletasks()
        dc = self.center_col.get("dice_canvas")
        if dc:
            dc.configure(scrollregion=dc.bbox("all"))
            if n > 4:
                dc.xview_moveto(0)

    def _skip_turn(self):
        ok, msg = self.state.skip_turn()
        if not ok:
            self.toast.show(msg, "warn")
        else:
            self.toast.show(msg, "warn")
            if self.state.last_event == "fail":
                shake_window(self, intensity=4, times=3)
        self.refresh()

    def _order_roll(self, p: int):
        v, msg = self.state.roll_order_die(p)
        if v < 0:
            self.toast.show(msg, "warn")
        else:
            self.sound.roll()
            kind = "epic" if self.state.phase == Phase.CHOOSE_TARGET else ("warn" if "平局" in msg else "info")
            self.toast.show(msg, kind)
        self.refresh()

    def _set_mode(self, opp: bool):
        self.selecting_opponent = opp
        self.state.message = "点击对手手牌" if opp else "点击中央公共区卡牌"
        self.toast.show(self.state.message, "info")
        self.refresh()

    def _roll(self):
        if self._rolling:
            self.toast.show("正在掷骰，请稍候…", "warn")
            return
        if self.state.phase != Phase.ROLL_DICE or not self.state.dice:
            self.toast.show("当前不能掷骰", "warn")
            return

        self._rolling = True
        labels = list(self._dice_anim_labels)

        def finish():
            try:
                self.state.roll_all_dice()
                self.sound.roll()
                self.toast.show("骰子已落定，请勾选后点「确认放置」", "info")
            finally:
                self._rolling = False
                self.refresh()

        try:
            if not labels:
                finish()
                return
            animate_dice_roll(self, labels, finish, steps=12, base_ms=50)
        except Exception as exc:
            self._rolling = False
            self.toast.show(f"掷骰异常，已直接结算: {exc}", "error")
            self.state.roll_all_dice()
            self.refresh()

    def _smart_pick(self):
        s = self.state
        s.selected_dice = s.suggest_dice_indices()
        if s.selected_dice:
            self.toast.show(f"已智能选中 {len(s.selected_dice)} 枚骰子", "info")
        else:
            self.toast.show("当前无合适骰子可放置", "warn")
        self.refresh()

    def _confirm(self):
        for i, var in enumerate(self.die_vars):
            if var.get():
                self.state.selected_dice.add(i)
            else:
                self.state.selected_dice.discard(i)
        prev_phase = self.state.phase
        ok, msg = self.state.confirm_placement()
        if not ok:
            self.toast.show(msg, "warn")
        else:
            if self.state.phase == Phase.ROLL_DICE:
                self.toast.show(msg or "继续掷剩余骰子", "info")
            elif prev_phase == Phase.PLACE_DICE and self.state.phase == Phase.CHOOSE_TARGET:
                self._toast_for_event()
        self.refresh()

    def _penalty(self):
        ok, msg = self.state.skip_place_penalty()
        if not ok:
            self.toast.show(msg, "warn")
        else:
            if self.state.last_event in ("success", "fail", "lock"):
                self._toast_for_event()
            else:
                self.toast.show(msg or "失去一枚骰子", "warn")
                self.sound.fail()
                shake_window(self, intensity=5, times=4)
        self.refresh()

    def _restart(self):
        names = list(self.state.player_names)
        self.state = GameState()
        self.state.player_names = names
        self.selecting_opponent = False
        self._game_over_shown = False
        self.refresh()
        self.toast.show("新局已开始，公共区已洗牌", "success")


def main():
    TianXiaApp().mainloop()


if __name__ == "__main__":
    main()
