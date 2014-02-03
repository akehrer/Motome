# Import the future
from __future__ import print_function
from __future__ import unicode_literals
from __future__ import absolute_import

# Import standard library modules
import glob
import logging
import os
import shutil
import sys
import time
import cPickle as pickle
from datetime import datetime

# Import extra modules
import markdown

# Import Qt modules
from PySide import QtCore, QtGui

# Import application window view
from Motome.Views.MainWindow import Ui_MainWindow

# Import configuration values
from Motome.config import NOTE_EXTENSION, ZIP_EXTENSION, MEDIA_FOLDER, \
    APP_DIR, WINDOW_TITLE, UNSAFE_CHARS, VERSION, NOTE_DATA_DIR, HTML_FOLDER, HTML_EXTENSION

# Import additional modules
from Motome.Modules.MotomeTextBrowser import MotomeTextBrowser
from Motome.Modules.NoteModel import NoteModel
from Motome.Modules.SettingsDialog import SettingsDialog
from Motome.Modules.AutoCompleterModel import AutoCompleteEdit
from Motome.Modules.Search import SearchModel
from Motome.Modules.Utils import build_preview_footer_html, build_preview_header_html, \
    diff_to_html, human_date, grab_urls

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
        self.notes_dir = ''

        # note file vars
        self.note_extension = NOTE_EXTENSION

        # create the app storage directory
        try:
            os.makedirs(self.app_data_dir)
            self.first_run = True
        except OSError:
            self.first_run = False

        self.conf = {}

        # Load configuration
        self.load_conf()
        self.notes_data_dir = os.path.join(self.notes_dir, NOTE_DATA_DIR)

        # Set some configuration variables
        if 'conf_checkbox_deleteempty' in self.conf.keys() and int(self.conf['conf_checkbox_deleteempty']) > 0:
            self.delete_empty = True
        else:
            self.delete_empty = False

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

        # insert the custom text editor
        self.noteEditor = MotomeTextBrowser(self.ui.tabEditor, self.notes_dir)
        self.noteEditor.setTextInteractionFlags(QtCore.Qt.LinksAccessibleByKeyboard|QtCore.Qt.LinksAccessibleByMouse|
                                                QtCore.Qt.TextBrowserInteraction|QtCore.Qt.TextEditable|
                                                QtCore.Qt.TextEditorInteraction|QtCore.Qt.TextSelectableByKeyboard|
                                                QtCore.Qt.TextSelectableByMouse)
        self.noteEditor.setObjectName("noteEditor")
        self.ui.horizontalLayout_3.insertWidget(1, self.noteEditor)
        self.noteEditor.textChanged.connect(self.start_save)
        self.noteEditor.anchorClicked.connect(self.load_anchor)
        
        # tag completer
        self.tagEditor = AutoCompleteEdit([])
        self.tagEditor.setObjectName("tagEditor")
        self.tagEditor.setFrame(False)
        self.ui.horizontalLayout_2.addWidget(self.tagEditor)
        self.tagEditor.textEdited.connect(self.start_save)

        # catch link clicks in the Preview pane
        self.ui.notePreview.anchorClicked.connect(self.load_anchor)
        self.ui.notePreview.setContextMenuPolicy(QtCore.Qt.CustomContextMenu)
        self.ui.notePreview.customContextMenuRequested.connect(self.show_custom_preview_menu)

        # Set the window location and size
        if 'window_x'in self.conf.keys():
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
        # self.current_row = 0
        self.old_data = None
        self.history = []

        # set the views
        self.set_ui_views()
        self.ui.notePreview.setSearchPaths(self.notes_dir)

        # notes list splitter size for hiding and showing the notes list
        self.notes_list_splitter_size = None

        # save file timer
        self.save_interval = 1000 # msec
        self.save_timer = QtCore.QTimer()
        self.save_timer.timeout.connect(self.save_note)

        # search
        self.search = SearchModel()
        self.query = ''
        self.search_interval = 250 # msec
        self.search_timer = QtCore.QTimer()
        self.search_timer.timeout.connect(self.search_files)

        # DB
        self.db_notes = {}

        if not self.first_run:
            self.load_db_data()

        # notes
        self._notes_dir_last_seen = 0.0
        self._all_notes = self.load_notemodels()
        self.load_ui_notes_list(self.all_notes)
        try:
            self.update_ui_views()
        except AttributeError as e:
            # note directory missing?
            if not os.path.isdir(self.notes_dir):
                self.first_run = True
            else:
                logger.error('Error running __init__/update_ui_views, %s'%e)
                self.first_run = True

        # set-up the keyboard shortcuts
        esc = QtCore.Qt.Key_Escape
        delete = QtCore.Qt.Key_Delete
        QtGui.QShortcut(QtGui.QKeySequence('Ctrl+N'), self, lambda item=None: self.process_keyseq('ctrl_n'))
        QtGui.QShortcut(QtGui.QKeySequence('Ctrl+F'), self, lambda item=None: self.process_keyseq('ctrl_f'))
        QtGui.QShortcut(QtGui.QKeySequence('Ctrl+E'), self, lambda item=None: self.process_keyseq('ctrl_e'))
        QtGui.QShortcut(QtGui.QKeySequence('Ctrl+P'), self, lambda item=None: self.process_keyseq('ctrl_p'))
        QtGui.QShortcut(QtGui.QKeySequence('Ctrl+D'), self, lambda item=None: self.process_keyseq('ctrl_d'))
        QtGui.QShortcut(QtGui.QKeySequence('Ctrl+L'), self, lambda item=None: self.process_keyseq('ctrl_l'))
        QtGui.QShortcut(QtGui.QKeySequence('Ctrl+T'), self, lambda item=None: self.process_keyseq('ctrl_t'))
        QtGui.QShortcut(QtGui.QKeySequence('Ctrl+S'), self, lambda item=None: self.process_keyseq('ctrl_s'))
        QtGui.QShortcut(QtGui.QKeySequence('Ctrl+R'), self, lambda item=None: self.process_keyseq('ctrl_r'))
        QtGui.QShortcut(QtGui.QKeySequence('Ctrl+]'), self, lambda item=None: self.process_keyseq('ctrl_up'))
        QtGui.QShortcut(QtGui.QKeySequence('Ctrl+['), self, lambda item=None: self.process_keyseq('ctrl_down'))
        QtGui.QShortcut(QtGui.QKeySequence('Ctrl+<'), self, lambda item=None: self.process_keyseq('ctrl_<'))
        QtGui.QShortcut(QtGui.QKeySequence('Ctrl+>'), self, lambda item=None: self.process_keyseq('ctrl_>'))
        QtGui.QShortcut(QtGui.QKeySequence('Ctrl+Shift+L'), self, lambda item=None: self.process_keyseq('ctrl_shift_l'))
        QtGui.QShortcut(QtGui.QKeySequence('Ctrl+Shift+H'), self, lambda item=None: self.process_keyseq('ctrl_shift_h'))
        QtGui.QShortcut(QtGui.QKeySequence('Ctrl+Shift+O'), self, lambda item=None: self.process_keyseq('ctrl_shift_o'))
        QtGui.QShortcut(QtGui.QKeySequence('Ctrl+Shift+F'), self, lambda item=None: self.process_keyseq('ctrl_shift_f'))
        QtGui.QShortcut(QtGui.QKeySequence('Ctrl+Shift+U'), self, lambda item=None: self.process_keyseq('ctrl_shift_u'))
        QtGui.QShortcut(QtGui.QKeySequence('Ctrl+Shift+P'), self, lambda item=None: self.process_keyseq('ctrl_shift_p'))
        QtGui.QShortcut(QtGui.QKeySequence(esc), self, lambda item=None: self.process_keyseq('esc'))

        # remove notes in the note list using the delete key
        QtGui.QShortcut(QtGui.QKeySequence(delete), self.ui.notesList, lambda item=None: self.delete_current_note())

        if self.first_run:
            logger.info('First run')
            self.do_first_run()

    @property
    def all_notes(self):
        try:
            if os.path.getmtime(self.notes_dir) > self._notes_dir_last_seen:
                self._all_notes = self.load_notemodels()
                self._notes_dir_last_seen = os.path.getmtime(self.notes_dir)
        except OSError:
            pass
        return self._all_notes

    @property
    def current_note(self):
        try:
            i = self.current_row  # self.ui.notesList.currentRow()
            filename = self.ui.notesList.item(i).text() + NOTE_EXTENSION
            self._current_note = self.db_notes[filename]
            # self.set_current_row(self._current_note.notename)
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

    def process_keyseq(self,seq):
        if seq == 'ctrl_n' or seq == 'ctrl_f':
            self.ui.omniBar.setFocus()
        elif seq == 'ctrl_e':
            self.ui.toolBox.setCurrentIndex(0)
            self.noteEditor.setFocus()
        elif seq == 'ctrl_p':
            self.ui.toolBox.setCurrentIndex(1)
        elif seq == 'ctrl_d':
            self.ui.toolBox.setCurrentIndex(2)
        elif seq == 'ctrl_l':
            self.ui.notesList.setFocus()
        elif seq == 'ctrl_m':
            self.click_merge_notes()
        elif seq == 'ctrl_t':
            self.ui.toolBox.setCurrentIndex(0)
            self.tagEditor.setFocus()
        elif seq == 'ctrl_s':
            if 'conf_checkbox_deleteempty' in self.conf.keys() and int(self.conf['conf_checkbox_deleteempty']) > 0:
                self.save_note(record=True)
            else:
                self.save_note(record=False)
        elif seq == 'ctrl_r':
            self.save_note(record=True)
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

    def stop(self):
        if self.save_timer.isActive():
            self.save_note()

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

    def load_conf(self):
        filepath = os.path.join(self.app_data_dir, 'conf')
        try:
            data = self._read_file(filepath)
            for line in data.splitlines():
                try:
                    key, value = line.strip().split(':', 1)
                    self.conf[key] = value
                except ValueError:
                    pass
            if not 'conf_notesLocation' in self.conf.keys():
                # Show the settings dialog if no notes location has been configured
                self.load_settings()
            else:
                self.notes_dir = self.conf['conf_notesLocation']
        except IOError as e:
            # No configuration file exists, create one
            self.save_conf()

    def save_conf(self):
        filepath = os.path.join(self.app_data_dir, 'conf')
        filedata = ''
        self.conf['motome_version'] = VERSION
        self.conf['conf_update'] = time.time()
        for key, value in self.conf.items():
                filedata = filedata + '{0}:{1}\n'.format(key, value)
        self._write_file(filepath, filedata)

    def load_anchor(self, url):
        url_path = url.path()

        # intranote link?
        if url_path+NOTE_EXTENSION in self.db_notes.keys():
            # filename = url_path + NOTE_EXTENSION
            # self.current_note = self.db_notes[filename]
            # self.set_current_row(url_path)
            self.current_row = url_path
            # self.update_ui_views()
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
        if self.tagEditor.completer.popup().isVisible():
            return

        if os.path.exists(self.notes_dir):
            notepaths = set(glob.glob(self.notes_dir + '/*' + NOTE_EXTENSION))
            notenames = map(os.path.basename, notepaths)
            note_keys = set(self.db_notes.keys())
            keys_missing_notes = note_keys - set(notenames)

            #remove keys missing notes
            for filename in keys_missing_notes:
                del(self.db_notes[filename])

            # add notes missing keys
            for filepath in notepaths:
                filename = os.path.basename(filepath)
                if filename not in self.db_notes.keys():
                    note = NoteModel(filepath)
                    self.db_notes[note.filename] = note

            # build the completer list
            completer_list = set()
            for note in self.db_notes.values():
                if 'tags' in note.metadata.keys():
                    for t in note.metadata['tags'].split():
                        completer_list.add(t)
            # attach a completer to the tag editor
            qlist = QtGui.QStringListModel(list(completer_list))
            # self.tag_completer.setModel(qlist)
            self.tagEditor.setCompleterModel(qlist)

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

        # if len(items) == 0:
        #     self.current_note = None

        self.ui.notesList.clear()

        for item in sorted(pinned_items, key=lambda x: x.notename):
            n = QtGui.QListWidgetItem(QtGui.QIcon(":/icons/resources/bullet_black.png"), item.notename)
            self.ui.notesList.addItem(n)

        for item in unpinned_items:
            u = QtGui.QListWidgetItem(item.notename)
            self.ui.notesList.addItem(u)

        if self.current_note is not None:
            self.current_row = self.current_note.notename  # self.set_current_row(self.current_note.notename)
        else:
            # self.current_row = 0
            self.update_ui_views()

        if self.current_row < 0:
            self.ui.notesList.setCurrentRow(self.current_row, QtGui.QItemSelectionModel.Select)
        else:
            self.ui.notesList.setCurrentRow(self.current_row, QtGui.QItemSelectionModel.Select)

    def update_ui_views(self, old_content=None, reload_editor=True):
        try:
            self.noteEditor.blockSignals(True)
            self.tagEditor.blockSignals(True)
        except AttributeError:
            pass

        if self.current_note is None:
            self.noteEditor.set_note_text('')
            self.tagEditor.setText('')
            self.setWindowTitle(' '.join([WINDOW_TITLE]))
            self.noteEditor.blockSignals(False)
            self.tagEditor.blockSignals(False)
            return

        if old_content is None:
            content = self.current_note.content
            new_content = content
            tab_date = ''
            self.load_history_data()
        else:
            new_content = self.current_note.content
            content, __ = NoteModel.parse_note_content(old_content[0])
            dt_str = old_content[1]
            dt = self._history_timestring_to_datetime(dt_str)
            tab_date = '[' + human_date(dt) + ']'

        if 'tags' in self.current_note.metadata.keys():
            self.tagEditor.setText(self.current_note.metadata['tags'])
        else:
            self.tagEditor.setText('')

        if 'title' in self.current_note.metadata.keys():
            title = self.current_note.metadata['title']
        else:
            title = self.current_note.unsafename

        # update the window title
        self.setWindowTitle(' '.join([WINDOW_TITLE, '-', title, tab_date]))

        if reload_editor:
            self.noteEditor.set_note_text(content)

        self.update_ui_preview()
        fromdesc = ' '.join([title, tab_date])
        self.update_ui_diff(content, new_content, fromdesc=fromdesc, todesc=title)

        if self.query is not '':
            self.noteEditor.highlight_search(self.query.split(' '))

        self.noteEditor.blockSignals(False)
        self.tagEditor.blockSignals(False)

    def click_update_ui_views(self, index=None):
        # if index is None:
        #     i = self.ui.notesList.currentRow()
        # else:
        #     i = index.row()
        #
        # # self.current_row = i

        if self.save_timer.isActive():
            self.save_timer.stop()
            self.save_note()

        # filename = self.ui.notesList.item(i).text() + NOTE_EXTENSION
        # try:
        #     self.current_note = self.db_notes[filename]  # self.notes_list[i]
        #     self.set_current_row(self.current_note.notename)
        # except KeyError:
        #     pass

        if self.record_on_switch and not self.current_note.recorded:
            self.current_note.record(self.notes_dir)

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

    def keyseq_update_ui_views(self, direction):
        """
        Moves through the notes list, looping at each end

        :param direction: which direction to move 'up' or 'down'
        """
        if self.save_timer.isActive():
            self.save_timer.stop()
            self.save_note()

        current_row = self.ui.notesList.currentRow()
        row_count = self.ui.notesList.count()
        if direction == 'down' and current_row > 0:
            self.ui.notesList.setCurrentRow(current_row-1)
        elif direction == 'down' and current_row == 0:
            self.ui.notesList.setCurrentRow(row_count-1)
        elif direction == 'up' and current_row < row_count-1:
            self.ui.notesList.setCurrentRow(current_row+1)
        elif direction == 'up' and current_row == row_count-1:
            self.ui.notesList.setCurrentRow(0)

    def update_ui_preview(self):
        content = self.noteEditor.toPlainText()
        html = self.generate_html(content)
        self.ui.notePreview.setSearchPaths([self.notes_dir])
        self.ui.notePreview.setHtml(html)
        self.ui.notePreview.reload()

    def update_ui_diff(self, content, new_content, fromdesc, todesc):
        if content != new_content:
            diff_html = diff_to_html(content, new_content, fromdesc, todesc)
        else:
            diff_html = self.current_note.get_status()
        self.ui.noteDiff.setHtml(diff_html)
        self.ui.noteDiff.reload()

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
            self.ui.frameHistory.show()
        else:
            self.ui.frameHistory.hide()

    def start_save(self):
        if self.save_timer.isActive():
            self.save_timer.stop()
        self.save_timer.start(self.save_interval)

    def save_note(self, record=False):
        if self.current_note is None:
            return
        
        if self.tagEditor.completer.popup().isVisible():
            return

        new_content = self.noteEditor.toPlainText()
        # if the new content is an empty note and delete empty notes is enabled
        # delete the note and it's history
        if len(new_content.strip()) == 0 and self.delete_empty_note(self.current_note):
            self.save_timer.stop()
            # self.search.remove(filepath)
            # self.all_notes = self.load_notemodels()
            # self.load_ui_notes_list(self.all_notes)
            self.search_files()
            self.update_ui_views()
            return
        else:
            self.save_timer.stop()
            if self.old_data:
                # if we've edited a history record then record the last saved note data
                # to the history before saving any new data
                self.current_note.record(self.notes_dir)
                self.old_data = None
            # update the content (will save automatically)
            self.current_note.content = new_content

            metadata = self.current_note.metadata
            if self.first_line_title:
                t = self._clean_filename(new_content.split('\n', 1)[0], '').strip()
                if t != '':
                    metadata['title'] = t

            metadata['tags'] = self.tagEditor.text()

            if 'conf_author' in self.conf.keys():
                metadata['author'] = self.conf['conf_author']

            # update the metadata (will save automatically)
            self.current_note.metadata = metadata

            if self.title_as_filename:
                self.current_note.rename()
                # update the notes list
                # self.all_notes = self.load_notemodels()
                self.ui.notesList.blockSignals(True)
                self.search_files()
                self.ui.notesList.blockSignals(False)

        if record:
            self.current_note.record(self.notes_dir)

        self.update_ui_views(None, False)

    def generate_html(self, content):
        try:
            header = build_preview_header_html(self.current_note.metadata['title'])
        except KeyError:
            # no title in metadata
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
        # self.search.add(filepath)
        # self.current_note = new_note
        self.db_notes[new_note.filename] = new_note
        # self.all_notes = self.load_notemodels()

        self.ui.omniBar.blockSignals(True)
        self.ui.omniBar.setText('')
        self.query = ''
        self.ui.omniBar.blockSignals(False)

        self.ui.notesList.blockSignals(True)
        self.load_ui_notes_list(self.all_notes)
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
            self.ui.historySlider.setMaximum(hlen)
            self.ui.historySlider.setValue(hlen)
        except:
            self.ui.historySlider.setMaximum(0)
            self.ui.historySlider.setValue(1)
        self.ui.historySlider.blockSignals(False)

    def load_old_note(self, sliderpos):
        if sliderpos == self.ui.historySlider.maximum():
            self.update_ui_views()
            self.old_data = None
        else:
            self.setCursor(QtGui.QCursor(QtCore.Qt.WaitCursor))
            old_content, old_date = self.current_note.load_old_note(sliderpos)
            self.old_data = old_content
            self.update_ui_views(old_content=(old_content, old_date))
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
            # find all the widgets in the settings tab and set the
            # conf dictionary
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
                    elif name == 'conf_checkbox_history':
                        if c.checkState() == QtCore.Qt.CheckState.Unchecked:
                            self.conf[name] = 0
                        else:
                            self.conf[name] = 1
                    elif name == 'conf_checkbox_deleteempty':
                        if c.checkState() == QtCore.Qt.CheckState.Unchecked:
                            self.conf[name] = 0
                        else:
                            self.conf[name] = 1
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
            # self.all_notes = self.load_notemodels()
            self._notes_dir_last_seen = 0.0
            # remove any empty file and history (if checked) and reload file list
            self.delete_empty_notes()
            # update the file list and views
            self.load_ui_notes_list(self.all_notes)

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

    def set_ui_views(self):
        try:
            if int(self.conf['conf_checkbox_history']) == 0:
                self.remove_history_bar()
            elif int(self.conf['conf_checkbox_history']) > 0:
                self.insert_history_bar()
        except KeyError:
            logger.debug('[set_ui_views] No conf file')
            pass

    def update_slider_tooltip(self, index):
        try:
            timestring = self.current_note.history[index].filename[:-(len(ZIP_EXTENSION)+1)]
            dt = self._history_timestring_to_datetime(timestring)
            tooltip = human_date(dt)
            self.ui.historySlider.setToolTip(tooltip)
        except IndexError:
            # at the 'now' position
            pass

    def delete_empty_notes(self):
        if self.delete_empty:
            for n in self.all_notes:
                data = self._read_file(n.filepath)
                c, m = NoteModel.parse_note_content(data)
                if len(c.strip()) == 0:
                    self.delete_note(n)
            # self.all_notes = self.load_notemodels()

    def delete_empty_note(self, filepath):
        if self.delete_empty:
            return self.delete_note(filepath)
        else:
            return False

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
            # self.all_notes = self.load_notemodels()
            # self.current_note = None
            omni_text = self.ui.omniBar.text()
            if omni_text == '':
                self.load_ui_notes_list(self.all_notes)
            else:
                self.query = omni_text
                self.search_files()

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
        self.load_db_data()

    def load_db_data(self):
        try:
            with open(os.path.join(self.notes_data_dir, 'Motome_data.fs'), 'rb') as data_file:
                self.db_notes = pickle.load(data_file)
        except IOError:
            self.load_notemodels()

    def save_db_data(self):
        try:
            with open(os.path.join(self.notes_data_dir, 'Motome_data.fs'), 'wb') as data_file:
                pickle.dump(self.db_notes, data_file, -1)
        except IOError:
            os.makedirs(self.notes_data_dir)
            with open(os.path.join(self.notes_data_dir, 'Motome_data.fs'), 'wb') as data_file:
                pickle.dump(self.db_notes, data_file, -1)

    # def set_current_row(self, notename):
    #     try:
    #         list_item = self.ui.notesList.findItems(notename, QtCore.Qt.MatchExactly)[0]
    #         self.current_row = self.ui.notesList.row(list_item)
    #     except IndexError:
    #         self.current_row = 0

    def show_custom_preview_menu(self, point):
        preview_rclk_menu = self.ui.notePreview.createStandardContextMenu()
        preview_rclk_menu.addSeparator()
        preview_rclk_menu.addAction(QtGui.QIcon(":/icons/resources/html.png"), 'Export HTML')
        preview_rclk_menu.triggered.connect(self.export_html)
        preview_rclk_menu.exec_(self.ui.notePreview.mapToGlobal(point))
        del preview_rclk_menu

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