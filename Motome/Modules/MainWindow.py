# Import the future
from __future__ import print_function
from __future__ import unicode_literals

# Import standard library modules
import gzip
import re
import os
import shutil
import sys
from datetime import datetime

# Import extra modules
import markdown

# Import Qt modules
from PySide import QtCore, QtGui

# Import application window view
from Views.MainWindow import Ui_MainWindow

# Import configuration values
from config import NOTE_EXTENSION, ZIP_EXTENSION, END_OF_TEXT, MEDIA_FOLDER

# Import additional modules
from MotomeTextBrowser import MotomeTextBrowser
from MergeNotesDialog import MergeNotesDialog
from MergeHistoryDialog import MergeHistoryDialog
from NoteModel import NoteModel
from SettingsDialog import SettingsDialog
from Search import SearchNotes, SearchError
from Utils import build_preview_footer_html, build_preview_header_html, \
    diff_to_html, parse_note_content, enc_read, enc_write


class MainWindow(QtGui.QMainWindow):

    def __init__(self, parent=None):
        super(MainWindow, self).__init__(parent)

        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)

        self.setWindowTitle("Motome")

        # additional settings
        self.ui.notePreview.setOpenExternalLinks(True)

        # Set up directories
        self.user_home_dir = os.path.expanduser('~')
        self.app_data_dir = os.path.join(self.user_home_dir, '.Motome')
        self.notes_dir = ''

        # note file vars
        self.note_extension = NOTE_EXTENSION

        self.conf = {}

        # Load configuration
        self.load_conf()

        # tab data
        self.tab_date = ''
        self.preview_tab = None
        self.diff_tab = None

        # create the app storage directory
        try:
            os.makedirs(self.app_data_dir)
            self.first_run = True
        except OSError:
            self.first_run = False

        # insert the custom text editor
        self.noteEditor = MotomeTextBrowser(self.ui.tabEditor, self.notes_dir)
        self.noteEditor.setTextInteractionFlags(QtCore.Qt.LinksAccessibleByKeyboard|QtCore.Qt.LinksAccessibleByMouse|
                                                QtCore.Qt.TextBrowserInteraction|QtCore.Qt.TextEditable|
                                                QtCore.Qt.TextEditorInteraction|QtCore.Qt.TextSelectableByKeyboard|
                                                QtCore.Qt.TextSelectableByMouse)
        self.noteEditor.setObjectName("noteEditor")
        # set a basic fixed-width style
        self.noteEditor.setStyleSheet('QTextEdit {Courier New, monospace, fixed}')
        self.ui.verticalLayout_2.insertWidget(0, self.noteEditor)
        self.noteEditor.textChanged.connect(self.start_save)
        self.noteEditor.anchorClicked.connect(self.load_anchor)

        # Set the window location and size
        if 'window_x'in self.conf.keys():
            rect = QtCore.QRect(int(self.conf['window_x']),
                                int(self.conf['window_y']),
                                int(self.conf['window_width']),
                                int(self.conf['window_height']))
            self.setGeometry(rect)

        # load the styles
        self.load_styles()

        # markdown translator
        self.md = markdown.Markdown()

        # current view
        self.current_note = None
        self.old_data = ''
        self.meta = {}
        self.history = []

        # set the views
        self.set_ui_views()
        self.ui.notePreview.setSearchPaths(self.notes_dir)

        # save file timer
        self.save_interval = 1000 # msec
        self.save_timer = QtCore.QTimer()
        self.save_timer.timeout.connect(self.save_file)

        # search
        self.search = None
        self.query = None
        self.query_timer = QtCore.QTimer()
        self.query_timer.setSingleShot(True)
        self.query_timer.setInterval(250)
        self.query_timer.timeout.connect(self.search_files)

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
        #ctrl = QtCore.Qt.Key_Control
        #up = QtCore.Qt.Key_Up
        #down = QtCore.Qt.Key_Down
        esc = QtCore.Qt.Key_Escape
        delete = QtCore.Qt.Key_Delete
        QtGui.QShortcut(QtGui.QKeySequence('Ctrl+N'), self, lambda item=None: self.process_keyseq('ctrl_n'))
        QtGui.QShortcut(QtGui.QKeySequence('Ctrl+F'), self, lambda item=None: self.process_keyseq('ctrl_f'))
        QtGui.QShortcut(QtGui.QKeySequence('Ctrl+E'), self, lambda item=None: self.process_keyseq('ctrl_e'))
        QtGui.QShortcut(QtGui.QKeySequence('Ctrl+P'), self, lambda item=None: self.process_keyseq('ctrl_p'))
        QtGui.QShortcut(QtGui.QKeySequence('Ctrl+D'), self, lambda item=None: self.process_keyseq('ctrl_d'))
        QtGui.QShortcut(QtGui.QKeySequence('Ctrl+L'), self, lambda item=None: self.process_keyseq('ctrl_l'))
        QtGui.QShortcut(QtGui.QKeySequence('Ctrl+T'), self, lambda item=None: self.process_keyseq('ctrl_t'))
        QtGui.QShortcut(QtGui.QKeySequence('Ctrl+M'), self, lambda item=None: self.process_keyseq('ctrl_m'))
        QtGui.QShortcut(QtGui.QKeySequence('Ctrl+S'), self, lambda item=None: self.process_keyseq('ctrl_s'))
        QtGui.QShortcut(QtGui.QKeySequence('Ctrl+R'), self, lambda item=None: self.process_keyseq('ctrl_r'))
        QtGui.QShortcut(QtGui.QKeySequence('Ctrl+J'), self, lambda item=None: self.process_keyseq('ctrl_j'))
        QtGui.QShortcut(QtGui.QKeySequence('Ctrl+K'), self, lambda item=None: self.process_keyseq('ctrl_k'))
        QtGui.QShortcut(QtGui.QKeySequence('Ctrl+Shift+L'), self, lambda item=None: self.process_keyseq('ctrl_shift_l'))
        QtGui.QShortcut(QtGui.QKeySequence('Ctrl+Shift+U'), self, lambda item=None: self.process_keyseq('ctrl_shift_u'))
        QtGui.QShortcut(QtGui.QKeySequence(esc), self, lambda item=None: self.process_keyseq('esc'))

        # remove notes in the note list using the delete key
        QtGui.QShortcut(QtGui.QKeySequence(delete), self.ui.notesList, lambda item=None: self.delete_current_note())

        if self.first_run:
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
            self.save_file(record=False)
        elif seq == 'ctrl_r':
            self.save_file(record=True)
        elif seq == 'ctrl_j':
            self.keyseq_update_ui_views('down')
        elif seq == 'ctrl_k':
            self.keyseq_update_ui_views('up')
        elif seq == 'ctrl_shift_l':
            self.toggle_notes_list_view()
        elif seq == 'ctrl_shift_u':
            now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            if self.noteEditor.hasFocus():
                self.noteEditor.insertPlainText('{0}\n'.format(now))
            else:
                self.ui.omniBar.setText(now)
        elif seq == 'esc':
            self.ui.omniBar.setText('')
        else:
            print('No code for {0}'.format(seq))

    def stop(self):
        if self.save_timer.isActive():
            self.save_file(record=True)
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
            # with open(filepath, mode='rb') as f:
            #     for line in f:
            #         try:
            #             key, value = line.strip().split(':', 1)
            #             self.conf[key] = value
            #         except ValueError:
            #             pass
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

    def load_ui_notes_list(self, items):
        self.ui.notesList.clear()
        for item in items:
            u = item.notename
            self.ui.notesList.addItem(u)
        self.notes_list = items
        self.ui.notesList.setCurrentRow(0)

    def update_ui_views(self, old_content=None, reload_editor=True):
        self.noteEditor.blockSignals(True)
        self.ui.tagEdit.blockSignals(True)

        try:
            filepath = self.current_note.filepath
            self.meta = {}
            data = self._read_file(filepath)
            self.old_data = data
        except:
            self.noteEditor.blockSignals(False)
            self.ui.tagEdit.blockSignals(False)
            return

        if old_content is None:
            content, self.meta = parse_note_content(data)
            new_content = content
            self.tab_date = ''
            self.load_history_data(filepath)
        else:
            new_content, self.meta = parse_note_content(data)
            content, x = parse_note_content(old_content[0])
            dt = old_content[1]
            self.tab_date = '[{Y}-{m}-{D} {H}:{M}:{S}]'.format(Y=dt[0:4],
                                                                m=dt[4:6],
                                                                D=dt[6:8],
                                                                H=dt[8:10],
                                                                M=dt[10:12],
                                                                S=dt[12:])

        if 'tags' in self.meta.keys():
            self.ui.tagEdit.setText(self.meta['tags'])
        else:
            self.ui.tagEdit.setText('')

        self.ui.toolBox.setTabText(0, 'Editor: {0} {1}'.format(self.current_note.notename, self.tab_date))
        if reload_editor:
            # link_pattern = r'\[([^\[]+)\]\(([^\)]+)\)'
            # link_transform = r'[\1](<a href="\2">\2</a>)'
            # linked_content = re.sub(link_pattern, link_transform, content)
            # self.noteEditor.document().setHtml('<pre>' + linked_content + '</pre>')
            self.noteEditor.set_note_text(content)

        if self.preview_tab is None:
            self.update_ui_preview(content)

        if self.diff_tab is None:
            self.update_ui_diff(content, new_content)

        if self.query is not None:
            self.noteEditor.highlight_search(self.query.split(' '))

        self.noteEditor.blockSignals(False)
        self.ui.tagEdit.blockSignals(False)

    def click_update_ui_views(self, idx=None):
        if idx is None:
            i = self.ui.notesList.currentRow()
        else:
            i = idx.row()
        self.current_note = self.notes_list[i]
        self.update_ui_views()

    def keyseq_update_ui_views(self,direction):
        """
        Moves through the notes list, looping at each end

        direction -- which direction to move 'up' or 'down'
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

    def update_ui_preview(self, content):
        try:
            header = build_preview_header_html(self.meta['title'])
        except KeyError:
            header = build_preview_header_html('')
        body = self.md.convert(content)  # TODO: getting re MemoryErrors for large files
        footer = build_preview_footer_html()
        html = header + body + footer
        self.ui.toolBox.setTabText(1, 'Preview: {0} {1}'.format(self.current_note.notename, self.tab_date))
        self.ui.notePreview.setSearchPaths([self.notes_dir,])
        self.ui.notePreview.setHtml(html)

    def update_ui_diff(self, content, new_content):
        if content != new_content:
            diff_html = diff_to_html(content,new_content)
            self.ui.toolBox.setTabText(2, 'Diff: {0} {1}'.format(self.current_note.notename, self.tab_date))
        else:
            diff_html = ''
            self.ui.toolBox.setTabText(2, 'Diff: {0}'.format(self.current_note.notename))
        self.ui.noteDiff.setHtml(diff_html)

    def remove_preview_tab(self):
        for idx in range(self.ui.toolBox.count()):
            if 'Preview' in self.ui.toolBox.tabText(idx):
                    self.preview_tab = self.ui.toolBox.widget(idx)
                    self.ui.toolBox.removeTab(idx)

    def insert_preview_tab(self):
        try:
            text = 'Preview: %s [%s]'%(self.current_note.notename,self.tab_date)
        except TypeError:
            text = 'Preview'
        self.ui.toolBox.insertTab(1,self.preview_tab,text)
        self.preview_tab = None

    def remove_diff_tab(self):
        for idx in range(self.ui.toolBox.count()):
            if 'Diff' in self.ui.toolBox.tabText(idx):
                    self.diff_tab = self.ui.toolBox.widget(idx)
                    self.ui.toolBox.removeTab(idx)

    def insert_diff_tab(self):
        try:
            text = 'Diff: %s [%s]'%(self.current_note.notename,self.tab_date)
        except TypeError:
            text = 'Diff'
        self.ui.toolBox.insertTab(2,self.diff_tab,text)
        self.diff_tab = None

    def remove_history_bar(self):
        self.ui.frameHistory.hide()

    def insert_history_bar(self):
        self.ui.frameHistory.show()

    def remove_merge_button(self):
        self.ui.btnMergeNotes.hide()

    def insert_merge_button(self):
        self.ui.btnMergeNotes.show()

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
            print('Toggle notes list view wierdness {0}'.format(self.notes_list_splitter_size))

    def start_save(self):
        if self.save_timer.isActive():
            self.save_timer.stop()
        self.save_timer.start(self.save_interval)

    def save_file(self, record=False):
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

        if not 'title' in self.meta.keys():
            self.meta['title'] = self.current_note.notename
        self.meta['tags'] = self.ui.tagEdit.text()
        # write the new file data (using 'wb' keeps the \n in Windows) [http://stackoverflow.com/questions/2536545/]
        filedata = new_content + '\n' + END_OF_TEXT + '\n'
        for key, value in self.meta.items():
                filedata = filedata + '{0}:{1}\n'.format(key, value)
        self._write_file(filepath, filedata)
        # with open(filepath, mode='wb', encoding=ENCODING) as f:
        #     f.write(new_content)
        #     f.write('\n')
        #     f.write(END_OF_TEXT + '\n')
        #     for key, value in self.meta.items():
        #         f.write(u'{0}:{1}\n'.format(key, value))
        # update the search index
        self.search.update(filepath)

        if record:
            # write the old file data to the zip archive
            now = datetime.now().strftime('%Y%m%d%H%M%S')
            old_filename = now + NOTE_EXTENSION
            old_filepath = os.path.join(self.notes_dir,old_filename)

            self._write_file(old_filepath, self.old_data)
            # with open(old_filepath, mode='wb', encoding=ENCODING) as fo:
            #     fo.write(self.old_data)
            zip_filepath = filepath + ZIP_EXTENSION
            with gzip.GzipFile(zip_filepath, 'a') as myzip:
                myzip.write(old_filepath,old_filename)
            os.remove(old_filepath)
            self.ui.statusbar.showMessage('Recorded {0}'.format(self.current_note.filepath),5000)

        self.save_timer.stop()
        self.all_notes = self.load_notemodels()
        self.update_ui_views(None, False)

    def search_files(self, query=None):
        if query == '':
            self.query = None
            self.load_ui_notes_list(self.all_notes)
        elif query is None and self.query_timer.isActive():
            pass
        elif query is not None and not self.query_timer.isActive():
            self.query = query
            self.query_timer.start()
        elif query is not None and self.query_timer.isActive():
            self.query = query
            self.query_timer.stop()
            self.query_timer.start()
        else:
            try:
                founds = self.search.run(self.query)
            except SearchError:
                founds = []
                self.ui.statusbar.showMessage('No notes directory selected, please change your settings',0)
            self.load_ui_search_list(founds)

    def load_ui_search_list(self, results):
        self.ui.notesList.clear()
        items = []
        for item in results:
            n = NoteModel(item.notepath)
            u = n.notename
            self.ui.notesList.addItem(u)
            items.append(n)
        self.notes_list = items
        self.ui.notesList.setCurrentRow(0)

    def new_note(self):
        title = self.ui.omniBar.text()
        if title == '':
            return
        if title in self.all_notes:
            return
        filename = title+NOTE_EXTENSION
        filepath = os.path.join(self.notes_dir,filename)
        filedata = title + '\n'
        self._write_file(filepath, filedata)
        # with open(filepath, mode='wb', encoding=ENCODING) as f:
        #     f.write(title + '\n')
        # add to search index
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

    def load_history_data(self,filepath):
        zip_filepath = filepath + ZIP_EXTENSION
        self.history = []
        self.ui.historySlider.blockSignals(True)
        try:
            with gzip.GzipFile(zip_filepath, 'r') as myzip:
                self.history = sorted(myzip.namelist())
            hlen = len(self.history)
            self.ui.historySlider.setMaximum(hlen)
            self.ui.historySlider.setSliderPosition(hlen)
        except:
            self.ui.historySlider.setMaximum(0)
            self.ui.historySlider.setSliderPosition(1)
        self.ui.historySlider.blockSignals(False)

    def load_old_note(self,sliderpos):
        if sliderpos == self.ui.historySlider.maximum():
            self.update_ui_views()
        else:
            try:
                zip_filepath = self.current_note.filepath + ZIP_EXTENSION
                with gzip.GzipFile(zip_filepath, 'r') as myzip:
                    old_content = (unicode(myzip.read(self.history[sliderpos])),self.history[sliderpos][:-4])
            except:
                old_content = None
            self.update_ui_views(old_content=old_content)

    def load_settings(self):
        dialog = SettingsDialog(self.conf)
        ret = dialog.exec_()
        if ret:
            # set the current tab to the settings tab
            dialog.ui.tabWidget.setCurrentIndex(0)
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
            style_dir = os.path.join(self.app_data_dir, 'styles', 'default')

        editor_path = os.path.join(style_dir, 'editor.css')
        preview_path = os.path.join(style_dir, 'preview.css')
        diff_path = os.path.join(style_dir, 'diff.css')

        if os.path.exists(editor_path):
            editor_style = self._read_file(editor_path) #open(editor_path, 'r').read()
            self.noteEditor.setStyleSheet(editor_style)

        if os.path.exists(preview_path):
            preview_style = self._read_file(preview_path) #open(preview_path, 'r').read()
            self.ui.notePreview.document().setDefaultStyleSheet(preview_style)

        if os.path.exists(diff_path):
            diff_style = self._read_file(diff_path) #open(diff_path, 'r').read()
            self.ui.noteDiff.document().setDefaultStyleSheet(diff_style)

    def click_older_date(self):
        sliderpos = self.ui.historySlider.sliderPosition()
        self.ui.historySlider.setSliderPosition(sliderpos - 1)

    def click_newer_date(self):
        sliderpos = self.ui.historySlider.sliderPosition()
        self.ui.historySlider.setSliderPosition(sliderpos + 1)

    def click_merge_history(self):
        try:
            filepath = self.current_note.filepath
            dialog = MergeHistoryDialog(filepath)
            dialog.exec_()
        except TypeError:
            pass

    def click_merge_notes(self):
        dialog = MergeNotesDialog(self.notes_list,self.notes_dir,self.md)
        dialog.exec_()
        self.all_notes = self.load_notemodels()
        self.load_ui_notes_list(self.all_notes)
        self.update_ui_views()

    def set_ui_views(self):
        try:
            if int(self.conf['conf_checkbox_preview']) == 0 and self.preview_tab is None:
                self.remove_preview_tab()
            elif self.preview_tab is not None:
                self.insert_preview_tab()

            if int(self.conf['conf_checkbox_diff']) == 0 and self.diff_tab is None:
                self.remove_diff_tab()
            elif self.diff_tab is not None:
                self.insert_diff_tab()

            if int(self.conf['conf_checkbox_history']) == 0:
                self.remove_history_bar()
            elif int(self.conf['conf_checkbox_history']) > 0:
                self.insert_history_bar()

            if int(self.conf['conf_checkbox_merge']) == 0:
                self.remove_merge_button()
            elif int(self.conf['conf_checkbox_merge']) > 0:
                self.insert_merge_button()
        except KeyError:
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
            self.load_ui_notes_list(self.all_notes)

    def delete_note(self, filepath):
        try:
            self.search.remove(filepath)
            os.remove(filepath)
            os.remove(filepath + ZIP_EXTENSION)
            return True
        except OSError:
            # Probably because there is no zip file
            if not os.path.exists(filepath):
                return True
            else:
                return False

    def do_first_run(self):
        """ Do stuff the first time the app runs """
        # Create styles folder and move base set over
        styles_dir = os.path.join(os.getcwd(), 'styles')
        dest_dir = os.path.join(self.app_data_dir, 'styles')
        shutil.copytree(styles_dir, dest_dir)
        # Show them the setting dialog
        self.load_settings()

    def _write_file(self, filepath, filedata):
        enc_write(filepath, filedata)

    def _read_file(self, filepath):
        return enc_read(filepath)
