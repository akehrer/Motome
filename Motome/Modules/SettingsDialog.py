# Import the future
from __future__ import print_function
from __future__ import unicode_literals

# Import Qt modules
from PySide import QtGui

# Import application window view
from Views.SettingsDialog import Ui_SettingsDialog


class SettingsDialog(QtGui.QDialog):

    def __init__(self, conf):
        super(SettingsDialog, self).__init__()

        self.ui=Ui_SettingsDialog()
        self.ui.setupUi(self)

        self.conf = conf

        self.setWindowTitle('Settings')

        try:
            self.ui.conf_notesLocation.setText(self.conf['conf_notesLocation'])
        except KeyError:
            pass

        if 'conf_checkbox_history' in self.conf.keys():
            if int(self.conf['conf_checkbox_history']) == 0:
                self.ui.conf_checkbox_history.setChecked(False)
        else:
            self.ui.conf_checkbox_history.setChecked(True)

        if 'conf_checkbox_deleteempty' in self.conf.keys():
            if int(self.conf['conf_checkbox_deleteempty']) == 0:
                self.ui.conf_checkbox_deleteempty.setChecked(False)
        else:
            self.ui.conf_checkbox_deleteempty.setChecked(True)

    def load_folder_location(self):
        if 'conf_notesLocation' in self.conf.keys():
            dirpath = self.conf['conf_notesLocation']
        else:
            dirpath = None

        savedir = QtGui.QFileDialog.getExistingDirectory (self, 'Notes Directory', dirpath)
        self.ui.conf_notesLocation.setText(savedir)
