import assert from 'node:assert/strict';
import { createHash } from 'node:crypto';
import { readFileSync } from 'node:fs';
import { after, test } from 'node:test';
import { Marp } from '@marp-team/marp-core';
import puppeteer from 'puppeteer-core';
import configure from '../engine.mjs';

const root = new URL('../', import.meta.url);
const theme = readFileSync(new URL('science-tokyo.css', root), 'utf8');
const fixture = readFileSync(new URL('tests/fixtures/components.md', root), 'utf8');
const hash = (text) => createHash('sha256').update(text).digest('hex');
function render(source) {
  const marp = configure({ marp: new Marp({ html: true }) });
  marp.themeSet.add(theme);
  return marp.render(source);
}
let browser;
after(async () => { if (browser) await browser.close(); });
async function inSlide(source, inspect, ...args) {
  browser ??= await puppeteer.launch({
    executablePath: process.env.CHROME_PATH || '/usr/bin/google-chrome',
    headless: true,
    args: ['--no-sandbox', '--disable-dev-shm-usage'],
  });
  const page = await browser.newPage();
  try {
    await page.setViewport({ width: 1280, height: 720 });
    const { html, css } = render(source);
    await page.setContent(`<style>${css}</style>${html}`, { waitUntil: 'domcontentloaded' });
    await page.evaluate(() => document.fonts.ready);
    return await page.evaluate(inspect, ...args);
  } finally {
    await page.close();
  }
}

// Executed in real Chrome. Composite the named components' solid background
// layers, including transparent cells over table rows, before measuring text.
function computedTextContrast(selector) {
  const rgba = (color) => {
    const channels = color.match(/[\d.]+/g).map(Number);
    return [...channels.slice(0, 3), channels[3] ?? 1];
  };
  const over = (front, back) => front.slice(0, 3)
    .map((value, index) => value * front[3] + back[index] * (1 - front[3]));
  const luminance = (rgb) => rgb.map((value) => {
    const channel = value / 255;
    return channel <= 0.04045 ? channel / 12.92 : ((channel + 0.055) / 1.055) ** 2.4;
  }).reduce((sum, value, index) => sum + value * [0.2126, 0.7152, 0.0722][index], 0);
  return Array.from(document.querySelectorAll(selector)).flatMap((scope) => [scope, ...scope.querySelectorAll('*')])
    .filter((node) => Array.from(node.childNodes).some((child) => child.nodeType === Node.TEXT_NODE && child.textContent.trim()))
    .map((node) => {
      const ancestors = [];
      for (let ancestor = node; ancestor; ancestor = ancestor.parentElement) ancestors.unshift(ancestor);
      const background = ancestors.reduce((back, ancestor) => over(rgba(getComputedStyle(ancestor).backgroundColor), back), [255, 255, 255]);
      const color = getComputedStyle(node).color;
      const foreground = over(rgba(color), background);
      const a = luminance(foreground);
      const b = luminance(background);
      return {
        element: node.tagName.toLowerCase(), class: node.className, text: node.textContent.trim(),
        color, background, contrast: (Math.max(a, b) + 0.05) / (Math.min(a, b) + 0.05),
      };
    });
}

function assertBandContrast(samples) {
  assert.ok(samples.length > 0, 'measure real rendered text');
  assert.deepEqual(samples.filter(({ contrast }) => contrast < 4.5), [], 'foreground must contrast with its effective background');
  for (const sample of samples) {
    assert.equal(sample.color, 'rgb(255, 255, 255)', JSON.stringify(sample));
    assert.deepEqual(sample.background, [28, 48, 119], JSON.stringify(sample));
  }
}

test('legacy source templates retain identical rendered HTML', () => {
  const expected = {
    'slides/science-tokyo-template.md': '71b09b6f47fa978ce1c82792fb1b32398138c0ffcd9c9ec500501bf71cc14d54',
    'slides/sample.md': 'bdca3870c9586dbd843c30d4fe032eed4c8ac89a39548fe48cd1af75d2d3232c',
  };
  for (const [file, digest] of Object.entries(expected)) {
    assert.equal(hash(render(readFileSync(new URL(file, root), 'utf8')).html), digest, file);
  }
});

