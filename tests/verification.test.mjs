import test from 'node:test';
import assert from 'node:assert/strict';
import { existsSync } from 'node:fs';
import { link, mkdir, mkdtemp, readFile, readdir, rm, symlink, writeFile } from 'node:fs/promises';
import { createHash } from 'node:crypto';
import { createServer } from 'node:http';
import { spawnSync } from 'node:child_process';
import path from 'node:path';
import { pathToFileURL } from 'node:url';
import { Marp } from '@marp-team/marp-core';
import configure from '../engine.mjs';
const modulePath = new URL('../scripts/verify-science-tokyo.mjs', import.meta.url);
const fixtureRoot = new URL('../.verification/node-html-regressions/', import.meta.url);
const fixtureStyle = `<style>html,body{margin:0}section{position:relative;width:1280px;height:720px;background:white;overflow:hidden}h1{position:absolute;left:60px;top:20px;font:40px sans-serif;margin:0}p{margin:0;font:28px sans-serif}</style>`;

async function fixture(t, content = '<h1>Clean control</h1>') {
  await mkdir(fixtureRoot, { recursive: true });
  const directory = await mkdtemp(path.join(fixtureRoot.pathname, 'run-'));
  t.after(() => rm(directory, { recursive: true, force: true }));
  const html = path.join(directory, 'input.html');
  const output = path.join(directory, 'audit');
  await writeFile(html, `<!doctype html>${fixtureStyle}<section>${content}</section>`);
  return { directory, html, output, expected: 1 };
}

// Render the installed core/KaTeX and real legacy theme, never ignored build output.
async function katexFixture(t, extraStyle = '', transform = html => html) {
  const input = await fixture(t);
  const marp = configure({ marp: new Marp({ html: true }) });
  marp.themeSet.add(await readFile(new URL('../style.css', import.meta.url), 'utf8'));
  const { html, css } = marp.render(String.raw`---
theme: kyomu
math: katex
---
# KaTeX visual layers

Inline $x$.

$$
y = \frac{x + 1}{2}
$$
`);
  assert.match(html, /class="katex-mathml"><math/, 'must exercise installed KaTeX MathML output');
  assert.match(html, /class="katex-html" aria-hidden="true"/, 'visible HTML is intentionally aria-hidden');
  await writeFile(input.html, `<!doctype html><style>${css}\n${extraStyle}</style>${transform(html)}`);
  return input;
}

test('real installed Marp KaTeX audits the human layer without false-clipping accessibility duplicates', async t => {
  const { verifyHtml } = await import(modulePath);
  const report = await verifyHtml(await katexFixture(t));
  assert.equal(report.issues, 0, 'standard clipped KaTeX MathML is an accessibility duplicate, not lost visible text');
  assert.equal(report.passed, true);
  assert.equal(report.slides[0].text.filter(item => item.label === 'x').length, 2, 'both inline/display HTML glyphs remain measured despite aria-hidden=true');
  assert.equal(report.slides[0].text.filter(item => item.label === 'y').length, 1);
});

test('real installed Marp KaTeX still rejects clipped visible HTML formula glyphs', async t => {
  const { verifyHtml } = await import(modulePath);
  const input = await katexFixture(t, '.katex .katex-html{display:inline-block;width:1px;overflow:hidden}');
  const report = await verifyHtml(input);
  assert.equal(report.passed, false);
  assert.ok(report.slides[0].issues.some(issue => issue.code === 'text-outside-container' && issue.label === 'x'));
  assert.equal(report.slides[0].text.filter(item => item.label === 'x').length, 2, 'clipped aria-hidden HTML must still be measured');
});

test('real installed Marp KaTeX requires a visible paired HTML representation', async t => {
  const { verifyHtml } = await import(modulePath);
  for (const mode of ['unpaired', 'display:none', 'visibility:hidden', 'opacity:0']) {
    await t.test(mode, async t => {
      const input = await katexFixture(t,
        mode === 'unpaired' ? '' : `.katex .katex-html{${mode}}`,
        html => mode === 'unpaired' ? html.replaceAll('class="katex-html"', 'class="unpaired-human"') : html);
      const report = await verifyHtml(input);
      assert.equal(report.passed, false, 'hidden MathML alone must not silently pass');
      assert.ok(report.slides[0].issues.some(issue => issue.code === 'text-outside-container' && issue.label === 'x'));
    });
  }
});

