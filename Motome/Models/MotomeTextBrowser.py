# Import the future
from __future__ import print_function
from __future__ import unicode_literals
from __future__ import absolute_import

# Import standard library modules
import cgi
import datetime
import logging
import mimetypes
import os
import re
import shutil

# Import Qt modules
from PySide import QtCore, QtGui

# Import configuration values
from Motome.config import HIGHLIGHT_COLOR, MEDIA_FOLDER, PLATFORM

from Motome.Models.Utils import safe_filename, grab_urls

# Set up the logger
logger = logging.getLogger(__name__)


class MotomeTextBrowser(QtGui.QTextBrowser):
    """Custom QTextBrowser for the Motome application"""
    noteSaved = QtCore.Signal()

    def __init__(self, parent):
        super(MotomeTextBrowser, self).__init__(parent)

        self.parent = parent

        self.setTextInteractionFlags(QtCore.Qt.TextEditorInteraction)
        self.setAcceptDrops(True)
        self.setReadOnly(False)
        self.setAcceptRichText(False)
        self.setMouseTracking(True)
        self.setOpenLinks(False)
        self.setOpenExternalLinks(False)
        self.setUndoRedoEnabled(True)
        self.setTabChangesFocus(True)
        self.setFrameShape(QtGui.QFrame.NoFrame)

        # save file timer
        self.save_interval = 1000  # msec
        self.save_timer = QtCore.QTimer()
        self.save_timer.timeout.connect(self.save_note)

        self.textChanged.connect(self.save_note)

        self.keyboard_shortcuts = {}
        self.setup_keyboard_shortcuts()

    @property
    def notes_dir(self):
        return self.parent.current_note.notedirectory

    @property
    def notemodel(self):
        return self.parent.current_note

    def setup_keyboard_shortcuts(self):
        self.keyboard_shortcuts = {'Bold':      {'seq': QtGui.QKeySequence('Ctrl+B'),
                                                 'func': lambda item=None: self.process_keyseq('ctrl_b')},
                                   'Italic':    {'seq': QtGui.QKeySequence('Ctrl+I'),
                                                 'func': lambda item=None: self.process_keyseq('ctrl_i')},
                                   'H1':        {'seq': QtGui.QKeySequence('Ctrl+1'),
                                                 'func': lambda item=None: self.process_keyseq('ctrl_1')},
                                   'H2':        {'seq': QtGui.QKeySequence('Ctrl+2'),
                                                 'func': lambda item=None: self.process_keyseq('ctrl_2')},
                                   'H3':        {'seq': QtGui.QKeySequence('Ctrl+3'),
                                                 'func': lambda item=None: self.process_keyseq('ctrl_3')},
                                   'H4':        {'seq': QtGui.QKeySequence('Ctrl+4'),
                                                 'func': lambda item=None: self.process_keyseq('ctrl_4')},
                                   'H5':        {'seq': QtGui.QKeySequence('Ctrl+5'),
                                                 'func': lambda item=None: self.process_keyseq('ctrl_5')},
                                   'H6':        {'seq': QtGui.QKeySequence('Ctrl+6'),
                                                 'func': lambda item=None: self.process_keyseq('ctrl_6')},
                                   'InsLink':   {'seq': QtGui.QKeySequence('Ctrl+K'),
                                                 'func': lambda item=None: self.process_insertseq('ctrl_k')},
                                   'InsFile':   {'seq': QtGui.QKeySequence('Ctrl+Shift+K'),
                                                 'func': lambda item=None: self.process_insertseq('ctrl_shift_k')}
                                   }
        for s in self.keyboard_shortcuts.values():
            QtGui.QShortcut(s['seq'], self, s['func'])

    def process_keyseq(self, seq):
        cursor = self.textCursor()
        example = False
        start_pos = 0
        end_pos = 0

        if not cursor.hasSelection():
            cursor.select(QtGui.QTextCursor.WordUnderCursor)
            text = cursor.selectedText()
            if text == '':
                text = 'example text'
                example = True
        else:
            text = cursor.selectedText()

        if seq == 'ctrl_b':
            cursor.insertText('**{0}**'.format(text))
            if example:
                start_pos = cursor.selectionEnd() - len(text) - 2
                end_pos = start_pos + len(text)
        elif seq == 'ctrl_i':
            cursor.insertText('*{0}*'.format(text))
            if example:
                start_pos = cursor.selectionEnd() - len(text) - 1
                end_pos = start_pos + len(text)
        elif seq == 'ctrl_1':
            cursor.insertText('# {0}\n'.format(text))
        elif seq == 'ctrl_2':
            cursor.insertText('## {0}\n'.format(text))
        elif seq == 'ctrl_3':
            cursor.insertText('### {0}\n'.format(text))
        elif seq == 'ctrl_4':
            cursor.insertText('#### {0}\n'.format(text))
        elif seq == 'ctrl_5':
            cursor.insertText('##### {0}\n'.format(text))
        elif seq == 'ctrl_6':
            cursor.insertText('###### {0}\n'.format(text))
        else:
            logger.info('No editor code for {0}'.format(seq))

        if example:
            if end_pos == 0:
                start_pos = cursor.selectionEnd() - len(text)
                end_pos = start_pos + len(text)
            cursor.setPosition(start_pos)
            cursor.setPosition(end_pos, QtGui.QTextCursor.KeepAnchor)
            self.setTextCursor(cursor)

    def process_insertseq(self, seq):
        cursor = self.textCursor()
        current_pos = cursor.position()

        link_title = 'Title'
        link_address = 'http://www.example.com'

        if not cursor.hasSelection():
            cursor.select(QtGui.QTextCursor.WordUnderCursor)
            text = cursor.selectedText()
            if text == '':
                text = 'example text'
        else:
            link_title = cursor.selectedText()

        if seq == 'ctrl_k':
            self._insert_hyperlink(title=link_title)
        elif seq == 'ctrl_shift_k':
            filepath, _ = QtGui.QFileDialog.getOpenFileName(self, "Select File", os.path.expanduser('~'))
            if filepath != '':
                self._insert_filelink(filepath)

    def event(self, event):
        if (event.type() == QtCore.QEvent.KeyPress) and (event.key() == QtCore.Qt.Key_Tab):
            self.insertHtml('&nbsp;&nbsp;&nbsp;&nbsp;')
            return True
        return QtGui.QTextBrowser.event(self, event)

    def set_note_text(self, content=None):
        try:
            if content is not None:
                text = cgi.escape(content)
            else:
                text = cgi.escape(self.notemodel.content)
            text = text.replace('  ', '&nbsp;&nbsp;')
            link_pattern = r'\[([^\[]+)\]\(([^\)]+)\)'
            link_transform = r'[\1](<a href="\2">\2</a>)'
            linked_content = re.sub(link_pattern, link_transform, text)
            intralink_pattern = r'\[\[([^\[]+)\]\]'
            intralink_transform = r'[[<a href="\1">\1</a>]]'
            intralink_content = re.sub(intralink_pattern, intralink_transform, linked_content)
            self.setHtml(intralink_content.replace('\n', '<br />'))
            self.setDocumentTitle(self.notemodel.title)  # for things like print to pdf
        except AttributeError:
            self.setHtml('')

    def canInsertFromMimeData(self, source):
        """ Capture pastes of files

        http://stackoverflow.com/questions/15592581/pasting-qmimedata-to-another-windows-qtextedit
        :param source:
        :return:
        """
        if source.hasImage():
            return True
        elif source.hasUrls():
            return True
        else:
            return super(MotomeTextBrowser, self).canInsertFromMimeData(source)

    def insertFromMimeData(self, source):
        """ Capture pastes of files

        http://stackoverflow.com/questions/15592581/pasting-qmimedata-to-another-windows-qtextedit
        :param source:
        :return:
        """
        if source.hasImage():
            image = source.imageData()
            now = datetime.datetime.now().strftime('%Y%m%d%H%M%S')
            imagepath = os.path.join(self.notes_dir, MEDIA_FOLDER, now + '.png')
            image.save(imagepath)
            self._insert_filelink(imagepath)
        elif source.hasUrls():
            urls = source.urls()
            self._insert_list_of_files(urls)
        super(MotomeTextBrowser, self).insertFromMimeData(source)

    def dragEnterEvent(self, e):
        """
        Need to accept drag enter events
        """
        e.accept()

    def dropEvent(self, e):
        """
        http://qt-project.org/wiki/Drag_and_Drop_of_files
        """
        # dropped files are file:// urls
        if e.mimeData().hasUrls():
            self._insert_list_of_files(e.mimeData().urls())

    def dragMoveEvent(self, e):
        """
        Need to accept drag move events
        http://qt-project.org/forums/viewthread/3093
        """
        e.accept()

    def start_save(self):
        if self.save_timer.isActive():
            self.save_timer.stop()
        self.save_timer.start(self.save_interval)

    def save_note(self):
        if self.notemodel is None:
            return

        if self.save_timer.isActive():
            self.save_timer.stop()

        content = self.toPlainText()
        self.notemodel.content = content
        self.noteSaved.emit()

    def highlight_search(self, query):
        """
        Highlight all the search terms
        http://www.qtcentre.org/threads/27005-QTextEdit-find-all
        """
        current_cursor = self.textCursor()
        extra_selections = []
        for term in query:
            self.moveCursor(QtGui.QTextCursor.Start)
            while self.find(term):
                extra = QtGui.QTextEdit.ExtraSelection()
                extra.format.setBackground(HIGHLIGHT_COLOR)
                extra.cursor = self.textCursor()
                extra_selections.append(extra)
        self.setExtraSelections(extra_selections)
        self.setTextCursor(current_cursor)

    def get_note_links(self):
        # url_re_compile = re.compile(r'\[([^\[]+)\]\(([^\)]+)\)', re.VERBOSE | re.MULTILINE)
        # return url_re_compile.findall(self.toPlainText())
        return self.notemodel.urls

    def _insert_list_of_files(self, file_list):
        for filepath in file_list:
            if filepath.isLocalFile():
                if 'win32' in PLATFORM:
                # mimedata path includes a leading slash that confuses copyfile on windows
                # http://stackoverflow.com/questions/2144748/is-it-safe-to-use-sys-platform-win32-check-on-64-bit-python
                    fpath = filepath.path()[1:]
                else:
                    # not windows
                    fpath = filepath.path()

                self._insert_filelink(fpath)

    def _insert_hyperlink(self, title=None):
        cursor = self.textCursor()
        current_pos = cursor.position()

        if title is not None:
            link_title = title
        else:
            link_title = 'Link Title'

        link_address = 'http://www.example.com'
        start_pos = current_pos + 1
        end_pos = start_pos + len(link_title)

        clipboard_text = QtGui.QClipboard().text()

        if len(grab_urls(clipboard_text)) > 0:
            link_address = clipboard_text

        text, ret = QtGui.QInputDialog.getText(self, 'Insert Link', 'Link address:', QtGui.QLineEdit.Normal,
                                               link_address)

        if cursor.hasSelection():
            start_pos = cursor.selectionEnd() + 3
            end_pos = start_pos + len(link_address)

        if ret:
            if text != '':
                link_address = text
            cursor.insertHtml('[{0}](<a href="{1}">{1}</a>)'.format(link_title, link_address))
            cursor.setPosition(start_pos)
            cursor.setPosition(end_pos, QtGui.QTextCursor.KeepAnchor)
            self.setTextCursor(cursor)

    def _insert_filelink(self, filepath):
        # create the media storage directory
        try:
            html_dir = os.path.join(self.notes_dir, MEDIA_FOLDER)
            os.makedirs(html_dir)
        except OSError:
            # already there
            pass
        except AttributeError:
            # notemodel is None
            return

        cursor = self.textCursor()
        current_pos = cursor.position()

        filename = safe_filename(os.path.basename(filepath))
        dst_path = os.path.join(self.notes_dir, MEDIA_FOLDER, filename)
        link_address = './{0}/{1}'.format(MEDIA_FOLDER, filename)

        if cursor.hasSelection():
            link_title = cursor.selectedText()
        else:
            link_title = filename

        try:
            is_image = 'image' in mimetypes.guess_type(filepath)[0]
        except TypeError:
            is_image = False

        if is_image:
            # user sent an image file
            try:
                shutil.copyfile(filepath, dst_path)
            except (IOError, shutil.Error):
                # file probably already there
                pass
            self.insertHtml('![{0}](<a href="{1}">{1}</a>)'.format(link_title, link_address))
        else:
            try:
                shutil.copyfile(filepath, dst_path)
            except (IOError, shutil.Error):
                # file probably already there
                pass
            self.insertHtml('[{0}](<a href="{1}">{1}</a>)'.format(link_title, link_address))