#!/usr/bin/env python3
import sys
import subprocess
import os
import re
import time
from pathlib import Path
from PyQt6.QtWidgets import *
from PyQt6.QtCore import *
from PyQt6.QtGui import QColor, QStandardItemModel, QStandardItem
import json


class CommitListDelegate(QStyledItemDelegate):
    HASH_RE = re.compile(r'^[0-9a-fA-F]{7,40}$')

    def paint(self, painter, option, index):
        text = index.data(Qt.ItemDataRole.DisplayRole) or ""
        if not isinstance(text, str) or not text.strip():
            super().paint(painter, option, index)
            return

        parts = text.split(maxsplit=1)
        commit_hash = parts[0] if parts else ""
        if not self.HASH_RE.match(commit_hash):
            super().paint(painter, option, index)
            return

        painter.save()

        if option.state & QStyle.StateFlag.State_Selected:
            painter.fillRect(option.rect, option.palette.highlight())

        base_color = option.palette.highlightedText().color() if (option.state & QStyle.StateFlag.State_Selected) else option.palette.text().color()
        hash_color = QColor("#FFD700")
        if option.state & QStyle.StateFlag.State_Selected:
            hash_color = hash_color.lighter(120)

        rect = option.rect.adjusted(6, 0, -6, 0)
        fm = option.fontMetrics
        baseline_y = rect.y() + (rect.height() + fm.ascent() - fm.descent()) // 2

        painter.setFont(option.font)
        painter.setPen(hash_color)
        painter.drawText(rect.x(), baseline_y, commit_hash)

        message = parts[1] if len(parts) > 1 else ""
        if message:
            hash_width = fm.horizontalAdvance(commit_hash + " ")
            painter.setPen(base_color)
            painter.drawText(rect.x() + hash_width, baseline_y, message)

        painter.restore()


class AutoRefreshComboBox(QComboBox):
    def __init__(self, refresh_callback=None, parent=None):
        super().__init__(parent)
        self.refresh_callback = refresh_callback

    def showPopup(self):
        if callable(self.refresh_callback):
            try:
                self.refresh_callback()
            except Exception:
                pass
        super().showPopup()


