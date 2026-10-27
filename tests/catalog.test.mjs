import test from 'node:test';
import assert from 'node:assert/strict';
import { existsSync, readFileSync } from 'node:fs';
import { Marp } from '@marp-team/marp-core';
import engine from '../engine.mjs';

const root = new URL('../', import.meta.url);
const file = (path) => new URL(path, root);
const read = (path) => readFileSync(file(path), 'utf8');
const expectedIds = `
title_page overview_map table_of_contents section_divider chevron_steps
premise_conclusion stat_table_readout card_grid_2x2 axis_table back_cover
claim_panel_figure lever_effect_table status_heatmap_comment harvey_ball_table
 dot_matrix_share progress_bubble_matrix ranked_bar_annotated scatter_annotated
pillars_foundation opposing_chevrons evidence_clip_grid proportional_circles
delta_bars_totals scenario_lines_cagr research_basis issue_action_columns
agenda_separator swimlane_numbered_notes front_back_two_tier qa_list
executive_summary evidence_basis big_stat_pair kpi_dashboard chart_insight
stacked_bar waterfall true_waterfall small_multiples comparison_table
scenario_table risk_table horizontal_axis_table heatmap_table matrix_2x2
process_matrix nested_row_matrix timeline_matrix theme_card_grid
recommendation_pillars numbered_imperatives scr issue_to_solution_map
issue_cause_solution issue_tree current_target_state calc_flow process_flow
cycle chevron_rail chevron_value_chain decision_fork roadmap gantt decision_page
`.trim().split(/\s+/);
const expectedKeys = [
  ...Array.from({ length: 30 }, (_, i) => `b${String(i + 1).padStart(2, '0')}`),
  ...Array.from({ length: 35 }, (_, i) => `m${String(i + 1).padStart(2, '0')}`),
];
const complexIds = new Set(`dot_matrix_share progress_bubble_matrix
ranked_bar_annotated scatter_annotated proportional_circles delta_bars_totals
scenario_lines_cagr swimlane_numbered_notes front_back_two_tier chart_insight
stacked_bar waterfall true_waterfall small_multiples matrix_2x2
issue_to_solution_map issue_tree calc_flow cycle decision_fork roadmap gantt`
  .trim().split(/\s+/));

// Characterize the installed renderer, not a homemade split-on---- parser.
// Frontmatter is metadata (not a slide); pattern comments move to comments[].
// h2 is body content; localized _class applies only to its own slide.
test('installed Marp consumes YAML and keeps pattern comments indexed by slide', () => {
  const rendered = new Marp({ html: true }).render(`---
marp: true
theme: science-tokyo
paginate: true
header: ""
footer: 構成・数値は説明用の架空例
math: katex
---
<!-- pattern: b01 title_page -->
<!-- _class: title -->
# 表紙

## 架空研究計画

---
<!-- pattern: b02 overview_map -->
# 全体マップ
`);
  const sections = [...rendered.html.matchAll(/<section\b[^>]*>[\s\S]*?<\/section>/g)]
    .map(([html]) => html);
  assert.equal(sections.length, 2);
  assert.equal((rendered.html.match(/<h1\b/g) ?? []).length, 2);
  assert.equal((rendered.html.match(/<h2\b/g) ?? []).length, 1);
  assert.match(sections[0], /class="title"/);
  assert.doesNotMatch(sections[1], /class="title"/);
  assert.ok(sections.every((html) => html.includes('<footer>構成・数値は説明用の架空例</footer>')));
  assert.ok(sections.every((html) => /data-paginate="true"/.test(html)));
  assert.deepEqual(rendered.comments, [
    ['pattern: b01 title_page'], ['pattern: b02 overview_map'],
  ]);
  assert.doesNotMatch(rendered.html, /marp: true|math: katex/);
});

