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

# 公共区单卡需求总和上限（本版本按实物卡提升到约 7）
MAX_PUBLIC_REQ_TOTAL = 7

# 五种颜色及同色集齐后的积分（按图片颜色分布调权）
COLORS = {
    "绿": {"rgb": (78, 162, 74), "score": 14},
    "赤": {"rgb": (180, 72, 62), "score": 8},
    "紫": {"rgb": (112, 74, 170), "score": 10},
    "蓝": {"rgb": (58, 96, 192), "score": 10},
    "金": {"rgb": (215, 182, 76), "score": 6},
}

# 公共区卡牌（按图片从上到下、从左到右重建）
# 说明：骰盘左侧遮挡区域并无卡牌，实装总数为 14 张
PUBLIC_CARDS = [
    {"id": 1, "color": "绿", "req": {BOW: 2, TIGER: 2, CATAPULT: 2, CHARIOT: 1}},
    {"id": 2, "color": "赤", "req": {BOW: 3, TIGER: 2, CATAPULT: 2}},
    {"id": 3, "color": "赤", "req": {BOW: 3, TIGER: 2}},
    {"id": 4, "color": "金", "req": {BOW: 4, TIGER: 1}},
    {"id": 5, "color": "紫", "req": {TIGER: 3, CATAPULT: 1}},
    {"id": 6, "color": "紫", "req": {BOW: 3, TIGER: 2}},
    {"id": 7, "color": "金", "req": {BOW: 3, TIGER: 1, SWORD: 2}},
    {"id": 8, "color": "蓝", "req": {BOW: 2, TIGER: 2, CATAPULT: 2, CHARIOT: 1}},
    {"id": 9, "color": "蓝", "req": {TIGER: 1, SWORD: 2, CATAPULT: 2}},
    {"id": 10, "color": "金", "req": {BOW: 2, TIGER: 1, CATAPULT: 2, SWORD: 1}},
    {"id": 11, "color": "赤", "req": {BOW: 1, TIGER: 1, CATAPULT: 2, SWORD: 2}},
    {"id": 12, "color": "赤", "req": {TIGER: 2, SWORD: 2}},
    {"id": 13, "color": "赤", "req": {BOW: 1, TIGER: 2, CATAPULT: 2, SWORD: 1}},
    {"id": 14, "color": "金", "req": {TIGER: 1, CATAPULT: 2, SWORD: 1}},
]

# 六面骰（每颗骰子的六面）
# 参考图片可见面：含虎符、弓箭、投石器、马车、宝剑，并有 1 个弓箭重复面
DIE_FACES = [
    {BOW: 1},
    {BOW: 1},
    {TIGER: 1},
    {CATAPULT: 1},
    {CHARIOT: 1},
    {SWORD: 1},
]

# 每回合图案骰数量（按你提供图片改为 7 枚）
MAX_DICE = 7
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

COLOR_LABEL = {
    "绿": "青岚",
    "赤": "赤焰",
    "紫": "紫霄",
    "蓝": "苍浪",
    "金": "金戈",
}


def card_req_total(req: dict) -> int:
    return sum(req.values())
