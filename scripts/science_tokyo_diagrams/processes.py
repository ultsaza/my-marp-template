"""Editable operational diagrams with real routes, dependencies and schedules."""
from pptx.enum.text import PP_ALIGN
from .drawing import *


def swimlane_numbered_notes(s):
    caption(s, "共同利用の業務フローと改善論点")
    for j, label in enumerate(("申請", "審査", "提供")):
        text(s, label, 1.7+j*2.25, .58, 1.95, .4, bold=True, align=PP_ALIGN.CENTER)
    for i, label in enumerate(("研究者", "事務局", "基盤担当")):
        yy = 1.12+i*.97
        shape(s, .3, yy, 8.2, .88, fill=PALE2 if i % 2 == 0 else PALE)
        text(s, label, .43, yy+.2, 1.15, .47, size=17, bold=True)
    # Cross-lane handoffs: submit -> review -> publish -> receive.
    arrow(s, 3.6, 1.54, 3.9, 1.54)
    line(s, 3.9, 1.54, 3.9, 2.52, color=NAVY, width=1.8)
    arrow(s, 3.9, 2.52, 4.05, 2.52)
    line(s, 5.95, 2.52, 6.18, 2.52, color=NAVY, width=1.8)
    line(s, 6.18, 2.52, 6.18, 3.49, color=NAVY, width=1.8)
    arrow(s, 6.18, 3.49, 6.3, 3.49)
    box(s, "利用申請", 1.7, 1.21, 1.9, .65, fill=NAVY, color=WHITE)
    box(s, "適格性確認", 4.05, 2.18, 1.9, .65, fill=BLUE)
    box(s, "権限を付与", 6.3, 3.15, 1.9, .65, fill=BLUE)
    for label, xx, yy in (("1", 3.48, 1.13), ("2", 5.83, 2.1)):
        circle(s, xx, yy, .35, fill=NAVY)
        text(s, label, xx-.17, yy-.18, .34, .35, size=14, bold=True,
             color=WHITE, align=PP_ALIGN.CENTER)
    shape(s, 8.83, 1.12, 2.42, 2.81, fill=PALE)
    text(s, "改善論点", 9, 1.27, 2.1, .43, bold=True, color=NAVY)
    text(s, "1  入力の重複\n    共通フォームへ", 9, 1.98, 2.1, .79, size=16)
    text(s, "2  確認の滞留\n    期限を可視化", 9, 2.98, 2.1, .79, size=16)


def front_back_two_tier(s):
    caption(s, "利用者の体験と裏側の処理を対応づける")
    text(s, "利用者", .32, .72, 1.25, .45, bold=True, color=NAVY)
    text(s, "運用側", .32, 2.7, 1.25, .45, bold=True, color=NAVY)
    fronts = ("申請する", "進捗を見る", "データを受領", "再利用する")
    backs = ("受付を登録", "審査を管理", "権限を付与", "履歴を記録")
    for j, (a, b) in enumerate(zip(fronts, backs)):
        x = 1.75+j*2.37
        box(s, a, x, .98, 2.05, .9, fill=NAVY, color=WHITE, size=18)
        box(s, b, x, 2.85, 2.05, .9, fill=PALE, size=18)
        arrow(s, x+1.025, 1.92, x+1.025, 2.78)
        if j < 3:
            arrow(s, x+2.08, 1.43, x+2.32, 1.43)
            arrow(s, x+2.08, 3.3, x+2.32, 3.3)
    text(s, "上下の列は同じ業務段階に対応", 1.75, 4.02, 9, .35, size=14, color=MUTED)


def issue_to_solution_map(s):
    caption(s, "課題から打ち手への対応：共通フォームが2つの課題に作用")
    box(s, "課題", .45, .73, 3.55, .57, fill=NAVY, color=WHITE, bold=True)
    box(s, "打ち手", 7.55, .73, 3.55, .57, fill=NAVY, color=WHITE, bold=True)
    ys = (1.57, 2.52, 3.47)
    edges = ((0, 0), (1, 0), (1, 1), (2, 2))
    for a, b in edges:
        arrow(s, 4.08, ys[a]+.31, 7.47, ys[b]+.31, name=f"mapping:{a}:{b}")
    for i, (a, b) in enumerate(zip(("同じ情報を重複入力", "項目の形式が不統一", "確認状況が見えない"),
                                  ("共通フォームに統合", "入力項目を標準化", "担当者へ自動通知"))):
        box(s, a, .45, ys[i], 3.55, .65, fill=PALE2)
        box(s, b, 7.55, ys[i], 3.55, .65, fill=PALE)


