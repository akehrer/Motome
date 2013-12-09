# Import the future
from __future__ import print_function
from __future__ import unicode_literals

# Import standard library modules
import gzip

# Import Qt modules
from PySide import QtGui

# Import application window view
from Views.MergeHistoryDialog import Ui_MergeHistoryDialog

# Import additional modules
from HistoryListModel import HistoryListModel
from Utils import diff_to_html

# Import configuration values
from config import NOTE_EXTENSION


class MergeHistoryDialog(QtGui.QDialog):

    def __init__(self, filepath):
        super(MergeHistoryDialog, self).__init__()

        self.ui=Ui_MergeHistoryDialog()
        self.ui.setupUi(self)

        self.setWindowTitle('Diff History')

        self.filepath = filepath
        self.zip_filepath = filepath + '.zip'
        self.extension = NOTE_EXTENSION

        self.history = []

        self.from_history_model = None
        self.to_history_model = None

        self.current_from_idx = 0
        self.current_to_idx = 0

        self.load_history_data()

    def load_history_data(self):
        self.history = []
        try:
            with gzip.GzipFile(self.zip_filepath, 'r') as myzip:
                self.history = sorted(myzip.namelist(), reverse=True)

            self.from_history_model = HistoryListModel(self.history)
            self.to_history_model = HistoryListModel(self.history)

            self.ui.fromNotesList.setModel(self.from_history_model)
            self.ui.toNotesList.setModel(self.to_history_model)
        except:
            pass

    def update_diff(self):
        from_fn = self.history[self.current_from_idx]
        to_fn = self.history[self.current_to_idx]
        from_content = self.load_from_zip(from_fn)
        to_content = self.load_from_zip(to_fn)

        diff_html = diff_to_html(from_content,to_content)
        self.ui.diffView.setHtml(diff_html)

    def load_from_zip(self,filename):
        with gzip.GzipFile(self.zip_filepath, 'r') as myzip:
            content = myzip.read(filename)
        return content

    def click_update_from(self):
        self.current_from_idx = self.ui.fromNotesList.currentIndex().row()
        self.update_diff()

    def click_update_to(self):
        self.current_to_idx = self.ui.toNotesList.currentIndex().row()
        self.update_diff()