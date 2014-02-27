# Import the future
from __future__ import print_function
from __future__ import unicode_literals
from __future__ import absolute_import

# Import Qt modules
from PySide import QtGui

# Import application window view
from Motome.Views.SettingsDialog import Ui_SettingsDialog


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

        try:
            self.ui.conf_author.setText(self.conf['conf_author'])
        except KeyError:
            pass

        # if 'conf_checkbox_history' in self.conf.keys():
        #     if int(self.conf['conf_checkbox_history']) == 0:
        #         self.ui.conf_checkbox_history.setChecked(False)
        # else:
        #     self.ui.conf_checkbox_history.setChecked(True)

        if 'conf_checkbox_recordonsave' in self.conf.keys():
            if int(self.conf['conf_checkbox_recordonsave']) == 0:
                self.ui.conf_checkbox_recordonexit.setChecked(False)
        else:
            self.ui.conf_checkbox_recordonexit.setChecked(True)

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

        if 'conf_checkbox_titleasfilename' in self.conf.keys():
            if int(self.conf['conf_checkbox_titleasfilename']) == 0:
                self.ui.conf_checkbox_titleasfilename.setChecked(False)
        else:
            self.ui.conf_checkbox_titleasfilename.setChecked(True)

        if 'conf_checkbox_firstlinetitle' in self.conf.keys():
            if int(self.conf['conf_checkbox_firstlinetitle']) == 0:
                self.ui.conf_checkbox_firstlinetitle.setChecked(False)
        else:
            self.ui.conf_checkbox_firstlinetitle.setChecked(True)

    def load_folder_location(self):
        if 'conf_notesLocation' in self.conf.keys():
            dirpath = self.conf['conf_notesLocation']
        else:
            dirpath = None

        savedir = QtGui.QFileDialog.getExistingDirectory(self, 'Notes Directory', dirpath)
        self.ui.conf_notesLocation.setText(savedir)
