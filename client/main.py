"""Klient CLI gry Statki: logowanie, lobby i rozgrywka w terminalu.

Uruchomienie:  python -m client.main  [host] [port]
"""

from __future__ import annotations

import hashlib
import sys
import time

from . import config
from . import game_ui
from .network import NetworkClient, DISCONNECTED

EMPTY = lambda: [["" for _ in range(game_ui.BOARD_SIZE)] for _ in range(game_ui.BOARD_SIZE)]
_HIT = ("HIT", "SUNK")


def _input(prompt: str) -> str:
    try:
        return input(prompt)
    except (EOFError, KeyboardInterrupt):
        raise SystemExit("\nPrzerwano.")


class GameClient:
    def __init__(self, host: str, port: int):
        self.client = NetworkClient(host=host, port=port)
        self.username: str = ""
        self.password_hash: str = ""
        self.own = EMPTY()
        self.tracking = EMPTY()
        self.current_turn = None
        self.over = False

    # --- logowanie ---------------------------------------------------------------

    def login_flow(self) -> bool:
        if not self.client.connect_with_retry():
            print(f"Nie udalo sie polaczyc z {self.client.host}:{self.client.port}.")
            return False
        if not self.client.cert_verified:
            print("UWAGA: certyfikat serwera nieweryfikowany (brak certs/server.crt).")

        for attempt in range(3):
            self.username = _input("Login: ").strip()
            password = _input("Haslo: ")
            self.password_hash = hashlib.sha256(password.encode("utf-8")).hexdigest()
            ok, info = self.client.login(self.username, self.password_hash)
            if ok:
                print(f"Zalogowano jako {self.username}.")
                self.client.start_keepalive()
                return True
            print(f"Logowanie nieudane: {info}")
        print("Przekroczono liczbe prob logowania.")
        return False

    # --- menu --------------------------------------------------------------------

    def menu_loop(self) -> None:
        while True:
            print("\n=== MENU ===")
            print("1) Utworz gre")
            print("2) Dolacz do gry")
            print("3) Wyjscie")
            choice = _input("Wybor: ").strip()
            if choice == "1":
                self._create_game()
            elif choice == "2":
                self._join_game()
            elif choice == "3":
                self.client.close()
                print("Do zobaczenia!")
                return
            else:
                print("Nieznana opcja.")

    def _create_game(self) -> None:
        self.client.send("CREATE_GAME")
        resp = self.client.wait_for({"GAME_CREATED", "ERROR"}, timeout=10)
        if resp is None or resp.get("type") == "ERROR":
            print("Nie udalo sie utworzyc gry:", (resp or {}).get("message", "brak odpowiedzi"))
            return
        print("Gra utworzona. Oczekiwanie na przeciwnika (Ctrl+C aby przerwac)...")
        try:
            start = self.client.wait_for({"GAME_START"}, timeout=3600)
        except KeyboardInterrupt:
            print("\nPowrot do menu.")
            return
        if start is None:
            print("Przeciwnik nie dolaczyl.")
            return
        self._play(start)

    def _join_game(self) -> None:
        self.client.send("JOIN_GAME")
        resp = self.client.wait_for({"GAME_START", "ERROR"}, timeout=10)
        if resp is None:
            print("Brak odpowiedzi serwera.")
            return
        if resp.get("type") == "ERROR":
            print("Nie mozna dolaczyc:", resp.get("message", "brak gier"))
            return
        self._play(resp)

    # --- rozgrywka ---------------------------------------------------------------

    def _load_state(self, msg: dict) -> None:
        self.own = msg.get("your_board") or EMPTY()
        if msg.get("tracking_board"):
            self.tracking = msg["tracking_board"]
        self.current_turn = msg.get("current_turn")

    def _play(self, start: dict) -> None:
        self.own = start.get("your_board") or EMPTY()
        self.tracking = EMPTY()
        self.current_turn = start.get("current_turn")
        self.over = False
        print("\n>>> GRA ROZPOCZETA <<<")

        while not self.over:
            print()
            print(game_ui.render_side_by_side(self.own, self.tracking))
            if self.current_turn == self.username:
                if not self._my_turn():
                    return
            else:
                print(f"Tura przeciwnika ({self.current_turn}). Czekam na ruch...")
                if not self._consume(self._next_event()):
                    return
        print("Powrot do menu.")

    def _next_event(self) -> dict:
        """Pobiera z inboxa pierwsza wiadomosc istotna dla rozgrywki,
        pomijajac komunikaty kontrolne (ACK/PONG)."""
        while True:
            msg = self.client.inbox.get()
            if msg.get("type") in ("ACK", "PONG"):
                continue
            return msg

    def _my_turn(self) -> bool:
        while True:
            raw = _input("Twoj strzal (np. B5), 'q' = wyjscie: ").strip()
            if raw.lower() in ("q", "quit", "exit"):
                self.client.close()
                raise SystemExit("Zakonczono gre.")
            coords = game_ui.parse_coords(raw)
            if coords is None:
                print("Niepoprawne wspolrzedne. Uzyj formatu kolumna+wiersz, np. C7.")
                continue
            x, y = coords
            if self.tracking[y][x] in _HIT or self.tracking[y][x] == "o":
                print("Juz strzelales w to pole.")
                continue
            self.client.send("MOVE", x=x, y=y)
            break
        return self._consume(self._next_event())

    def _consume(self, msg: dict) -> bool:
        """Przetwarza wiadomosc z inboxa. Zwraca False przy rozlaczeniu bez powrotu."""
        mtype = msg.get("type")
        if mtype == DISCONNECTED:
            return self._reconnect()
        if mtype in ("ACK", "PONG"):
            return True
        if mtype == "MOVE_RESULT":
            self._apply_move_result(msg)
        elif mtype == "GAME_END":
            self._apply_game_end(msg)
        elif mtype == "GAME_STATE":
            self._load_state(msg)
            print("Stan gry odtworzony.")
        elif mtype == "ERROR":
            print("Blad:", msg.get("message") or msg.get("code"))
        return True

    def _apply_move_result(self, msg: dict) -> None:
        x, y, result, by = msg.get("x"), msg.get("y"), msg.get("result"), msg.get("by")
        label = game_ui.coord_label(x, y)
        mark = "X" if result in _HIT else "o"
        if by == self.username:
            self.tracking[y][x] = mark
            print(f"Twoj strzal {label}: {result}")
        else:
            self.own[y][x] = mark
            print(f"Przeciwnik strzela {label}: {result}")
        self.current_turn = msg.get("next_turn")

    def _apply_game_end(self, msg: dict) -> None:
        self.over = True
        winner = msg.get("winner")
        reason = msg.get("reason", "")
        print("\n========================")
        if winner == self.username:
            print(f"ZWYCIESTWO! Wygrales ({reason}).")
        elif winner:
            print(f"PORAZKA. Wygrywa {winner} ({reason}).")
        else:
            print(f"Gra zakonczona: {reason}")
        print("========================")

    def _reconnect(self) -> bool:
        print("Utracono polaczenie. Proba ponownego polaczenia...")
        if not self.client.connect_with_retry():
            print("Reconnect nieudany. Powrot do menu.")
            return False
        ok, _ = self.client.login(self.username, self.password_hash)
        if not ok:
            print("Ponowne logowanie nieudane.")
            return False
        self.client.start_keepalive()
        self.client.send("JOIN_GAME")
        msg = self.client.wait_for({"GAME_STATE", "GAME_START", "ERROR"}, timeout=10)
        if msg and msg.get("type") in ("GAME_STATE", "GAME_START"):
            self._load_state(msg)
            print("Wznowiono gre.")
            return True
        print("Nie udalo sie wznowic gry (sesja mogla wygasnac).")
        return False


def run() -> None:
    host = sys.argv[1] if len(sys.argv) > 1 else config.HOST
    port = int(sys.argv[2]) if len(sys.argv) > 2 else config.PORT
    print(f"=== Statki — klient CLI === ({host}:{port})")
    gc = GameClient(host, port)
    try:
        if gc.login_flow():
            gc.menu_loop()
    except SystemExit as exc:
        print(exc)
    finally:
        gc.client.close()


if __name__ == "__main__":
    run()
