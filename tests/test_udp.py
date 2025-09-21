import unittest
import time
import ctypes
from backend.bindings import core_lib, ON_MESSAGE_RECEIVED_FUNC

received_data = None

def mock_callback(message, sender_ip):
    global received_data
    received_data = {
        "message": message.decode('utf-8'),
        "sender_ip": sender_ip.decode('utf-8')
    }

class TestUdpCore(unittest.TestCase):
    def test_send_receive_loopback(self):
        global received_data
        received_data = None

        test_port = 9999
        test_message = "hello_world"

        c_callback = ON_MESSAGE_RECEIVED_FUNC(mock_callback)
        core_lib.start_udp_listener(test_port, c_callback)
        time.sleep(0.1)
        core_lib.send_udp_message(test_message.encode('utf-8'), b'127.0.0.1', test_port)
        time.sleep(0.1)

        self.assertIsNotNone(received_data)
        self.assertEqual(received_data["message"], test_message)
        self.assertEqual(received_data["sender_ip"], "127.0.0.1")

if __name__ == '__main__':
    print("Run this after building the C++ core library.")
