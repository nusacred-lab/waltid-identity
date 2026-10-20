"""Report fixed failure categories, not arbitrary package/compiler log contents."""
import json
from pathlib import Path
import re
import sys

stage, temporary, destination = sys.argv[1:]
private = Path(temporary)
state = json.loads((private / 'state.json').read_text())
text = (private / (stage + '.log')).read_text(errors='replace')
categories = {
    'network_request_blocked': any(word in text for word in ('ENETUNREACH', 'ENOTFOUND', 'EAI_AGAIN')),
    'missing_module': any(word in text for word in ('ERR_MODULE_NOT_FOUND', 'Cannot find module', 'Cannot find package')),
    'native_binding_missing': 'Could not locate the bindings file' in text,
    'readonly_filesystem': 'EROFS' in text,
    'permission_denied': 'EACCES' in text,
    'documentation_ssr_failed': 'Documentation' in text or 'Missing document did not return 404' in text,
}
record = dict(schemaVersion=1, stage=stage, exitCode=state['ExitCode'], oomKilled=state['OOMKilled'],
              typescriptErrorCodes=sorted(set(re.findall(r'\bTS\d{4}\b', text))),
              failureCategories=[key for key, present in categories.items() if present],
              rawPackageOrBuildLogsPublished=False)
(Path(destination) / 'failure.json').write_text(json.dumps(record, indent=2) + '\n')
print('Frontend stage failed: ' + stage + '; categories=' + ','.join(record['failureCategories']))
