# Import the future
from __future__ import print_function
from __future__ import unicode_literals
from __future__ import absolute_import

import glob
import os

# Import Qt modules
from PySide import QtCore, QtGui

from Motome.Models.NoteListWidgetItem import NoteListWidgetItem
from Motome.Models.NoteModel import NoteModel

from Motome.config import NOTE_EXTENSION


class NoteListWidget(QtGui.QListWidget):

    def __init__(self, notemodel_dict):
        super(NoteListWidget, self).__init__()

        self.session_notemodel_dict = notemodel_dict

        self.itemDoubleClicked.connect(self._dblclick_pin_note)

        self.previous_item = None
        self.currentItemChanged.connect(self._update_previous_item)

        self._notes_dir = None
        self.dir_watcher = QtCore.QFileSystemWatcher(self)
        # self.dir_watcher.directoryChanged.connect(self.update_list)

        self.update_list()

    @property
    def notes_dir(self):
        return self._notes_dir

    @notes_dir.setter
    def notes_dir(self, value):
        self._notes_dir = value
        old_paths = self.dir_watcher.directories()
        if len(old_paths) > 0:
            self.dir_watcher.removePaths(old_paths)
        self.dir_watcher.addPath(value)
        self.clear()
        self.update_list()
        self.setCurrentRow(0)

    @property
    def all_items(self):
        return self.findItems('*', QtCore.Qt.MatchWildcard)

    @property
    def all_visible_items(self):
        items = []
        for item in self.all_items:
            if not item.isHidden():
                items.append(item)
        return items

    def update_list(self):
        self._update_notemodel_dict()
        for value in self.session_notemodel_dict.values():
            if len(self.findItems(value.title, QtCore.Qt.MatchWildcard)) == 0:
                n = NoteListWidgetItem(value)
                self.addItem(n)
        self.sortItems(QtCore.Qt.DescendingOrder)

    def search_noteitems(self, search_object):
        for nw in self.all_items:
            if not search_object.search_notemodel(nw.notemodel):
                nw.setHidden(True)
            else:
                nw.setHidden(False)
        try:
            self.setCurrentItem(self.all_visible_items[0])
            return True
        except IndexError:
            # no items found
            self.setCurrentRow(-1)
            return False

    def show_all(self):
        for nw in self.all_items:
            nw.setHidden(False)

    def delete_current_item(self):
        message_box = QtGui.QMessageBox()
        message_box.setText('Delete {0}?'.format(self.currentItem().notemodel.title))
        message_box.setInformativeText('Are you sure you want to delete this note?')
        delete_btn = message_box.addButton('Delete', QtGui.QMessageBox.YesRole)
        cancel_btn = message_box.addButton(QtGui.QMessageBox.Cancel)
        message_box.setEscapeButton(QtGui.QMessageBox.Cancel)
        message_box.setDefaultButton(cancel_btn)

        message_box.exec_()

        if message_box.clickedButton() == delete_btn:
            i = self.currentRow()
            item = self.takeItem(i)
            if not item.notemodel.remove():
                message_box = QtGui.QMessageBox()
                message_box.setText('Delete Error!'.format(item.notemodel.title))
                message_box.setInformativeText('There was a problem deleting all the note files. Please check the {0} '
                                               'directory for any remaining data.'.format(self.notes_dir))
                message_box.exec_()
            else:
                del item

    def rename_current_item(self):
        self.dir_watcher.blockSignals(True)
        self.currentItem().notemodel.rename()
        self.update()
        self.dir_watcher.blockSignals(False)

    def _dblclick_pin_note(self, noteitem):
        if noteitem.notemodel.pinned:
            noteitem.notemodel.pinned = False
        else:
            noteitem.notemodel.pinned = True
        self.update_list()

    def _update_notemodel_dict(self):
        if self.notes_dir is None or self.notes_dir == '':
            return
        notepaths = set(glob.glob(self.notes_dir + '/*' + NOTE_EXTENSION))
        notenames = map(os.path.basename, notepaths)
        note_keys = set(self.session_notemodel_dict.keys())
        keys_missing_notes = note_keys - set(notenames)

        # remove keys missing notes
        for filename in keys_missing_notes:
            del self.session_notemodel_dict[filename]

        # add notes missing keys
        for filepath in notepaths:
            filename = os.path.basename(filepath)
            if filename not in self.session_notemodel_dict.keys():
                note = NoteModel(filepath)
                self.session_notemodel_dict[note.filename] = note

    def _update_previous_item(self, current, previous):
        self.previous_item = previous