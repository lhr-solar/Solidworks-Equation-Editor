from PyQt6.QtWidgets import QWidget, QHBoxLayout, QPlainTextEdit, QComboBox, QPushButton
from highlighter import ExpressionHighlighter


class ExpressionEditor(QWidget):
    def __init__(self, get_known_names_callable, parent=None, initial_text=''):
        super().__init__(parent)
        self.get_known_names = get_known_names_callable

        lay = QHBoxLayout(self)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.setSpacing(6)

        self.edit = QPlainTextEdit(initial_text)
        self.edit.setTabChangesFocus(True)  # Allow tab key to move focus
        self.combo = QComboBox()
        self.combo.setEditable(False)
        self.reload_combo()

        self.btn = QPushButton('+')
        self.btn.setToolTip('Insert selected variable at cursor')
        self.btn.setFixedWidth(28)

        lay.addWidget(self.edit, 1)
        lay.addWidget(self.combo)
        lay.addWidget(self.btn)

        self.btn.clicked.connect(self.insert_selected)

        # Attach the highlighter directly to the QPlainTextEdit's document
        self._highlighter = ExpressionHighlighter(self.edit.document(), self.get_known_names)

    def reload_combo(self):
        self.combo.clear()
        names = sorted(self.get_known_names())
        self.combo.addItems(names)

    def insert_selected(self):
        var = self.combo.currentText()
        if not var:
            return
        # Insert as "var"
        quoted = f'"{var}"'
        cursor = self.edit.textCursor()
        cursor.insertText(quoted)

    def text(self):
        return self.edit.toPlainText()

    def setText(self, t: str):
        self.edit.setPlainText(t)