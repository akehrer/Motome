# Import the future
from __future__ import print_function
from __future__ import unicode_literals
from __future__ import absolute_import

# Import standard library modules
import os

# Import Qt modules
from PySide import QtGui

# Import application window view
from Motome.Views.SettingsDialog import Ui_SettingsDialog


class SettingsDialog(QtGui.QDialog):

    def __init__(self, conf):
        super(SettingsDialog, self).__init__()

        self.ui = Ui_SettingsDialog()
        self.ui.setupUi(self)

        self.conf = conf

        self.setWindowTitle('Settings')

        # try:
        #     self.ui.conf_notesLocation.setText(self.conf['conf_notesLocation'])
        # except KeyError:
        #     pass

        try:
            self.ui.tbl_notesLocations.blockSignals(True)
            for k, v in self.conf['conf_notesLocations'].iteritems():
                self._insert_noteslocation_row(v, k)
            self.ui.tbl_notesLocations.blockSignals(False)
        except KeyError:
            pass

        try:
            self.ui.conf_author.setText(self.conf['conf_author'])
        except KeyError:
            pass

        if 'conf_checkbox_recordonsave' in self.conf.keys():
            if int(self.conf['conf_checkbox_recordonsave']) == 0:
                self.ui.conf_checkbox_recordonsave.setChecked(False)
        else:
            self.ui.conf_checkbox_recordonsave.setChecked(True)

        if 'conf_checkbox_recordonexit' in self.conf.keys():
            if int(self.conf['conf_checkbox_recordonexit']) == 0:
                self.ui.conf_checkbox_recordonexit.setChecked(False)
        else:
            self.ui.conf_checkbox_recordonexit.setChecked(True)

        if 'conf_checkbox_recordonswitch' in self.conf.keys():
            if int(self.conf['conf_checkbox_recordonswitch']) == 0:
                self.ui.conf_checkbox_recordonswitch.setChecked(False)
        else:
            self.ui.conf_checkbox_recordonswitch.setChecked(True)

        if 'conf_checkbox_firstlinetitle' in self.conf.keys():
            if int(self.conf['conf_checkbox_firstlinetitle']) == 0:
                self.ui.conf_checkbox_firstlinetitle.setChecked(False)
        else:
            self.ui.conf_checkbox_firstlinetitle.setChecked(True)

    # def load_folder_location(self):
    #     if 'conf_notesLocation' in self.conf.keys():
    #         dirpath = self.conf['conf_notesLocation']
    #     else:
    #         dirpath = None
    #
    #     savedir = QtGui.QFileDialog.getExistingDirectory(self, 'Notes Directory', dirpath)
    #     self.ui.conf_notesLocation.setText(savedir)

    def add_folder_location(self):
        notesdir = QtGui.QFileDialog.getExistingDirectory(self, 'Notes Directory', os.path.expanduser('~'))
        try:
            if notesdir not in self.conf['conf_notesLocations'].keys():
                self._add_noteslocation_row(notesdir)
        except KeyError:
            self.conf['conf_notesLocations'] = {}
            self._add_noteslocation_row(notesdir)

    def _add_noteslocation_row(self, notesdir):
        self._insert_noteslocation_row(os.path.basename(notesdir), notesdir)
        self.conf['conf_notesLocations'][notesdir] = os.path.basename(notesdir)

    def _insert_noteslocation_row(self, col0, col1):
        self.ui.tbl_notesLocations.blockSignals(True)
        num_rows = self.ui.tbl_notesLocations.rowCount()
        self.ui.tbl_notesLocations.setRowCount(num_rows + 1)
        row = self.ui.tbl_notesLocations.rowCount() - 1

        new_item = QtGui.QTableWidgetItem(col0)
        self.ui.tbl_notesLocations.setItem(row, 0, new_item)

        new_item = QtGui.QTableWidgetItem(col1)
        self.ui.tbl_notesLocations.setItem(row, 1, new_item)
        self.ui.tbl_notesLocations.blockSignals(False)

    def remove_folder_location(self):
        row = self.ui.tbl_notesLocations.currentRow()
        row_key = self.ui.tbl_notesLocations.item(row, 1).text()
        self.ui.tbl_notesLocations.removeRow(row)
        del self.conf['conf_notesLocations'][row_key]

    def update_noteslocations_conf(self, row, col):
        if col == 0:
            item_val = self.ui.tbl_notesLocations.item(row, col).text()
            conf_key = self.ui.tbl_notesLocations.item(row, 1).text()
            self.conf['conf_notesLocations'][conf_key] = item_val
        else:
            item_key = self.ui.tbl_notesLocations.item(row, col).text()
            conf_val = self.ui.tbl_notesLocations.item(row, 0).text()
            conf_key = [k for k, v in self.conf['conf_notesLocations'].iteritems() if v == conf_val][0]
            del self.conf['conf_notesLocations'][conf_key]
            self.conf['conf_notesLocations'][item_key] = conf_val
