"""Science Tokyo editable diagram sources and validated raster exports."""
from . import quantitative as q, processes as p

DEFINITIONS = (
    ("dot_matrix_share", q.dot_matrix_share),
    ("progress_bubble_matrix", q.progress_bubble_matrix),
    ("ranked_bar_annotated", q.ranked_bar_annotated),
    ("scatter_annotated", q.scatter_annotated),
    ("proportional_circles", q.proportional_circles),
    ("delta_bars_totals", q.delta_bars_totals),
    ("scenario_lines_cagr", q.scenario_lines_cagr),
    ("swimlane_numbered_notes", p.swimlane_numbered_notes),
    ("front_back_two_tier", p.front_back_two_tier),
    ("chart_insight", q.chart_insight),
    ("stacked_bar", q.stacked_bar),
    ("waterfall", q.waterfall),
    ("true_waterfall", q.true_waterfall),
    ("small_multiples", q.small_multiples),
    ("matrix_2x2", q.matrix_2x2),
    ("issue_to_solution_map", p.issue_to_solution_map),
    ("issue_tree", p.issue_tree),
    ("calc_flow", p.calc_flow),
    ("cycle", p.cycle),
    ("decision_fork", p.decision_fork),
    ("roadmap", p.roadmap),
    ("gantt", p.gantt),
)
IDS = tuple(name for name, _ in DEFINITIONS)
SOURCE_NAME = "science-tokyo-diagrams.pptx"
MANIFEST_NAME = "manifest.json"


def mapping():
    return [{"id": name, "slide": i, "file": f"{name}.png"}
            for i, name in enumerate(IDS, 1)]
