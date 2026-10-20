"""Require exact reviewed frontend manifests and registry archive integrities."""
import hashlib
import json
from pathlib import Path
from urllib.parse import unquote, urlparse

apps = ("waltid-credentials", "waltid-web-portal2", "waltid-digital-credentials")
ledger = json.loads(Path("ci/npm-dependency-review.json").read_text())

def require(condition, message):
    if not condition:
        raise SystemExit(message)

expected_files = {f"waltid-applications/{app}/{name}" for app in apps
                  for name in ("package.json", "package-lock.json", ".npmrc")}
require(set(ledger["manifestFiles"]) == expected_files, "Frontend manifest inventory changed without review")
for name, expected in ledger["manifestFiles"].items():
    require(hashlib.sha256(Path(name).read_bytes()).hexdigest() == expected, "Frontend manifest changed: " + name)

reviewed = {}
for item in ledger["artifacts"]:
    url = urlparse(item["url"])
    require(url.scheme == "https" and url.hostname == "registry.npmjs.org"
            and not url.username and not url.query and not url.fragment, "Unreviewed npm registry")
    require(item["method"] == "official-registry-metadata-and-download-sha512", "Unrecognized npm review method")
    require(item["integrity"].startswith("sha512-") and " " not in item["integrity"], "Strong npm integrity required")
    key = (item["url"], item["integrity"])
    require(key not in reviewed, "Duplicate npm review entry")
    reviewed[key] = item

expected = set()
for app in apps:
    packages = json.loads(Path(f"waltid-applications/{app}/package-lock.json").read_text())["packages"]
    for path, item in packages.items():
        if not path:
            continue
        if item.get("inBundle"):
            parent = path.rsplit("/node_modules/", 1)[0]
            parent_item = packages[parent]
            review = reviewed[(parent_item["resolved"], parent_item["integrity"])]
            child_path = path[len(parent) + 1:]
            matches = [child for child in review["reviewedBundled"]
                       if child["path"] == child_path and child["version"] == item["version"]]
            require(len(matches) == 1, "Bundled npm component requires archive review")
            continue
        key = (item["resolved"], item["integrity"])
        require(key in reviewed, "Unreviewed npm archive")
        review = reviewed[key]
        actual_name = unquote(urlparse(item["resolved"]).path.lstrip("/").split("/-/")[0])
        require((review["name"], review["version"]) == (actual_name, item["version"]), "npm component identity changed")
        expected.add(key)
require(set(reviewed) == expected, "npm review must exactly match all three frontend lock inventories")
print(f"PASS: {len(reviewed)} independently downloaded npm archives and three frontend manifest sets match")