class BranchTreeComboBox(QWidget):
    branchSelected = pyqtSignal(str)

    def __init__(self, refresh_callback=None, parent=None):
        super().__init__(parent)
        self.refresh_callback = refresh_callback
        self._selected_branch = ''
        self._all_label = 'All (--all)'
        self._pinned_branches = set()

        row = QHBoxLayout(self)
        row.setContentsMargins(0, 0, 0, 0)
        row.setSpacing(0)

        self._edit = QLineEdit()
        self._edit.setReadOnly(True)
        self._edit.mousePressEvent = lambda e: self._toggle_popup()
        row.addWidget(self._edit)

        # Floating popup — Qt.Popup auto-closes when focus is lost
        self._popup = QFrame(None, Qt.WindowType.Popup)
        self._popup.setFrameShape(QFrame.Shape.StyledPanel)
        pl = QVBoxLayout(self._popup)
        pl.setContentsMargins(2, 2, 2, 2)
        pl.setSpacing(0)

        self._tree = QTreeWidget()
        self._tree.setHeaderHidden(True)
        self._tree.setRootIsDecorated(True)
        self._tree.setExpandsOnDoubleClick(False)
        self._tree.itemClicked.connect(self._on_item_clicked)
        pl.addWidget(self._tree)

    def _toggle_popup(self):
        if self._popup.isVisible():
            self._popup.hide()
            return
        if callable(self.refresh_callback):
            try:
                self.refresh_callback()
            except Exception:
                pass
        pos = self.mapToGlobal(QPoint(0, self.height()))
        self._popup.resize(max(self.width(), 320), 260)
        self._popup.move(pos)
        self._popup.show()

    def _on_item_clicked(self, item, column):
        if item.childCount() > 0:
            item.setExpanded(not item.isExpanded())
            return
        branch_value = item.data(0, Qt.ItemDataRole.UserRole)
        if branch_value is not None:
            self._selected_branch = str(branch_value)
            self._edit.setText(self._display_text(self._selected_branch))
            self._popup.hide()
            self.branchSelected.emit(self._selected_branch)

    def selected_branch(self):
        return self._selected_branch

    def _display_text(self, branch):
        if not branch:
            return self._all_label
        if branch in self._pinned_branches:
            return f'📌 {branch}'
        return branch

    def set_selected_branch(self, branch):
        self._selected_branch = branch or ''
        self._edit.setText(self._display_text(self._selected_branch))

    def update_all_label(self, all_label):
        self._all_label = all_label
        for i in range(self._tree.topLevelItemCount()):
            item = self._tree.topLevelItem(i)
            if item and item.data(0, Qt.ItemDataRole.UserRole) == '':
                item.setText(0, all_label)
                break
        if not self._selected_branch:
            self._edit.setText(self._display_text(''))

    def set_branch_data(self, all_label, pinned_branches, other_branches, selected_branch=''):
        self._all_label = all_label
        self._pinned_branches = set(pinned_branches)
        self._tree.clear()

        all_item = QTreeWidgetItem([all_label])
        all_item.setData(0, Qt.ItemDataRole.UserRole, '')
        self._tree.addTopLevelItem(all_item)

        def find_or_create(parent, text):
            for i in range(parent.childCount()):
                child = parent.child(i)
                if child and child.text(0) == text:
                    return child
            new_child = QTreeWidgetItem([text])
            parent.addChild(new_child)
            return new_child

        def add_branch(full_branch, pinned=False):
            parts = [p for p in full_branch.split('/') if p]
            if not parts:
                return
            if pinned:
                # Flat top-level item with full branch name
                item = QTreeWidgetItem([f"📌 {full_branch}"])
                item.setData(0, Qt.ItemDataRole.UserRole, full_branch)
                item.setToolTip(0, full_branch)
                self._tree.insertTopLevelItem(self._tree.topLevelItemCount(), item)
            else:
                parent = self._tree.invisibleRootItem()
                for part in parts[:-1]:
                    parent = find_or_create(parent, part)
                leaf = find_or_create(parent, parts[-1])
                leaf.setData(0, Qt.ItemDataRole.UserRole, full_branch)
                leaf.setToolTip(0, full_branch)

        for branch in pinned_branches:
            add_branch(branch, pinned=True)
        for branch in other_branches:
            add_branch(branch, pinned=False)

        self._tree.collapseAll()
        self.set_selected_branch(selected_branch)


