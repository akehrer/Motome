# Import the future
from __future__ import print_function
from __future__ import unicode_literals

# Import standard library modules
import re
from mimetypes import guess_type
from os import path
from shutil import copyfile

# Import Qt modules
from PySide import QtGui

# Import configuration values
from config import HIGHLIGHT_COLOR, MEDIA_FOLDER, PLATFORM

from Utils import safe_filename, grab_urls


class MotomeTextBrowser(QtGui.QTextBrowser):
    """Custom QTextBrowser for the Motome application"""

    def __init__(self, parent, notes_dir, *args, **kwargs):
        super(MotomeTextBrowser, self).__init__(parent, *args, **kwargs)

        self.setAcceptDrops(True)
        self.setReadOnly(False)
        self.setAcceptRichText(False)
        self.setMouseTracking(True)
        self.setOpenLinks(False)
        self.setOpenExternalLinks(False)

        self.notes_dir = notes_dir

        QtGui.QShortcut(QtGui.QKeySequence('Ctrl+B'), self, lambda item=None: self.process_keyseq('ctrl_b'))
        QtGui.QShortcut(QtGui.QKeySequence('Ctrl+I'), self, lambda item=None: self.process_keyseq('ctrl_i'))

        QtGui.QShortcut(QtGui.QKeySequence('Ctrl+K'), self, lambda item=None: self.process_insertseq('ctrl_k'))
        QtGui.QShortcut(QtGui.QKeySequence('Ctrl+Shift+K'), self,
                        lambda item=None: self.process_insertseq('ctrl_shift_k'))

    def process_keyseq(self, seq):
        cursor = self.textCursor()
        if not cursor.hasSelection():
            cursor.select(QtGui.QTextCursor.WordUnderCursor)
            text = cursor.selectedText()
        else:
            text = cursor.selectedText()

        if seq == 'ctrl_b':
            cursor.insertText('**{0}**'.format(text))
        elif seq == 'ctrl_i':
            cursor.insertText('*{0}*'.format(text))
        else:
            print('No editor code for {0}'.format(seq))

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
            filepath, _ = QtGui.QFileDialog.getOpenFileName(self, "Select File", path.expanduser('~'))
            if filepath != '':
                self.insert_filelink(filepath)

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
        link_pattern = r'\[([^\[]+)\]\(([^\)]+)\)'
        link_transform = r'[\1](<a href="\2">\2</a>)'
        linked_content = re.sub(link_pattern, link_transform, text)
        # need to wrap in <pre> so CRLF renders and needs pre-wrap for word wrapping
        content = ''.join(('<pre style="white-space: pre-wrap;">', linked_content, '</pre>'))
        self.document().setHtml(content)

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

                filename = safe_filename(path.basename(fpath))
                dst_path = path.join(self.notes_dir, MEDIA_FOLDER, filename)
                media_path = './{0}/{1}'.format(MEDIA_FOLDER, filename)

                try:
                    is_image = 'image' in guess_type(fpath)[0]
                except TypeError:
                    is_image = False

                if is_image:
                    # user dropped an image file
                    try:
                        copyfile(fpath, dst_path)
                    except:
                        # file probably already there
                        pass
                    self.insertPlainText('![{0}]({1}) '.format(filename, media_path))
                else:
                    try:
                        copyfile(fpath, dst_path)
                    except Exception as e:
                        # file probably already there
                        print(e)
                        pass
                    self.insertPlainText('[{0}]({1})'.format(filename, media_path))

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
            cursor.insertText('[{0}]({1})'.format(link_title, link_address))
            cursor.setPosition(start_pos)
            cursor.setPosition(end_pos, QtGui.QTextCursor.KeepAnchor)
            self.setTextCursor(cursor)

    def insert_filelink(self, filepath):
        cursor = self.textCursor()
        current_pos = cursor.position()

        filename = safe_filename(path.basename(filepath))
        dst_path = path.join(self.notes_dir, MEDIA_FOLDER, filename)
        link_address = './{0}/{1}'.format(MEDIA_FOLDER, filename)

        if cursor.hasSelection():
            cursor.select(QtGui.QTextCursor.WordUnderCursor)
            link_title = cursor.selectedText()
        else:
            link_title = filename

        try:
            is_image = 'image' in guess_type(filepath)[0]
        except TypeError:
            is_image = False

        if is_image:
            # user sent an image file
            try:
                copyfile(filepath, dst_path)
            except:
                # file probably already there
                pass
            self.insertPlainText('![{0}]({1}) '.format(link_title, link_address))
        else:
            try:
                copyfile(filepath, dst_path)
            except Exception as e:
                # file probably already there
                print(e)
                pass
            self.insertPlainText('[{0}]({1})'.format(link_title, link_address))