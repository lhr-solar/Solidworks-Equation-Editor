from PyQt6.QtGui import QTextDocument
from PyQt6.QtWidgets import QWidget, QHBoxLayout, QPlainTextEdit, QComboBox, QPushButton, QLabel, QLineEdit, QVBoxLayout
from highlighter import ExpressionHighlighter


class ExpressionEditor(QWidget):
    CATEGORIES = ['Variables', 'File Properties', 'Functions', 'Constants']
    SW_FILE_PROPERTIES = [
        'SW-Mass', 'SW-Volume', 'SW-SurfaceArea',
        'SW-CenterofMassX', 'SW-CenterofMassY', 'SW-CenterofMassZ',
        'SW-Density', 'SW-Px', 'SW-Py', 'SW-Pz',
        'SW-Lxx', 'SW-Lxy', 'SW-Lxz', 'SW-Lyx', 'SW-Lyy', 'SW-Lyz', 'SW-Lzx', 'SW-Lzy', 'SW-Lzz'
    ]
    FUNCTIONS = {
        'sin': ('',),
        'cos': ('',),
        'tan': ('',),
        'sec': ('',),
        'cosec': ('',),
        'cotan': ('',),
        'arcsin': ('',),
        'arccos': ('',),
        'arctan': ('',),
        'arcsec': ('',),
        'arccotan': ('',),
        'abs': ('',),
        'exp': ('',),
        'log': ('',),
        'ln': ('',),
        'sqr': ('',),
        'sqrt': ('',),
        'int': ('',),
        'sgn': ('',),
        'max': ('', ''),
        'min': ('', ''),
        'if': ('', '', ''),
    }
    CONSTANTS = ['pi', 'e']

    def __init__(self, get_known_names_callable, parent=None, initial_text=''):
        super().__init__(parent)
        self.get_known_names = get_known_names_callable

        # Layout
        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setSpacing(4)

        # Row 1: expression line
        self.edit = QLineEdit(initial_text)
        outer.addWidget(self.edit, 1)

        # Row 2: insertion controls
        insert_row = QWidget()
        irl = QHBoxLayout(insert_row)
        irl.setContentsMargins(0, 0, 0, 0)
        irl.setSpacing(6)

        irl.addWidget(QLabel('Insert:'))

        self.category_combo = QComboBox()
        self.category_combo.addItems(self.CATEGORIES)
        self.category_combo.currentIndexChanged.connect(self._refresh_item_combo)
        irl.addWidget(self.category_combo)

        self.item_combo = QComboBox()
        irl.addWidget(self.item_combo, 1)

        self.btn_insert = QPushButton('Insert')
        self.btn_insert.setToolTip('Insert selected token at cursor')
        self.btn_insert.clicked.connect(self._insert_selected_token)
        irl.addWidget(self.btn_insert)

        outer.addWidget(insert_row)

        # Initial fill of item combo
        self._refresh_item_combo()

        # Mirror into a QTextDocument for syntax highlighting
        self._doc = QTextDocument(self)
        self._doc.setPlainText(self.edit.text())
        self._highlighter = ExpressionHighlighter(self._doc, self.get_known_names)
        self.edit.textChanged.connect(self._doc.setPlainText)

    def _refresh_item_combo(self):
        cat = self.category_combo.currentText()
        self.item_combo.clear()
        if cat == 'Variables':
            # Known names come from the model
            self.item_combo.addItems(sorted(self.get_known_names()))
        elif cat == 'File Properties':
            self.item_combo.addItems(self.SW_FILE_PROPERTIES)
        elif cat == 'Functions':
            self.item_combo.addItems(sorted(self.FUNCTIONS.keys()))
        elif cat == 'Constants':
            self.item_combo.addItems(self.CONSTANTS)

    def _insert_selected_token(self):
        cat = self.category_combo.currentText()
        val = self.item_combo.currentText()
        if not val:
            return

        token = ''
        if cat == 'Variables':
            # Insert as quoted variable reference
            token = f'"{val}"'
        elif cat == 'File Properties':
            # Insert as quoted property reference (SolidWorks expects quoted names)
            token = f'"{val}"'
        elif cat == 'Functions':
            # Insert function with parentheses and appropriate comma placeholders
            sig = self.FUNCTIONS.get(val, tuple())
            if len(sig) == 0:
                token = f'{val}()'
            else:
                # Create placeholders for each parameter
                placeholders = [''] * len(sig)
                inner = ', '.join(placeholders)
                token = f'{val}({inner})'
        elif cat == 'Constants':
            # Constants like pi are bare
            token = val

        # Insert at cursor
        edit = self.edit
        pos = edit.cursorPosition()
        t = edit.text()
        new_t = t[:pos] + token + t[pos:]
        edit.setText(new_t)
        # Place cursor inside parentheses for functions; otherwise after token
        if cat == 'Functions':
            # Move cursor to between the parentheses
            open_idx = new_t.find('(', pos)
            if open_idx != -1:
                edit.setCursorPosition(open_idx + 1)
            else:
                edit.setCursorPosition(pos + len(token))
        else:
            edit.setCursorPosition(pos + len(token))

    def text(self):
        return self.edit.text()

    def setText(self, t: str):
        self.edit.setText(t)

    def reload_variables(self):
        # If currently on Variables, refresh list
        if self.category_combo.currentText() == 'Variables':
            self._refresh_item_combo()