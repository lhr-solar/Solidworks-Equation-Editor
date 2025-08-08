from PyQt6.QtGui import QTextDocument, QColor
from PyQt6.QtWidgets import QStyledItemDelegate, QComboBox
from PyQt6.QtCore import Qt, QRegularExpression, QRectF


class SectionComboDelegate(QStyledItemDelegate):
    def __init__(self, get_sections_callable, parent=None):
        super().__init__(parent)
        self.get_sections = get_sections_callable  # should return list[str]

    def createEditor(self, parent, option, index):
        combo = QComboBox(parent)
        combo.setEditable(False)
        combo.addItems(self.get_sections())
        return combo

    def setEditorData(self, editor, index):
        current = index.model().data(index, Qt.ItemDataRole.EditRole)
        if isinstance(editor, QComboBox):
            i = editor.findText(current)
            if i >= 0:
                editor.setCurrentIndex(i)

    def setModelData(self, editor, model, index):
        if isinstance(editor, QComboBox):
            value = editor.currentText()
            model.setData(index, value, Qt.ItemDataRole.EditRole)

    def updateEditorGeometry(self, editor, option, index):
        editor.setGeometry(option.rect)


class HighlightingDelegate(QStyledItemDelegate):
    def __init__(self, get_known_names_callable, parent=None):
        super().__init__(parent)
        self.get_known_names = get_known_names_callable
        self.quote_re = QRegularExpression(r'"([^"]+)"')  # Quoted strings
        self.identifier_re = QRegularExpression(r'\b([a-zA-Z_][a-zA-Z0-9_]*)\b')  # Unquoted identifiers

        # Define the categories from editors.py
        self.SW_FILE_PROPERTIES = [
            'SW-Mass', 'SW-Volume', 'SW-SurfaceArea',
            'SW-CenterofMassX', 'SW-CenterofMassY', 'SW-CenterofMassZ',
            'SW-Density', 'SW-Px', 'SW-Py', 'SW-Pz',
            'SW-Lxx', 'SW-Lxy', 'SW-Lxz', 'SW-Lyx', 'SW-Lyy', 'SW-Lyz', 'SW-Lzx', 'SW-Lzy', 'SW-Lzz'
        ]
        
        self.FUNCTIONS = {
            'sin': ('',), 'cos': ('',), 'tan': ('',), 'sec': ('',), 'cosec': ('',), 'cotan': ('',),
            'arcsin': ('',), 'arccos': ('',), 'arctan': ('',), 'arcsec': ('',), 'arccotan': ('',),
            'abs': ('',), 'exp': ('',), 'log': ('',), 'ln': ('',), 'sqr': ('',), 'sqrt': ('',),
            'int': ('',), 'sgn': ('',), 'max': ('', ''), 'min': ('', ''), 'if': ('', '', ''),
        }
        
        self.CONSTANTS = ['pi', 'e']

    def paint(self, painter, option, index):
        text = index.data()  # Get the text from the model
        if not text:
            return super().paint(painter, option, index)

        # Create a QTextDocument for rich text rendering
        doc = QTextDocument()
        doc.setPlainText(text)

        # Apply highlighting
        known = set(self.get_known_names())
        
        # Highlight quoted strings (variable names and SW file properties in equations)
        cursor = doc.find(self.quote_re)
        while not cursor.isNull():
            inner = cursor.selectedText().strip('"')
            fmt = cursor.charFormat()
            
            # Determine the type of quoted string
            if inner in self.SW_FILE_PROPERTIES:
                fmt.setForeground(QColor(255, 100, 100))  # red for SW file properties
            elif inner in known:
                fmt.setForeground(QColor(180, 130, 255))  # purple for global variables
            
            cursor.mergeCharFormat(fmt)
            cursor = doc.find(self.quote_re, cursor)
        
        # Highlight unquoted identifiers (functions, constants, variables in expressions)
        cursor = doc.find(self.identifier_re)
        while not cursor.isNull():
            identifier = cursor.selectedText()
            fmt = cursor.charFormat()
            
            # Determine the type and apply appropriate formatting
            if identifier in self.FUNCTIONS:
                fmt.setForeground(QColor(100, 150, 255))  # blue for functions
            elif identifier in self.CONSTANTS:
                fmt.setForeground(QColor(100, 255, 100))  # green for constants
            elif identifier in known:
                fmt.setForeground(QColor(180, 130, 255))  # purple for global variables
            
            cursor.mergeCharFormat(fmt)
            cursor = doc.find(self.identifier_re, cursor)

        # Render the QTextDocument
        painter.save()
        painter.translate(option.rect.topLeft())
        doc.setTextWidth(option.rect.width())
        doc.drawContents(painter, QRectF(0, 0, option.rect.width(), option.rect.height()))
        painter.restore()

    def sizeHint(self, option, index):
        # Adjust size to fit the rendered text
        doc = QTextDocument()
        doc.setPlainText(index.data())
        doc.setTextWidth(option.rect.width())
        return doc.size().toSize()