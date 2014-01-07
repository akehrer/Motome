# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file '..\Motome\Views\SettingsDialog.ui'
#
# Created: Tue Jan 07 11:33:10 2014
#      by: pyside-uic 0.2.15 running on PySide 1.2.1
#
# WARNING! All changes made in this file will be lost!

from PySide import QtCore, QtGui

class Ui_SettingsDialog(object):
    def setupUi(self, SettingsDialog):
        SettingsDialog.setObjectName("SettingsDialog")
        SettingsDialog.setWindowModality(QtCore.Qt.ApplicationModal)
        SettingsDialog.resize(578, 348)
        icon = QtGui.QIcon()
        icon.addPixmap(QtGui.QPixmap(":/logo/resources/logo_320x320.png"), QtGui.QIcon.Normal, QtGui.QIcon.Off)
        SettingsDialog.setWindowIcon(icon)
        SettingsDialog.setModal(True)
        self.verticalLayout_2 = QtGui.QVBoxLayout(SettingsDialog)
        self.verticalLayout_2.setObjectName("verticalLayout_2")
        self.tabWidget = QtGui.QTabWidget(SettingsDialog)
        self.tabWidget.setObjectName("tabWidget")
        self.tab = QtGui.QWidget()
        self.tab.setObjectName("tab")
        self.verticalLayout = QtGui.QVBoxLayout(self.tab)
        self.verticalLayout.setObjectName("verticalLayout")
        self.horizontalLayout = QtGui.QHBoxLayout()
        self.horizontalLayout.setObjectName("horizontalLayout")
        self.label_3 = QtGui.QLabel(self.tab)
        self.label_3.setObjectName("label_3")
        self.horizontalLayout.addWidget(self.label_3)
        self.conf_notesLocation = QtGui.QLineEdit(self.tab)
        self.conf_notesLocation.setObjectName("conf_notesLocation")
        self.horizontalLayout.addWidget(self.conf_notesLocation)
        self.pushButton = QtGui.QPushButton(self.tab)
        self.pushButton.setObjectName("pushButton")
        self.horizontalLayout.addWidget(self.pushButton)
        self.verticalLayout.addLayout(self.horizontalLayout)
        self.label_2 = QtGui.QLabel(self.tab)
        self.label_2.setObjectName("label_2")
        self.verticalLayout.addWidget(self.label_2)
        self.conf_checkbox_history = QtGui.QCheckBox(self.tab)
        self.conf_checkbox_history.setChecked(True)
        self.conf_checkbox_history.setTristate(False)
        self.conf_checkbox_history.setObjectName("conf_checkbox_history")
        self.verticalLayout.addWidget(self.conf_checkbox_history)
        spacerItem = QtGui.QSpacerItem(20, 40, QtGui.QSizePolicy.Minimum, QtGui.QSizePolicy.Expanding)
        self.verticalLayout.addItem(spacerItem)
        self.label_4 = QtGui.QLabel(self.tab)
        self.label_4.setObjectName("label_4")
        self.verticalLayout.addWidget(self.label_4)
        self.conf_checkbox_deleteempty = QtGui.QCheckBox(self.tab)
        self.conf_checkbox_deleteempty.setChecked(True)
        self.conf_checkbox_deleteempty.setObjectName("conf_checkbox_deleteempty")
        self.verticalLayout.addWidget(self.conf_checkbox_deleteempty)
        self.conf_checkbox_ctrlsrecord = QtGui.QCheckBox(self.tab)
        self.conf_checkbox_ctrlsrecord.setChecked(True)
        self.conf_checkbox_ctrlsrecord.setObjectName("conf_checkbox_ctrlsrecord")
        self.verticalLayout.addWidget(self.conf_checkbox_ctrlsrecord)
        spacerItem1 = QtGui.QSpacerItem(20, 40, QtGui.QSizePolicy.Minimum, QtGui.QSizePolicy.Expanding)
        self.verticalLayout.addItem(spacerItem1)
        self.tabWidget.addTab(self.tab, "")
        self.tab_3 = QtGui.QWidget()
        self.tab_3.setObjectName("tab_3")
        self.verticalLayout_4 = QtGui.QVBoxLayout(self.tab_3)
        self.verticalLayout_4.setObjectName("verticalLayout_4")
        self.label = QtGui.QLabel(self.tab_3)
        self.label.setOpenExternalLinks(True)
        self.label.setObjectName("label")
        self.verticalLayout_4.addWidget(self.label)
        self.textMarkdownHelp = QtGui.QTextBrowser(self.tab_3)
        self.textMarkdownHelp.setReadOnly(True)
        self.textMarkdownHelp.setAcceptRichText(False)
        self.textMarkdownHelp.setSource(QtCore.QUrl("file:///C:/Users/Aaron Kehrer/Google Drive/Workspaces/Motome/Motome/resources/markdown_help.html"))
        self.textMarkdownHelp.setObjectName("textMarkdownHelp")
        self.verticalLayout_4.addWidget(self.textMarkdownHelp)
        self.tabWidget.addTab(self.tab_3, "")
        self.tab_4 = QtGui.QWidget()
        self.tab_4.setObjectName("tab_4")
        self.verticalLayout_5 = QtGui.QVBoxLayout(self.tab_4)
        self.verticalLayout_5.setObjectName("verticalLayout_5")
        self.textShorcutsHelp = QtGui.QTextBrowser(self.tab_4)
        self.textShorcutsHelp.setSource(QtCore.QUrl("file:///C:/Users/Aaron Kehrer/Google Drive/Workspaces/Motome/Motome/resources/keyboard_shortcuts.html"))
        self.textShorcutsHelp.setObjectName("textShorcutsHelp")
        self.verticalLayout_5.addWidget(self.textShorcutsHelp)
        self.tabWidget.addTab(self.tab_4, "")
        self.tab_2 = QtGui.QWidget()
        self.tab_2.setObjectName("tab_2")
        self.verticalLayout_3 = QtGui.QVBoxLayout(self.tab_2)
        self.verticalLayout_3.setObjectName("verticalLayout_3")
        self.textAboutHelp = QtGui.QTextBrowser(self.tab_2)
        self.textAboutHelp.setSource(QtCore.QUrl("file:///C:/Users/Aaron Kehrer/Google Drive/Workspaces/Motome/Motome/resources/about.html"))
        self.textAboutHelp.setObjectName("textAboutHelp")
        self.verticalLayout_3.addWidget(self.textAboutHelp)
        self.tabWidget.addTab(self.tab_2, "")
        self.verticalLayout_2.addWidget(self.tabWidget)
        self.buttonBox = QtGui.QDialogButtonBox(SettingsDialog)
        self.buttonBox.setOrientation(QtCore.Qt.Horizontal)
        self.buttonBox.setStandardButtons(QtGui.QDialogButtonBox.Cancel|QtGui.QDialogButtonBox.Save)
        self.buttonBox.setObjectName("buttonBox")
        self.verticalLayout_2.addWidget(self.buttonBox)

        self.retranslateUi(SettingsDialog)
        self.tabWidget.setCurrentIndex(0)
        QtCore.QObject.connect(self.buttonBox, QtCore.SIGNAL("accepted()"), SettingsDialog.accept)
        QtCore.QObject.connect(self.buttonBox, QtCore.SIGNAL("rejected()"), SettingsDialog.reject)
        QtCore.QObject.connect(self.pushButton, QtCore.SIGNAL("clicked()"), SettingsDialog.load_folder_location)
        QtCore.QMetaObject.connectSlotsByName(SettingsDialog)

    def retranslateUi(self, SettingsDialog):
        SettingsDialog.setWindowTitle(QtGui.QApplication.translate("SettingsDialog", "Dialog", None, QtGui.QApplication.UnicodeUTF8))
        self.label_3.setText(QtGui.QApplication.translate("SettingsDialog", "Notes location", None, QtGui.QApplication.UnicodeUTF8))
        self.conf_notesLocation.setPlaceholderText(QtGui.QApplication.translate("SettingsDialog", "Please select a notes location...", None, QtGui.QApplication.UnicodeUTF8))
        self.pushButton.setText(QtGui.QApplication.translate("SettingsDialog", "...", None, QtGui.QApplication.UnicodeUTF8))
        self.label_2.setText(QtGui.QApplication.translate("SettingsDialog", "Display Settings", None, QtGui.QApplication.UnicodeUTF8))
        self.conf_checkbox_history.setText(QtGui.QApplication.translate("SettingsDialog", "Show History Bar", None, QtGui.QApplication.UnicodeUTF8))
        self.label_4.setText(QtGui.QApplication.translate("SettingsDialog", "Action Settings", None, QtGui.QApplication.UnicodeUTF8))
        self.conf_checkbox_deleteempty.setToolTip(QtGui.QApplication.translate("SettingsDialog", "Should notes that contain no content be deleted, including their history?", None, QtGui.QApplication.UnicodeUTF8))
        self.conf_checkbox_deleteempty.setText(QtGui.QApplication.translate("SettingsDialog", "Delete empty notes", None, QtGui.QApplication.UnicodeUTF8))
        self.conf_checkbox_ctrlsrecord.setToolTip(QtGui.QApplication.translate("SettingsDialog", "Should the current note state be recored to the note history when you press Ctrl/Cmd-S", None, QtGui.QApplication.UnicodeUTF8))
        self.conf_checkbox_ctrlsrecord.setText(QtGui.QApplication.translate("SettingsDialog", "Record current note to history with Ctrl/Cmd-S", None, QtGui.QApplication.UnicodeUTF8))
        self.tabWidget.setTabText(self.tabWidget.indexOf(self.tab), QtGui.QApplication.translate("SettingsDialog", "Settings", None, QtGui.QApplication.UnicodeUTF8))
        self.label.setText(QtGui.QApplication.translate("SettingsDialog", "<html><head/><body><p><a href=\"http://daringfireball.net/projects/markdown/syntax\"><span style=\" text-decoration: underline; color:#0000ff;\">See official syntax for details</span></a></p></body></html>", None, QtGui.QApplication.UnicodeUTF8))
        self.tabWidget.setTabText(self.tabWidget.indexOf(self.tab_3), QtGui.QApplication.translate("SettingsDialog", "Markdown Help", None, QtGui.QApplication.UnicodeUTF8))
        self.tabWidget.setTabText(self.tabWidget.indexOf(self.tab_4), QtGui.QApplication.translate("SettingsDialog", "Keyboard Shortcuts", None, QtGui.QApplication.UnicodeUTF8))
        self.tabWidget.setTabText(self.tabWidget.indexOf(self.tab_2), QtGui.QApplication.translate("SettingsDialog", "About", None, QtGui.QApplication.UnicodeUTF8))

import MainWindow_rc
