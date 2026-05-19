"""Newline-delimited JSON socket server that runs inside FL Studio."""

import json
import os
import socket
import threading
import time
import traceback

import dispatcher

HOST = "127.0.0.1"
PORT = 9001
LOG_PATH = os.path.join(os.path.dirname(__file__), "aux_debug.log")

_server_socket = None
_running = False


def _log(message):
    try:
        with open(LOG_PATH, "a") as log_file:
            log_file.write(
                "{0} {1}\n".format(
                    time.strftime("%Y-%m-%d %H:%M:%S"),
                    message,
                )
            )
    except Exception:
        pass


def start(port=PORT):
    global _server_socket, _running

    if _running:
        _log("Bridge already running")
        print("[Aux] Bridge already running")
        return

    try:
        _server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        _server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        _server_socket.bind((HOST, int(port)))
        _server_socket.listen(5)
    except Exception:
        _log("Failed to start socket:")
        _log(traceback.format_exc())
        raise

    _running = True
    _log("[Aux] Listening on {0}:{1}".format(HOST, port))
    print("[Aux] Listening on {0}:{1}".format(HOST, port))

    while _running:
        try:
            connection, _address = _server_socket.accept()
        except OSError:
            break

        thread = threading.Thread(target=_handle_client, args=(connection,))
        thread.daemon = True
        thread.start()


def stop():
    global _running, _server_socket

    _log("Stopping bridge")
    _running = False
    if _server_socket:
        try:
            _server_socket.close()
        except Exception:
            pass
        _server_socket = None


def _handle_client(connection):
    buffer = b""
    with connection:
        while _running:
            try:
                chunk = connection.recv(4096)
            except OSError:
                break

            if not chunk:
                break

            buffer += chunk
            while b"\n" in buffer:
                line, buffer = buffer.split(b"\n", 1)
                _handle_message(connection, line)


def _handle_message(connection, line):
    try:
        message = json.loads(line.decode("utf-8"))
        response = dispatcher.dispatch(
            message.get("command", ""),
            message.get("args", {}),
        )
    except ValueError:
        response = {"ok": False, "error": "Invalid JSON"}
    except Exception as exc:
        response = {"ok": False, "error": str(exc)}

    payload = json.dumps(response).encode("utf-8") + b"\n"
    connection.sendall(payload)
