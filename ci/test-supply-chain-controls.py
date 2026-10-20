"""Exercise attack scenarios against the real gates; upload outcome labels only."""
from copy import deepcopy
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import secrets
import shutil
import subprocess
import sys
import tempfile
import xml.etree.ElementTree as ET

from demo_history import evaluate, load_policy, scan

root = Path.cwd()
scanner = Path(sys.argv[1]).resolve()
policy, allowed = load_policy()
rows = [dict(zip(('Commit', 'File', 'RuleID', 'StartLine', 'EndLine', 'StartColumn', 'EndColumn'), item))
        for item, count in allowed.items() for _ in range(count)]
checks = []


def reject(name, operation):
    try:
        operation()
    except ValueError:
        checks.append({'case': name, 'result': 'rejected'})
    else:
        raise SystemExit('Control failed to reject: ' + name)


def run_verifier(name, command, cwd, expected_ok=False):
    process = subprocess.run(command, cwd=cwd, capture_output=True)
    if (process.returncode == 0) != expected_ok:
        raise SystemExit('Unexpected verification outcome: ' + name)
    checks.append({'case': name, 'result': 'passed' if expected_ok else 'rejected'})


reject('expired-demo-policy', lambda: evaluate(rows, 1, policy, allowed,
                                             datetime(2026, 11, 21, tzinfo=timezone.utc)))
reject('scanner-error', lambda: evaluate(rows, 2, policy, allowed))
reject('missing-history-coverage', lambda: evaluate(rows[:-1], 1, policy, allowed))
reused = deepcopy(rows[0]); reused['Commit'] = '0' * 40
reject('old-material-in-new-commit', lambda: evaluate(rows + [reused], 1, policy, allowed))

