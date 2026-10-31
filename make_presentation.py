"""Build the editable Safe Fruit course presentation using measured results."""

from pathlib import Path

from pptx import Presentation
from pptx.dml.color import RGBColor
from pptx.enum.shapes import MSO_CONNECTOR, MSO_SHAPE
from pptx.enum.text import PP_ALIGN, MSO_ANCHOR
from pptx.util import Inches, Pt


ROOT = Path(__file__).resolve().parent
OUT = ROOT / "safe_fruit_presentation.pptx"
FONT = "Microsoft YaHei"
MONO = "Consolas"
INK = RGBColor(31, 37, 42)
MUTED = RGBColor(91, 99, 106)
BLUE = RGBColor(39, 75, 108)
PALE = RGBColor(233, 239, 243)
RULE = RGBColor(208, 214, 219)
WHITE = RGBColor(255, 255, 255)

prs = Presentation()
prs.slide_width = Inches(13.333)
prs.slide_height = Inches(7.5)
blank = prs.slide_layouts[6]


def rect(slide, x, y, w, h, fill=None, border=None, radius=False):
    shape = slide.shapes.add_shape(
        MSO_SHAPE.ROUNDED_RECTANGLE if radius else MSO_SHAPE.RECTANGLE,
        Inches(x), Inches(y), Inches(w), Inches(h)
    )
    shape.fill.solid()
    shape.fill.fore_color.rgb = fill or WHITE
    shape.line.fill.background() if border is None else None
    if border is not None:
        shape.line.color.rgb = border
        shape.line.width = Pt(1)
    if radius:
        shape.adjustments[0] = 0.06
    return shape


def line(slide, x1, y1, x2, y2, color=RULE, width=1):
    shape = slide.shapes.add_connector(
        MSO_CONNECTOR.STRAIGHT, Inches(x1), Inches(y1),
        Inches(x2), Inches(y2)
    )
    shape.line.color.rgb = color
    shape.line.width = Pt(width)
    return shape


def text(slide, value, x, y, w, h, size=18, color=INK, bold=False,
         align=PP_ALIGN.LEFT, font=FONT, margin=0, valign=MSO_ANCHOR.MIDDLE):
    box = slide.shapes.add_textbox(Inches(x), Inches(y), Inches(w), Inches(h))
    tf = box.text_frame
    tf.clear()
    tf.word_wrap = True
    tf.margin_left = tf.margin_right = Inches(margin)
    tf.margin_top = tf.margin_bottom = 0
    tf.vertical_anchor = valign
    for i, part in enumerate(value.split("\n")):
        p = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
        p.alignment = align
        p.space_after = Pt(0)
        run = p.add_run()
        run.text = part
        run.font.name = font
        run.font.size = Pt(size)
        run.font.bold = bold
        run.font.color.rgb = color
    return box


def base(title, kicker, num):
    slide = prs.slides.add_slide(blank)
    rect(slide, 0, 0, 13.333, 7.5, WHITE)
    text(slide, kicker, 0.72, 0.33, 11.7, 0.24, 10, MUTED)
    text(slide, title, 0.72, 0.72, 11.95, 0.65, 28, INK, True)
    line(slide, 0.72, 1.48, 12.58, 1.48, RULE)
    text(slide, "Safe Fruit · ADS Project 3", 0.72, 7.11, 5, 0.18, 9, MUTED)
    text(slide, f"{num:02d}", 12.05, 7.08, 0.5, 0.22, 9, MUTED,
         align=PP_ALIGN.RIGHT)
    return slide


def label(slide, value, x, y, w, size=13, color=MUTED):
    return text(slide, value, x, y, w, 0.3, size, color, True)


def small_note(slide, value, y=6.64):
    text(slide, value, 0.75, y, 11.8, 0.34, 10, MUTED)


