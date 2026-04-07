import container from 'markdown-it-container';
import attrs from 'markdown-it-attrs';
import mark from 'markdown-it-mark';

export default ({ marp }) =>
  marp
    .use(mark)
    .use(attrs)
    .use(container, 'note')
    .use(container, 'warning')
    .use(container, 'info');
