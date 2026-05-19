"""MCP-style tool definitions for the FL Studio bridge.

Import TOOLS into your existing Aux MCP server and register them the same way
you register the Reaper bridge tools.
"""

from __future__ import annotations

from .client import FLClient

fl = FLClient()


def connect() -> None:
    fl.connect()


def _empty_schema() -> dict:
    return {"type": "object", "properties": {}}


TOOLS = [
    {
        "name": "fl_get_state",
        "description": (
            "Get the current FL Studio project state: tempo, transport, mixer "
            "tracks, channels, and patterns."
        ),
        "input_schema": _empty_schema(),
        "handler": lambda args: fl.get_state(),
    },
    {
        "name": "fl_set_mixer_volume",
        "description": "Set the volume of a mixer track in FL Studio.",
        "input_schema": {
            "type": "object",
            "properties": {
                "track": {"type": "integer", "description": "Mixer track index. 0 is master."},
                "volume": {"type": "number", "description": "0.0 silent to 1.0 full."},
            },
            "required": ["track", "volume"],
        },
        "handler": lambda args: fl.set_mixer_volume(args["track"], args["volume"]),
    },
    {
        "name": "fl_set_mixer_pan",
        "description": "Set the pan of a mixer track in FL Studio.",
        "input_schema": {
            "type": "object",
            "properties": {
                "track": {"type": "integer"},
                "pan": {"type": "number", "description": "-1.0 left to 1.0 right."},
            },
            "required": ["track", "pan"],
        },
        "handler": lambda args: fl.set_mixer_pan(args["track"], args["pan"]),
    },
    {
        "name": "fl_mute_track",
        "description": "Mute or unmute an FL Studio mixer track.",
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
        "name": "fl_set_channel_volume",
        "description": "Set the volume of an FL Studio channel.",
        "input_schema": {
            "type": "object",
            "properties": {
                "channel": {"type": "integer"},
                "volume": {"type": "number", "description": "0.0 silent to 1.0 full."},
            },
            "required": ["channel", "volume"],
        },
        "handler": lambda args: fl.set_channel_volume(args["channel"], args["volume"]),
    },
    {
        "name": "fl_set_channel_pan",
        "description": "Set the pan of an FL Studio channel.",
        "input_schema": {
            "type": "object",
            "properties": {
                "channel": {"type": "integer"},
                "pan": {"type": "number", "description": "-1.0 left to 1.0 right."},
            },
            "required": ["channel", "pan"],
        },
        "handler": lambda args: fl.set_channel_pan(args["channel"], args["pan"]),
    },
    {
        "name": "fl_set_channel_pitch",
        "description": "Set a channel or instrument pitch in semitones.",
        "input_schema": {
            "type": "object",
            "properties": {
                "channel": {"type": "integer"},
                "semitones": {"type": "number", "description": "-48 to 48."},
            },
            "required": ["channel", "semitones"],
        },
        "handler": lambda args: fl.set_channel_pitch(args["channel"], args["semitones"]),
    },
    {
        "name": "fl_mute_channel",
        "description": "Mute or unmute an FL Studio channel.",
        "input_schema": {
            "type": "object",
            "properties": {
                "channel": {"type": "integer"},
                "muted": {"type": "boolean"},
            },
            "required": ["channel", "muted"],
        },
        "handler": lambda args: fl.mute_channel(args["channel"], args["muted"]),
    },
    {
        "name": "fl_set_tempo",
        "description": "Set the FL Studio project tempo in BPM.",
        "input_schema": {
            "type": "object",
            "properties": {
                "bpm": {"type": "number", "description": "40 to 999."},
            },
            "required": ["bpm"],
        },
        "handler": lambda args: fl.set_tempo(args["bpm"]),
    },
    {
        "name": "fl_play",
        "description": "Start FL Studio playback.",
        "input_schema": _empty_schema(),
        "handler": lambda args: fl.play(),
    },
    {
        "name": "fl_stop",
        "description": "Stop FL Studio playback.",
        "input_schema": _empty_schema(),
        "handler": lambda args: fl.stop(),
    },
    {
        "name": "fl_jump_to_pattern",
        "description": "Jump to an FL Studio pattern by index.",
        "input_schema": {
            "type": "object",
            "properties": {
                "index": {"type": "integer"},
            },
            "required": ["index"],
        },
        "handler": lambda args: fl.jump_to_pattern(args["index"]),
    },
]