test('real installed Marp KaTeX retains nonhidden MathML glyph measurements', async t => {
  const { verifyHtml } = await import(modulePath);
  const input = await katexFixture(t, '.katex .katex-mathml{position:static!important;clip:auto!important;width:auto!important;height:auto!important;overflow:visible!important}');
  const report = await verifyHtml(input);
  assert.equal(report.passed, true, 'unclipped MathML alongside HTML is legitimate visible content');
  assert.equal(report.slides[0].text.filter(item => item.label === 'x').length, 4, 'measure both visible MathML and HTML, inline and display');
  assert.equal(report.slides[0].text.filter(item => item.label === 'y').length, 2);
});

test('real Chromium rejects wholly clipped text inside a plain ancestor and accepts clean flow', async t => {
  const { verifyHtml } = await import(modulePath);
  const clipped = await fixture(t, '<h1>Clipping regression</h1><div style="position:absolute;left:60px;top:180px;width:360px;height:20px;overflow:hidden"><p style="position:relative;top:70px">THIS TEXT IS COMPLETELY CLIPPED</p></div>');
  const report = await verifyHtml(clipped);
  assert.ok(report.slides[0].text.some(item => item.label.startsWith('THIS TEXT') && item.rect.top >= 250), 'must extract actual off-clip Range line boxes');
  assert.equal(report.passed, false);
  assert.ok(report.errors.length > 0);
  assert.equal(report.checked, 1);
  assert.ok(report.slides[0].issues.some(issue => issue.code === 'text-outside-container' && issue.label.startsWith('THIS TEXT')), 'plain overflow ancestor must be audited');
  const control = await fixture(t, '<h1>Clean control</h1><div style="position:absolute;left:60px;top:180px;width:500px"><p style="line-height:18px">Legitimate <span>inline and flowing</span> text</p></div>');
  assert.equal((await verifyHtml(control)).issues, 0);
});

test('real Chromium audits every clipping mode and outer ancestor without treating flow or inline bounds as clips', async t => {
  const { verifyHtml } = await import(modulePath);
  for (const overflow of ['hidden', 'clip', 'auto', 'scroll']) {
    await t.test(overflow, async t => {
      const input = await fixture(t, `<div id="outer" style="position:absolute;left:60px;top:180px;width:500px;height:20px;overflow:${overflow}"><div class="card" style="height:180px"><p style="position:relative;top:70px">Outer clip regression</p></div></div>`);
      const report = await verifyHtml(input);
      assert.ok(report.slides[0].issues.some(issue => issue.code === 'text-outside-container' && issue.boundary === 'div#outer'));
    });
  }
  for (const [axes, position] of [['overflow-x:clip;overflow-y:visible', 'top:70px'], ['overflow-x:visible;overflow-y:clip', 'left:350px']]) {
    await t.test(axes, async t => {
      const input = await fixture(t, `<div style="position:absolute;left:60px;top:180px;width:300px;height:60px;${axes}"><p style="position:relative;${position}"><span style="overflow:hidden;width:1px;height:1px">Visible axis text</span></p></div>`);
      assert.equal((await verifyHtml(input)).issues, 0, 'overflow on a visible axis or non-replaced inline must not be flagged');
    });
  }
});

test('real Chromium measures transformed clipping in ancestor local coordinates', async t => {
  const { verifyHtml } = await import(modulePath);
  for (const transform of ['scale(2)', 'rotate(35deg)', 'skewX(25deg)', 'scale(-1, 1)']) {
    await t.test(transform, async t => {
      const style = `position:absolute;left:450px;top:230px;width:200px;height:60px;border:8px solid black;padding:10px;overflow:hidden;transform:${transform};transform-origin:0 0`;
      const clean = await fixture(t, `<div style="${style}"><p>Clean text</p></div>`);
      assert.equal((await verifyHtml(clean)).issues, 0, 'transformed clean text stays within the padding clip');
      const clipped = await fixture(t, `<div id="transformed" style="${style}"><p style="position:relative;top:110px">Hidden</p></div>`);
      assert.ok((await verifyHtml(clipped)).slides[0].issues.some(issue => issue.boundary === 'div#transformed'), 'transformed ancestor still clips text');
    });
  }
});

