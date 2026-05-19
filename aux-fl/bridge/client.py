"""Client for the Aux FL Studio socket bridge."""

from __future__ import annotations

import json
import socket
import threading
from typing import Any


class FLBridgeError(RuntimeError):
    """Raised when the FL bridge returns an error response."""


class FLClient:
    def __init__(self, host: str = "127.0.0.1", port: int = 9001, timeout: float = 5.0):
        self.host = host
        self.port = port
        self.timeout = timeout
        self._sock: socket.socket | None = None
        self._lock = threading.Lock()

    def connect(self) -> None:
        if self.connected:
            return

        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(self.timeout)
        try:
            sock.connect((self.host, self.port))
        except Exception:
            sock.close()
            raise

        self._sock = sock

    def disconnect(self) -> None:
        if self._sock:
            self._sock.close()
            self._sock = None

    @property
    def connected(self) -> bool:
        return self._sock is not None

    def call(self, command: str, args: dict[str, Any] | None = None) -> dict[str, Any]:
        if not self._sock:
            self.connect()

        assert self._sock is not None
        payload = json.dumps({"command": command, "args": args or {}}) + "\n"

        with self._lock:
            try:
                self._sock.sendall(payload.encode("utf-8"))
                response = self._read_response()
            except Exception:
                self.disconnect()
                raise

        return response

    def _read_response(self) -> dict[str, Any]:
        assert self._sock is not None

        raw = b""
        while not raw.endswith(b"\n"):
            chunk = self._sock.recv(4096)
            if not chunk:
                raise ConnectionError("FL bridge disconnected")
            raw += chunk

        return json.loads(raw.decode("utf-8").strip())

    def require_ok(self, response: dict[str, Any]) -> Any:
        if response.get("ok"):
            return response.get("result")
        raise FLBridgeError(str(response.get("error", "Unknown FL bridge error")))

    def get_state(self) -> dict[str, Any]:
        return self.call("get_state")

    def set_mixer_volume(self, track: int, volume: float) -> dict[str, Any]:
        return self.call("set_mixer_volume", {"track": track, "volume": volume})

    def set_mixer_pan(self, track: int, pan: float) -> dict[str, Any]:
        return self.call("set_mixer_pan", {"track": track, "pan": pan})

    def mute_track(self, track: int, muted: bool) -> dict[str, Any]:
        return self.call("mute_track", {"track": track, "muted": muted})

    def set_channel_volume(self, channel: int, volume: float) -> dict[str, Any]:
        return self.call("set_channel_volume", {"channel": channel, "volume": volume})

    def set_channel_pan(self, channel: int, pan: float) -> dict[str, Any]:
        return self.call("set_channel_pan", {"channel": channel, "pan": pan})

    def set_channel_pitch(self, channel: int, semitones: float) -> dict[str, Any]:
        return self.call(
            "set_channel_pitch",
            {"channel": channel, "semitones": semitones},
        )

    def mute_channel(self, channel: int, muted: bool) -> dict[str, Any]:
        return self.call("mute_channel", {"channel": channel, "muted": muted})

    def set_tempo(self, bpm: float) -> dict[str, Any]:
        return self.call("set_tempo", {"bpm": bpm})

    def play(self) -> dict[str, Any]:
        return self.call("play")

    def stop(self) -> dict[str, Any]:
        return self.call("stop")

    def jump_to_pattern(self, index: int) -> dict[str, Any]:
        return self.call("jump_to_pattern", {"index": index})
