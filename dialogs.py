from PyQt6.QtWidgets import QDialog, QFormLayout, QLineEdit, QComboBox, QDialogButtonBox
from editors import ExpressionEditor


class AddEditDialog(QDialog):
    def __init__(self, parent=None, name='', expr='', sections=None, current_section='Unassigned', comment='', get_known_names_callable=lambda: ()):
        super().__init__(parent)
        self.setWindowTitle('Add / Edit Equation')
        form = QFormLayout(self)

        self.name_edit = QLineEdit(name)
        # Expression editor with variable picker + highlighter
        self.expr_editor = ExpressionEditor(get_known_names_callable, initial_text=expr)

        self.section_combo = QComboBox()
        self.section_combo.setEditable(False)
        sections = sections or []
        if sections:
            self.section_combo.addItems(sorted(sections))
        if current_section and current_section in sections:
            self.section_combo.setCurrentText(current_section)
        else:
            self.section_combo.setCurrentText('Unassigned')

        self.comment_edit = QLineEdit(comment)

        form.addRow('Variable name (in quotes in file):', self.name_edit)
        form.addRow('Expression:', self.expr_editor)
        form.addRow('Section:', self.section_combo)
        form.addRow('Comment:', self.comment_edit)

        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        form.addRow(buttons)

    def values(self):
        return (
            self.name_edit.text().strip().strip('"'),
            self.expr_editor.text().strip(),
            self.section_combo.currentText().strip(),
            self.comment_edit.text().strip()
        )