test('real Chromium audits SVG viewBox half-scale clipping in local coordinates', async t => {
  const { verifyHtml } = await import(modulePath);
  const input = await fixture(t);
  const wrap = text => `<!doctype html>${fixtureStyle}<svg xmlns="http://www.w3.org/2000/svg" width="640" height="360" viewBox="0 0 1280 720"><foreignObject width="1280" height="720"><section xmlns="http://www.w3.org/1999/xhtml"><div id="svgclip" style="position:absolute;left:60px;top:180px;width:500px;height:60px;overflow:hidden"><p style="position:relative;top:70px">${text}</p></div></section></foreignObject></svg>`;
  await writeFile(input.html, wrap('SVG clipped text'));
  const report = await verifyHtml(input);
  await writeFile(input.html, wrap(''));
  const blank = await verifyHtml({ ...input, output: path.join(input.directory, 'blank') });
  assert.deepEqual(await readFile(report.slides[0].screenshot), await readFile(blank.slides[0].screenshot), 'real SVG screenshot confirms this text is entirely clipped');
  assert.equal(report.passed, false, 'half-scale SVG must not hide clipped text from the audit');
  assert.ok(report.slides[0].issues.some(issue => issue.boundary === 'div#svgclip'));
});

test('real Chromium accepts clean text inside a double-scale SVG viewBox', async t => {
  const { verifyHtml } = await import(modulePath);
  const input = await fixture(t);
  await writeFile(input.html, `<!doctype html>${fixtureStyle}<svg xmlns="http://www.w3.org/2000/svg" width="2560" height="1440" viewBox="0 0 1280 720"><foreignObject width="1280" height="720"><section xmlns="http://www.w3.org/1999/xhtml"><div id="svgclip" style="position:absolute;left:60px;top:180px;width:500px;height:60px;overflow:hidden"><p>VISIBLE OR CLIPPED</p></div></section></foreignObject></svg>`);
  const report = await verifyHtml(input);
  assert.equal(report.issues, 0, 'viewport Range coordinates must not be compared with unscaled clip dimensions');
  assert.equal(report.passed, true);
  assert.ok(report.slides[0].text.some(item => item.label === 'VISIBLE OR CLIPPED'));
});

test('real Chromium respects escaping absolute positioning', async t => {
  const { verifyHtml } = await import(modulePath);
  const escaped = await fixture(t, '<div style="margin:180px 0 0 60px;width:300px;height:20px;overflow:hidden"><p style="position:absolute;left:60px;top:250px">Visible escaped text</p></div>');
  const escapedReport = await verifyHtml(escaped);
  assert.equal(escapedReport.issues, 0, 'an ancestor between absolute text and its containing block does not clip it');
  const blank = await fixture(t, '<div style="margin:180px 0 0 60px;width:300px;height:20px;overflow:hidden"></div>');
  const blankReport = await verifyHtml(blank);
  assert.notDeepEqual(await readFile(escapedReport.slides[0].screenshot), await readFile(blankReport.slides[0].screenshot), 'Chrome must actually paint the escaped text');
});

test('real Chromium respects the overflow clip margin', async t => {
  const { verifyHtml } = await import(modulePath);
  const margin = await fixture(t, '<div style="position:absolute;left:60px;top:180px;width:300px;height:20px;overflow:clip;overflow-clip-margin:80px"><p style="position:relative;top:30px">Visible clip margin</p></div>');
  assert.equal((await verifyHtml(margin)).issues, 0, 'clip margin expands the actual clip edge');
});

