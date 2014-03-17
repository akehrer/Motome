# Import the future
from __future__ import print_function
from __future__ import unicode_literals
from __future__ import absolute_import

# Import Qt modules
from PySide import QtCore, QtGui


class NoteListWidgetItem(QtGui.QListWidgetItem):

    def __init__(self, notemodel):
        super(NoteListWidgetItem, self).__init__()

        self.notemodel = notemodel
        self._found = True

    def data(self, role=QtCore.Qt.DisplayRole):
        if role == QtCore.Qt.DisplayRole:
            return self.notemodel.title
        elif role == QtCore.Qt.DecorationRole:
            if self.notemodel.pinned:
                return QtGui.QIcon(":/icons/resources/pushpin_16.png")
            else:
                return None

    def __lt__(self, other):
        """ Used for custom sort on note's timestamp
        :param other: NoteListWidgetItem to compare against
        :return: boolean True if should be sorted below
        """
        if other.notemodel.pinned and self.notemodel.pinned:
            return self.notemodel.timestamp < other.notemodel.timestamp
        elif not other.notemodel.pinned and not self.notemodel.pinned:
            return self.notemodel.timestamp < other.notemodel.timestamp
        elif other.notemodel.pinned and not self.notemodel.pinned:
            return True
        elif not other.notemodel.pinned and self.notemodel.pinned:
            return False