import os
import sys

AUTOSTART_DIR = os.path.expanduser("~/.config/autostart")
DESKTOP_FILE_PATH = os.path.join(AUTOSTART_DIR, "desktop-pet.desktop")

def is_autostart_enabled() -> bool:
    return os.path.exists(DESKTOP_FILE_PATH)

def set_autostart(enable: bool, app_dir: str = None) -> bool:
    """
    Creates or removes the desktop launcher in ~/.config/autostart/
    """
    if app_dir is None:
        app_dir = os.path.dirname(os.path.abspath(__file__))

    if not enable:
        if os.path.exists(DESKTOP_FILE_PATH):
            os.remove(DESKTOP_FILE_PATH)
        return False

    os.makedirs(AUTOSTART_DIR, exist_ok=True)
    python_executable = sys.executable
    main_script_path = os.path.join(app_dir, "main.py")

    content = f"""[Desktop Entry]
Type=Application
Name=Desktop Pet
Exec=env QT_QPA_PLATFORM=xcb {python_executable} {main_script_path}
Hidden=false
NoDisplay=false
X-GNOME-Autostart-enabled=true
"""
    with open(DESKTOP_FILE_PATH, "w") as f:
        f.write(content)

    return True
