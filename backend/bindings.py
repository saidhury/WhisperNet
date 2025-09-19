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
except FileNotFoundError:
    print("="*80)
    print(f"FATAL ERROR: Could not find the core library at '{lib_path}'")
    print("Please ensure you have run the build script './scripts/build_core.sh' successfully.")
    print("="*80)
    raise

ON_MESSAGE_RECEIVED_FUNC = ctypes.CFUNCTYPE(None, ctypes.c_char_p, ctypes.c_char_p)

core_lib.start_udp_listener.argtypes = [ctypes.c_int, ON_MESSAGE_RECEIVED_FUNC]
core_lib.send_udp_message.argtypes = [ctypes.c_char_p, ctypes.c_char_p, ctypes.c_int]