def issue_tree(s):
    caption(s, "利用開始の遅れを分解し、検証する問いを定める")
    branches = ((1.23, "申請前の遅れ", ((.78, "要件を理解できるか"), (1.67, "必要書類が揃うか"))),
                (3.16, "申請後の遅れ", ((2.75, "確認待ちは長いか"), (3.64, "差戻しは多いか"))))
    for yy, label, leaves in branches:
        line(s, 3.05, 2.42, 3.47, 2.42, color=NAVY, width=1.8)
        line(s, 3.47, 2.42, 3.47, yy+.33, color=NAVY, width=1.8)
        arrow(s, 3.47, yy+.33, 3.9, yy+.33)
        for ly, question in leaves:
            line(s, 6.46, yy+.33, 6.88, yy+.33, color=NAVY, width=1.8)
            line(s, 6.88, yy+.33, 6.88, ly+.33, color=NAVY, width=1.8)
            arrow(s, 6.88, ly+.33, 7.3, ly+.33)
            box(s, question, 7.3, ly, 3.85, .65, fill=PALE2, size=18)
        box(s, label, 3.9, yy, 2.55, .65, fill=PALE, bold=True)
    box(s, "利用開始が遅い", .35, 1.95, 2.7, .94, fill=NAVY, color=WHITE, size=20, bold=True)


def calc_flow(s):
    caption(s, "作業時間の試算ロジック（単位をそろえて算出）")
    # Native shapes preserve each operand and the arithmetic chain.
    operands = (("対象件数", "120件", .55), ("1件の短縮時間", "15分 / 件", 4.37))
    for heading, value, x in operands:
        text(s, heading, x, .85, 2.85, .48, bold=True, color=NAVY, align=PP_ALIGN.CENTER)
        box(s, value, x, 1.55, 2.85, 1.0, fill=PALE, size=26, bold=True)
    text(s, "×", 3.66, 1.72, .5, .55, size=30, color=NAVY, align=PP_ALIGN.CENTER)
    arrow(s, 7.48, 2.05, 8.19, 2.05)
    text(s, "合計短縮時間", 8.42, .85, 2.65, .48, bold=True, color=NAVY, align=PP_ALIGN.CENTER)
    box(s, "1,800分", 8.42, 1.55, 2.65, 1.0, fill=NAVY, color=WHITE, size=26, bold=True)
    text(s, "÷ 60分 / 時間", 8.37, 2.87, 2.8, .5, size=18, align=PP_ALIGN.CENTER)
    arrow(s, 9.75, 2.6, 9.75, 2.85)
    box(s, "30時間", 8.42, 3.5, 2.65, .65, fill=PALE, bold=True, size=22)
    text(s, "件 × 分 / 件 ＝ 分\n時間への換算でも単位を明示する", .55, 3.22, 6.7, .86, size=18)


def cycle(s):
    caption(s, "共同研究の改善サイクル：評価結果を次の設計へ戻す")
    # Four orthogonal legs form a closed, directed loop; not a linear list.
    for coords in ((4.88, 1.12, 6.69, 1.12), (8.17, 1.72, 8.17, 2.81),
                   (6.69, 3.36, 4.88, 3.36), (3.4, 2.81, 3.4, 1.72)):
        arrow(s, *coords)
    for label, x, y, fill, color in (("1  設計", 1.93, .67, NAVY, WHITE),
                  ("2  実装", 6.69, .67, BLUE, INK),
                  ("3  検証", 6.69, 2.91, BLUE, INK),
                  ("4  改善", 1.93, 2.91, PALE, INK)):
        box(s, label, x, y, 2.95, .9, fill=fill, color=color, bold=True, size=21)
    text(s, "検証記録を共有\n次の設計に反映", 4.43, 1.92, 2.7, .76,
         size=18, bold=True, color=NAVY, align=PP_ALIGN.CENTER)
    text(s, "1サイクル：四半期単位", .35, 4.03, 10.8, .35, size=14, color=MUTED,
         align=PP_ALIGN.CENTER)


