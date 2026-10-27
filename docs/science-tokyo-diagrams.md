# Editable Science Tokyo diagrams

The complex archetypes use **one native-editable PPTX source with exactly 22 slides** plus 22 PNGs for Marp. The PPTX is the editable original; a PPTX exported from the Marp catalog embeds the PNGs and is **not** the native diagram source.

- Source: `assets/science-tokyo/diagrams/science-tokyo-diagrams.pptx`
- Marp image: `assets/science-tokyo/diagrams/{id}.png`
- Lineage/structural manifest: `assets/science-tokyo/diagrams/manifest.json`
- Source canvas: **11.6 × 4.5 inches**; exports default to **2000 × 776 px**, contained without distortion in Marp's approximately 1160 × 450 px figure area.
- Only the diagram is exported. Marp supplies slide title, logo, pagination, and the fictional-data footer: `構成・数値は説明用の架空例`.

## Install the isolated Python environment

From the repository root, with Python 3.10+:

```sh
python3 -m venv .venv-diagrams
.venv-diagrams/bin/python -m pip install -r requirements-diagrams.txt
```

Do not use system pip. Also install system executables **LibreOffice (`soffice`) and Poppler (`pdfinfo`, `pdftoppm`)** using the host's normal package management. Missing executables, failed conversions, missing pages, invalid sizes, source changes during export, and stale assets are errors with nonzero exit status; there is no fake or image-only fallback.

LibreOffice uses a fresh isolated `UserInstallation` profile, and its temporary files live under the project-ignored `.verification/diagrams/`. The pipeline does not touch the user's normal LibreOffice profile. Python tests also keep their temporary workspaces there. A diagnostic `last-render.pdf` is retained there; tests can replace it with their own fixture render.

## Regenerate from definitions — destructive to manual edits

```sh
npm run diagrams:build
# Equivalent:
.venv-diagrams/bin/python scripts/build-science-tokyo-diagrams.py
```

**The default command regenerates and overwrites the native source, then renders all 22 PNGs. Any manual edits to the source are lost.** Use version control/backups before intentionally regenerating. No `--generate` flag is needed.

Definitions are split by responsibility:

| Module | Responsibility |
| --- | --- |
| `scripts/science_tokyo_diagrams/drawing.py` | Native shapes, typography, area scaling, axes, connectors, and explicit no-shadow styling |
| `scripts/science_tokyo_diagrams/charts.py` | Native charts and embedded editable workbooks, chart scales, labels, legends |
| `scripts/science_tokyo_diagrams/quantitative.py` | Quantitative archetype definitions and floating waterfall geometry |
| `scripts/science_tokyo_diagrams/processes.py` | Operational diagrams, routes, milestones, and time geometry |
| `scripts/science_tokyo_diagrams/source.py` | Native PPTX assembly, exact slide-ID validation, deterministic ZIP/workbook normalization |
| `scripts/science_tokyo_diagrams/export.py` | Isolated LibreOffice/Poppler execution and SHA256 lineage validation |
| `scripts/build-science-tokyo-diagrams.py` | CLI orchestration |

To generate only the editable source, without rendering:

```sh
.venv-diagrams/bin/python scripts/build-science-tokyo-diagrams.py --generate-only
```

This also overwrites the source and can deliberately leave old PNGs stale; `--check`/tests will fail until export runs.

## Edit the PPTX, then export without regenerating

1. Open `science-tokyo-diagrams.pptx` in PowerPoint or LibreOffice Impress.
2. Edit native text, shapes, connectors, or native charts' **Edit Data** workbooks. Do not flatten slides. Preserve the 22-slide order, slide names/IDs, and 11.6 × 4.5-inch canvas. Do not rename slide IDs.
3. Save the source PPTX.
4. Run **export-only**, not the default regeneration command:

```sh
npm run diagrams:export
# Equivalent:
.venv-diagrams/bin/python scripts/build-science-tokyo-diagrams.py --export-only
```

`--export-only` (`--export-existing` is an alias) reads the source and **never rewrites or regenerates it**. It exports all 22 slides and updates the source SHA256 → slide ID/filename → PNG SHA256 manifest. Tests exercise a real manual text edit, reject its stale old PNGs, export the edited source, and verify source bytes are unchanged.

Native-shape quantitative diagrams do not have hidden spreadsheet formulas: if changing waterfall values, circles, or Gantt schedules manually, update corresponding geometry, labels, and connectors consistently. Alternatively change definitions and intentionally regenerate. The export-only command respects manual shapes rather than recomputing them.

Useful explicit options:

```sh
# Use a separate source/output location for experimentation:
.venv-diagrams/bin/python scripts/build-science-tokyo-diagrams.py \
  --export-only --source path/to/edited.pptx --output-dir .verification/edited-diagrams

# Higher raster resolution; widths below 1600 are rejected:
.venv-diagrams/bin/python scripts/build-science-tokyo-diagrams.py --export-only --width 2400

# Print the fixed native-slide-to-PNG mapping:
.venv-diagrams/bin/python scripts/build-science-tokyo-diagrams.py --list

# Read-only freshness and integrity validation:
.venv-diagrams/bin/python scripts/build-science-tokyo-diagrams.py --check
```

The output directory is reserved for these 22 PNG names. Unexpected `.png` files are rejected rather than deleted or silently ignored. Export first renders all pages to staging and validates page count/resolution, then publishes PNGs and finally the manifest. Source changes during export cause a failure. The manifest records renderer versions, per-slide native-shape/chart counts, source hash, image hashes, dimensions, IDs, and slide order.

