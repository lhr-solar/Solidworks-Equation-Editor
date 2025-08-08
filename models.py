from PyQt6.QtCore import Qt, QAbstractTableModel, QModelIndex

COLUMNS = ['Variable', 'Expression', 'Section', 'Comment']


class EquationModel(QAbstractTableModel):
    def __init__(self, equations, cfg, parent=None):
        super().__init__(parent)
        self.equations = equations
        self.cfg = cfg
        self.rebuild_section_map()

    def rebuild_section_map(self):
        self.name_to_section = {}
        for sec, names in self.cfg.get('sections', {}).items():
            for n in names:
                self.name_to_section[n] = sec

    def rowCount(self, parent=QModelIndex()):
        return len(self.equations)

    def columnCount(self, parent=QModelIndex()):
        return len(COLUMNS)

    def headerData(self, section, orientation, role):
        if role == Qt.ItemDataRole.DisplayRole and orientation == Qt.Orientation.Horizontal:
            return COLUMNS[section]
        return None

    def data(self, index, role):
        if not index.isValid():
            return None
        row = index.row()
        col = index.column()
        item = self.equations[row]
        if role in (Qt.ItemDataRole.DisplayRole, Qt.ItemDataRole.EditRole):
            if col == 0:
                return item['name']
            elif col == 1:
                return item['expr']
            elif col == 2:
                return self.name_to_section.get(item['name'], 'Unassigned')
            elif col == 3:
                return self.cfg.get('comments', {}).get(item['name'], '')
        return None

    def flags(self, index):
        if not index.isValid():
            return Qt.ItemFlag.NoItemFlags
        return Qt.ItemFlag.ItemIsSelectable | Qt.ItemFlag.ItemIsEnabled | Qt.ItemFlag.ItemIsEditable

    def setData(self, index, value, role):
        if role != Qt.ItemDataRole.EditRole:
            return False
        row = index.row()
        col = index.column()
        item = self.equations[row]
        if col == 0:
            old_name = item['name']
            new_name = str(value).strip().strip('"')
            if not new_name:
                return False
            if any(e['name'] == new_name for i, e in enumerate(self.equations) if i != row):
                return False
            item['name'] = new_name
            sec = self.name_to_section.pop(old_name, 'Unassigned')
            if sec not in self.cfg['sections']:
                self.cfg['sections'][sec] = []
            if old_name in self.cfg['sections'][sec]:
                self.cfg['sections'][sec].remove(old_name)
            if new_name not in self.cfg['sections'][sec]:
                self.cfg['sections'][sec].append(new_name)
            self.rebuild_section_map()

            comments = self.cfg.setdefault('comments', {})
            if old_name in comments:
                comments[new_name] = comments.pop(old_name)
        elif col == 1:
            item['expr'] = str(value).strip()
        elif col == 2:
            new_sec = str(value).strip() or 'Unassigned'
            old_sec = self.name_to_section.get(item['name'], 'Unassigned')
            if new_sec not in self.cfg['sections']:
                self.cfg['sections'][new_sec] = []
            if item['name'] in self.cfg['sections'].get(old_sec, []):
                self.cfg['sections'][old_sec].remove(item['name'])
            if item['name'] not in self.cfg['sections'][new_sec]:
                self.cfg['sections'][new_sec].append(item['name'])
            for sec in list(self.cfg['sections'].keys()):
                if sec != 'Unassigned' and not self.cfg['sections'][sec]:
                    del self.cfg['sections'][sec]
            self.rebuild_section_map()
        elif col == 3:
            self.cfg.setdefault('comments', {})[item['name']] = str(value)
        else:
            return False
        self.dataChanged.emit(index, index)
        return True

    def add_equation(self, name, expr, section='Unassigned'):
        name = name.strip().strip('"')
        if not name:
            return
        if any(e['name'] == name for e in self.equations):
            return
        self.beginInsertRows(QModelIndex(), len(self.equations), len(self.equations))
        self.equations.append({'name': name, 'expr': expr})
        self.endInsertRows()
        if section not in self.cfg['sections']:
            self.cfg['sections'][section] = []
        if name not in self.cfg['sections'][section]:
            self.cfg['sections'][section].append(name)
        self.rebuild_section_map()

    def remove_rows(self, rows):
        for row in sorted(rows, reverse=True):
            if 0 <= row < len(self.equations):
                name = self.equations[row]['name']
                self.beginRemoveRows(QModelIndex(), row, row)
                self.equations.pop(row)
                self.endRemoveRows()
                for sec in list(self.cfg['sections'].keys()):
                    if name in self.cfg['sections'][sec]:
                        self.cfg['sections'][sec].remove(name)
                        if not self.cfg['sections'][sec] and sec != 'Unassigned':
                            del self.cfg['sections'][sec]
                        self.cfg.setdefault('comments', {}).pop(name, None)
        self.rebuild_section_map()
