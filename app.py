import sys
from pathlib import Path

from PyQt6.QtGui import QIcon
from PyQt6.QtWidgets import QApplication
from main_window import MainWindow


def main():
    app = QApplication(sys.argv)
    
    # Handle command line arguments
    start_path = None
    if len(sys.argv) > 1:
        try:
            start_path = Path(sys.argv[1])
            # Resolve the path to handle relative paths
            if start_path.exists():
                start_path = start_path.resolve()
            else:
                print(f"Warning: File not found: {start_path}")
                start_path = None
        except Exception as e:
            print(f"Warning: Could not parse file path: {e}")
            start_path = None
    
    win = MainWindow(start_path)
    win.show()
    sys.exit(app.exec())


if __name__ == '__main__':
    main()
