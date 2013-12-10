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

from Utils import safe_filename


class MotomeTextBrowser(QtGui.QTextBrowser):
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

    def process_keyseq(self,seq):
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
        pass

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