def node(slide, x, y, name, selected=False, d=0.45):
    shape = slide.shapes.add_shape(
        MSO_SHAPE.OVAL, Inches(x), Inches(y), Inches(d), Inches(d)
    )
    shape.fill.solid()
    shape.fill.fore_color.rgb = BLUE if selected else WHITE
    shape.line.color.rgb = BLUE if selected else MUTED
    shape.line.width = Pt(1.4)
    text(slide, name, x, y + 0.005, d, d - 0.01, 11,
         WHITE if selected else INK, True, PP_ALIGN.CENTER)


def metric(slide, x, y, big, caption, w=3.1):
    text(slide, big, x, y, w, 0.56, 27, BLUE, True)
    text(slide, caption, x, y + 0.64, w, 0.5, 12, MUTED)


def table(slide, x, y, widths, rows, row_h=0.46, font_size=15,
          highlight_rows=()):
    lefts = [x]
    for w in widths[:-1]:
        lefts.append(lefts[-1] + w)
    total = sum(widths)
    for i, row in enumerate(rows):
        yy = y + i * row_h
        if i == 0:
            rect(slide, x, yy, total, row_h, PALE)
        elif i in highlight_rows:
            rect(slide, x, yy, total, row_h, RGBColor(247, 249, 250))
        for j, cell in enumerate(row):
            c = BLUE if j == 0 and i > 0 else INK
            text(slide, str(cell), lefts[j] + 0.1, yy + 0.02,
                 widths[j] - 0.2, row_h - 0.04, font_size, c, i == 0)
        if i > 0:
            line(slide, x, yy + row_h, x + total, yy + row_h, RULE, 0.6)


# 01 — Cover
s = prs.slides.add_slide(blank)
rect(s, 0, 0, 13.333, 7.5, WHITE)
rect(s, 0.73, 0.88, 0.08, 4.65, BLUE)
text(s, "Safe Fruit", 1.16, 1.22, 10.6, 0.86, 42, INK, True)
text(s, "从回溯到森林动态规划", 1.16, 2.18, 10.8, 0.73, 28, INK)
line(s, 1.16, 3.15, 10.95, 3.15, RULE)
text(s, "算法设计与分析 · Project 3", 1.16, 3.45, 7.5, 0.44, 17, MUTED)
text(s, "版本演进、消融对比与性能分析", 1.16, 4.04, 8.5, 0.44, 17, MUTED)
text(s, "组长   游龙斌   3250106392", 1.16, 5.48, 7.5, 0.32, 14, INK)
text(s, "组员   陈智锟   3250100883", 1.16, 5.88, 7.5, 0.32, 14, INK)
text(s, "组员   黄绎睿   3250104426", 1.16, 6.28, 7.5, 0.32, 14, INK)
text(s, "2026.10", 11.2, 6.85, 1.2, 0.25, 11, MUTED, align=PP_ALIGN.RIGHT)


# 02 — Problem statement only; graph modeling is introduced later.
s = base("Safe Fruit：水果选取", "问题描述", 2)
text(s, "从一篮水果中，选取可以安全地一起食用的水果。",
     .85, 1.88, 11.65, .5, 20)
line(s, .85, 2.55, 12.46, 2.55, RULE)
label(s, "水果种类", .86, 2.84, 2.0, 16, BLUE)
text(s, "用三位编号来表示水果种类，如 001、002。", 3.06, 2.78, 9.25, .5, 18)
label(s, "数据大小", .86, 3.48, 2.0, 16, BLUE)
text(s, "输入的水果最多 100 种，选取规则最多 100 条。", 3.06, 3.42, 9.25, .5, 18)
label(s, "输入数据", .86, 4.12, 2.0, 16, BLUE)
text(s, "一是选取规则，一条规则里的两种水果不能同时选取。",
     3.06, 4.06, 9.25, .5, 18)
text(s, "二是每种水果的价格，价格是不超过 1000 的正整数。",
     3.06, 4.67, 9.25, .5, 18)
rect(s, .85, 5.62, 11.6, .95, PALE)
text(s, "选取的最终目标是选取尽可能多的水果；在数量相同时，选取总价格尽量小的方案。",
     1.06, 5.78, 11.18, .58, 17, INK, True)