test('legacy typography declarations and imports stay byte-for-byte unchanged', () => {
  const typography = theme.split('ASSET DATA')[0]
    .match(/@import[^;]*;|(?:font[\w-]*|line-height|letter-spacing)\s*:[^;]*;/g);
  assert.equal(hash(JSON.stringify(typography)), '9130342cf79c2073dc4cc488cc802bf6e820a8d3b7809e1fcc31edd538aafaba');
});

test('all contract containers render their named semantic wrappers', async () => {
  const names = ['grid-2', 'grid-3', 'stack', 'metric', 'band', 'foundation', 'steps', 'step', 'matrix', 'compare', 'figure'];
  for (const name of names) {
    const { html } = render(`::: ${name}\n\nBody ${name}\n\n:::`);
    assert.ok(html.includes(`<div class="${name}">`), `${name} must render as a container`);
    assert.ok(!html.includes(':::'));
  }
});

test('columns scope separators through nested columns and grids', async () => {
  const source = [
    ':::::: cols',
    '::::: columns 2',
    ':::: grid-2', '::: card', 'Alpha', ':::', '::: card', 'Beta', ':::', '::::',
    '|||', 'Inner right', ':::::',
    '|||', 'Outer right', '::::::',
    'After all containers',
  ].join('\n\n');
  const structure = await inSlide(source, () => {
    const outer = document.querySelector('section > .columns');
    const inner = outer?.querySelector('.columns');
    return {
      outer: outer?.children.length,
      inner: inner?.children.length,
      cards: inner?.querySelectorAll('.grid-2 > .card').length,
      outside: document.querySelector('section > p:last-child')?.textContent,
      right: outer?.lastElementChild.textContent.trim(),
    };
  });
  assert.deepEqual(structure, { outer: 2, inner: 2, cards: 2, outside: 'After all containers', right: 'Outer right' });
});

for (const kind of ['cols', 'grid-2']) {
  test(`${kind} ignores container markers and separators inside fenced code`, async () => {
    const source = [
      `:::: ${kind}`, '::: card', 'Before',
      '~~~~md', '::: warning', '|||', '::::', '~~~~',
      'After code', ':::',
      ...(kind === 'cols' ? ['|||', 'Right'] : ['::: card', 'Right', ':::']),
      '::::', 'Outside',
    ].join('\n\n');
    const result = await inSlide(source, () => {
      const layout = document.querySelector('.columns, .grid-2');
      return {
        children: layout?.children.length,
        code: layout?.querySelector('pre code, marp-pre code')?.textContent.trim(),
        body: layout?.textContent.includes('After code'),
        outside: document.querySelector('section > p:last-child')?.textContent,
      };
    });
    assert.deepEqual(result, { children: 2, code: '::: warning\n\n|||\n\n::::', body: true, outside: 'Outside' });
  });
}

// Frozen HTML hashes were measured with .verification/baseline/engine.mjs,
// the pre-implementation engine, using the same Marp options and theme.
for (const [kind, literal, expected] of [
  ['comment', '<!--\n::: warning\n-->', '3f4c8e217739eb1f5e65a4368e5fb408bd3ae6cbae9dd9ac212634d2682fbdae'],
  ['pre', '<pre>\n::: warning\n</pre>', '32f9a7b1ab0c280a2977d735d1263c7a5791fc5176fe722cd153cb8f6120612c'],
]) {
  test(`HTML ${kind} literal markers retain the baseline outer card boundary`, async () => {
    const source = `:::: card\n${literal}\n::::\nOutside`;
    assert.equal(hash(render(source).html), expected, 'match the frozen baseline HTML');
    const structure = await inSlide(source, () => ({
      outside: document.querySelector('section > p:last-child')?.textContent,
      warnings: document.querySelectorAll('.warning').length,
      literal: document.querySelector('.card pre, .card marp-pre')?.textContent.trim() ?? null,
    }));
    assert.deepEqual(structure, { outside: 'Outside', warnings: 0, literal: kind === 'pre' ? '::: warning' : null });
  });
}

