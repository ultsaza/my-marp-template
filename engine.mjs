import container from 'markdown-it-container';
import attrs from 'markdown-it-attrs';
import mark from 'markdown-it-mark';

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
};

const blockContainerNames = new Set(Object.keys(blockContainers));

function useClassContainer(md, name, className = name) {
  return md.use(container, name, {
    render(tokens, idx) {
      return tokens[idx].nesting === 1
        ? `<div class="${className}">\n`
        : '</div>\n';
    },
  });
}

function getLine(state, line) {
  const start = state.bMarks[line] + state.tShift[line];
  const end = state.eMarks[line];
  return state.src.slice(start, end).trim();
}

function columnsBlockPlugin(md) {
  md.block.ruler.before(
    'fence',
    'science_tokyo_columns',
    (state, startLine, endLine, silent) => {
      const start = state.bMarks[startLine] + state.tShift[startLine];
      const max = state.eMarks[startLine];

      if (state.sCount[startLine] - state.blkIndent >= 4) return false;
      if (state.src.charCodeAt(start) !== 0x3a /* : */) return false;

      const markerEnd = state.skipChars(start, 0x3a);
      const markerLen = markerEnd - start;
      if (markerLen < 3) return false;

      const params = state.src.slice(markerEnd, max).trim();
      const match = params.match(/^(?:cols|columns)(?:-([23])|\s+([23]))?$/);
      if (!match) return false;
      if (silent) return true;

      const className = (match[1] || match[2]) === '3' ? 'columns-3' : 'columns';
      const segments = [];
      const nestedMarkers = [];
      let segmentStart = startLine + 1;
      let nextLine = startLine + 1;
      let found = false;

      for (; nextLine < endLine; nextLine += 1) {
        const line = getLine(state, nextLine);
        const colonMatch = line.match(/^(:{3,})(.*)$/);

        if (nestedMarkers.length === 0 && line === '|||') {
          segments.push([segmentStart, nextLine]);
          segmentStart = nextLine + 1;
          continue;
        }

        if (!colonMatch) continue;

        const currentMarkerLen = colonMatch[1].length;
        const rest = colonMatch[2].trim();

        if (rest === '') {
          if (
            nestedMarkers.length > 0
            && currentMarkerLen >= nestedMarkers[nestedMarkers.length - 1]
          ) {
            nestedMarkers.pop();
            continue;
          }

          if (nestedMarkers.length === 0 && currentMarkerLen >= markerLen) {
            segments.push([segmentStart, nextLine]);
            found = true;
            break;
          }

          continue;
        }

        const innerName = rest.match(/^([A-Za-z][\w-]*)(?:\s|$)/)?.[1];
        if (blockContainerNames.has(innerName)) nestedMarkers.push(currentMarkerLen);
      }

      if (!found) return false;

      const oldParent = state.parentType;
      const oldLineMax = state.lineMax;

      state.parentType = 'container';

      const open = state.push('science_tokyo_columns_open', 'div', 1);
      open.block = true;
      open.markup = state.src.slice(start, markerEnd);
      open.map = [startLine, nextLine];
      open.attrSet('class', className);

      for (const [from, to] of segments) {
        const colOpen = state.push('science_tokyo_column_open', 'div', 1);
        colOpen.block = true;
        colOpen.attrSet('class', 'col');

        state.lineMax = to;
        state.md.block.tokenize(state, from, to);

        const colClose = state.push('science_tokyo_column_close', 'div', -1);
        colClose.block = true;
      }

      const close = state.push('science_tokyo_columns_close', 'div', -1);
      close.block = true;

      state.parentType = oldParent;
      state.lineMax = oldLineMax;
      state.line = nextLine + 1;
      return true;
    },
    { alt: ['paragraph', 'reference', 'blockquote', 'list'] },
  );
}

export default ({ marp }) => {
  marp.use(mark).use(attrs).use(columnsBlockPlugin);

  for (const [name, className] of Object.entries(blockContainers)) {
    useClassContainer(marp, name, className);
  }

  return marp;
};
