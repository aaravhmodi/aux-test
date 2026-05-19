# Aux FL Studio — MVP Start Guide

## What We're Building

Same concept as the Reaper bridge:
- A Python process that talks to FL Studio
- FL exposes state (tracks, tempo, patterns, channels)
- Aux reads that state and sends commands back
- Your existing Next.js frontend and MCP agent loop plug in unchanged

The only difference from Reaper: FL has no native HTTP API so we use FL's
MIDI Controller Script system as the bridge layer instead.

---

## Repo Structure

Start fresh, wire into Aux later.

```
aux-fl/
├── fl_script/                  # Runs INSIDE FL Studio
│   ├── device_Aux.py           # FL entry point (must be named device_*.py)
│   ├── server.py               # Socket RPC server
│   ├── api.py                  # FL internal API wrappers
│   └── dispatcher.py           # Maps command strings to API calls
│
├── bridge/                     # Runs OUTSIDE FL, on Aux side
│   ├── client.py               # Connects to FL socket
│   └── mcp_tools.py            # Wraps client as MCP tools
│
├── install.py                  # One-shot installer
├── test_bridge.py              # Quick test script
└── requirements.txt
```

---

## Step 1 — Create the Repo

```bash
mkdir aux-fl && cd aux-fl
git init
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install mcp                 # your existing MCP library
touch requirements.txt
```

`requirements.txt`:
```
mcp
```

That's it for dependencies. Everything else uses FL's built-in Python runtime
(inside the script) and stdlib (outside).

---

## Step 2 — Write the FL Script

These four files go in `fl_script/`. They run inside FL's Python runtime,
not your venv — so no third-party imports, stdlib only.

### `fl_script/api.py`

Thin wrappers around every FL internal module we need. This is the only file
that touches FL internals directly.

```python
# fl_script/api.py
import channels
import mixer
import transport
import patterns


# ── READ ──────────────────────────────────────────────────────────────────────

def get_state():
    return {
        "tempo":         transport.getTempo(),
        "is_playing":    transport.isPlaying(),
        "song_pos":      transport.getSongPos(),
        "master_volume": mixer.getTrackVolume(0),
        "mixer":         _get_mixer(),
        "channels":      _get_channels(),
        "patterns":      _get_patterns(),
    }


def _get_mixer():
    count = mixer.trackCount()
    tracks = []
    for i in range(min(count, 64)):
        tracks.append({
            "index":  i,
            "name":   mixer.getTrackName(i),
            "volume": mixer.getTrackVolume(i),
            "pan":    mixer.getTrackPan(i),
            "muted":  not mixer.isTrackEnabled(i),
        })
    return tracks


def _get_channels():
    count = channels.channelCount()
    result = []
    for i in range(count):
        result.append({
            "index":  i,
            "name":   channels.getChannelName(i),
            "volume": channels.getChannelVolume(i),
            "pan":    channels.getChannelPan(i),
            "muted":  channels.isChannelMuted(i),
            "pitch":  channels.getChannelPitch(i),
        })
    return result


def _get_patterns():
    count = patterns.patternCount()
    result = []
    for i in range(count):
        result.append({
            "index":  i,
            "name":   patterns.getPatternName(i),
            "length": patterns.getPatternLength(i),
        })
    return result


# ── WRITE ─────────────────────────────────────────────────────────────────────

def set_mixer_volume(track: int, volume: float):
    mixer.setTrackVolume(track, max(0.0, min(1.0, volume)))

def set_mixer_pan(track: int, pan: float):
    mixer.setTrackPan(track, max(-1.0, min(1.0, pan)))

def mute_track(track: int, muted: bool):
    mixer.muteTrack(track) if muted else mixer.enableTrack(track)

def set_channel_volume(channel: int, volume: float):
    channels.setChannelVolume(channel, max(0.0, min(1.0, volume)))

def set_channel_pitch(channel: int, semitones: float):
    channels.setChannelPitch(channel, max(-48.0, min(48.0, semitones)))

def mute_channel(channel: int, muted: bool):
    channels.muteChannel(channel, muted)

def set_tempo(bpm: float):
    transport.setTempo(max(40.0, min(999.0, bpm)))

def play():
    transport.start()

def stop():
    transport.stop()

def jump_to_pattern(index: int):
    patterns.jumpToPattern(index)
```

---

### `fl_script/dispatcher.py`

