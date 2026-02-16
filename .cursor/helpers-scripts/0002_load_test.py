#!/usr/bin/env python3
"""Load test: execute workflow with ~5000-word meditation text."""
import json
import sys
import time
import urllib.request
import http.cookiejar

import os

N8N_URL = os.environ.get("N8N_URL", "http://localhost:5678")
EMAIL = os.environ.get("N8N_EMAIL", "admin@local.dev")
PASSWORD = os.environ.get("N8N_PASSWORD", "changeme")

# ~500 words per paragraph, 10 paragraphs = ~5000 words
LONG_TEXT = """Take a deep breath in through your nose, filling your lungs completely, and hold it for just a moment before slowly releasing it through your mouth. Feel the warmth of each exhale as it carries away the tension you have been holding in your body. With every breath, you are becoming more and more relaxed, more and more at peace with yourself and the world around you. Let your shoulders drop, let your jaw unclench, let your hands rest gently in your lap. You are safe here. You are protected. There is nothing that needs your attention right now, nothing that requires your effort or your worry. This moment belongs entirely to you, and you can use it however you choose. Choose to be still. Choose to be calm. Choose to simply exist in this quiet space where nothing is demanded of you and everything is offered freely.

Now bring your attention to the sensation of your body resting where it is. Feel the weight of gravity holding you gently to the earth, connecting you to something vast and ancient and unchanging. The ground beneath you has supported countless souls before you, and it will support countless more after you are gone. But right now, in this precise moment, it supports you. It holds you without judgment, without expectation, without any desire other than to keep you safe and grounded. Let yourself sink into that support. Let yourself trust that you are held. You do not need to hold yourself up right now. You do not need to be strong or brave or composed. You can simply be exactly as you are, with all of your imperfections and all of your beauty, and the earth will hold you just the same.

Imagine now that you are standing at the edge of a vast, still lake. The water stretches out before you in every direction, its surface so smooth and undisturbed that it perfectly mirrors the sky above. The sky is a deep, endless blue, dotted with soft white clouds that drift slowly from one horizon to the other. The air is warm and gentle, carrying the faint scent of wildflowers and fresh grass. You can hear the distant call of birds, the quiet rustle of leaves in a breeze so soft you can barely feel it on your skin. This place is yours. It exists for you and only you, a sanctuary that you can return to whenever you need to find peace. Step forward now, and let your feet touch the cool water at the lake's edge. Feel how the water welcomes you, how it parts gently around your ankles as you wade in slowly, step by careful step.

As you walk deeper into the water, feel it rise around your calves, then your knees, then your thighs. It is neither cold nor warm, but exactly the perfect temperature, as though this lake was created specifically for you in this moment. The water supports your weight as you continue forward, and you feel yourself becoming lighter with each step. The worries that you carried with you to this shore are dissolving now, melting away like morning frost in the first rays of sunlight. Your responsibilities, your fears, your regrets, your anxieties, all of them are being washed clean by this sacred water. Let them go. You do not need them here. This is a place of pure peace and absolute freedom, and in this place, you are whole and complete exactly as you are.

Now lower yourself gently into the water until you are floating on your back, looking up at the infinite sky above. Your body is weightless, held by the water as easily as a leaf. Your arms float at your sides, your legs drift apart, and every muscle in your body releases its last remnant of tension. You are floating in perfect stillness, in perfect peace. The sky above you is vast and open, stretching endlessly in every direction, and you realize that this vastness mirrors something inside of you. There is a space within you that is just as infinite, just as open, just as full of possibility. In your daily life, this space might get crowded with thoughts and emotions and obligations, but right now it is clear and empty and beautiful.

Listen now to the sound of your own heartbeat. Feel it pulsing steadily in your chest, a rhythm that has been with you since before you were born, a rhythm that connects you to every living being on this planet. Your heart beats in time with the hearts of billions of others, all of us sharing this brief, precious experience of being alive. There is a profound comfort in this connection, a deep sense of belonging that transcends all of the divisions and separations that the mind creates. You are not alone in this world. You are part of something infinitely larger than yourself, a great web of life that stretches across time and space, connecting all beings in a dance of mutual dependence and mutual love. Rest in that knowledge. Let it fill you with warmth and gratitude.

As you float here on this still, sacred water, I want you to think about something you are grateful for. It does not have to be something large or impressive. It might be the warmth of sunlight on your face, or the laughter of someone you love, or the simple pleasure of a good meal shared with friends. Whatever comes to mind, hold it gently in your heart and let yourself feel the full weight of your gratitude. Gratitude is one of the most powerful forces in the universe. It has the ability to transform suffering into acceptance, fear into courage, and loneliness into connection. When you practice gratitude regularly, you begin to see the world differently. You begin to notice the countless small blessings that surround you every day, and your life becomes richer and more meaningful as a result.

Now imagine that your gratitude is a warm, golden light that begins to glow in the center of your chest. With each breath, this light grows brighter and stronger, expanding outward through your body until it fills every cell, every organ, every fiber of your being. This golden light is healing and protective. It dissolves any remaining tension or negativity that may be lingering in your body, replacing it with warmth and love and peace. Feel this light radiating from your heart center, extending beyond the boundaries of your physical body, reaching out into the world around you. It touches the water beneath you, the sky above you, the trees and flowers on the distant shore. Everything it touches is blessed and transformed.

Take another deep breath now, and as you inhale, draw this golden light back into your body, concentrating it once again in your heart center. This light will stay with you when you leave this place. It will accompany you through your daily life, providing comfort and strength whenever you need it. All you have to do is close your eyes, take a deep breath, and remember this moment, this feeling of floating in perfect peace on a still and sacred lake. The peace is always available to you. It lives within you, in that infinite space at the center of your being. No matter what challenges you face, no matter how turbulent the world around you becomes, you can always return to this place of stillness and find the calm that you need to carry on.

Slowly now, begin to bring your awareness back to the present moment. Feel the weight of your body once again, the sensation of the surface beneath you. Wiggle your fingers and toes gently. Take a deep breath in, and as you exhale, open your eyes softly. You are back in the room, but the peace of the lake is still with you. Carry it with you through the rest of your day. Carry it with you through the rest of your life. You are at peace. You are whole. You are loved. And you are exactly where you need to be. Take one final deep breath, and when you are ready, return fully to the world around you, refreshed and renewed and ready to embrace whatever comes next with grace and courage and an open heart."""

