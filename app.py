import sys
from pathlib import Path

from PyQt6.QtGui import QIcon
from PyQt6.QtWidgets import QApplication
from main_window import MainWindow


def main():
    app = QApplication(sys.argv)
    start_path = Path(sys.argv[1]) if len(sys.argv) > 1 else None
    win = MainWindow(start_path)
    win.show()
    sys.exit(app.exec())


if __name__ == '__main__':
    main()