// Frozen baseline HTML hash uses the exact quoted-attribute counterregression.
test('raw HTML quoted-attribute pre text retains the baseline card boundary in Chrome', async () => {
  const source = ':::: card\n<div data-example="\n<pre>\n">\nRaw body\n</div>\n\n::::\nOutside';
  const structure = await inSlide(source, () => ({
    outside: document.querySelector('section > p:last-child')?.textContent ?? null,
    cardOutside: document.querySelector('.card')?.textContent.includes('Outside'),
    residue: document.querySelector('section')?.textContent.includes('::::'),
    attribute: document.querySelector('.card > div')?.getAttribute('data-example'),
    rawBody: document.querySelector('.card > div')?.textContent.trim(),
  }));
  assert.deepEqual({ html: hash(render(source).html), structure }, {
    html: 'd9fd64df53c94c7a0a31f13e341d7fa62f4c782125f3ea6411a799cc616fbee4',
    structure: { outside: 'Outside', cardOutside: false, residue: false, attribute: '\n<pre>\n', rawBody: 'Raw body' },
  });
});

// Raw HTML block ownership ends at the installed parser's end rule; literal
// protection resumes after that end, but type-7 inline tags cannot interrupt a paragraph.
for (const [context, body, expected, literal] of [
  ["generic div body pre", "<div>\n<pre>\nRaw body\n</pre>\n</div>", "d42040693e96a696686b3a01d2cde489a2a7f7220a904475fc6fd72b10aaeba0", "Raw body"],
  ["generic div quoted script marker", "<div data-example=\"\n<script>\n\">\nRaw body\n</div>", "b835ee2d4ba621e9f845517bcd5f1ee8ed9e770a8a523721f55082b20e563670", null],
  ["actual pre after generic div blank-line end", "<div>Raw body</div>\n\n<pre>\n::: warning\n~~~md\n</pre>", "2b861a9f579990629406a5bdb089661e543d396589f91a56c27e475d0a235b70", "::: warning\n~~~md"],
  ["actual comment after generic div blank-line end", "<div>Raw body</div>\n\n<!--\n::: warning\n~~~md\n-->", "56cdfa2ef81dc53a4657428ed62764ff92c29c93a784002a4209231d4a762512", null],
  ["actual pre after paragraph inline tag", "Lead paragraph\n<span></span>\n<pre>\n::: warning\n~~~md\n</pre>", "3b3bbe1dc321fe3f6f07d88bdc4e1cc5976f630de7abb2f69f54e0c421a8e9f5", "::: warning\n~~~md"],
]) {
  test(`raw HTML context ${context} retains baseline HTML and the outside boundary in Chrome`, async () => {
    const source = `:::: card\n${body}\n\n::::\nOutside`;
    const structure = await inSlide(source, () => ({
      outside: document.querySelector('section > p:last-child')?.textContent ?? null,
      cardOutside: document.querySelector('.card')?.textContent.includes('Outside'),
      residue: document.querySelector('section')?.textContent.includes('::::'),
      warnings: document.querySelectorAll('.warning').length,
      literal: document.querySelector('.card pre, .card marp-pre')?.textContent.trim() ?? null,
    }));
    assert.deepEqual({ html: hash(render(source).html), structure }, {
      html: expected, structure: { outside: 'Outside', cardOutside: false, residue: false, warnings: 0, literal },
    });
  });
}

for (const [kind, open, close] of [['comment', '<!--', '-->'], ['pre', '<PRE class="example">', '</PRE>']]) {
  test(`columns ignore separators, closing markers and code fences inside HTML ${kind} blocks`, async () => {
    const source = [
      ':::: cols', open, '::: warning', '|||', '::::', '~~~md', close,
      'Left', '|||', 'Right', '::::', 'Outside',
    ].join('\n');
    const structure = await inSlide(source, () => {
      const columns = document.querySelector('section > .columns');
      return {
        children: columns?.children.length,
        left: columns?.firstElementChild.querySelector('p')?.textContent,
        right: columns?.lastElementChild.textContent.trim(),
        outside: document.querySelector('section > p:last-child')?.textContent,
        warnings: document.querySelectorAll('.warning').length,
      };
    });
    assert.deepEqual(structure, { children: 2, left: 'Left', right: 'Right', outside: 'Outside', warnings: 0 });
  });
}