def main():
    workflow_id = sys.argv[1] if len(sys.argv) > 1 else "DDIG1GP3G9rst9w1"

    word_count = len(LONG_TEXT.split())
    char_count = len(LONG_TEXT)
    expected_chunks = (char_count // 2500) + 1
    print(f"Load test: {word_count} words, {char_count} chars, ~{expected_chunks} chunks expected")

    cj = http.cookiejar.CookieJar()
    opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(cj))

    # Login
    data = json.dumps({"emailOrLdapLoginId": EMAIL, "password": PASSWORD}).encode()
    req = urllib.request.Request(f"{N8N_URL}/rest/login", data=data, headers={"Content-Type": "application/json"})
    opener.open(req)

    # Fetch workflow
    req = urllib.request.Request(f"{N8N_URL}/rest/workflows/{workflow_id}")
    resp = opener.open(req)
    wf = json.loads(resp.read()).get("data", {})

    # Replace the input text
    for node in wf["nodes"]:
        if node["name"] == "Set Input Text":
            node["parameters"]["assignments"]["assignments"][0]["value"] = LONG_TEXT
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
        print(f"HTTP {e.code}: {e.read().decode()[:300]}")
        sys.exit(1)

    exec_id = result.get("data", {}).get("executionId")
    if not exec_id:
        print(f"No execution ID: {json.dumps(result)[:300]}")
        sys.exit(1)

    print(f"Execution started: {exec_id}")
    start = time.time()

    for attempt in range(120):
        time.sleep(3)
        req = urllib.request.Request(f"{N8N_URL}/rest/executions/{exec_id}")
        resp = opener.open(req)
        ex = json.loads(resp.read()).get("data", {})
        status = ex.get("status", "unknown")
        finished = ex.get("finished", False)
        elapsed = time.time() - start
        sys.stdout.write(f"\r  [{elapsed:.0f}s] Status: {status}      ")
        sys.stdout.flush()

        if finished or status in ("success", "error", "crashed"):
            print(f"\n\nCompleted in {elapsed:.1f}s with status: {status}")
            break
    else:
        print("\nTimeout after 6 min")
        sys.exit(1)

    # Check output file
    import subprocess
    result = subprocess.run(
        ["docker", "exec", "n8n", "ls", "-la", "/home/node/.n8n/meditation_final.mp3"],
        capture_output=True, text=True
    )
    print(f"Output file: {result.stdout.strip()}")

    size_bytes = int(result.stdout.split()[4]) if result.returncode == 0 else 0
    size_mb = size_bytes / (1024 * 1024)
    print(f"File size: {size_mb:.2f} MB")
    print(f"Expected chunks: {expected_chunks}")

if __name__ == "__main__":
    main()
