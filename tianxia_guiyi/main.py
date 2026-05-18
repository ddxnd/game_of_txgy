# -*- coding: utf-8 -*-
"""
天下归一 - Windows 桌游
运行: python main.py
"""
from __future__ import annotations

import os
import sys
import time

import pygame

from constants import (
    COLORS as COLOR_INFO,
    PATTERN_SYMBOL,
    SCREEN_W,
    SCREEN_H,
)
from game_logic import GameState, Phase, Card

# 字体
def load_font(size: int, bold: bool = False) -> pygame.font.Font:
    paths = [
        r"C:\Windows\Fonts\msyh.ttc",
        r"C:\Windows\Fonts\simhei.ttf",
        r"C:\Windows\Fonts\simsun.ttc",
    ]
    for p in paths:
        if os.path.isfile(p):
            return pygame.font.Font(p, size)
    return pygame.font.SysFont("microsoftyahei,simhei", size, bold=bold)


# 颜色
BG = (28, 32, 48)
PANEL = (42, 48, 68)
ACCENT = (220, 180, 80)
TEXT = (240, 240, 245)
SUBTEXT = (180, 185, 200)
BTN = (70, 110, 160)
BTN_HOVER = (90, 140, 200)
BTN_DISABLED = (55, 58, 72)
GREEN = (80, 180, 120)
RED = (200, 90, 90)


class Button:
    def __init__(self, rect, text, callback=None, enabled=True):
        self.rect = pygame.Rect(rect)
        self.text = text
        self.callback = callback
        self.enabled = enabled
        self.hover = False

    def draw(self, surf, font):
        c = BTN_HOVER if self.hover and self.enabled else BTN
        if not self.enabled:
            c = BTN_DISABLED
        pygame.draw.rect(surf, c, self.rect, border_radius=8)
        pygame.draw.rect(surf, ACCENT, self.rect, 2, border_radius=8)
        t = font.render(self.text, True, TEXT if self.enabled else SUBTEXT)
        surf.blit(t, t.get_rect(center=self.rect.center))

    def handle(self, event) -> bool:
        if event.type == pygame.MOUSEMOTION:
            self.hover = self.rect.collidepoint(event.pos)
        if event.type == pygame.MOUSEBUTTONUP and event.button == 1:
            if self.enabled and self.rect.collidepoint(event.pos) and self.callback:
                self.callback()
                return True
        return False


