#!/usr/bin/env python3
"""Edge case tests for the Meditation TTS Pipeline."""
import json
import sys
import time
import urllib.request
import http.cookiejar

import os

N8N_URL = os.environ.get("N8N_URL", "http://localhost:5678")
EMAIL = os.environ.get("N8N_EMAIL", "admin@local.dev")
PASSWORD = os.environ.get("N8N_PASSWORD", "changeme")

EDGE_CASES = [
    {
        "name": "Empty input",
        "text": "",
        "expect_error": True,
        "expect_message": "empty or too short"
    },
    {
        "name": "Too short input",
        "text": "Hello.",
        "expect_error": True,
        "expect_message": "empty or too short"
    },
    {
        "name": "Single sentence",
        "text": "Breathe deeply and let the calmness of this moment fill your entire being with peace and tranquility.",
        "expect_error": False,
    },
    {
        "name": "Heavy markdown",
        "text": "## Welcome to Meditation\n\n**Take a deep breath** and _relax your body_. ~~Forget your worries~~ and [click here](https://example.com) to find inner peace. Let the **bold** and _italic_ words guide you to a place of stillness and calm.",
        "expect_error": False,
    },
    {
        "name": "Text with emojis",
        "text": "Take a deep breath in and feel the peace surrounding you. Let go of all tension and stress from your day. You are safe and protected in this moment of calm reflection and inner harmony.",
        "expect_error": False,
    },
]

def run_with_text(opener, workflow_id, text):
    """Execute workflow with custom text, return (status, error_msg_or_none)."""
    # Fetch workflow
    req = urllib.request.Request(f"{N8N_URL}/rest/workflows/{workflow_id}")
    resp = opener.open(req)
    wf = json.loads(resp.read()).get("data", {})

    # Replace input text
    for node in wf["nodes"]:
        if node["name"] == "Set Input Text":
            node["parameters"]["assignments"]["assignments"][0]["value"] = text
            break

    # Execute
    run_body = json.dumps({
        "workflowData": wf,
        "runData": {},
        "pinData": {},
        "startNodes": [{"name": "Manual Trigger", "sourceData": None}],
        "destinationNode": ""
    }).encode()
    req = urllib.request.Request(
        f"{N8N_URL}/rest/workflows/{workflow_id}/run",
        data=run_body,
        headers={"Content-Type": "application/json"}
    )
    try:
        resp = opener.open(req)
        result = json.loads(resp.read())
    except urllib.error.HTTPError as e:
        return "http_error", e.read().decode()[:200]

    exec_id = result.get("data", {}).get("executionId")
    if not exec_id:
        return "no_exec_id", str(result)[:200]

    # Poll
    for _ in range(60):
        time.sleep(2)
        req = urllib.request.Request(f"{N8N_URL}/rest/executions/{exec_id}")
        resp = opener.open(req)
        ex = json.loads(resp.read()).get("data", {})
        status = ex.get("status", "unknown")
        finished = ex.get("finished", False)

        if finished or status in ("success", "error", "crashed"):
            # Try to get error from flatted data
            exec_data = ex.get("data", "{}")
            if isinstance(exec_data, str):
                exec_data = json.loads(exec_data)
            error_msg = None
            if isinstance(exec_data, list) and len(exec_data) > 22:
                arr = exec_data
                last_node = arr[8] if len(arr) > 8 else "unknown"
                potential_error = arr[22] if isinstance(arr[22], str) else None
                if status == "error" and potential_error:
                    error_msg = f"[{last_node}] {potential_error}"
            return status, error_msg

    return "timeout", None


def main():
    workflow_id = sys.argv[1] if len(sys.argv) > 1 else "DDIG1GP3G9rst9w1"

    cj = http.cookiejar.CookieJar()
    opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(cj))

    # Login
    data = json.dumps({"emailOrLdapLoginId": EMAIL, "password": PASSWORD}).encode()
    req = urllib.request.Request(f"{N8N_URL}/rest/login", data=data, headers={"Content-Type": "application/json"})
    opener.open(req)

    print("=" * 60)
    print("EDGE CASE TESTS")
    print("=" * 60)

    results = []
    for tc in EDGE_CASES:
        print(f"\n--- {tc['name']} ---")
        print(f"  Input: {repr(tc['text'][:80])}{'...' if len(tc['text']) > 80 else ''}")
        print(f"  Expect error: {tc['expect_error']}")

        status, error_msg = run_with_text(opener, workflow_id, tc["text"])
        print(f"  Status: {status}")
        if error_msg:
            print(f"  Error: {error_msg[:150]}")

        if tc["expect_error"]:
            passed = status == "error"
            if passed and tc.get("expect_message"):
                passed = tc["expect_message"].lower() in (error_msg or "").lower()
        else:
            passed = status == "success"

        verdict = "PASS" if passed else "FAIL"
        print(f"  Result: {verdict}")
        results.append((tc["name"], verdict))

    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)
    all_pass = True
    for name, verdict in results:
        mark = "+" if verdict == "PASS" else "-"
        print(f"  [{mark}] {name}: {verdict}")
        if verdict == "FAIL":
            all_pass = False

    print(f"\nOverall: {'ALL PASSED' if all_pass else 'SOME FAILED'}")
    sys.exit(0 if all_pass else 1)


if __name__ == "__main__":
    main()