def decision_fork(s):
    caption(s, "データ提供の判断：同意と匿名化を順に確認する")
    # Route connectors are drawn behind nodes and explicitly labelled.
    arrow(s, 2.32, 2.15, 3.04, 2.15)
    arrow(s, 5.25, 2.15, 6.04, 2.15)
    arrow(s, 8.25, 2.15, 9.08, 2.15)
    arrow(s, 4.15, 2.81, 4.15, 3.43, name="decision-no:consent")
    arrow(s, 7.15, 2.81, 7.15, 3.43, name="decision-no:anonymize")
    box(s, "提供依頼", .35, 1.74, 1.97, .82, fill=NAVY, color=WHITE, bold=True)
    diamond(s, "同意あり？", 3.05, 1.5, 2.2, 1.3)
    diamond(s, "匿名化済？", 6.05, 1.5, 2.2, 1.3)
    box(s, "提供可", 9.08, 1.74, 2.1, .82, fill=NAVY, color=WHITE, bold=True)
    box(s, "同意を確認", 2.9, 3.47, 2.5, .7, fill=PALE, size=18)
    box(s, "匿名化を実施", 5.9, 3.47, 2.5, .7, fill=PALE, size=18)
    for value, x, y in (("はい", 5.31, 1.66), ("はい", 8.3, 1.66),
                         ("いいえ", 3.04, 3.01), ("いいえ", 6.1, 3.01)):
        text(s, value, x, y, .95, .37, size=14, color=MUTED)


def roadmap(s):
    caption(s, "共用データ基盤の段階的な整備ロードマップ")
    xs = (2, 4.95, 7.9)
    for x, title in zip(xs, ("2026年度：設計", "2027年度：試行", "2028年度：展開")):
        box(s, title, x, .65, 2.85, .57, fill=NAVY, color=WHITE, size=17, bold=True)
    tracks = (("基盤", ("要件を整理", "試作基盤を運用", "全学へ展開")),
              ("運用", ("管理責任を定義", "3部局で試行", "支援窓口を統合")))
    for i, (label, steps) in enumerate(tracks):
        yy = 1.57+i*1.03
        text(s, label, .4, yy+.13, 1.3, .45, bold=True, color=NAVY)
        for j, val in enumerate(steps):
            box(s, val, xs[j], yy, 2.85, .72, fill=PALE2 if i else PALE, size=18)
            if j < 2:
                arrow(s, xs[j]+2.85, yy+.36, xs[j+1]-.025, yy+.36)
    line(s, 2.2, 3.7, 10.9, 3.7, color=BLUE, width=2)
    for cx, label in ((3.4, "設計承認"), (6.35, "試行評価"), (9.3, "展開判断")):
        shape(s, cx-.085, 3.615, .17, .17, fill=NAVY, kind=MSO_SHAPE.DIAMOND,
              name=f"milestone:{label}")
        text(s, label, cx-1.25, 3.95, 2.5, .39, size=16, align=PP_ALIGN.CENTER)


def gantt(s):
    caption(s, "6か月の実行計画：期間と前後関係を明示")
    left, top, col, rowh = 2.95, 1.14, 1.3, .7
    tasks = (("要件定義", 0, 1), ("試作", 1, 2), ("利用者検証", 3, 1), ("改善・移行", 4, 2))
    # Paint ALL row surfaces first. Otherwise a later surface hides a route
    # or a time-grid line belonging to the preceding task.
    for i, (label, start, length) in enumerate(tasks):
        yy = top+i*rowh
        shape(s, .4, yy, 10.35, rowh-.035, fill=PALE2, name=f"gantt-row:{i}")
    for month in range(7):
        xx = left+month*col
        line(s, xx, top, xx, top+4*rowh-.035, color=RULE, name=f"gantt-grid:{month}")
        if month < 6:
            shape(s, xx, .57, col-.025, .46, fill=NAVY)
            text(s, f"{month+4}月", xx, .59, col-.025, .42, size=17,
                 color=WHITE, bold=True, align=PP_ALIGN.CENTER)
    for i, (label, start, length) in enumerate(tasks):
        yy = top+i*rowh
        text(s, label, .56, yy+.13, 2.25, .42, size=18, bold=True)
        shape(s, left+start*col, yy+.17, length*col, .35,
              fill=NAVY if i in (0, 3) else BLUE, name=f"gantt:{label}:{start}:{length}")
    for i, (label, start, length) in enumerate(tasks[:-1]):
        boundary = left+(start+length)*col
        yy = top+i*rowh
        arrow(s, boundary, yy+.53, boundary, yy+rowh+.14, name=f"dependency:{i}:{i+1}")
    text(s, "■ 作業期間　↓ 完了後に次工程を開始", .48, 4.11, 10.5, .33, size=14, color=MUTED)
