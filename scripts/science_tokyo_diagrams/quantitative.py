"""Quantitative archetypes. All numbers are fictional teaching examples."""
from math import sqrt
from pptx.enum.text import PP_ALIGN
from .drawing import *
from . import charts


def dot_matrix_share(s):
    caption(s, "共用データの公開状況（100件）")
    for i in range(100):
        row, col = divmod(i, 10)
        circle(s, .75+col*.29, .95+row*.29, .2,
               fill=NAVY if i < 64 else PALE,
               name=f"record:{i+1}:{'open' if i < 64 else 'pending'}")
    text(s, "64%", 4.4, .85, 5.6, .95, size=44, bold=True, color=NAVY)
    text(s, "公開済み 64件 ／ 未公開 36件", 4.4, 1.94, 6.1, .5, size=21)
    text(s, "1つの点＝1件\n公開条件を満たしたデータを順次共有", 4.4, 2.65, 6.4, .95, size=18)
    key(s, "公開済み", 4.4, 3.76, fill=NAVY)
    key(s, "未公開", 7.3, 3.76, fill=PALE)


def progress_bubble_matrix(s):
    caption(s, "研究テーマ × 工程の達成率")
    cols = ("計画", "試作", "検証")
    rows = ("データ基盤", "解析手法", "実証準備")
    values = ((100, 70, 30), (100, 60, 10), (90, 40, 0))
    for j, c in enumerate(cols):
        text(s, c, 2.25+j*2, .58, 1.55, .4, bold=True, align=PP_ALIGN.CENTER)
    for i, (r, vals) in enumerate(zip(rows, values)):
        yy = 1.42+i*.95
        text(s, r, .32, yy-.19, 1.9, .42, size=18)
        line(s, 2.2, yy+.48, 8.35, yy+.48)
        for j, v in enumerate(vals):
            cx = 3+j*2
            if v:
                circle(s, cx, yy-.08, area_diameter(v, 100, .52),
                       fill=NAVY if v == 100 else BLUE, name=f"progress:{i}:{j}:{v}")
            text(s, f"{v}%", cx-.65, yy+.2, 1.3, .38, size=14, align=PP_ALIGN.CENTER)
    shape(s, 8.7, 1.05, 2.55, 2.85, fill=PALE2)
    text(s, "検証が次の焦点", 8.9, 1.25, 2.2, .65, size=19, bold=True, color=NAVY)
    text(s, "試作を完了し\n検証へ移行する", 8.9, 2.08, 2.1, 1, size=18)
    text(s, "円面積＝達成率\n0%は円なし", 8.9, 3.16, 2.15, .6, size=14, color=MUTED)


def ranked_bar_annotated(s):
    caption(s, "分野別の共同利用申請数")
    text(s, "申請件数（件）", .4, .57, 6, .4, size=14, color=MUTED)
    charts.category(s, "applications", ("情報", "材料", "医工", "環境"),
                    (("申請数", (18, 14, 10, 6)),), .25, 1.03, 7.9, 3.15,
                    kind="bar", ymax=20, step=5)
    shape(s, 8.6, 1.12, 2.6, 2.75, fill=PALE)
    text(s, "上位2分野", 8.82, 1.35, 2.2, .5, bold=True, color=NAVY)
    text(s, "32 / 48件", 8.82, 2.03, 2.2, .55, size=24, bold=True, color=NAVY)
    text(s, "全体の約67%\n支援枠の配分を検討", 8.82, 2.85, 2.15, .7, size=16)


def scatter_annotated(s):
    caption(s, "研究候補の資源量と準備度")
    text(s, "準備度（%）", .38, .54, 4, .4, size=14, color=MUTED)
    charts.xy(s, "readiness-cost", (("基盤A", ((20, 40),)),
              ("解析B", ((45, 70),)), ("実証C", ((70, 50),))),
              .25, 1.01, 8.1, 3.05, xmin=0, xmax=80, xstep=20,
              ymin=0, ymax=100, ystep=20)
    text(s, "必要経費（万円）", 5.8, 4.04, 2.6, .34, size=14, color=MUTED)
    shape(s, 8.7, 1.03, 2.55, 2.91, fill=PALE2)
    text(s, "解析Bを先行", 8.9, 1.25, 2.1, .6, size=19, bold=True, color=NAVY)
    text(s, "45万円・70%\n中程度の経費で\n準備度が最も高い", 8.9, 2.05, 2.1, 1.5, size=17)