# 03 — Analysis of the problem and the baseline search.
s = base("数据存储与回溯思路", "问题分析", 3)
label(s, "数据存储", .86, 1.85, 2.0, 16, BLUE)
text(s, "水果看作节点，不能同时选取的规则看作边。",
     .86, 2.27, 11.4, .48, 18)
text(s, "用二维数组记录每种水果的冲突邻居，用一维数组记录价格。",
     .86, 2.79, 11.4, .48, 18)
line(s, .86, 3.45, 12.46, 3.45, RULE)
label(s, "选取思路", .86, 3.75, 2.0, 16, BLUE)
text(s, "采取回溯法：每种水果都有“选”和“不选”两种情况。",
     .86, 4.18, 11.4, .49, 19)
rect(s, .86, 4.86, 5.55, .68, PALE)
text(s, "选：记录水果，并排除冲突水果", 1.11, 4.99, 5.06, .38, 16)
rect(s, 6.74, 4.86, 5.55, .68, PALE)
text(s, "不选：继续讨论剩余水果", 6.99, 4.99, 5.05, .38, 16)
rect(s, .86, 5.84, 11.43, .81, WHITE, RULE)
text(s, "不进行任何优化，100 种水果需要讨论 2^100 种情况；主要工作放在剪枝上。",
     1.06, 5.99, 11.05, .49, 17, BLUE, True)


# 04 — The count and price objectives become one exact score.
s = base("把“数量优先、价格次之”合成一个分数", "共同优化 1 / 目标编码", 4)
text(s, "每种水果先给一个足够大的基础分，再根据价格扣掉一小部分。",
     .85, 1.85, 11.65, .46, 18)
rect(s, .85, 2.66, 11.62, 1.17, PALE)
text(s, "每种水果的分数：w(i) = 100001 − p(i)", 1.17, 2.9,
     10.95, .54, 25, BLUE, True)
label(s, "为什么取 100001？", .86, 4.19, 3.6, 16, INK)
text(s, "水果最多 100 种，每种价格最多 1000：全部价格之和最多 100000。",
     .86, 4.62, 11.45, .48, 18)
text(s, "100001 比总价格可能产生的差额更大，多选一种的增益一定占优。",
     .86, 5.15, 11.45, .48, 18)
rect(s, .86, 5.88, 11.6, .67, WHITE, RULE)
text(s, "同样数量下，价格越低，分数越高；后续只需比较一个总分。",
     1.09, 6.02, 11.08, .39, 17, BLUE, True)


# 05 — Common optimizations in all versions.
s = base("共有的基础优化", "共同优化 2 / 搜索提速", 5)
text(s, "以下三项用于减少搜索工作，贯穿各版本。", .86, 1.78, 11.4, .38, 16, MUTED)
for yy, num, heading, body1, body2 in [
    (2.28, "01", "分数上界剪枝",
     "当前得分 + 剩余候选的最高可能得分 ≤ 已知最优分",
     "当前分支无法改进答案，提前终止。代码用冲突配对收紧这个上界。"),
    (3.68, "02", "掩码保存状态",
     "一个候选集合用两个 64 位整数表示，覆盖最多 100 种水果。",
     "按位操作即可检查、加入或移除水果，快速更新搜索状态。"),
    (5.08, "03", "先选无冲突水果",
     "没有任何冲突的水果一定可以选入答案，因为它能增加水果数量。",
     "程序先把它们选上，再从回溯搜索中移除。"),
]:
    text(s, num, .9, yy, .65, .5, 20, BLUE, True)
    text(s, heading, 1.72, yy, 3.2, .43, 18, INK, True)
    text(s, body1, 4.55, yy, 7.8, .43, 16, INK)
    text(s, body2, 4.55, yy + .48, 7.8, .43, 15, MUTED)
    if num != "03":
        line(s, .9, yy + 1.13, 12.35, yy + 1.13, RULE)
small_note(s, "这些优化由各版本共用，不作为版本差异单独比较。", 6.72)