test('input/output alias rejection precedes all mutation and preserves source bytes', async t => {
  const { verifyHtml } = await import(modulePath);
  for (const target of ['html-report', 'catalog-report', 'symlink-report', 'symlink-page', 'hardlink-page', 'symlink-directory']) {
    await t.test(target, async t => {
      const input = await fixture(t);
      await mkdir(input.output);
      const reportPath = path.join(input.output, 'layout-report.json');
      if (target === 'html-report') {
        await writeFile(reportPath, await readFile(input.html));
        input.html = reportPath;
      } else if (target === 'catalog-report') {
        await writeFile(reportPath, JSON.stringify({ patterns: [{ key: 'test', id: 'test' }] }));
        input.catalog = reportPath;
      } else if (target === 'symlink-report') {
        await symlink(input.html, reportPath);
      } else {
        const pages = path.join(input.output, 'html');
        if (target === 'symlink-directory') {
          const source = path.join(input.directory, 'page-001.png');
          await writeFile(source, await readFile(input.html));
          input.html = source;
          await symlink(input.directory, pages);
        } else {
          await mkdir(pages);
          await (target === 'hardlink-page' ? link : symlink)(input.html, path.join(pages, 'page-001.png'));
        }
      }
      const source = input.catalog ?? input.html;
      const before = await readFile(source);
      const entries = await readdir(input.output);
      let error;
      try { await verifyHtml(input); } catch (e) { error = e; }
      assert.deepEqual(await readFile(source), before, 'must not overwrite or delete a protected input alias');
      assert.deepEqual(await readdir(input.output), entries, 'reject before even creating screenshot directories or receipts');
      assert.match(String(error), /alias|protect/i, 'must reject with a clear protected-alias error');
    });
  }
});

test('a successful real-browser run followed by CLI read failure removes stale owned evidence', async t => {
  const { verifyHtml } = await import(modulePath);
  const input = await fixture(t);
  const prior = await verifyHtml(input);
  const page = prior.slides[0].screenshot;
  const extra = path.join(input.output, 'html', 'page-999.png');
  await writeFile(extra, await readFile(page));
  const keep = path.join(input.output, 'html', 'keep.png');
  await writeFile(keep, 'unowned sentinel');
  const result = spawnSync(process.execPath, [modulePath.pathname, '--html', path.join(input.directory, 'missing.html'), '--output', input.output, '--expected', '1'], { encoding: 'utf8', timeout: 90000 });
  assert.equal(result.status, 1, result.stderr);
  assert.equal(existsSync(page), false, 'prior page-001 must be invalidated before reading the new input');
  assert.equal(existsSync(extra), false, 'old extra owned page must not survive');
  assert.equal(await readFile(keep, 'utf8'), 'unowned sentinel');
  const failed = JSON.parse(await readFile(path.join(input.output, 'layout-report.json'), 'utf8'));
  assert.equal(failed.schema_version, 2);
  assert.deepEqual(failed.inputs, { html: { path: path.join(input.directory, 'missing.html'), sha256: null }, catalog: null });
  assert.equal(failed.passed, false);
  assert.equal(failed.checked, 0);
  assert.equal(failed.issues, 0);
  assert.deepEqual(failed.slides, []);
  assert.deepEqual(failed.screenshots, []);
  assert.ok(failed.errors.some(error => /missing\.html|ENOENT/.test(error)));
});

test('real-browser count and partial screenshot failures publish current failure and close Chrome', async t => {
  const { verifyHtml } = await import(modulePath);
  const { default: puppeteer } = await import('puppeteer-core');
  for (const stage of ['count', 'screenshot']) {
    await t.test(stage, async t => {
      const input = await fixture(t);
      const prior = await verifyHtml(input);
      let browser;
      const launch = puppeteer.launch.bind(puppeteer);
      t.mock.method(puppeteer, 'launch', async options => { browser = await launch(options); return browser; });
      input.expected = 2;
      if (stage === 'screenshot') await writeFile(input.html, `<!doctype html>${fixtureStyle}<section><h1>First real screenshot</h1></section><section style="display:none"><p>Cannot capture this section</p></section>`);
      await assert.rejects(verifyHtml(input), stage === 'count' ? /Expected 2 slides, found 1/ : /screenshot|width|height|visible/i);
      assert.equal(browser.connected, false, 'real browser must close even on an audit/capture exception');
      assert.notEqual(browser.process().exitCode, null, 'Chrome process must have exited');
      assert.equal(existsSync(prior.slides[0].screenshot), false, 'stale or partial PNG must not survive');
      const failed = JSON.parse(await readFile(path.join(input.output, 'layout-report.json'), 'utf8'));
      assert.equal(failed.passed, false);
      assert.equal(failed.checked, stage === 'count' ? 1 : 2, 'retain the number of actually measured/audited sections');
      assert.equal(failed.issues, 0);
      assert.deepEqual(failed.screenshots, [], 'partial captures are not usable receipt evidence');
      assert.ok(failed.errors.length > 0);
      assert.ok(failed.slides.every(slide => slide.screenshot === null));
    });
  }
});

