"""Require internal aliases and no external route before exercising real services."""
import errno
import json
import os
from pathlib import Path
import socket

for service, port in (('issuer', 7005), ('wallet', 7006), ('verifier', 7004)):
    if os.environ.get(service.upper() + '_URL') != f'http://{service}:{port}':
        raise SystemExit('Only internal demo service URLs are permitted')
for name, value in os.environ.items():
    if name.lower() in ('http_proxy', 'https_proxy', 'all_proxy') and value:
        raise SystemExit('External proxy configuration is prohibited')
probe = socket.socket()
probe.settimeout(2)
try:
    # Reserved documentation address: no real provider or credential is probed.
    probe.connect(('192.0.2.1', 443))
except OSError as error:
    if error.errno not in (errno.ENETUNREACH, errno.EHOSTUNREACH):
        raise SystemExit('External routing isolation could not be proved') from None
else:
    raise SystemExit('External route exists')
finally:
    probe.close()
Path(os.environ['HARNESS_ISOLATION_REPORT']).write_text(json.dumps({
    'schemaVersion': 1, 'internalServiceUrlsOnly': True,
    'externalRouteRejected': True, 'providerAuthenticationAttempted': False,
    'productionAllowed': False
}, indent=2) + '\n')
print('PASS: internal aliases, no proxy, no external route')