class GameApp:
    def __init__(self):
        pygame.init()
        pygame.display.set_caption("天下归一")
        self.screen = pygame.display.set_mode((SCREEN_W, SCREEN_H))
        self.clock = pygame.time.Clock()
        self.font = load_font(20)
        self.font_sm = load_font(16)
        self.font_lg = load_font(28, bold=True)
        self.font_title = load_font(36, bold=True)
        self.state = GameState()
        self.buttons: list[Button] = []
        self.card_rects: dict[int, pygame.Rect] = {}
        self.die_rects: list[pygame.Rect] = []
        self.selecting_opponent = False
        self.roll_anim_until = 0.0
        self._build_buttons()

    def _build_buttons(self):
        self.buttons = []

    def _add_btn(self, rect, text, cb, enabled=True):
        b = Button(rect, text, cb, enabled)
        self.buttons.append(b)
        return b

    def _rebuild_phase_buttons(self):
        self.buttons.clear()
        s = self.state
        y = SCREEN_H - 72

        if s.phase == Phase.ROLL_ORDER:
            turn = s.order_roll_whose_turn()
            if turn == 0:
                self._add_btn(
                    (SCREEN_W // 2 - 220, y, 200, 48),
                    "玩家一 掷骰",
                    lambda _p=0: self._order_roll(_p),
                )
            elif turn == 1:
                self._add_btn(
                    (SCREEN_W // 2 + 20, y, 200, 48),
                    "玩家二 掷骰",
                    lambda _p=1: self._order_roll(_p),
                )
        elif s.phase == Phase.CHOOSE_TARGET:
            self._add_btn(
                (40, y, 160, 48),
                "选公共卡" if not self.selecting_opponent else "← 公共区",
                self._toggle_opponent_select,
            )
            self._add_btn(
                (220, y, 160, 48),
                "抢对手手牌",
                lambda: self._set_opponent_select(True),
            )
        elif s.phase == Phase.ROLL_DICE:
            self._add_btn((SCREEN_W // 2 - 100, y, 200, 48), "掷骰", self._do_roll)
        elif s.phase == Phase.PLACE_DICE:
            self._add_btn((SCREEN_W // 2 - 280, y, 160, 48), "确认放置", self._confirm_place)
            self._add_btn((SCREEN_W // 2 - 80, y, 160, 48), "无法放置(-1骰)", self._skip_penalty)
            self._add_btn((SCREEN_W // 2 + 120, y, 160, 48), "重新选骰", lambda: s.selected_dice.clear())
        elif s.phase == Phase.GAME_OVER:
            self._add_btn((SCREEN_W // 2 - 100, y, 200, 48), "再来一局", self._restart)

    def _toggle_opponent_select(self):
        self.selecting_opponent = not self.selecting_opponent

    def _set_opponent_select(self, v: bool):
        self.selecting_opponent = v

    def _do_roll(self):
        self.state.roll_all_dice()
        self.roll_anim_until = time.time() + 0.35
        self._rebuild_phase_buttons()

    def _confirm_place(self):
        ok, msg = self.state.confirm_placement()
        if not ok:
            self.state.message = msg
        self._rebuild_phase_buttons()

    def _skip_penalty(self):
        ok, msg = self.state.skip_place_penalty()
        if not ok:
            self.state.message = msg
        self._rebuild_phase_buttons()

    def _restart(self):
        self.state = GameState()
        self.selecting_opponent = False
        self._rebuild_phase_buttons()

    def _order_roll(self, player: int):
        v, msg = self.state.roll_order_die(player)
        if v >= 0:
            self.state.message = msg
        self._rebuild_phase_buttons()

    def _on_card_click(self, card: Card):
        s = self.state
        if s.phase != Phase.CHOOSE_TARGET:
            return
        from_opp = self.selecting_opponent
        ok, msg = s.start_assault(card, from_opp)
        if not ok:
            s.message = msg
        else:
            self.selecting_opponent = False
        self._rebuild_phase_buttons()

    def _on_die_click(self, idx: int):
        if self.state.phase == Phase.PLACE_DICE:
            self.state.toggle_die_selection(idx)

    def run(self):
        self._rebuild_phase_buttons()
        running = True
        while running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                elif event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                    running = False
                else:
                    for b in self.buttons:
                        b.handle(event)
                    if event.type == pygame.MOUSEBUTTONUP and event.button == 1:
                        self._handle_click(event.pos)

            self.draw()
            pygame.display.flip()
            self.clock.tick(60)
        pygame.quit()

    def _handle_click(self, pos):
        for cid, rect in self.card_rects.items():
            if rect.collidepoint(pos):
                card = next((c for c in self.state.public if c.id == cid), None)
                if card is None:
                    for p in self.state.players:
                        for c in p.hand:
                            if c.id == cid:
                                card = c
                                break
                if card and (
                    self.state.phase != Phase.CHOOSE_TARGET
                    or (card.owner is None and not self.selecting_opponent)
                    or (card.owner == 1 - self.state.current and self.selecting_opponent)
                ):
                    self._on_card_click(card)
                return
        for i, rect in enumerate(self.die_rects):
            if rect.collidepoint(pos):
                self._on_die_click(i)
                return

    def draw(self):
        self.screen.fill(BG)
        self.card_rects.clear()
        self.die_rects.clear()

        title = self.font_title.render("天下归一", True, ACCENT)
        self.screen.blit(title, (SCREEN_W // 2 - title.get_width() // 2, 12))

        self._draw_players()
        self._draw_public()
        self._draw_target_panel()
        self._draw_dice()
        self._draw_message()
        for b in self.buttons:
            b.draw(self.screen, self.font)

    def _draw_players(self):
        s = self.state
        for pi in range(2):
            x = 40 if pi == 0 else SCREEN_W - 340
            p = s.players[pi]
            active = s.current == pi and s.phase not in (Phase.GAME_OVER, Phase.ROLL_ORDER)
            border = ACCENT if active else (80, 80, 100)
            panel = pygame.Rect(x, 56, 300, 200)
            pygame.draw.rect(self.screen, PANEL, panel, border_radius=10)
            pygame.draw.rect(self.screen, border, panel, 3, border_radius=10)

            name = f"玩家{'一' if pi == 0 else '二'}"
            if s.phase == Phase.ROLL_ORDER and s.order_rolls[pi] is not None:
                name += f"  先手骰:{s.order_rolls[pi]}"
            t = self.font_lg.render(name, True, ACCENT if active else TEXT)
            self.screen.blit(t, (x + 12, 64))

            sc = self.font.render(f"积分: {p.score}", True, GREEN)
            self.screen.blit(sc, (x + 12, 100))
            locked = "、".join(p.locked_colors) if p.locked_colors else "无"
            self.screen.blit(self.font_sm.render(f"锁定颜色: {locked}", True, SUBTEXT), (x + 12, 128))

            hy = 156
            for c in p.hand[:4]:
                self._draw_mini_card(c, x + 12 + (c.id % 4) * 68, hy, clickable=s.phase == Phase.CHOOSE_TARGET and self.selecting_opponent)
            if len(p.hand) > 4:
                extra = self.font_sm.render(f"+{len(p.hand)-4}张", True, SUBTEXT)
                self.screen.blit(extra, (x + 12, hy + 50))

    def _draw_public(self):
        s = self.state
        label = self.font.render("公共区", True, TEXT)
        self.screen.blit(label, (SCREEN_W // 2 - 30, 270))
        public = [c for c in s.public if c.owner is None]
        if not public:
            t = self.font_sm.render("（公共区已空）", True, SUBTEXT)
            self.screen.blit(t, (SCREEN_W // 2 - 50, 300))
            return
        cols = 5
        cw, ch = 118, 150
        start_x = SCREEN_W // 2 - (cols * (cw + 8)) // 2
        for i, card in enumerate(public):
            row, col = i // cols, i % cols
            x = start_x + col * (cw + 8)
            y = 300 + row * (ch + 10)
            locked = s.is_color_locked_by_opponent(s.current, card.color)
            self._draw_card(card, x, y, cw, ch, clickable=s.phase == Phase.CHOOSE_TARGET and not self.selecting_opponent, locked=locked)

    def _draw_target_panel(self):
        s = self.state
        if not s.target or s.phase not in (Phase.ROLL_DICE, Phase.PLACE_DICE):
            return
        panel = pygame.Rect(SCREEN_W // 2 - 200, 56, 400, 200)
        pygame.draw.rect(self.screen, (55, 45, 35), panel, border_radius=10)
        pygame.draw.rect(self.screen, ACCENT, panel, 2, border_radius=10)
        t = self.font.render(f"攻占目标 {s.target.display_id}", True, ACCENT)
        self.screen.blit(t, (panel.x + 12, panel.y + 8))
        if s.target_from_opponent:
            self.screen.blit(self.font_sm.render("（对手手牌 +1 虎符）", True, RED), (panel.x + 12, panel.y + 34))

        y = panel.y + 58
        if s.phase == Phase.PLACE_DICE:
            for pat, (have, need) in s.progress_display().items():
                sym = PATTERN_SYMBOL.get(pat, pat[0])
                color = GREEN if have >= need else TEXT
                line = self.font.render(f"{pat}  {have}/{need}  [{sym}]", True, color)
                self.screen.blit(line, (panel.x + 12, y))
                y += 26
        else:
            eff = s.effective_req(s.target, s.target_from_opponent)
            for pat, need in eff.items():
                sym = PATTERN_SYMBOL.get(pat, pat[0])
                line = self.font.render(f"{pat} ×{need}  [{sym}]", True, TEXT)
                self.screen.blit(line, (panel.x + 12, y))
                y += 26

    def _draw_dice(self):
        s = self.state
        if s.phase not in (Phase.ROLL_DICE, Phase.PLACE_DICE) or not s.dice:
            return
        label = self.font.render(f"骰子（剩余 {len(s.dice)} 枚）", True, TEXT)
        self.screen.blit(label, (SCREEN_W // 2 - 80, 520))
        dx = SCREEN_W // 2 - (len(s.dice) * 72) // 2
        for i, die in enumerate(s.dice):
            rect = pygame.Rect(dx + i * 76, 550, 68, 68)
            self.die_rects.append(rect)
            sel = i in s.selected_dice
            c = (90, 140, 90) if sel else (90, 85, 75)
            pygame.draw.rect(self.screen, c, rect, border_radius=8)
            pygame.draw.rect(self.screen, ACCENT if sel else (120, 115, 105), rect, 3, border_radius=8)
            if s.phase == Phase.PLACE_DICE and die.face_idx >= 0:
                txt = die.pattern_key()
                sym = PATTERN_SYMBOL.get(txt.split("×")[0], txt[:1])
                if "×" in txt:
                    sym = f"{sym}\n{txt.split('×')[1]}"
                lines = txt.split("×")
                if len(lines) == 2:
                    t1 = self.font_sm.render(lines[0][:2], True, TEXT)
                    t2 = self.font.render(lines[1], True, ACCENT)
                    self.screen.blit(t1, (rect.centerx - t1.get_width() // 2, rect.y + 8))
                    self.screen.blit(t2, (rect.centerx - t2.get_width() // 2, rect.y + 32))
                else:
                    t1 = self.font.render(sym, True, TEXT)
                    self.screen.blit(t1, t1.get_rect(center=rect.center))
            else:
                q = self.font_lg.render("?", True, SUBTEXT)
                self.screen.blit(q, q.get_rect(center=rect.center))

    def _draw_card(self, card: Card, x, y, w, h, clickable=False, locked=False):
        rgb = COLOR_INFO[card.color]["rgb"]
        rect = pygame.Rect(x, y, w, h)
        self.card_rects[card.id] = rect
        if locked:
            pygame.draw.rect(self.screen, (50, 50, 55), rect, border_radius=8)
        else:
            pygame.draw.rect(self.screen, rgb, rect, border_radius=8)
        pygame.draw.rect(self.screen, (20, 20, 30), rect, 2, border_radius=8)
        if clickable:
            pygame.draw.rect(self.screen, ACCENT, rect, 3, border_radius=8)

        id_t = self.font_sm.render(card.display_id, True, (255, 255, 255))
        self.screen.blit(id_t, (x + 6, y + 6))
        col_t = self.font_sm.render(card.color, True, (255, 255, 220))
        self.screen.blit(col_t, (x + w - 28, y + 6))

        py = y + 28
        for pat, cnt in card.req.items():
            sym = PATTERN_SYMBOL.get(pat, "?")
            line = self.font_sm.render(f"{sym}×{cnt}", True, (255, 255, 255))
            self.screen.blit(line, (x + 8, py))
            py += 20
        if locked:
            lk = self.font_sm.render("已锁定", True, SUBTEXT)
            self.screen.blit(lk, (x + 8, y + h - 22))

    def _draw_mini_card(self, card: Card, x, y, clickable=False):
        w, h = 62, 80
        self._draw_card(card, x, y, w, h, clickable=clickable)

    def _draw_message(self):
        panel = pygame.Rect(40, SCREEN_H - 130, SCREEN_W - 80, 48)
        pygame.draw.rect(self.screen, PANEL, panel, border_radius=8)
        msg = self.state.message
        if len(msg) > 60:
            msg = msg[:58] + "…"
        t = self.font.render(msg, True, TEXT)
        self.screen.blit(t, (52, SCREEN_H - 118))


def main():
    try:
        app = GameApp()
        app.run()
    except Exception as e:
        import traceback
        traceback.print_exc()
        input("按回车退出…")
        sys.exit(1)


if __name__ == "__main__":
    main()