test('catalog and Chrome launch failures replace a prior successful receipt', async t => {
  const { verifyHtml } = await import(modulePath);
  for (const stage of ['catalog', 'browser']) {
    await t.test(stage, async t => {
      const input = await fixture(t);
      const prior = await verifyHtml(input);
      if (stage === 'catalog') {
        input.catalog = path.join(input.directory, 'invalid.json');
        await writeFile(input.catalog, '{invalid json');
      } else {
        const previous = process.env.CHROME_PATH;
        process.env.CHROME_PATH = path.join(input.directory, 'missing-chrome');
        t.after(() => { if (previous === undefined) delete process.env.CHROME_PATH; else process.env.CHROME_PATH = previous; });
      }
      await assert.rejects(verifyHtml(input));
      assert.equal(existsSync(prior.slides[0].screenshot), false);
      const failed = JSON.parse(await readFile(path.join(input.output, 'layout-report.json'), 'utf8'));
      assert.equal(failed.passed, false);
      assert.equal(failed.checked, 0);
      assert.deepEqual(failed.screenshots, []);
      assert.ok(failed.errors.length > 0);
    });
  }
});

const sha256 = bytes => createHash('sha256').update(bytes).digest('hex');

test('version 2 receipts bind real input and captured PNG bytes and round-trip through JSON', async t => {
  const { verifyHtml } = await import(modulePath);
  const input = await fixture(t, '<h1>実際の入力 bytes</h1>');
  input.catalog = path.join(input.directory, 'catalog.json');
  input.expected = undefined;
  await writeFile(input.catalog, '{\n  "patterns": [ { "key": "test-key", "id": "test-id" } ]\n}\n');
  const report = await verifyHtml(input);
  assert.equal(report.schema_version, 2);
  assert.equal(report.passed, true);
  assert.equal(report.html, path.resolve(input.html));
  assert.equal(report.expected, 1);
  assert.equal(report.checked, 1);
  assert.equal(report.issues, 0);
  assert.deepEqual(report.errors, []);
  assert.deepEqual(report.inputs, {
    html: { path: path.resolve(input.html), sha256: sha256(await readFile(input.html)) },
    catalog: { path: path.resolve(input.catalog), sha256: sha256(await readFile(input.catalog)) },
  });
  assert.equal(report.slides[0].key, 'test-key');
  assert.equal(report.slides[0].id, 'test-id');
  const png = await readFile(report.slides[0].screenshot);
  assert.equal(png.subarray(0, 8).toString('hex'), '89504e470d0a1a0a', 'must hash a real captured PNG');
  assert.deepEqual(report.screenshots, [{ page: 1, path: path.resolve(report.slides[0].screenshot), sha256: sha256(png) }]);
  assert.deepEqual(JSON.parse(JSON.stringify(report)), JSON.parse(await readFile(path.join(input.output, 'layout-report.json'), 'utf8')));

  const baseline = await fixture(t);
  const result = spawnSync(process.execPath, [modulePath.pathname, '--html', baseline.html, '--output', baseline.output, '--expected', '1'], { encoding: 'utf8', timeout: 90000 });
  assert.equal(result.status, 0, result.stderr);
  const baselineReport = JSON.parse(await readFile(path.join(baseline.output, 'layout-report.json'), 'utf8'));
  assert.equal(baselineReport.schema_version, 2);
  assert.equal(baselineReport.inputs.catalog, null, 'explicit expected-count CLI mode requires no catalog');
  assert.equal(baselineReport.inputs.html.sha256, sha256(await readFile(baseline.html)));
  assert.equal(baselineReport.passed, true);
});