Maps incoming command strings to api.py calls. Add new commands here as you
expand.

```python
# fl_script/dispatcher.py
import api

COMMANDS = {
    "get_state":          lambda a: api.get_state(),
    "set_mixer_volume":   lambda a: api.set_mixer_volume(a["track"], a["volume"]),
    "set_mixer_pan":      lambda a: api.set_mixer_pan(a["track"], a["pan"]),
    "mute_track":         lambda a: api.mute_track(a["track"], a["muted"]),
    "set_channel_volume": lambda a: api.set_channel_volume(a["channel"], a["volume"]),
    "set_channel_pitch":  lambda a: api.set_channel_pitch(a["channel"], a["semitones"]),
    "mute_channel":       lambda a: api.mute_channel(a["channel"], a["muted"]),
    "set_tempo":          lambda a: api.set_tempo(a["bpm"]),
    "play":               lambda a: api.play(),
    "stop":               lambda a: api.stop(),
    "jump_to_pattern":    lambda a: api.jump_to_pattern(a["index"]),
}


def dispatch(command: str, args: dict) -> dict:
    if command not in COMMANDS:
        return {"ok": False, "error": f"Unknown command: {command}"}
    try:
        result = COMMANDS[command](args)
        return {"ok": True, "result": result}
    except Exception as e:
        return {"ok": False, "error": str(e)}
```

---

### `fl_script/server.py`

Socket RPC server that runs in a background thread inside FL. Newline-delimited
JSON — one command in, one response out.

```python
# fl_script/server.py
import socket
import threading
import json
import dispatcher

_server_socket = None
_running = False


def start(port: int = 9001):
    global _server_socket, _running
    _server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    _server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    _server_socket.bind(("127.0.0.1", port))
    _server_socket.listen(5)
    _running = True
    print(f"[Aux] Listening on 127.0.0.1:{port}")

    while _running:
        try:
            conn, _ = _server_socket.accept()
            threading.Thread(target=_handle, args=(conn,), daemon=True).start()
        except OSError:
            break


def stop():
    global _running
    _running = False
    if _server_socket:
        try:
            _server_socket.close()
        except Exception:
            pass


def _handle(conn):
    buffer = b""
    with conn:
        while True:
            data = conn.recv(4096)
            if not data:
                break
            buffer += data
            while b"\n" in buffer:
                line, buffer = buffer.split(b"\n", 1)
                try:
                    msg = json.loads(line.decode())
                    result = dispatcher.dispatch(
                        msg.get("command", ""),
                        msg.get("args", {}),
                    )
                    conn.sendall(json.dumps(result).encode() + b"\n")
                except json.JSONDecodeError:
                    conn.sendall(
                        json.dumps({"ok": False, "error": "Invalid JSON"}).encode() + b"\n"
                    )
```

---

### `fl_script/device_Aux.py`

The FL entry point. FL identifies controller scripts by the `device_` prefix.
This file must be named exactly `device_Aux.py`.

```python
# fl_script/device_Aux.py
# FL Studio loads this as a MIDI controller script.
# Named device_Aux.py so FL lists it as "Aux" in MIDI settings.

import threading
import server

_thread = None


def OnInit():
    """FL calls this when the script loads."""
    global _thread
    _thread = threading.Thread(target=server.start, args=(9001,), daemon=True)
    _thread.start()
    print("[Aux] Bridge started on localhost:9001")


def OnDeInit():
    """FL calls this when the script unloads or FL closes."""
    server.stop()
    print("[Aux] Bridge stopped")


def OnMidiMsg(event):
    """Required by FL even if unused."""
    event.handled = False
```

---

## Step 3 — Write the Bridge Client

This runs outside FL in your normal Python environment.

### `bridge/client.py`

