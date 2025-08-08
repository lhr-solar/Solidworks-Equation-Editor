from PyQt6.QtGui import QSyntaxHighlighter, QTextCharFormat, QColor
from PyQt6.QtCore import QRegularExpression


class ExpressionHighlighter(QSyntaxHighlighter):
    def __init__(self, doc, get_known_names_callable):
        super().__init__(doc)
        self.get_known_names = get_known_names_callable

        # Regex patterns for different types of identifiers
        self.quote_re = QRegularExpression(r'"([^"]+)"')  # Quoted strings
        self.identifier_re = QRegularExpression(r'\b([a-zA-Z_][a-zA-Z0-9_]*)\b')  # Unquoted identifiers

        # Define formats for different types
        self.var_format = QTextCharFormat()
        self.var_format.setForeground(QColor(180, 130, 255))  # purple for global variables

        self.sw_prop_format = QTextCharFormat()
        self.sw_prop_format.setForeground(QColor(255, 100, 100))  # red for SW file properties

        self.function_format = QTextCharFormat()
        self.function_format.setForeground(QColor(100, 150, 255))  # blue for functions

        self.constant_format = QTextCharFormat()
        self.constant_format.setForeground(QColor(100, 255, 100))  # green for constants

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

    def highlightBlock(self, text: str):
        known = set(self.get_known_names())
        
        # Highlight quoted strings (variable names and SW file properties in equations)
        it = self.quote_re.globalMatch(text)
        while it.hasNext():
            m = it.next()
            inner = m.captured(1)
            start = m.capturedStart(0)
            length = m.capturedLength(0)
            
            # Determine the type of quoted string
            if inner in self.SW_FILE_PROPERTIES:
                self.setFormat(start, length, self.sw_prop_format)  # red for SW file properties
            elif inner in known:
                self.setFormat(start, length, self.var_format)  # purple for global variables
        
        # Highlight unquoted identifiers (functions, constants, variables in expressions)
        it = self.identifier_re.globalMatch(text)
        while it.hasNext():
            m = it.next()
            identifier = m.captured(1)
            start = m.capturedStart(1)
            length = m.capturedLength(1)
            
            # Determine the type and apply appropriate formatting
            if identifier in self.FUNCTIONS:
                self.setFormat(start, length, self.function_format)  # blue for functions
            elif identifier in self.CONSTANTS:
                self.setFormat(start, length, self.constant_format)  # green for constants
            elif identifier in known:
                self.setFormat(start, length, self.var_format)  # purple for global variables
