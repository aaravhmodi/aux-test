# Aux FL Studio Bridge

MVP bridge for controlling FL Studio from Aux.

The design mirrors the Reaper bridge:

- `fl_script/` runs inside FL Studio as a MIDI Controller Script.
- `bridge/` runs outside FL Studio in the normal Aux Python environment.
- FL exposes a local JSON socket server at `127.0.0.1:9001`.
- Aux registers the `fl_*` MCP tools and talks to FL through the bridge client.

## Files

```text
aux-fl/
├── fl_script/
│   ├── device_Aux.py
│   ├── server.py
│   ├── api.py
│   └── dispatcher.py
├── bridge/
│   ├── __init__.py
│   ├── client.py
│   └── mcp_tools.py
├── install.py
├── test_bridge.py
└── requirements.txt
```

## Setup

```powershell
cd "C:\Users\upsid\Documents\projects\aux project\aux-fl"
py -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
python install.py
```

Then in FL Studio:

1. Open `Options > MIDI Settings`.
2. Set controller type to `Aux`.
3. Enable the script.
4. Confirm FL logs: `[Aux] Bridge started on localhost:9001`.

If `Aux` does not appear, close and reopen FL Studio. User scripts must have a
`#name=...` line at the top of `device_*.py`; `device_Aux.py` declares
`#name=Aux`.

## Test

```powershell
python test_bridge.py
```

The test reads the current project state and sets tempo to `140`.

## Wire Into Aux MCP

Register the FL tools alongside your existing Reaper tools:

```python
from bridge.mcp_tools import TOOLS as FL_TOOLS, connect as fl_connect

fl_connect()
server.register_tools(FL_TOOLS)
```

## Phase 1 Tools

- `fl_get_state`
- `fl_set_mixer_volume`
- `fl_set_mixer_pan`
- `fl_mute_track`
- `fl_set_channel_volume`
- `fl_set_channel_pan`
- `fl_set_channel_pitch`
- `fl_mute_channel`
- `fl_set_tempo`
- `fl_play`
- `fl_stop`
- `fl_jump_to_pattern`

## Notes

FL Studio's script runtime should stay stdlib-only. Put third-party packages in
the outside-FL Aux environment, not in `fl_script/`.
