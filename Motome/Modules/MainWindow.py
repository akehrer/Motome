# Import the future
from __future__ import print_function
from __future__ import unicode_literals
from __future__ import absolute_import

# Import standard library modules
import glob
import json
import logging
import os
import shutil
import sys
import time
import cPickle as pickle
import yaml
from datetime import datetime

# Import extra modules
import markdown

# Import Qt modules
from PySide import QtCore, QtGui

# Import application window view
from Motome.Views.MainWindow import Ui_MainWindow

# Import configuration values
from Motome.config import NOTE_EXTENSION, ZIP_EXTENSION, MEDIA_FOLDER, \
    APP_DIR, WINDOW_TITLE, UNSAFE_CHARS, VERSION, NOTE_DATA_DIR, HTML_FOLDER, HTML_EXTENSION, MOTOME_BLUE

# Import additional modules
from Motome.Modules.MotomeTextBrowser import MotomeTextBrowser, MotomeTextBrowser2
from Motome.Modules.NoteModel import NoteModel
from Motome.Modules.SettingsDialog import SettingsDialog
from Motome.Modules.AutoCompleterModel import AutoCompleteEdit
from Motome.Modules.Search import SearchModel
from Motome.Modules.Utils import build_preview_footer_html, build_preview_header_html, \
    diff_to_html, human_date, pickle_find_NoteModel

from Motome.Modules.Utils import transition_versions

# Set up the logger
logger = logging.getLogger(__name__)


