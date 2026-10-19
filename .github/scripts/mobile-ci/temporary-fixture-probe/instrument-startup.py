"""Temporary native startup evidence for the unchanged Enterprise iOS execution path."""
from pathlib import Path
import hashlib
import sys

root = Path(sys.argv[1])
build = root / 'waltid-enterprise-integration-tests/build.gradle.kts'
source = build.read_text()

def replace_once(old, new):
    global source
    assert source.count(old) == 1, f'Expected one anchor: {old[:80]}'
    source = source.replace(old, new, 1)

replace_once('import java.util.concurrent.TimeUnit', 'import java.util.concurrent.TimeUnit\nimport java.time.Instant')

helper = '''fun captureFixtureProcessState(fixture: Process?, logFile: File) {
    val commands = linkedMapOf(
        "processes" to listOf("/bin/ps", "-axo", "pid,ppid,pgid,stat,etime,time,%cpu,rss,comm"),
        "memory" to listOf("/usr/bin/vm_stat"),
    )
    if (fixture != null && fixture.isAlive) {
        commands["sample"] = listOf("/usr/bin/sample", fixture.pid().toString(), "3", "10", "-file",
            logFile.resolveSibling("${logFile.nameWithoutExtension}-native-sample.log").absolutePath)
    }
    for ((name, command) in commands) {
        val output = logFile.resolveSibling("${logFile.nameWithoutExtension}-$name.log")
        val capture = ProcessBuilder(command).redirectErrorStream(true).redirectOutput(output).start()
        try {
            val completed = capture.waitFor(15, TimeUnit.SECONDS)
            logger.lifecycle("FIXTURE_PROBE ${Instant.now()} $name completed=$completed exit=${if (completed) capture.exitValue() else null}")
        } finally {
            if (capture.isAlive) {
                capture.destroyForcibly()
                capture.waitFor(5, TimeUnit.SECONDS)
            }
        }
    }
}

'''
replace_once('fun captureEnterpriseMobileFixtureThreads(fixture: Process, logFile: File) {',
             helper + 'fun captureEnterpriseMobileFixtureThreads(fixture: Process, logFile: File) {')
replace_once('    val fixture = startEnterpriseMobileFixtureProcess(logFile)', '''    captureFixtureProcessState(null, logFile.resolveSibling("${logFile.nameWithoutExtension}-before.log"))
    logger.lifecycle("FIXTURE_PROBE ${Instant.now()} spawning fixture")
    val fixture = startEnterpriseMobileFixtureProcess(logFile)''')
replace_once('    logger.lifecycle("Enterprise mobile fixture started (pid ${fixture.pid()})")',
             '    logger.lifecycle("Enterprise mobile fixture started (pid ${fixture.pid()}) at ${Instant.now()}")')
replace_once('''        } catch (failure: Exception) {
            runCatching { captureEnterpriseMobileFixtureThreads(fixture, logFile) }''', '''        } catch (failure: Exception) {
            logger.lifecycle("FIXTURE_PROBE ${Instant.now()} readiness failed; alive=${fixture.isAlive}")
            runCatching { captureFixtureProcessState(fixture, logFile) }
                .onFailure { logger.warn("Native startup evidence unavailable", it) }
            runCatching { captureEnterpriseMobileFixtureThreads(fixture, logFile) }
                .onFailure { logger.warn("JVM startup evidence unavailable", it) }''')
build.write_text(source)

main = root / 'waltid-enterprise-integration-tests/src/main/kotlin/id/walt/enterprise/test/integration/mobile/EnterpriseMobileFixtureServer.kt'
text = main.read_text()
anchor = 'fun main(args: Array<String>) {\n'
assert text.count(anchor) == 1
main.write_text(text.replace(anchor, anchor + '    println("FIXTURE_PROBE ${Instant.now()} entered fixture main")\n', 1))
for path in (build, main):
    print(f'{hashlib.sha256(path.read_bytes()).hexdigest()}  {path.relative_to(root)}')