# 06 — Version map
s = base("版本设计：按优化目标组织对比", "05 / 实验设计", 6)
table(s, .82, 1.9, [1.52, 3.3, 2.2, 4.43], [
    ["版本", "分支选点", "分量分解", "新增结构处理"],
    ["v1", "固定顺序", "否", "基础回溯"],
    ["v2", "动态最大候选度", "是", "作为后续基线"],
    ["v3", "固定顺序", "是", "与 v2 对比选点"],
    ["v4", "动态最大候选度", "否", "与 v2 对比分量"],
    ["v5", "初始度数预排序", "否", "静态顺序"],
    ["v6", "沿用 v2", "是", "原始树分量 DP"],
    ["v7", "沿用 v2", "是", "回溯中检测森林"],
    ["v8", "沿用 v2", "是", "调整森林检测时机"],
], row_h=.48, font_size=14, highlight_rows=(2, 6, 7, 8))
small_note(s, "所有版本求的都是精确最优解；性能比较关注搜索工作量如何变化。")


# 07 — Candidate set and degree pivot.
s = base("回溯中的候选集与高冲突节点", "06 / 分支策略 1", 7)
text(s, "候选集 C：当前仍可讨论、且不与已选水果冲突的节点集合。",
     .86, 1.82, 11.5, .46, 18)
coords = [(1.45, 2.65), (2.78, 2.25), (4.12, 2.65),
          (4.12, 4.18), (2.78, 4.62), (1.45, 4.18)]
center = (2.78, 3.43)
for x, y in coords:
    line(s, center[0] + .24, center[1] + .24, x + .24, y + .24, MUTED, 1.3)
for i, (x, y) in enumerate(coords):
    node(s, x, y, f"{i+1:03d}", d=.48)
node(s, center[0], center[1], "007", selected=True, d=.48)
text(s, "中心点 007 的度数最高", 1.3, 5.3, 4.5, .36, 15, MUTED, True,
     align=PP_ALIGN.CENTER)
line(s, 6.1, 2.22, 6.1, 5.76, RULE)
label(s, "讨论 007 时", 6.55, 2.25, 4.5, 16, BLUE)
rect(s, 6.55, 2.8, 5.55, .86, PALE)
text(s, "选 007：它和 5 个邻居都移出候选集",
     6.78, 2.98, 5.1, .48, 16)
rect(s, 6.55, 3.94, 5.55, .86, PALE)
text(s, "不选 007：只把 007 移出候选集",
     6.78, 4.12, 5.1, .48, 16)
text(s, "优先讨论高冲突节点，选中它时往往能一次缩小很多候选。",
     6.55, 5.12, 5.55, .62, 16, INK, True)
small_note(s, "图中蓝色中心节点与 5 个叶节点冲突；每条边表示一条不能同时选取的规则。", 6.67)


# 08 — Static versus dynamic branching.
s = base("两种选点策略：固定顺序与动态调整", "07 / 分支策略 2", 8)
rect(s, .86, 1.92, 5.62, 3.75, WHITE, RULE)
rect(s, 6.83, 1.92, 5.62, 3.75, WHITE, RULE)
text(s, "静态预排序（v5）", 1.12, 2.16, 5.1, .46, 20, BLUE, True)
text(s, "回溯开始前，按每种水果的总冲突数从大到小排一次；拆分分量后，各分量沿固定顺序讨论。",
     1.12, 2.83, 5.1, 1.0, 17)
text(s, "优点：预处理简单；M ≤ 100，排序开销很小。",
     1.12, 4.11, 5.1, .64, 16, INK, True)
text(s, "局限：顺序依据原始冲突数，不随候选集变化。",
     1.12, 4.91, 5.1, .53, 15, MUTED)
text(s, "动态选点（v2）", 7.1, 2.16, 5.1, .46, 20, BLUE, True)
text(s, "每次回溯都在当前候选集中，选择与剩余候选冲突数最多的水果。",
     7.1, 2.83, 5.1, 1.0, 17)
