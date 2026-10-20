// Real SSR regression checks for the Content 2 -> 3 security migration.
import { spawn } from 'node:child_process';
import { writeFile } from 'node:fs/promises';

const server = spawn(process.execPath, ['.output/server/index.mjs'], {
  env: { ...process.env, HOST: '127.0.0.1', PORT: '3000' },
  stdio: 'ignore',
});
const base = 'http://127.0.0.1:3000';
const checks = [];
try {
  const deadline = Date.now() + 120_000;
  for (;;) {
    try {
      const response = await fetch(base, { signal: AbortSignal.timeout(2_000) });
      if (response.status === 200) break;
    } catch {}
    if (server.exitCode !== null || Date.now() >= deadline) {
      throw new Error('Documentation SSR listener did not become ready');
    }
    await new Promise(resolve => setTimeout(resolve, 1_000));
  }
  for (const [path, expected] of [
    ['/', 'Getting Started'],
    ['/iso-mdoc-credentials/iso-18013-5-1-mdl', 'ISO 18013-5 Mobile Driving License'],
  ]) {
    const response = await fetch(base + path, { signal: AbortSignal.timeout(10_000) });
    const html = await response.text();
    const headings = [...html.matchAll(/<h1\b[^>]*>([\s\S]*?)<\/h1>/gi)]
      .map(match => match[1].replace(/<[^>]*>/g, '').replace(/\s+/g, ' ').trim());
    if (response.status !== 200 || !headings.some(heading => heading.includes(expected))) {
      throw new Error('Documentation content did not render');
    }
    checks.push({ path, httpStatus: 200, expectedHeadingRendered: true });
  }
  const missing = await fetch(base + '/g1-nonexistent-document', { signal: AbortSignal.timeout(10_000) });
  if (missing.status !== 404) throw new Error('Missing document did not return 404');
  checks.push({ path: '/g1-nonexistent-document', httpStatus: 404 });
  await writeFile('/evidence/docs-smoke.json', JSON.stringify({ schemaVersion: 1, checks }, null, 2) + '\n');
  console.log('PASS: real documentation SSR renders root/nested content and rejects a missing page');
} finally {
  server.kill('SIGTERM');
  setTimeout(() => server.kill('SIGKILL'), 3_000).unref();
}
