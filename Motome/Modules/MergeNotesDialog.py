# Import the future
from __future__ import print_function
from __future__ import unicode_literals

# Import standard library modules
import gzip
import re
from datetime import datetime
from io import open
from operator import itemgetter
from os import path, remove

# Import Qt modules
from PySide import QtCore, QtGui

# Import application window view
from Views.MergeNotesDialog import Ui_MergeNotesDialog

# Import configuration values
from config import NOTE_EXTENSION, END_OF_TEXT, ZIP_EXTENSION

# Import utilities
from Utils import parse_note_content, enc_write, enc_read


class MergeNotesDialog(QtGui.QDialog):

    def __init__(self, notes_list, notes_dir, md):
        """
        Initialize the merge notes dialog
        :param notes_list: list of notes from the main window notes list
        :param notes_dir: string path to the notes directory
        :param md: a Markdown object for rendering the notes preview
        """
        super(MergeNotesDialog, self).__init__()

        self.ui=Ui_MergeNotesDialog()
        self.ui.setupUi(self)
        # install an event filter to catch internal drop events
        self.ui.notesList.installEventFilter(self)

        self.setWindowTitle('Merge & Export Notes')

        self.notes_dir = notes_dir

        self.md = md

        self.notes_list = notes_list
        self.note_extension = NOTE_EXTENSION
        self.load_notes_list(notes_list)

        self.merged_content = ''
        self.merged_meta = {}
        self.merged_history = []

        self.update_views()

    def eventFilter(self, sender, event):
        # this is the function that processes internal drop in the notesList
        if event.type() == QtCore.QEvent.ChildRemoved:
            self.update_views()
        return False # don't actually interrupt anything

    def load_notes_list(self,items):
        for item in items:
            u = item.notename
            self.ui.notesList.addItem(u)

    def update_views(self):
        self.merged_content = ''
        self.merged_meta = {}
        for i in range(self.ui.notesList.count()):
            item = self.ui.notesList.item(i)
            filename = item.text() + self.note_extension
            filepath = path.join(self.notes_dir,filename)
            data = enc_read(filepath)
            content,meta = parse_note_content(data)
            # process the meta dictionary
            for key,val in meta.items():
                if self.merged_meta.has_key(key):
                    if key == 'tags':
                        # add any new tags
                        tags = re.findall(r'\w+',meta['tags'])
                        for t in tags:
                            if t not in self.merged_meta['tags']:
                                self.merged_meta['tags'].append(t)
                    else:
                        self.merged_meta[key] = u' '.join([self.merged_meta[key],val])
                else:
                    if key == 'tags':
                        self.merged_meta['tags'] = re.findall(r'\w+',meta['tags'])
                    else:
                        self.merged_meta[key] = meta[key]
            self.merged_content += content.rstrip() + '\n\n' # clean up any trailing whitespace and add newline between notes
        html = self.md.convert(self.merged_content)
        self.ui.mergedNoteTitle.setText(self.merged_meta['title'])
        self.ui.mergedNoteTags.setText(u' '.join(self.merged_meta['tags']))
        self.ui.textMergedNotes.setText(self.merged_content)
        self.ui.textMergedPreview.setHtml(html)

    def click_note_up(self):
        current_row = self.ui.notesList.currentRow()
        if current_row == 0:
            return
        else:
            item = self.ui.notesList.takeItem(current_row)
            self.ui.notesList.insertItem(current_row-1,item)
            self.ui.notesList.setCurrentRow(current_row-1)
            self.update_views()

    def click_note_down(self):
        current_row = self.ui.notesList.currentRow()
        count = self.ui.notesList.count()
        if current_row+1 == count:
            # rows in 0 space, count in 1 space
            return
        else:
            item = self.ui.notesList.takeItem(current_row)
            self.ui.notesList.insertItem(current_row+1,item)
            self.ui.notesList.setCurrentRow(current_row+1)
            self.update_views()

    def click_export_html(self):
        filepath = path.join(self.notes_dir, 'motome_html_export')
        savefile = QtGui.QFileDialog.getSaveFileName(self, 'Export HTML', filepath,'*.html')
        if len(savefile[0]) == 0:
            return False
        else:
            html = self.ui.textMergedPreview.toHtml()
            enc_write(savefile[0], html)

    def click_print(self):
        printer = QtGui.QPrinter()
        dialog = QtGui.QPrintDialog(printer)
        if dialog.exec_() == 1:
            self.ui.textMergedPreview.print_(printer)

    def click_merge_notes(self):
        # get title and tags
        new_title = self.ui.mergedNoteTitle.text()
        new_tags = self.ui.mergedNoteTags.text()
        notes_list = []

        for i in range(self.ui.notesList.count()):
            notes_list.append(self.ui.notesList.item(i).text())

        # write the new note
        filepath = path.join(self.notes_dir,new_title+self.note_extension)
        filedata = self.merged_content + '\n' + END_OF_TEXT + '\n'
        for key,value in self.merged_meta.items():
            if key == 'tags':
                value = u' '.join(value)
            filedata = filedata + '%s:%s\n'%(key,value)

        enc_write(filepath, filedata)

        now = datetime.now().strftime('%Y%m%d%H%M%S')
        # collect all the diffs
        for item in self.notes_list:
            note_title = item[1][:-len(self.note_extension)]
            zip_filepath = item[0] + ZIP_EXTENSION
            try:
                with gzip.GzipFile(zip_filepath, 'r') as myzip:
                    self.merged_history.extend([(note_title,name) for name in myzip.namelist()])
            except:
                # no history stored for this note
                self.merged_history.extend([(note_title,now + NOTE_EXTENSION)]) # add .txt to be consistent with zip.namelist

        zip_filepath = path.join(self.notes_dir,new_title + self.note_extension + ZIP_EXTENSION)
        current_history = {} # title:content
        #print sorted(self.merged_history, key=itemgetter(1), reverse=True)
        for h in sorted(self.merged_history, key=itemgetter(1), reverse=True): # sort newest to oldest
            # get the old content
            old_zip_filepath = path.join(self.notes_dir,h[0] + self.note_extension + ZIP_EXTENSION)
            try:
                with gzip.GzipFile(old_zip_filepath, 'r') as myzip:
                    old_content,m = parse_note_content(unicode(myzip.read(h[1]))) # meta discarded
            except:
                old_content = None
            # update the dictionary
            if old_content is not None:
                current_history[h[0]] = old_content
            # build the merged text
            merged = u''
            for n in notes_list:
                if current_history.has_key(n):
                    merged += current_history[n] + '\n'
                else:
                    pass
            # write the merged content to a temp file
            temp_filepath = path.join(self.notes_dir,h[1])
            enc_write(temp_filepath, merged)
            # put temp file in zip and delete it
            with gzip.GzipFile(zip_filepath, 'a') as myzip:
                myzip.write(temp_filepath,h[1])
            remove(temp_filepath)
