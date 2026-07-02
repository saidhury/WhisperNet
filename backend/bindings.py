import ctypes
import os
import platform
import sys

def get_lib_path():
    meipass = getattr(sys, "_MEIPASS", None)
    if meipass:
        search_dirs = [
            os.path.join(meipass, "backend", "lib"),
            os.path.join(meipass, "lib"),
            meipass
        ]
    else:
        base_dir = os.path.dirname(__file__)
        search_dirs = [
            os.path.join(base_dir, "lib", "Release"),
            os.path.join(base_dir, "lib", "Debug"),
            os.path.join(base_dir, "lib"),
            base_dir
        ]

    filename = "whispernet_core.dll"
    if platform.system() == "Darwin":
        filename = "libwhispernet_core.dylib"
    elif platform.system() != "Windows":
        filename = "libwhispernet_core.so"

    for directory in search_dirs:
        candidate = os.path.join(directory, filename)
        if os.path.exists(candidate):
            return candidate

    return os.path.join(os.path.dirname(__file__), "lib", "Debug", filename)

lib_path = get_lib_path()

if platform.system() == "Windows" and hasattr(os, 'add_dll_directory'):
    lib_dir = os.path.dirname(lib_path)
    try:
        os.add_dll_directory(lib_dir)
    except FileNotFoundError:
        pass

try:
    # winmode=0 tells Python >=3.8 to load dependencies normally
    core_lib = ctypes.CDLL(lib_path, winmode=0)
except Exception as e:
    print("WARNING: Could not load core library, using fallback mock. Error:", e)
    import threading
    import socket as _socket

    class _Fallback:
        def __init__(self):
            self._listener_thread = None
            self._sock = None
            self._running = False

        def start_udp_listener(self, port, callback):
            if self._running: return 8888
            self._running = True
            self._sock = _socket.socket(_socket.AF_INET, _socket.SOCK_DGRAM)
            try: self._sock.bind(("", port))
            except Exception: pass

            def _listen():
                while self._running:
                    try:
                        data, addr = self._sock.recvfrom(65535)
                        sender_ip = addr[0].encode('utf-8')
                        try: callback(data, sender_ip, addr[1])
                        except Exception: pass
                    except Exception: break

            self._listener_thread = threading.Thread(target=_listen, daemon=True)
            self._listener_thread.start()
            return port

        def stop_udp_listener(self):
            self._running = False
            if self._sock:
                try: self._sock.close()
                except Exception: pass
                self._sock = None

        def send_udp_message(self, message_bytes, addr_bytes, port):
            addr = addr_bytes.decode('utf-8') if isinstance(addr_bytes, (bytes, bytearray)) else str(addr_bytes)
            s = _socket.socket(_socket.AF_INET, _socket.SOCK_DGRAM)
            try:
                s.setsockopt(_socket.SOL_SOCKET, _socket.SO_BROADCAST, 1)
                s.sendto(message_bytes, (addr, port))
            except Exception: pass
            finally: s.close()

        def send_broadcast_message(self, message_bytes, port):
            self.send_udp_message(message_bytes, b"255.255.255.255", port)

        def join_multicast_group(self, multicast_ip_bytes):
            return 1

        def get_local_ip(self, out_buffer, max_len):
            try:
                ip_bytes = b"127.0.0.1"
                out_buffer[:len(ip_bytes)] = ip_bytes
                return 1
            except:
                return 0

    core_lib = _Fallback()

ON_MESSAGE_RECEIVED_FUNC = ctypes.CFUNCTYPE(None, ctypes.c_char_p, ctypes.c_char_p, ctypes.c_int)

try:
    core_lib.start_udp_listener.argtypes = [ctypes.c_int, ON_MESSAGE_RECEIVED_FUNC]
    core_lib.start_udp_listener.restype = ctypes.c_int
    
    core_lib.send_udp_message.argtypes = [ctypes.c_char_p, ctypes.c_char_p, ctypes.c_int]

    core_lib.send_broadcast_message.argtypes = [ctypes.c_char_p, ctypes.c_int]
    
    core_lib.join_multicast_group.argtypes = [ctypes.c_char_p]
    core_lib.join_multicast_group.restype = ctypes.c_int
    
    core_lib.get_local_ip.argtypes = [ctypes.c_char_p, ctypes.c_int]
    core_lib.get_local_ip.restype = ctypes.c_int
except Exception:
    pass