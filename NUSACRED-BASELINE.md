# nusacred-lab controlled baseline

Upstream: https://github.com/walt-id/waltid-identity
Tag: v1.2.0
Commit: ef516ecec4c79fd9fba6f1e8b226b52a4e8cf790
Target branch: codex/baseline-v1.2.0; upstream main is not the build baseline.

LICENSE, NOTICE.md and THIRD-PARTY-NOTICE.md remain unchanged. Project additions
use Apache-2.0. The upstream third-party notice is an inventory, not proof that
the selected target artifacts and their packaged license texts have been audited.

Imported workflows are preserved under .github/quarantined-workflows/upstream-v1.2.0/
and are not executable workflows. They include mutable action tags, publishing,
Docker credentials, cloud deployment, schedules, upstream composite checkout and
cross-repository assumptions. Only the new read-only project workflows may run.
No upstream secrets were copied. The original main branch is retained as history;
never run its imported workflows or merge it into the controlled baseline blindly.

G1 is pending until resolved dependencies, strict verification, target image scans,
SBOMs and a real issuance/presentation run against those exact images all pass.
Bootstrap metadata is not automatically trusted and cannot authorize deployment.
