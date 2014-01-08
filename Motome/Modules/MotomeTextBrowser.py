# Import the future
from __future__ import print_function
from __future__ import unicode_literals

# Import standard library modules
import cgi
import logging
import mimetypes
import os
import re
import shutil

# Import Qt modules
from PySide import QtCore, QtGui

# Import configuration values
from config import HIGHLIGHT_COLOR, MEDIA_FOLDER, PLATFORM

from Utils import safe_filename, grab_urls

# Set up the logger
logger = logging.getLogger(__name__)


class MotomeTextBrowser(QtGui.QTextBrowser):
    """Custom QTextBrowser for the Motome application"""

    def __init__(self, parent, notes_dir, *args, **kwargs):
        super(MotomeTextBrowser, self).__init__(parent, *args, **kwargs)

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

        self.notes_dir = notes_dir

        QtGui.QShortcut(QtGui.QKeySequence('Ctrl+B'), self, lambda item=None: self.process_keyseq('ctrl_b'))
        QtGui.QShortcut(QtGui.QKeySequence('Ctrl+I'), self, lambda item=None: self.process_keyseq('ctrl_i'))
        QtGui.QShortcut(QtGui.QKeySequence('Ctrl+1'), self, lambda item=None: self.process_keyseq('ctrl_1'))
        QtGui.QShortcut(QtGui.QKeySequence('Ctrl+2'), self, lambda item=None: self.process_keyseq('ctrl_2'))
        QtGui.QShortcut(QtGui.QKeySequence('Ctrl+3'), self, lambda item=None: self.process_keyseq('ctrl_3'))
        QtGui.QShortcut(QtGui.QKeySequence('Ctrl+4'), self, lambda item=None: self.process_keyseq('ctrl_4'))
        QtGui.QShortcut(QtGui.QKeySequence('Ctrl+5'), self, lambda item=None: self.process_keyseq('ctrl_5'))
        QtGui.QShortcut(QtGui.QKeySequence('Ctrl+6'), self, lambda item=None: self.process_keyseq('ctrl_6'))


        QtGui.QShortcut(QtGui.QKeySequence('Ctrl+K'), self, lambda item=None: self.process_insertseq('ctrl_k'))
        QtGui.QShortcut(QtGui.QKeySequence('Ctrl+Shift+K'), self,
                        lambda item=None: self.process_insertseq('ctrl_shift_k'))

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
            cursor.insertText('\n# {0}\n'.format(text))
        elif seq == 'ctrl_2':
            cursor.insertText('\n## {0}\n'.format(text))
        elif seq == 'ctrl_3':
            cursor.insertText('\n### {0}\n'.format(text))
        elif seq == 'ctrl_4':
            cursor.insertText('\n#### {0}\n'.format(text))
        elif seq == 'ctrl_5':
            cursor.insertText('\n##### {0}\n'.format(text))
        elif seq == 'ctrl_6':
            cursor.insertText('\n###### {0}\n'.format(text))
        else:
            logger.info('No editor code for {0}'.format(seq))
            # print('No editor code for {0}'.format(seq))

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
        start_pos = current_pos + 1
        end_pos = start_pos + len(link_title)

        if cursor.hasSelection():
            cursor.select(QtGui.QTextCursor.WordUnderCursor)
            link_title = cursor.selectedText()
            start_pos = cursor.selectionEnd() + 3
            end_pos = start_pos + len(link_address)

        if seq == 'ctrl_k':
            self.insert_hyperlink()
        elif seq == 'ctrl_shift_k':
            filepath, _ = QtGui.QFileDialog.getOpenFileName(self, "Select File", os.path.expanduser('~'))
            if filepath != '':
                self.insert_filelink(filepath)

    def event(self, event):
        if (event.type() == QtCore.QEvent.KeyPress) and (event.key() == QtCore.Qt.Key_Tab):
            self.insertHtml('&nbsp;&nbsp;&nbsp;&nbsp;')
            return True
        return QtGui.QTextBrowser.event(self, event)

    def highlight_search(self, query):
        """
        Highlight all the search terms
        http://www.qtcentre.org/threads/27005-QTextEdit-find-all
        """
        current_cursor = self.textCursor()
        extra_selections = []
        extra = None
        for term in query:
            self.moveCursor(QtGui.QTextCursor.Start)
            while self.find(term):
                extra = QtGui.QTextEdit.ExtraSelection()
                extra.format.setBackground(HIGHLIGHT_COLOR)
                extra.cursor = self.textCursor()
                extra_selections.append(extra)
        self.setExtraSelections(extra_selections)
        self.setTextCursor(current_cursor)

    def set_note_text(self, text):
        text = cgi.escape(text)
        text = text.replace('  ', '&nbsp;&nbsp;')
        link_pattern = r'\[([^\[]+)\]\(([^\)]+)\)'
        link_transform = r'[\1](<a href="\2">\2</a>)'
        linked_content = re.sub(link_pattern, link_transform, text)
        self.setHtml(linked_content.replace('\n', '<br />'))

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
            for filepath in e.mimeData().urls():
                # mimedata path includes a leading slash that confuses copyfile on windows
                # http://stackoverflow.com/questions/2144748/is-it-safe-to-use-sys-platform-win32-check-on-64-bit-python
                if 'win32' in PLATFORM:
                    fpath = filepath.path()[1:]
                else:
                    # not windows
                    fpath = filepath.path()

                self.insert_filelink(fpath)

    def dragMoveEvent(self, e):
        """
        Need to accept drag move events
        http://qt-project.org/forums/viewthread/3093
        """
        e.accept()

    def insert_hyperlink(self):
        cursor = self.textCursor()
        current_pos = cursor.position()

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
            cursor.select(QtGui.QTextCursor.WordUnderCursor)
            link_title = cursor.selectedText()
            start_pos = cursor.selectionEnd() + 3
            end_pos = start_pos + len(link_address)

        if ret:
            if text != '':
                link_address = text
            cursor.insertHtml('[{0}](<a href="{1}">{1}</a>)'.format(link_title, link_address))
            cursor.setPosition(start_pos)
            cursor.setPosition(end_pos, QtGui.QTextCursor.KeepAnchor)
            self.setTextCursor(cursor)

    def insert_filelink(self, filepath):
        # create the media storage directory
        try:
            html_dir = os.path.join(self.notes_dir, MEDIA_FOLDER)
            os.makedirs(html_dir)
        except OSError:
            # already there
            pass

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
            except:
                # file probably already there
                pass
            self.insertHtml('![{0}](<a href="{1}">{1}</a>)'.format(link_title, link_address))
        else:
            try:
                shutil.copyfile(filepath, dst_path)
            except Exception as e:
                # file probably already there
                pass
            self.insertHtml('[{0}](<a href="{1}">{1}</a>)'.format(link_title, link_address))
