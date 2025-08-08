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
        self.quote_re = QRegularExpression(r'"([^"]+)"')

    def paint(self, painter, option, index):
        text = index.data()  # Get the text from the model
        if not text:
            return super().paint(painter, option, index)

        # Create a QTextDocument for rich text rendering
        doc = QTextDocument()
        doc.setPlainText(text)

        # Apply highlighting
        known = set(self.get_known_names())
        cursor = doc.find(self.quote_re)
        while not cursor.isNull():
            inner = cursor.selectedText().strip('"')
            if inner in known:
                fmt = cursor.charFormat()
                fmt.setForeground(QColor(180, 130, 255))  # Soft purple
                cursor.mergeCharFormat(fmt)
            cursor = doc.find(self.quote_re, cursor)

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