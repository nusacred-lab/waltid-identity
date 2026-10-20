"""Extract fixed failure categories; never publish arbitrary container log text."""
import json
from pathlib import Path
import sys

private, reports = map(Path, sys.argv[1:])
signatures = {
    "read_only_filesystem": "Read-only file system",
    "permission_denied": "Permission denied",
    "native_mapping_failed": "failed to map segment from shared object",
    "native_library_load_failed": "java.lang.UnsatisfiedLinkError",
    "sqlite_error": "org.sqlite.SQLiteException",
    "sqlite_cannot_open": "SQLITE_CANTOPEN",
    "sqlite_native_library_missing": "org.sqlite.NativeLibraryNotFoundException",
    "pool_initialization_failed": "PoolInitializationException",
    "missing_class": "java.lang.NoClassDefFoundError",
    "class_not_found": "java.lang.ClassNotFoundException",
    "missing_method": "java.lang.NoSuchMethodError",
    "initializer_failed": "java.lang.ExceptionInInitializerError",
    "duplicate_plugin": "DuplicatePluginException",
    "configuration_error": "ConfigurationException",
    "out_of_memory": "OutOfMemoryError",
}
matched = sorted({name for path in private.glob("*.log")
                  for text in [path.read_text(errors="replace")]
                  for name, signature in signatures.items() if signature in text})
reports.mkdir(parents=True, exist_ok=True)
(reports / "startup-diagnostics.json").write_text(json.dumps({
    "schemaVersion": 1, "failureCategories": matched,
    "rawContainerLogsPublished": False
}, indent=2) + "\n")
print("Startup diagnostic categories: " + (", ".join(matched) or "unclassified"))
