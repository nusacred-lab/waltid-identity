"""Verify every exact checksum classification before applying scanner fingerprints."""
import hashlib
import json
from pathlib import Path
import re
import subprocess

def require(condition, message):
    if not condition:
        raise SystemExit(message)

data = json.loads(Path('ci/checksum-finding-review.json').read_text())
ignored = {line.strip() for line in Path('.gitleaksignore').read_text().splitlines()
           if line.strip() and not line.lstrip().startswith('#')}
verified = set()
expected_outcome = {
    'schemaVersion': 1, 'syntheticData': True, 'realHttpServices': True,
    'issuance': 'passed', 'walletStorage': 'passed', 'preview': 'passed',
    'holderBoundPresentation': 'passed', 'verification': 'passed',
}
for item in data['resolutions']:
    require(item['classification'] == 'verified-non-secret-build-checksum', 'Unsupported secret finding classification')
    revision = item['sourceCommit']
    source = Path(item['sourceFile'])
    proof = Path(item['proofFile'])
    require(re.fullmatch('[0-9a-f]{40}', revision), 'An immutable source commit is required')
    for path in (source, proof):
        require(not path.is_absolute() and '..' not in path.parts
                and path.parts[:3] == ('docs', 'nusacred', 'evidence'), 'Unexpected checksum evidence path')
    parts = item['fingerprint'].split(':')
    require(len(parts) == 4 and parts[0] == revision and parts[1] == str(source)
            and parts[2] == 'generic-api-key' and parts[3].isdigit(), 'Finding must match the exact immutable source')
    historical = subprocess.check_output(['git', 'show', revision + ':' + str(source)])
    document = json.loads(historical)
    published = document['evidenceFileSha256'][item['sourceMapEntry']]
    require(re.fullmatch('[0-9a-f]{64}', published), 'Finding is not a SHA-256 field')
    line = historical.decode().splitlines()[int(parts[3]) - 1]
    require(item['sourceMapEntry'] == 'reports/credential-harness.json', 'Unrecognized outcome map field')
    line_object = json.loads('{' + line.strip().removesuffix(',') + '}')
    require(line_object == {item['sourceMapEntry']: published}, 'Finding line must contain only the verified checksum field')
    payload = proof.read_bytes()
    require(json.loads(payload) == expected_outcome, 'Proof must contain only fixed non-secret outcome fields')
    require(hashlib.sha256(payload).hexdigest() == published, 'Proof bytes do not match the recorded checksum')
    require(item['fingerprint'] not in verified, 'Duplicate checksum resolution')
    verified.add(item['fingerprint'])
require(ignored == verified, 'Every scanner fingerprint must have exact verified non-secret evidence')
print(f'PASS: {len(verified)} immutable generated-checksum classifications verified')
