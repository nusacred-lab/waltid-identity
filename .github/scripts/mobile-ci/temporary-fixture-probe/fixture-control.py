"""Temporary real-fixture startup/request experiment; no wallet UI acceptance claim."""
import http.client
import json
from pathlib import Path
import socket
import subprocess
import time

ROOT = Path(__file__).resolve().parent
launch = json.loads((ROOT / 'fixture-launch.json').read_text())
results = []

for port in (33334, 33335):
    with socket.socket() as connection:
        connection.settimeout(1)
        assert connection.connect_ex(('127.0.0.1', port)) != 0, f'Port {port} already in use'

for iteration in range(1, 6):
    record = {'iteration': iteration, 'requests': []}
    log_path = ROOT / f'fixture-control-{iteration}.log'
    started = time.monotonic()
    with log_path.open('wb') as log:
        process = subprocess.Popen(launch['command'], cwd=launch['workingDirectory'],
                                   stdin=subprocess.PIPE, stdout=log, stderr=subprocess.STDOUT)
        try:
            while True:
                if process.poll() is not None:
                    raise RuntimeError(f'Fixture exited before readiness: {process.returncode}')
                connection = http.client.HTTPConnection('127.0.0.1', 33335, timeout=1)
                try:
                    connection.request('GET', '/health')
                    response = connection.getresponse()
                    response.read()
                    if response.status == 200:
                        break
                except OSError:
                    pass
                finally:
                    connection.close()
                elapsed = time.monotonic() - started
                if elapsed > 30 and 'thread_dump' not in record:
                    dump = ROOT / f'fixture-control-{iteration}-threads.log'
                    with dump.open('wb') as output:
                        try:
                            result = subprocess.run([str(Path(launch['command'][0]).with_name('jcmd')),
                                                     str(process.pid), 'Thread.print', '-l'],
                                                    stdout=output, stderr=subprocess.STDOUT, timeout=10)
                            record['thread_dump'] = {'path': dump.name, 'exit': result.returncode}
                        except subprocess.TimeoutExpired:
                            record['thread_dump'] = {'path': dump.name, 'timeout': True}
                if elapsed > 180:
                    raise TimeoutError('Fixture did not become ready within 180 seconds')
                time.sleep(0.2)
            record['ready_seconds'] = round(time.monotonic() - started, 3)
            connection = http.client.HTTPConnection('localhost', 33335, timeout=30)
            try:
                for index in range(12):
                    request_started = time.monotonic()
                    if index % 3 == 0:
                        route = '/scenarios'
                        connection.request('GET', route)
                    else:
                        route = '/offers'
                        connection.request('POST', route, json.dumps({
                            'scenarioId': 'enterprise-mdl' if index % 3 == 1 else 'enterprise-mdl-authorized',
                            'platform': 'IOS',
                        }), {'Content-Type': 'application/json'})
                    response = connection.getresponse()
                    payload = json.loads(response.read())
                    record['requests'].append({'route': route, 'status': response.status,
                                               'seconds': round(time.monotonic() - request_started, 3)})
                    assert response.status == 200
                    if route == '/offers':
                        assert payload['offerUrl']
            finally:
                connection.close()
            record['result'] = 'passed'
        except Exception as error:
            record['result'] = 'failed'
            record['error_type'] = type(error).__name__
            record['error'] = str(error)
        finally:
            process.terminate()
            try:
                process.wait(timeout=10)
            except subprocess.TimeoutExpired:
                process.kill()
                process.wait(timeout=10)
            process.stdin.close()
            record['cleanup_exit'] = process.returncode
    results.append(record)
    (ROOT / 'fixture-control-results.json').write_text(json.dumps(results, indent=2) + '\n')
    print(json.dumps({key: value for key, value in record.items() if key != 'requests'}), flush=True)
    if record['result'] != 'passed':
        raise SystemExit(1)
