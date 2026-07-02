import os
import sys
import shutil
import subprocess
import platform

def get_hash(file_path):
    if not os.path.exists(file_path):
        return ""
    import hashlib
    hasher = hashlib.sha256()
    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            hasher.update(chunk)
    return hasher.hexdigest()

def main():
    root_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    os.chdir(root_dir)

    print("=== Determining OS and environment ===")
    is_windows = os.name == "nt"
    is_termux = "com.termux" in sys.executable or os.path.exists("/data/data/com.termux")
    
    # Determine paths inside virtualenv
    venv_dir = os.path.join("backend", ".venv")
    if is_windows:
        venv_python = os.path.abspath(os.path.join(venv_dir, "Scripts", "python.exe"))
        venv_pip = os.path.abspath(os.path.join(venv_dir, "Scripts", "pip.exe"))
        venv_pyinstaller = os.path.abspath(os.path.join(venv_dir, "Scripts", "pyinstaller.exe"))
    else:
        venv_python = os.path.abspath(os.path.join(venv_dir, "bin", "python"))
        venv_pip = os.path.abspath(os.path.join(venv_dir, "bin", "pip"))
        venv_pyinstaller = os.path.abspath(os.path.join(venv_dir, "bin", "pyinstaller"))

    # Ensure virtualenv exists
    if not os.path.exists(venv_python):
        print("Creating virtual environment...")
        if os.path.exists(venv_dir):
            shutil.rmtree(venv_dir, ignore_errors=True)
        subprocess.run([sys.executable, "-m", "venv", venv_dir], check=True)

    # Install Python dependencies including PyInstaller and Pillow (for icon generation)
    req_file = os.path.join("backend", "requirements.txt")
    print("Installing/updating Python dependencies...")
    subprocess.run([venv_pip, "install", "-r", req_file], check=True)
    subprocess.run([venv_pip, "install", "pyinstaller", "Pillow"], check=True)

    # 1. Compile C++ core library in Release mode
    print("=== Compiling C++ Core Library in Release mode ===")
    subprocess.run(["cmake", "-S", "core", "-B", "build/core", "-DCMAKE_BUILD_TYPE=Release"], check=True)
    if is_windows:
        subprocess.run(["cmake", "--build", "build/core", "--config", "Release"], check=True)
    else:
        subprocess.run(["cmake", "--build", "build/core"], check=True)

    # 2. Verify C++ library exists in backend/lib (handling direct CMake output)
    print("=== Verifying/Staging C++ library ===")
    backend_lib_dir = os.path.join("backend", "lib")
    
    if is_windows:
        expected_dll = os.path.join(backend_lib_dir, "Release", "whispernet_core.dll")
        if not os.path.exists(expected_dll):
            build_dll = os.path.join("build", "core", "Release", "whispernet_core.dll")
            if os.path.exists(build_dll):
                os.makedirs(os.path.dirname(expected_dll), exist_ok=True)
                shutil.copy2(build_dll, expected_dll)
            else:
                raise FileNotFoundError(f"Could not find compiled whispernet_core.dll. Checked: {expected_dll} and {build_dll}")
    else:
        filename = "libwhispernet_core.dylib" if platform.system() == "Darwin" else "libwhispernet_core.so"
        expected_lib = os.path.join(backend_lib_dir, filename)
        if not os.path.exists(expected_lib):
            build_lib = os.path.join("build", "core", filename)
            if os.path.exists(build_lib):
                shutil.copy2(build_lib, expected_lib)
            else:
                raise FileNotFoundError(f"Could not find compiled core library. Checked: {expected_lib} and {build_lib}")

    # 3. Build React Frontend Static Assets
    print("=== Building React Frontend Static Assets ===")
    pkg_file = os.path.join("webui", "package.json")
    node_modules_dir = os.path.join("webui", "node_modules")
    
    # Run npm install if needed
    if not os.path.isdir(node_modules_dir):
        print("Installing WebUI npm packages...")
        subprocess.run(["npm", "install"], cwd="webui", shell=is_windows, check=True)

    print("Compiling frontend assets...")
    subprocess.run(["npm", "run", "build"], cwd="webui", shell=is_windows, check=True)

    # Copy frontend assets to backend/static
    backend_static_dir = os.path.join("backend", "static")
    if os.path.exists(backend_static_dir):
        shutil.rmtree(backend_static_dir)
    shutil.copytree(os.path.join("webui", "dist"), backend_static_dir)

    # Generate logo.ico from the PNG if it exists (for application executable icon)
    logo_png = os.path.abspath(os.path.join("webui", "src", "assets", "logo.png"))
    logo_ico = os.path.abspath(os.path.join("backend", "logo.ico"))
    has_icon = False
    if os.path.exists(logo_png):
        print("Generating application icon (logo.ico)...")
        try:
            from PIL import Image
            img = Image.open(logo_png)
            img.save(logo_ico, format="ICO", sizes=[(16, 16), (32, 32), (48, 48), (64, 64), (128, 128), (256, 256)])
            has_icon = True
            print("Successfully generated logo.ico")
        except Exception as e:
            print("Warning: Failed to generate logo.ico:", e)

    # 4. Run PyInstaller to package everything
    print("=== Bundling application via PyInstaller ===")
    path_sep = ";" if is_windows else ":"
    
    # Bundle both the static folder and the C++ binary folder
    pyinstaller_cmd = [
        venv_pyinstaller,
        "--onefile",
        "--clean",
        "--name", "whispernet",
        "--add-data", f"backend/static{path_sep}static",
        "--add-data", f"backend/lib{path_sep}backend/lib",
    ]
    if has_icon and os.path.exists(logo_ico):
        pyinstaller_cmd.extend(["--icon", logo_ico])
        
    pyinstaller_cmd.append(os.path.join("backend", "main.py"))
    
    # Exclude unnecessary modules to shrink binary size
    pyinstaller_cmd.extend([
        "--exclude-module", "pytest",
        "--exclude-module", "numpy",
        "--exclude-module", "pandas",
        "--exclude-module", "matplotlib"
    ])

    subprocess.run(pyinstaller_cmd, check=True)

    # 5. Stage the final binary in the root directory
    print("=== Packaging complete ===")
    ext = ".exe" if is_windows else ""
    src_bin = os.path.join("dist", f"whispernet{ext}")
    dest_bin = os.path.join(root_dir, f"whispernet{ext}")
    
    if os.path.exists(dest_bin):
        os.remove(dest_bin)
    shutil.copy2(src_bin, dest_bin)
    
    # Clean up temporary PyInstaller folders
    print("Cleaning up build workspace...")
    shutil.rmtree("build/whispernet", ignore_errors=True)
    shutil.rmtree("dist", ignore_errors=True)
    if os.path.exists("whispernet.spec"):
        os.remove("whispernet.spec")
    if os.path.exists(logo_ico):
        try:
            os.remove(logo_ico)
        except Exception:
            pass

    print(f"\nSUCCESS! Created standalone executable at: {dest_bin}")
    if is_windows:
        print("You can now double-click 'whispernet.exe' to launch the app!")
    else:
        print("You can run './whispernet' to launch the app!")

if __name__ == "__main__":
    main()