def proportional_circles(s):
    caption(s, "計画別の対象データ数（円面積が件数に比例）")
    for label, value, cx, color in (("小規模", 25, 2, BLUE),
                                    ("中規模", 50, 5.7, BLUE),
                                    ("広域", 100, 9.4, NAVY)):
        d = area_diameter(value, 100, 2.15)
        circle(s, cx, 2.22, d, fill=color, name=f"area:{value}")
        text(s, str(value), cx-d/2, 2.0, d, .45, size=26, bold=True,
             color=WHITE, align=PP_ALIGN.CENTER)
        text(s, f"{label}  {value}件", cx-1.35, 3.57, 2.7, .48,
             bold=True, align=PP_ALIGN.CENTER)
    text(s, "面積比 1 : 2 : 4 ／ 同一単位・同一基準で比較", .35, 4.07, 10.8, .33,
         size=14, color=MUTED, align=PP_ALIGN.CENTER)


def delta_bars_totals(s):
    caption(s, "支援枠の増減と期首・期末の合計")
    x, y, w, h = 1, .98, 10, 2.72
    yv = lambda v: y+h*(100-v)/120
    text(s, "支援枠（件）", .35, .55, 4, .4, size=14, color=MUTED)
    for v in (-20, 0, 20, 40, 60, 80, 100):
        yy = yv(v)
        line(s, x, yy, x+w, yy, color=MUTED if v == 0 else RULE)
        text(s, str(v), .33, yy-.16, .52, .32, size=14, color=MUTED, align=PP_ALIGN.RIGHT)
    for cx, label, value, total in ((1.6, "期首", 64, True), (3.8, "新規", 18, False),
                                   (6, "終了", -8, False), (8.2, "再開", 12, False),
                                   (10.4, "期末", 86, True)):
        top, bottom = min(yv(value), yv(0)), max(yv(value), yv(0))
        shape(s, cx-.42, top, .84, bottom-top, fill=NAVY if total else BLUE,
              name=f"delta:{label}:{value}")
        text(s, str(value) if total else f"{value:+d}", cx-.7,
             top-.44 if value >= 0 else bottom+.03, 1.4, .4, size=18,
             bold=True, align=PP_ALIGN.CENTER, color=NAVY)
        text(s, label, cx-.85, 3.96, 1.7, .4, size=17, align=PP_ALIGN.CENTER)


def scenario_lines_cagr(s):
    caption(s, "共用基盤の利用シナリオ（2026年＝100）")
    high = (100, 120, 144, 172.8)
    base = (100, 110, 121, 133.1)
    low = (100, 105, 110.25, 115.7625)
    text(s, "利用指数", .35, .55, 3, .4, size=14, color=MUTED)
    charts.xy(s, "scenarios", tuple((label, tuple(zip(range(2026, 2030), vals)))
              for label, vals in (("拡大", high), ("標準", base), ("慎重", low))),
              .25, 1, 8.1, 3.13, xmin=2026, xmax=2029, xstep=1,
              ymin=0, ymax=200, ystep=50, lines=True)
    text(s, "年", 7.88, 4.08, .5, .3, size=14, color=MUTED)
    for i, (label, rate, vals, fill) in enumerate((("拡大", 20, high, NAVY),
                   ("標準", 10, base, BLUE), ("慎重", 5, low, "B8C7E0"))):
        box(s, f"{label}  年率 {rate}%\n2029年：{vals[-1]:.1f}", 8.7, 1+i*.92,
            2.55, .76, fill=fill, color=WHITE if i == 0 else INK, size=17)
    text(s, "年率＝3期間のCAGR", 8.7, 3.92, 2.6, .35, size=14, color=MUTED)


def chart_insight(s):
    caption(s, "共用設備の利用件数と次期の検討事項")
    text(s, "利用件数（件）", .4, .55, 4, .4, size=14, color=MUTED)
    charts.category(s, "quarterly-use", ("第1期", "第2期", "第3期", "第4期"),
                    (("利用件数", (24, 32, 40, 48)),), .25, .99, 7.3, 3.24,
                    ymax=60, step=20)
    shape(s, 7.9, 1.05, 3.35, 2.98, fill=PALE)
    text(s, "24 → 48件", 8.1, 1.25, 2.95, .61, size=25, bold=True, color=NAVY)
    text(s, "期初比 2.0倍", 8.1, 2.01, 2.95, .48, size=20, bold=True)
    line(s, 8.1, 2.65, 11.03, 2.65)
    text(s, "次期は予約枠の拡張と\n保守時間の確保を検討", 8.1, 2.85, 2.95, .9, size=18)


def stacked_bar(s):
    caption(s, "利用目的の構成変化（全体件数も表示）")
    text(s, "利用件数（件）", .4, .56, 4, .4, size=14, color=MUTED)
    charts.category(s, "purpose", ("前期", "当期", "次期案"),
                    (("基礎研究", (20, 24, 30)), ("共同研究", (12, 20, 30)),
                     ("教育", (8, 16, 20))), .35, 1, 8.05, 3.18,
                    kind="stacked", ymax=100, step=20, legend=True)
    text(s, "合計", 8.8, 1.15, 2.1, .45, bold=True, color=NAVY)
    for i, (label, total) in enumerate((("前期", 40), ("当期", 60), ("次期案", 80))):
        text(s, f"{label}  {total}件", 8.8, 1.92+i*.66, 2.4, .5, size=19)