gitdir = subprocess.check_output(['git', 'rev-parse', '--absolute-git-dir'], text=True).strip()
with tempfile.TemporaryDirectory(prefix='g1-negative-controls-') as private:
    base = Path(private)

    def copy_files(destination, names):
        for name in names:
            path = destination / name
            path.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(root / name, path)

    policy_copy = base / 'policy'
    copy_files(policy_copy, ['ci/demo-history-inventory.json', 'ci/demo-history-policy.json', 'ci/gitleaks.toml'])
    altered = json.loads((policy_copy / 'ci/demo-history-inventory.json').read_text())
    altered['findings'][0]['StartLine'] += 1
    (policy_copy / 'ci/demo-history-inventory.json').write_text(json.dumps(altered))
    reject('changed-historical-inventory', lambda: load_policy(policy_copy))
    copy_files(policy_copy, ['ci/demo-history-inventory.json'])
    altered = deepcopy(policy); altered['productionAllowed'] = True
    (policy_copy / 'ci/demo-history-policy.json').write_text(json.dumps(altered))
    reject('production-scope-escalation', lambda: load_policy(policy_copy))

    npm = base / 'npm'
    ledger = json.loads((root / 'ci/npm-dependency-review.json').read_text())
    copy_files(npm, ['ci/npm-dependency-review.json', *ledger['manifestFiles']])
    run_verifier('reviewed-npm-inputs', [sys.executable, str(root / 'ci/verify-npm-review.py')], npm, True)
    lock_name = 'waltid-applications/waltid-digital-credentials/package-lock.json'
    lock_path = npm / lock_name
    lock = json.loads(lock_path.read_text())
    lock['packages']['node_modules/unreviewed-demo-fixture'] = {
        'version': '0.0.0', 'resolved': 'https://registry.npmjs.org/unreviewed-demo-fixture/-/unreviewed-demo-fixture-0.0.0.tgz',
        'integrity': 'sha512-' + 'A' * 86 + '=='}
    lock_path.write_text(json.dumps(lock))
    ledger['manifestFiles'][lock_name] = hashlib.sha256(lock_path.read_bytes()).hexdigest()
    (npm / 'ci/npm-dependency-review.json').write_text(json.dumps(ledger))
    run_verifier('npm-injection-even-with-updated-lock-digest',
                 [sys.executable, str(root / 'ci/verify-npm-review.py')], npm)

    gradle = base / 'gradle'
    ledger = json.loads((root / 'ci/dependency-review.json').read_text())
    copy_files(gradle, ['ci/dependency-review.json', 'gradle/verification-metadata.xml', *ledger['lockfiles']])
    (gradle / '.git').write_text('gitdir: ' + gitdir + '\n')
    verifier = [sys.executable, str(root / 'ci/verify-dependency-review.py'), str(gradle)]
    run_verifier('reviewed-gradle-inputs', verifier, root, True)
    metadata = gradle / 'gradle/verification-metadata.xml'
    tree = ET.parse(metadata); ns = '{https://schema.gradle.org/dependency-verification}'
    component = ET.SubElement(tree.find(ns + 'components'), ns + 'component',
                              {'group': 'example.unreviewed', 'name': 'injected-demo', 'version': '0.0.0'})
    artifact = ET.SubElement(component, ns + 'artifact', {'name': 'injected-demo.jar'})
    ET.SubElement(artifact, ns + 'sha256', {'value': '0' * 64})
    tree.write(metadata, encoding='utf-8', xml_declaration=True)
    ledger['metadataSha256'] = hashlib.sha256(metadata.read_bytes()).hexdigest()
    (gradle / 'ci/dependency-review.json').write_text(json.dumps(ledger))
    run_verifier('gradle-injection-even-with-updated-xml-digest', verifier, root)
    copy_files(gradle, ['ci/dependency-review.json', 'gradle/verification-metadata.xml'])
    lock = gradle / 'build-logic/gradle.lockfile'; lock.write_bytes(lock.read_bytes() + b'\n')
    run_verifier('changed-build-tool-lock', verifier, root)

    ignores = base / 'ignore'
    copy_files(ignores, ['ci/verify-checksum-findings.py', 'ci/checksum-finding-review.json', '.gitleaksignore',
                         'docs/nusacred/evidence/g1-api2-39454853516-outcome.json'])
    (ignores / '.git').write_text('gitdir: ' + gitdir + '\n')
    with (ignores / '.gitleaksignore').open('a') as output:
        output.write('0' * 40 + ':fixture.txt:generic-api-key:1\n')
    run_verifier('unreviewed-ignore', [sys.executable, 'ci/verify-checksum-findings.py'], ignores)

    # A real, newly generated, non-provider test value in a disposable Git repo.
    # The allow comment must not suppress detection. Nothing is pushed or printed.
    fixture = base / 'scanner-fixture'; fixture.mkdir()
    env = {**os.environ, 'GIT_CONFIG_NOSYSTEM': '1', 'GIT_CONFIG_GLOBAL': os.devnull}
    def git(*args):
        subprocess.run(['git', '-c', 'core.hooksPath=/dev/null', '-c', 'commit.gpgsign=false',
                        '-c', 'user.name=G1 fixture', '-c', 'user.email=fixture@example.invalid', *args],
                       cwd=fixture, env=env, check=True, capture_output=True)
    git('init', '-q', '--template=')
    (fixture / 'fixture.txt').write_text('api_key = "' + secrets.token_urlsafe(32) + '" # gitleaks:allow\n')
    git('add', 'fixture.txt'); git('commit', '-q', '-m', 'synthetic detector fixture')
    found, code = scan(scanner, root, fixture)
    if not found or code != 1:
        raise SystemExit('Synthetic new-secret detector did not fire')
    reject('new-secret-with-inline-allow-comment', lambda: evaluate(found, code, policy, allowed))

report = {'schemaVersion': 1, 'checks': checks, 'realCredentialsUsed': False,
          'externalServicesContacted': False, 'rawScannerReportsUploaded': False}
output = root / 'build/source-control-evidence/supply-chain-negative-checks.json'
output.parent.mkdir(parents=True, exist_ok=True)
output.write_text(json.dumps(report, indent=2) + '\n')
print(f'PASS: {len(checks)} supply-chain acceptance/rejection scenarios')
