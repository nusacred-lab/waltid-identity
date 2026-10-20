// Real SSR regression checks for the Content 2 -> 3 security migration.
import { spawn } from 'node:child_process';
import { readFile, writeFile } from 'node:fs/promises';
import { isDeepStrictEqual } from 'node:util';

const server = spawn(process.execPath, ['.output/server/index.mjs'], {
  env: { ...process.env, HOST: '127.0.0.1', PORT: '3000' },
  // The container driver captures this privately and publishes only categories.
  stdio: 'inherit',
});
const base = 'http://127.0.0.1:3000';
const checks = [];
async function fail(stage, details) {
  await writeFile('/evidence/docs-failure.json', JSON.stringify({ schemaVersion: 1, stage, ...details }, null, 2) + '\n');
  throw new Error('Documentation SSR failed at ' + stage);
}
async function readJson(response, stage, details) {
  if (response.status !== 200) await fail(stage, { ...details, httpStatus: response.status });
  try { return await response.json(); }
  catch { await fail(stage, { ...details, invalidJson: true }); }
}
const request = path => fetch(base + path, { signal: AbortSignal.timeout(10_000) });
try {
  const deadline = Date.now() + 120_000;
  let lastStatus = null;
  for (;;) {
    try {
      const response = await fetch(base, { signal: AbortSignal.timeout(2_000) });
      lastStatus = response.status;
      if (response.status === 200) break;
    } catch {}
    if (server.exitCode !== null || Date.now() >= deadline) {
      await fail('listener', { httpStatus: lastStatus, serverExitCode: server.exitCode });
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
      await fail('content', { path, httpStatus: response.status, h1Count: headings.length });
    }
    const toc = html.match(/<nav\b[^>]*aria-label="Table of contents"[^>]*>([\s\S]*?)<\/nav>/)?.[1] ?? '';
    const footer = html.match(/<nav\b[^>]*aria-label="Previous and next pages"[^>]*>([\s\S]*?)<\/nav>/)?.[1] ?? '';
    const ids = new Set([...html.matchAll(/\bid="([^"]+)"/g)].map(match => match[1]));
    const tocTargets = [...toc.matchAll(/\bhref="([^"]+)"/g)].map(match => new URL(match[1], base + path));
    const validToc = tocTargets.length > 0 && tocTargets.every(target =>
      target.origin === base && target.pathname === path && target.hash.length > 1
      && ids.has(decodeURIComponent(target.hash.slice(1))));
    if (!validToc || !footer.includes('<a')
        || !html.includes('href="/iso-mdoc-credentials/iso-18013-5-1-mdl"')) {
      await fail('navigation', { path });
    }
    checks.push({ path, httpStatus: 200, expectedHeadingRendered: true });
  }
  const missing = await fetch(base + '/g1-nonexistent-document', { signal: AbortSignal.timeout(10_000) });
  if (missing.status !== 404) await fail('missing-page', { httpStatus: missing.status });
  checks.push({ path: '/g1-nonexistent-document', httpStatus: 404 });
  async function reference(file, heading) {
    const markdown = await readFile('src/content/' + file, 'utf8');
    const section = heading
      ? markdown.split(/^## /m).find(part => part.split('\n', 1)[0].trim().toLowerCase() === heading)
      : markdown;
    const block = section?.match(/^```json[^\n]*\n([\s\S]*?)^```[ \t]*$/m);
    if (!block) await fail('reference-fixture', { file });
    return JSON.parse(block[1]);
  }
  for (const fixture of [
    { api: 'mdoc', file: '1.iso-mdoc-credentials/asit-iso-id-austria.md', title: 'ID Austria' },
    { api: 'sdjwt-vc', file: '2.sd-jwt-credentials/asit-asit-tax-id-credential.md', title: 'Tax ID Credential' },
    { api: 'vc', file: '3.w3c-credentials/AlpsTourReservation.md', title: 'AlpsTourReservation' },
  ]) {
    const listing = await request('/api/' + fixture.api + '/list');
    const names = await readJson(listing, 'api-list', { api: fixture.api });
    if (listing.status !== 200 || !Array.isArray(names) || !names.includes(fixture.title)) {
      await fail('api-list', { api: fixture.api, httpStatus: listing.status });
    }
    const response = await request('/api/' + fixture.api + '/' + encodeURIComponent(fixture.title));
    const result = await readJson(response, 'api-json', { api: fixture.api });
    if (response.status !== 200 || !isDeepStrictEqual(result, await reference(fixture.file))) {
      await fail('api-json', { api: fixture.api, httpStatus: response.status });
    }
    const unknown = await request('/api/' + fixture.api + '/g1-nonexistent-credential');
    if (unknown.status !== 400) await fail('api-missing', { api: fixture.api, httpStatus: unknown.status });
    checks.push({ api: fixture.api, list: 'passed', jsonMatchesSource: true, missingStatus: 400 });
  }
  for (const api of ['mapping', 'manifest']) {
    const response = await request('/api/' + api + '/' + encodeURIComponent('G1 Contract Fixture'));
    const result = await readJson(response, 'api-section', { api });
    if (response.status !== 200 || !isDeepStrictEqual(result,
      await reference('3.w3c-credentials/g1-contract-fixture.md', api))) {
      await fail('api-section', { api, httpStatus: response.status });
    }
    checks.push({ api, jsonMatchesVersionedSyntheticFixture: true });
  }
  await writeFile('/evidence/docs-smoke.json', JSON.stringify({ schemaVersion: 1, checks }, null, 2) + '\n');
  console.log('PASS: real documentation SSR, navigation, TOC and JSON APIs preserve their contracts');
} finally {
  server.kill('SIGTERM');
  setTimeout(() => server.kill('SIGKILL'), 3_000).unref();
}
