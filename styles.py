from PyQt6.QtCore import Qt


def apply_dark_palette(widget):
    palette = widget.palette()
    palette.setColor(palette.ColorRole.Window, Qt.GlobalColor.black)
    palette.setColor(palette.ColorRole.WindowText, Qt.GlobalColor.white)
    palette.setColor(palette.ColorRole.Base, Qt.GlobalColor.black)
    palette.setColor(palette.ColorRole.AlternateBase, Qt.GlobalColor.black)
    palette.setColor(palette.ColorRole.ToolTipBase, Qt.GlobalColor.white)
    palette.setColor(palette.ColorRole.ToolTipText, Qt.GlobalColor.white)
    palette.setColor(palette.ColorRole.Text, Qt.GlobalColor.white)
    palette.setColor(palette.ColorRole.Button, Qt.GlobalColor.black)
    palette.setColor(palette.ColorRole.ButtonText, Qt.GlobalColor.white)
    palette.setColor(palette.ColorRole.Highlight, Qt.GlobalColor.darkGray)
    palette.setColor(palette.ColorRole.HighlightedText, Qt.GlobalColor.black)
    widget.setPalette(palette)