test('grid, comparison and matrix form equal rectangular tracks', async () => {
  const layouts = await inSlide(fixture, () => ['grid-2', 'grid-3', 'compare', 'matrix'].map((name) => {
    const node = document.querySelector(`.${name}`);
    const css = getComputedStyle(node);
    return {
      name, display: css.display, tracks: css.gridTemplateColumns.split(' ').map(parseFloat),
      children: Array.from(node.children, (child) => ({ x: child.offsetLeft, y: child.offsetTop, width: child.offsetWidth })),
    };
  }));
  for (const layout of layouts) {
    assert.equal(layout.display, 'grid', layout.name);
    assert.equal(layout.tracks.length, layout.name === 'grid-3' ? 3 : 2, layout.name);
    assert.ok(Math.max(...layout.tracks) - Math.min(...layout.tracks) < 1, `${layout.name}: equal-width tracks`);
    if (['grid-2', 'matrix'].includes(layout.name)) {
      assert.equal(layout.children.length, 4);
      assert.equal(layout.children[0].y, layout.children[1].y);
      assert.ok(layout.children[2].y > layout.children[0].y, '2×2 arrangement');
    }
  }
});

test('metric and foundation use structured number blocks and a full-width base', async () => {
  const result = await inSlide(fixture, () => {
    const metrics = Array.from(document.querySelectorAll('.metric'));
    const foundation = document.querySelector('.foundation');
    const stack = document.querySelector('.stack');
    return {
      metrics: metrics.map((node) => ({
        radius: getComputedStyle(node).borderRadius,
        rule: parseFloat(getComputedStyle(node).borderBottomWidth),
        headingSize: getComputedStyle(node.querySelector('h2')).fontSize,
      })),
      foundation: { background: getComputedStyle(foundation).backgroundColor, width: foundation.offsetWidth, radius: getComputedStyle(foundation).borderRadius },
      stack: { display: getComputedStyle(stack).display, gap: parseFloat(getComputedStyle(stack).gap) },
    };
  });
  assert.equal(result.metrics.length, 3);
  for (const metric of result.metrics) {
    assert.equal(metric.radius, '0px');
    assert.ok(metric.rule >= 2, 'metric needs a visible baseline rule');
    assert.equal(metric.headingSize, '30px', 'reuse the unchanged h2 scale');
  }
  assert.deepEqual(result.foundation, { background: 'rgb(232, 236, 244)', width: 1160, radius: '0px' });
  assert.equal(result.stack.display, 'grid');
  assert.ok(result.stack.gap >= 12);
});

test('steps are equal horizontal tiles with directional separators', async () => {
  const result = await inSlide(fixture, () => {
    const steps = document.querySelector('.steps');
    return {
      display: getComputedStyle(steps).display,
      tiles: Array.from(steps.children, (tile) => ({
        y: tile.offsetTop, width: tile.offsetWidth,
        radius: getComputedStyle(tile).borderRadius,
        shadow: getComputedStyle(tile).boxShadow,
        separator: getComputedStyle(tile, '::after').content,
      })),
    };
  });
  assert.equal(result.display, 'grid');
  assert.equal(result.tiles.length, 3);
  assert.ok(result.tiles.every((tile) => tile.y === result.tiles[0].y));
  assert.ok(Math.max(...result.tiles.map((tile) => tile.width)) - Math.min(...result.tiles.map((tile) => tile.width)) <= 1);
  assert.deepEqual(result.tiles.map((tile) => tile.separator), ['""', '""', 'none']);
  for (const tile of result.tiles) {
    assert.equal(tile.radius, '0px');
    assert.equal(tile.shadow, 'none');
  }
});

test('navy surfaces keep all foreground text white, including rich table headers', async () => {
  const source = '---\ntheme: science-tokyo\n---\n# Readable surfaces\n\n'
    + '| **Header** | [Link](https://example.org) |\n|:--|:--|\n| Data | Value |\n\n'
    + '::: band\n### **Principle**\n[Link](https://example.org) and `code` and ==mark== and *emphasis* and muted{.muted}\n:::';
  const result = await inSlide(source, () => ({
    band: getComputedStyle(document.querySelector('.band')).backgroundColor,
    foreground: Array.from(document.querySelectorAll('.band, .band *, th, th *'), (node) => getComputedStyle(node).color),
    table: getComputedStyle(document.querySelector('table')).borderCollapse,
  }));
  assert.equal(result.band, 'rgb(28, 48, 119)');
  assert.ok(result.foreground.length >= 10);
  assert.ok(result.foreground.every((color) => color === 'rgb(255, 255, 255)'), JSON.stringify(result.foreground));
  assert.equal(result.table, 'collapse');
});

