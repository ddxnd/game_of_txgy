# -*- coding: utf-8 -*-
"""天下归一 - 增强体验版（左 | 中 | 右）"""
from __future__ import annotations

import tkinter as tk
from tkinter import font as tkfont
from tkinter import messagebox, ttk

from constants import COLORS as COLOR_INFO, COLOR_LABEL, PATTERN_SYMBOL
from game_logic import GameState, Phase, Card
from ui_effects import SoundManager, ToastBar, animate_dice_roll

SIDE_BG = "#2a3048"
CENTER_BG = "#1c2030"
ACTIVE_BORDER = "#dcb850"
RULES_TEXT = """《天下归一》规则摘要

【目标】占领卡牌、集齐同色，积分高者胜。

【先手】双方各掷 1d6，大者先行；相同则重掷。

【回合】选公共区卡或抢对手手牌（需多 1 虎符）→ 掷 6 枚图案骰 → 选骰放置到卡上（可超额不可不足）→ 剩余骰继续掷；若本轮无骰可放则失去 1 枚骰。

【积分】仅当集齐某颜色全部卡牌时，获得该色难度分（赤12/青10/墨8/金6），并锁定该色不让对手再抢。

【提示】放置阶段可用「智能选骰」；音效可在顶部开关。"""


class TianXiaApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("天下归一")
        self.geometry("1320x800")
        self.minsize(1150, 720)
        self.configure(bg=CENTER_BG)

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
        self.progress_bars: dict[str, ttk.Progressbar] = {}

        self._build_ui()
        self.toast = ToastBar(self, font=self.font)
        self.after(300, self._show_start_dialog)
        self.refresh()

    def _show_start_dialog(self):
        dlg = tk.Toplevel(self)
        dlg.title("开局设置")
        dlg.configure(bg=SIDE_BG)
        dlg.transient(self)
        dlg.grab_set()
        tk.Label(dlg, text="天下归一 · 新局", font=self.font_title, fg=ACTIVE_BORDER, bg=SIDE_BG).pack(pady=12)
        f = tk.Frame(dlg, bg=SIDE_BG)
        f.pack(padx=20, pady=8)
        e0 = tk.Entry(f, font=self.font, width=16)
        e1 = tk.Entry(f, font=self.font, width=16)
        e0.insert(0, "玩家一")
        e1.insert(0, "玩家二")
        tk.Label(f, text="左侧：", fg="#ccc", bg=SIDE_BG, font=self.font).grid(row=0, column=0, sticky="e")
        e0.grid(row=0, column=1, padx=6, pady=4)
        tk.Label(f, text="右侧：", fg="#ccc", bg=SIDE_BG, font=self.font).grid(row=1, column=0, sticky="e")
        e1.grid(row=1, column=1, padx=6, pady=4)

        def ok():
            self.state.player_names[0] = e0.get().strip() or "玩家一"
            self.state.player_names[1] = e1.get().strip() or "玩家二"
            dlg.destroy()
            self.refresh()
            self.toast.show("祝两位征战顺利！", "success")

        tk.Button(dlg, text="开始征战", font=self.font_btn, bg="#4a7a5a", fg="white", command=ok).pack(pady=16)
        dlg.geometry("+%d+%d" % (self.winfo_x() + 200, self.winfo_y() + 120))

    def _build_ui(self):
        top = tk.Frame(self, bg=CENTER_BG)
        top.pack(fill=tk.X, padx=10, pady=6)
        tk.Label(top, text="天下归一", font=self.font_title, fg=ACTIVE_BORDER, bg=CENTER_BG).pack(side=tk.LEFT)
        tk.Button(top, text="📜 规则", font=self.font_sm, command=self._show_rules).pack(side=tk.RIGHT, padx=4)
        self.sound_btn = tk.Button(top, text="🔊 音效", font=self.font_sm, command=self._toggle_sound)
        self.sound_btn.pack(side=tk.RIGHT, padx=4)

        main = tk.Frame(self, bg=CENTER_BG)
        main.pack(fill=tk.BOTH, expand=True, padx=8, pady=4)
        main.columnconfigure(0, weight=1, uniform="c")
        main.columnconfigure(1, weight=2, uniform="c")
        main.columnconfigure(2, weight=1, uniform="c")
        main.rowconfigure(0, weight=1)

        self._build_player_column(main, 0, 0)
        self.center_col = self._build_center_column(main, 1)
        self._build_player_column(main, 2, 1)

        bottom = tk.Frame(self, bg="#243044")
        bottom.pack(fill=tk.X, side=tk.BOTTOM, padx=8, pady=6)
        tk.Label(bottom, textvariable=self.msg_var, font=self.font, fg="#eee", bg="#243044", wraplength=1050).pack(
            fill=tk.X, padx=10, pady=4
        )

    def _build_player_column(self, parent, grid_col: int, player_idx: int):
        outer = tk.Frame(parent, bg=CENTER_BG)
        outer.grid(row=0, column=grid_col, sticky="nsew", padx=4)
        name = self.state.pname(player_idx) if player_idx < len(self.state.player_names) else f"P{player_idx}"
        lf = tk.LabelFrame(outer, text=name, font=self.font_btn, fg="#eee", bg=SIDE_BG, labelanchor="n")
        lf.pack(fill=tk.BOTH, expand=True)

        info = tk.Label(lf, text="", font=self.font_sm, fg="#ccc", bg=SIDE_BG, justify=tk.LEFT, wraplength=280)
        info.pack(anchor="w", padx=10, pady=6)

        color_prog = tk.Frame(lf, bg=SIDE_BG)
        color_prog.pack(fill=tk.X, padx=8)

        order_box = tk.LabelFrame(lf, text="定先手", font=self.font_sm, fg=ACTIVE_BORDER, bg=SIDE_BG)
        order_val = tk.Label(order_box, text="—", font=self.font_dice, fg="#fff", bg=SIDE_BG)
        order_val.pack(pady=4)
        order_btn = tk.Button(
            order_box, text="掷先手骰", font=self.font_sm, width=14, height=2,
            bg="#4a6a9a", fg="white", command=lambda p=player_idx: self._order_roll(p),
        )
        order_btn.pack(pady=(0, 8), padx=8)

        action_box = tk.LabelFrame(lf, text="回合操作", font=self.font_sm, fg="#aad4ff", bg=SIDE_BG)
        action_inner = tk.Frame(action_box, bg=SIDE_BG)
        action_inner.pack(fill=tk.X, padx=6, pady=6)

        hand_lf = tk.LabelFrame(lf, text="手牌", font=self.font_sm, fg="#aaa", bg=SIDE_BG)
        hand_inner = tk.Frame(hand_lf, bg=SIDE_BG)
        hand_inner.pack(fill=tk.BOTH, expand=True, padx=4, pady=4)

        self.player_panels.append({
            "player": player_idx, "frame": lf, "info": info, "color_prog": color_prog,
            "order_box": order_box, "order_val": order_val, "order_btn": order_btn,
            "action_inner": action_inner, "hand_inner": hand_inner,
        })

    def _build_center_column(self, parent, grid_col: int) -> dict:
        center = tk.Frame(parent, bg=CENTER_BG)
        center.grid(row=0, column=grid_col, sticky="nsew", padx=4)

        pub = tk.LabelFrame(center, text="公共区", font=self.font, fg="#eee", bg="#252a3a")
        pub.pack(fill=tk.BOTH, expand=True, pady=(0, 4))
        public_inner = tk.Frame(pub, bg="#252a3a")
        public_inner.pack(fill=tk.BOTH, expand=True, padx=6, pady=6)

        mid = tk.Frame(center, bg=CENTER_BG)
        mid.pack(fill=tk.X, pady=4)

        target_frame = tk.LabelFrame(mid, text="攻占目标", font=self.font, fg=ACTIVE_BORDER, bg="#3a3228")
        target_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 4))
        target_labels = tk.Label(target_frame, text="", font=self.font, fg="#fff", bg="#3a3228", justify=tk.LEFT)
        target_labels.pack(anchor="w", padx=8, pady=4)
        progress_frame = tk.Frame(target_frame, bg="#3a3228")
        progress_frame.pack(fill=tk.X, padx=8, pady=(0, 8))

        dice_frame = tk.LabelFrame(mid, text="本回合骰子", font=self.font, fg="#eee", bg=SIDE_BG)
        dice_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(4, 0))
        dice_inner = tk.Frame(dice_frame, bg=SIDE_BG)
        dice_inner.pack(fill=tk.X, padx=8, pady=8)

        center_actions = tk.Frame(center, bg=CENTER_BG)
        center_actions.pack(fill=tk.X, pady=4)

        log_frame = tk.LabelFrame(center, text="战报", font=self.font_sm, fg="#aaa", bg="#1e2230")
        log_frame.pack(fill=tk.X, pady=4)
        log_text = tk.Text(log_frame, height=5, font=self.font_sm, bg="#151820", fg="#b8c0d0", wrap=tk.WORD, state=tk.DISABLED)
        log_scroll = ttk.Scrollbar(log_frame, command=log_text.yview)
        log_text.configure(yscrollcommand=log_scroll.set)
        log_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=4, pady=4)
        log_scroll.pack(side=tk.RIGHT, fill=tk.Y, pady=4)

        return {
            "public_inner": public_inner, "target_labels": target_labels,
            "progress_frame": progress_frame, "dice_inner": dice_inner,
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
        w.configure(bg=SIDE_BG)
        t = tk.Text(w, font=self.font, wrap=tk.WORD, bg="#252a3a", fg="#eee", padx=12, pady=12)
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
        elif ev == "fail":
            self.toast.show(self.state.message.split("→")[0].strip(), "warn")
            self.sound.fail()
        elif ev == "game_over":
            self.sound.game_over()

    def refresh(self):
        for i, panel in enumerate(self.player_panels):
            panel["frame"].config(text=self.state.pname(i))
        self.msg_var.set(self.state.message)
        self._refresh_players()
        self._refresh_public()
        self._refresh_target()
        self._refresh_dice()
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
                highlightbackground=ACTIVE_BORDER if (active or is_turn) else SIDE_BG,
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
                row = tk.Frame(panel["color_prog"], bg=SIDE_BG)
                row.pack(fill=tk.X, pady=1)
                tk.Label(row, text=f"{COLOR_LABEL.get(color, color)}{mark}", font=self.font_sm, fg=hex_c, bg=SIDE_BG, width=6).pack(side=tk.LEFT)
                pb = ttk.Progressbar(row, length=120, maximum=max(total, 1), value=owned)
                pb.pack(side=tk.LEFT, padx=4)
                tk.Label(row, text=f"{owned}/{total}", font=self.font_sm, fg="#888", bg=SIDE_BG).pack(side=tk.LEFT)

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
            if not p.hand:
                tk.Label(panel["hand_inner"], text="（无）", font=self.font_sm, fg="#666", bg=SIDE_BG).pack()
            else:
                for card in p.hand:
                    self._card_button(
                        panel["hand_inner"], card, small=True,
                        enabled=s.phase == Phase.CHOOSE_TARGET and self.selecting_opponent and card.owner == 1 - s.current,
                    )

    def _fill_player_actions(self, panel: dict):
        s, pi, inner = self.state, panel["player"], panel["action_inner"]
        is_turn = s.current == pi

        def side_btn(text, cmd, enabled=True, color="#4a7a5a"):
            tk.Button(
                inner, text=text, font=self.font_sm, width=16,
                bg=color if enabled else "#3a3f4a", fg="white",
                state=tk.NORMAL if enabled else tk.DISABLED, command=cmd,
            ).pack(pady=3, fill=tk.X)

        if s.phase == Phase.ROLL_ORDER:
            return
        if s.phase == Phase.CHOOSE_TARGET and is_turn:
            side_btn("🎯 公共区", lambda: self._set_mode(False))
            side_btn("⚔ 抢对手牌", lambda: self._set_mode(True), color="#7a4a4a")
            return
        if s.phase == Phase.ROLL_DICE and is_turn:
            side_btn("🎲 掷图案骰", self._roll, enabled=not self._rolling)
            return
        if s.phase == Phase.PLACE_DICE and is_turn:
            side_btn("✓ 确认放置", self._confirm)
            side_btn("🤖 智能选骰", self._smart_pick, color="#4a5a8a")
            side_btn("✗ 无法放置", self._penalty, color="#6a4a4a")
            side_btn("清空选择", lambda: (s.selected_dice.clear(), self.refresh()))
            return
        if not is_turn and s.phase in (Phase.ROLL_DICE, Phase.PLACE_DICE, Phase.CHOOSE_TARGET):
            tk.Label(inner, text="⏳ 等待对手", font=self.font_sm, fg="#888", bg=SIDE_BG).pack(pady=10)

    def _refresh_center_actions(self):
        self._clear(self.center_col["center_actions"])
        s = self.state
        if s.phase == Phase.ROLL_ORDER:
            r0, r1 = s.order_rolls
            tk.Label(
                self.center_col["center_actions"],
                text=f"⚔ 定先手  {s.pname(0)}:{r0 or '—'}  VS  {s.pname(1)}:{r1 or '—'}"
                     + (f"  （平局×{s.order_tie_count}）" if s.order_tie_count else ""),
                font=self.font, fg=ACTIVE_BORDER, bg=CENTER_BG,
            ).pack()
        elif s.phase == Phase.GAME_OVER:
            tk.Button(self.center_col["center_actions"], text="🔄 再来一局", font=self.font_btn,
                      bg="#8a6040", fg="white", command=self._restart).pack(pady=4)
        elif s.phase == Phase.CHOOSE_TARGET:
            mode = "抢对手手牌" if self.selecting_opponent else "攻占公共区"
            tk.Label(self.center_col["center_actions"], text=f"模式：{mode}", font=self.font, fg="#aad4ff", bg=CENTER_BG).pack()

    def _refresh_public(self):
        self._clear(self.center_col["public_inner"])
        public = self.state.public_cards()
        inner = self.center_col["public_inner"]
        if not public:
            tk.Label(inner, text="（公共区已空）", font=self.font, fg="#888", bg="#252a3a").pack(pady=20)
            return
        row = tk.Frame(inner, bg="#252a3a")
        row.pack()
        for i, card in enumerate(public):
            if i and i % 4 == 0:
                row = tk.Frame(inner, bg="#252a3a")
                row.pack()
            locked = self.state.is_color_locked_by_opponent(self.state.current, card.color)
            self._card_button(row, card, enabled=self.state.phase == Phase.CHOOSE_TARGET and not self.selecting_opponent and not locked, locked=locked)

    def _card_button(self, parent, card: Card, small=False, enabled=True, locked=False):
        rgb = COLOR_INFO[card.color]["rgb"]
        hex_c = "#%02x%02x%02x" % rgb
        req_txt = " ".join(f"{PATTERN_SYMBOL.get(k, k[0])}×{v}" for k, v in card.req.items())
        diff = sum(card.req.values())
        stars = "★" * min(diff // 4, 3)
        txt = f"{card.display_id}·{card.color}{stars}\n{req_txt}"
        if locked:
            txt += "\n🔒"
        tk.Button(
            parent, text=txt, font=self.font_sm if small else self.font,
            width=11 if small else 13, height=3 if small else 4,
            bg=hex_c if not locked else "#444", fg="white", activebackground=hex_c,
            state=tk.NORMAL if enabled else tk.DISABLED,
            command=lambda c=card: self._pick_target(c),
        ).pack(side=tk.LEFT, padx=3, pady=3)

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
        self.progress_bars.clear()
        if s.target and s.phase in (Phase.ROLL_DICE, Phase.PLACE_DICE):
            lines = [f"🎯 {s.target.display_id}（{s.target.color}）"]
            if s.target_from_opponent:
                lines.append("⚔ 抢牌 +1 虎符")
            self.center_col["target_labels"].config(text="\n".join(lines))
            if s.phase == Phase.PLACE_DICE:
                for pat, (have, need) in s.progress_display().items():
                    row = tk.Frame(self.center_col["progress_frame"], bg="#3a3228")
                    row.pack(fill=tk.X, pady=2)
                    sym = PATTERN_SYMBOL.get(pat, pat[0])
                    done = have >= need
                    tk.Label(row, text=f"{'✓' if done else '○'} {sym}{pat}", font=self.font_sm,
                             fg="#8f8" if done else "#ddd", bg="#3a3228", width=10, anchor="w").pack(side=tk.LEFT)
                    pb = ttk.Progressbar(row, length=140, maximum=max(need, 1), value=min(have, need))
                    pb.pack(side=tk.LEFT, padx=4)
                    tk.Label(row, text=f"{have}/{need}", font=self.font_sm, fg="#ccc", bg="#3a3228").pack(side=tk.LEFT)
                    self.progress_bars[pat] = pb
            else:
                for pat, n in s.effective_req(s.target, s.target_from_opponent).items():
                    row = tk.Frame(self.center_col["progress_frame"], bg="#3a3228")
                    row.pack(fill=tk.X, pady=1)
                    tk.Label(row, text=f"· {PATTERN_SYMBOL.get(pat, '')}{pat} ×{n}", font=self.font_sm, fg="#ccc", bg="#3a3228").pack(anchor="w")
        else:
            who = s.pname(s.current) if s.phase == Phase.CHOOSE_TARGET else "—"
            self.center_col["target_labels"].config(text=f"（{who} 请选择攻占目标）")

    def _refresh_dice(self):
        self._clear(self.center_col["dice_inner"])
        self.die_vars = []
        self._dice_anim_labels = []
        s, inner = self.state, self.center_col["dice_inner"]
        if s.phase not in (Phase.ROLL_DICE, Phase.PLACE_DICE) or not s.dice:
            tk.Label(inner, text="—", font=self.font, fg="#888", bg=SIDE_BG).pack()
            return
        tk.Label(inner, text=f"⚡ {s.pname(s.current)}", font=self.font_sm, fg=ACTIVE_BORDER, bg=SIDE_BG).pack(anchor="w")
        row = tk.Frame(inner, bg=SIDE_BG)
        row.pack(fill=tk.X, pady=6)
        for i, die in enumerate(s.dice):
            cell = tk.Frame(row, bg="#3d4558", relief=tk.RAISED, bd=2)
            cell.pack(side=tk.LEFT, padx=5)
            txt = die.pattern_key() if die.face_idx >= 0 else "?"
            lbl = tk.Label(cell, text=txt, font=self.font_dice, fg=ACTIVE_BORDER if die.face_idx >= 0 else "#888",
                           bg="#3d4558", width=5, height=2)
            lbl.pack(padx=6, pady=6)
            self._dice_anim_labels.append(lbl)
            if s.phase == Phase.PLACE_DICE:
                var = tk.BooleanVar(value=i in s.selected_dice)
                self.die_vars.append(var)
                def toggle(idx=i, v=var, lb=lbl):
                    if v.get():
                        s.selected_dice.add(idx)
                        lb.config(bg="#4a6a4a")
                    else:
                        s.selected_dice.discard(idx)
                        lb.config(bg="#3d4558")
                cb = tk.Checkbutton(cell, variable=var, bg="#3d4558", selectcolor="#4a6a4a", command=toggle)
                if i in s.selected_dice:
                    lbl.config(bg="#4a6a4a")
                cb.pack()

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
            return
        self._rolling = True
        labels = self._dice_anim_labels
        if not labels:
            self.state.roll_all_dice()
            self.sound.roll()
            self._rolling = False
            self.refresh()
            return

        def finish():
            self.state.roll_all_dice()
            self.sound.roll()
            self._rolling = False
            self.toast.show("骰子已落定，请选择放置", "info")
            self.refresh()

        animate_dice_roll(self, labels, finish, steps=12, interval_ms=60)

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