test('real-browser HTML replacement and restoration consumes only hash-bound captured bytes with relative file assets', async t => {
  const { verifyHtml } = await import(modulePath);
  const { default: puppeteer } = await import('puppeteer-core');
  const input = await fixture(t);
  const assets = path.join(input.directory, 'assets');
  await mkdir(assets);
  await writeFile(path.join(assets, 'relative.css'), 'h1{color:rgb(19, 51, 83)}');
  await writeFile(path.join(assets, 'relative.svg'), '<svg xmlns="http://www.w3.org/2000/svg" width="120" height="60"><rect width="120" height="60" fill="#135383"/></svg>');
  await writeFile(path.join(assets, 'relative.js'), 'window.relativeAssetLoaded = true;');
  await writeFile(input.html, `<!doctype html><base href="./assets/">${fixtureStyle}<link rel="stylesheet" href="relative.css"><section><h1>Original captured HTML</h1><img src="relative.svg" style="position:absolute;left:60px;top:180px;width:120px;height:60px"></section><script src="relative.js"></script>`);
  input.catalog = path.join(input.directory, 'catalog.json');
  input.expected = undefined;
  await writeFile(input.catalog, '{"patterns":[{"key":"original","id":"original"}]}');
  const original = await readFile(input.html);
  const control = await verifyHtml({ ...input, output: path.join(input.directory, 'control') });
  assert.equal(control.passed, true);
  const launch = puppeteer.launch.bind(puppeteer);
  let browser, observed;
  t.mock.method(puppeteer, 'launch', async options => {
    // Parent's real launch/close hook: replace after the initial read, restore
    // before the final read. Endpoint hashes alone cannot detect this ABA.
    await writeFile(input.html, original.toString().replace('Original captured HTML', 'DIFFERENT ACTUALLY RENDERED HTML'));
    browser = await launch(options);
    const close = browser.close.bind(browser);
    browser.close = async () => {
      try {
        const pages = await browser.pages();
        observed = await pages[pages.length - 1].evaluate(() => ({
          url: location.href, base: document.baseURI,
          css: getComputedStyle(document.querySelector('h1')).color,
          script: window.relativeAssetLoaded,
          image: document.querySelector('img').naturalWidth,
        }));
      } finally {
        try { await close(); } finally { await writeFile(input.html, original); }
      }
    };
    return browser;
  });
  let report;
  try { report = await verifyHtml(input); }
  finally { await writeFile(input.html, original); }
  assert.equal(browser.connected, false);
  assert.deepEqual(await readFile(input.html), original);
  assert.equal(report.passed, true);
  assert.equal(report.slides[0].title, 'Original captured HTML', 'must audit the bytes whose hash was captured, never the temporary replacement');
  assert.equal(report.inputs.html.path, path.resolve(input.html));
  assert.equal(report.inputs.html.sha256, sha256(original));
  assert.equal(report.slides[0].key, 'original');
  assert.deepEqual(await readFile(report.slides[0].screenshot), await readFile(control.slides[0].screenshot), 'captured original bytes must produce the original control PNG');
  assert.deepEqual(observed, {
    url: pathToFileURL(input.html).href, base: pathToFileURL(assets + path.sep).href,
    css: 'rgb(19, 51, 83)', script: true, image: 120,
  }, 'retain the original file URL, explicit relative base, CSS, JS and image loading');
});

test('real-browser captured HTML response errors fail closed without unhandled interception rejections', async t => {
  const { verifyHtml } = await import(modulePath);
  const { default: puppeteer } = await import('puppeteer-core');
  const input = await fixture(t);
  const prior = await verifyHtml(input);
  const launch = puppeteer.launch.bind(puppeteer);
  let browser, attempted = false;
  t.mock.method(puppeteer, 'launch', async options => {
    browser = await launch(options);
    const newPage = browser.newPage.bind(browser);
    browser.newPage = async () => {
      const page = await newPage();
      page.on('request', request => {
        if (request.isNavigationRequest() && request.frame() === page.mainFrame()) {
          t.mock.method(request, 'respond', async () => {
            attempted = true;
            throw new Error('Injected captured HTML response failure');
          });
        }
      });
      return page;
    };
    return browser;
  });
  await assert.rejects(verifyHtml(input), /Injected captured HTML response failure|ERR_FAILED/);
  assert.equal(attempted, true, 'inject at the real main-document HTTPRequest response boundary');
  assert.equal(browser.connected, false);
  assert.equal(existsSync(prior.slides[0].screenshot), false);
  const report = JSON.parse(await readFile(path.join(input.output, 'layout-report.json'), 'utf8'));
  assert.equal(report.passed, false);
  assert.deepEqual(report.screenshots, []);
  assert.ok(report.errors.some(message => message.includes('Injected captured HTML response failure')));
});

