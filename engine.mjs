import attrs from 'markdown-it-attrs';
import mark from 'markdown-it-mark';
import htmlBlock from 'markdown-it/lib/rules_block/html_block.mjs';

const blockContainers = {
  box: 'box',
  card: 'card',
  'navy-card': 'navy-card',
  callout: 'callout',
  lead: 'lead',
  cite: 'cite',
  'cite-right': 'cite-right',
  center: 'center',
  small: 'small',
  xs: 'xs',
  col: 'col',
  note: 'note',
  info: 'info',
  warning: 'warning',
  'grid-2': 'grid-2',
  'grid-3': 'grid-3',
  stack: 'stack',
  metric: 'metric',
  band: 'band',
  foundation: 'foundation',
  steps: 'steps',
  step: 'step',
  matrix: 'matrix',
  compare: 'compare',
  figure: 'figure',
};

const blockContainerNames = new Set(Object.keys(blockContainers));
const columnsPattern = /^(?:cols|columns)(?:-([23])|\s+([23]))?$/;
const blockAlternatives = { alt: ['paragraph', 'reference', 'blockquote', 'list'] };
// markdown-it html_block types 1/2: these literal blocks can interrupt a
// paragraph and end at a terminator, not a blank line. Do not treat inline
// tags or ordinary HTML layout blocks as literal containers.
const htmlLiteralSequences = [
  [/^<(script|pre|style|textarea)(?=(\s|>|$))/i, /<\/(script|pre|style|textarea)>/i],
  [/^<!--/, /-->/],
];

function getLine(state, line) {
  return state.src.slice(state.bMarks[line] + state.tShift[line], state.eMarks[line]).trim();
}

/* Share boundary scanning: neither a nested layout's ||| nor a code example
   may terminate its parent. Longer outer fences are the recommended syntax;
   same-length legacy card-in-cols fences remain supported as well. */
function scanContainer(state, startLine, endLine, markerLen) {
  const segments = [];
  const nestedMarkers = [];
  let segmentStart = startLine + 1;
  let codeFence;
  let htmlLiteralEnd;
  let htmlBlockEnd = 0;
  let nextLine = startLine + 1;
  let closed = false;

  for (; nextLine < endLine; nextLine += 1) {
    const line = getLine(state, nextLine);
    if (line && state.sCount[nextLine] < state.blkIndent) break;
    if (htmlLiteralEnd) {
      if (htmlLiteralEnd.test(line)) htmlLiteralEnd = undefined;
      continue;
    }
    if (state.sCount[nextLine] - state.blkIndent >= 4) continue;

    const fence = line.match(/^(`{3,}|~{3,})(.*)$/);
    if (codeFence) {
      if (fence && fence[1][0] === codeFence.char
          && fence[1].length >= codeFence.length && !fence[2].trim()) codeFence = undefined;
      continue;
    }
    if (fence && (fence[1][0] !== '`' || !fence[2].includes('`'))) {
      codeFence = { char: fence[1][0], length: fence[1].length };
      continue;
    }

    if (state.md.options.html && nextLine >= htmlBlockEnd) {
      const literal = htmlLiteralSequences.find(([open]) => open.test(line));
      if (literal) {
        if (!literal[1].test(line)) htmlLiteralEnd = literal[1];
        continue;
      }
      // An interrupting raw HTML block owns its content until markdown-it's
      // end rule, even if a quoted attribute or body line looks like <pre>.
      // Probe without emitting tokens or advancing the real parser state.
      const probe = Object.assign(Object.create(state), { tokens: [] });
      if (htmlBlock(probe, nextLine, endLine, true)) {
        htmlBlock(probe, nextLine, endLine, false);
        htmlBlockEnd = probe.line;
      }
    }

    if (nestedMarkers.length === 0 && line === '|||') {
      segments.push([segmentStart, nextLine]);
      segmentStart = nextLine + 1;
      continue;
    }
    const colon = line.match(/^(:{3,})(.*)$/);
    if (!colon) continue;
    const length = colon[1].length;
    const rest = colon[2].trim();
    if (!rest) {
      if (nestedMarkers.length > 0 && length >= nestedMarkers.at(-1)) {
        nestedMarkers.pop();
      } else if (nestedMarkers.length === 0 && length >= markerLen) {
        closed = true;
        break;
      }
      continue;
    }
    const innerName = rest.match(/^([A-Za-z][\w-]*)(?:\s|$)/)?.[1];
    if (blockContainerNames.has(innerName) || columnsPattern.test(rest)) nestedMarkers.push(length);
  }
  segments.push([segmentStart, nextLine]);
  return { end: nextLine, closed, segments };
}

function opener(state, startLine) {
  if (state.sCount[startLine] - state.blkIndent >= 4) return undefined;
  return getLine(state, startLine).match(/^(:{3,})\s*(.*)$/);
}

function tokenizeInside(state, from, to) {
  const oldParent = state.parentType;
  const oldLineMax = state.lineMax;
  state.parentType = 'container';
  state.lineMax = to;
  try {
    state.md.block.tokenize(state, from, to);
  } finally {
    state.parentType = oldParent;
    state.lineMax = oldLineMax;
  }
}

function useClassContainer(md, name, className = name) {
  md.block.ruler.before('fence', `container_${name}`, (state, startLine, endLine, silent) => {
    const match = opener(state, startLine);
    if (!match || match[2].trim().split(' ', 2)[0] !== name) return false;
    if (silent) return true;
    const boundary = scanContainer(state, startLine, endLine, match[1].length);
    const open = state.push(`container_${name}_open`, 'div', 1);
    open.block = true;
    open.markup = match[1];
    open.info = match[2];
    open.map = [startLine, boundary.end];
    tokenizeInside(state, startLine + 1, boundary.end);
    const close = state.push(`container_${name}_close`, 'div', -1);
    close.block = true;
    close.markup = boundary.closed ? getLine(state, boundary.end) : '';
    state.line = boundary.end + (boundary.closed ? 1 : 0);
    return true;
  }, blockAlternatives);
  md.renderer.rules[`container_${name}_open`] = () => `<div class="${className}">\n`;
  md.renderer.rules[`container_${name}_close`] = () => '</div>\n';
}

function columnsBlockPlugin(md) {
  md.block.ruler.before('fence', 'science_tokyo_columns', (state, startLine, endLine, silent) => {
    const opening = opener(state, startLine);
    const match = opening?.[2].trim().match(columnsPattern);
    if (!match) return false;
    if (silent) return true;
    const boundary = scanContainer(state, startLine, endLine, opening[1].length);
    // Preserve legacy behavior: an unclosed columns declaration is plain text.
    if (!boundary.closed) return false;
    const className = (match[1] || match[2]) === '3' ? 'columns-3' : 'columns';
    const open = state.push('science_tokyo_columns_open', 'div', 1);
    open.block = true;
    open.markup = opening[1];
    open.map = [startLine, boundary.end];
    open.attrSet('class', className);
    for (const [from, to] of boundary.segments) {
      const colOpen = state.push('science_tokyo_column_open', 'div', 1);
      colOpen.block = true;
      colOpen.attrSet('class', 'col');
      tokenizeInside(state, from, to);
      state.push('science_tokyo_column_close', 'div', -1).block = true;
    }
    state.push('science_tokyo_columns_close', 'div', -1).block = true;
    state.line = boundary.end + 1;
    return true;
  }, blockAlternatives);
}

export default ({ marp }) => {
  marp.use(mark).use(attrs).use(columnsBlockPlugin);
  for (const [name, className] of Object.entries(blockContainers)) {
    marp.use(useClassContainer, name, className);
  }
  return marp;
};
