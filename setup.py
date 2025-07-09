#!/usr/bin/env python3
"""
setup.py: One-step setup for Open Physics Ed

- Creates a Python virtual environment (.venv) if missing
- Installs dependencies from requirements.txt
- If not in venv, reinvokes itself inside the venv
- Does NOT run the site build script
"""
import os
import subprocess
import sys

VENV_DIR = ".venv"
REQ_FILE = "requirements.txt"


def run(cmd, **kwargs):
    print(f"$ {' '.join(cmd)}")
    subprocess.check_call(cmd, **kwargs)


def in_venv():
    return (
        hasattr(sys, 'real_prefix') or
        (hasattr(sys, 'base_prefix') and sys.base_prefix != sys.prefix)
    )


def main():
    # 1. Create virtual environment if missing
    if not os.path.isdir(VENV_DIR):
        print(f"Creating virtual environment in {VENV_DIR}...")
        run([sys.executable, "-m", "venv", VENV_DIR])

    # 2. If not in venv, re-invoke this script inside the venv
    venv_python = os.path.join(VENV_DIR, "bin", "python3")
    if not in_venv():
        print(f"Re-invoking setup.py inside the virtual environment...")
        run([venv_python, __file__])
        sys.exit(0)

    # 3. Install requirements
    pip_path = os.path.join(VENV_DIR, "bin", "pip")
    print("Installing dependencies from requirements.txt...")
    run([pip_path, "install", "-r", REQ_FILE])

    print("\nSetup complete! To build the site, run: python build.py\n")

if __name__ == "__main__":
    main()
