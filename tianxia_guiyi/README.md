# 天下归一

双人回合制桌游 Windows 版（Python）。

## 快速开始

1. 安装 [Python 3.10+](https://www.python.org/downloads/)（Windows 自带 tkinter，**无需额外安装**）
2. 双击 `run.bat`，或在目录下执行：

```bash
python main_tk.py
```

可选图形增强版（需联网安装 pygame）：

```bash
python -m pip install -r requirements.txt
python main.py
```

## 规则摘要

- **公共区** 10 张卡，分赤 / 青 / 墨 / 金四色；每张卡右上角 2～4 种图案及数量。
- **先手**：双方各掷一颗 1～6 标准骰，点数大者先行。
- **回合**：选择攻占目标 → 用 6 枚图案骰匹配卡牌需求 → 可超额、不可不足 → 剩余骰继续掷；若本轮无任何骰可放，失去 1 枚骰再掷，直至匹配完成或骰子用尽。
- **抢对手手牌**：图案需求在对手卡牌基础上 **+1 虎符**。
- **同色集齐**：获得该色难度积分，该色对对手 **锁定** 不可再抢。
- **终局**：仅集齐某色全部卡才计该色积分，积分高者胜。

## 操作

| 阶段 | 操作 |
|------|------|
| 定先手 | 点击「掷骰定先手」 |
| 选目标 | 点公共卡，或「抢对手手牌」后点对方卡牌 |
| 掷骰 | 「掷骰」 |
| 放置 | 点选骰子 →「确认放置」；无法放置时用「无法放置(-1骰)」 |

按 `Esc` 退出。

## 打包为 exe（可选）

```bash
pip install pyinstaller
pyinstaller --onefile --windowed --name TianXiaGuiYi main.py
```

生成文件在 `dist/TianXiaGuiYi.exe`。
