import { mkdir, readFile, readdir, realpath, rm, stat, writeFile } from 'node:fs/promises';
import { createHash } from 'node:crypto';
import path from 'node:path';
import { pathToFileURL } from 'node:url';
import { parseArgs } from 'node:util';
import puppeteer from 'puppeteer-core';

function outside(r, box, tolerance = 2) {
  return r.left < box.left - tolerance || r.top < box.top - tolerance
    || r.right > box.right + tolerance || r.bottom > box.bottom + tolerance;
}

/** Audit real browser measurements; inputs deliberately remain serializable. */
export function auditSlide(slide) {
  const issues = [];
  const bounds = { left: 0, top: 0, right: slide.width, bottom: slide.height };
  for (const item of slide.text) {
    if (outside(item.rect, bounds)) issues.push({ code: 'text-outside-slide', label: item.label });
    if (item.container && outside(item.rect, item.container)) issues.push({ code: 'text-outside-container', label: item.label });
    for (const clip of item.clips ?? []) {
      const r = clip.textRect ?? item.rect;
      if ((clip.x && (r.left < clip.rect.left - 2 || r.right > clip.rect.right + 2))
        || (clip.y && (r.top < clip.rect.top - 2 || r.bottom > clip.rect.bottom + 2))) {
        issues.push({ code: 'text-outside-container', label: item.label, boundary: clip.label });
      }
    }
  }
  for (const card of slide.cards) {
    if (card.radius.split(/[\s/]+/).some(x => parseFloat(x) > 0)) issues.push({ code: 'rounded-card', label: card.label });
    if (card.shadow !== 'none') issues.push({ code: 'card-shadow', label: card.label });
  }
  for (const image of slide.images) {
    if (!image.loaded) issues.push({ code: 'broken-image', label: image.label });
    if (outside(image.rect, bounds)) issues.push({ code: 'image-outside-slide', label: image.label });
  }
  for (const collision of slide.collisions) issues.push({ code: 'overlapping-blocks', label: collision.label });
  return issues;
}