text(s, "优点：选点反映当前真正剩下的冲突关系。",
     7.1, 4.11, 5.1, .64, 16, INK, True)
text(s, "代价：每个搜索节点都要重新统计候选度数。",
     7.1, 4.91, 5.1, .53, 15, MUTED)
rect(s, .86, 5.96, 11.6, .61, PALE)
text(s, "预期：简单图上静态顺序成本低；候选关系变化明显的复杂图上，动态顺序更能适应。",
     1.06, 6.08, 11.15, .38, 15, INK, True)


# 09 — Branch comparison results.
s = base("测试总体支持动态选点的预期", "08 / v2、v3、v5", 9)
label(s, "p95 求解时间（ms，越低越好）", .84, 1.84, 7, 15, INK)
for yy, name, value in [(2.52, "v2 动态", 25.976), (3.31, "v3 固定顺序", 243.824),
                        (4.10, "v5 预排序", 84.137)]:
    text(s, name, .85, yy, 2.05, .42, 17, INK)
    rect(s, 3.0, yy + .07, 6.6 * value / 260, .28,
         BLUE if name.startswith("v2") else RGBColor(126, 137, 146))
    text(s, f"{value:.1f}", 9.82, yy, 1.35, .42, 17, INK, True)
rect(s, .84, 5.16, 11.65, .71, PALE)
text(s, "超时次数 / 2460：  v2 = 0     v3 = 9     v5 = 4",
     1.08, 5.28, 11.0, .4, 17)
text(s, "banded M=100 中位数：v2 87.4 ms   ·   v3 544.5 ms   ·   v5 373.3 ms",
     .85, 5.96, 11.5, .38, 14, INK, True)
small_note(s, "三版均做分量分解；v2/v5 对比动态与静态选点，v3 使用固定下标顺序。", 6.58)


# 10 — Connected-component decomposition.
s = base("分量分解：孤立节点思路的延伸", "09 / 结构优化 1", 10)
text(s, "孤立节点没有冲突边，可以直接选入；它其实是大小为 1 的连通分量。",
     .86, 1.82, 11.55, .48, 18)
tri = [(1.55, 2.62), (2.2, 2.04), (2.85, 2.62)]
for a, b in [(0, 1), (1, 2), (2, 0)]:
    line(s, tri[a][0] + .22, tri[a][1] + .22,
         tri[b][0] + .22, tri[b][1] + .22, MUTED, 1.3)
for i, (x, y) in enumerate(tri):
    node(s, x, y, f"A{i+1}", d=.44)
text(s, "分量 A", 1.55, 3.16, 1.75, .32, 14, MUTED, True,
     align=PP_ALIGN.CENTER)
line(s, 4.85, 2.54, 5.7, 2.54, MUTED, 1.3)
node(s, 4.4, 2.32, "B1", d=.44)
node(s, 5.7, 2.32, "B2", d=.44)
text(s, "分量 B", 4.35, 3.16, 1.8, .32, 14, MUTED, True,
     align=PP_ALIGN.CENTER)
node(s, 7.45, 2.32, "C", d=.44)
text(s, "孤立分量 C", 7.02, 3.16, 1.6, .32, 14, MUTED, True,
     align=PP_ALIGN.CENTER)
text(s, "不同连通分量之间没有边；一个分量的选取不会影响另一个分量。",
     .86, 3.78, 11.55, .48, 18, INK, True)
text(s, "分别求每个分量的局部最优解，再把这些解合起来：",
     .86, 4.47, 11.55, .43, 17)
rect(s, .86, 5.08, 11.55, .76, PALE)
text(s, "S* = S₁ ∪ S₂ ∪ ··· ∪ Sₖ",
     1.12, 5.22, 5.0, .42, 21, BLUE, True)
text(s, "各分量得分可相加，所以合并后就是全图的最优解。",
     6.15, 5.22, 5.95, .42, 16, INK)
small_note(s, "把“单个孤立水果可以先选”推广为“多个互不相连的子图可以分别求解”。", 6.55)


