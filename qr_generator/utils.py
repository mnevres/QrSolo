import os
import sys

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