/** Runs inside Chromium: inspect text line boxes, not just parent scrollHeight. */
function measureDocument() {
  const cardSelector = '.card,.navy-card,.box,.callout,.note,.info,.warning,.band,.foundation,.step';
  const isKatexAccessibilityDuplicate = element => {
    const mathml = element.closest('.katex > .katex-mathml');
    if (!mathml) return false;
    const visual = mathml.parentElement.querySelector(':scope > .katex-html');
    // KaTeX marks the painted HTML aria-hidden, not the screen-reader MathML.
    // Only select that visual layer for the standard, zero-area clipped pair.
    if (!visual?.textContent.trim()
      || !visual.checkVisibility({ checkOpacity: true, checkVisibilityCSS: true })
      || ![...visual.getClientRects()].some(r => r.width > 0 && r.height > 0)) return false;
    const style = getComputedStyle(mathml);
    return style.position === 'absolute' && style.clip === 'rect(1px, 1px, 1px, 1px)'
      && style.width === '1px' && style.height === '1px'
      && style.overflowX === 'hidden' && style.overflowY === 'hidden';
  };
  // Range rects are viewport AABBs: inverse-transforming them loses rotated/skewed
  // edges. Measure again with only the clip's ancestor transforms neutralized.
  // Identity transforms retain containing blocks; restore every inline style.
  const inClipSpace = (ancestor, measure) => {
    const saved = [];
    try {
      for (let e = ancestor; e; e = e.parentElement) {
        const style = getComputedStyle(e);
        const values = { transform: 'matrix(1,0,0,1,0,0)', translate: '0px', rotate: '0deg', scale: '1', perspective: '1000000000px' };
        const active = Object.keys(values).filter(property => style[property] !== 'none');
        if (!active.length) continue;
        saved.push([e, e.getAttribute('style')]);
        for (const property of active) e.style.setProperty(property, values[property], 'important');
      }
      return measure();
    } finally {
      for (const [e, style] of saved.reverse()) {
        if (style === null) e.removeAttribute('style');
        else e.setAttribute('style', style);
      }
    }
  };
  return [...document.querySelectorAll('section')].map((section, index) => {
    const root = section.getBoundingClientRect();
    const rect = elementOrRect => {
      const r = elementOrRect instanceof Element ? elementOrRect.getBoundingClientRect() : elementOrRect;
      return { left: r.left - root.left, top: r.top - root.top, right: r.right - root.left, bottom: r.bottom - root.top };
    };
    const label = e => (e.textContent || e.getAttribute('alt') || e.tagName).trim().replace(/\s+/g, ' ').slice(0, 90);
    const text = [];
    const walker = document.createTreeWalker(section, NodeFilter.SHOW_TEXT);
    while (walker.nextNode()) {
      const node = walker.currentNode;
      if (!node.textContent.trim()) continue;
      const element = node.parentElement;
      if (element.closest('script,style') || isKatexAccessibilityDuplicate(element)) continue;
      const card = element.closest(cardSelector);
      const range = document.createRange();
      range.selectNodeContents(node);
      const lines = [...range.getClientRects()].map(r => ({ label: node.textContent.trim().slice(0, 90),
        rect: rect(r), container: card ? rect(card) : null, clips: [] }));
      for (let ancestor = element; ancestor && section.contains(ancestor); ancestor = ancestor.parentElement) {
        const style = getComputedStyle(ancestor);
        if (style.display === 'inline' || style.display === 'contents') continue;
        const x = /^(hidden|clip|auto|scroll)$/.test(style.overflowX);
        const y = /^(hidden|clip|auto|scroll)$/.test(style.overflowY);
        if (!x && !y) continue;
        // Absolutely/fixed-positioned descendants escape overflow ancestors
        // between themselves and their containing block (including inline wraps).
        let escapes = false;
        for (let e = element; e && e !== ancestor; e = e.parentElement) {
          if (!/^(absolute|fixed)$/.test(getComputedStyle(e).position)) continue;
          const containingBlock = e.offsetParent;
          if (!containingBlock || (containingBlock !== ancestor && !ancestor.contains(containingBlock))) {
            escapes = true;
            break;
          }
        }
        if (escapes) continue;
        inClipSpace(ancestor, () => {
          const bounds = ancestor.getBoundingClientRect();
          // SVG viewBox scaling survives CSS transform neutralization. Convert
          // viewport Range rects back to the same local units as client* metrics.
          const scaleX = ancestor.offsetWidth ? bounds.width / ancestor.offsetWidth : 1;
          const scaleY = ancestor.offsetHeight ? bounds.height / ancestor.offsetHeight : 1;
          const left = bounds.left + ancestor.clientLeft * scaleX, top = bounds.top + ancestor.clientTop * scaleY;
          const clipRect = { left: 0, top: 0, right: ancestor.clientWidth, bottom: ancestor.clientHeight };
          if (style.overflowX === 'clip' || style.overflowY === 'clip') {
            const margin = style.overflowClipMargin || '0px';
            const expansion = Number.parseFloat(margin.match(/[\d.]+px$/)?.[0]) || 0;
            if (margin.includes('content-box')) {
              clipRect.left += parseFloat(style.paddingLeft); clipRect.right -= parseFloat(style.paddingRight);
              clipRect.top += parseFloat(style.paddingTop); clipRect.bottom -= parseFloat(style.paddingBottom);
            } else if (margin.includes('border-box')) {
              clipRect.left -= ancestor.clientLeft; clipRect.right += parseFloat(style.borderRightWidth);
              clipRect.top -= ancestor.clientTop; clipRect.bottom += parseFloat(style.borderBottomWidth);
            }
            clipRect.left -= expansion; clipRect.right += expansion;
            clipRect.top -= expansion; clipRect.bottom += expansion;
          }
          for (const [i, r] of [...range.getClientRects()].entries()) {
            lines[i].clips.push({ label: `${ancestor.tagName.toLowerCase()}${ancestor.id ? `#${ancestor.id}` : ''}`, x, y,
              coordinateSpace: 'ancestor-padding-box',
              rect: clipRect,
              textRect: { left: (r.left - left) / scaleX, top: (r.top - top) / scaleY,
                right: (r.right - left) / scaleX, bottom: (r.bottom - top) / scaleY } });
          }
        });
      }
      text.push(...lines.filter(line => line.rect.right - line.rect.left >= 0.5 && line.rect.bottom - line.rect.top >= 0.5));
    }
    const cards = [...section.querySelectorAll(cardSelector)].map(e => {
      const s = getComputedStyle(e);
      return { label: label(e), radius: s.borderRadius, shadow: s.boxShadow };
    });
    const images = [...section.querySelectorAll('img')].map(e => ({ label: e.getAttribute('src'), loaded: e.complete && e.naturalWidth > 0,
      naturalWidth: e.naturalWidth, naturalHeight: e.naturalHeight, rect: rect(e) }));
    const collisions = [];
    const blocks = 'H1,H2,H3,H4,H5,H6,P,DIV,UL,OL,TABLE,IMG,PRE,BLOCKQUOTE'.split(',');
    for (const parent of [section, ...section.querySelectorAll('div')]) {
      const children = [...parent.children].filter(e => blocks.includes(e.tagName) && getComputedStyle(e).display !== 'none');
      for (let i = 0; i < children.length; i++) for (let j = i + 1; j < children.length; j++) {
        const a = children[i].getBoundingClientRect(), b = children[j].getBoundingClientRect();
        if (Math.min(a.right, b.right) - Math.max(a.left, b.left) > 3
          && Math.min(a.bottom, b.bottom) - Math.max(a.top, b.top) > 3) {
          collisions.push({ label: `${label(children[i])} / ${label(children[j])}` });
        }
      }
    }
    const footer = section.querySelector('footer');
    if (footer?.textContent.trim()) {
      const f = footer.getBoundingClientRect();
      for (const child of [...section.children].filter(e => blocks.includes(e.tagName))) {
        const c = child.getBoundingClientRect();
        if (Math.min(c.right, f.right) - Math.max(c.left, f.left) > 3
          && Math.min(c.bottom, f.bottom) - Math.max(c.top, f.top) > 3) {
          collisions.push({ label: `${label(child)} / footer` });
        }
      }
    }
    return { number: index + 1, title: section.querySelector('h1')?.textContent || '',
      width: root.width, height: root.height, text, cards, images, collisions };
  });
}

