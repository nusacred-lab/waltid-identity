"""Use real API2 HTTP endpoints; publish only a fixed-schema outcome."""
import json
import os
from pathlib import Path
import sys
from walt import new_wallet, offer, resolve_offer, accept, session, preview, present, info

stage = "wallet"
try:
    wallet, key = new_wallet()
    stage = "offer"
    resolved = resolve_offer(wallet, offer()["credentialOffer"])
    stage = "issuance"
    accept(wallet, key, resolved)
    stage = "preview"
    request = session()
    selection = preview(wallet, request["bootstrapAuthorizationRequestUrl"])
    if selection.get("valid") is not True or not selection.get("credentialOptions"):
        raise ValueError("Invalid preview")
    stage = "presentation"
    response = present(wallet, request["bootstrapAuthorizationRequestUrl"],
                       selection["credentialOptions"][0], selection["keyId"])
    if response.get("transmission_success") is not True:
        raise ValueError("Transmission failed")
    stage = "verification"
    result = info(request["sessionId"])
    if result.get("status") != "SUCCESSFUL":
        raise ValueError("Verifier did not accept presentation")
except Exception:
    # Exception messages/response bodies may contain access-bearing protocol data.
    print("FAIL: real credential flow at stage " + stage, file=sys.stderr)
    sys.exit(1)

Path(os.environ["HARNESS_REPORT"]).write_text(json.dumps({
    "schemaVersion": 1, "syntheticData": True, "realHttpServices": True,
    "issuance": "passed", "walletStorage": "passed", "preview": "passed",
    "holderBoundPresentation": "passed", "verification": "passed"
}, indent=2) + "\n")
print("PASS: real issuance, wallet storage and holder-bound presentation verified")
