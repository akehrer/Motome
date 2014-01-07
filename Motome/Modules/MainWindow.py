# Import the future
from __future__ import print_function
from __future__ import unicode_literals

# Import standard library modules
import logging
import os
import shutil
import sys
import zipfile
from datetime import datetime

# Import extra modules
import markdown

# Import Qt modules
from PySide import QtCore, QtGui

# Import application window view
from Views.MainWindow import Ui_MainWindow

# Import configuration values
from config import NOTE_EXTENSION, ZIP_EXTENSION, MEDIA_FOLDER, \
    HTML_EXTENSION, APP_DIR, HTML_FOLDER, WINDOW_TITLE, UNSAFE_CHARS

# Import additional modules
from MotomeTextBrowser import MotomeTextBrowser
# from MergeNotesDialog import MergeNotesDialog
from NoteModel import NoteModel
from SettingsDialog import SettingsDialog
from Search import SearchNotes, SearchError
from Utils import build_preview_footer_html, build_preview_header_html, \
    diff_to_html, parse_note_content, enc_read, enc_write, human_date

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

        # tab data
        self.preview_tab = None
        self.diff_tab = None

        # insert the custom text editor
        self.noteEditor = MotomeTextBrowser(self.ui.tabEditor, self.notes_dir)
        self.noteEditor.setTextInteractionFlags(QtCore.Qt.LinksAccessibleByKeyboard|QtCore.Qt.LinksAccessibleByMouse|
                                                QtCore.Qt.TextBrowserInteraction|QtCore.Qt.TextEditable|
                                                QtCore.Qt.TextEditorInteraction|QtCore.Qt.TextSelectableByKeyboard|
                                                QtCore.Qt.TextSelectableByMouse)
        self.noteEditor.setObjectName("noteEditor")
        self.ui.verticalLayout_2.insertWidget(0, self.noteEditor)
        self.noteEditor.textChanged.connect(self.start_save)
        self.noteEditor.anchorClicked.connect(self.load_anchor)

        # catch link clicks in the Preview pane
        self.ui.notePreview.anchorClicked.connect(self.load_anchor)

        # Set the window location and size
        if 'window_x'in self.conf.keys():
            rect = QtCore.QRect(int(self.conf['window_x']),
                                int(self.conf['window_y']),
                                int(self.conf['window_width']),
                                int(self.conf['window_height']))
            self.setGeometry(rect)


        # load main window style
        main_style_path = os.path.join(APP_DIR, 'styles', 'main_window.css')
        main_style = self._read_file(main_style_path)
        self.setStyleSheet(main_style)

        # load the text browser styles
        self.load_styles()

        # markdown translator
        self.md = markdown.Markdown()

        # current view
        self.current_note = None
        self.old_data = None
        #self.meta = {}
        self.history = []

        # set the views
        self.set_ui_views()
        self.ui.notePreview.setSearchPaths(self.notes_dir)

        # save file timer
        self.save_interval = 1000 # msec
        self.save_timer = QtCore.QTimer()
        self.save_timer.timeout.connect(self.save_note)

        # search
        self.search = None
        self.query = ''

        if not self.first_run:
            self.search = SearchNotes(self.notes_dir)
            self.search.build_index()

        # notes
        self.all_notes = self.load_notemodels()
        self.notes_list = []
        self.load_ui_notes_list(self.all_notes)
        self.update_ui_views()

        # notes list splitter size for hiding and showing the notes list
        self.notes_list_splitter_size = None

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
        # QtGui.QShortcut(QtGui.QKeySequence('Ctrl+M'), self, lambda item=None: self.process_keyseq('ctrl_m'))
        QtGui.QShortcut(QtGui.QKeySequence('Ctrl+S'), self, lambda item=None: self.process_keyseq('ctrl_s'))
        QtGui.QShortcut(QtGui.QKeySequence('Ctrl+R'), self, lambda item=None: self.process_keyseq('ctrl_r'))
        QtGui.QShortcut(QtGui.QKeySequence('Ctrl+Up'), self, lambda item=None: self.process_keyseq('ctrl_up'))
        QtGui.QShortcut(QtGui.QKeySequence('Ctrl+Down'), self, lambda item=None: self.process_keyseq('ctrl_down'))
        QtGui.QShortcut(QtGui.QKeySequence('Ctrl+<'), self, lambda item=None: self.process_keyseq('ctrl_<'))
        QtGui.QShortcut(QtGui.QKeySequence('Ctrl+>'), self, lambda item=None: self.process_keyseq('ctrl_>'))
        QtGui.QShortcut(QtGui.QKeySequence('Ctrl+Shift+L'), self, lambda item=None: self.process_keyseq('ctrl_shift_l'))
        QtGui.QShortcut(QtGui.QKeySequence('Ctrl+Shift+H'), self, lambda item=None: self.process_keyseq('ctrl_shift_h'))
        QtGui.QShortcut(QtGui.QKeySequence('Ctrl+Shift+O'), self, lambda item=None: self.process_keyseq('ctrl_shift_o'))
        QtGui.QShortcut(QtGui.QKeySequence('Ctrl+Shift+F'), self, lambda item=None: self.process_keyseq('ctrl_shift_f'))
        QtGui.QShortcut(QtGui.QKeySequence('Ctrl+Shift+U'), self, lambda item=None: self.process_keyseq('ctrl_shift_u'))
        QtGui.QShortcut(QtGui.QKeySequence(esc), self, lambda item=None: self.process_keyseq('esc'))

        # remove notes in the note list using the delete key
        QtGui.QShortcut(QtGui.QKeySequence(delete), self.ui.notesList, lambda item=None: self.delete_current_note())

        if self.first_run:
            logger.info('First run')
            self.do_first_run()

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
            self.ui.tagEdit.setFocus()
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
        elif seq == 'esc':
            self.ui.omniBar.setText('')
        else:
            logger.info('No code for {0}'.format(seq))
            # print('No code for {0}'.format(seq))

    def stop(self):
        if self.save_timer.isActive():
            self.save_note(record=True)
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
        for key, value in self.conf.items():
                filedata = filedata + '{0}:{1}\n'.format(key, value)
        self._write_file(filepath, filedata)

    def load_anchor(self, url):
        media_path = os.path.join(self.notes_dir, MEDIA_FOLDER, url.path().split('/')[-1])
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
        items = []
        if os.path.exists(self.notes_dir):
            for file in os.listdir(self.notes_dir):
                if file.endswith(self.note_extension):
                    note = NoteModel(os.path.join(self.notes_dir, file))
                    items.append(note)
            if len(items) > 0:
                # reverse sort the note list based on last modified time
                return sorted(items, key=lambda x: x.timestamp, reverse=True)
            else:
                return items
        else:
            return items

    def load_ui_notes_list(self, items):
        self.ui.notesList.clear()
        for item in items:
            u = item.notename
            self.ui.notesList.addItem(u)
        self.notes_list = items
        self.ui.notesList.setCurrentRow(0)

    def update_ui_views(self, old_content=None, reload_editor=True):
        try:
            self.noteEditor.blockSignals(True)
            self.ui.tagEdit.blockSignals(True)
            self.ui.titleEdit.blockSignals(True)
        except AttributeError:
            pass

        # try:
        #     filepath = self.current_note.filepath
        #     data = self._read_file(filepath)
        #     self.old_data = data
        # except Exception as e:
        #     logger.debug('[update_ui_views] %s'%e)
        #     self.noteEditor.blockSignals(False)
        #     self.ui.tagEdit.blockSignals(False)
        #     self.ui.titleEdit.blockSignals(False)
        #     return

        if old_content is None:
            #content, self.meta = parse_note_content(data)
            content = self.current_note.content
            new_content = content
            tab_date = ''
            self.load_history_data()
        else:
            new_content = self.current_note.content
            content, __ = parse_note_content(old_content[0])
            dt_str = old_content[1]
            dt = self._history_timestring_to_datetime(dt_str)
            tab_date = '[' + human_date(dt) + ']'

        if 'tags' in self.current_note.metadata.keys():
            self.ui.tagEdit.setText(self.current_note.metadata['tags'])
        else:
            self.ui.tagEdit.setText('')

        if 'title' in self.current_note.metadata.keys():
            title = self.current_note.metadata['title']
            self.ui.titleEdit.setText(self.current_note.metadata['title'])
        else:
            title = self.current_note.unsafename
            self.ui.titleEdit.setText(self.current_note.unsafename)

        # update the window title
        self.setWindowTitle(' '.join([WINDOW_TITLE, '-', title, tab_date]))

        if reload_editor:
            # cursor = self.noteEditor.textCursor()
            # start_pos = cursor.selectionStart()
            # end_pos = cursor.selectionEnd()
            self.noteEditor.set_note_text(content)
            # cursor.setPosition(start_pos)
            # cursor.setPosition(end_pos, QtGui.QTextCursor.KeepAnchor)
            # self.noteEditor.setTextCursor(cursor)

        if self.preview_tab is None:
            self.update_ui_preview()

        if self.diff_tab is None:
            self.update_ui_diff(content, new_content)

        if self.query is not '':
            self.noteEditor.highlight_search(self.query.split(' '))

        self.noteEditor.blockSignals(False)
        self.ui.tagEdit.blockSignals(False)
        self.ui.titleEdit.blockSignals(False)

    def click_update_ui_views(self, idx=None):
        if idx is None:
            i = self.ui.notesList.currentRow()
        else:
            i = idx.row()

        self.current_note = self.notes_list[i]
        self.update_ui_views()

    def keyseq_update_ui_views(self, direction):
        """
        Moves through the notes list, looping at each end

        :param direction: which direction to move 'up' or 'down'
        """
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
        self.ui.notePreview.setSearchPaths([self.notes_dir, ])
        html_filename = self.current_note.safename + HTML_EXTENSION
        url = QtCore.QUrl('html/' + html_filename)
        try:
            with open(html_filename):
                pass
        except IOError:
            # file doesn't exist, create it
            self.save_html(self.current_note.content)
        self.ui.notePreview.setSource(url)
        self.ui.notePreview.reload()

    def update_ui_diff(self, content, new_content):
        if content != new_content:
            diff_html = diff_to_html(content, new_content)
        else:
            diff_html = ''
        self.ui.noteDiff.setHtml(diff_html)

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
            self.ui.splitter.setSizes([256,current_size[1]])
        elif self.notes_list_splitter_size is not None:
            self.notes_list_splitter_size = None
            self.ui.splitter.setSizes([0,current_size[1]])
        elif self.notes_list_splitter_size is None:
            self.notes_list_splitter_size = self.ui.splitter.sizes()
            self.ui.splitter.setSizes([0,current_size[1]])
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
        filepath = self.current_note.filepath
        new_content = self.noteEditor.toPlainText()
        # if the new content is an empty note and delete empty notes is enabled
        # delete the note and it's history
        if len(new_content.strip()) == 0 and self.delete_empty_note(filepath):
            self.save_timer.stop()
            self.search.remove(filepath)
            self.all_notes = self.load_notemodels()
            self.load_ui_notes_list(self.all_notes)
            self.update_ui_views()
            return
        else:
            if self.old_data:
                # if we've edited a history record then record the last saved note data
                # to the history before saving any new data
                self.current_note.record(self.notes_dir)
                self.old_data = None
            # update the content (will save automatically)
            self.current_note.content = new_content
            self.current_note.metadata['title'] = self.ui.titleEdit.text()
            self.current_note.metadata['tags'] = self.ui.tagEdit.text()

        self.search.update(filepath)
        self.save_html(new_content)

        if record:
            self.current_note.record(self.notes_dir)

        self.save_timer.stop()
        self.all_notes = self.load_notemodels()
        self.update_ui_views(None, False)

    def save_html(self, content):
        # create the html storage directory
        try:
            html_dir = os.path.join(self.notes_dir, HTML_FOLDER)
            os.makedirs(html_dir)
        except OSError:
            # already there
            pass

        try:
            header = build_preview_header_html(self.current_note.metadata['title'])
        except KeyError:
            # no title in metadata
            header = build_preview_header_html('')
        body = self.md.convert(content)  # TODO: getting re MemoryErrors for large files
        footer = build_preview_footer_html()
        html = header + body + footer
        filepath = os.path.join(self.notes_dir, 'html', self.current_note.safename) + HTML_EXTENSION
        self._write_file(filepath, html)

    def search_files(self, query=None):
        self.query = query
        if query == '':
            founds = self.all_notes
        elif query is None:
            founds = self.all_notes
        else:
            try:
                founds = sorted(self.search.run(self.query), key=lambda x: x.matchsum, reverse=True)
            except SearchError as e:
                logger.warning('[serach_files] %s'%e)
                founds = []
                message_box = QtGui.QMessageBox()
                message_box.setText('No notes directory selected.'.format(self.current_note.notename))
                message_box.setInformativeText('Please change your settings.')
                message_box.exec_()
        self.load_ui_search_list(founds)

    def load_ui_search_list(self, results):
        self.ui.notesList.clear()
        items = []
        for item in results:
            n = NoteModel(item.filepath)
            u = n.notename
            self.ui.notesList.addItem(u)
            items.append(n)
        self.notes_list = items
        self.ui.notesList.setCurrentRow(0)

    def new_note(self):
        tagged_title = self.ui.omniBar.text()
        if tagged_title == '':
            return
        if tagged_title in self.all_notes:
            return

        # filter the #tags out
        words = tagged_title.split(' ')
        tags = ''
        title = ''
        for word in words:
            if word[0] == '#':
                tags += ' ' + word[1:]
            else:
                title += ' ' + word

        title = title.strip()
        tags = tags.strip()

        # build the new note
        filename = self._clean_filename(title) + NOTE_EXTENSION
        filepath = os.path.join(self.notes_dir, filename)
        content = title + '\n'
        new_note = NoteModel(filepath)
        new_note.metadata['title'] = title
        new_note.metadata['tags'] = tags
        new_note.content = content

        # update
        self.search.add(filepath)
        self.all_notes = self.load_notemodels()
        self.current_note = self.all_notes[0]
        self.update_ui_views()
        self.ui.omniBar.setText('')
        # set the focus on the editor and move the cursor to the end
        self.noteEditor.setFocus()
        cursor = self.noteEditor.textCursor()
        cursor.movePosition(QtGui.QTextCursor.MoveOperation.End,QtGui.QTextCursor.MoveMode.MoveAnchor)
        self.noteEditor.setTextCursor(cursor)

    def load_history_data(self):
        self.ui.historySlider.blockSignals(True)
        try:
            hlen = len(self.current_note.history)
            self.ui.historySlider.setMaximum(hlen)
            self.ui.historySlider.setSliderPosition(hlen)
        except:
            self.ui.historySlider.setMaximum(0)
            self.ui.historySlider.setSliderPosition(1)
        self.ui.historySlider.blockSignals(False)

    def load_old_note(self,sliderpos):
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
        ret = dialog.exec_()
        if ret:
            # set the current tab to the settings tab
            dialog.ui.tabWidget.setCurrentIndex(0)
            # set the help source files
            resource_dir = os.path.join(APP_DIR, 'resources')
            dialog.ui.textMarkdownHelp.setSearchPaths([resource_dir, ])
            dialog.ui.textShorcutsHelp.setSearchPaths([resource_dir, ])
            dialog.ui.textAboutHelp.setSearchPaths([resource_dir, ])
            md_url = QtCore.QUrl('markdown_help.html')
            dialog.ui.textMarkdownHelp.setSource('markdown_help.html')
            dialog.ui.textShorcutsHelp.setSource('keyboard_shortcuts.html')
            dialog.ui.textAboutHelp.setSource('about.html')
            # a tuple of widget types to find in the settings tab
            to_find = (QtGui.QLineEdit,QtGui.QFontComboBox,QtGui.QComboBox,QtGui.QCheckBox)
            # find all the widgets in the settings tab and set the
            # conf dictionary
            for f in to_find:
                for c in dialog.ui.tabWidget.currentWidget().findChildren(f):
                    name = c.objectName()
                    if name == 'conf_notesLocation':
                        self.conf[name] = c.text()
                    elif name == 'conf_checkbox_preview':
                        if c.checkState() == QtCore.Qt.CheckState.Unchecked:
                            self.conf[name] = 0
                        else:
                            self.conf[name] = 1
                    elif name == 'conf_checkbox_diff':
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
                    elif name == 'conf_checkbox_merge':
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
            self.search = SearchNotes(self.notes_dir)
            self.all_notes = self.load_notemodels()
            # remove any empty file and history (if checked) and reload file list
            self.delete_empty_notes()
            # update the file list and views
            self.load_ui_notes_list(self.all_notes)

        elif self.first_run:
            shutil.rmtree(self.app_data_dir)
            sys.exit()

    def load_styles(self):
        if 'style' in self.conf.keys():
            style_dir = os.path.join(self.app_data_dir, 'styles', self.conf['style'])
        else:
            style_dir = os.path.join(APP_DIR, 'styles', 'default')

        editor_path = os.path.join(style_dir, 'editor.css')
        preview_path = os.path.join(style_dir, 'preview.css')
        diff_path = os.path.join(style_dir, 'diff.css')

        if os.path.exists(editor_path):
            editor_style = self._read_file(editor_path)
            self.noteEditor.setStyleSheet(editor_style)
            self.noteEditor.document().setDefaultStyleSheet(editor_style)

        if os.path.exists(preview_path):
            preview_style = self._read_file(preview_path)
            self.ui.notePreview.document().setDefaultStyleSheet(preview_style)

        if os.path.exists(diff_path):
            diff_style = self._read_file(diff_path)
            self.ui.noteDiff.setStyleSheet(diff_style)

    def click_older_date(self):
        sliderpos = self.ui.historySlider.sliderPosition()
        if sliderpos != self.ui.historySlider.minimum():
            self.ui.historySlider.setSliderPosition(sliderpos - 1)
            self.load_old_note(sliderpos - 1)

    def click_newer_date(self):
        sliderpos = self.ui.historySlider.sliderPosition()
        if sliderpos != self.ui.historySlider.maximum():
            self.ui.historySlider.setSliderPosition(sliderpos + 1)
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
            timestring = self.current_note.history[index][:-(len(ZIP_EXTENSION)+1)]
            dt = self._history_timestring_to_datetime(timestring)
            tooltip = human_date(dt)
            self.ui.historySlider.setToolTip(tooltip)
        except IndexError:
            # at the 'now' position
            pass

    def delete_empty_notes(self):
        if 'conf_checkbox_deleteempty' in self.conf.keys() and int(self.conf['conf_checkbox_deleteempty']) > 0:
            for n in self.all_notes:
                data = self._read_file(n.filepath)
                # with open(n.filepath, mode='rb') as f:
                #     data = f.read()
                c, m = parse_note_content(data)
                if len(c.strip()) == 0:
                    self.delete_note(n.filepath)
            self.all_notes = self.load_notemodels()

    def delete_empty_note(self, filepath):
        if 'conf_checkbox_deleteempty' in self.conf.keys() and int(self.conf['conf_checkbox_deleteempty']) > 0:
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
            self.delete_note(self.current_note.filepath)
            self.all_notes = self.load_notemodels()
            omni_text = self.ui.omniBar.text()
            if omni_text == '':
                self.load_ui_notes_list(self.all_notes)
            else:
                self.search_files(omni_text)

    def delete_note(self, filepath):
        paths = [filepath,
                 filepath + HTML_EXTENSION,
                 filepath + ZIP_EXTENSION]
        for path in paths:
            try:
                os.remove(path)
                ret = True
            except OSError as e:
                logger.warning(e)
                if not os.path.exists(path):
                    ret = True
                else:
                    ret = False
        try:
            self.search.remove(filepath)
            ret = True
        except:
            ret = False

        return ret

    def do_first_run(self):
        """ Do stuff the first time the app runs """
        # Show them the settings dialog
        self.load_settings()

    def _clean_filename(self, unclean):
        clean = unclean
        for c in UNSAFE_CHARS:
            clean = clean.replace(c, '_')
        return clean

    def _history_timestring_to_datetime(self, timestring):
        return datetime(int(timestring[0:4]),
                          int(timestring[4:6]),
                          int(timestring[6:8]),
                          int(timestring[8:10]),
                          int(timestring[10:12]),
                          int(timestring[12:]))

    def _write_file(self, filepath, filedata):
        enc_write(filepath, filedata)

    def _read_file(self, filepath):
        return enc_read(filepath)
