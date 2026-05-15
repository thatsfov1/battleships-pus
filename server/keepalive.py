import threading
import time
import uuid
import logging
from . import protocol

def start_keepalive_thread(conn, stop_event):
    thread = threading.Thread(
        target=_keepalive_loop,
        args=(conn, stop_event),
        daemon=True,
        name=f"Keepalive-{conn.getpeername() if hasattr(conn, 'getpeername') else 'unknown'}"
    )
    thread.start()
    return thread

def _keepalive_loop(conn, stop_event):
    while not stop_event.is_set():
        try:
            time.sleep(10)
            if stop_event.is_set():
                break
            
            protocol.send_message(conn, {
                "type": "PING",
                "msg_id": str(uuid.uuid4()),
                "timestamp": time.time()
            })
        except Exception:
            break
