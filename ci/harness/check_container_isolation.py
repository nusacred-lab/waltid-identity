"""Inspect actual Docker state; do not infer isolation from command-line intent."""
import json
from pathlib import Path
import sys


def require(condition):
    if not condition:
        raise SystemExit('Actual demo container isolation rejected')


private, reports = map(Path, sys.argv[1:])
network = json.loads((private / 'network.json').read_text())[0]
require(network['Internal'] is True)
for service in ('issuer', 'wallet', 'verifier', 'runner'):
    container = json.loads((private / (service + '-container.json')).read_text())[0]
    config, host = container['Config'], container['HostConfig']
    require(config['User'].split(':')[0] not in ('', '0', 'root'))
    require(host['ReadonlyRootfs'] and not host['Privileged'])
    require(host.get('CapAdd') in (None, []) and 'ALL' in host['CapDrop'])
    require(any(option.startswith('no-new-privileges') for option in host['SecurityOpt']))
    require(not host.get('PortBindings') and host['Dns'] == ['127.0.0.1'])
    require(set(container['NetworkSettings']['Networks']) == {network['Name']})
    require(all(mount['Type'] in ('bind', 'tmpfs') for mount in container['Mounts']))
    require(set(host['Tmpfs']) == {'/tmp'})
    blocked = {'AWS_ACCESS_KEY_ID', 'AWS_SECRET_ACCESS_KEY', 'AWS_SESSION_TOKEN',
               'AZURE_CLIENT_SECRET', 'GOOGLE_APPLICATION_CREDENTIALS', 'GITHUB_TOKEN', 'GH_TOKEN'}
    require(not any(value.partition('=')[0] in blocked for value in config['Env']))
    if service == 'runner':
        sources = {'/checks': Path(__file__).resolve().parent, '/reports': reports.resolve()}
    else:
        sources = {f'/waltid-{service}-api2/config': private / 'runtime/walt' / service}
        if service == 'wallet':
            sources['/data'] = private / 'runtime/data'
    bind_mounts = [mount for mount in container['Mounts'] if mount['Type'] == 'bind']
    require({mount['Destination'] for mount in bind_mounts} == set(sources))
    for mount in bind_mounts:
        require(Path(mount['Source']).resolve() == sources[mount['Destination']].resolve())
        require(mount['RW'] == (mount['Destination'] in ('/data', '/reports')))
    if service == 'runner':
        require(container['State']['Status'] == 'exited' and container['State']['ExitCode'] == 0)
        require(not container['State']['OOMKilled'])
result = json.loads((reports / 'demo-isolation.json').read_text())
expected = {'schemaVersion': 1, 'internalServiceUrlsOnly': True, 'externalRouteRejected': True,
            'providerAuthenticationAttempted': False, 'productionAllowed': False}
require(all(result.get(name) == value for name, value in expected.items()))
result.update(internalDockerBridge=True, externalDnsForwardingDisabled=True,
              hostPortsPublished=False, unprivilegedReadOnlyContainers=True,
              exactMountSourcesAndTargetsVerified=True, runnerPrivateKeysMounted=False)
(reports / 'demo-isolation.json').write_text(json.dumps(result, indent=2) + '\n')
print('PASS: actual network, DNS, privileges, mounts and harness exit state verified')