async function canonicalPath(file) {
  try { return await realpath(file); }
  catch (error) {
    if (!['ENOENT', 'ENOTDIR'].includes(error.code)) throw error;
    const parent = path.dirname(file);
    if (parent === file) throw error;
    return path.join(await canonicalPath(parent), path.basename(file));
  }
}

async function fileIdentity(file) {
  let info = null;
  try { info = await stat(file); }
  catch (error) { if (!['ENOENT', 'ENOTDIR'].includes(error.code)) throw error; }
  return { path: await canonicalPath(file), info };
}

async function ownedPages(directory) {
  try { return (await readdir(directory)).filter(name => /^page-\d+\.png$/.test(name)).map(name => path.join(directory, name)); }
  catch (error) { if (error.code === 'ENOENT') return []; throw error; }
}

// Resolve symlinked directories/files and hardlinks before creating, removing or
// writing anything. In particular, failure publication must not destroy inputs.
async function protectInputs({ html, catalog, output }) {
  const pages = path.join(output, 'html');
  const targets = [output, pages, path.join(output, 'layout-report.json'), ...await ownedPages(pages)];
  const sources = await Promise.all([html, catalog].filter(Boolean).map(fileIdentity));
  for (const target of targets) {
    const identity = await fileIdentity(target);
    if (sources.some(source => source.path === identity.path || (source.info && identity.info
      && source.info.dev === identity.info.dev && source.info.ino === identity.info.ino))) {
      throw new Error(`Protected input/output alias: ${target}`);
    }
  }
}

const sha256 = bytes => createHash('sha256').update(bytes).digest('hex');

