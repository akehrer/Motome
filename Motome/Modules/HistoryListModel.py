# Import the future
from __future__ import print_function
from __future__ import unicode_literals

# Import Qt modules
from PySide import QtCore, QtGui

# Import configuration values
from config import NOTE_EXTENSION


class HistoryListModel(QtCore.QAbstractListModel):
    def __init__(self, items):
        """
        :param items: a list of tuples (filename,filepath,last_modified_timestamp)
        """
        super(HistoryListModel, self).__init__()
        self.items = items
        self.extension = NOTE_EXTENSION

    def rowCount(self, index):
        return len(self.items)

    def data(self, index, role=QtCore.Qt.DisplayRole):
        if role == QtCore.Qt.DisplayRole:
            dt = self.items[index.row()][:-len(self.extension)]
            date = '%s-%s-%s %s:%s:%s'%(dt[0:4],dt[4:6],dt[6:8],dt[8:10],dt[10:12],dt[12:])
            item = QtGui.QStandardItem()
            item.setText('%s'%date)
            item.setSelectable(False)
            return '%s'%date
        else:
            return None
