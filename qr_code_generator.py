import sys
import os
import logging
from PyQt5.QtWidgets import QApplication
from qr_generator.ui.mainwindow import QRCodeGenerator

# Setup logging with absolute path
script_dir = os.path.dirname(os.path.abspath(__file__))
log_file = os.path.join(script_dir, 'qr_code_generator.log')

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(log_file, encoding='utf-8'),
        logging.StreamHandler(sys.stdout)
    ]
)

def main():
    try:
        logging.info("Application starting...")
        app = QApplication(sys.argv)
        window = QRCodeGenerator()
        window.show()
        logging.info("Application main window shown.")
        sys.exit(app.exec_())
    except Exception as e:
        logging.critical("Application failed to start: %s", e, exc_info=True)
        print(f"CRITICAL ERROR: {e}")

if __name__ == '__main__':
    main()