# 11 — Controlled component-decomposition comparison.
s = base("v2 与 v4：只差连通分量分解", "10 / 结构优化 2", 11)
text(s, "两个版本都用动态最大度数选点；v4 不分解，v2 把各分量拆开搜索。",
     .86, 1.82, 11.55, .48, 18)
table(s, .86, 2.58, [3.35, 3.25, 3.25, 1.5], [
    ["测试指标", "v4：不分解", "v2：分解", "图形"],
    ["components100 中位数", "76.470 ms", "0.083 ms", "多分量"],
    ["path100 中位数", "149.884 ms", "150.025 ms", "单分量"],
    ["全套 2460 组超时", "21", "0", "full"],
], row_h=.68, font_size=15, highlight_rows=(1, 3))
rect(s, .86, 5.72, 11.55, .68, PALE)
text(s, "多分量图收益显著；只有一个分量的路径图，拆分前后耗时接近。",
     1.08, 5.86, 11.1, .4, 16, INK, True)
small_note(s, "来自 v1–v4 同轮测试：2460 组输入，5 秒超时上限；v2/v4 仅分解策略不同。", 6.63)


# 12 — A connected acyclic component is a tree.
s = base("无环的连通分量就是树", "11 / 树形 DP 1", 12)
text(s, "分量分解把全图拆成独立问题；现在看单个连通分量有没有环。",
     .86, 1.82, 11.55, .46, 18)
tree_nodes = {
    "R": (3.0, 2.38),
    "A": (2.0, 3.37), "B": (4.0, 3.37),
    "C": (1.42, 4.42), "D": (2.55, 4.42),
    "E": (3.45, 4.42), "F": (4.58, 4.42),
}
for parent, child in [("R", "A"), ("R", "B"), ("A", "C"),
                      ("A", "D"), ("B", "E"), ("B", "F")]:
    x1, y1 = tree_nodes[parent]
    x2, y2 = tree_nodes[child]
    line(s, x1 + .22, y1 + .22, x2 + .22, y2 + .22, MUTED, 1.3)
for name, (x, y) in tree_nodes.items():
    node(s, x, y, name, selected=(name == "R"), d=.44)
text(s, "根", 3.17, 2.09, .5, .25, 12, BLUE, True)
text(s, "父节点", .98, 3.23, .9, .3, 13, MUTED, True)
text(s, "孩子节点", 4.77, 4.42, 1.0, .3, 13, MUTED, True)
line(s, 6.05, 2.05, 6.05, 5.28, RULE)
text(s, "无环的连通图就是树。", 6.48, 2.15, 5.65, .43, 19, BLUE, True)
text(s, "选一个根后，每个其他节点都有一个父节点，也可以有多个孩子。",
     6.48, 2.85, 5.65, .72, 17)
text(s, "选中父节点，孩子不能选；不选父节点，孩子可选也可不选。",
     6.48, 3.78, 5.65, .72, 17)
text(s, "不同孩子的子树之间没有边，可以分别计算再合并。",
     6.48, 4.7, 5.65, .62, 17, INK, True)
rect(s, .86, 5.73, 11.55, .61, PALE)
text(s, "\u6bcf\u4e2a\u8282\u70b9\u7684\u9009\u53d6\u72b6\u6001\u53ea\u53d7\u7236\u8282\u70b9\u5f71\u54cd\uff0c\u4e5f\u53ea\u5f71\u54cd\u5b50\u8282\u70b9\uff1b\u8fd9\u79cd\u5c40\u90e8\u4f20\u9012\u5f88\u50cf\u9a6c\u5c14\u53ef\u592b\u94fe\u3002",
     1.07, 5.85, 11.08, .37, 16, INK, True)
small_note(s, "\u65e0\u73af\u7684\u8fde\u901a\u56fe\u5c31\u662f\u6811\uff1b\u9009\u5b9a\u6839\u540e\uff0c\u72b6\u6001\u6309\u7236\u5b50\u5173\u7cfb\u4f20\u9012\u3002", 6.68)


