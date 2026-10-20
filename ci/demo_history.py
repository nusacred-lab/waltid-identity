"""Evaluate an explicit, expiring demo-only disposition; never hide scanner findings."""
from collections import Counter
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import re
import subprocess
import tempfile

INVENTORY_SHA256 = 'af27df8123fd8a19ea60cd3a1434ae8f464e74df38b0863e269fe6151d73e2fa'
UPSTREAM = 'ef516ecec4c79fd9fba6f1e8b226b52a4e8cf790'
SNAPSHOT = '00eccf347f8c9b3c58a1fbc85a8dc334ec4bbeb6'
FIELDS = ('Commit', 'File', 'RuleID', 'StartLine', 'EndLine', 'StartColumn', 'EndColumn')


def require(condition, message):
    if not condition:
        raise ValueError(message)


def identity(item):
    require(re.fullmatch(r'[0-9a-f]{40}', item['Commit']) is not None, 'Invalid finding commit')
    path = Path(item['File'])
    require(not path.is_absolute() and '..' not in path.parts, 'Invalid finding path')
    require(re.fullmatch(r'[a-z0-9-]+', item['RuleID']) is not None, 'Invalid finding rule')
    for field in FIELDS[3:]:
        require(type(item[field]) is int and item[field] > 0, 'Invalid finding location')
    require(item['EndLine'] >= item['StartLine'], 'Invalid finding span')
    return tuple(item[field] for field in FIELDS)


def load_policy(root=Path('.')):
    require(hashlib.sha256((root / 'ci/gitleaks.toml').read_bytes()).hexdigest() == 'f4a1b36b33c3a6db6c5ca39a28e88f7aed9113649125e7adca2d8fa8d997f6fa',
            'Pinned scanner configuration changed')
    inventory_file = root / 'ci/demo-history-inventory.json'
    policy = json.loads((root / 'ci/demo-history-policy.json').read_text())
    require(hashlib.sha256(inventory_file.read_bytes()).hexdigest() == INVENTORY_SHA256,
            'Historical inventory changed without a new explicit policy review')
    require(policy['inventorySha256'] == INVENTORY_SHA256, 'Historical inventory binding changed')
    require(policy['id'] == 'G1-DEMO-HISTORY-20261021', 'Unknown demo policy')
    require(policy['scope'] == 'synthetic-isolated-demo-only' and policy['productionAllowed'] is False,
            'Historical disposition cannot authorize production')
    require(policy['newFindingsAllowed'] == 0, 'New findings cannot be accepted')
    require(policy['expiresAt'] == '2026-11-20T17:00:00Z', 'Policy extension requires explicit review')
    data = json.loads(inventory_file.read_text())
    require(data['upstreamBaseline'] == UPSTREAM and data['snapshotCommit'] == SNAPSHOT,
            'Historical source anchor changed')
    allowed = Counter()
    for item in data['findings']:
        key = identity(item)
        require(key not in allowed and type(item['count']) is int and item['count'] > 0,
                'Invalid historical occurrence count')
        require(item['origin'] in ('pinned-upstream-ancestry', 'unselected-imported-branch-history'),
                'Unknown historical provenance')
        allowed[key] = item['count']
    require(sum(allowed.values()) == data['rawFindingRecords'] == 2282, 'Incomplete historical inventory')
    return policy, allowed


def evaluate(rows, exit_code, policy, allowed, now=None):
    now = now or datetime.now(timezone.utc)
    expiry = datetime.fromisoformat(policy['expiresAt'].replace('Z', '+00:00'))
    require(now < expiry, 'Demo history disposition expired; review is required')
    require(exit_code in (0, 1), 'Secret scanner failed; no disposition applies')
    require((exit_code == 1) == bool(rows), 'Scanner exit status and evidence disagree')
    observed = Counter(identity(item) for item in rows)
    require(not (observed - allowed), 'New or changed secret findings block the demo')
    require(not (allowed - observed), 'Historical coverage changed; do not silently drop findings')
    return {'schemaVersion': 1, 'policyId': policy['id'], 'scope': policy['scope'],
            'policyExpiresAt': policy['expiresAt'], 'fullHistoryFindingRecords': sum(observed.values()),
            'historyClean': not rows, 'scannerExitCode': exit_code, 'newFindingRecords': 0,
            'decision': 'accepted-known-risk-for-isolated-demo', 'productionAllowed': False,
            'credentialValidityOrRevocationConfirmed': False, 'externalReportingRequested': False}


def scan(scanner, root=Path('.'), target=Path('.')):
    # Use explicit pinned defaults, ignore no inline allow comments, and preserve
    # only the separately proved checksum fingerprint. Never use --baseline-path.
    config = root.resolve() / 'ci/gitleaks.toml'
    ignore = root.resolve() / '.gitleaksignore'
    with tempfile.TemporaryDirectory(prefix='g1-history-') as private:
        report = Path(private) / 'findings.json'
        process = subprocess.run([str(scanner.resolve()), 'git', str(target.resolve()),
                                  '--config', str(config), '--gitleaks-ignore-path', str(ignore),
                                  '--ignore-gitleaks-allow', '--redact', '--no-banner',
                                  '--report-format', 'json', '--report-path', str(report)],
                                 stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=600)
        require(report.exists(), 'Scanner did not produce complete evidence')
        try:
            rows = json.loads(report.read_text())
        except (ValueError, UnicodeError):
            raise ValueError('Scanner evidence is invalid') from None
        require(type(rows) is list and all(item.get('Secret') == 'REDACTED' for item in rows),
                'Scanner evidence must be fully redacted')
        return rows, process.returncode


def main():
    import sys
    try:
        policy, allowed = load_policy()
        for anchor in (UPSTREAM, SNAPSHOT):
            require(subprocess.run(['git', 'merge-base', '--is-ancestor', anchor, 'HEAD'],
                                   stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL).returncode == 0,
                    'Pinned source ancestry must remain intact')
        rows, code = scan(Path(sys.argv[1]))
        result = evaluate(rows, code, policy, allowed)
        result['sourceCommit'] = subprocess.check_output(['git', 'rev-parse', 'HEAD'], text=True).strip()
        destination = Path('build/source-control-evidence/history-policy.json')
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_text(json.dumps(result, indent=2) + '\n')
        print('PASS (demo policy): full history retains 2282 findings; zero new findings; production prohibited')
    except (ValueError, KeyError, OSError, subprocess.SubprocessError):
        # Raw scanner output, values and exception contents never reach CI logs.
        print('FAIL: historical policy, scanner health, coverage or new-finding checks rejected the demo', file=sys.stderr)
        sys.exit(1)


if __name__ == '__main__':
    main()
