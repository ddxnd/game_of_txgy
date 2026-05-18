# -*- coding: utf-8 -*-
"""天下归一 - 核心规则引擎"""
from __future__ import annotations

import random
from dataclasses import dataclass, field
from enum import Enum, auto
from typing import Dict, List, Optional, Set, Tuple

from constants import (
    COLORS,
    PUBLIC_CARDS,
    TIGER,
    DIE_FACES,
    MAX_DICE,
    FLAVOR_LINES,
)

# 比标准 random 更难预测，用于先手与图案骰
_rng = random.SystemRandom()


def roll_d6() -> int:
    return _rng.randint(1, 6)


class Phase(Enum):
    ROLL_ORDER = auto()       # 比大小定先手
    CHOOSE_TARGET = auto()    # 选攻占目标
    ROLL_DICE = auto()        # 掷骰
    PLACE_DICE = auto()       # 选择放置
    TURN_END = auto()         # 回合结算提示
    GAME_OVER = auto()


@dataclass
class Card:
    id: int
    color: str
    req: Dict[str, int]
    owner: Optional[int] = None  # None=公共区, 0/1=玩家

    def copy_req(self) -> Dict[str, int]:
        return dict(self.req)

    @property
    def display_id(self) -> str:
        return f"C{self.id}"


@dataclass
class Die:
    index: int
    face_idx: int = -1  # -1 未掷

    def roll(self) -> Dict[str, int]:
        self.face_idx = _rng.randint(0, len(DIE_FACES) - 1)
        return dict(DIE_FACES[self.face_idx])

    def face_value(self) -> Dict[str, int]:
        if self.face_idx < 0:
            return {}
        return dict(DIE_FACES[self.face_idx])

    def pattern_key(self) -> str:
        """用于 UI 显示的单行描述"""
        v = self.face_value()
        if not v:
            return "?"
        k, n = next(iter(v.items()))
        return f"{k}×{n}" if n > 1 else k


@dataclass
class PlayerState:
    hand: List[Card] = field(default_factory=list)
    locked_colors: Set[str] = field(default_factory=set)
    score: int = 0

    def add_card(self, card: Card) -> None:
        self.hand.append(card)

    def recalc_score(self) -> None:
        self.score = 0
        for color in self.locked_colors:
            self.score += COLORS[color]["score"]

    def try_lock_color(self, color: str, color_cards: List[Card]) -> bool:
        """集齐该色所有卡则锁定并计分"""
        owned = {c.id for c in self.hand if c.color == color}
        needed = {c.id for c in color_cards}
        if owned >= needed:
            self.locked_colors.add(color)
            return True
        return False


