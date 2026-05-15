from __future__ import annotations

import json
import socket
import unittest
from unittest.mock import patch

from server import protocol


class ProtocolTests(unittest.TestCase):
    def setUp(self) -> None:
        protocol._recent_message_ids.clear()

    def test_send_message_serializes_json_with_newline_delimiter(self) -> None:
        left, right = socket.socketpair()
        try:
            message = {"type": "PING", "msg_id": "1", "timestamp": 123.45}

            protocol.send_message(left, message)

            raw = right.recv(4096)
            self.assertTrue(raw.endswith(b"\n"))
            self.assertEqual(json.loads(raw.rstrip(b"\n").decode("utf-8")), message)
        finally:
            left.close()
            right.close()

    def test_receive_message_deserializes_json_message(self) -> None:
        left, right = socket.socketpair()
        try:
            message = {"type": "PING", "msg_id": "1", "timestamp": 123.45}
            left.sendall(json.dumps(message).encode("utf-8") + b"\n")

            self.assertEqual(protocol.receive_message(right), message)
        finally:
            left.close()
            right.close()

    def test_receive_message_returns_error_for_invalid_json(self) -> None:
        self.assert_receive_error(b"{not-json}\n", protocol.INVALID_JSON)

    def test_receive_message_returns_error_for_non_dict_json(self) -> None:
        payload = json.dumps(["not", "a", "dict"]).encode("utf-8") + b"\n"

        self.assert_receive_error(payload, protocol.INVALID_TYPE)

    def test_receive_message_returns_error_for_missing_required_field(self) -> None:
        payload = json.dumps({"type": "PING", "timestamp": 123.45}).encode("utf-8") + b"\n"

        self.assert_receive_error(payload, protocol.INVALID_TYPE)

    def test_receive_message_detects_duplicate_msg_id_within_ttl(self) -> None:
        first, second = socket.socketpair()
        try:
            message = {"type": "PING", "msg_id": "duplicate-id", "timestamp": 123.45}
            protocol.send_message(first, message)
            self.assertEqual(protocol.receive_message(second), message)

            protocol.send_message(first, {**message, "timestamp": 124.45})
            self.assertEqual(
                protocol.receive_message(second),
                {"type": "ERROR", "code": protocol.DUPLICATE_MESSAGE},
            )
        finally:
            first.close()
            second.close()

    def test_receive_message_allows_same_msg_id_after_ttl(self) -> None:
        current_time = 1000.0

        with patch.object(protocol.time, "time", side_effect=lambda: current_time):
            first, second = socket.socketpair()
            try:
                message = {"type": "PING", "msg_id": "old-id", "timestamp": 123.45}
                protocol.send_message(first, message)
                self.assertEqual(protocol.receive_message(second), message)

                current_time += protocol.MESSAGE_ID_TTL_SECONDS + 1
                second_message = {**message, "timestamp": 124.45}
                protocol.send_message(first, second_message)
                self.assertEqual(protocol.receive_message(second), second_message)
            finally:
                first.close()
                second.close()

    def assert_receive_error(self, payload: bytes, code: str) -> None:
        left, right = socket.socketpair()
        try:
            left.sendall(payload)

            self.assertEqual(protocol.receive_message(right), {"type": "ERROR", "code": code})
        finally:
            left.close()
            right.close()


if __name__ == "__main__":
    unittest.main()