test('band tables contrast against effective row and cell backgrounds in Chrome', async (t) => {
  const source = [
    '---', 'theme: science-tokyo', '---', '# Nested table', '::: band',
    '| **Heading** | [Link](https://example.org) | State |', '|:--|:--|:--|',
    '| Odd row | `Code` | High{.status-high} |',
    '| Even row | ==Mark== | Mid{.status-mid} |',
    '| Last row | *Emphasis* | Low{.status-low} |', ':::',
  ].join('\n');
  const samples = await inSlide(source, computedTextContrast, '.band');
  assert.ok(samples.some(({ text }) => text === 'Odd row'));
  assert.ok(samples.some(({ text }) => text === 'Even row'));
  assert.equal(samples.filter(({ class: name }) => name.startsWith('status-')).length, 3);
  t.diagnostic(JSON.stringify({ samples: samples.length, minimumContrast: Math.min(...samples.map(({ contrast }) => contrast)) }));
  assertBandContrast(samples);
});

test('band note, info and warning text contrast against effective panel backgrounds in Chrome', async (t) => {
  const source = [
    '---', 'theme: science-tokyo', '---', '# Nested callouts', ':::: band',
    ...['note', 'info', 'warning'].flatMap((name) => [
      `::: ${name}`, `### ${name}`, '**Strong** and *emphasis* and [link](https://example.org) and `code` and ==mark== and muted{.muted}', ':::',
    ]), '::::',
  ].join('\n\n');
  const samples = await inSlide(source, computedTextContrast, '.band :is(.note, .info, .warning)');
  for (const name of ['note', 'info', 'warning']) assert.ok(samples.some(({ text }) => text === name));
  t.diagnostic(JSON.stringify({ samples: samples.length, minimumContrast: Math.min(...samples.map(({ contrast }) => contrast)) }));
  assertBandContrast(samples);
});

test('figure contains images without distortion or overflowing its body area', async () => {
  const bytes = readFileSync(new URL('assets/science-tokyo/logo-stacked.png', root));
  const aspect = bytes.readUInt32BE(16) / bytes.readUInt32BE(20);
  const image = bytes.toString('base64');
  const source = `---\ntheme: science-tokyo\n---\n# Figure\n\n::: figure\n![wide](data:image/png;base64,${image})\n:::`;
  const result = await inSlide(source, () => {
    const figure = document.querySelector('.figure');
    const image = figure.querySelector('img');
    return { fit: getComputedStyle(image).objectFit, width: image.width, height: image.height, areaHeight: figure.offsetHeight };
  });
  assert.equal(result.fit, 'contain');
  assert.ok(result.width <= 1160 && result.height <= 432, JSON.stringify(result));
  assert.ok(result.areaHeight <= 432);
  assert.ok(Math.abs(result.width / result.height - aspect) < 0.01, 'preserve the source aspect ratio');
});

test('semantic helpers work through markdown attributes and retain grayscale distinctions', async () => {
  const source = '---\ntheme: science-tokyo\n---\n# Helpers\n\n'
    + '**改善**{.positive} / **注意**{.negative} / **補足**{.muted}\n\n'
    + '| 高 | 中 | 低 |\n|:--|:--|:--|\n'
    + '| 高{.status-high} | 中{.status-mid} | 低{.status-low} |\n\n'
    + '**改行しない**{.no-wrap}';
  const result = await inSlide(source, () => ({
    colors: ['positive', 'negative', 'muted'].map((name) => getComputedStyle(document.querySelector(`.${name}`)).color),
    statuses: ['status-high', 'status-mid', 'status-low'].map((name) => {
      const css = getComputedStyle(document.querySelector(`.${name}`));
      return { background: css.backgroundColor, rule: css.borderBottomStyle };
    }),
    wrap: getComputedStyle(document.querySelector('.no-wrap')).whiteSpace,
  }));
  assert.deepEqual(result.colors, ['rgb(63, 125, 78)', 'rgb(210, 75, 70)', 'rgb(107, 114, 128)']);
  assert.equal(new Set(result.statuses.map((status) => status.background)).size, 3);
  assert.deepEqual(result.statuses.map((status) => status.rule), ['solid', 'dashed', 'dotted']);
  assert.equal(result.wrap, 'nowrap');
});