class GameState:
    def __init__(self, shuffle_public: bool = True):
        self.public: List[Card] = []
        self.players: List[PlayerState] = [PlayerState(), PlayerState()]
        self.player_names: List[str] = ["玩家一", "玩家二"]
        self.current: int = 0
        self.phase: Phase = Phase.ROLL_ORDER
        self.order_rolls: List[Optional[int]] = [None, None]
        self.order_tie_count: int = 0
        self.turn_number: int = 0
        self.target: Optional[Card] = None
        self.target_from_opponent: bool = False
        self.dice: List[Die] = []
        self.dice_count: int = MAX_DICE
        self.progress: Dict[str, int] = {}
        self.selected_dice: Set[int] = set()
        self.message: str = "欢迎来到《天下归一》！左右两侧各掷先手骰，点数大者先行。"
        self.winner: Optional[int] = None
        self.log: List[str] = []
        self.last_event: str = ""  # success | fail | lock | order | normal | warn | game_over
        self.last_locked_color: Optional[str] = None
        self._init_cards(shuffle_public)

    def pname(self, i: int) -> str:
        return self.player_names[i]

    def add_log(self, text: str) -> None:
        self.log.append(text)
        if len(self.log) > 80:
            self.log = self.log[-80:]

    def color_progress(self, player: int) -> Dict[str, Tuple[int, int, int]]:
        """颜色 -> (已有张数, 总张数, 该色积分)"""
        out: Dict[str, Tuple[int, int, int]] = {}
        for color in COLORS:
            total = len([c for c in PUBLIC_CARDS if c["color"] == color])
            owned = len([c for c in self.players[player].hand if c.color == color])
            out[color] = (owned, total, COLORS[color]["score"])
        return out

    def _init_cards(self, shuffle: bool) -> None:
        self.public = [
            Card(c["id"], c["color"], c["req"].copy()) for c in PUBLIC_CARDS
        ]
        if shuffle:
            _rng.shuffle(self.public)
        self.add_log("── 新局开始，公共区卡牌已就位 ──")
        self._cards_by_color: Dict[str, List[Card]] = {}
        for c in self.public:
            self._cards_by_color.setdefault(c.color, []).append(c)
        self._all_template = {c.id: c for c in self.public}

    def all_cards_of_color(self, color: str) -> List[Card]:
        return [c for c in self.public if c.color == color] + [
            c for p in self.players for c in p.hand if c.color == color
        ]

    def color_total_ids(self, color: str) -> Set[int]:
        return {c["id"] for c in PUBLIC_CARDS if c["color"] == color}

    def public_cards(self) -> List[Card]:
        return [c for c in self.public if c.owner is None]

    def opponent_hand(self, player: int) -> List[Card]:
        return self.players[1 - player].hand

    def is_color_locked_by_opponent(self, player: int, color: str) -> bool:
        return color in self.players[1 - player].locked_colors

    def is_color_locked_by_any(self, color: str) -> bool:
        return any(color in p.locked_colors for p in self.players)

    def _has_legal_target(self, player: int) -> bool:
        for c in self.public_cards():
            if not self.is_color_locked_by_opponent(player, c.color):
                return True
        for c in self.opponent_hand(player):
            if not self.is_color_locked_by_opponent(player, c.color):
                return True
        return False

    def game_finished(self) -> bool:
        if all(c.owner is not None for c in self.public):
            return True
        if not self._has_legal_target(0) and not self._has_legal_target(1):
            return True
        return False

    def _finalize_game_over(self) -> None:
        self.phase = Phase.GAME_OVER
        s0, s1 = self.players[0].score, self.players[1].score
        if s0 > s1:
            self.winner = 0
            self.message = f"游戏结束！{self.pname(0)} 获胜（{s0}:{s1}）"
        elif s1 > s0:
            self.winner = 1
            self.message = f"游戏结束！{self.pname(1)} 获胜（{s1}:{s0}）"
        else:
            self.winner = None
            self.message = f"游戏结束！平局（{s0}:{s1}）"
        self.last_event = "game_over"
        self.add_log(self.message)

    def _check_game_over(self) -> None:
        if self.game_finished():
            self._finalize_game_over()

    def maybe_auto_pass(self) -> Optional[str]:
        """当前玩家无可攻占目标 → 跳过；若双方都困死 → 终局。返回提示文本或 None。"""
        if self.phase != Phase.CHOOSE_TARGET:
            return None
        cur = self.current
        if self._has_legal_target(cur):
            return None
        if not self._has_legal_target(1 - cur):
            self._finalize_game_over()
            return self.message
        skipped = self.pname(cur)
        self.current = 1 - cur
        self.last_event = "warn"
        msg = f"⊘ {skipped} 无可攻占目标，自动跳过 → 轮到 {self.pname(self.current)}"
        self.message = msg
        self.add_log(msg)
        return msg

    # --- 先手 ---
    def order_roll_whose_turn(self) -> Optional[int]:
        """当前应由哪位玩家掷先手骰；双方都已掷则返回 None"""
        if self.phase != Phase.ROLL_ORDER:
            return None
        if self.order_rolls[0] is None:
            return 0
        if self.order_rolls[1] is None:
            return 1
        return None

    def roll_order_die(self, player: int) -> Tuple[int, str]:
        """掷先手骰。返回 (点数, 提示信息)；若不应由该玩家掷则点数为 -1"""
        if self.phase != Phase.ROLL_ORDER:
            return -1, "当前不是定先手阶段。"
        expected = self.order_roll_whose_turn()
        if expected is None:
            return -1, "双方已掷完，请等待系统判定。"
        if player != expected:
            who = "玩家一" if expected == 0 else "玩家二"
            return -1, f"请由{who}掷骰（需按顺序各掷一次）。"
        if self.order_rolls[player] is not None:
            return -1, "您本轮已掷过，请让对手掷骰。"

        v = roll_d6()
        self.order_rolls[player] = v
        if self.order_rolls[0] is not None and self.order_rolls[1] is not None:
            a, b = self.order_rolls[0], self.order_rolls[1]
            if a > b:
                self.current = 0
                self.phase = Phase.CHOOSE_TARGET
                self.last_event = "order"
                msg = f"先手：{self.pname(0)} {a} 点 > {self.pname(1)} {b} 点，{self.pname(0)} 先行！"
                self.message = msg
                self.add_log(msg)
                return v, msg
            if b > a:
                self.current = 1
                self.phase = Phase.CHOOSE_TARGET
                self.last_event = "order"
                msg = f"先手：{self.pname(1)} {b} 点 > {self.pname(0)} {a} 点，{self.pname(1)} 先行！"
                self.message = msg
                self.add_log(msg)
                return v, msg
            self.order_tie_count += 1
            self.order_rolls = [None, None]
            self.last_event = "normal"
            msg = f"平局 {a}:{b}（第 {self.order_tie_count} 次），请重新各掷一次。"
            self.message = msg
            self.add_log(msg)
            return v, msg

        msg = f"{self.pname(player)} 掷出 {v} 点，请 {self.pname(1 - player)} 掷骰。"
        self.message = msg
        self.last_event = "normal"
        return v, msg

    # --- 选目标 ---
    def can_target_card(self, card: Card, from_opponent: bool) -> Tuple[bool, str]:
        if card.owner is None:
            if self.is_color_locked_by_opponent(self.current, card.color):
                return False, "该颜色已被对手集齐锁定，不可攻占。"
            return True, ""
        if from_opponent and card.owner == 1 - self.current:
            if self.is_color_locked_by_opponent(self.current, card.color):
                return False, "该颜色已被对手锁定。"
            return True, ""
        return False, "不能攻占此卡。"

    def effective_req(self, card: Card, from_opponent: bool) -> Dict[str, int]:
        req = card.copy_req()
        if from_opponent:
            req[TIGER] = req.get(TIGER, 0) + 1
        return req

    def start_assault(self, card: Card, from_opponent: bool) -> Tuple[bool, str]:
        ok, msg = self.can_target_card(card, from_opponent)
        if not ok:
            return False, msg
        self.target = card
        self.target_from_opponent = from_opponent
        self.progress = {k: 0 for k in self.effective_req(card, from_opponent)}
        self.dice_count = MAX_DICE
        self.dice = [Die(i) for i in range(self.dice_count)]
        self.selected_dice = set()
        self.phase = Phase.ROLL_DICE
        self.turn_number += 1
        extra = "（+1虎符）" if from_opponent else ""
        src = "对手手牌" if from_opponent else "公共区"
        self.message = (
            f"第 {self.turn_number} 回合 · {self.pname(self.current)} 攻占 {card.display_id}"
            f"（{src}{extra}），请掷 {self.dice_count} 枚骰子。"
        )
        self.add_log(self.message)
        self.last_event = "normal"
        return True, ""

    # --- 掷骰 ---
    def roll_all_dice(self) -> None:
        self.dice = [Die(i) for i in range(len(self.dice))]
        for d in self.dice:
            d.roll()
        self.selected_dice = set()
        self.phase = Phase.PLACE_DICE
        self.message = "请选择要放置到卡牌上的骰子（可超额），然后点击「确认放置」。"

    def toggle_die_selection(self, idx: int) -> None:
        if self.phase != Phase.PLACE_DICE:
            return
        if idx in self.selected_dice:
            self.selected_dice.discard(idx)
        else:
            self.selected_dice.add(idx)

    def _remaining_need(self) -> Dict[str, int]:
        eff = self.effective_req(self.target, self.target_from_opponent)
        return {k: max(0, eff[k] - self.progress.get(k, 0)) for k in eff}

    def _placement_valid(self, placement: Dict[str, int]) -> Tuple[bool, str]:
        """放置的图案必须对得上剩余需求中的类型，数量可超额"""
        need = self._remaining_need()
        if not any(need.values()):
            return False, "图案已全部匹配。"
        for pat, cnt in placement.items():
            if pat not in need:
                return False, f"卡牌不需要图案：{pat}"
            if cnt <= 0:
                return False, "数量无效。"
        return True, ""

    def selected_placement(self) -> Dict[str, int]:
        total: Dict[str, int] = {}
        for i in self.selected_dice:
            for k, v in self.dice[i].face_value().items():
                total[k] = total.get(k, 0) + v
        return total

    def suggest_dice_indices(self) -> Set[int]:
        """智能选骰：优先满足剩余需求中缺口最大的图案"""
        if self.phase != Phase.PLACE_DICE:
            return set()
        need = self._remaining_need()
        if not any(need.values()):
            return set()
        picked: Set[int] = set()
        need_left = dict(need)
        for _ in range(len(self.dice)):
            best_i, best_score = -1, -1
            for i, d in enumerate(self.dice):
                if i in picked:
                    continue
                fv = d.face_value()
                score = 0
                for pat, cnt in fv.items():
                    if pat in need_left and need_left[pat] > 0:
                        score += min(cnt, need_left[pat]) * 10 + need_left[pat]
                if score > best_score:
                    best_score, best_i = score, i
            if best_i < 0 or best_score <= 0:
                break
            picked.add(best_i)
            for pat, cnt in self.dice[best_i].face_value().items():
                if pat in need_left:
                    need_left[pat] = max(0, need_left[pat] - cnt)
            if not any(need_left.values()):
                break
        return picked

    def can_place_any_unselected(self) -> bool:
        """是否存在未选骰子可放到剩余需求上"""
        need = self._remaining_need()
        if not any(need.values()):
            return False
        used = self.selected_dice
        for i, d in enumerate(self.dice):
            if i in used:
                continue
            fv = d.face_value()
            for pat in fv:
                if pat in need and need[pat] > 0:
                    return True
        return False

    def confirm_placement(self) -> Tuple[bool, str]:
        if not self.selected_dice:
            return False, "请至少选择一枚骰子。"
        placement = self.selected_placement()
        ok, msg = self._placement_valid(placement)
        if not ok:
            return False, msg
        for pat, cnt in placement.items():
            self.progress[pat] = self.progress.get(pat, 0) + cnt
        # 移除已用骰子
        remaining = [d for i, d in enumerate(self.dice) if i not in self.selected_dice]
        self.dice = remaining
        self.selected_dice = set()

        if self.is_pattern_complete():
            return self._complete_assault(True)
        if not self.dice:
            return self._complete_assault(False)
        # 继续掷剩余骰
        self.phase = Phase.ROLL_DICE
        self.message = f"剩余 {len(self.dice)} 枚骰子，请继续掷骰。"
        return True, ""

    def skip_place_penalty(self) -> Tuple[bool, str]:
        """本轮无可用放置：减少一枚骰子"""
        if self.can_place_any_unselected():
            return False, "仍有骰子可放置，不能跳过。"
        if len(self.dice) <= 1:
            self.dice = []
            return self._complete_assault(False)
        self.dice.pop()
        self.selected_dice = set()
        if not self.dice:
            return self._complete_assault(False)
        self.phase = Phase.ROLL_DICE
        self.message = f"本轮无法放置，失去 1 枚骰子！剩余 {len(self.dice)} 枚，请掷骰。"
        return True, ""

    def is_pattern_complete(self) -> bool:
        eff = self.effective_req(self.target, self.target_from_opponent)
        for k, need in eff.items():
            if self.progress.get(k, 0) < need:
                return False
        return True

    def _complete_assault(self, success: bool) -> Tuple[bool, str]:
        p = self.current
        card = self.target
        if success:
            # 从公共或对手手中夺取
            if card.owner is None:
                for c in self.public:
                    if c.id == card.id:
                        c.owner = p
                        break
            else:
                opp = self.players[1 - p]
                for i, c in enumerate(opp.hand):
                    if c.id == card.id:
                        opp.hand.pop(i)
                        break
            card.owner = p
            self.players[p].add_card(card)
            # 检查同色集齐
            color = card.color
            ids_needed = self.color_total_ids(color)
            owned = {c.id for c in self.players[p].hand if c.color == color}
            flavor = _rng.choice(FLAVOR_LINES)
            if owned >= ids_needed:
                self.players[p].locked_colors.add(color)
                self.players[p].recalc_score()
                self.last_event = "lock"
                self.last_locked_color = color
                self.message = (
                    f"【{flavor}】攻占 {card.display_id}！"
                    f"集齐「{color}」色，+{COLORS[color]['score']} 分！"
                )
                self.add_log(f"★ {self.pname(p)} 集齐{color}色，锁定并得分 +{COLORS[color]['score']}")
            else:
                self.last_event = "success"
                self.message = f"【{flavor}】攻占成功，获得 {card.display_id}（{color}）"
                self.add_log(f"✓ {self.pname(p)} 占领 {card.display_id}")
            self.players[p].recalc_score()
            self.players[1 - p].recalc_score()
        else:
            self.last_event = "fail"
            self.message = f"攻占失败，未能匹配 {card.display_id}。"
            self.add_log(f"✗ {self.pname(p)} 攻占 {card.display_id} 失败")

        self.target = None
        self.dice = []
        self._check_game_over()
        if self.phase != Phase.GAME_OVER:
            self.current = 1 - self.current
            self.phase = Phase.CHOOSE_TARGET
            self.message += f" → 轮到 {self.pname(self.current)}。"
        return True, ""

    def final_summary(self) -> str:
        lines = ["═══ 终局结算 ═══"]
        for i in range(2):
            p = self.players[i]
            lines.append(f"\n{self.pname(i)}：总分 {p.score}")
            lines.append(f"  手牌 {len(p.hand)} 张")
            if p.locked_colors:
                parts = [f"{c}(+{COLORS[c]['score']})" for c in sorted(p.locked_colors)]
                lines.append(f"  锁定颜色：{', '.join(parts)}")
            else:
                lines.append("  锁定颜色：无")
            for color, (owned, total, pts) in self.color_progress(i).items():
                if owned:
                    lines.append(f"  ·{color}：{owned}/{total} 张")
        if self.winner is not None:
            lines.append(f"\n🏆 胜者：{self.pname(self.winner)}")
        else:
            lines.append("\n🤝 平局")
        return "\n".join(lines)

    def progress_display(self) -> Dict[str, Tuple[int, int]]:
        """图案 -> (已有, 需要)"""
        eff = self.effective_req(self.target, self.target_from_opponent)
        return {k: (self.progress.get(k, 0), eff[k]) for k in eff}