```python
# bridge/client.py
import socket
import json
import threading
from typing import Any


class FLClient:
    def __init__(self, host: str = "127.0.0.1", port: int = 9001):
        self.host = host
        self.port = port
        self._sock = None
        self._lock = threading.Lock()

    def connect(self):
        self._sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self._sock.connect((self.host, self.port))
        self._sock.settimeout(5.0)

    def disconnect(self):
        if self._sock:
            self._sock.close()
            self._sock = None

    @property
    def connected(self) -> bool:
        return self._sock is not None

    def call(self, command: str, args: dict = {}) -> Any:
        with self._lock:
            msg = json.dumps({"command": command, "args": args}) + "\n"
            self._sock.sendall(msg.encode())
            raw = b""
            while not raw.endswith(b"\n"):
                chunk = self._sock.recv(4096)
                if not chunk:
                    raise ConnectionError("FL bridge disconnected")
                raw += chunk
            return json.loads(raw.strip())

    # Convenience methods
    def get_state(self):
        return self.call("get_state")

    def set_mixer_volume(self, track: int, volume: float):
        return self.call("set_mixer_volume", {"track": track, "volume": volume})

    def set_mixer_pan(self, track: int, pan: float):
        return self.call("set_mixer_pan", {"track": track, "pan": pan})

    def mute_track(self, track: int, muted: bool):
        return self.call("mute_track", {"track": track, "muted": muted})

    def set_channel_volume(self, channel: int, volume: float):
        return self.call("set_channel_volume", {"channel": channel, "volume": volume})

    def set_channel_pitch(self, channel: int, semitones: float):
        return self.call("set_channel_pitch", {"channel": channel, "semitones": semitones})

    def mute_channel(self, channel: int, muted: bool):
        return self.call("mute_channel", {"channel": channel, "muted": muted})

    def set_tempo(self, bpm: float):
        return self.call("set_tempo", {"bpm": bpm})

    def play(self):
        return self.call("play")

    def stop(self):
        return self.call("stop")

    def jump_to_pattern(self, index: int):
        return self.call("jump_to_pattern", {"index": index})
```

---

### `bridge/mcp_tools.py`

Drop these into your existing MCP server the same way your Reaper tools are
registered. The agent loop doesn't change at all.

```python
# bridge/mcp_tools.py
from client import FLClient

fl = FLClient()


def connect():
    fl.connect()


TOOLS = [
    {
        "name": "fl_get_state",
        "description": (
            "Get the full current state of the FL Studio project: "
            "tempo, transport, mixer tracks, channels, and patterns."
        ),
        "input_schema": {"type": "object", "properties": {}},
        "handler": lambda args: fl.get_state(),
    },
    {
        "name": "fl_set_mixer_volume",
        "description": "Set the volume of a mixer track in FL Studio.",
        "input_schema": {
            "type": "object",
            "properties": {
                "track":  {"type": "integer", "description": "Mixer track index. 0 = master."},
                "volume": {"type": "number",  "description": "0.0 (silent) to 1.0 (full)"},
            },
            "required": ["track", "volume"],
        },
        "handler": lambda args: fl.set_mixer_volume(args["track"], args["volume"]),
    },
    {
        "name": "fl_set_mixer_pan",
        "description": "Set the pan of a mixer track.",
        "input_schema": {
            "type": "object",
            "properties": {
                "track": {"type": "integer"},
                "pan":   {"type": "number", "description": "-1.0 (left) to 1.0 (right)"},
            },
            "required": ["track", "pan"],
        },
        "handler": lambda args: fl.set_mixer_pan(args["track"], args["pan"]),
    },
    {
        "name": "fl_mute_track",
        "description": "Mute or unmute a mixer track.",
        "input_schema": {
            "type": "object",
            "properties": {
                "track": {"type": "integer"},
                "muted": {"type": "boolean"},
            },
            "required": ["track", "muted"],
        },
        "handler": lambda args: fl.mute_track(args["track"], args["muted"]),
    },
    {
        "name": "fl_set_channel_pitch",
        "description": "Set the pitch of a channel/instrument in semitones.",
        "input_schema": {
            "type": "object",
            "properties": {
                "channel":   {"type": "integer"},
                "semitones": {"type": "number", "description": "-48 to 48"},
            },
            "required": ["channel", "semitones"],
        },
        "handler": lambda args: fl.set_channel_pitch(args["channel"], args["semitones"]),
    },
    {
        "name": "fl_set_tempo",
        "description": "Set the project tempo in BPM.",
        "input_schema": {
            "type": "object",
            "properties": {
                "bpm": {"type": "number", "description": "40 to 999"},
            },
            "required": ["bpm"],
        },
        "handler": lambda args: fl.set_tempo(args["bpm"]),
    },
    {
        "name": "fl_play",
        "description": "Start FL Studio playback.",
        "input_schema": {"type": "object", "properties": {}},
        "handler": lambda args: fl.play(),
    },
    {
        "name": "fl_stop",
        "description": "Stop FL Studio playback.",
        "input_schema": {"type": "object", "properties": {}},
        "handler": lambda args: fl.stop(),
    },
]
```