test('catalog has all 65 pinned source IDs in exact b01..b30,m01..m35 order', () => {
  assert.ok(existsSync(file('catalog/science-tokyo.json')),
    'missing catalog/science-tokyo.json: the complete 65-pattern manifest is required');
  const catalog = JSON.parse(read('catalog/science-tokyo.json'));
  assert.deepEqual(catalog.reference, {
    repository: 'https://github.com/carnot-tech/jinba-consulting-pptx-skill',
    revision: 'e5f35e57e14d3998249a559c620a9286c95b4595',
  });
  assert.equal(catalog.patterns.length, 65);
  assert.deepEqual(catalog.patterns.map((p) => p.key), expectedKeys);
  assert.deepEqual(catalog.patterns.map((p) => p.id), expectedIds);
  assert.equal(new Set(catalog.patterns.map((p) => p.key)).size, 65);
  assert.equal(new Set(catalog.patterns.map((p) => p.id)).size, 65);
  for (const [index, pattern] of catalog.patterns.entries()) {
    assert.equal(pattern.slide, index + 1, pattern.key);
    assert.equal(pattern.source, 'slides/science-tokyo-catalog.md', pattern.key);
    assert.match(pattern.title, /[\u3040-\u30ff\u3400-\u9fff]/, pattern.key);
    assert.equal(pattern.mode, complexIds.has(pattern.id) ? 'pptx-image' : 'markdown', pattern.key);
    assert.equal(pattern.diagram, complexIds.has(pattern.id)
      ? `assets/science-tokyo/diagrams/${pattern.id}.png` : null, pattern.key);
  }
  assert.equal(catalog.patterns.filter((p) => p.mode === 'pptx-image').length, 22);
  assert.equal(catalog.patterns.filter((p) => p.mode === 'markdown').length, 43);
  const pinned = JSON.parse(read('catalog/reference-archetypes.json'));
  assert.deepEqual(catalog.reference, { repository: pinned.repository, revision: pinned.revision });
  assert.deepEqual(catalog.patterns.map(({ key, id, title }) => ({ key, id, title })), pinned.patterns,
    'IDs and unabridged Japanese type titles must match the separately pinned source catalog');
});

test('the deck renders exactly 65 indexed slides with visible type headings', () => {
  assert.ok(existsSync(file('slides/science-tokyo-catalog.md')),
    'missing slides/science-tokyo-catalog.md: every pattern needs a usable example');
  const source = read('slides/science-tokyo-catalog.md');
  const catalog = JSON.parse(read('catalog/science-tokyo.json'));
  const marp = engine({ marp: new Marp({ html: true }) });
  const rendered = marp.render(source);
  const sections = [...rendered.html.matchAll(/<section\b[^>]*>[\s\S]*?<\/section>/g)]
    .map(([html]) => html);
  assert.equal(sections.length, 65);
  assert.equal(rendered.comments.length, 65);
  assert.doesNotMatch(rendered.html, /<p>:{3,}|\|\|\|/,
    'all catalog containers and column separators must be consumed by the installed engine');
  assert.match(source, /^---\r?\nmarp: true\r?\ntheme: science-tokyo\r?\npaginate: true\r?\n/);
  assert.match(source, /^math: katex$/m);
  for (const [index, pattern] of catalog.patterns.entries()) {
    const html = sections[index];
    const comments = rendered.comments[index];
    assert.equal(comments.filter((text) => text.startsWith('pattern:')).length, 1, pattern.key);
    assert.ok(comments.includes(`pattern: ${pattern.key} ${pattern.id}`), pattern.key);
    assert.ok(comments.some((text) => text.startsWith('source: ') && text.includes(catalog.reference.revision)), pattern.key);
    assert.equal((html.match(/<h1\b/g) ?? []).length, 1, pattern.key);
    const heading = html.match(/<h1\b[^>]*>([\s\S]*?)<\/h1>/)?.[1].replace(/<[^>]*>/g, '');
    assert.ok(heading.startsWith(pattern.title.split('（')[0]), `${pattern.key}: ${heading}`);
    assert.ok(html.includes(pattern.id), `visible, copyable ID: ${pattern.key}`);
    assert.ok(html.includes('<footer>構成・数値は説明用の架空例</footer>'), pattern.key);
    assert.match(html, /data-paginate="true"/, pattern.key);
    assert.equal((html.match(/<img\b/g) ?? []).length, pattern.mode === 'pptx-image' ? 1 : 0, pattern.key);
    if (pattern.mode === 'pptx-image') {
      assert.ok(html.includes(`src="../${pattern.diagram}"`), pattern.key);
      assert.match(html, /class="figure"/, pattern.key);
      assert.match(html, /class="cite"/, pattern.key);
      assert.doesNotMatch(html, /<h[2-6]\b|<table\b|<ul\b|<ol\b/, pattern.key);
      assert.equal((html.match(/<p\b/g) ?? []).length, 2, `diagram + short cite only: ${pattern.key}`);
    }
  }
  assert.match(sections[0], /class="title"/);
  assert.match(sections[3], /class="section"/);
  for (const index of [9, 26]) assert.doesNotMatch(sections[index], /class="(?:title|section)"/);
  const allowed = new Set('cols cols-3 columns columns-3 box card navy-card callout lead cite cite-right center small xs col note info warning grid-2 grid-3 stack metric band foundation steps step matrix compare figure'.split(' '));
  for (const match of source.matchAll(/^:{3,}[ \t]+([A-Za-z][\w-]*)/gm)) {
    assert.ok(allowed.has(match[1]), `uncontracted container: ${match[1]}`);
  }
  assert.doesNotMatch(source, /font-size\s*:|transform\s*:\s*scale|^<style\b/im,
    'examples must not shrink or replace the inherited type scale');
});