# 13 — Two-state tree DP and bottom-up evaluation.
s = base("树上每个节点只需“选 / 不选”两个状态", "12 / 树形 DP 2", 13)
text(s, "take(v)：选中 v 时，v 的子树能得到的最高分；skip(v)：不选 v 时的最高分。",
     .86, 1.82, 11.55, .48, 17)
rect(s, .86, 2.58, 11.55, 1.02, PALE)
text(s, "take(v) = w(v) + Σ skip(u)", 1.18, 2.73, 10.95, .38, 21, BLUE, True)
text(s, "u 是 v 的孩子：选 v 后，每个孩子都不能选。",
     1.2, 3.14, 10.9, .32, 14, MUTED)
rect(s, .86, 3.84, 11.55, 1.02, PALE)
text(s, "skip(v) = Σ max(take(u), skip(u))", 1.18, 3.99, 10.95, .38, 21, BLUE, True)
text(s, "不选 v 后，每个孩子都可在选 / 不选中取分数较高的一种。",
     1.2, 4.4, 10.9, .32, 14, MUTED)
text(s, "\u53f6\u5b50\uff1atake(v)=w(v)\uff0cskip(v)=0\uff1b\u4ece\u53f6\u5b50\u5f00\u59cb\uff0c\u4e00\u5c42\u5c42\u5411\u6839\u9012\u63a8\u3002",
     .86, 5.13, 11.55, .48, 17)
rect(s, .86, 5.83, 11.55, .64, WHITE, RULE)
text(s, "\u4f9d\u636e\u8fd9\u4e24\u6761\u9012\u5f52\u5173\u7cfb\uff0c\u53ef\u4ee5\u53cd\u5411\u4ece\u53f6\u5b50\u5411\u6839\u9012\u63a8\uff1b\u6700\u540e\u4ece\u6839\u56de\u6eaf\u91cd\u5efa\u7b54\u6848\u3002",
     1.05, 5.95, 11.15, .4, 15, INK, True)
small_note(s, "M=100 路径：v2 80.479 ms → v6 0.0046 ms；树：4.521 ms → 0.0071 ms。", 6.7)


# 14 — Forest
s = base("v7：回溯后，环图可能变成森林", "13 / v6 → v7", 14)
left = [(1.25, 3.11), (2.22, 2.42), (3.2, 3.11),
        (3.2, 4.1), (2.22, 4.78), (1.25, 4.1)]
for i in range(6):
    a, b = left[i], left[(i + 1) % 6]
    line(s, a[0] + .2, a[1] + .2, b[0] + .2, b[1] + .2, MUTED, 1.3)
for i, (x, y) in enumerate(left):
    node(s, x, y, str(i + 1), selected=(i == 0), d=.42)
text(s, "原始分量：有环", 1.18, 2.05, 3.45, .4, 18, INK, True)
text(s, "删去候选点", 4.53, 3.48, 2.0, .38, 17, BLUE, True)
line(s, 4.5, 3.88, 6.15, 3.88, BLUE, 1.7)
right = [(7.15, 3.58), (8.15, 3.58), (9.15, 3.58), (10.15, 3.58),
         (11.15, 3.58)]
for a, b in zip(right, right[1:]):
    line(s, a[0] + .2, a[1] + .2, b[0] + .2, b[1] + .2, MUTED, 1.3)
for i, (x, y) in enumerate(right):
    node(s, x, y, str(i + 2), d=.42)
text(s, "剩余候选图：无环", 7.08, 2.62, 5.0, .4, 18, INK, True)
rect(s, 6.97, 4.6, 5.18, .69, PALE)
text(s, "检测成功 → 森林 DP 结束该分支", 7.15, 4.74, 4.85, .36, 16)
metric(s, 1.2, 5.68, "67.204 → 0.0423 ms", "100 点环图：v6 → v7", 6.2)
small_note(s, "无环性由程序检查；检测失败时继续精确回溯。")