test('panels keep disciplined interior spacing and separation from adjacent blocks', async () => {
  const result = await inSlide(fixture, () => {
    const card = document.querySelector('.card');
    const columns = document.querySelector('.columns-3');
    const note = columns.nextElementSibling;
    return {
      inset: card.firstElementChild.getBoundingClientRect().top - card.getBoundingClientRect().top,
      gap: note.getBoundingClientRect().top - columns.getBoundingClientRect().bottom,
      followingGap: note.nextElementSibling.getBoundingClientRect().top - note.getBoundingClientRect().bottom,
    };
  });
  assert.ok(result.inset >= 16 && result.inset <= 24, JSON.stringify(result));
  assert.ok(result.gap >= 14, JSON.stringify(result));
  assert.ok(result.followingGap >= 14, JSON.stringify(result));
});

test('tables fill their available width, including inside navy-card bodies', async () => {
  const tables = await inSlide(fixture, () => Array.from(document.querySelectorAll('table'), (table) => ({
    display: getComputedStyle(table).display,
    width: table.getBoundingClientRect().width,
    row: table.querySelector('tr').getBoundingClientRect().width,
    inset: table.parentElement.classList.contains('navy-card')
      ? table.querySelector('tr').getBoundingClientRect().left - table.parentElement.getBoundingClientRect().left : null,
  })));
  assert.ok(tables.length >= 2);
  for (const table of tables) {
    assert.equal(table.display, 'table');
    assert.ok(table.row / table.width > 0.98, JSON.stringify(table));
    if (table.inset !== null) assert.ok(table.inset >= 18 && table.inset <= 24, JSON.stringify(table));
  }
});

test('layout-owned gaps replace panel margins, keeping matrix axes thin', async () => {
  const result = await inSlide(fixture, () => {
    const matrix = document.querySelector('.matrix');
    const cells = Array.from(matrix.children);
    const first = cells[0].getBoundingClientRect();
    const lower = cells[2].getBoundingClientRect();
    return {
      margins: Array.from(document.querySelectorAll('.grid-2 > *, .grid-3 > *, .compare > *, .matrix > *'), (node) => getComputedStyle(node).marginBottom),
      axis: lower.top - first.bottom,
      tail: matrix.getBoundingClientRect().bottom - cells.at(-1).getBoundingClientRect().bottom,
    };
  });
  assert.ok(result.margins.every((margin) => margin === '0px'), JSON.stringify(result));
  assert.ok(result.axis >= 1 && result.axis <= 3, JSON.stringify(result));
  assert.ok(result.tail >= 1 && result.tail <= 3, JSON.stringify(result));
});

test('navy foreground inheritance survives nested components and helper classes', async () => {
  const source = [
    '---', 'theme: science-tokyo', '---', '# Nested foreground',
    ':::: band', '::: metric', '## Number', '**Label**{.negative}', ':::',
    '| State |\n|:--|\n| High{.status-high} |', '::::',
    '::: navy-card', '### Header <span class="muted">detail</span>', 'Body', ':::',
  ].join('\n\n');
  const colors = await inSlide(source, () => Array.from(document.querySelectorAll(
    '.band, .band *, .navy-card > :first-child, .navy-card > :first-child *',
  ), (node) => ({ tag: node.tagName, color: getComputedStyle(node).color })));
  assert.ok(colors.length >= 10);
  assert.ok(colors.every(({ color }) => color === 'rgb(255, 255, 255)'), JSON.stringify(colors));
});

test('cover uses available title width instead of orphaning the last glyph', async () => {
  const result = await inSlide(readFileSync(new URL('slides/science-tokyo-template.md', root), 'utf8'), () => {
    const heading = document.querySelector('section.title h1');
    const css = getComputedStyle(heading);
    return { height: heading.offsetHeight, line: parseFloat(css.lineHeight), font: css.fontSize };
  });
  assert.equal(result.font, '56px');
  assert.ok(result.height <= result.line + 1, JSON.stringify(result));
});

test('embedded official assets are unchanged', () => {
  assert.equal(hash(theme.split('ASSET DATA')[1]), 'bf23be1fd21fe60206e51aa6de2d026afaf23edd1b420f1859903ab2993e72fb');
});

test('unrelated code and swatch corner treatments are not blanket-zeroed', async () => {
  const source = '---\ntheme: science-tokyo\n---\n# Legacy details\n\n`inline`\n\n```text\nblock\n```\n\n**■**{.swatch .bg-navy}';
  const radii = await inSlide(source, () => [
    getComputedStyle(document.querySelector('p > code')).borderRadius,
    getComputedStyle(document.querySelector('pre, marp-pre')).borderRadius,
    getComputedStyle(document.querySelector('.swatch')).borderRadius,
  ]);
  assert.deepEqual(radii, ['4px', '8px', '6px']);
});