test('documentation indexes every source key, target slide, and editable mode', () => {
  assert.ok(existsSync(file('docs/science-tokyo-catalog.md')),
    'missing docs/science-tokyo-catalog.md: a copyable 65-row index is required');
  const docs = read('docs/science-tokyo-catalog.md');
  const rows = [...docs.matchAll(/^\| (b\d{2}|m\d{2}) \| (\d+) \| `([^`]+)` \|/gm)];
  assert.equal(rows.length, 65);
  assert.deepEqual(rows.map((row) => row[1]), expectedKeys);
  assert.deepEqual(rows.map((row) => row[3]), expectedIds);
  assert.deepEqual(rows.map((row) => Number(row[2])), Array.from({ length: 65 }, (_, i) => i + 1));
  assert.ok(docs.includes('e5f35e57e14d3998249a559c620a9286c95b4595'));
  assert.ok(docs.includes('templates/freeform_parts_16x9.html'));
  assert.ok(docs.includes('templates/freeform_parts_more_16x9.html'));
  assert.ok(docs.includes('science-tokyo-diagrams.pptx'));
  assert.ok(docs.includes('架空'));
  assert.ok(docs.includes('node --test tests/catalog.test.mjs'));
  const catalog = JSON.parse(read('catalog/science-tokyo.json'));
  const indexLines = docs.split('\n').filter((line) => /^\| [bm]\d{2} \|/.test(line));
  for (const [i, pattern] of catalog.patterns.entries()) {
    assert.ok(indexLines[i].includes(`| ${pattern.title} |`), pattern.key);
    assert.ok(indexLines[i].includes(`| \`${pattern.mode}\` |`), pattern.key);
    const origin = pattern.key.startsWith('b')
      ? 'templates/freeform_parts_16x9.html' : 'templates/freeform_parts_more_16x9.html';
    assert.ok(indexLines[i].includes(`/${catalog.reference.revision}/${origin}`), pattern.key);
  }
});

// Structural characterization guards against a catalog of relabelled cards.
// These checks are deliberately about the relationship each native type shows.
test('native examples retain tables, row hierarchy, pillars, Q&A and opposed directions', () => {
  const rendered = engine({ marp: new Marp({ html: true }) })
    .render(read('slides/science-tokyo-catalog.md'));
  const sections = [...rendered.html.matchAll(/<section\b[^>]*>[\s\S]*?<\/section>/g)]
    .map(([html]) => html);
  const byKey = Object.fromEntries(expectedKeys.map((key, i) => [key, sections[i]]));
  for (const key of ['b09', 'b12', 'b13', 'b14', 'm10', 'm11', 'm12', 'm13', 'm14', 'm16', 'm17', 'm18']) {
    assert.match(byKey[key], /<table\b/, key);
    assert.doesNotMatch(byKey[key], /class="card"/, key);
  }
  assert.equal((byKey.b08.match(/class="card"/g) ?? []).length, 4);
  assert.match(byKey.b08, /class="grid-2"/);
  assert.match(byKey.b07, /<td><h2>24 件<\/h2><\/td>/);
  assert.match(byKey.b07, /読み取り/);
  assert.equal((byKey.b19.match(/class="navy-card"/g) ?? []).length, 3);
  assert.match(byKey.b19, /class="foundation"/);
  assert.match(byKey.b20, /研究班から →/);
  assert.match(byKey.b20, /← 支援室から/);
  assert.equal((byKey.b20.match(/clip-path:/g) ?? []).length, 2);
  assert.equal((byKey.b30.match(/scope="row"/g) ?? []).length, 3);
  assert.equal((byKey.b30.match(/<strong>A\.<\/strong>/g) ?? []).length, 3);
  assert.equal((byKey.m17.match(/rowspan="2"/g) ?? []).length, 2);
  assert.match(byKey.m22, /class="stack"/);
  assert.equal((byKey.m22.match(/<h3\b/g) ?? []).length, 3);
  assert.match(byKey.m26, /class="compare"/);
  assert.equal((byKey.m28.match(/class="step"/g) ?? []).length, 4);
  assert.match(byKey.m35, /決めること/);
  assert.match(byKey.m35, /前提/);
  assert.match(byKey.m35, /依頼/);
});
