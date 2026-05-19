"""Map socket RPC commands to FL API calls."""

import api


COMMANDS = {
    "get_state": lambda args: api.get_state(),
    "set_mixer_volume": lambda args: api.set_mixer_volume(
        args["track"], args["volume"]
    ),
    "set_mixer_pan": lambda args: api.set_mixer_pan(args["track"], args["pan"]),
    "mute_track": lambda args: api.mute_track(args["track"], args["muted"]),
    "set_channel_volume": lambda args: api.set_channel_volume(
        args["channel"], args["volume"]
    ),
    "set_channel_pan": lambda args: api.set_channel_pan(args["channel"], args["pan"]),
    "set_channel_pitch": lambda args: api.set_channel_pitch(
        args["channel"], args["semitones"]
    ),
    "mute_channel": lambda args: api.mute_channel(args["channel"], args["muted"]),
    "set_tempo": lambda args: api.set_tempo(args["bpm"]),
    "play": lambda args: api.play(),
    "stop": lambda args: api.stop(),
    "jump_to_pattern": lambda args: api.jump_to_pattern(args["index"]),
}


def dispatch(command, args):
    if command not in COMMANDS:
        return {"ok": False, "error": "Unknown command: {0}".format(command)}

    try:
        return {"ok": True, "result": COMMANDS[command](args or {})}
    except KeyError as exc:
        return {"ok": False, "error": "Missing argument: {0}".format(exc)}
    except Exception as exc:
        return {"ok": False, "error": str(exc)}
