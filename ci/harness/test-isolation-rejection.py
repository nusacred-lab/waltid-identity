"""Mutate captured inspection evidence, never live container privileges or mounts."""
from copy import deepcopy
import json
from pathlib import Path
import subprocess
import sys

private, reports = map(Path, sys.argv[1:])
checker = Path(__file__).with_name('check_container_isolation.py')
network_file, issuer_file = private / 'network.json', private / 'issuer-container.json'
original_network, original_issuer = network_file.read_bytes(), issuer_file.read_bytes()
checks = []
try:
    for case in ('egress-enabled-bridge', 'host-port', 'root-user', 'extra-capability',
                 'external-dns', 'host-credential-mount'):
        network, issuer = json.loads(original_network), json.loads(original_issuer)
        if case == 'egress-enabled-bridge': network[0]['Internal'] = False
        elif case == 'host-port': issuer[0]['HostConfig']['PortBindings'] = {'7005/tcp': [{'HostPort': '7005'}]}
        elif case == 'root-user': issuer[0]['Config']['User'] = '0:1000'
        elif case == 'extra-capability': issuer[0]['HostConfig']['CapAdd'] = ['SYS_ADMIN']
        elif case == 'external-dns': issuer[0]['HostConfig']['Dns'] = ['8.8.8.8']
        elif case == 'host-credential-mount':
            next(m for m in issuer[0]['Mounts'] if m['Type'] == 'bind')['Source'] = '/host-credentials-not-mounted'
        network_file.write_text(json.dumps(network)); issuer_file.write_text(json.dumps(issuer))
        result = subprocess.run([sys.executable, str(checker), str(private), str(reports)], capture_output=True)
        if result.returncode == 0:
            raise SystemExit('Isolation guard failed to reject: ' + case)
        checks.append({'case': case, 'result': 'rejected'})
finally:
    network_file.write_bytes(original_network); issuer_file.write_bytes(original_issuer)
(reports / 'demo-isolation-negative-checks.json').write_text(json.dumps({
    'schemaVersion': 1, 'checks': checks, 'liveContainerSecurityWeakened': False
}, indent=2) + '\n')
print('PASS: six unsafe container inspection scenarios rejected without weakening live containers')
