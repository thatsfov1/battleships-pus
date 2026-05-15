import unittest
import socket
import threading
import time
import json
import ssl
from server.session import SessionManager
from server.handlers import ClientSession

class MockConn:
    def __init__(self):
        self.sent_messages = []
        self.timeout = None
        self.closed = False

    def sendall(self, data):
        self.sent_messages.append(json.loads(data.decode('utf-8').strip()))

    def recv(self, size):
        return b""

    def settimeout(self, value):
        self.timeout = value

    def close(self):
        self.closed = True

    def getpeername(self):
        return ("127.0.0.1", 12345)

class TestKeepalive(unittest.TestCase):
    def test_ack_mechanism(self):
        sm = SessionManager()
        conn = MockConn()
        session = ClientSession(conn, ("127.0.0.1", 12345), sm)
        msg_id = "test-id-123"
        session._send_ack(msg_id)
        
        self.assertTrue(any(m["type"] == "ACK" and m["msg_id"] == msg_id for m in conn.sent_messages))

    def test_timeout_configuration(self):
        sm = SessionManager()
        conn = MockConn()
        session = ClientSession(conn, ("127.0.0.1", 12345), sm)
        
        def mock_receive(*args):
            raise socket.timeout()
        
        import server.protocol
        original_recv = server.protocol.receive_message
        server.protocol.receive_message = mock_receive
        
        try:
            session.handle()
            self.assertEqual(conn.timeout, 30.0)
        finally:
            server.protocol.receive_message = original_recv

if __name__ == "__main__":
    unittest.main()
