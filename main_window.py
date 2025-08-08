import os
from pathlib import Path

from PyQt6.QtCore import Qt
from PyQt6.QtGui import QAction
from PyQt6.QtWidgets import (
    QMainWindow, QFileDialog, QTableView, QToolBar,
    QWidget, QVBoxLayout, QHBoxLayout, QLineEdit, QMessageBox,
    QLabel, QSplitter, QListWidget, QListWidgetItem, QStyleFactory,
    QPushButton, QHeaderView, QInputDialog
)

from parsing import parse_equations, serialize_equations
from config_io import cfg_path_for, load_cfg, save_cfg, reconcile_cfg_with_txt
from file_lock import FileHandleLock
from models import EquationModel
from dialogs import AddEditDialog
from styles import apply_dark_palette
from delegates import SectionComboDelegate, ExpressionDelegate, HighlightingDelegate


class MainWindow(QMainWindow):
    def __init__(self, path: Path | None = None):
        super().__init__()
        self.setWindowTitle('SolidWorks Equations Editor')
        self.resize(1200, 740)

        # Dark Fusion style
        from PyQt6.QtWidgets import QApplication
        QApplication.setStyle(QStyleFactory.create('Fusion'))
        apply_dark_palette(self)

        self.current_path: Path | None = None
        self.cfg: dict | None = None
        self.fhlock: FileHandleLock | None = None

        self._build_ui()

        if path is not None:
            self.load_path(Path(path))

    def _build_ui(self):
        container = QWidget()
        root = QVBoxLayout(container)
        root.setContentsMargins(6, 6, 6, 6)
        root.setSpacing(6)

        # Toolbar
        tb = QToolBar('Main')
        tb.setMovable(False)
        self.addToolBar(tb)

        open_act = QAction('Open', self)
        open_act.triggered.connect(self.open_file)
        tb.addAction(open_act)

        save_act = QAction('Save', self)
        save_act.triggered.connect(self.save_file)
        tb.addAction(save_act)

        add_act = QAction('Add', self)
        add_act.triggered.connect(self.add_equation)
        tb.addAction(add_act)

        del_act = QAction('Delete', self)
        del_act.triggered.connect(self.delete_selected)
        tb.addAction(del_act)

        # Compact filter row
        fb = QWidget()
        fbl = QHBoxLayout(fb)
        fbl.setContentsMargins(0, 0, 0, 0)
        fbl.setSpacing(8)
        fbl.addWidget(QLabel('Filter:'))
        self.filter_edit = QLineEdit()
        self.filter_edit.setPlaceholderText('Type to filter by name, expression, or comment...')
        self.filter_edit.textChanged.connect(self.apply_filter)
        fbl.addWidget(self.filter_edit)
        root.addWidget(fb)

        # Left sidebar with sections and controls
        left = QWidget()
        ll = QVBoxLayout(left)
        ll.setContentsMargins(0, 0, 0, 0)
        ll.setSpacing(6)

        btn_add_sec = QPushButton('Add Section')
        btn_ren_sec = QPushButton('Rename Section')
        btn_del_sec = QPushButton('Delete Section')
        btn_add_sec.clicked.connect(self.add_section)
        btn_ren_sec.clicked.connect(self.rename_section)
        btn_del_sec.clicked.connect(self.delete_section)

        ll.addWidget(btn_add_sec)
        ll.addWidget(btn_ren_sec)
        ll.addWidget(btn_del_sec)

        self.section_list = QListWidget()
        self.section_list.itemSelectionChanged.connect(self.apply_section_filter)
        ll.addWidget(self.section_list, 1)

        # Table view
        self.view = QTableView()
        self.view.setAlternatingRowColors(True)
        self.view.setSelectionBehavior(QTableView.SelectionBehavior.SelectRows)
        self.view.setSelectionMode(QTableView.SelectionMode.ExtendedSelection)
        self.view.verticalHeader().setVisible(False)

        splitter = QSplitter()
        splitter.addWidget(left)
        splitter.addWidget(self.view)
        splitter.setStretchFactor(0, 0)
        splitter.setStretchFactor(1, 1)

        root.addWidget(splitter, 1)
        self.setCentralWidget(container)

        # Read-only banner in status bar
        self.readonly_banner = QLabel('')
        self.readonly_banner.setStyleSheet('color: yellow;')
        self.statusBar().addPermanentWidget(self.readonly_banner)

    # ------------ File ops ------------
    def open_file(self):
        fn, _ = QFileDialog.getOpenFileName(
            self,
            'Open SolidWorks Equations',
            os.getcwd(),
            'Text Files (*.txt);;All Files (*)'
        )
        if fn:
            self.load_path(Path(fn))

    def load_path(self, path: Path):
        if self.fhlock:
            self.fhlock.release()

        self.current_path = path
        self.fhlock = FileHandleLock(path)
        locked = self.fhlock.acquire()
        if not self.fhlock.file:
            QMessageBox.critical(self, 'Error', 'Failed to open file.')
            return

        if locked and not self.fhlock.readonly:
            self.readonly_banner.setText('')
            self.statusBar().showMessage('Exclusive lock acquired (other apps blocked from writing).')
        else:
            self.readonly_banner.setText('READ-ONLY: Could not acquire lock')
            self.statusBar().showMessage('Opened without exclusive lock; edits may not save.')

        try:
            text = self.fhlock.read_all()
        except Exception as e:
            QMessageBox.critical(self, 'Error', f'Failed to read file: {e}')
            return

        eqs = parse_equations(text)

        cfgp = cfg_path_for(path)
        cfg = load_cfg(cfgp)
        names_in_txt = {e['name'] for e in eqs}
        cfg = reconcile_cfg_with_txt(cfg, names_in_txt)

        try:
            save_cfg(cfgp, cfg)
        except Exception as e:
            QMessageBox.warning(self, 'Warning', f'Failed to write CFG: {e}')

        self.cfg = cfg
        self.model = EquationModel(eqs, self.cfg, self)
        self.view.setModel(self.model)

        # Delegates:
        # - Section as combo (column 2)
        def get_sections():
            return sorted(self.cfg.get('sections', {}).keys())
        self.view.setItemDelegateForColumn(2, SectionComboDelegate(get_sections, self))

        # - Expression composite editor (column 1) with highlighter and insert combo
        def get_known_names():
            # Current variable names from the model
            return [e['name'] for e in self.model.equations]
        self.view.setItemDelegateForColumn(1, ExpressionDelegate(get_known_names, self))
        self.view.setItemDelegateForColumn(1, HighlightingDelegate(get_known_names, self))

        # Column sizing: stretch Comment column to fill extra space
        self.view.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Interactive)
        try:
            self.view.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeMode.Stretch)
        except Exception:
            pass

        self.populate_sections()
        self.apply_filter()
        self.statusBar().showMessage(f'Loaded {path.name} — {len(eqs)} equations')

    def save_file(self):
        if not self.current_path or not self.fhlock or not self.fhlock.file:
            return
        if self.fhlock.readonly:
            QMessageBox.warning(
                self,
                'Read-only',
                'File is read-only (no lock). Close other apps and use Reload from the menu if present.'
            )
            return
        try:
            txt = serialize_equations(self.model.equations)
            self.fhlock.write_all(txt)
        except Exception as e:
            QMessageBox.critical(self, 'Error', f'Failed to write TXT: {e}')
            return
        try:
            save_cfg(cfg_path_for(self.current_path), self.cfg)
        except Exception as e:
            QMessageBox.critical(self, 'Error', f'Failed to write CFG: {e}')
            return
        self.statusBar().showMessage('Saved')

    def closeEvent(self, event):
        event.accept()

    # ------------ Sections ------------
    def populate_sections(self):
        self.section_list.clear()
        self.section_list.addItem(QListWidgetItem('All'))
        for sec in sorted(self.cfg.get('sections', {}).keys()):
            self.section_list.addItem(QListWidgetItem(sec))
        if not self.section_list.selectedItems():
            items = self.section_list.findItems('All', Qt.MatchFlag.MatchExactly)
            if items:
                self.section_list.setCurrentItem(items[0])

    def add_section(self):
        name, ok = QInputDialog.getText(self, 'Add Section', 'Section name:')
        name = (name or '').strip()
        if not (ok and name):
            return
        if name in self.cfg['sections']:
            QMessageBox.information(self, 'Exists', 'Section already exists.')
            return
        self.cfg['sections'][name] = []
        self.populate_sections()

    def rename_section(self):
        sel = self.section_list.selectedItems()
        if not sel:
            QMessageBox.information(self, 'Rename Section', 'Select a section to rename.')
            return
        old = sel[0].text()
        if old in ('All', 'Unassigned'):
            QMessageBox.information(self, 'Not allowed', f'"{old}" cannot be renamed.')
            return
        new, ok = QInputDialog.getText(self, 'Rename Section', 'New name:', text=old)
        new = (new or '').strip()
        if not (ok and new):
            return
        if new in self.cfg['sections'] and new != old:
            QMessageBox.information(self, 'Exists', 'A section with that name already exists.')
            return
        self.cfg['sections'][new] = self.cfg['sections'].pop(old)
        self.model.rebuild_section_map()
        self.populate_sections()
        items = self.section_list.findItems(new, Qt.MatchFlag.MatchExactly)
        if items:
            self.section_list.setCurrentItem(items[0])
        self.apply_filter()

    def delete_section(self):
        sel = self.section_list.selectedItems()
        if not sel:
            QMessageBox.information(self, 'Delete Section', 'Select a section to delete.')
            return
        name = sel[0].text()
        if name in ('All', 'Unassigned'):
            QMessageBox.information(self, 'Not allowed', f'"{name}" cannot be deleted.')
            return
        if QMessageBox.question(
            self,
            'Confirm',
            f'Delete section "{name}" and move its variables to Unassigned?'
        ) != QMessageBox.StandardButton.Yes:
            return
        vars_in_sec = self.cfg['sections'].pop(name, [])
        self.cfg['sections'].setdefault('Unassigned', []).extend(vars_in_sec)
        self.cfg['sections']['Unassigned'] = sorted(set(self.cfg['sections']['Unassigned']))
        self.model.rebuild_section_map()
        self.populate_sections()
        self.apply_filter()

    def apply_section_filter(self):
        selected = [i.text() for i in self.section_list.selectedItems()]
        if not selected or 'All' in selected:
            self.apply_filter(section_subset=None)
        else:
            self.apply_filter(section_subset=set(selected))

    # ------------ Filtering ------------
    def apply_filter(self, text=None, section_subset=None):
        if not hasattr(self, 'model') or self.model is None:
            return
        if text is None:
            text = self.filter_edit.text().strip().lower()

        comments = self.cfg.get('comments', {}) if self.cfg else {}

        def visible(e):
            ok = True
            if text:
                name_l = e['name'].lower()
                expr_l = e['expr'].lower()
                cmt_l = comments.get(e['name'], '').lower()
                ok = (text in name_l) or (text in expr_l) or (text in cmt_l)
            if ok and section_subset is not None:
                sec = self.model.name_to_section.get(e['name'], 'Unassigned')
                ok = sec in section_subset
            return ok

        filtered = [e for e in self.model.equations if visible(e)]
        self.view.clearSelection()
        for r, e in enumerate(self.model.equations):
            self.view.setRowHidden(r, e not in filtered)

    # ------------ Editing ------------
    def add_equation(self):
        if not self.cfg:
            QMessageBox.information(self, 'No file open', 'Open a SolidWorks equations .txt file first.')
            return
        sec_names = list(self.cfg.get('sections', {}).keys())
        def get_known_names():
            return [e['name'] for e in self.model.equations]
        dlg = AddEditDialog(self, sections=sec_names, get_known_names_callable=get_known_names)
        if dlg.exec():
            name, expr, sec, comment = dlg.values()
            if not name:
                return
            self.model.add_equation(name, expr, section=sec or 'Unassigned')
            if comment:
                self.cfg.setdefault('comments', {})[name] = comment
            self.apply_filter()

    def delete_selected(self):
        if not hasattr(self, 'model') or self.model is None:
            return
        sels = self.view.selectionModel().selectedRows()
        rows = [i.row() for i in sels]
        if not rows:
            return
        if QMessageBox.question(self, 'Confirm', f'Delete {len(rows)} selected equation(s)?') != QMessageBox.StandardButton.Yes:
            return
        self.model.remove_rows(rows)
        self.apply_filter()