---

## Step 4 — Installer

Detects FL's scripts folder and copies the four files in.

```python
# install.py
import os
import shutil
import sys

FILES = [
    "fl_script/device_Aux.py",
    "fl_script/server.py",
    "fl_script/api.py",
    "fl_script/dispatcher.py",
]

def fl_script_path():
    base = os.path.expanduser("~/Documents/Image-Line/FL Studio/Settings/Hardware")
    return os.path.join(base, "Aux")

def install():
    dest = fl_script_path()
    os.makedirs(dest, exist_ok=True)

    for src in FILES:
        filename = os.path.basename(src)
        shutil.copy(src, os.path.join(dest, filename))
        print(f"  ✓ {filename} → {dest}")

    print("\nInstalled. Now in FL Studio:")
    print("  Options → MIDI Settings → Controller type → Aux → Enable")
    print("  You should see '[Aux] Bridge started on localhost:9001' in FL's log")

if __name__ == "__main__":
    install()
```

---

## Step 5 — Test Script

Run this after FL has the script loaded to confirm the bridge is working
end to end before touching the MCP layer.

```python
# test_bridge.py
from bridge.client import FLClient

fl = FLClient()

print("Connecting to FL Studio...")
fl.connect()
print("Connected.\n")

# Read state
state = fl.get_state()
if not state["ok"]:
    print(f"Error: {state['error']}")
    exit(1)

s = state["result"]
print(f"Tempo:    {s['tempo']} BPM")
print(f"Playing:  {s['is_playing']}")
print(f"Tracks:   {[t['name'] for t in s['mixer']]}")
print(f"Channels: {[c['name'] for c in s['channels']]}")
print(f"Patterns: {[p['name'] for p in s['patterns']]}")

# Quick write test
print("\nSetting tempo to 140...")
r = fl.set_tempo(140)
print("OK" if r["ok"] else f"Failed: {r['error']}")

print("\nMuting mixer track 1...")
r = fl.mute_track(1, True)
print("OK" if r["ok"] else f"Failed: {r['error']}")

fl.disconnect()
print("\nDone.")
```

---

## Running It

```bash
# 1. Install the script into FL
python install.py

# 2. Open FL Studio
# 3. Options → MIDI Settings → Controller type → Aux → Enable
#    You'll see "[Aux] Bridge started on localhost:9001" in FL's console

# 4. Test the bridge
python test_bridge.py

# 5. Wire mcp_tools.py into your existing MCP server
#    Same pattern as your Reaper tools — just different tool names
```

---

## Wiring Into Your Existing Aux MCP Server

Your Reaper bridge probably registers tools something like:

```python
# Your existing pattern (Reaper)
from reaper_bridge.mcp_tools import TOOLS as REAPER_TOOLS
server.register_tools(REAPER_TOOLS)
```

FL plugs in the same way:

```python
# Add FL tools alongside Reaper
from bridge.mcp_tools import TOOLS as FL_TOOLS, connect as fl_connect
fl_connect()
server.register_tools(FL_TOOLS)
```

The agent loop, approval diff, and frontend don't change at all.
The agent just has more tools available and uses `fl_*` prefixed ones
when the user is on FL.

---

## What Works After Phase 1

| Can Do | Can't Do Yet |
|---|---|
| Read full project state | Move clips on playlist |
| Set mixer volumes and pan | Plugin parameter access |
| Mute/unmute mixer tracks | Render / export |
| Set channel volume and pitch | Automation curve editing |
| Mute/unmute channels | |
| Set tempo | |
| Play / stop transport | |
| Jump between patterns | |

Phase 2 adds `pyflp` for project file parsing (plugin params, playlist layout).
Phase 3 adds `pywinauto` UI automation for render and clip movement.

---

## Gotchas

- **FL's Python runtime is sandboxed** — no pip installs inside the script,
  stdlib only. All your real dependencies stay in your venv on the outside.
- **FL must be open** for the socket to exist. Your client should handle
  `ConnectionRefusedError` gracefully and show a "FL not detected" state
  in the UI — same as your Reaper "no project" state.
- **FL on Mac** puts scripts in the same path but UAC/permissions can be
  trickier. Test on Windows first where FL usage is highest anyway.
- **Restart the script** after code changes by toggling the controller off
  and on in FL's MIDI settings — FL doesn't hot-reload scripts.