test('all concise component fixtures remain in the slide body and clear of the footer', async () => {
  const report = await inSlide(fixture, () => Array.from(document.querySelectorAll('section'), (section) => {
    const slide = section.getBoundingClientRect();
    return Array.from(section.children).filter((node) => !['H1', 'FOOTER', 'HEADER', 'SCRIPT'].includes(node.tagName)).map((node) => {
      const box = node.getBoundingClientRect();
      return { slide: section.id, class: node.className, top: box.top - slide.top, bottom: box.bottom - slide.top, left: box.left - slide.left, right: box.right - slide.left };
    });
  }));
  assert.equal(report.length, 8);
  for (const block of report.flat()) {
    assert.ok(block.top >= 165 && block.bottom <= 640, JSON.stringify(block));
    assert.ok(block.left >= 58 && block.right <= 1222, JSON.stringify(block));
  }
});

test('highlighted navy-card headings preserve light marks and contrasting rich text in Chrome', async (t) => {
  const source = [
    '---', 'theme: science-tokyo', '---', '# Highlighted heading', '::: navy-card',
    '### ==Important== / ==Rich **Strong** *emphasis* [link](https://example.org)== / **White** [Unmarked link](https://example.org) and `code` and <span class="muted">detail</span>',
    'Body', ':::',
  ].join('\n\n');
  const samples = await inSlide(source, computedTextContrast, '.navy-card > :first-child');
  const marks = samples.filter(({ element }) => element === 'mark');
  assert.equal(marks.length, 2, 'existing ==mark== syntax retains semantic mark elements');
  for (const sample of marks) assert.deepEqual(sample.background, [255, 240, 168], 'preserve the light highlight background');
  t.diagnostic(JSON.stringify({ markedText: marks.map(({ text, color, background, contrast }) => ({ text, color, background, contrast })) }));
  assert.deepEqual(samples.filter(({ contrast }) => contrast < 4.5), [], 'each rich-text run must contrast with its own effective background');
  for (const text of ['Important', 'Strong', 'emphasis', 'link']) {
    assert.equal(samples.find((sample) => sample.text === text)?.color, 'rgb(26, 26, 26)', text);
  }
  for (const text of ['White', 'Unmarked link', 'code', 'detail']) {
    assert.equal(samples.find((sample) => sample.text === text)?.color, 'rgb(255, 255, 255)', text);
  }
});

test('navy-card pads every body child and keeps rich header text readable', async () => {
  const result = await inSlide(fixture, () => {
    const card = document.querySelector('.navy-card');
    return {
      body: Array.from(document.querySelectorAll('.navy-card')).flatMap((panel) => Array.from(panel.children).slice(1)).map((node) => {
        const css = getComputedStyle(node);
        return { tag: node.tagName, left: parseFloat(css.paddingLeft), right: parseFloat(css.paddingRight) };
      }),
      header: Array.from(card.firstElementChild.querySelectorAll('strong, a'),
        (node) => getComputedStyle(node).color),
    };
  });
  assert.ok(result.body.length >= 5, 'multi-paragraph, list, table, nested-panel fixture');
  for (const child of result.body) {
    assert.ok(child.left >= 16 && child.right >= 16, `${child.tag} needs padding on both sides: ${JSON.stringify(child)}`);
  }
  assert.deepEqual(result.header, ['rgb(255, 255, 255)', 'rgb(255, 255, 255)']);
});

test('cards and related rectangular panels have square corners and no shadows', async () => {
  const panels = await inSlide(fixture, () => Array.from(document.querySelectorAll(
    '.card, .box, .navy-card, .callout, .note, .info, .warning',
  ), (node) => {
    const css = getComputedStyle(node);
    return { name: node.className, radius: css.borderRadius, shadow: css.boxShadow };
  }));
  assert.ok(panels.length >= 7, 'real Marp fixture renders the existing component family');
  for (const panel of panels) {
    assert.equal(panel.radius, '0px', `${panel.name} must be square`);
    assert.equal(panel.shadow, 'none', `${panel.name} must not cast a shadow`);
  }
});