def bridge_segments(start, changes):
    result = [("期首", 0, start, True)]
    running = start
    for label, delta in changes:
        result.append((label, running, running+delta, False))
        running += delta
    result.append(("期末", 0, running, True))
    return result


def draw_bridge(s, *, start, changes, ymax, step, title):
    caption(s, title)
    yv = axes(s, 1.05, 1.05, 9.98, 2.62, ymax, step, unit="支援額（万円）")
    segments = bridge_segments(start, changes)
    count = len(segments)
    dx = 8.8/(count-1)
    for i, (label, before, after, total) in enumerate(segments):
        cx = 1.7+i*dx
        upper, lower = max(before, after), min(before, after)
        shape(s, cx-.43, yv(upper), .86, yv(lower)-yv(upper),
              fill=NAVY if total else BLUE, name=f"bridge:{label}:{before}:{after}")
        val = after if total else after-before
        text(s, f"{val}" if total else f"{val:+d}", cx-.7, yv(upper)-.43,
             1.4, .38, size=18, bold=True, color=NAVY, align=PP_ALIGN.CENTER)
        text(s, label, cx-.95, 3.91, 1.9, .45, size=17, align=PP_ALIGN.CENTER)
        if i < count-1:
            line(s, cx+.43, yv(after), cx+dx-.43, yv(after), color=MUTED,
                 dashed=True, name=f"bridge-link:{after}")


def waterfall(s):
    draw_bridge(s, start=40, changes=(("新規採択", 20), ("終了", -10), ("追加支援", 15)),
                ymax=80, step=20, title="支援額の寄与度ブリッジ：40 + 20 − 10 + 15 = 65")


def true_waterfall(s):
    draw_bridge(s, start=80, changes=(("拡張", 30), ("縮小", -20), ("再配分", 10)),
                ymax=120, step=20, title="起点から着地までの厳密な増減：80 + 30 − 20 + 10 = 100")


def small_multiples(s):
    caption(s, "3領域の検証達成率：すべて同じ0–100%スケール")
    for k, (label, vals) in enumerate((("データ基盤", (20, 35, 50, 70)),
                                     ("解析手法", (40, 45, 50, 60)),
                                     ("実証準備", (15, 30, 55, 90)))):
        x = 1+k*3.65
        text(s, label, x-.3, .65, 3, .4, bold=True, color=NAVY, align=PP_ALIGN.CENTER)
        yv = axes(s, x, 1.56, 2.8, 1.97, 100, 50, unit="達成率（%）")
        for j, val in enumerate(vals):
            px = x+j*2.8/3
            if j:
                line(s, px-2.8/3, yv(vals[j-1]), px, yv(val), color=NAVY, width=2.5,
                     name=f"small:{k}:{j-1}:{j}")
            circle(s, px, yv(val), .1, name=f"point:{k}:{j}:{val}")
            text(s, f"{val}", px-.28, yv(val)-.38, .56, .32, size=14, color=NAVY,
                 align=PP_ALIGN.CENTER)
            text(s, f"Q{j+1}", px-.32, 3.71, .64, .35, size=14, align=PP_ALIGN.CENTER)


def matrix_2x2(s):
    caption(s, "研究施策の位置づけ：定性的な優先順位")
    x, y, w, h = 1.65, .85, 8.95, 2.9
    for i in range(2):
        for j in range(2):
            shape(s, x+j*w/2, y+i*h/2, w/2, h/2,
                  fill=PALE if i == 0 and j == 1 else PALE2)
    line(s, x, y+h/2, x+w, y+h/2, color=RULE)
    line(s, x+w/2, y, x+w/2, y+h, color=RULE)
    arrow(s, x, y+h, x+w+.2, y+h)
    arrow(s, x, y+h, x, y-.1)
    text(s, "期待効果", .28, .63, 1.3, .5, bold=True, color=NAVY)
    text(s, "高", .96, 1.02, .5, .4, size=16)
    text(s, "低", .96, 3.26, .5, .4, size=16)
    text(s, "実行容易性  低 → 高", 5.7, 3.97, 4.8, .4, bold=True, color=NAVY,
         align=PP_ALIGN.RIGHT)
    for label, xx, yy, color in (("基盤刷新", 3.7, 1.65, BLUE), ("共通申請", 8.1, 1.6, NAVY),
                                 ("長期拡張", 3.5, 3.1, BLUE), ("手順共有", 8.1, 3, BLUE)):
        circle(s, xx-.78, yy, .13, fill=color)
        text(s, label, xx-.57, yy-.23, 2.5, .46, size=19, bold=color == NAVY)
