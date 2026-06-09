"""Most WebSocket <-> TCP/TLS dla klienta przegladarkowego (React).

Przegladarka nie potrafi otworzyc surowego gniazda TCP/TLS, dlatego React laczy
sie po WebSocket z tym mostem. Kazde polaczenie WebSocket utrzymuje jedno
polaczenie TLS do serwera gry (poprzez client.network.NetworkClient) i
transparentnie przekazuje komunikaty protokolu w obie strony.

Uruchomienie:  python ws_gateway.py     (domyslnie ws://localhost:8765)
"""

from __future__ import annotations

import json
import logging
import os
import threading

from websockets.sync.server import serve

from client.network import NetworkClient, DISCONNECTED

GW_HOST = os.getenv("GW_HOST", "localhost")
GW_PORT = int(os.getenv("GW_PORT", "8765"))
GAME_HOST = os.getenv("BS_HOST", "localhost")
GAME_PORT = int(os.getenv("BS_PORT", os.getenv("PORT", "5000")))


def _pump_server_to_ws(nc: NetworkClient, ws, stop: threading.Event) -> None:
    """Przekazuje wiadomosci z serwera gry do przegladarki."""
    while not stop.is_set():
        msg = nc.inbox.get()
        if msg.get("type") == DISCONNECTED:
            try:
                ws.close()
            except Exception:
                pass
            return
        try:
            ws.send(json.dumps(msg, ensure_ascii=False))
        except Exception:
            return


def handler(ws) -> None:
    nc = NetworkClient(host=GAME_HOST, port=GAME_PORT)
    try:
        nc.connect()
    except Exception as exc:
        logging.error(f"Most: nie udalo sie polaczyc z serwerem gry: {exc}")
        ws.close()
        return

    nc.start_keepalive()
    stop = threading.Event()
    pump = threading.Thread(target=_pump_server_to_ws, args=(nc, ws, stop), daemon=True)
    pump.start()
    logging.info("Most: nowe polaczenie WebSocket -> serwer gry")

    try:
        for raw in ws:
            try:
                data = json.loads(raw)
            except (json.JSONDecodeError, TypeError):
                continue
            if not isinstance(data, dict):
                continue
            mtype = data.pop("type", None)
            if not mtype:
                continue
            try:
                nc.send(mtype, **data)
            except Exception:
                break
    except Exception:
        pass
    finally:
        stop.set()
        nc.close()
        logging.info("Most: zamknieto polaczenie")


def main() -> None:
    logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
    logging.info(f"Most WS nasluchuje na ws://{GW_HOST}:{GW_PORT} -> gra {GAME_HOST}:{GAME_PORT}")
    with serve(handler, GW_HOST, GW_PORT) as server:
        server.serve_forever()


if __name__ == "__main__":
    main()