test('real-browser source mutation cannot publish a hash-bound pass', async t => {
  const { verifyHtml } = await import(modulePath);
  for (const changed of ['html', 'catalog']) {
    await t.test(changed, async t => {
      const input = await fixture(t);
      input.catalog = path.join(input.directory, 'catalog.json');
      await writeFile(input.catalog, '{"patterns":[{"key":"before","id":"before"}]}');
      let mutated = false;
      const server = createServer(async (_request, response) => {
        await writeFile(input[changed], changed === 'html' ? '<section>changed source</section>' : '{"patterns":[{"key":"after","id":"after"}]}');
        mutated = true;
        response.writeHead(200, { 'Access-Control-Allow-Origin': '*' });
        response.end('changed');
      });
      await new Promise(resolve => server.listen(0, '127.0.0.1', resolve));
      t.after(() => new Promise(resolve => server.close(resolve)));
      await writeFile(input.html, `<!doctype html>${fixtureStyle}<section><h1>Original rendered source</h1></section><script>fetch('http://127.0.0.1:${server.address().port}/mutate')</script>`);
      const original = sha256(await readFile(input[changed]));
      let error;
      try { await verifyHtml(input); } catch (e) { error = e; }
      assert.equal(mutated, true, 'the real file-origin Chrome page must trigger the actual source write');
      assert.match(String(error), /changed|modified/i, 'source changes during capture must fail the current run');
      const report = JSON.parse(await readFile(path.join(input.output, 'layout-report.json'), 'utf8'));
      assert.equal(report.passed, false);
      assert.equal(report.inputs[changed].sha256, original, 'receipt records the bytes originally read, not a later replacement');
      assert.ok(report.errors.some(message => /changed|modified/i.test(message)));
      assert.deepEqual(report.screenshots, []);
      assert.equal(existsSync(path.join(input.output, 'html', 'page-001.png')), false);
    });
  }
});

test('layout audit detects text outside its measured slide bounds', async () => {
  assert.ok(existsSync(modulePath), 'layout audit module must exist');
  const { auditSlide } = await import(modulePath);
  const issues = auditSlide({number: 1, title: 'overflow fixture', width: 1280, height: 720,
    text: [{label: 'clipped', rect: {left: 60, top: 690, right: 400, bottom: 735}}],
    cards: [], images: [], collisions: []});
  assert.ok(issues.some(x => x.code === 'text-outside-slide' && x.label === 'clipped'));
});

test('layout audit rejects unsafe card surfaces, failed assets, clipping and collisions', async () => {
  const { auditSlide } = await import(modulePath);
  const issues = auditSlide({number: 2, title: 'hazards fixture', width: 1280, height: 720,
    text: [{label: 'hidden body', rect: {left: 80, top: 100, right: 420, bottom: 220},
      container: {left: 60, top: 80, right: 400, bottom: 200}}],
    cards: [{label: 'rounded', radius: '6px', shadow: 'none'}, {label: 'shadow', radius: '0px', shadow: 'rgb(0,0,0) 0px 2px 4px'}],
    images: [{label: 'missing', loaded: false, rect: {left:60,top:180,right:500,bottom:380}}],
    collisions: [{label: 'body / footer'}]});
  for (const code of ['text-outside-container', 'rounded-card', 'card-shadow', 'broken-image', 'overlapping-blocks']) {
    assert.ok(issues.some(x => x.code === code), `must detect ${code}`);
  }
});

test('clean measured slide passes without ignoring any supplied records', async () => {
  const { auditSlide } = await import(modulePath);
  assert.deepEqual(auditSlide({number: 1, title: 'clean', width: 1280, height: 720,
    text: [{label: 'body', rect: {left:80,top:190,right:350,bottom:240}, container: {left:60,top:170,right:400,bottom:300}}],
    cards: [{label:'card',radius:'0px',shadow:'none'}], images:[{label:'diagram',loaded:true,rect:{left:60,top:310,right:1220,bottom:620}}], collisions: []}), []);
});
