# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file '..\Motome\Views\MergeHistoryDialog.ui'
#
# Created: Tue Dec 10 11:33:54 2013
#      by: pyside-uic 0.2.14 running on PySide 1.1.2
#
# WARNING! All changes made in this file will be lost!

from PySide import QtCore, QtGui

class Ui_MergeHistoryDialog(object):
    def setupUi(self, MergeHistoryDialog):
        MergeHistoryDialog.setObjectName("MergeHistoryDialog")
        MergeHistoryDialog.resize(600, 600)
        icon = QtGui.QIcon()
        icon.addPixmap(QtGui.QPixmap(":/icons/resources/logo_320x320.png"), QtGui.QIcon.Normal, QtGui.QIcon.Off)
        MergeHistoryDialog.setWindowIcon(icon)
        self.verticalLayout_3 = QtGui.QVBoxLayout(MergeHistoryDialog)
        self.verticalLayout_3.setObjectName("verticalLayout_3")
        self.splitter = QtGui.QSplitter(MergeHistoryDialog)
        self.splitter.setOrientation(QtCore.Qt.Vertical)
        self.splitter.setObjectName("splitter")
        self.layoutWidget = QtGui.QWidget(self.splitter)
        self.layoutWidget.setObjectName("layoutWidget")
        self.horizontalLayout = QtGui.QHBoxLayout(self.layoutWidget)
        self.horizontalLayout.setContentsMargins(0, 0, 0, 0)
        self.horizontalLayout.setObjectName("horizontalLayout")
        self.verticalLayout = QtGui.QVBoxLayout()
        self.verticalLayout.setObjectName("verticalLayout")
        self.label = QtGui.QLabel(self.layoutWidget)
        self.label.setObjectName("label")
        self.verticalLayout.addWidget(self.label)
        self.fromNotesList = QtGui.QListView(self.layoutWidget)
        self.fromNotesList.setObjectName("fromNotesList")
        self.verticalLayout.addWidget(self.fromNotesList)
        self.horizontalLayout.addLayout(self.verticalLayout)
        self.verticalLayout_2 = QtGui.QVBoxLayout()
        self.verticalLayout_2.setObjectName("verticalLayout_2")
        self.label_2 = QtGui.QLabel(self.layoutWidget)
        self.label_2.setObjectName("label_2")
        self.verticalLayout_2.addWidget(self.label_2)
        self.toNotesList = QtGui.QListView(self.layoutWidget)
        self.toNotesList.setObjectName("toNotesList")
        self.verticalLayout_2.addWidget(self.toNotesList)
        self.horizontalLayout.addLayout(self.verticalLayout_2)
        self.diffView = QtGui.QTextBrowser(self.splitter)
        self.diffView.setObjectName("diffView")
        self.verticalLayout_3.addWidget(self.splitter)
        self.buttonBox = QtGui.QDialogButtonBox(MergeHistoryDialog)
        self.buttonBox.setOrientation(QtCore.Qt.Horizontal)
        self.buttonBox.setStandardButtons(QtGui.QDialogButtonBox.Close)
        self.buttonBox.setObjectName("buttonBox")
        self.verticalLayout_3.addWidget(self.buttonBox)

        self.retranslateUi(MergeHistoryDialog)
        QtCore.QObject.connect(self.buttonBox, QtCore.SIGNAL("accepted()"), MergeHistoryDialog.accept)
        QtCore.QObject.connect(self.buttonBox, QtCore.SIGNAL("rejected()"), MergeHistoryDialog.reject)
        QtCore.QObject.connect(self.fromNotesList, QtCore.SIGNAL("clicked(QModelIndex)"), MergeHistoryDialog.click_update_from)
        QtCore.QObject.connect(self.toNotesList, QtCore.SIGNAL("clicked(QModelIndex)"), MergeHistoryDialog.click_update_to)
        QtCore.QMetaObject.connectSlotsByName(MergeHistoryDialog)

    def retranslateUi(self, MergeHistoryDialog):
        MergeHistoryDialog.setWindowTitle(QtGui.QApplication.translate("MergeHistoryDialog", "Dialog", None, QtGui.QApplication.UnicodeUTF8))
        self.label.setText(QtGui.QApplication.translate("MergeHistoryDialog", "From", None, QtGui.QApplication.UnicodeUTF8))
        self.label_2.setText(QtGui.QApplication.translate("MergeHistoryDialog", "To", None, QtGui.QApplication.UnicodeUTF8))

import MainWindow_rc