# 15 — Check policy
s = base("v8：根据环秩调整森林检测时机", "14 / v7 → v8", 15)
label(s, "v7：固定阈值", .85, 1.87, 5.0, 16, INK)
text(s, "初始环秩 < 3：删去 5 个候选点后首次检测\n初始环秩 ≥ 3：剩余 ≤ 15 点时首次检测\n失败后：再删去 5 个候选点才复查",
     .85, 2.38, 5.6, 2.08, 18)
line(s, 6.62, 1.82, 6.62, 5.32, RULE)
label(s, "v8：跟随初始环秩", 7.0, 1.87, 5.3, 16, INK)
text(s, "r = 边数 − 点数 + 1", 7.0, 2.4, 4.95, .45, 21, BLUE, True)
text(s, "首次检测：删去 q = min(n, ⌈r/2⌉) 个候选点", 7.0, 3.14, 5.1, .48, 16)
text(s, "失败后：一次分支使候选点减少 ≥ 2 时复查", 7.0, 3.89, 5.1, .82, 18)
rect(s, .84, 5.63, 11.64, .69, PALE)
text(s, "\u73af\u79e9\u662f\u6253\u65ad\u6240\u6709\u73af\u81f3\u5c11\u8981\u5220\u7684\u8fb9\u6570\uff1b\u666e\u901a\u73af\u4e0a\u6bcf\u4e2a\u70b9\u8fde\u4e24\u6761\u8fb9\uff0c\u6240\u4ee5\u5148\u4ece\u73af\u79e9\u7684\u4e00\u534a\u5f00\u59cb\u68c0\u6d4b\u3002\u8fd9\u662f\u7ecf\u9a8c\u8d77\u70b9\u3002",
     1.05, 5.77, 11.05, .38, 16)
small_note(s, "取一个点可连同多个邻居一起移出候选集，因此 v8 倾向在这类分支后复查。")


# 16 — Structural comparison
s = base("结构优化的整体效果", "15 / v2、v6、v7、v8", 16)
table(s, .84, 1.98, [2.65, 2.75, 2.75, 3.5], [
    ["版本", "p95（ms）", "累计耗时（s）", "100 点环图（ms）"],
    ["v2 基线", "25.145", "16.721", "69.597"],
    ["v6 原始树 DP", "10.509", "11.041", "67.204"],
    ["v7 剩余森林 DP", "2.294", "1.612", "0.0423"],
    ["v8 检测时机调整", "0.795", "0.773", "0.0147"],
], row_h=.67, font_size=16, highlight_rows=(4,))
text(s, "测试集：2,460 组；四个版本均 0 超时。", .85, 5.6, 11.6, .42, 17)
text(s, "局部反例：100 点核心外围图，v7 为 0.0546 ms，v8 为 0.0967 ms。",
     .85, 6.16, 11.6, .44, 15, MUTED)
small_note(s, "耗时为同一轮程序内部计时；小于 1 ms 的差值不宜单独解读。", 6.75)


# 17 — Close
s = base("结论", "16 / 总结", 17)
for yy, n, head, body in [
    (1.94, "01", "选点", "动态度数降低困难实例的搜索尾部。"),
    (3.07, "02", "分量", "拆开独立子图，避免组合搜索。"),
    (4.20, "03", "结构", "树和回溯后形成的森林可由 DP 精确求解。"),
]:
    text(s, n, .87, yy, .74, .56, 23, BLUE, True)
    line(s, 1.68, yy + .03, 1.68, yy + .54, RULE)
    text(s, head, 2.01, yy + .02, 1.37, .46, 20, INK, True)
    text(s, body, 3.45, yy + .02, 8.95, .52, 18)
rect(s, .85, 5.6, 11.62, .75, PALE)
text(s, "最终版本 v8：精确求解；在 2,460 组基准中全部完成并通过答案校验。",
     1.06, 5.74, 11.2, .45, 17)
small_note(s, "最终提交代码：v8_cycle_tree_dp.c；完整实验与报告见项目仓库。")

prs.save(OUT)
print(OUT)
