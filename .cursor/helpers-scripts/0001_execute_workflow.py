#!/usr/bin/env python3
"""Execute an n8n workflow via the internal REST API."""
import json
import sys
import time
import urllib.request
import http.cookiejar

import os

N8N_URL = os.environ.get("N8N_URL", "http://localhost:5678")
EMAIL = os.environ.get("N8N_EMAIL", "admin@local.dev")
PASSWORD = os.environ.get("N8N_PASSWORD", "changeme")

def api(opener, method, path, data=None):
    body = json.dumps(data).encode() if data else None
    req = urllib.request.Request(f"{N8N_URL}{path}", data=body, method=method,
                                 headers={"Content-Type": "application/json"} if body else {})
    try:
        resp = opener.open(req)
        return json.loads(resp.read()), resp.status
    except urllib.error.HTTPError as e:
        err = e.read().decode()
        try:
            return json.loads(err), e.code
        except:
            return {"raw": err[:500]}, e.code

def main():
    workflow_id = sys.argv[1] if len(sys.argv) > 1 else "b5fwhjUNVH3zIw3p"

    cj = http.cookiejar.CookieJar()
    opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(cj))

    # Login
    result, code = api(opener, "POST", "/rest/login",
                       {"emailOrLdapLoginId": EMAIL, "password": PASSWORD})
    print(f"Login: {'OK' if result.get('data',{}).get('id') else 'FAILED'}")

    # Fetch workflow
    result, code = api(opener, "GET", f"/rest/workflows/{workflow_id}")
    wf = result.get("data", result)
    print(f"Workflow: {wf['name']} ({len(wf['nodes'])} nodes)")

    # Try multiple payload formats for manual execution
    payloads = [
        {
            "workflowData": wf,
            "runData": {},
            "pinData": {},
            "startNodes": [{"name": "Manual Trigger", "sourceData": None}],
            "destinationNode": ""
        },
        {
            "workflowData": wf,
            "runData": {},
            "pinData": wf.get("pinData", {}),
            "startNodes": [],
            "destinationNode": "",
            "triggerToStartFrom": {"name": "Manual Trigger", "data": {}}
        },
        {
            "workflowData": wf,
            "runData": {},
            "pinData": wf.get("pinData", {}),
            "startNodes": [{"name": "Manual Trigger", "sourceData": None}],
        },
    ]

    exec_id = None
    for i, payload in enumerate(payloads):
        print(f"\nAttempt {i+1}...")
        result, code = api(opener, "POST", f"/rest/workflows/{workflow_id}/run", payload)
        if code == 200 and "data" in result:
            exec_id = result["data"].get("executionId")
            print(f"  Execution started! ID: {exec_id}")
            break
        else:
            msg = result.get("message", str(result)[:200])
            print(f"  HTTP {code}: {msg}")

    if not exec_id:
        print("\nAll payload formats failed. Exiting.")
        sys.exit(1)

    # Poll for completion
    print(f"\nPolling execution {exec_id}...")
    for attempt in range(60):
        time.sleep(3)
        result, code = api(opener, "GET", f"/rest/executions/{exec_id}")
        ex = result.get("data", result)
        status = ex.get("status", "unknown")
        finished = ex.get("finished", False)
        sys.stdout.write(f"\r  [{attempt+1}] Status: {status}, Finished: {finished}    ")
        sys.stdout.flush()

        if finished or status in ("success", "error", "crashed", "canceled"):
            print()
            run_data = ex.get("data", {}).get("resultData", {}).get("runData", {})
            print(f"\n--- Node Results ---")
            for node_name, node_runs in run_data.items():
                for run in node_runs:
                    has_error = run.get("error")
                    items_out = 0
                    if run.get("data", {}).get("main"):
                        for branch in run["data"]["main"]:
                            if branch:
                                items_out += len(branch)
                    status_str = "ERROR" if has_error else f"OK ({items_out} items)"
                    print(f"  {node_name}: {status_str}")
                    if has_error:
                        err_msg = has_error.get("message", str(has_error))
                        print(f"    -> {err_msg[:300]}")

            # Check for final output file info
            if "Binary Merge" in run_data:
                last = run_data["Binary Merge"][-1]
                if last.get("data", {}).get("main"):
                    for item in last["data"]["main"][0]:
                        j = item.get("json", {})
                        if j:
                            print(f"\n--- Merged Output ---")
                            print(f"  File: {j.get('fileName','?')}")
                            print(f"  Size: {j.get('size_mb','?')} MB")
                            print(f"  Chunks: {j.get('chunks_merged','?')}")
            break
    else:
        print("\n\nTimeout waiting for execution (3 min).")

if __name__ == "__main__":
    main()
