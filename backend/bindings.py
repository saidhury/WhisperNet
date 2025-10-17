import ctypes
import os
import platform

def get_lib_path():
    base_path = os.path.join(os.path.dirname(__file__), "lib", "Debug")
    if platform.system() == "Windows":
        return os.path.join(base_path, "whispernet_core.dll")
    elif platform.system() == "Darwin":
        base_path_nix = os.path.join(os.path.dirname(__file__), "lib")
        return os.path.join(base_path_nix, "libwhispernet_core.dylib")
    else:
        base_path_nix = os.path.join(os.path.dirname(__file__), "lib")
        return os.path.join(base_path_nix, "libwhispernet_core.so")

lib_path = get_lib_path()

if platform.system() == "Windows" and hasattr(os, 'add_dll_directory'):
    lib_dir = os.path.dirname(lib_path)
    try:
        os.add_dll_directory(lib_dir)
    except FileNotFoundError:
        pass

try:
    core_lib = ctypes.CDLL(lib_path)
except Exception as e:
    # In some test or dev environments the compiled core library won't exist.
    # Provide a lightweight fallback object with the same attributes so imports don't fail.
    print("WARNING: Could not load core library, using fallback mock. Error:", e)
    import threading
    import socket as _socket

    class _Fallback:
        def __init__(self):
            self._listener_thread = None
            self._sock = None
            self._running = False

        def start_udp_listener(self, port, callback):
            # callback is expected to be a ctypes CFUNCTYPE or callable taking (message, sender_ip)
            if self._running:
                return
            self._running = True
            self._sock = _socket.socket(_socket.AF_INET, _socket.SOCK_DGRAM)
            try:
                self._sock.bind(("", port))
            except Exception:
                # fallback bind may fail in some environments; ignore
                pass

            def _listen():
                while self._running:
                    try:
                        data, addr = self._sock.recvfrom(65535)
                        sender_ip = addr[0].encode('utf-8')
                        # Call the callback with bytes objects
                        try:
                            callback(data, sender_ip)
                        except Exception:
                            # callback may be a ctypes function expecting c_char_p; attempt conversion
                            try:
                                callback(ctypes.c_char_p(data), ctypes.c_char_p(sender_ip))
                            except Exception:
                                pass
                    except Exception:
                        break

            self._listener_thread = threading.Thread(target=_listen, daemon=True)
            self._listener_thread.start()

        def send_udp_message(self, message_bytes, addr_bytes, port):
            addr = addr_bytes.decode('utf-8') if isinstance(addr_bytes, (bytes, bytearray)) else str(addr_bytes)
            s = _socket.socket(_socket.AF_INET, _socket.SOCK_DGRAM)
            try:
                s.sendto(message_bytes, (addr, port))
            except Exception:
                # best-effort in fallback
                pass
            finally:
                try:
                    s.close()
                except Exception:
                    pass

    core_lib = _Fallback()

ON_MESSAGE_RECEIVED_FUNC = ctypes.CFUNCTYPE(None, ctypes.c_char_p, ctypes.c_char_p)

try:
    # Only set argtypes when core_lib is the real CDLL with callable function objects
    core_lib.start_udp_listener.argtypes = [ctypes.c_int, ON_MESSAGE_RECEIVED_FUNC]
    core_lib.send_udp_message.argtypes = [ctypes.c_char_p, ctypes.c_char_p, ctypes.c_int]
except Exception:
    # fallback/mock doesn't have argtypes; that's fine for tests/dev
    pass
