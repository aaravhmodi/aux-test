# name=Aux
"""FL Studio MIDI Controller Script entry point.

The device_ prefix is required so FL lists this script as "Aux" in MIDI
settings.
"""

import threading
import os
import time
import traceback

LOG_PATH = os.path.join(os.path.dirname(__file__), "aux_debug.log")


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


try:
    import server
except Exception:
    _log("Failed to import server:")
    _log(traceback.format_exc())
    raise

_log("device_Aux imported")

_thread = None


def OnInit():
    global _thread
    _log("OnInit called")

    if _thread and _thread.is_alive():
        _log("Bridge thread already alive")
        return

    _thread = threading.Thread(target=server.start, args=(9001,))
    _thread.daemon = True
    _thread.start()
    _log("Bridge thread started")
    print("[Aux] Bridge started on localhost:9001")


def OnDeInit():
    _log("OnDeInit called")
    server.stop()
    print("[Aux] Bridge stopped")


def OnMidiMsg(event):
    event.handled = False
