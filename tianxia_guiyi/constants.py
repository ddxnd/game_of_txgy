# -*- coding: utf-8 -*-
"""图案、颜色与界面常量"""

# 图案类型
BOW = "弓箭"
CATAPULT = "投石器"
TIGER = "虎符"
CHARIOT = "马车"
SWORD = "宝剑"

ALL_PATTERNS = [BOW, CATAPULT, TIGER, CHARIOT, SWORD]

# 图案显示符号（卡牌上用单字缩写）
PATTERN_SYMBOL = {
    BOW: "弓",
    CATAPULT: "石",
    TIGER: "虎",
    CHARIOT: "车",
    SWORD: "剑",
}

# 公共区单卡需求总和上限（对应约 5 枚骰子可完成；抢对手牌另 +1 虎符）
MAX_PUBLIC_REQ_TOTAL = 5

# 四种颜色及同色集齐后的难度积分
COLORS = {
    "赤": {"rgb": (200, 60, 60), "score": 12},
    "青": {"rgb": (50, 140, 200), "score": 10},
    "墨": {"rgb": (70, 70, 90), "score": 8},
    "金": {"rgb": (210, 170, 50), "score": 6},
}

# 10 张公共卡：每张需求总和 ≤ 5，最高难度为 5
PUBLIC_CARDS = [
    {"id": 1, "color": "赤", "req": {BOW: 3, TIGER: 1, CHARIOT: 1}},           # 5
    {"id": 2, "color": "赤", "req": {BOW: 2, TIGER: 1, CHARIOT: 1}},           # 4
    {"id": 3, "color": "赤", "req": {CATAPULT: 2, TIGER: 1, SWORD: 1}},        # 4
    {"id": 4, "color": "青", "req": {BOW: 3, CATAPULT: 1, CHARIOT: 1}},        # 5
    {"id": 5, "color": "青", "req": {BOW: 2, SWORD: 1, CHARIOT: 2}},           # 5
    {"id": 6, "color": "青", "req": {CATAPULT: 2, TIGER: 2}},                  # 4
    {"id": 7, "color": "墨", "req": {BOW: 2, CHARIOT: 2, SWORD: 1}},           # 5
    {"id": 8, "color": "墨", "req": {TIGER: 2, CATAPULT: 1, CHARIOT: 1}},      # 4
    {"id": 9, "color": "金", "req": {BOW: 2, CATAPULT: 1, TIGER: 1, SWORD: 1}},  # 5
    {"id": 10, "color": "金", "req": {CHARIOT: 3, SWORD: 2}},                  # 5
]

# 六面骰：面 -> {图案: 数量}，弓箭面可为 2 或 3
DIE_FACES = [
    {BOW: 2},
    {BOW: 3},
    {TIGER: 1},
    {CATAPULT: 1},
    {CHARIOT: 1},
    {SWORD: 1},
]

MAX_DICE = 6
SCREEN_W = 1280
SCREEN_H = 800

FLAVOR_LINES = [
    "势如破竹！",
    "用兵如神！",
    "旗开得胜！",
    "天命在我！",
    "一鼓作气！",
    "攻城略地！",
]

COLOR_LABEL = {"赤": "赤焰", "青": "苍狼", "墨": "玄铁", "金": "金戈"}


def card_req_total(req: dict) -> int:
    return sum(req.values())
