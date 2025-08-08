from PyQt6.QtGui import QSyntaxHighlighter, QTextCharFormat, QColor
from PyQt6.QtCore import QRegularExpression


class ExpressionHighlighter(QSyntaxHighlighter):
    def __init__(self, doc, get_known_names_callable):
        super().__init__(doc)
        self.get_known_names = get_known_names_callable

        self.quote_re = QRegularExpression(r'"([^"]+)"')

        self.var_format = QTextCharFormat()
        self.var_format.setForeground(QColor(180, 130, 255))  # soft purple

    def highlightBlock(self, text: str):
        it = self.quote_re.globalMatch(text)
        known = set(self.get_known_names())
        while it.hasNext():
            m = it.next()
            inner = m.captured(1)
            if inner in known:
                print(inner)
                start = m.capturedStart(0)
                length = m.capturedLength(0)
                self.setFormat(start, length, self.var_format)