class GitSearcher(QMainWindow):
    DEFAULT_PAGE_SIZE = 300
    QUICK_LOAD_PAGE_SIZE = 50
    BRANCH_CACHE_TTL = 30.0
    COMMIT_FILTER_CACHE_TTL = 45.0
    COMMIT_FILTER_MAX = 150

    def __init__(self):
        super().__init__()
        self.i18n_file = self._resource_path("i18n.json")
        self.settings_file = Path.home() / ".git_commit_search_settings.json"
        self.settings = self.load_settings()
        self.language = self.settings.get('language', 'it')
        self.texts = self.load_translations()
        self.pinned_branches = set(self.settings.get('pinned_branches', []))
        self.desired_branch = self.settings.get('selected_branch', '')
        self.desired_since_hash = self.settings.get('since_hash', '')
        self.desired_until_hash = self.settings.get('until_hash', '')
        self.page_size = self.DEFAULT_PAGE_SIZE
        self.current_offset = 0
        self.has_more_results = True
        self.is_loading_results = False
        self._cached_branches = []
        self._cached_branches_ts = 0.0
        self._cached_commits = []
        self._cached_commits_ts = 0.0
        self._cached_commits_branch = None
        self.view_commits_mode = False
        self._saved_view_state = None
        self.repo_path = self.load_last_repo()
        self.timer = QTimer(); self.timer.setSingleShot(True); self.timer.timeout.connect(self.search)
        self.settings_save_timer = QTimer()
        self.settings_save_timer.setSingleShot(True)
        self.settings_save_timer.timeout.connect(self.save_settings)
        self.setWindowTitle(self.txt('window_title'))
        self.setGeometry(100, 100, 900, 700)
        
        # Single instance check
        self.lock_file = Path.home() / ".git_search_engine.lock"
        try:
            if self.lock_file.exists():
                self.lock_file.unlink(missing_ok=True)
            self.lock_file.write_text(str(os.getpid()), encoding='utf-8')
            self.destroyed.connect(lambda: self.lock_file.unlink(missing_ok=True))
        except Exception:
            pass
        
        central = QWidget(); self.setCentralWidget(central); layout = QVBoxLayout(central)
        
        # Header
        row1 = QHBoxLayout()
        self.path_label = QLabel("")
        row1.addWidget(self.path_label)

        self.btn_paste_repo = QPushButton()
        self.btn_paste_repo.setFixedWidth(36)
        self.btn_paste_repo.clicked.connect(self.paste_repo_from_clipboard)
        row1.addWidget(self.btn_paste_repo)

        self.btn_change = QPushButton()
        self.btn_change.clicked.connect(self.change_repo)
        row1.addWidget(self.btn_change)

        row1.addStretch()
        self.lang_label = QLabel()
        row1.addWidget(self.lang_label)
        self.lang_combo = QComboBox()
        self.lang_combo.addItem("🇮🇹", "it")
        self.lang_combo.addItem("🇬🇧", "en")
        lang_idx = self.lang_combo.findData(self.language)
        if lang_idx >= 0:
            self.lang_combo.setCurrentIndex(lang_idx)
        self.lang_combo.currentIndexChanged.connect(self.on_language_changed)
        row1.addWidget(self.lang_combo)
        layout.addLayout(row1)
        
        # Search row
        row2 = QHBoxLayout()
        self.search_edit = QLineEdit()
        self.search_edit.setText(self.settings.get('search_text', ''))
        self.search_edit.textChanged.connect(self.debounce_search); row2.addWidget(self.search_edit)
        self.search_edit.textChanged.connect(lambda _value: self.schedule_save_settings())
        
        self.btn_search = QPushButton(); self.btn_search.clicked.connect(self.search)
        row2.addWidget(self.btn_search)
        self.btn_load_commits = QPushButton()
        self.btn_load_commits.setCheckable(True)
        self.btn_load_commits.toggled.connect(self.on_toggle_view_commits)
        row2.addWidget(self.btn_load_commits)
        layout.addLayout(row2)
        
        # Flags
        self.flags_gb = QGroupBox(); flags_layout = QGridLayout(self.flags_gb)
        self.case_cb = QCheckBox("🔤 Match Case"); flags_layout.addWidget(self.case_cb, 0, 0)
        self.word_cb = QCheckBox("📝 Whole Word"); flags_layout.addWidget(self.word_cb, 0, 1)
        self.regex_cb = QCheckBox("⚡ Regex"); flags_layout.addWidget(self.regex_cb, 0, 2)
        self.case_cb.setChecked(bool(self.settings.get('match_case', False)))
        self.word_cb.setChecked(bool(self.settings.get('whole_word', False)))
        self.regex_cb.setChecked(bool(self.settings.get('regex', False)))
        self.case_cb.toggled.connect(lambda _checked: self.schedule_save_settings())
        self.word_cb.toggled.connect(lambda _checked: self.schedule_save_settings())
        self.regex_cb.toggled.connect(lambda _checked: self.schedule_save_settings())

        self.since_combo = AutoRefreshComboBox(self.populate_commit_filters); self.since_combo.setEditable(True); self.since_combo.setInsertPolicy(QComboBox.InsertPolicy.NoInsert)
        self.since_combo.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self.since_combo.currentTextChanged.connect(lambda _value: self.schedule_save_settings())
        self.lbl_since = QLabel()
        flags_layout.addWidget(self.lbl_since, 1, 0); flags_layout.addWidget(self.since_combo, 1, 1)

        self.until_combo = AutoRefreshComboBox(self.populate_commit_filters); self.until_combo.setEditable(True); self.until_combo.setInsertPolicy(QComboBox.InsertPolicy.NoInsert)
        self.until_combo.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self.until_combo.currentTextChanged.connect(lambda _value: self.schedule_save_settings())
        self.lbl_until = QLabel()
        flags_layout.addWidget(self.lbl_until, 1, 2); flags_layout.addWidget(self.until_combo, 1, 3)

        self.branch_combo = BranchTreeComboBox(self.populate_branches)
        self.branch_combo.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self.branch_combo.branchSelected.connect(self.on_branch_selected)
        self.lbl_branch = QLabel()
        flags_layout.addWidget(self.lbl_branch, 2, 0); flags_layout.addWidget(self.branch_combo, 2, 1, 1, 2)
        self.btn_pin_branch = QPushButton(); self.btn_pin_branch.clicked.connect(self.toggle_pin_current_branch)
        flags_layout.addWidget(self.btn_pin_branch, 2, 3)
        current_pin_width = self.btn_pin_branch.sizeHint().width()
        self.btn_pin_branch.setFixedWidth(max(36, current_pin_width // 1.5))
        layout.addWidget(self.flags_gb)
        
        # Status + Actions
        row3 = QHBoxLayout()
        self.status_label = QLabel(); row3.addWidget(self.status_label)
        layout.addLayout(row3)
        
        # Results
        self.list_widget = QListWidget(); self.list_widget.itemDoubleClicked.connect(self.copy_hash)
        self.list_widget.setItemDelegate(CommitListDelegate(self.list_widget))
        self.list_widget.verticalScrollBar().valueChanged.connect(self.on_scroll)

        row_results = QHBoxLayout()
        self.results_label = QLabel()
        row_results.addWidget(self.results_label)
        row_results.addStretch()
        self.btn_export = QPushButton(); self.btn_export.clicked.connect(self.export_txt)
        row_results.addWidget(self.btn_export)
        layout.addLayout(row_results)

        layout.addWidget(self.list_widget)

        self.update_path_label()
        self.apply_language_to_ui()
        self.branch_combo.set_branch_data(self.txt('all_branches'), [], [], selected_branch='')
        self.status_label.setText(self.txt('status_ready'))

    @staticmethod
    def _resource_path(filename: str) -> Path:
        # Resolve bundled resources both in source mode and PyInstaller onefile/onedir mode.
        if getattr(sys, 'frozen', False) and hasattr(sys, '_MEIPASS'):
            return Path(getattr(sys, '_MEIPASS')) / filename
        return Path(__file__).resolve().with_name(filename)
    
    def debounce_search(self): self.timer.start(300)

    def schedule_save_settings(self):
        self.settings_save_timer.start(700)

    def txt(self, key, **kwargs):
        default_pack = self.texts.get('it', {})
        lang_pack = self.texts.get(self.language, default_pack)
        value = lang_pack.get(key, key)
        return value.format(**kwargs) if kwargs else value

    def load_translations(self):
        candidates = [self.i18n_file]
        if getattr(sys, 'frozen', False):
            candidates.append(Path(sys.executable).resolve().with_name("i18n.json"))
        candidates.append(Path.cwd() / "i18n.json")

        for candidate in candidates:
            try:
                if candidate.exists():
                    data = json.loads(candidate.read_text(encoding='utf-8'))
                    if isinstance(data, dict):
                        return data
            except Exception:
                continue

        return {'it': {}, 'en': {}}

    def load_settings(self):
        if not self.settings_file.exists():
            return {}
        try:
            data = json.loads(self.settings_file.read_text(encoding='utf-8'))
            if isinstance(data, dict):
                return data
        except Exception:
            pass
        return {}

    def load_last_repo(self):
        default_repo = Path.cwd()
        try:
            saved_repo = self.settings.get('last_repo')
            if saved_repo:
                candidate = Path(saved_repo)
                if candidate.exists() and (candidate / '.git').exists():
                    return candidate
        except Exception:
            pass
        return default_repo

    def save_settings(self):
        try:
            payload = {
                'last_repo': str(self.repo_path),
                'language': self.language,
                'pinned_branches': sorted(self.pinned_branches)
            }
            if hasattr(self, 'search_edit'):
                payload['search_text'] = self.search_edit.text()
            if hasattr(self, 'case_cb'):
                payload['match_case'] = self.case_cb.isChecked()
            if hasattr(self, 'word_cb'):
                payload['whole_word'] = self.word_cb.isChecked()
            if hasattr(self, 'regex_cb'):
                payload['regex'] = self.regex_cb.isChecked()
            if hasattr(self, 'branch_combo'):
                payload['selected_branch'] = self.current_branch()
            if hasattr(self, 'since_combo'):
                payload['since_hash'] = self.current_commit_hash(self.since_combo)
            if hasattr(self, 'until_combo'):
                payload['until_hash'] = self.current_commit_hash(self.until_combo)
            self.settings_file.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding='utf-8')
        except Exception:
            pass

    def update_path_label(self):
        self.path_label.setText(f"📁 {self.repo_path}")

    def apply_language_to_ui(self):
        self.setWindowTitle(self.txt('window_title'))
        self.btn_paste_repo.setText(self.txt('btn_paste_repo'))
        self.btn_change.setText(self.txt('btn_change_repo'))
        self.lang_label.setText(self.txt('lbl_language'))
        self.btn_search.setText(self.txt('btn_search'))
        self.update_load_commits_button_ui()
        self.flags_gb.setTitle(self.txt('filters_title'))
        self.lbl_since.setText(self.txt('lbl_since'))
        self.lbl_until.setText(self.txt('lbl_until'))
        self.lbl_branch.setText(self.txt('lbl_branch'))
        self.btn_pin_branch.setText(self.txt('btn_pin_branch'))
        self.btn_export.setText(self.txt('btn_export_txt'))
        self.results_label.setText(self.txt('results_title'))
        it_ready = self.texts.get('it', {}).get('status_ready')
        en_ready = self.texts.get('en', {}).get('status_ready')
        if not self.status_label.text() or self.status_label.text() in [
            it_ready,
            en_ready
        ]:
            self.status_label.setText(self.txt('status_ready'))

        self.search_edit.setPlaceholderText(self.txt('ph_search'))

        self.path_label.setToolTip(self.txt('tt_path'))
        self.btn_paste_repo.setToolTip(self.txt('tt_paste_repo'))
        self.btn_change.setToolTip(self.txt('tt_change_repo'))
        self.lang_combo.setToolTip(self.txt('tt_language'))
        self.search_edit.setToolTip(self.txt('tt_search'))
        self.btn_search.setToolTip(self.txt('tt_search'))
        self.update_load_commits_button_ui()
        self.case_cb.setToolTip(self.txt('tt_case'))
        self.word_cb.setToolTip(self.txt('tt_word'))
        self.regex_cb.setToolTip(self.txt('tt_regex'))
        self.since_combo.setToolTip(self.txt('tt_since'))
        self.until_combo.setToolTip(self.txt('tt_until'))
        self.branch_combo.setToolTip(self.txt('tt_branch'))
        self.btn_pin_branch.setToolTip(self.txt('tt_pin_branch'))
        self.btn_export.setToolTip(self.txt('tt_export'))
        self.status_label.setToolTip(self.txt('tt_status'))
        self.list_widget.setToolTip(self.txt('tt_results'))

    def on_language_changed(self, _index):
        selected_language = self.lang_combo.currentData()
        if selected_language not in ('it', 'en'):
            return
        if selected_language == self.language:
            return
        self.language = selected_language
        self.apply_language_to_ui()
        self.branch_combo.update_all_label(self.txt('all_branches'))
        self.save_settings()

    def on_branch_selected(self, branch):
        self.desired_branch = branch or ''
        self._cached_commits = []
        self._cached_commits_ts = 0.0
        self._cached_commits_branch = None
        self.schedule_save_settings()

    def update_load_commits_button_ui(self):
        if not hasattr(self, 'btn_load_commits'):
            return
        if self.view_commits_mode:
            self.btn_load_commits.setText(self.txt('btn_hide_commits'))
            self.btn_load_commits.setToolTip(self.txt('tt_hide_commits'))
        else:
            self.btn_load_commits.setText(self.txt('btn_load_commits'))
            self.btn_load_commits.setToolTip(self.txt('tt_load_commits'))

    def on_toggle_view_commits(self, checked):
        self.view_commits_mode = bool(checked)
        self.update_load_commits_button_ui()
        if self.view_commits_mode:
            self._saved_view_state = {
                'search_text': self.search_edit.text(),
                'case': self.case_cb.isChecked(),
                'word': self.word_cb.isChecked(),
                'regex': self.regex_cb.isChecked(),
                'since': self.current_commit_hash(self.since_combo),
                'until': self.current_commit_hash(self.until_combo),
            }
            self.load_recent_commits()
            return

        self.page_size = self.DEFAULT_PAGE_SIZE
        self.current_offset = 0
        self.has_more_results = False
        self.search_edit.clear()
        self.case_cb.setChecked(False)
        self.word_cb.setChecked(False)
        self.regex_cb.setChecked(False)
        self.since_combo.setCurrentIndex(0)
        self.until_combo.setCurrentIndex(0)
        self.list_widget.clear()
        self.status_label.setText(self.txt('status_ready'))

    def run_git(self, args, timeout=40):
        cmd = ['git', '-C', str(self.repo_path)] + args
        return subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)

    def is_git_repo(self):
        return (self.repo_path / '.git').exists()

    def set_repo_path(self, new_repo: Path):
        self.repo_path = new_repo
        self._cached_branches = []
        self._cached_branches_ts = 0.0
        self._cached_commits = []
        self._cached_commits_ts = 0.0
        self._cached_commits_branch = None
        self.update_path_label()
        self.save_settings()
        self.refresh_git_lists()
        self.search()

    def paste_repo_from_clipboard(self):
        raw_text = QApplication.clipboard().text().strip().strip('"').strip("'")
        if not raw_text:
            QMessageBox.information(self, self.txt('info_title'), self.txt('msg_clipboard_empty'))
            return

        candidate = Path(raw_text)
        if not candidate.exists():
            QMessageBox.warning(self, self.txt('warn_invalid_repo_title'), self.txt('msg_clipboard_not_exists'))
            return
        if candidate.is_file():
            candidate = candidate.parent
        if not (candidate / '.git').exists():
            QMessageBox.warning(self, self.txt('warn_invalid_repo_title'), self.txt('msg_clipboard_not_git'))
            return

        self.set_repo_path(candidate)
    
    def change_repo(self):
        folder = QFileDialog.getExistingDirectory(self, self.txt('dialog_git_repo'))
        if folder:
            new_repo = Path(folder)
            if not (new_repo / '.git').exists():
                QMessageBox.warning(self, self.txt('warn_invalid_repo_title'), self.txt('warn_invalid_repo_msg'))
                return
            self.set_repo_path(new_repo)

    def refresh_git_lists(self):
        self.populate_branches(force=True)
        self.populate_commit_filters(force=True)

    def _branch_sort_key(self, branch):
        return tuple(part.lower() for part in branch.split('/'))

    def _branch_display(self, branch, pinned=False):
        parts = branch.split('/')
        depth = max(0, len(parts) - 1)
        leaf = parts[-1] if parts else branch
        indent = '  ' * depth
        marker = '📌 ' if pinned else ''
        return f"{marker}{indent}{leaf}"

    def toggle_pin_current_branch(self):
        branch = self.current_branch() or self.desired_branch
        if not isinstance(branch, str) or not branch:
            return

        if branch in self.pinned_branches:
            self.pinned_branches.remove(branch)
            self.status_label.setText(self.txt('status_branch_unpinned', branch=branch))
        else:
            self.pinned_branches.add(branch)
            self.status_label.setText(self.txt('status_branch_pinned', branch=branch))

        self.desired_branch = branch
        self.schedule_save_settings()
        self.populate_branches()

    def populate_branches(self, force=False):
        previous_data = self.branch_combo.selected_branch() or self.desired_branch

        branches = []
        now = time.monotonic()
        use_cache = (
            not force and
            self._cached_branches and
            (now - self._cached_branches_ts) <= self.BRANCH_CACHE_TTL
        )

        if use_cache:
            branches = list(self._cached_branches)
        elif self.is_git_repo():
            try:
                result = self.run_git(['for-each-ref', '--format=%(refname:short)', 'refs/heads', 'refs/remotes'])
                if result.returncode == 0:
                    branches = sorted({line.strip() for line in result.stdout.splitlines() if line.strip()}, key=self._branch_sort_key)
                    self._cached_branches = list(branches)
                    self._cached_branches_ts = now
            except Exception:
                pass

        branch_set = set(branches)
        self.pinned_branches.intersection_update(branch_set)

        pinned = sorted(self.pinned_branches, key=self._branch_sort_key)
        others = sorted(branch_set.difference(self.pinned_branches), key=self._branch_sort_key)

        selected_branch = previous_data if previous_data in branch_set else ''
        self.branch_combo.set_branch_data(self.txt('all_branches'), pinned, others, selected_branch=selected_branch)
        self.desired_branch = selected_branch
        self.schedule_save_settings()

    def populate_commit_filters(self, force=False):
        current_since_hash = self.current_commit_hash(self.since_combo) or self.desired_since_hash
        current_until_hash = self.current_commit_hash(self.until_combo) or self.desired_until_hash

        self.since_combo.blockSignals(True)
        self.until_combo.blockSignals(True)
        self.since_combo.clear()
        self.until_combo.clear()
        self.since_combo.addItem('')
        self.until_combo.addItem('')

        now = time.monotonic()
        selected_branch = self.current_branch().strip()
        use_cache = (
            not force and
            self._cached_commits and
            self._cached_commits_branch == selected_branch and
            (now - self._cached_commits_ts) <= self.COMMIT_FILTER_CACHE_TTL
        )

        commits = []
        if use_cache:
            commits = list(self._cached_commits)
        elif self.is_git_repo():
            try:
                log_args = ['log', '--oneline', f'--max-count={self.COMMIT_FILTER_MAX}']
                if selected_branch:
                    log_args.append(selected_branch)
                else:
                    log_args.append('--all')
                result = self.run_git(log_args)
                if result.returncode == 0:
                    commits = [line.strip() for line in result.stdout.splitlines() if line.strip()]
                    self._cached_commits = list(commits)
                    self._cached_commits_ts = now
                    self._cached_commits_branch = selected_branch
            except Exception:
                pass

        for cleaned in commits:
            commit_hash = cleaned.split(maxsplit=1)[0]
            self.since_combo.addItem(cleaned, commit_hash)
            self.until_combo.addItem(cleaned, commit_hash)

        if current_since_hash:
            since_index = self.since_combo.findData(current_since_hash, Qt.ItemDataRole.UserRole)
            if since_index >= 0:
                self.since_combo.setCurrentIndex(since_index)
            else:
                self.since_combo.setCurrentText(current_since_hash)
        if current_until_hash:
            until_index = self.until_combo.findData(current_until_hash, Qt.ItemDataRole.UserRole)
            if until_index >= 0:
                self.until_combo.setCurrentIndex(until_index)
            else:
                self.until_combo.setCurrentText(current_until_hash)
        self.since_combo.blockSignals(False)
        self.until_combo.blockSignals(False)
        self.desired_since_hash = self.current_commit_hash(self.since_combo)
        self.desired_until_hash = self.current_commit_hash(self.until_combo)
        self.schedule_save_settings()

    def current_branch(self):
        if hasattr(self.branch_combo, 'selected_branch'):
            selected = self.branch_combo.selected_branch()
            if selected:
                return selected
        return self.desired_branch or ''

    def current_commit_hash(self, combo: QComboBox):
        text = combo.currentText().strip()
        if not text:
            return ''
        if ' ' in text:
            return text.split(maxsplit=1)[0]
        return text
    
    def build_log_args(self):
        args = ['log']
        grep_opt = self.search_edit.text().strip()

        # Branch
        branch = self.current_branch()
        if branch:
            args.append(branch)
        else:
            args.append('--all')

        if grep_opt:
            args.append(f'--grep={grep_opt}')
            if not self.case_cb.isChecked():
                args.append('-i')
            if self.word_cb.isChecked():
                args.append('-w')
            if self.regex_cb.isChecked():
                args.append('-E')

        # Since/Until
        since = self.current_commit_hash(self.since_combo)
        until = self.current_commit_hash(self.until_combo)
        if since and until:
            args.append(f'{since}..{until}')
        elif since:
            args.append(f'{since}..HEAD')
        elif until:
            args.append(until)

        args.append('--oneline')
        return args
    
    def search(self):
        if not self.is_git_repo():
            self.list_widget.clear()
            self.status_label.setText(self.txt('status_not_git'))
            return

        if self.view_commits_mode:
            self.btn_load_commits.blockSignals(True)
            self.btn_load_commits.setChecked(False)
            self.btn_load_commits.blockSignals(False)
            self.view_commits_mode = False
            self.update_load_commits_button_ui()

        self.page_size = self.DEFAULT_PAGE_SIZE
        self.current_offset = 0
        self.has_more_results = True
        self.list_widget.clear()
        self.status_label.setText(self.txt('status_searching'))
        QApplication.processEvents()
        self.load_more_results()

    def load_recent_commits(self):
        if not self.is_git_repo():
            self.list_widget.clear()
            self.status_label.setText(self.txt('status_not_git'))
            return

        self.page_size = self.QUICK_LOAD_PAGE_SIZE
        self.current_offset = 0
        self.has_more_results = True
        self.list_widget.clear()
        self.status_label.setText(self.txt('status_searching'))
        self.search_edit.clear()
        self.case_cb.setChecked(False)
        self.word_cb.setChecked(False)
        self.regex_cb.setChecked(False)
        self.since_combo.setCurrentIndex(0)
        self.until_combo.setCurrentIndex(0)
        QApplication.processEvents()
        self.load_more_results()

    def load_more_results(self):
        if self.is_loading_results or not self.has_more_results:
            return

        self.is_loading_results = True
        is_infinite_scroll_load = self.current_offset > 0
        if is_infinite_scroll_load:
            self.status_label.setText(self.txt('status_loading_more'))
            self.list_widget.addItem(self.txt('status_loading_more'))
        args = self.build_log_args()
        args.extend([f'--skip={self.current_offset}', f'--max-count={self.page_size}'])

        try:
            result = self.run_git(args, timeout=120)
            if is_infinite_scroll_load and self.list_widget.count() > 0:
                last_item = self.list_widget.item(self.list_widget.count() - 1)
                if last_item and last_item.text() == self.txt('status_loading_more'):
                    self.list_widget.takeItem(self.list_widget.count() - 1)

            if result.returncode != 0:
                self.status_label.setText(self.txt('status_error', error=result.stderr.strip() or 'Git error'))
                self.has_more_results = False
            elif result.stdout.strip():
                lines = [line for line in result.stdout.splitlines() if line.strip()]
                for line in lines:
                    self.list_widget.addItem(line.strip())
                self.current_offset += len(lines)
                self.has_more_results = len(lines) == self.page_size
                if self.has_more_results:
                    self.status_label.setText(self.txt('status_loaded_more', count=self.list_widget.count()))
                else:
                    self.status_label.setText(self.txt('status_found', count=self.list_widget.count()))
            else:
                if self.current_offset == 0:
                    self.status_label.setText(self.txt('status_no_results'))
                self.has_more_results = False
        except Exception as e:
            if is_infinite_scroll_load and self.list_widget.count() > 0:
                last_item = self.list_widget.item(self.list_widget.count() - 1)
                if last_item and last_item.text() == self.txt('status_loading_more'):
                    self.list_widget.takeItem(self.list_widget.count() - 1)
            self.status_label.setText(self.txt('status_error', error=str(e)))
            self.has_more_results = False
        finally:
            self.is_loading_results = False

    def on_scroll(self, value):
        bar = self.list_widget.verticalScrollBar()
        if bar.maximum() <= 0:
            return
        if value >= bar.maximum() - 8:
            self.load_more_results()
    
    def copy_hash(self, item):
        parts = item.text().split(maxsplit=1)
        if parts:
            QApplication.clipboard().setText(parts[0])
            if not item.text().endswith(" ✅"):
                item.setText(item.text() + " ✅")
    
    def export_txt(self):
        if not self.list_widget.count():
            return QMessageBox.information(self, self.txt('info_title'), self.txt('msg_nothing_to_export'))

        path, _ = QFileDialog.getSaveFileName(self, self.txt('dialog_export_txt'), "commits.txt", "TXT (*.txt)")
        if path:
            with open(path, 'w', encoding='utf-8') as f:
                for i in range(self.list_widget.count()):
                    line = self.list_widget.item(i).text().split(" ✅")[0]
                    f.write(f"{line}\n")
            self.status_label.setText(self.txt('status_exported', path=path))

if __name__ == "__main__":
    app = QApplication(sys.argv)
    # Single instance
    if len(app.arguments()) > 1 and app.arguments()[1] == '--single':
        pass
    win = GitSearcher()
    win.show()
    sys.exit(app.exec())
