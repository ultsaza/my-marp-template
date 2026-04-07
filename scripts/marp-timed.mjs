import { spawn } from 'node:child_process';

const args = process.argv.slice(2);
const child = spawn('npx', ['marp', ...args], { stdio: ['inherit', 'pipe', 'pipe'] });

let start = Date.now();
let tot = 0;

function handleLine(line) {
  if (line.includes('Converting') && line.includes('markdown')) {
    start = Date.now();
  }
  if (line.includes('=>')) {
    const elapsed = Date.now() - start;
    tot += elapsed;
    process.stdout.write(`${line}  (${elapsed}ms)\n`);
    return;
  }
  if (line.includes('[WARN]') || line.includes('[ERROR]')) {
    process.stderr.write(line + '\n');
    return;
  }
  if (line.includes('[Watch mode]')) {
    process.stdout.write(`\x1b[30m\x1b[103m Total time: ${tot}ms \x1b[0m\n`);
  }
  process.stdout.write(line + '\n');
}

let buffer = '';
child.stdout.on('data', (data) => {
  buffer += data.toString();
  const lines = buffer.split('\n');
  buffer = lines.pop();
  for (const line of lines) handleLine(line);
});

child.stderr.on('data', (data) => {
  buffer += data.toString();
  const lines = buffer.split('\n');
  buffer = lines.pop();
  for (const line of lines) handleLine(line);
});

child.on('close', (code) => {
  if (buffer) handleLine(buffer);
  process.exit(code);
});