export async function verifyHtml({ html, output, expected, catalog }) {
  html = path.resolve(html);
  output = path.resolve(output);
  catalog = catalog ? path.resolve(catalog) : undefined;
  await protectInputs({ html, catalog, output });
  const pages = path.join(output, 'html');
  const reportFile = path.join(output, 'layout-report.json');
  const report = { schema_version: 2, html, expected: expected ?? null, checked: 0, issues: 0, slides: [],
    passed: false, errors: [], screenshots: [],
    inputs: { html: { path: html, sha256: null }, catalog: catalog ? { path: catalog, sha256: null } : null } };
  let browser, failure, interceptionFailure;
  const pendingInterceptions = new Set();
  let complete = false;
  try {
    await mkdir(output, { recursive: true });
    await rm(reportFile, { force: true });
    for (const file of await ownedPages(pages)) await rm(file, { force: true });
    await mkdir(pages, { recursive: true });
    const htmlBytes = await readFile(html);
    report.inputs.html.sha256 = sha256(htmlBytes);
    let manifest = null;
    if (catalog) {
      const bytes = await readFile(catalog);
      report.inputs.catalog.sha256 = sha256(bytes);
      manifest = JSON.parse(bytes.toString('utf8'));
    }
    const count = expected ?? manifest?.patterns?.length;
    report.expected = count ?? null;
    if (!Number.isInteger(count) || count < 1) throw new Error('A positive expected slide count is required');
    browser = await puppeteer.launch({ executablePath: process.env.CHROME_PATH || '/usr/bin/google-chrome', headless: true,
      args: ['--no-sandbox', '--allow-file-access-from-files'] });
    const page = await browser.newPage();
    await page.setViewport({ width: 1280, height: 720, deviceScaleFactor: 1 });
    const htmlURL = pathToFileURL(html).href;
    let consumedHtml = false;
    await page.setRequestInterception(true);
    page.on('request', request => {
      const operation = (async () => {
        try {
          if (request.isNavigationRequest() && request.frame() === page.mainFrame()) {
            if (request.url() !== htmlURL) throw new Error(`Unexpected HTML navigation: ${request.url()}`);
            // Fulfill at the original file URL: hash and Chromium consume one
            // immutable read, preserving the file origin/base and relative assets.
            await request.respond({ status: 200, contentType: 'text/html', body: htmlBytes });
            consumedHtml = true;
          } else await request.continue();
        } catch (error) {
          interceptionFailure ??= error;
          try { if (!request.isInterceptResolutionHandled()) await request.abort(); }
          catch (abortError) { interceptionFailure ??= abortError; }
        }
      })();
      pendingInterceptions.add(operation);
      return operation.finally(() => pendingInterceptions.delete(operation));
    });
    await page.goto(htmlURL, { waitUntil: 'networkidle0', timeout: 60000 });
    if (interceptionFailure) throw interceptionFailure;
    if (!consumedHtml) throw new Error('Chrome did not consume the captured HTML');
    await page.emulateMediaType('print');
    await page.evaluate(async () => {
      await document.fonts.ready;
      await Promise.all([...document.images].map(i => i.decode().catch(() => undefined)));
    });
    const measurements = await page.evaluate(measureDocument);
    report.slides = measurements.map((measurement, index) => ({ ...measurement,
      key: manifest?.patterns[index]?.key ?? null, id: manifest?.patterns[index]?.id ?? null,
      screenshot: null, issues: auditSlide(measurement) }));
    report.checked = report.slides.length;
    report.issues = report.slides.reduce((n, slide) => n + slide.issues.length, 0);
    if (measurements.length !== count) throw new Error(`Expected ${count} slides, found ${measurements.length}`);
    const handles = await page.$$('section');
    for (const [index, slide] of report.slides.entries()) {
      const screenshot = path.join(pages, `page-${String(index + 1).padStart(3, '0')}.png`);
      const png = await handles[index].screenshot({ path: screenshot, type: 'png' });
      slide.screenshot = screenshot;
      report.screenshots.push({ page: index + 1, path: screenshot, sha256: sha256(png) });
    }
    complete = true;
  } catch (error) {
    failure = error;
    report.errors.push(error.message || String(error));
  } finally {
    if (browser) {
      try { await browser.close(); }
      catch (error) { failure ??= error; report.errors.push(`Closing Chrome: ${error.message || error}`); }
    }
    await Promise.all(pendingInterceptions);
  }
  if (interceptionFailure && interceptionFailure !== failure) {
    failure ??= interceptionFailure;
    report.errors.push(`Consuming captured HTML: ${interceptionFailure.message || interceptionFailure}`);
  }
  if (complete && !failure) {
    try {
      for (const input of Object.values(report.inputs).filter(Boolean)) {
        if (sha256(await readFile(input.path)) !== input.sha256) throw new Error(`Input changed during layout audit: ${input.path}`);
      }
    } catch (error) { failure = error; report.errors.push(error.message || String(error)); }
  }
  if (!complete || failure) {
    report.screenshots = [];
    for (const slide of report.slides) slide.screenshot = null;
    try { for (const file of await ownedPages(pages)) await rm(file, { force: true }); }
    catch (error) { failure ??= error; report.errors.push(`Removing incomplete screenshots: ${error.message || error}`); }
  }
  if (report.issues) report.errors.push(`Layout audit found ${report.issues} issue(s)`);
  report.passed = complete && !failure && report.issues === 0;
  await writeFile(reportFile, JSON.stringify(report, null, 2) + '\n');
  if (failure) throw failure;
  console.log(JSON.stringify({ checked: report.checked, issues: report.issues,
    failures: report.slides.filter(slide => slide.issues.length).map(slide => ({ slide: slide.number, key: slide.key, title: slide.title, issues: slide.issues })) }, null, 2));
  return report;
}

async function main() {
  const { values } = parseArgs({ options: {
    html: { type: 'string', default: 'html/science-tokyo-catalog.html' },
    output: { type: 'string', default: '.verification' },
    catalog: { type: 'string', default: 'catalog/science-tokyo.json' },
    expected: { type: 'string' },
  } });
  const expected = values.expected === undefined ? undefined : Number(values.expected);
  const report = await verifyHtml({ ...values, expected, catalog: values.expected ? undefined : values.catalog });
  if (!report.passed) process.exitCode = 1;
}

if (process.argv[1] && import.meta.url === pathToFileURL(path.resolve(process.argv[1])).href) {
  main().catch(error => { console.error(error.stack || String(error)); process.exitCode = 1; });
}
