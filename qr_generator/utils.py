import os
import sys
import logging

def apply_dark_title_bar(widget):
    """Ask Windows to draw this window's native title bar in dark mode.
    No-op on non-Windows platforms or older Windows builds that don't support it."""
    if sys.platform != 'win32':
        return
    try:
        import ctypes
        hwnd = int(widget.winId())
        value = ctypes.c_int(1)
        # DWMWA_USE_IMMERSIVE_DARK_MODE: 20 on Windows 10 1903+/11, 19 on Windows 10 1809.
        for attribute in (20, 19):
            result = ctypes.windll.dwmapi.DwmSetWindowAttribute(
                hwnd, attribute, ctypes.byref(value), ctypes.sizeof(value)
            )
            if result == 0:
                break
    except Exception as e:
        logging.error(f"Could not set dark title bar: {e}")

def resource_path(relative_path):
    """Resolve a path to a bundled resource, working both from source and from a PyInstaller build."""
    if hasattr(sys, '_MEIPASS'):
        base_path = sys._MEIPASS
    else:
        base_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    return os.path.join(base_path, relative_path)

def sanitize_filename(input_string):
    # Remove protocol
    input_string = input_string.replace('https://', '').replace('http://', '')
    # If it's a URL with a path, just take the domain to keep it clean (User's request)
    if '/' in input_string:
        input_string = input_string.split('/')[0]
    # Replace remaining non-safe characters
    for char in ['\\', ':', '*', '?', '"', '<', '>', '|', '.', ' ']:
        input_string = input_string.replace(char, '_')
    return input_string
