"""Verify immutable catalog preservation and removal of unused Nuxt runtimes."""
import hashlib
import json
from pathlib import Path
import subprocess


def require(condition, message):
    if not condition:
        raise SystemExit(message)


baseline = '51daa3381dfb434265572c33c8f0ac5fd3687df0'
catalog = 'waltid-applications/waltid-credentials/'
manifest = json.loads(Path('ci/credential-catalog-source.json').read_text())
require(manifest['sourceCommit'] == baseline, 'Catalog origin changed without review')
original = subprocess.check_output(['git', 'ls-tree', '-r', '--name-only', baseline, '--',
                                    catalog + 'src/content', catalog + 'src/public'], text=True).splitlines()
proof = {entry['path']: entry['sha256'] for entry in manifest['files']}
require(len(proof) == len(manifest['files']), 'Duplicate catalog proof')
require(set(proof) == set(original), 'Original catalog inventory must remain complete')
for name in original:
    source = subprocess.check_output(['git', 'show', baseline + ':' + name])
    require(hashlib.sha256(source).hexdigest() == proof[name], 'Catalog proof changed: ' + name)
    require(Path(name).read_bytes() == source, 'Catalog source changed: ' + name)
require(not Path('waltid-applications/waltid-web-portal2').exists(), 'Retired Nuxt portal must not reappear')
files = {str(p) for p in Path(catalog).rglob('*') if p.is_file()}
require(files == set(original) | {catalog + 'README.md'}, 'Catalog must remain source-only')
for filename in ['docker-compose/docker-compose.yaml', 'docker-compose/Caddyfile']:
    content = Path(filename).read_text()
    require('web-portal2' not in content and 'vc-repo' not in content,
            'Retired service/proxy reference remains: ' + filename)
environment = Path('docker-compose/.env.example').read_text()
require(not any(line.startswith(('WEB_PORTAL2_', 'VC_REPO_PORT=', 'VERSION_VC_REPO='))
                for line in environment.splitlines()), 'Retired environment setting remains')
lock = json.loads(Path('waltid-applications/waltid-digital-credentials/package-lock.json').read_text())
require(not any(p.endswith(('/node-forge', '/braces')) for p in lock['packages']),
        'Retained example reintroduced vulnerable dependency family')
print(f'PASS: {len(original)} catalog files match immutable source; retired runtimes absent')
