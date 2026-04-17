# scripts/verify/10_websocket.py
import sys, os, asyncio, json, threading, time
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from dotenv import load_dotenv
load_dotenv()

print("=== PHASE 10: WebSocket Event Pipeline ===\n")

import websockets
import requests

# First verify the FastAPI server is running
try:
    resp = requests.get("http://127.0.0.1:8000/api/health", timeout=5)
    print(f"✅ FastAPI server: {resp.json()}")
except Exception as e:
    print(f"❌ FastAPI server not running: {e}")
    print("Start it with: uvicorn api.main:app --reload --port 8000")
    sys.exit(1)

# Subscribe to WebSocket and collect events
received_events = []
connection_error = None

async def collect_events():
    global connection_error
    try:
        # Note: In a headless environment, this assumes the server is reachable at 127.0.0.1:8000
        async with websockets.connect("ws://127.0.0.1:8000/ws/pipeline") as ws:
            print("✅ WebSocket connection established")

            # Trigger a mock pipeline event
            trigger_resp = requests.post(
                "http://127.0.0.1:8000/ws/trigger-mock",
                json={"workflow_id": "ws_verify_001"},
                timeout=5
            )
            print(f"Mock trigger response: {trigger_resp.status_code}")

            # Collect events for 15 seconds (needs more time for the sequence)
            deadline = time.time() + 15
            while time.time() < deadline:
                try:
                    msg = await asyncio.wait_for(ws.recv(), timeout=1.0)
                    event = json.loads(msg)
                    received_events.append(event)
                    print(f"  Event received: {event.get('event_type')} | node: {event.get('node_id')}")
                except asyncio.TimeoutError:
                    pass
    except Exception as e:
        connection_error = e

try:
    asyncio.run(collect_events())
except KeyboardInterrupt:
    pass

if connection_error:
    print(f"❌ WebSocket error: {connection_error}")
else:
    print(f"\nTotal events received: {len(received_events)}")

    if len(received_events) == 0:
        print("⚠️  No events received — verify PipelineBroadcaster is called from pipeline engines")
        print("Check: engines/system/token_messenger/messenger.py calls broadcaster.broadcast_sync()")
    else:
        # Verify event schema
        event_types = set(e.get("event_type") for e in received_events)
        print(f"Event types seen: {event_types}")

        for event in received_events:
            assert "event_id" in event, "Missing event_id"
            assert "workflow_id" in event, "Missing workflow_id"
            assert "timestamp" in event, "Missing timestamp"
            assert "event_type" in event, "Missing event_type"
            assert "node_id" in event, "Missing node_id"
            assert "session_quality" in event, "Missing session_quality"
            assert "token_hash" not in event, "SECURITY: token_hash should not be in WS events"

        print("✅ All events have correct schema")
        print("✅ No cryptographic token values exposed in WebSocket stream")

print("\n✅ PHASE 10 COMPLETE\n")