class MainWindow(QtGui.QMainWindow):
    def __init__(self, parent=None):
        super(MainWindow, self).__init__(parent)

        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)

        self.setWindowTitle(WINDOW_TITLE)

        # load main window style
        main_style_path = os.path.join(APP_DIR, 'styles', 'main_window.css')
        main_style = self._read_file(main_style_path)
        self.setStyleSheet(main_style)

        # additional settings
        self.ui.notePreview.setOpenExternalLinks(True)

        # Set up directories
        self.user_home_dir = os.path.expanduser('~')
        self.app_data_dir = os.path.join(self.user_home_dir, '.Motome')
        self._notes_dir = ''
        self.notes_data_dir = ''

        # DB
        self.db_notes = {}

        # note file vars
        self.note_extension = NOTE_EXTENSION

        # create the app storage directory
        try:
            os.makedirs(self.app_data_dir)
            self.first_run = True
        except OSError:
            self.first_run = False

        # Configuration and defaults
        self.conf = {}
        self.record_on_exit = False
        self.record_on_switch = False
        self.title_as_filename = True
        self.first_line_title = True

        # Load configuration
        self.load_conf()

        # Set some configuration variables
        if 'conf_checkbox_recordonexit' in self.conf.keys() and int(self.conf['conf_checkbox_recordonexit']) > 0:
            self.record_on_exit = True
        else:
            self.record_on_exit = False
        if 'conf_checkbox_recordonswitch' in self.conf.keys() and int(self.conf['conf_checkbox_recordonswitch']) > 0:
            self.record_on_switch = True
        else:
            self.record_on_switch = False

        if 'conf_checkbox_titleasfilename' in self.conf.keys() and int(self.conf['conf_checkbox_titleasfilename']) > 0:
            self.title_as_filename = True
        else:
            self.title_as_filename = False
        if 'conf_checkbox_firstlinetitle' in self.conf.keys() and int(self.conf['conf_checkbox_firstlinetitle']) > 0:
            self.first_line_title = True
        else:
            self.first_line_title = False

        # keyboard shortcuts
        self.keyboard_shortcuts = {}
        self.setup_keyboard_shortcuts()

        # setup the ui
        self.noteEditor = None
        self.tagEditor = None
        self.setup_mainwindow()
        self.setup_preview()
        self.setup_diff()
        self.insert_ui_noteeditor()
        self.insert_ui_tageditor()
        self.insert_ui_tagcompleter()

        # Set the window location and size
        if 'window_x' in self.conf.keys():
            rect = QtCore.QRect(int(self.conf['window_x']),
                                int(self.conf['window_y']),
                                int(self.conf['window_width']),
                                int(self.conf['window_height']))
            self.setGeometry(rect)

        # load the text browser styles
        self.style_dir = os.path.join(APP_DIR, 'styles', 'default')
        self.load_styles()

        # markdown translator
        self.md = markdown.Markdown()

        # current view
        self._current_note = None
        self.old_data = None
        self.history = []

        # set the views
        self.set_ui_views()

        # notes list splitter size for hiding and showing the notes list
        self.notes_list_splitter_size = None

        # save file timer
        self.save_interval = 1000  # msec
        self.save_timer = QtCore.QTimer()
        self.save_timer.timeout.connect(self.save_note_meta)

        # search
        self.search = SearchModel()
        self.query = ''
        self.search_interval = 250  # msec
        self.search_timer = QtCore.QTimer()
        self.search_timer.timeout.connect(self.search_files)

        if not self.first_run:
            self.load_db_data()

        # notes
        self._notes_dir_last_seen = 0.0
        self._all_notes = self.load_notemodels()
        self.load_ui_notes_list(self.all_notes)

        if self.first_run:
            logger.info('First run')
            self.do_first_run()

        # update the views
        self.update_ui_views()

        # set the focus to the window frame
        self.setFocus(QtCore.Qt.ActiveWindowFocusReason)

    @property
    def notes_dir(self):
        return self._notes_dir

    @notes_dir.setter
    def notes_dir(self, value):
        """ Things to do when the notes directory changes """
        self._notes_dir = value
        self.notes_data_dir = os.path.join(self._notes_dir, NOTE_DATA_DIR)
        # set the db connection
        self.load_db_data()

    @property
    def all_notes(self):
        try:
            self._all_notes = self.load_notemodels()
        except OSError:
            pass
        return self._all_notes

    @property
    def current_note(self):
        try:
            i = self.current_row
            filename = self.ui.notesList.item(i).text() + NOTE_EXTENSION
            self._current_note = self.db_notes[filename]
        except (KeyError, AttributeError):
            self._current_note = None
        return self._current_note

    @property
    def current_row(self):
        i = self.ui.notesList.currentRow()
        if i < 0:
            return 0
        else:
            return i

    @current_row.setter
    def current_row(self, notename):
        try:
            list_item = self.ui.notesList.findItems(notename, QtCore.Qt.MatchExactly)[0]
            row = self.ui.notesList.row(list_item)
            if row != self.current_row:
                self.ui.notesList.setCurrentRow(row)
                self.update_ui_views()
        except IndexError:
            message_box = QtGui.QMessageBox()
            message_box.setText("Cannot open link.")
            message_box.setInformativeText('The {0} note is not in the current notes list.'.format(notename))
            ok_btn = message_box.addButton(QtGui.QMessageBox.Ok)
            message_box.setDefaultButton(ok_btn)
            message_box.exec_()

    def stop(self):
        if self.noteEditor.save_timer.isActive():
            self.noteEditor.save_note()

        if self.save_timer.isActive():
            self.save_note_meta()

        if self.record_on_exit:
            for note in self.db_notes.values():
                if not note.recorded:
                    note.record(self.notes_dir)

        self.save_db_data()

        window_geo = self.geometry()
        self.conf['window_x'] = window_geo.x()
        self.conf['window_y'] = window_geo.y()
        self.conf['window_width'] = window_geo.width()
        self.conf['window_height'] = window_geo.height()
        self.save_conf()

    def setup_mainwindow(self):
        # load main window style
        main_style_path = os.path.join(APP_DIR, 'styles', 'main_window.css')
        main_style = NoteModel.enc_read(main_style_path)
        self.setStyleSheet(main_style)

    def setup_preview(self):
        # catch link clicks in the Preview pane
        self.ui.notePreview.setOpenExternalLinks(True)
        self.ui.notePreview.anchorClicked.connect(self.load_anchor)
        self.ui.notePreview.setContextMenuPolicy(QtCore.Qt.CustomContextMenu)
        self.ui.notePreview.customContextMenuRequested.connect(self.show_custom_preview_menu)
        self.ui.notePreview.setSearchPaths(self.notes_dir)

    def setup_diff(self):
        self.ui.noteDiff.setContextMenuPolicy(QtCore.Qt.CustomContextMenu)
        self.ui.noteDiff.customContextMenuRequested.connect(self.show_custom_diff_menu)

    def setup_keyboard_shortcuts(self):
        """ Setup the keyboard shortcuts and load the keyboard_shortcuts dict for use elsewhere

        """
        esc = QtCore.Qt.Key_Escape
        delete = QtCore.Qt.Key_Delete
        self.keyboard_shortcuts = {'New': {'seq': QtGui.QKeySequence('Ctrl+N'),
                                           'func': lambda item=None: self.process_keyseq('ctrl_n')},
                                   'Find': {'seq': QtGui.QKeySequence('Ctrl+F'),
                                            'func': lambda item=None: self.process_keyseq('ctrl_f')},
                                   'ShowEdit': {'seq': QtGui.QKeySequence('Ctrl+E'),
                                                'func': lambda item=None: self.process_keyseq('ctrl_e')},
                                   'ShowPre': {'seq': QtGui.QKeySequence('Ctrl+W'),
                                               'func': lambda item=None: self.process_keyseq('ctrl_w')},
                                   'ShowDiff': {'seq': QtGui.QKeySequence('Ctrl+D'),
                                                'func': lambda item=None: self.process_keyseq('ctrl_d')},
                                   'NoteList': {'seq': QtGui.QKeySequence('Ctrl+L'),
                                                'func': lambda item=None: self.process_keyseq('ctrl_l')},
                                   'TagEdit': {'seq': QtGui.QKeySequence('Ctrl+T'),
                                               'func': lambda item=None: self.process_keyseq('ctrl_t')},
                                   'Save': {'seq': QtGui.QKeySequence('Ctrl+S'),
                                            'func': lambda item=None: self.process_keyseq('ctrl_s')},
                                   'Record': {'seq': QtGui.QKeySequence('Ctrl+R'),
                                              'func': lambda item=None: self.process_keyseq('ctrl_r')},
                                   'UpNote': {'seq': QtGui.QKeySequence('Ctrl+]'),
                                              'func': lambda item=None: self.process_keyseq('ctrl_up')},
                                   'DownNote': {'seq': QtGui.QKeySequence('Ctrl+['),
                                                'func': lambda item=None: self.process_keyseq('ctrl_down')},
                                   'BackHist': {'seq': QtGui.QKeySequence('Ctrl+<'),
                                                'func': lambda item=None: self.process_keyseq('ctrl_<')},
                                   'FwdHist': {'seq': QtGui.QKeySequence('Ctrl+>'),
                                               'func': lambda item=None: self.process_keyseq('ctrl_>')},
                                   'TglList': {'seq': QtGui.QKeySequence('Ctrl+Shift+L'),
                                               'func': lambda item=None: self.process_keyseq('ctrl_shift_l')},
                                   'TglHist': {'seq': QtGui.QKeySequence('Ctrl+Shift+H'),
                                               'func': lambda item=None: self.process_keyseq('ctrl_shift_h')},
                                   'TglOmni': {'seq': QtGui.QKeySequence('Ctrl+Shift+O'),
                                               'func': lambda item=None: self.process_keyseq('ctrl_shift_o')},
                                   'TglFull': {'seq': QtGui.QKeySequence('Ctrl+Shift+F'),
                                               'func': lambda item=None: self.process_keyseq('ctrl_shift_f')},
                                   'InsDate': {'seq': QtGui.QKeySequence('Ctrl+Shift+U'),
                                               'func': lambda item=None: self.process_keyseq('ctrl_shift_u')},
                                   'PinNote': {'seq': QtGui.QKeySequence('Ctrl+Shift+P'),
                                               'func': lambda item=None: self.process_keyseq('ctrl_shift_p')},
                                   'ClearOmni': {'seq': QtGui.QKeySequence(esc),
                                                 'func': lambda item=None: self.process_keyseq('esc')},
                                   'DelNote': {'seq': QtGui.QKeySequence(delete),
                                               'func': lambda item=None: self.delete_current_note()}
                                    }

        for s in self.keyboard_shortcuts.values():
            QtGui.QShortcut(s['seq'], self, s['func'])

    def insert_ui_noteeditor(self):
        # insert the custom text editor
        self.noteEditor = MotomeTextBrowser2(self.ui.tabEditor, None)
        self.noteEditor.setTextInteractionFlags(QtCore.Qt.LinksAccessibleByKeyboard | QtCore.Qt.LinksAccessibleByMouse |
                                                QtCore.Qt.TextBrowserInteraction | QtCore.Qt.TextEditable |
                                                QtCore.Qt.TextEditorInteraction | QtCore.Qt.TextSelectableByKeyboard |
                                                QtCore.Qt.TextSelectableByMouse)
        self.noteEditor.setObjectName("noteEditor")
        self.ui.horizontalLayout_3.insertWidget(1, self.noteEditor)
        self.noteEditor.anchorClicked.connect(self.load_anchor)
        self.noteEditor.noteSaved.connect(self.save_note_meta)
        # Custom right-click menu
        self.noteEditor.setContextMenuPolicy(QtCore.Qt.CustomContextMenu)
        self.noteEditor.customContextMenuRequested.connect(self.show_custom_editor_menu)

    def insert_ui_tageditor(self):
        # tag completer
        self.tagEditor = AutoCompleteEdit([])
        self.tagEditor.setObjectName("tagEditor")
        self.tagEditor.setFrame(False)
        self.ui.horizontalLayout_2.addWidget(self.tagEditor)
        self.tagEditor.textEdited.connect(self.start_meta_save)

    def insert_ui_tagcompleter(self):
        # build the completer list
        completer_list = set()
        for note in self.db_notes.values():
            if 'tags' in note.metadata.keys():
                for t in note.metadata['tags'].split():
                    completer_list.add(t)
        # attach a completer to the tag editor
        qlist = QtGui.QStringListModel(list(completer_list))
        try:
            self.tagEditor.setCompleterModel(qlist)
        except AttributeError:
            pass

    def set_ui_views(self):
        self.remove_history_bar()

    def load_conf(self):
        filepath = os.path.join(self.app_data_dir, 'conf.yml')
        try:
            data = NoteModel.enc_read(filepath)
            self.conf = yaml.safe_load(data)
            if not 'conf_notesLocation' in self.conf.keys():
                # Show the settings dialog if no notes location has been configured
                self.load_settings()
            else:
                self.notes_dir = self.conf['conf_notesLocation']
        except IOError as e:
            # No configuration file exists, create one
            self.save_conf()

    def save_conf(self):
        filepath = os.path.join(self.app_data_dir, 'conf.yml')
        self.conf['motome_version'] = VERSION
        self.conf['conf_update'] = time.time()
        try:
            data = yaml.safe_dump(self.conf, default_flow_style=False)
            out = '# Motome configuration values\n---\n' + data + '...'
            NoteModel.enc_write(filepath, out)
        except IOError:
            pass

    def load_anchor(self, url):
        url_path = url.path()

        # intranote link?
        if url_path + NOTE_EXTENSION in self.db_notes.keys():
            self.current_row = url_path
            return

        media_path = os.path.join(self.notes_dir, MEDIA_FOLDER, url_path.split('/')[-1])
        if os.path.isfile(media_path):
            ret = QtGui.QDesktopServices.openUrl(QtCore.QUrl('file:///' + media_path, QtCore.QUrl.TolerantMode))
        else:
            ret = QtGui.QDesktopServices.openUrl(url)

        if not ret:
            message_box = QtGui.QMessageBox()
            message_box.setText("Cannot open link.")
            message_box.setInformativeText('The link at {0} cannot be opened.'.format(media_path))
            ok_btn = message_box.addButton(QtGui.QMessageBox.Ok)
            message_box.setDefaultButton(ok_btn)

            message_box.exec_()

    def load_notemodels(self):
        try:
            if self.tagEditor.completer.popup().isVisible():
                return
        except AttributeError:
            pass

        if os.path.exists(self.notes_dir):
            notepaths = set(glob.glob(self.notes_dir + '/*' + NOTE_EXTENSION))
            notenames = map(os.path.basename, notepaths)
            note_keys = set(self.db_notes.keys())
            keys_missing_notes = note_keys - set(notenames)

            #remove keys missing notes
            for filename in keys_missing_notes:
                del (self.db_notes[filename])

            # add notes missing keys
            for filepath in notepaths:
                filename = os.path.basename(filepath)
                if filename not in self.db_notes.keys():
                    note = NoteModel(filepath)
                    self.db_notes[note.filename] = note

            # build the completer list
            self.insert_ui_tagcompleter()

            if len(self.db_notes.keys()) > 0:
                # reverse sort the note list based on last modified time
                return sorted(self.db_notes.values(), key=lambda x: x.timestamp, reverse=True)
            else:
                return []
        else:
            return []

    def load_ui_notes_list(self, items):
        pinned_items = [i for i in items if i.pinned]
        unpinned_items = [i for i in items if not i.pinned]

        self.ui.notesList.clear()

        for item in sorted(pinned_items, key=lambda x: x.notename):
            n = QtGui.QListWidgetItem(QtGui.QIcon(":/icons/resources/pushpin_16.png"), item.notename)
            self.ui.notesList.addItem(n)

        for item in unpinned_items:
            u = QtGui.QListWidgetItem(item.notename)
            self.ui.notesList.addItem(u)

        self.ui.notesList.setCurrentRow(self.current_row, QtGui.QItemSelectionModel.Select)

    def update_ui_views(self):
        # update the note editor
        self.noteEditor.blockSignals(True)
        self.noteEditor.notemodel = self.current_note
        self.load_history_data()
        self.noteEditor.blockSignals(False)

        # highlight any search terms
        if self.query is not '':
            self.noteEditor.highlight_search(self.query.split(' '))

        # update the tag editor
        self.tagEditor.blockSignals(True)
        try:
            self.tagEditor.setText(self.current_note.metadata['tags'])
        except (TypeError, KeyError, AttributeError):
            # no metadata or no tag metadata
            self.tagEditor.setText('')
        self.tagEditor.blockSignals(False)

        # update the preview and diff panes
        self.old_data = None
        self.update_ui_preview()
        self.update_ui_diff()
        self.update_ui_historyLabel()

        # update the window title
        try:
            title = self.current_note.title
        except AttributeError:
            # current_note is None
            title = ''
        self.setWindowTitle(' '.join([WINDOW_TITLE, '-', title]))

    def update_ui_views_history(self):
        if self.old_data is None:
            self.update_ui_views()
        else:
            old_content, old_meta = NoteModel.parse_note_content(self.old_data[0])
            # update the note editor
            self.noteEditor.blockSignals(True)
            self.noteEditor.set_note_text(old_content)
            self.noteEditor.blockSignals(False)

            # update the tag editor
            self.tagEditor.blockSignals(True)
            try:
                self.tagEditor.setText(old_meta['tags'])
            except (TypeError, KeyError):
                # no metadata or no tag metadata
                self.tagEditor.setText('')
            self.tagEditor.blockSignals(False)

            # update the preview and diff panes
            self.update_ui_preview()
            self.update_ui_diff()

            # update the window title
            dt_str = self.old_data[1]
            dt = self._history_timestring_to_datetime(dt_str)
            tab_date = '[' + human_date(dt) + ']'
            self.setWindowTitle(' '.join([WINDOW_TITLE, '-', self.current_note.title, tab_date]))

    def click_update_ui_views(self, index=None):
        if self.record_on_switch and not self.current_note.recorded:
            self.noteEditor.record_note()

        self.update_ui_views()

    def dblclick_pin_list_item(self, index):
        if index is None:
            return
        else:
            i = index.row()

        filename = self.ui.notesList.item(i).text() + NOTE_EXTENSION
        note = self.db_notes[filename]
        if note.pinned:
            note.pinned = False
        else:
            note.pinned = True

        self.search_files()

    def process_keyseq(self, seq):
        if seq == 'ctrl_n' or seq == 'ctrl_f':
            self.ui.omniBar.setFocus()
        elif seq == 'ctrl_e':
            self.ui.toolBox.setCurrentIndex(0)
            self.noteEditor.setFocus()
        elif seq == 'ctrl_w':
            self.update_ui_preview()
            self.ui.toolBox.setCurrentIndex(1)
        elif seq == 'ctrl_d':
            self.update_ui_diff()
            self.ui.toolBox.setCurrentIndex(2)
        elif seq == 'ctrl_l':
            self.ui.notesList.setFocus()
        elif seq == 'ctrl_m':
            self.click_merge_notes()
        elif seq == 'ctrl_t':
            self.ui.toolBox.setCurrentIndex(0)
            self.tagEditor.setFocus()
        elif seq == 'ctrl_s':
            self.noteEditor.save_note()
        elif seq == 'ctrl_r':
            self.noteEditor.record_note()
            self.load_history_data()
        elif seq == 'ctrl_up':
            self.keyseq_update_ui_views('down')
        elif seq == 'ctrl_down':
            self.keyseq_update_ui_views('up')
        elif seq == 'ctrl_<':
            self.click_older_date()
        elif seq == 'ctrl_>':
            self.click_newer_date()
        elif seq == 'ctrl_shift_l':
            self.toggle_notes_list_view()
        elif seq == 'ctrl_shift_h':
            self.toggle_history_bar_view()
        elif seq == 'ctrl_shift_o':
            self.toggle_omnibar_view()
        elif seq == 'ctrl_shift_f':
            self.toggle_notes_list_view()
            self.toggle_omnibar_view()
            self.toggle_history_bar_view()
        elif seq == 'ctrl_shift_u':
            now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            if self.noteEditor.hasFocus():
                self.noteEditor.insertPlainText('{0}\n'.format(now))
            else:
                self.ui.omniBar.setText(now)
        elif seq == 'ctrl_shift_p':
            self.dblclick_pin_list_item(self.ui.notesList.currentIndex())
        elif seq == 'esc':
            self.ui.omniBar.setText('')
        else:
            logger.info('No code for {0}'.format(seq))

    def keyseq_update_ui_views(self, direction):
        """
        Moves through the notes list, looping at each end

        :param direction: which direction to move 'up' or 'down'
        """
        current_row = self.ui.notesList.currentRow()
        row_count = self.ui.notesList.count()
        if direction == 'down' and current_row > 0:
            self.ui.notesList.setCurrentRow(current_row - 1)
        elif direction == 'down' and current_row == 0:
            self.ui.notesList.setCurrentRow(row_count - 1)
        elif direction == 'up' and current_row < row_count - 1:
            self.ui.notesList.setCurrentRow(current_row + 1)
        elif direction == 'up' and current_row == row_count - 1:
            self.ui.notesList.setCurrentRow(0)

        self.ui.notesList.setCurrentRow(self.current_row, QtGui.QItemSelectionModel.Select)
        self.update_ui_views()

    def update_ui_preview(self):
        content = self.noteEditor.toPlainText()
        html = self.generate_html(content)
        self.ui.notePreview.setSearchPaths([self.notes_dir])
        self.ui.notePreview.setHtml(html)
        self.ui.notePreview.reload()

    def update_ui_diff(self):
        if self.old_data is not None:
            new_content = self.current_note.content
            content, __ = NoteModel.parse_note_content(self.old_data[0])
            dt_str = self.old_data[1]
            dt = self._history_timestring_to_datetime(dt_str)
            tab_date = '[' + human_date(dt) + ']'
            fromdesc = ' '.join([self.current_note.title, tab_date])
            diff_html = diff_to_html(content, new_content, fromdesc, self.current_note.title)
        else:
            try:
                diff_html = self.current_note.get_status()
            except AttributeError:
                # current_note is None
                diff_html = ''
        self.ui.noteDiff.setHtml(diff_html)
        self.ui.noteDiff.reload()

    def update_ui_historyLabel(self):
        color = 'rgb({0}, {1}, {2}, {3})'.format(*MOTOME_BLUE.getRgb())
        l = len(self.current_note.history)
        self.ui.historyLabel.setText('<a href="#" style="color: {color}">{title} has {num} {version}</a>'.format(
            color=color,
            title=self.current_note.title,
            num=l,
            version='versions' if l != 1 else 'version'))

    def remove_history_bar(self):
        self.ui.frameHistory.hide()

    def insert_history_bar(self):
        self.ui.frameHistory.show()

    def toggle_notes_list_view(self):
        current_size = self.ui.splitter.sizes()
        if current_size[0] == 0 and self.notes_list_splitter_size is not None:
            self.ui.splitter.setSizes(self.notes_list_splitter_size)
            self.notes_list_splitter_size = None
        elif current_size[0] == 0 and self.notes_list_splitter_size is None:
            self.notes_list_splitter_size = current_size
            self.ui.splitter.setSizes([256, current_size[1]])
        elif self.notes_list_splitter_size is not None:
            self.notes_list_splitter_size = None
            self.ui.splitter.setSizes([0, current_size[1]])
        elif self.notes_list_splitter_size is None:
            self.notes_list_splitter_size = self.ui.splitter.sizes()
            self.ui.splitter.setSizes([0, current_size[1]])
        else:
            logger.warning('Toggle notes list view wierdness {0}'.format(self.notes_list_splitter_size))

    def toggle_omnibar_view(self):
        if self.ui.frameOmniSettings.isHidden():
            self.ui.frameOmniSettings.show()
        else:
            self.ui.frameOmniSettings.hide()

    def toggle_history_bar_view(self):
        if self.ui.frameHistory.isHidden():
            self.insert_history_bar()
        else:
            self.remove_history_bar()

    def start_meta_save(self):
        if self.save_timer.isActive():
            self.save_timer.stop()
        self.save_timer.start(self.save_interval)

    def save_note_meta(self):
        if self.noteEditor.save_timer.isActive():
            self.noteEditor.save_note()

        if self.save_timer.isActive():
            self.save_timer.stop()

        metadata = self.current_note.metadata
        if self.first_line_title:
            nt = self.noteEditor.notemodel.content.split('\n', 1)[0]
            t = self._clean_filename(nt, '').strip()
            if t != '':
                metadata['title'] = t

        metadata['tags'] = self.tagEditor.text()

        if 'conf_author' in self.conf.keys():
            metadata['author'] = self.conf['conf_author']

        # update the metadata (will save automatically)
        self.current_note.metadata = metadata

        # check for history position and move to latest if needed
        if self.old_data is not None:
            self.ui.historySlider.setValue(self.ui.historySlider.maximum())

    def generate_html(self, content):
        try:
            header = build_preview_header_html(self.current_note.metadata['title'])
        except (AttributeError, KeyError, TypeError):
            # no title in metadata or no metadata
            header = build_preview_header_html('')
        body = self.md.convert(content)  # TODO: getting re MemoryErrors for large files
        footer = build_preview_footer_html()
        html = header + body + footer
        return html

    def export_html(self):
        html = self.generate_html(self.noteEditor.toPlainText())
        urls = self.noteEditor.get_note_links()
        media_urls = [url for url in urls if MEDIA_FOLDER in url[1]]
        export_dir = os.path.join(self.notes_dir, HTML_FOLDER, self.current_note.safename)
        stylesheets_dir = os.path.join(export_dir, 'stylesheets')
        media_dir = os.path.join(export_dir, MEDIA_FOLDER)
        dirs_to_make = [export_dir, stylesheets_dir, media_dir]
        # make the needed directories
        for d in dirs_to_make:
            try:
                os.makedirs(d)
            except OSError:
                pass
        # copy the needed files
        shutil.copy(os.path.join(self.style_dir, 'preview.css'), os.path.join(stylesheets_dir, 'preview.css'))
        for mediapath in media_urls:
            filename = os.path.basename(mediapath[1])
            shutil.copy(os.path.join(self.notes_dir, MEDIA_FOLDER, filename), os.path.join(media_dir, filename))
        htmlpath = os.path.join(export_dir, self.current_note.safename + HTML_EXTENSION)
        self._write_file(htmlpath, html)

        message_box = QtGui.QMessageBox()
        message_box.setTextFormat(QtCore.Qt.RichText)
        message_box.setWindowTitle("HTML Export Complete")
        message_box.setText("<center><b>HTML Export Complete</b></center>")
        message_box.setInformativeText('<center>Click to open the export directory<br>'
                                       '<a href="file:///{0}">{0}</a></center>'.format(export_dir))
        ok_btn = message_box.addButton(QtGui.QMessageBox.Ok)
        message_box.setDefaultButton(ok_btn)

        message_box.exec_()

    def start_search(self, query):
        self.query = query

        if len(query) > 2 and query[:-1] == ' ':
            self.search_files()

        if self.search_timer.isActive():
            self.search_timer.stop()
        self.search_timer.start(self.search_interval)

    def search_files(self):
        if self.search_timer.isActive():
            self.search_timer.stop()
        if self.query is None or self.query == '' or len(self.query) < 3:
            founds = self.all_notes
        else:
            self.search.query = self.query.lower()
            founds = [note for note in self.db_notes.values() if self.search.search_notemodel(note)]
        self.load_ui_notes_list(founds)

    def new_note(self):
        tagged_title = self.ui.omniBar.text()
        if tagged_title == '':
            return
        if tagged_title in self.all_notes:
            return

        # build new note name
        self.search.query = tagged_title

        if len(self.search.use_words) == 0:
            # no words to use in the title
            return

        title = ' '.join(self.search.use_words)
        tags = ' '.join(self.search.use_tags)

        # build the new note
        filename = self._clean_filename(title) + NOTE_EXTENSION
        filepath = os.path.join(self.notes_dir, filename)
        content = title + '\n'
        new_note = NoteModel(filepath)
        new_note.metadata['title'] = title
        new_note.metadata['tags'] = tags
        new_note.content = content

        # update
        self.db_notes[new_note.filename] = new_note

        self.ui.omniBar.blockSignals(True)
        self.ui.omniBar.setText('')
        self.query = ''
        self.ui.omniBar.blockSignals(False)

        self.ui.notesList.blockSignals(True)
        self.load_ui_notes_list(self.all_notes)
        self.current_row = new_note.notename
        self.update_ui_views()
        self.ui.notesList.blockSignals(False)

        # set the focus on the editor and move the cursor to the end
        self.noteEditor.setFocus()
        cursor = self.noteEditor.textCursor()
        cursor.movePosition(QtGui.QTextCursor.MoveOperation.End, QtGui.QTextCursor.MoveMode.MoveAnchor)
        self.noteEditor.setTextCursor(cursor)

    def load_history_data(self):
        """
        Updates the history slider with history info from the current note
        """
        self.ui.historySlider.blockSignals(True)
        try:
            hlen = len(self.current_note.history)
        except AttributeError:
            hlen = 0
        self.ui.historySlider.setMaximum(hlen)
        self.ui.historySlider.setValue(hlen)
        self.ui.historySlider.blockSignals(False)

    def load_old_note(self, sliderpos):
        if sliderpos == self.ui.historySlider.maximum():
            self.update_ui_views()
            self.old_data = None
        else:
            self.setCursor(QtGui.QCursor(QtCore.Qt.WaitCursor))
            self.old_data = self.current_note.load_old_note(sliderpos)
            self.update_ui_views_history()
            self.unsetCursor()

    def load_settings(self):
        dialog = SettingsDialog(self.conf)
        dialog.ui.about_version_label.setText('v' + VERSION)
        ret = dialog.exec_()
        if ret:
            # set the current tab to the settings tab
            dialog.ui.tabWidget.setCurrentIndex(0)
            # a tuple of widget types to find in the settings tab
            to_find = (QtGui.QLineEdit, QtGui.QFontComboBox, QtGui.QComboBox, QtGui.QCheckBox)
            # find all the widgets in the settings tab and set the conf dictionary
            for f in to_find:
                for c in dialog.ui.tabWidget.currentWidget().findChildren(f):
                    name = c.objectName()
                    if name == 'conf_notesLocation':
                        self.conf[name] = c.text()
                    elif name == 'conf_author':
                        self.conf[name] = c.text()
                    elif name == 'conf_checkbox_preview':
                        if c.checkState() == QtCore.Qt.CheckState.Unchecked:
                            self.conf[name] = 0
                        else:
                            self.conf[name] = 1
                    # elif name == 'conf_checkbox_history':
                    #     if c.checkState() == QtCore.Qt.CheckState.Unchecked:
                    #         self.conf[name] = 0
                    #     else:
                    #         self.conf[name] = 1
                    # elif name == 'conf_checkbox_deleteempty':
                    #     if c.checkState() == QtCore.Qt.CheckState.Unchecked:
                    #         self.conf[name] = 0
                    #     else:
                    #         self.conf[name] = 1
                    elif name == 'conf_checkbox_recordonexit':
                        if c.checkState() == QtCore.Qt.CheckState.Unchecked:
                            self.conf[name] = 0
                        else:
                            self.conf[name] = 1
                    elif name == 'conf_checkbox_recordonswitch':
                        if c.checkState() == QtCore.Qt.CheckState.Unchecked:
                            self.conf[name] = 0
                        else:
                            self.conf[name] = 1
                    elif name == 'conf_checkbox_titleasfilename':
                        if c.checkState() == QtCore.Qt.CheckState.Unchecked:
                            self.conf[name] = 0
                        else:
                            self.conf[name] = 1
                    elif name == 'conf_checkbox_firstlinetitle':
                        if c.checkState() == QtCore.Qt.CheckState.Unchecked:
                            self.conf[name] = 0
                        else:
                            self.conf[name] = 1
                    else:
                        pass
            self.save_conf()
            self.set_ui_views()
            # load the notes directory and get all the files
            self.notes_dir = self.conf['conf_notesLocation']
            self.notes_data_dir = os.path.join(self.notes_dir, NOTE_DATA_DIR)
            # set the db connection
            self.load_db_data()
            self._notes_dir_last_seen = 0.0
            # update the file list and views
            self.load_ui_notes_list(self.all_notes)
            self.update_ui_views()

        elif self.first_run:
            shutil.rmtree(self.app_data_dir)
            sys.exit()

    def load_styles(self):
        if 'style' in self.conf.keys():
            self.style_dir = os.path.join(self.app_data_dir, 'styles', self.conf['style'])
        else:
            self.style_dir = os.path.join(APP_DIR, 'styles', 'default')

        editor_path = os.path.join(self.style_dir, 'editor.css')
        preview_path = os.path.join(self.style_dir, 'preview.css')
        diff_path = os.path.join(self.style_dir, 'diff.css')

        if os.path.exists(editor_path):
            editor_style = self._read_file(editor_path)
            self.noteEditor.setStyleSheet(editor_style)
            self.noteEditor.document().setDefaultStyleSheet(editor_style)

        if os.path.exists(preview_path):
            preview_style = self._read_file(preview_path)
            self.ui.notePreview.document().setDefaultStyleSheet(preview_style)

        if os.path.exists(diff_path):
            diff_style = self._read_file(diff_path)
            self.ui.noteDiff.document().setDefaultStyleSheet(diff_style)

    def click_older_date(self):
        sliderpos = self.ui.historySlider.sliderPosition()
        if sliderpos != self.ui.historySlider.minimum():
            self.ui.historySlider.setValue(sliderpos - 1)
            self.load_old_note(sliderpos - 1)

    def click_newer_date(self):
        sliderpos = self.ui.historySlider.sliderPosition()
        if sliderpos != self.ui.historySlider.maximum():
            self.ui.historySlider.setValue(sliderpos + 1)
            self.load_old_note(sliderpos + 1)

    def update_slider_tooltip(self, index):
        try:
            timestring = self.current_note.history[index].filename[:-(len(ZIP_EXTENSION) + 1)]
            dt = self._history_timestring_to_datetime(timestring)
            tooltip = human_date(dt)
            self.ui.historySlider.setToolTip(tooltip)
        except IndexError:
            # at the 'now' position
            pass

    def delete_current_note(self):
        message_box = QtGui.QMessageBox()
        message_box.setText('Delete {0}?'.format(self.current_note.notename))
        message_box.setInformativeText('Are you sure you want to delete this note?')
        delete_btn = message_box.addButton('Delete', QtGui.QMessageBox.YesRole)
        cancel_btn = message_box.addButton(QtGui.QMessageBox.Cancel)
        message_box.setEscapeButton(QtGui.QMessageBox.Cancel)
        message_box.setDefaultButton(cancel_btn)

        message_box.exec_()

        if message_box.clickedButton() == delete_btn:
            self.delete_note(self.current_note)
            omni_text = self.ui.omniBar.text()
            if omni_text == '':
                self.load_ui_notes_list(self.all_notes)
            else:
                self.query = omni_text
                self.search_files()
            self.update_ui_views()

    def delete_note(self, note):
        if note.remove():
            del self.db_notes[note.filename]
        else:
            message_box = QtGui.QMessageBox()
            message_box.setText('Delete Error!'.format(self.current_note.notename))
            message_box.setInformativeText('There was a problem deleting all the note files. Please check the {0} '
                                           'directory for any remaining data.'.format(self.notes_dir))

    def do_first_run(self):
        """ Do stuff the first time the app runs """
        # Show them the settings dialog
        self.load_settings()
        transition_versions(self.notes_dir)
        self.load_db_data()
        self.first_run = False

    def load_db_data(self):
        try:
            with open(os.path.join(self.notes_data_dir, 'Motome_data.fs'), 'rb') as data_file:
                # Practice safer unpickling by making sure the UnPickler only loads NoteModel objects
                unp = pickle.Unpickler(data_file)
                unp.find_global = pickle_find_NoteModel
                self.db_notes = unp.load()
        except IOError:
            self.load_notemodels()
        except pickle.UnpicklingError as e:
            logger.warning('[load_db_data] %r' % e)

    def save_db_data(self):
        try:
            with open(os.path.join(self.notes_data_dir, 'Motome_data.fs'), 'wb') as data_file:
                pickle.dump(self.db_notes, data_file, -1)
        except IOError:
            os.makedirs(self.notes_data_dir)
            with open(os.path.join(self.notes_data_dir, 'Motome_data.fs'), 'wb') as data_file:
                pickle.dump(self.db_notes, data_file, -1)

    def show_custom_preview_menu(self, point):
        preview_rclk_menu = self.ui.notePreview.createStandardContextMenu()
        preview_rclk_menu.addSeparator()

        export_html_act = preview_rclk_menu.addAction(QtGui.QIcon(":/icons/resources/html.png"), 'Export HTML')
        export_html_act.triggered.connect(self.export_html)

        preview_rclk_menu.addSeparator()

        act_edit = preview_rclk_menu.addAction('Show Editor')
        act_edit.setShortcut(self.keyboard_shortcuts['ShowEdit']['seq'])
        act_edit.triggered.connect(self.keyboard_shortcuts['ShowEdit']['func'])

        act_diff = preview_rclk_menu.addAction('Show Diff')
        act_diff.setShortcut(self.keyboard_shortcuts['ShowDiff']['seq'])
        act_diff.triggered.connect(self.keyboard_shortcuts['ShowDiff']['func'])

        preview_rclk_menu.exec_(self.ui.notePreview.mapToGlobal(point))
        del preview_rclk_menu

    def show_custom_editor_menu(self, point):
        editor_rclk_menu = self.noteEditor.createStandardContextMenu()
        editor_rclk_menu.addSeparator()

        act_inslink = editor_rclk_menu.addAction('Insert Hyperlink')
        act_inslink.setShortcut(self.noteEditor.keyboard_shortcuts['InsLink']['seq'])
        act_inslink.triggered.connect(self.noteEditor.keyboard_shortcuts['InsLink']['func'])

        act_insfile = editor_rclk_menu.addAction('Insert File')
        act_insfile.setShortcut(self.noteEditor.keyboard_shortcuts['InsFile']['seq'])
        act_insfile.triggered.connect(self.noteEditor.keyboard_shortcuts['InsFile']['func'])

        editor_rclk_menu.addSeparator()

        act_preview = editor_rclk_menu.addAction('Show Preview')
        act_preview.setShortcut(self.keyboard_shortcuts['ShowPre']['seq'])
        act_preview.triggered.connect(self.keyboard_shortcuts['ShowPre']['func'])

        act_diff = editor_rclk_menu.addAction('Show Diff')
        act_diff.setShortcut(self.keyboard_shortcuts['ShowDiff']['seq'])
        act_diff.triggered.connect(self.keyboard_shortcuts['ShowDiff']['func'])

        editor_rclk_menu.exec_(self.noteEditor.mapToGlobal(point))
        del editor_rclk_menu

    def show_custom_diff_menu(self, point):
        diff_rclk_menu = self.noteEditor.createStandardContextMenu()
        diff_rclk_menu.addSeparator()
        
        act_edit = diff_rclk_menu.addAction('Show Editor')
        act_edit.setShortcut(self.keyboard_shortcuts['ShowEdit']['seq'])
        act_edit.triggered.connect(self.keyboard_shortcuts['ShowEdit']['func'])

        act_preview = diff_rclk_menu.addAction('Show Preview')
        act_preview.setShortcut(self.keyboard_shortcuts['ShowPre']['seq'])
        act_preview.triggered.connect(self.keyboard_shortcuts['ShowPre']['func'])

        diff_rclk_menu.exec_(self.noteEditor.mapToGlobal(point))
        del diff_rclk_menu

    def _clean_filename(self, unclean, replace='_'):
        clean = unclean
        for c in UNSAFE_CHARS:
            clean = clean.replace(c, replace)
        return clean

    def _history_timestring_to_datetime(self, timestring):
        return datetime(int(timestring[0:4]),
                        int(timestring[4:6]),
                        int(timestring[6:8]),
                        int(timestring[8:10]),
                        int(timestring[10:12]),
                        int(timestring[12:]))

    def _write_file(self, filepath, filedata):
        NoteModel.enc_write(filepath, filedata)

    def _read_file(self, filepath):
        return NoteModel.enc_read(filepath)