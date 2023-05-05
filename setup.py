import sys
from cx_Freeze import setup, Executable

# Dependencies are automatically detected, but it might need fine tuning.
build_exe_options = {
    "excludes": ["unittest"],
    "zip_include_packages": ["encodings", "PySide6"],
}

# base="Win32GUI" should be used only for Windows GUI app
base = "Win32GUI" if sys.platform == "win32" else None

setup(
    name="ToonTuber Player",
    version="1.3.0",
    description="ToonTuber Player",
    options={"build_exe": build_exe_options},
    executables=[Executable("toontuber.py", base=base)],
)