## Fixed slide mapping and numerical integrity

All values are fictional academic/research-planning illustrations, not real research findings.

| Source slide | ID / PNG stem | Editable structure and invariant |
| ---: | --- | --- |
| 1 | `dot_matrix_share` | 100 native circles; exactly 64 navy/public records |
| 2 | `progress_bubble_matrix` | Theme × stage grid; circle **area** encodes achievement; 0% has no circle |
| 3 | `ranked_bar_annotated` | Native horizontal chart; 18, 14, 10, 6 applications; zero-origin count axis |
| 4 | `scatter_annotated` | Native XY chart; actual cost/readiness coordinates, units, legend |
| 5 | `proportional_circles` | 25/50/100 records; areas 1:2:4, diameters proportional to square roots |
| 6 | `delta_bars_totals` | Zero-baseline signed changes; 64 + 18 − 8 + 12 = 86; endpoint totals |
| 7 | `scenario_lines_cagr` | Native XY chart; actual annual compound values, 2026–2029; 20%/10%/5% CAGR |
| 8 | `swimlane_numbered_notes` | Researcher/administration/platform lanes; cross-lane handoffs and linked numbered notes |
| 9 | `front_back_two_tier` | User-facing steps vertically aligned to corresponding back-office operations |
| 10 | `chart_insight` | Native quarterly chart; 24/32/40/48 uses; labeled count axis and 2× implication |
| 11 | `stacked_bar` | Native stacked chart; three purpose series; totals 40/60/80; readable segment labels and legend |
| 12 | `waterfall` | Native floating contribution bars: 40 → +20 → −10 → +15 → 65; endpoint totals start at zero |
| 13 | `true_waterfall` | Native strict bridge: 80 → +30 → −20 → +10 → 100; cumulative connector levels |
| 14 | `small_multiples` | Three editable point/line plots; identical 0–100% scale, quarterly categories |
| 15 | `matrix_2x2` | Two explicit qualitative axes, four quadrants, labeled research initiatives |
| 16 | `issue_to_solution_map` | Explicit many-to-one/one-to-many issue/action connector mapping |
| 17 | `issue_tree` | Root issue → before/after-application branches → four diagnostic questions |
| 18 | `calc_flow` | 120 records × 15 min/record = 1,800 min ÷ 60 min/hour = 30 hours |
| 19 | `cycle` | Closed directed four-stage design/implementation/validation/improvement loop |
| 20 | `decision_fork` | Two sequential decisions; separately routed negative outcomes and labeled yes/no paths |
| 21 | `roadmap` | Three yearly phases, two workstreams, and explicit review milestones |
| 22 | `gantt` | Six monthly columns; 1/2/1/2-month task bars and visible completion dependencies |

There are five native charts with five embedded XLSX workbooks. The remaining diagrams use native DrawingML text, shapes, and connectors, not screenshots. No reference-company branding or source images are imported. Shapes are rectangular except meaningful circles/decision diamonds; no rounded cards, gradients, or shadows. The generator explicitly disables the default PowerPoint theme's inherited shape/connector shadows.

## Fonts and rendering

All newly authored text retains the existing **Yu Gothic** family metadata. Body diagram text is normally 18 pt (approximately 25 px at 1160 px width); compact chart labels/units/legends use a **14 pt minimum** (approximately 19 px). No font family is added to the template or silently substituted in the PPTX source.

On the exercised Linux host, `fc-match :lang=ja` resolves to **Noto Sans CJK JP**, while generic `fc-match "Yu Gothic"` resolves to Noto Sans because Yu Gothic itself is absent. LibreOffice's actual rendered PDF embeds Noto Sans CJK SC and Noto Sans fallback faces, as reported by `pdffonts`. The rendered Japanese labels were visually inspected and contain real glyphs, not tofu. This is existing host fallback behavior, not a changed source font declaration. PowerPoint on a system with Yu Gothic can render differently; review before publishing.

Source generation is byte-deterministic with the pinned dependency set: ZIP timestamps, package ordering, PPTX core dates, and embedded XLSX core dates are normalized. Repeated PNG export is tested byte-for-byte on the same renderer/font environment. Raster bytes are **not** promised identical across LibreOffice/Poppler/font versions or operating systems; the manifest records the actual renderer versions.

## Verification

```sh
.venv-diagrams/bin/python -m unittest discover -s tests -p test_diagrams.py
# Or the parent's npm wrapper:
npm run test:diagrams
```

The suite checks native source count/order/IDs, no raster media, native chart workbooks/data, geometry and typography bounds, circle-area scaling, actual floating waterfall contributions, real scenario growth values, shared small-multiple scales, Gantt time geometry/layer order, distinct negative decision routes, no inherited theme shadows, label contrast, deterministic source/export bytes, and actual rendered 22-image resolution/aspect/content bounds. It also exercises export failure, missing/corrupt PNGs, wrong IDs, stale source hashes, and preservation of manual edits.

**The repository-asset synchronization test is unconditional.** It reads the delivered source and PNG manifest, so changing the source without `--export-only` fails `test:diagrams` before the parent rebuilds the catalog. Tests render to isolated fixture workspaces, not to the delivered assets.

For visual review, inspect all 22 exported PNGs (contact sheets are useful), especially after manual edits or renderer/font changes. Structural tests complement visual inspection; they cannot certify every possible text collision in arbitrary hand-edited sources.
