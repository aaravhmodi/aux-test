"""Smoke test for the Aux FL Studio socket bridge.

Run this after FL Studio is open and the Aux MIDI Controller Script is enabled.
"""

from __future__ import annotations

from bridge.client import FLClient


def main() -> int:
    fl = FLClient()

    print("Connecting to FL Studio on 127.0.0.1:9001...")
    try:
        fl.connect()
    except ConnectionRefusedError:
        print("FL bridge not detected. Open FL Studio and enable the Aux MIDI script.")
        return 1
    except OSError as exc:
        print(f"Could not connect to FL bridge: {exc}")
        return 1

    print("Connected.")

    state_response = fl.get_state()
    if not state_response.get("ok"):
        print(f"Error reading state: {state_response.get('error')}")
        return 1

    state = state_response["result"]
    print()
    print(f"Tempo:    {state['tempo']} BPM")
    print(f"Playing:  {state['is_playing']}")
    print(f"Tracks:   {[track['name'] for track in state['mixer']]}")
    print(f"Channels: {[channel['name'] for channel in state['channels']]}")
    print(f"Patterns: {[pattern['name'] for pattern in state['patterns']]}")

    print()
    print("Setting tempo to 140...")
    tempo_response = fl.set_tempo(140)
    print("OK" if tempo_response.get("ok") else f"Failed: {tempo_response.get('error')}")

    fl.disconnect()
    print("Done.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
